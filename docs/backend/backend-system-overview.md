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

Routes parse HTTP requests, load Marshmallow schemas, call services, and format API responses. Services coordinate use cases and own transactions. Policies apply stateless business checks. Repositories perform database reads and writes. Models define persisted entities and serialization helpers.

This is the current implemented pattern, not a fully abstract Unit-of-Work architecture: services commit through SQLAlchemy's `db.session` directly.

## Implemented Features

- **Authentication and users:** login, logout, current-user lookup, session-based authentication, and Administrator-only user creation.
- **Season lifecycle:** list/create, controlled status transitions, history retention, and single-active-season validation at the service layer.
- **Sports and divisions:** catalog create/list/update/delete, plus season-specific sport and division assignments. Catalog deletion is rejected while referenced; season assignments may be edited only while the season is Planning or Registration.
- **Teams and rosters:** public team/roster lists; Administrator team registration, team updates/archive, roster membership changes, jersey updates, and season-window validation.
- **Players:** Administrator player profile create/read/update/archive/restore, with season voter eligibility recorded for adult roster additions.

The current ORM models are User, Role, Season, Sport, Division, SeasonSport, SeasonSportDivision, SeasonTeam, Player, Roster, and SeasonPlayerEligibility. Games, statistics, playoffs, reports, audit logging, idempotency storage, venues, and system settings remain planned.

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

## Current Alignment

This overview describes implemented behavior. The full Version 1 target and known gaps are recorded in [the implementation alignment tracker](implementation-alignment.md); the project roadmap is in [the checklist](../../checklist.md).
