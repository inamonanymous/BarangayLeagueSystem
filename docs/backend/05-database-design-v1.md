# Database Design

## Overview

This document defines the database structure of the League Management System.

The system is designed for deployment at the barangay level.

Each installation of the application represents a single barangay and may manage multiple league seasons over time.

The database is designed to support:

* Multi-season tournaments
* Multi-sport competitions
* Historical record preservation
* Configurable statistics
* Extensibility for future tournament formats

The system uses MySQL as its relational database.

> **Implementation status:** This document describes the Version 1 target schema, not the current live database. Implemented tables, migration state, and known gaps are tracked in [implementation-alignment.md](implementation-alignment.md). Current ORM models cover users, roles, seasons, sports, divisions, season associations, season teams, players, rosters, and season-player eligibility; later competition and reporting tables remain planned.

All entities shall use soft deletion through archival mechanisms instead of physical deletion.

---

# System Architecture

```text
One Installation
    =
One Barangay

One Barangay
    └── Multiple Seasons
            ├── Summer League 2026
            ├── Christmas League 2026
            └── Summer League 2027
```

---

# Core Aggregates

```text
Season
│
├── SeasonSport
├── SeasonSportDivision
├── SeasonTeam
└── Roster
```

```text
Player
│
└── SeasonPlayerEligibility
```

```text
Game
│
└── PlayerGameStatistic
```

```text
PlayoffBracket
│
└── PlayoffSeed
```

---

# 1. SystemSettings

Stores barangay and league information for the installation.

| Column         | Type         | Notes    |
| -------------- | ------------ | -------- |
| id             | BIGINT       | PK       |
| barangay_name  | VARCHAR(150) |          |
| municipality   | VARCHAR(150) |          |
| province       | VARCHAR(150) |          |
| address        | TEXT         |          |
| contact_number | VARCHAR(30)  | Nullable |
| created_at     | DATETIME     |          |
| updated_at     | DATETIME     |          |

Note:

* This table is expected to contain only one record.

---

# 2. Season

Represents a league season.

| Column                  | Type         | Notes                                                |
| ----------------------- | ------------ | ---------------------------------------------------- |
| id                      | BIGINT       | PK                                                   |
| name                    | VARCHAR(150) |                                                      |
| year                    | INT          |                                                      |
| registration_start_date | DATE         | Nullable; set with registration_end_date             |
| registration_end_date   | DATE         | Nullable; set with registration_start_date           |
| start_date              | DATE         | Nullable                                             |
| end_date                | DATE         | Nullable                                             |
| season_status                  | ENUM         | PLANNING, REGISTRATION, ONGOING, COMPLETED, ARCHIVED |
| created_at              | DATETIME     |                                                      |
| updated_at              | DATETIME     |                                                      |

Business Rules:

* New seasons are created in `PLANNING` status.
* Status changes follow `PLANNING` → `REGISTRATION` → `ONGOING` → `COMPLETED` → `ARCHIVED`; a planned season may also be archived.
* At most one season may be active at a time. `REGISTRATION` and `ONGOING` are active statuses.
* A new season may become active only after the current active season is completed or archived.
* Completed and archived seasons remain stored as historical records and are not deleted when a new season starts.

---

# 3. Sport

Master list of supported sports.

| Column      | Type         |
| ----------- | ------------ |
| id          | BIGINT       |
| name        | VARCHAR(100) |
| description | TEXT         |
| created_at  | DATETIME     |
| updated_at  | DATETIME     |

Examples:

```text
Basketball
Volleyball
```

---

# 4. Division

Reusable league divisions.

| Column              | Type         | Notes                              |
| ------------------- | ------------ | ---------------------------------- |
| id                  | BIGINT       | PK                                 |
| name                | VARCHAR(100) |                                    |
| gender_policy       | ENUM         | ANY, MALE_ONLY, FEMALE_ONLY, MIXED |
| minimum_roster_size | INT          |                                    |
| maximum_roster_size | INT          |                                    |
| created_at          | DATETIME     |                                    |
| updated_at          | DATETIME     |                                    |

Examples:

```text
Junior
Senior
Women's
Pro
```

---

# 5. SeasonSport

Represents a sport participating in a season.

| Column     | Type     |
| ---------- | -------- |
| id         | BIGINT   |
| season_id  | BIGINT   |
| sport_id   | BIGINT   |
| created_at | DATETIME |
| updated_at | DATETIME |

Examples:

```text
Summer League 2026 + Basketball
Summer League 2026 + Volleyball
```

---

# 6. SeasonSportDivision

Represents divisions available for a sport in a season.

| Column          | Type     |
| --------------- | -------- |
| id              | BIGINT   |
| season_sport_id | BIGINT   |
| division_id     | BIGINT   |
| created_at      | DATETIME |
| updated_at      | DATETIME |

