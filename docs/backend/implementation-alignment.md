# Implementation Alignment Tracker

Last reviewed: 2026-11-15

This file separates the documented Version 1 target from what is currently implemented. The detailed table definitions remain in [database design](05-database-design-v1.md); this tracker records implementation status and unresolved differences.

## Implemented and Tested

| Area | Current implementation |
| --- | --- |
| Authentication | Session login, logout, current-user lookup, password hashing, and active-account checks. |
| User creation | Administrator-only create-user API with supported roles, password hashing, duplicate handling, and tests. User listing, editing, activation, and password reset are not implemented. |
| Season lifecycle | Public history, Administrator create, controlled status transitions, date validation, sequential one-active-season checks, and a roster-readiness gate before moving to Ongoing. |
| Season configuration | Administrators create, edit and remove season-owned sports and their divisions during Planning or Registration. Removal is blocked when teams exist. |
| Season Teams | Public list; Administrator-only registration, update, and soft archive/restore. Archive/restore require Registration status, and restore also requires an open registration window and no conflicting active-team roster assignments. Duplicate names are blocked per division, including archived teams. |
| Players and Rosters | Administrator Player profile create/read/update/archive/restore; roster list/add/jersey update/remove. Adult roster additions require voter verification, and Player profiles remain when roster links are removed. |
| Game scheduling | Administrators create games for active teams in an Ongoing season and reschedule them before their start; public division listings show local start/end times and free-text venues. A serialized write prevents overlapping team or venue bookings. |
| Results and standings | Administrators and Encoders enter scores after the scheduled end during Ongoing; Administrators finalize or reopen with a reason. Finalized games determine division win/loss standings. |
| Game statistics | Administrators configure required/optional statistics per season sport; Administrators and Encoders record Played/DNP and player statistics. Finalization checks completeness and optional score reconciliation. |
| Frontend | Login, dashboard, Add User, Players, Seasons, and Season Configuration with nested sport/division/team tabs, roster management, and division scheduling. Selected data uses a one-minute freshness period and can be manually refreshed. |
| Database migrations | Roles/legacy user-role conversion, Seasons, seasonal configuration, SeasonTeam, Player, Roster, eligibility, archive fields, games, and schedule lock. |

## Implemented Tables

The current ORM models cover `users`, `roles`, `seasons`, `season_sports`, `season_sport_divisions`, `season_teams`, `players`, `rosters`, `season_player_eligibilities`, `games`, result reopening history, sport statistic configurations and types, game participants, player game statistics, team points, and the singleton `schedule_lock`. The migration chain creates these feature tables; its first migration assumes a `users` table already exists.

The remaining tables in the Version 1 database design are targets, not implemented tables. This includes managed venues, playoffs, general audit logs, API request idempotency, and system settings. Game result reopening has a dedicated history table; it is not a general audit log.

## Results and standings

The result lifecycle is `SCHEDULED` → `FOR_ENCODING` → `FINALIZED`. Only
Administrators finalize or reopen; Administrators and Encoders can enter
non-negative whole-number scores for games whose scheduled end has passed.
Results can be changed only while the season is Ongoing. Scores must identify
a winner, including any overtime; overtime periods are not recorded separately.
Reopening requires a reason and saves the previous scores, finalizer, reopening
user and timestamps. Reopened games stop counting until finalized again.

Standings are calculated per season division from finalized games, including
teams with no games (and archived historical teams). Rank by total wins; for
equal wins compare head-to-head win percentages among those tied teams using
their available finalized games. Teams with no head-to-head games rank after
those with such games; identical tie-break values share a rank, with the next
rank skipped. Results are not recursively re-ranked. Playoff stages and their
effect on standings remain unimplemented.

Revision `f5a6b7c8d901` adds results and reopening history, preserving existing
schedules as `SCHEDULED`. Revision `a6b7c8d9e012` adds statistics without changing
existing results. Back up and verify a restore before upgrading; downgrades
require backup restoration because they would otherwise discard data.

## Game statistics and finalization

Administrators configure statistics for each season sport independently. Each
definition has a name, abbreviation and required/optional flag. At most one
required statistic may be designated to match the official score; an
Administrator can also enable unattributed team points for that sport. With
no scoring statistic, player statistics do not determine the winner: the
official game score does. Definitions are locked once any participant status
or team points are saved for a game in that sport.

