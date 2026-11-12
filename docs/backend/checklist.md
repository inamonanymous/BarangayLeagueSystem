# Backend Checklist

Last reviewed: 2026-11-13

`[x]` implemented; `[~]` partial; `[ ]` planned. The [alignment tracker](implementation-alignment.md) explains the remaining gaps.

## Foundation

- [x] Flask app, configuration, SQLAlchemy, Flask-Migrate, Marshmallow, and API response helpers.
- [x] Session authentication and role-based authorization for administrative actions.
- [~] Migration chain: existing development databases can be migrated, but the initial migration requires a legacy `users` table.
- [ ] Supported clean-database and initial Administrator bootstrap.
- [ ] Structured logging, persistent idempotency, and production deployment configuration.
- [ ] Swagger/OpenAPI and Docker, if adopted for the project.

## Implemented features

- [~] Users and roles: create users and enforce roles; list/edit/activation/password reset remain.
- [~] Seasons: create, list, status transitions, date validation, and roster readiness; concurrency enforcement remains.
- [x] Sport and division catalogs and season-specific assignments.
- [~] Season teams: register, list, edit, archive, and restore; decide post-registration archive policy.
- [~] Players and rosters: player CRUD/archive and roster add/list/update/remove, including adult voter verification; division eligibility policy is not fully defined.
- [x] Demo team/player seed and read-only post-seed verification for development.

## Planned features

- [ ] Game scheduling and schedule conflict validation.
- [ ] Venues and Rounds, subject to the scheduling and V1 design decisions.
- [ ] Game results, finalization and corrections.
- [ ] Standings and player statistics.
- [ ] Playoffs, audit logs, and reports.
- [ ] Independent voter-registration source, if required by the agreed policy.

## Verification and release

- [~] Unit and API integration tests exist for implemented slices; full workflow coverage remains.
- [ ] Functional and regression testing across a complete season.
- [ ] Database-level protection against concurrent active seasons.
- [ ] Resolve fresh-install migrations, soft-delete, eligibility, and other issues in the [alignment tracker](implementation-alignment.md).
- [ ] Remove tracked runtime/session files and dependencies, configure production, and document deployment.