Examples:

```text
Summer League 2026
Basketball
Senior Division
```

---

# 7. SeasonTeam

Represents a team participating in a specific season, sport, and division.

Teams are seasonal and are not permanent entities.

| Column                   | Type         | Notes    |
| ------------------------ | ------------ | -------- |
| id                       | BIGINT       | PK       |
| season_sport_division_id | BIGINT       | FK       |
| name                     | VARCHAR(150) |          |
| barangay                 | VARCHAR(150) |          |
| coach_name               | VARCHAR(150) | Nullable |
| manager_name             | VARCHAR(150) | Nullable |
| team_color               | VARCHAR(50)  | Nullable |
| created_at               | DATETIME     |          |
| updated_at               | DATETIME     |          |

Business Rules:

* Team names must be unique within a SeasonSportDivision.
* The same team name may exist in different sports.

Examples:

```text
Basketball -> Team Pogi
Volleyball -> Team Pogi
```

---

# 8. Player

Represents permanent player records.

| Column      | Type         |
| ----------- | ------------ |
| id          | BIGINT       |
| first_name  | VARCHAR(100) |
| middle_name | VARCHAR(100) |
| last_name   | VARCHAR(100) |
| birthdate   | DATE         |
| gender      | ENUM         |
| address     | TEXT         |
| created_at  | DATETIME     |
| updated_at  | DATETIME     |

Unique Constraint:

```text
(first_name, middle_name, last_name, birthdate)
```

---

# 9. SeasonPlayerEligibility

Stores season-specific eligibility information.

| Column            | Type         |
| ----------------- | ------------ |
| id                | BIGINT       |
| season_id         | BIGINT       |
| player_id         | BIGINT       |
| is_voter_verified | BOOLEAN      |
| voter_number      | VARCHAR(100) |
| verified_by       | BIGINT       |
| verified_at       | DATETIME     |
| notes             | TEXT         |
| created_at        | DATETIME     |
| updated_at        | DATETIME     |

Unique Constraint:

```text
(season_id, player_id)
```

Business Rules:

* Players aged 18 and above must be verified voters.
* Eligibility verification is season-specific.

---

# 10. Roster

Represents player participation in a seasonal team.

| Column         | Type        |
| -------------- | ----------- |
| id             | BIGINT      |
| season_team_id | BIGINT      |
| player_id      | BIGINT      |
| jersey_number  | VARCHAR(10) |
| created_at     | DATETIME    |
| updated_at     | DATETIME    |

Business Rules:

* One player may only belong to one team per sport per season.
* Jersey numbers are unique within a team.
* Rosters become locked when the season status becomes ONGOING.

---

# 11. Venue

Represents game venues.

| Column     | Type         |
| ---------- | ------------ |
| id         | BIGINT       |
| name       | VARCHAR(150) |
| address    | TEXT         |
| created_at | DATETIME     |
| updated_at | DATETIME     |

---

# 12. Game

Represents both regular season and playoff games.

| Column                   | Type     |
| ------------------------ | -------- |
| id                       | BIGINT   |
| season_sport_division_id | BIGINT   |
| team_a_id                | BIGINT   |
| team_b_id                | BIGINT   |
| venue_id                 | BIGINT   |
| scheduled_at             | DATETIME |
| stage                    | ENUM     |
| status                   | ENUM     |
| team_a_score             | INT      |
| team_b_score             | INT      |
| overtime_count           | INT      |
| finalized_at             | DATETIME |
| finalized_by             | BIGINT   |
| created_at               | DATETIME |
| updated_at               | DATETIME |

## Game Stages

```text
REGULAR_SEASON
QUARTER_FINAL
SEMI_FINAL
THIRD_PLACE
FINAL
```

## Game Statuses

```text
SCHEDULED
FOR_ENCODING
FINALIZED
POSTPONED
CANCELLED
```

Business Rules:

* Games always involve exactly two teams.
* Only FINALIZED games affect standings and statistics.

---

# 13. StatisticType

Configurable statistics per sport.

| Column       | Type         |
| ------------ | ------------ |
| id           | BIGINT       |
| sport_id     | BIGINT       |
| name         | VARCHAR(100) |
| abbreviation | VARCHAR(20)  |
| created_at   | DATETIME     |
| updated_at   | DATETIME     |

Examples:

```text
PTS
REB
AST

KILLS
ACES
DIGS
```

---

# 14. PlayerGameStatistic

Stores player statistics for a game.

| Column            | Type          |
| ----------------- | ------------- |
| id                | BIGINT        |
| game_id           | BIGINT        |
| player_id         | BIGINT        |
| statistic_type_id | BIGINT        |
| value             | DECIMAL(10,2) |
| created_at        | DATETIME      |
| updated_at        | DATETIME      |

