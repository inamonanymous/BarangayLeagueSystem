# Backend System Overview

## Current Scope

The backend is a Flask JSON API organized around feature routes, application services, policies, repositories, SQLAlchemy models, and Alembic migrations. The main entry point is [wsgi.py](../../backend/wsgi.py); the app factory and blueprint registration are in [app/__init__.py](../../backend/app/__init__.py) and [app/api/v1/__init__.py](../../backend/app/api/v1/__init__.py).

## Request Flow

The intended path is:

```text
Route -> Schema -> Service -> Policy / Repository -> Model -> Database
   ^                                                        |
   +---------------------- JSON response -------------------+
```

Routes parse HTTP requests, load Marshmallow schemas where applicable, call services, and format API responses. Services coordinate use cases and own transactions. Policies apply business checks where used. Repositories perform database reads and writes where used. Models define persisted entities and serialization helpers.

Not every request uses every layer. Implemented feature services use policies and repositories for their applicable rules and queries. Most services still use SQLAlchemy's `db.session` directly; roster writes instead use a shared transaction wrapper.

## Implemented Features

- **Authentication and users:** login, logout, current-user lookup, session-based authentication, and Administrator-only user creation.
- **Season lifecycle:** list/create, controlled status transitions, history retention, single-active-season validation at the service layer, and an active-roster minimum check before Ongoing.
- **Sports and divisions:** season-owned sport and division creation, editing and removal during Planning or Registration. Removal is rejected when teams are registered.
- **Teams and rosters:** public team/roster lists; Administrator team registration, edits, archive/restore, roster membership changes, jersey updates, and season-window validation. Archive and restore require Registration status; restore also requires an open window and no roster player on another active team in the same sport and season. The Administrator-only available-player list excludes players already on active teams in the same sport and season.
- **Players:** Administrator player profile create/read/update/archive/restore, with year-specific voter IDs and season-level adult voter verification when required.
- **Game scheduling:** public division game listings; Administrators can schedule or reschedule during Ongoing with team and venue overlap checks. Rescheduling retains teams and requires both the original and new starts to be in the future.
- **Game results and standings:** Administrators and Encoders enter scores; Administrators finalize or reopen with an audit reason. Standings are calculated from finalized games.
- **Game statistics:** Administrators configure season-sport statistic types; Administrators and Encoders enter player participation and values. Finalization validates completeness and configured score matching.

The ORM also includes sport statistic configurations and types, game participants, player game statistics and team points. Game cancellation, aggregate statistics, playoffs, reports, general audit logging, idempotency storage, managed venues, and system settings remain planned.

## Main Packages

- `app/api/v1`: HTTP endpoints grouped by feature.
- `app/application`: services and policies.
- `app/infrastructure/database`: repositories and persistence helpers.
- `app/domain/models`: SQLAlchemy entities.
- `app/schemas`: request validation and deserialization.
- `app/extensions`: SQLAlchemy, Flask-Migrate, and session initialization.
- `migrations/versions`: forward/backward schema changes.

## Feature Flow Examples

Authentication flows through [auth routes](../../backend/app/api/v1/auth/routes.py), [AuthService](../../backend/app/application/auth/services.py), [AuthPolicy](../../backend/app/application/auth/policies.py), and UserRepository.

Season configuration flows through [season routes](../../backend/app/api/v1/seasons/routes.py), [CatalogService](../../backend/app/application/catalogs/services.py), [CatalogPolicy](../../backend/app/application/catalogs/policies.py), and [CatalogRepository](../../backend/app/infrastructure/database/catalog_repository.py).

Scheduling flows through [game routes](../../backend/app/api/v1/games/routes.py), [game schemas](../../backend/app/schemas/game_schema.py), [GameService](../../backend/app/application/games/services.py), [GamePolicy](../../backend/app/application/games/policies.py), and [GameRepository](../../backend/app/infrastructure/database/game_repository.py). The repository supplies [typed snapshots](../../backend/app/application/games/types.py) for policy validation and owns ORM persistence. The service coordinates lookups, the schedule lock and the unit of work.

Statistics flow through [statistics routes](../../backend/app/api/v1/statistics/routes.py),
[StatisticsService](../../backend/app/application/statistics/services.py),
[StatisticsPolicy](../../backend/app/application/statistics/policies.py), and
[StatisticsRepository](../../backend/app/infrastructure/database/statistics_repository.py).
Writes share the schedule lock and unit of work with game finalization.

Roster changes flow through [team routes](../../backend/app/api/v1/teams/routes.py), [RosterService](../../backend/app/application/rosters/services.py), [RosterPolicy](../../backend/app/application/rosters/policies.py), and [RosterRepository](../../backend/app/infrastructure/database/roster_repository.py). The repository converts ORM records to [typed snapshots and response data](../../backend/app/application/rosters/types.py), so the service and policy do not manipulate ORM models. The [transaction wrapper](../../backend/app/infrastructure/database/unit_of_work.py) commits roster and adult eligibility changes together and rolls them back on failure. Roster additions and team archive/restore use a [shared season-sport lock](../../backend/app/infrastructure/database/team_roster_lock.py) to serialize the conflict check and write. Roster lists fetch their players in one joined query.

## Current Alignment

This overview describes implemented behavior. The full Version 1 target and known gaps are recorded in [the implementation alignment tracker](implementation-alignment.md); the project roadmap is in [the checklist](../checklist.md).

For a feature-by-feature layer inventory, roster cleanup steps, and an
all-feature refactoring tracker, see the [Excel code matrix](feature-code-matrix.xlsx).
It is a snapshot and must be updated as the code changes. The roster feature now
uses typed data and a transaction wrapper; other features still need their own
boundary and transaction work.

The separate [backend cleanup tracker](backend-cleanup-tracker.xlsx) provides
ordered tasks for each implemented feature. Its roster sheet is copied from the
saved matrix; progress in the two workbooks is independent.