Administrators and Encoders can save partial statistics after the scheduled
game end while the season is Ongoing. They mark every rostered player Played
or DNP; DNP players cannot have values. Values are decimals with at most two
fractional digits; scoring values and team points cannot be negative.
Finalization requires a configured sport, a Played or DNP status for every
rostered player, at least one Played player per team, and every required value
for each Played player. If score matching is enabled, player scoring values
plus enabled team points must equal each team's official score; explicit zero
team points must be entered when team points are enabled.

Pre-existing finalized games remain finalized and continue to count without
statistics. If reopened, they must satisfy the current checks to be finalized
again. Reopening retains the existing statistics for editing, but the reopening
history currently records scores and finalization details, not prior statistics.
Season/career aggregation and leaderboards remain planned.

## Misalignment Register

### Season-owned sports and divisions

**Status: implemented; the local development database was migrated after backup and restore testing.** Other databases still require their own backup and migration. Players remain reusable across seasons;
user accounts remain shared for authentication. Each season owns its sports,
each sport in a season owns its divisions, and teams, rosters and games remain
attached to those season-specific records. Administrators create sports and
divisions manually; no cross-season templates or copy workflow are planned.
Configuration changes are allowed only in Planning or Registration. Venue
overlaps remain global across seasons.

The physical model keeps the existing `season_sports` and
`season_sport_divisions` IDs as the owning records: move sport name and
description onto `season_sports`, and division name, gender policy and roster
limits onto `season_sport_divisions`. Enforce unique sport names within a season
and division names within a season sport. Links to these IDs from teams and
games are preserved by the migration.

Global catalog endpoints have been removed. Season-scoped sport and
season-sport-scoped division changes validate the parent and season status on
the server. The frontend and seed scripts use the new API and model. Roster
rules compare players within the same season sport, and the shared roster lock
serializes additions and team restore. Venue conflicts include all seasons.

The migration copies every existing assignment using the shared
catalog's **current** values, retaining season-sport and division-assignment
IDs so team, roster and game links survive. Historical settings changed before
this migration cannot be reconstructed. Back up the target database before
applying the migration. With the user's approval, unassigned shared catalog
records are removed after the backup; they cannot be attributed to a season.
Test a restored backup on a disposable database before applying it to the
target. The migration rejects missing references and scoped name collisions
before DDL. A later DDL failure can leave a partial migration (notably because
MySQL DDL can commit implicitly): restore the verified backup rather than retrying blindly.
Downgrade is unsupported; restore the backup instead.

The SQLite migration requires `PRAGMA foreign_keys=OFF` on its migration
connection **before** its transaction starts. It aborts before schema changes
if foreign keys are enabled. Verify `PRAGMA foreign_key_check` after migrating
and re-enable foreign keys before normal application use. The migration passed
a synthetic linked-record test on SQLite and a disposable MySQL database;
neither test replaces validation with a restored target backup.

| Priority | Misalignment | Status / next action |
| --- | --- | --- |
| High | The initial roles migration alters `users` but does not create it. A fresh database cannot be initialized solely from this migration chain. | Resolve before claiming clean-install support: add a baseline migration or document and script the required legacy users-table prerequisite. Do not rewrite an applied migration. |
| High | The one-active-season rule is checked in application code, but concurrent activation requests can both pass the query before either commits. | Add database/transaction-level serialization or a database constraint appropriate to the production database, plus a concurrency test, before production. |
| Medium | Database design says entities use archival/soft deletion, but unused seasonal Sports/Divisions are physically deleted. | Decide whether to implement archive fields/statuses or narrow the soft-delete rule. Deletion is blocked when teams exist. |
| Medium | API docs describe idempotency and an `ApiRequest` table, but the current idempotency decorator is a pass-through and there is no model/migration. | Treat idempotency as planned; implement storage and replay semantics before marking it complete. |
| Medium | Business rules and API specification describe Rounds, but the canonical database design has no Round table or `round_id` on Game. | Rounds are deferred for the initial scheduling feature. Decide whether to add them to V1 before implementing later competition workflows. |
| Medium | Scheduling stores a free-text venue and local start/end times; the V1 design describes managed Venues and a richer Game lifecycle. | Define managed venues, cancellation, and game status/results before implementing them. Venue conflict checks compare normalized names, not aliases. |
| Medium | The Season completion transition does not require or set `end_date`, although the date is intended to describe competition dates. | Decide whether completion requires an end date or records one automatically, then encode and test that rule. |
| Medium | Player gender is stored as short text because the docs call it an enum but do not define allowed values. | Agree on the permitted gender values and convert the column/schema to a validated enum if needed. |
| Medium | Roster minimum size is checked before moving a season to Ongoing; division gender rules and eligibility policy remain incomplete. | Resolved for roster minimum: transition checks each non-archived team's active players against its division minimum and reports incomplete rosters. Define and enforce gender/eligibility rules separately. |
| Medium | Season status transitions and roster/team changes are not serialized together. | Before production, test and enforce the Registration-to-Ongoing boundary against concurrent roster and team changes. Archive/restore and roster additions now share a season-sport lock for player conflicts; their concurrency test uses SQLite. |
| Medium | SeasonTeam registration checks the current date against the registration window but does not persist a dedicated `registered_on` date. | Add an auditable registration date if later reports or eligibility rules need to prove when a team registered. |
| Low | The full architecture document describes a Unit of Work, but current services commit via `db.session` directly. | Accept this as a deliberate current simplification or add a Unit of Work when transaction coordination grows. |