---

# 15. PlayoffBracket

Represents playoff tournaments.

| Column                   | Type         |
| ------------------------ | ------------ |
| id                       | BIGINT       |
| season_sport_division_id | BIGINT       |
| name                     | VARCHAR(100) |
| format                   | ENUM         |
| created_at               | DATETIME     |
| updated_at               | DATETIME     |

Format Examples:

```text
SINGLE_ELIMINATION
DOUBLE_ELIMINATION
BEST_OF_N
```

Only SINGLE_ELIMINATION is supported in Version 1.

---

# 16. PlayoffSeed

Stores playoff team seedings.

| Column             | Type   |
| ------------------ | ------ |
| id                 | BIGINT |
| playoff_bracket_id | BIGINT |
| season_team_id     | BIGINT |
| seed_number        | INT    |

Business Rules:

* Seeding is manually assigned by administrators.
* Teams without seeds are considered eliminated from playoff contention.

---

# 17. Role

Represents system roles.

| Column      | Type         |
| ----------- | ------------ |
| id          | BIGINT       |
| name        | VARCHAR(100) |
| description | TEXT         |

Examples:

```text
Administrator
Encoder
Viewer
```

---

# 18. User

Represents system users.

| Column        | Type         |
| ------------- | ------------ |
| id            | BIGINT       |
| username      | VARCHAR(100) |
| password_hash | VARCHAR(255) |
| role_id       | BIGINT       |
| is_active     | BOOLEAN      |
| created_at    | DATETIME     |
| updated_at    | DATETIME     |

Business Rules:

* Players cannot log in.
* Only authorized system users may access the application.

---

# 19. AuditLog

Tracks important system activities.

| Column      | Type         |
| ----------- | ------------ |
| id          | BIGINT       |
| user_id     | BIGINT       |
| action      | VARCHAR(100) |
| entity_type | VARCHAR(100) |
| entity_id   | BIGINT       |
| old_values  | JSON         |
| new_values  | JSON         |
| created_at  | DATETIME     |

Examples:

```text
CREATE
UPDATE
ARCHIVE
FINALIZE
REOPEN
```

---

# 20. ApiRequest

Stores processed idempotent API requests.

This table enables the system to safely handle duplicate requests caused by:

* User double-clicks
* Browser retries
* Network interruptions
* Frontend request retries
* Accidental resubmissions

The table acts as the backend idempotency store.

| Column          | Type         | Notes                     |
| --------------- | ------------ | ------------------------- |
| id              | BIGINT       | PK                        |
| idempotency_key | VARCHAR(255) | Unique, Required          |
| request_method  | VARCHAR(20)  | HTTP Method               |
| request_path    | VARCHAR(255) | API endpoint path         |
| request_hash    | VARCHAR(255) | Hash of request payload   |
| response_status | INT          | HTTP response status code |
| response_body   | JSON         | Serialized response body  |
| user_id         | BIGINT       | FK → User, Nullable       |
| created_at      | DATETIME     |                           |
| expires_at      | DATETIME     | Nullable                  |

## Unique Constraint

```text
(idempotency_key)
```

## Business Rules

* Every idempotent request must provide a unique `Idempotency-Key`.
* If the same key is received again, the previously stored response shall be returned.
* Duplicate requests must not execute business logic more than once.
* Only successful requests (HTTP 2xx) shall be stored by default.
* Keys may expire after a configurable retention period (recommended: 24 hours).
* Requests with the same idempotency key but different payloads shall be rejected.

## Example

Request:

```http
POST /api/v1/players

Idempotency-Key: 2b19e638-7b76-4dcb-9e1d-f2f8c0b3e8ea
```

Response:

```json
{
    "message": "Player created successfully.",
    "data": {
        "id": 15
    }
}
```

If the frontend sends the same request again using the same key:

```http
POST /api/v1/players

Idempotency-Key: 2b19e638-7b76-4dcb-9e1d-f2f8c0b3e8ea
```

The backend shall return the previously stored response without creating a duplicate player.

--

# Soft Deletion Strategy

Major entities shall support archival.

Recommended columns:

```text
is_archived BOOLEAN
archived_at DATETIME
archived_by BIGINT
```

Applicable entities:

* Season
* SeasonTeam
* Player
* Venue
* Sport
* Division

---

# Computed Data

The following information shall be computed dynamically and shall not be stored in the database:

* Team standings
* Win-loss records
* Career statistics
* Season statistics
* Leaderboards

The source of truth shall always be FINALIZED games.

---

# Aggregate Roots

```text
Season
Player
Game
PlayoffBracket
User
Venue
SystemSettings
AuditLog
```
