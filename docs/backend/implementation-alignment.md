# Implementation Alignment Tracker

Last reviewed: 2026-11-12

This file separates the documented Version 1 target from what is currently implemented. The detailed table definitions remain in [database design](05-database-design-v1.md); this tracker records implementation status and unresolved differences.

## Implemented and Tested

| Area | Current implementation |
| --- | --- |
| Authentication | Session login, logout, current-user lookup, password hashing, and active-account checks. |
| User creation | Administrator-only create-user API with supported roles, password hashing, duplicate handling, and tests. User listing, editing, activation, and password reset are not implemented. |
| Season lifecycle | Public history, Administrator create, controlled status transitions, date validation, and sequential one-active-season checks. |
| Sport and Division catalogs | Administrator create/read/update/delete. Catalog entries cannot be deleted while referenced. |
| Season configuration | Assign catalog Sports to a Season; assign catalog Divisions under a Season-Sport; remove those assignments while the Season is Planning or Registration. |
| Frontend | Login, dashboard, Add User, Seasons, and Season Configuration pages. |
| Database migrations | Roles/legacy user-role conversion, Seasons, optional registration dates, Sport/Division catalogs, and season association tables. The current checked-in head additionally includes the Season name-width migration described below. |

## Implemented Tables

The current ORM models cover `users`, `roles`, `seasons`, `sports`, `divisions`, `season_sports`, and `season_sport_divisions`. The migration chain creates the role, season, sport/division, and association tables; its first migration assumes a `users` table already exists.

The remaining tables in the Version 1 database design are targets, not implemented tables. This includes teams, players, rosters, games, venues, statistics, playoffs, audit logs, API request idempotency, and system settings.

## Misalignment Register

| Priority | Misalignment | Status / next action |
| --- | --- | --- |
| High | The initial roles migration alters `users` but does not create it. A fresh database cannot be initialized solely from this migration chain. | Resolve before claiming clean-install support: add a baseline migration or document and script the required legacy users-table prerequisite. Do not rewrite an applied migration. |
| High | The one-active-season rule is checked in application code, but concurrent activation requests can both pass the query before either commits. | Add database/transaction-level serialization or a database constraint appropriate to the production database, plus a concurrency test, before production. |
| Medium | Database design says entities use archival/soft deletion, but current catalog deletion physically deletes unused Sports/Divisions and the models have no archive fields. | Decide whether to implement archive fields/statuses or narrow the soft-delete rule. Until then, catalog deletion is blocked when assigned. |
| Medium | API docs describe idempotency and an `ApiRequest` table, but the current idempotency decorator is a pass-through and there is no model/migration. | Treat idempotency as planned; implement storage and replay semantics before marking it complete. |
| Medium | Business rules and API specification describe Rounds, but the canonical database design has no Round table or `round_id` on Game. | Decide whether Rounds are part of Version 1; if yes, define the table and relation in the database design before implementing them. |
| Medium | The Season completion transition does not require or set `end_date`, although the date is intended to describe competition dates. | Decide whether completion requires an end date or records one automatically, then encode and test that rule. |
| Low | The full architecture document describes a Unit of Work, but current services commit via `db.session` directly. | Accept this as a deliberate current simplification or add a Unit of Work when transaction coordination grows. |
| Low | Editing a shared Sport or Division changes the catalog record shown by every season assignment; no per-season snapshot is stored. | Confirm this shared-update behavior is intended. If historical values must be frozen, add versioned/snapshotted configuration before teams and games depend on it. |

## Resolved Documentation Drift

| Date | Misalignment | Resolution |
| --- | --- | --- |
| 2026-11-12 | ERD used `VoterRegistration`, `Round`, `PlayoffMatch`, `SystemSetting`, home/away game IDs, and a User email constraint that did not match the canonical database-design document. | Updated the ERD entity names, relationships, and fields to follow `05-database-design-v1.md`. |
| 2026-11-12 | Backend overview still described auth-only scope and linked singular model filenames. | Updated it to describe the current services/policies/repositories and implemented Season/catalog workflows. |
| 2026-11-12 | Checklist showed completed foundation work and current features as untouched. | Reconciled it with implemented, partial, and planned scope. |
| 2026-11-12 | ERD omitted SeasonPlayerEligibility relationships after entity names were aligned. | Added Season, Player, and verifying User relationships to its summary. |
| 2026-11-12 | Schemas used Marshmallow `load_default`, but the project pins Marshmallow 3.9.0, which did not apply those defaults. | Removed the unsupported schema options; optional values now fall through to explicit service defaults. |

## Pending Migration

The database-design document specifies Season names up to 150 characters. The model, request schema, policy, frontend, and a new migration now match that limit. The current database was last confirmed at revision `c8d47a1e2f90`; apply the new `d29e7b6ac145` migration with `flask --app wsgi db upgrade` before accepting names longer than 100 characters in that database.

## Recommended Next Work

1. Apply and verify the pending Season name-width migration.
2. Decide the migration bootstrap and soft-delete policy.
3. Add `SeasonTeam` management, which can now depend on the implemented Season-Sport-Division chain.
4. Continue with Player, Eligibility, and Roster features, reconciling the ERD first.