## Resolved Documentation Drift

| Date | Misalignment | Resolution |
| --- | --- | --- |
| 2026-11-12 | ERD used `VoterRegistration`, `Round`, `PlayoffMatch`, `SystemSetting`, home/away game IDs, and a User email constraint that did not match the canonical database-design document. | Updated the ERD entity names, relationships, and fields to follow `05-database-design-v1.md`. |
| 2026-11-12 | Backend overview still described auth-only scope and linked singular model filenames. | Updated it to describe the current services/policies/repositories and implemented Season/catalog workflows. |
| 2026-11-12 | Checklist showed completed foundation work and current features as untouched. | Reconciled it with implemented, partial, and planned scope. |
| 2026-11-12 | ERD omitted SeasonPlayerEligibility relationships after entity names were aligned. | Added Season, Player, and verifying User relationships to its summary. |
| 2026-11-12 | Schemas used Marshmallow `load_default`, but the project pins Marshmallow 3.9.0, which did not apply those defaults. | Removed the unsupported schema options; optional values now fall through to explicit service defaults. |

## Migration State

On 2026-11-17 the local development database was backed up and restore-tested
before upgrading through `a6b7c8d9e012`. Existing table rows were compared with
the restored backup after the statistics migration. Check each other target
database's revision and create and verify its own backup before applying migrations.

## Demo Teams and Players

Refreshing the frontend or restarting the application does not run either seed script. In the development database, `DEMO - Registration Season 2027` must already exist, be in Registration, and be within its registration window. From `backend`, run `..\.venv\Scripts\python.exe seed_demo_teams.py --actor-id <administrator-user-id>`. Use the ID of an active Administrator. The script creates four Senior and three Junior sample basketball teams, with at least the division's minimum number of players on each, and skips existing demo roster entries on reruns. It does not populate other teams.

After seeding, the script verifies the sample teams, players, roster links, and fictional adult voter details; it also reports any active team below its division minimum. Run the same checks without modifying data at any time using `..\.venv\Scripts\python.exe seed_demo_teams.py --check`. A sample-data verification error exits with an error; incomplete non-demo teams are reported separately because they also prevent the season from moving to Ongoing.

All generated players are fictional and identifiable by `Demo` in their names and `DEMO -` in their addresses. Adult entries receive fictional `DEMO-` voter numbers marked as verified by the supplied Administrator, with a note that the details are not real. Never run this script against a production database. The script uses the configured development `DATABASE_URL`; service operations commit as they run, so an error may leave partial demo data. Resolve the error and rerun it.

## Recommended Next Work

1. Validate a complete test season and decide the outstanding player-eligibility policies.
2. Extend manual scheduling with agreed cancellation rules; decide whether managed venues and Rounds are needed.
3. Manually verify results, player statistics and standings; then design playoffs and aggregate statistics.
4. Before production or publishing, resolve the fresh-install and Administrator bootstrap gaps, concurrent active-season enforcement, soft-delete policy, and tracked runtime/session artifacts.
