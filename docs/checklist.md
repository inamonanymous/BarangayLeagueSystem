# Project Roadmap

Last reviewed: 2026-11-13

This roadmap describes the current implementation and proposed next milestones. `[x]` means implemented, `[~]` means partial, and `[ ]` means planned. Design documents may describe features that are not implemented; see the [alignment tracker](backend/implementation-alignment.md) for known differences.

## Current progress

- [x] Flask API, React frontend, SQLAlchemy, migrations, and test setup.
- [x] Session login/logout and current-user lookup.
- [~] Users and roles: role checks and Administrator-created users exist; account management remains.
- [~] Seasons, sports, and divisions: lifecycle, catalogs, and season assignments exist; stronger database enforcement and usability work remain.
- [~] Players and eligibility: player CRUD/archive and adult voter verification exist; an independent voter-registration source and division eligibility rules remain unresolved.
- [~] Teams and rosters: registration, edits, archive/restore, roster management, and the minimum-roster gate before Ongoing exist. Team archive behavior after registration remains a policy decision.
- [x] Guided division-to-team-to-roster frontend, roster-readiness indicators, and development demo data.
- [~] Dashboard: basic account dashboard exists; league reporting is planned.

## Proposed implementation order

1. **Complete and validate a test season**
   - [ ] Resolve incomplete team rosters before moving the season to Ongoing.
   - [ ] Decide post-registration team archive behavior and document outstanding eligibility rules.
2. **Manual game scheduling**
   - [ ] Agree on when scheduling is allowed, venue requirements, conflict rules, and whether Rounds belong in V1.
   - [ ] Add the necessary database migrations, backend models, policies, services, API, and tests.
   - [ ] Add a schedule creation and listing interface.
3. **Results and standings**
   - [ ] Record and finalize game scores; define correction/reopening rules.
   - [ ] Calculate and display standings from finalized games.
4. **Later competition features**
   - [ ] Player statistics, playoffs, dashboard reporting, and venues as needed by the agreed scheduling design.

## Foundation and documentation

- [x] Project overview, features, roles, workflows, business rules, database design, ERD, architecture, tech stack, and API specification documents.
- [x] Frontend overview, architecture, and route reference.
- [x] Use-case and component diagrams.
- [ ] Frontend coding standards and activity/sequence diagrams.
- [ ] Logging, persistent API idempotency, and broader reusable frontend components.
- [ ] Reconcile the planned API and design documents with implemented behavior as features change.

## Testing and release readiness

- [~] Unit and API integration tests cover implemented features; broader end-to-end testing remains.
- [ ] Functional and regression testing of complete league workflows.
- [ ] Resolve the fresh-database migration and first-administrator bootstrap gaps.
- [ ] Enforce the one-active-season rule safely under concurrent requests.
- [ ] Review soft-delete, eligibility, and production configuration decisions.
- [ ] Remove tracked runtime/session files and generated dependencies; add appropriate ignore rules before publishing.
- [ ] Production database, deployment, operational documentation, and V1 release.

See the [backend checklist](backend/checklist.md) for a backend-focused breakdown.
