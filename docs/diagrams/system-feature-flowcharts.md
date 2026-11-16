# Barangay League System: Current Feature Flowcharts

Reviewed against the code on 2026-11-16. These diagrams describe the **current
implementation**, not the complete planned Version 1 design. Solid arrows
represent existing behavior; planned features are listed separately at the end.
They are a guide to reading and extending the code, not a substitute for tests.

The diagrams below use Mermaid. GitHub renders Mermaid blocks; in VS Code, use
a Markdown preview with Mermaid support. A diamond is a decision, a rectangle
is an action, and an arrow shows the next step.

## PlantUML flowcharts for VS Code

Install the PlantUML extension for VS Code if needed, then open a `.puml` file
below and use **Preview Current Diagram** (usually `Alt+D`). Configure the
extension to render **locally** with Java and, when needed, Graphviz; do not use
a remote rendering server for private project files. Each diagram stands alone.
The descriptions and code links in this guide explain the rules and limitations
in more detail.

| PlantUML diagram | Guide |
| --- | --- |
| [01 System overview](flowcharts/01-system-overview.puml) | [System overview](#1-system-overview) |
| [02 Request layers](flowcharts/02-request-layers.puml) | [Request flow](#2-how-a-request-travels-through-the-code) |
| [03 Login and authorization](flowcharts/03-login-and-authorization.puml) | [Login and protected actions](#login-and-protected-actions) |
| [04 Create a user](flowcharts/04-create-user.puml) | [Create a user](#create-a-user) |
| [05 Season lifecycle](flowcharts/05-season-lifecycle.puml) | [Creation and status transitions](#creation-and-status-transitions) |
| [06 Ongoing readiness](flowcharts/06-ongoing-readiness.puml) | [Before moving to Ongoing](#before-moving-to-ongoing) |
| [07 Catalogs](flowcharts/07-catalogs.puml) | [Sport and division catalogs](#5-sport-and-division-catalogs) |
| [08 Season assignments](flowcharts/08-season-assignments.puml) | [Assign sports and divisions](#6-assign-sports-and-divisions-to-a-season) |
| [09 Team registration](flowcharts/09-team-registration.puml) | [Register and edit](#register-and-edit) |
| [10 Team archive and restore](flowcharts/10-team-archive-restore.puml) | [Archive and restore](#archive-and-restore) |
| [11 Player profiles](flowcharts/11-player-profiles.puml) | [Player profile management](#8-player-profile-management) |
| [12 Available players](flowcharts/12-available-players.puml) | [Available-player picker](#9-available-player-picker) |
| [13 Add a roster player](flowcharts/13-add-roster-player.puml) | [Add a player to a roster](#10-add-a-player-to-a-roster) |
| [14 Edit or remove a roster entry](flowcharts/14-edit-remove-roster.puml) | [Edit or remove a roster entry](#11-edit-or-remove-a-roster-entry) |
| [15 Schedule a game](flowcharts/15-schedule-game.puml) | [Schedule a game](#12-schedule-a-game) |
| [16 Reschedule a game](flowcharts/16-reschedule-game.puml) | [Reschedule a game](#13-reschedule-a-game) |
| [17 Frontend query cache](flowcharts/17-frontend-query-cache.puml) | [Frontend selection and query cache](#14-frontend-selection-and-query-cache) |
| [18 Data relationships](flowcharts/18-data-relationships.puml) | [Main data relationships](#15-main-data-relationships) |
| [19 Planned features (not implemented)](flowcharts/19-planned-features.puml) | [Planned features and known boundaries](#17-planned-features-and-known-boundaries) |

## 1. System overview

This is a typical administrator workflow, not a claim that every arrow is an
enforced prerequisite. Public visitors can read the season, catalog, team,
roster, and game lists without logging in.

```mermaid
flowchart TD
    A["Open the React application"] --> B{"What does the visitor need?"}
    B -->|"Read public information"| C["View seasons, configuration, teams, rosters, or games"]
    B -->|"Perform an administrative action"| D["Sign in as an Administrator"]
    D --> E["Create a season in Planning"]
    E --> F["Create or choose sports and divisions"]
    F --> G["Assign sports and divisions to the season"]
    G --> H["Move season to Registration"]
    H --> I["Create player profiles and register teams"]
    I --> J["Assign players to team rosters"]
    J --> K["Request transition to Ongoing"]
    K --> L{"Active teams meet roster minimums?"}
    L -->|"No"| J
    L -->|"Yes and transition allowed"| M["Schedule and reschedule games"]
    M --> N["Complete, then archive the season"]
    C --> O["Display API data"]
```

**Important:** The current Ongoing check does not require the season to have at
least one team. If there are active teams, each must meet its division minimum.
Player profiles can also be created independently of this sequence.

## 2. How a request travels through the code

```mermaid
flowchart LR
    UI["React page or component"] --> CLIENT["Axios API function"]
    CLIENT --> ROUTE["Flask route"]
    ROUTE --> AUTH{"Protected action?"}
    AUTH -->|"Yes"| CHECK["Check session, active user, and role"]
    AUTH -->|"No"| SCHEMA["Validate JSON with schema when needed"]
    CHECK -->|"Allowed"| SCHEMA
    CHECK -->|"Denied"| ERROR["Return an error"]
    SCHEMA --> SERVICE["Application service"]
    SERVICE --> POLICY["Policy checks where used"]
    SERVICE --> REPO["Repository queries where used"]
    POLICY --> SERVICE
    REPO --> MODEL["SQLAlchemy models and database"]
    SERVICE --> MODEL
    MODEL --> RESPONSE["Response returned to the frontend"]
    SERVICE -->|"Rejected"| ERROR
```

This is a map of responsibilities, not a claim that every request uses every
box. The implemented feature services use policies and repositories for their
applicable rules and queries. Services still coordinate checks, model changes,
and transactions; not every request needs each layer.

## 3. Login, authorization, and user creation

### Login and protected actions

```mermaid
flowchart TD
    A["Submit username and password"] --> B["Auth route calls AuthService"]
    B --> C["Repository looks up user"]
    C --> D{"Password correct and account active?"}
    D -->|"No"| E["Reject login"]
    D -->|"Yes"| F["Store user ID, username, and role in session"]
    F --> G["Frontend requests current user"]
    G --> H{"Administrator action requested?"}
    H -->|"No"| I["Use public endpoint or other applicable access rule"]
    H -->|"Yes"| J["Decorator reloads the active user"]
    J --> K{"User is an Administrator?"}
    K -->|"No"| L["Return authentication or permission error"]
    K -->|"Yes"| M["Run the protected route"]
    F --> N["Logout clears the session"]
```

Administrator, Encoder, and Viewer are supported roles. The currently
implemented management mutations use administrator checks; game results and
statistics entry are **not implemented**. Public roster listings include player
data, while the player-profile management endpoints require an Administrator.

### Create a user

```mermaid
flowchart TD
    A["Administrator submits username, password, and role"] --> B["Route checks session and validates input"]
    B --> C["UserService checks username, password, role, and duplicates"]
    C --> D{"Valid and available?"}
    D -->|"No"| E["Return an error"]
    D -->|"Yes"| F["Find or create supported role"]
    F --> G["Hash password and create active user"]
    G --> H["Commit and return user details"]
```

The system does not yet provide user listing, password reset, or a supported
first-administrator bootstrap.

## 4. Season creation and lifecycle

### Creation and status transitions

```mermaid
flowchart TD
    A["Administrator creates season"] --> B["Validate name, year, dates, and duplicate name"]
    B --> C["Save with PLANNING status"]
    C --> D["PLANNING"]
    D -->|"Open registration"| E["REGISTRATION"]
    D -->|"Archive early"| H["ARCHIVED"]
    E -->|"Request start"| F["ONGOING"]
    E -->|"Archive early"| H
    F -->|"Complete"| G["COMPLETED"]
    G -->|"Archive"| H
```

Only the shown transitions are supported. Opening Registration or moving to
Ongoing checks whether another season is already in Registration or Ongoing.
That check is application-level and is **not safe against all concurrent
activation requests**.

### Before moving to Ongoing

```mermaid
flowchart TD
    A["Administrator requests ONGOING"] --> B["Check transition and other active seasons"]
    B --> C{"Checks passed?"}
    C -->|"No"| X["Reject transition"]
    C -->|"Yes"| D["Find each non-archived team in the season"]
    D --> E["Count roster entries whose player profiles are active"]
    E --> F{"Every active team meets its division minimum?"}
    F -->|"No"| G["Return incomplete team names and counts"]
    F -->|"Yes"| H["Set season to ONGOING and commit"]
```

Archived teams and archived player profiles are excluded from this readiness
count. There is currently no explicit minimum-team requirement.

## 5. Sport and division catalogs

```mermaid
flowchart TD
    A["Administrator creates or edits a catalog item"] --> B{"Sport or division?"}
    B -->|"Sport"| C["Validate name and optional description"]
    B -->|"Division"| D["Validate name, gender policy, and roster limits"]
    C --> E{"Duplicate name?"}
    D --> E
    E -->|"Yes"| F["Reject"]
    E -->|"No"| G["Save shared catalog record"]
    H["Administrator deletes catalog item"] --> I{"Item assigned to a season?"}
    I -->|"Yes"| J["Reject deletion"]
    I -->|"No"| K["Delete unused catalog record"]
```

Catalog records are shared. Editing a catalog item can change what existing
season configurations display. Division gender policy is stored, but gender
eligibility is not yet enforced when adding players.

## 6. Assign sports and divisions to a season

```mermaid
flowchart TD
    A["Administrator chooses a season"] --> B{"Season is Planning or Registration?"}
    B -->|"No"| X["Reject assignment change"]
    B -->|"Yes"| C["Assign an existing sport to the season"]
    C --> D{"Sport already assigned?"}
    D -->|"Yes"| X
    D -->|"No"| E["Save SeasonSport link"]
    E --> F["Assign an existing division to that sport"]
    F --> G{"Division already assigned to this sport?"}
    G -->|"Yes"| X
    G -->|"No"| H["Save SeasonSportDivision link"]
    H --> I["Register teams against this division assignment"]
    J["Remove a sport or division assignment"] --> K{"Assignment has registered teams?"}
    K -->|"Yes"| X
    K -->|"No"| L["Remove assignment link, not the catalog record"]
```

The removal check includes teams associated with the assignment; it is not
limited to active teams. Removing a sport link also removes its division links
when none of them has teams.

## 7. Team registration and management

### Register and edit

```mermaid
flowchart TD
    A["Administrator selects a season division"] --> B["Enter team and barangay details"]
    B --> C["Route validates the request"]
    C --> D{"Assignment and season exist?"}
    D -->|"No"| X["Reject"]
    D -->|"Yes"| E{"Registration status and date window allow changes?"}
    E -->|"No"| X
    E -->|"Yes"| F["Normalize team details"]
    F --> G{"Team name already exists in this division?"}
    G -->|"Yes"| X
    G -->|"No"| H["Save SeasonTeam and refresh team list"]
```

The registration window is inclusive when both dates are set; when both are
empty, Registration status alone controls the window. Editing additionally
requires the team not to be archived. Name checks include archived teams.

### Archive and restore

```mermaid
flowchart TD
    A["Administrator chooses archive or restore"] --> S{"Season in Registration?"}
    S -->|"No"| E["Reject"]
    S -->|"Yes"| B{"Action"}
    B -->|"Archive"| C["Set archived flag and record actor and time"]
    B -->|"Restore an archived team"| D{"Registration window permits restore?"}
    D -->|"No"| E["Reject restore"]
    D -->|"Yes"| H{"Any player on another active team in the same sport and season?"}
    H -->|"Yes"| I["Reject with conflict details"]
    H -->|"No"| F["Clear archive flag and archive metadata"]
    C --> G["Commit and refresh teams and available-player data"]
    F --> G
```

Archiving is allowed throughout Registration, even outside the date window.
Restoring requires the window to be open when dates are configured. A conflict
returns HTTP 409 with the player and other team; remove the player from the
other team before restoring. Roster additions and archive/restore operations
share a season-sport lock during their checks and writes.

## 8. Player profile management

```mermaid
flowchart TD
    A["Administrator opens Players"] --> B{"Action"}
    B -->|"Create or edit"| C["Validate and normalize name, birthdate, gender, and address"]
    C --> D{"Duplicate identity or invalid input?"}
    D -->|"Yes"| E["Reject"]
    D -->|"No"| F["Create or update player profile"]
    B -->|"Archive or restore"| G["Update archive flag, actor, and timestamp"]
    F --> H["Commit and refresh affected queries"]
    G --> H
```

The duplicate check uses first, middle and last name plus birthdate. An archived
profile must be restored before it can be edited. Archiving preserves roster
links; an archived player is excluded from active roster readiness and the
available-player list.

## 9. Available-player picker

```mermaid
flowchart TD
    A["Administrator opens the selected active team's roster"] --> B["GET available players for team"]
    B --> C{"Team exists and is not archived?"}
    C -->|"No"| D["Return an error"]
    C -->|"Yes"| E["Find the team's season and sport"]
    E --> F["Start with active player profiles"]
    F --> G["Exclude players assigned to an active team in the same sport and season"]
    G --> H["Return remaining players to the dropdown"]
```

An assignment in another sport or season does not block the player. A roster
link to an archived team does not block availability. The dropdown is only a
convenience: the add-player service checks the rules again on submission.

## 10. Add a player to a roster

```mermaid
flowchart TD
    A["Administrator submits player, jersey, and voter details"] --> B["Route checks administrator and validates JSON"]
    B --> C{"Team active and Registration window open?"}
    C -->|"No"| X["Reject"]
    C -->|"Yes"| D{"Player exists and profile is active?"}
    D -->|"No"| X
    D -->|"Yes"| E["Normalize jersey number"]
    E --> F{"Already on team or another active team in same sport and season?"}
    F -->|"Yes"| X
    F -->|"No"| G{"Jersey already used or roster at maximum?"}
    G -->|"Yes"| X
    G -->|"No"| H{"Player is 18 or older today?"}
    H -->|"Yes"| I{"Voter verified and voter number supplied?"}
    I -->|"No"| X
    I -->|"Yes"| J["Create or update season eligibility record"]
    H -->|"No"| K["Create roster link"]
    J --> K
    K --> L["Commit roster and eligibility changes"]
    L --> M["Refresh roster and available-player queries"]
```

Adult verification is entered by the administrator; there is no independent
voter-registration lookup. The service requires the verification checkbox and
number on each adult add request, even if an eligibility record already exists.
Age and registration-window checks use the server's current date.
The [roster service](../../backend/app/application/rosters/services.py) obtains
records and coordinates persistence, while the
[roster policy](../../backend/app/application/rosters/policies.py) validates
player, team, conflict, capacity, and voter requirements. The
[team policy](../../backend/app/application/teams/policies.py) checks the
registration window. The [roster repository](../../backend/app/infrastructure/database/roster_repository.py)
handles ORM changes and supplies typed data to the service. Its
[transaction wrapper](../../backend/app/infrastructure/database/unit_of_work.py)
commits both writes together or rolls them back on failure.

## 11. Edit or remove a roster entry

```mermaid
flowchart TD
    A["Administrator selects a roster entry"] --> B{"Team active and Registration window open?"}
    B -->|"No"| X["Reject"]
    B -->|"Yes"| C{"Action"}
    C -->|"Edit jersey"| D["Normalize number and check uniqueness within the team"]
    D --> E{"Valid and unused?"}
    E -->|"No"| X
    E -->|"Yes"| F["Save new jersey number"]
    C -->|"Remove player"| G["Delete roster link"]
    F --> H["Commit and refresh roster"]
    G --> I["Keep player profile and eligibility record"]
    I --> J["Commit and refresh roster and available players"]
```

## 12. Schedule a game

```mermaid
flowchart TD
    A["Administrator enters teams, venue, start, and end"] --> B["Route checks administrator and schema"]
    B --> C["Validate venue and local whole-second times"]
    C --> D{"Two different teams and end after start?"}
    D -->|"No"| X["Reject"]
    D -->|"Yes"| E["Acquire singleton schedule lock"]
    E --> F{"Season Ongoing and teams active in the selected division?"}
    F -->|"No"| X
    F -->|"Yes"| G["Check overlapping team or normalized venue bookings"]
    G --> H{"Overlap found?"}
    H -->|"Yes"| I["Roll back and return conflict"]
    H -->|"No"| J["Create game and commit"]
    J --> K["Refresh division game list"]
```

Times are stored as local datetimes without a timezone offset or fractional
seconds. Venue comparison normalizes whitespace and case. Adjacent intervals
are allowed. The venue check applies across all games, including games in other
divisions or seasons. Current game creation does **not** require a future start.

## 13. Reschedule a game

```mermaid
flowchart TD
    A["Administrator selects Reschedule"] --> B["Form preloads existing venue, start, and end"]
    B --> C["Submit venue and times without changing teams"]
    C --> D["Route checks administrator and schema"]
    D --> E["Validate venue and local whole-second times"]
    E --> F["Acquire singleton schedule lock and load game"]
    F --> G{"Season Ongoing and original start still in future?"}
    G -->|"No"| X["Reject and roll back"]
    G -->|"Yes"| H{"New start is in the future?"}
    H -->|"No"| X
    H -->|"Yes"| I["Check team and venue overlaps, excluding this game"]
    I --> J{"Overlap found?"}
    J -->|"Yes"| K["Roll back and return conflict"]
    J -->|"No"| L["Update venue and times, then commit"]
    L --> M["Refresh division game list"]
```

Both future-time checks use the **server's local clock**. They do not convert
between timezones, so deployments must account for the server and users'
expected local time. Rescheduling retains the existing teams; it does not
revalidate their current archive status.

## 14. Frontend selection and query cache

```mermaid
flowchart TD
    A["Open season configuration"] --> B["Load season configuration and catalogs"]
    B --> C["Select sport and division tabs"]
    C --> D["Enable teams and game queries for selected division"]
    D --> E["Select team tab"]
    E --> F["Enable roster query for selected team"]
    F --> G{"Administrator can edit roster?"}
    G -->|"Yes"| H["Enable available-player query"]
    G -->|"No"| I["Show read-only roster"]
    H --> J["Reuse fresh cached data while switching tabs"]
    I --> J
    J --> K{"Relevant mutation or Refresh data?"}
    K -->|"Yes"| L["Invalidate affected queries and reload active data"]
    K -->|"No"| M["Reuse data until it becomes stale"]
    M --> N["A later selection, page return, or browser refocus can refetch"]
```

Season-page data has a one-minute freshness period. Expiry itself is not a
polling timer: updates made elsewhere are not pushed live. **Refresh data**
checks immediately; a browser reload starts a new in-memory cache. Hidden tab
panels stay mounted to preserve drafts, but their queries are disabled.

## 15. Main data relationships

This is a learning map, not a complete entity-relationship diagram.

```mermaid
flowchart TD
    S["Season"] --> SS["SeasonSport"]
    SP["Sport catalog"] --> SS
    SS --> SD["SeasonSportDivision"]
    DI["Division catalog"] --> SD
    SD --> T["SeasonTeam"]
    T --> R["Roster"]
    P["Player profile"] --> R
    S --> EL["SeasonPlayerEligibility"]
    P --> EL
    SD --> G["Game"]
    T -->|"home team"| G
    T -->|"away team"| G
    LOCK["Singleton ScheduleLock"] -->|"serializes schedule writes"| G
```

Removing a roster entry deletes the team-player link, not the player profile.
Eligibility is stored separately for a player and season.

## 16. Where to read and build each feature

All paths below are links to the current source, not proposed files.

| Feature | Route | Service and rules | Storage / tests |
| --- | --- | --- | --- |
| Authentication | [Auth routes](../../backend/app/api/v1/auth/routes.py) | [Auth service](../../backend/app/application/auth/services.py), [auth policy](../../backend/app/application/auth/policies.py), [authorization decorator](../../backend/app/application/common/decorators/authorization.py) | [User repository](../../backend/app/infrastructure/database/user_repository.py) |
| User creation | [User routes](../../backend/app/api/v1/users/routes.py) | [User service](../../backend/app/application/users/services.py) | [User model](../../backend/app/domain/models/users.py) |
| Seasons | [Season routes](../../backend/app/api/v1/seasons/routes.py) | [Season service](../../backend/app/application/season/services.py), [season policy](../../backend/app/application/season/policies.py) | [Season repository](../../backend/app/infrastructure/database/season_repository.py) |
| Catalogs and assignments | [Catalog routes](../../backend/app/api/v1/catalogs/routes.py), [season routes](../../backend/app/api/v1/seasons/routes.py) | [Catalog service](../../backend/app/application/catalogs/services.py), [catalog policy](../../backend/app/application/catalogs/policies.py) | [Catalog repository](../../backend/app/infrastructure/database/catalog_repository.py) |
| Teams | [Team routes](../../backend/app/api/v1/teams/routes.py) | [Team service](../../backend/app/application/teams/services.py), [team policy](../../backend/app/application/teams/policies.py) | [Team repository](../../backend/app/infrastructure/database/season_team_repository.py) |
| Players | [Player routes](../../backend/app/api/v1/players/routes.py) | [Player service](../../backend/app/application/players/services.py), [player policy](../../backend/app/application/players/policies.py) | [Player repository](../../backend/app/infrastructure/database/player_repository.py) |
| Rosters | [Team and roster routes](../../backend/app/api/v1/teams/routes.py) | [Roster service](../../backend/app/application/rosters/services.py), [roster policy](../../backend/app/application/rosters/policies.py), [team policy](../../backend/app/application/teams/policies.py) | [Roster repository](../../backend/app/infrastructure/database/roster_repository.py), [roster tests](../../backend/tests/test_players_rosters_api.py) |
| Games | [Game routes](../../backend/app/api/v1/games/routes.py), [game schemas](../../backend/app/schemas/game_schema.py) | [Game service](../../backend/app/application/games/services.py), [game policy](../../backend/app/application/games/policies.py) | [Game repository](../../backend/app/infrastructure/database/game_repository.py), [game model](../../backend/app/domain/models/games.py), [game tests](../../backend/tests/test_games_api.py) |
| Frontend | [Application routes](../../frontend/src/App.tsx) | [Season configuration](../../frontend/src/features/seasons/SeasonConfigurationPage.tsx), [team section](../../frontend/src/features/seasons/SeasonTeamsSection.tsx), [roster section](../../frontend/src/features/seasons/TeamRosterSection.tsx), [schedule section](../../frontend/src/features/seasons/DivisionScheduleSection.tsx) | [Season API client](../../frontend/src/shared/api/seasons.ts), [tab component](../../frontend/src/shared/components/SelectionTabs.tsx) |

### Suggested way to implement a new feature

1. Write down the actor, inputs, allowed states, failure cases, and expected
   result. Decide unresolved rules before coding.
2. Add focused tests for a successful request and important rejected cases.
3. Add or change the model and a **new** migration only if persistence changes.
4. Implement validation and business logic in the existing appropriate layer.
   Use policies for business rules and repositories for queries; keep
   orchestration and transaction boundaries in the service.
5. Add the schema and route, including authorization and explicit errors.
6. Connect the API client and UI; invalidate the relevant cached queries.
7. Run the focused tests and frontend build, then trace a real request through
   each layer. Do not edit an already-applied migration.

## 17. Planned features and known boundaries

These are **not implemented flows**. Their rules still need decisions and tests:

```mermaid
flowchart LR
    A["Current: schedule and reschedule games"] -.-> B["Planned: cancellation rules"]
    A -.-> C["Planned: record and finalize results"]
    C -.-> D["Planned: standings"]
    D -.-> E["Planned: statistics and playoffs"]
    A -.-> F["Decide managed venues and rounds"]
```

Other known gaps include a clean-database migration and first-administrator
bootstrap, stronger concurrent active-season enforcement, division eligibility
rules, and repository cleanup before publishing. See the [project roadmap](../checklist.md)
and [implementation alignment tracker](../backend/implementation-alignment.md).
