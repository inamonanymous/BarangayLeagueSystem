# Architecture Design

## Overview

This document defines the software architecture of the League Management System.

The system follows a layered architecture designed to provide:

* Maintainability
* Testability
* Separation of concerns
* Scalability
* Simplicity for solo development

The architecture intentionally avoids unnecessary enterprise complexity while still adhering to professional software engineering practices.

---

# Architectural Principles

The system shall adhere to the following principles:

* Separation of Concerns
* Single Responsibility Principle
* Dependency Inversion Principle
* Feature-based organization
* Thin Controllers
* Thin Services
* Explicit Transactions
* API-First Design

---

# High-Level Architecture

```text
React Frontend
        ↓
REST API (HTTP/JSON)
        ↓
Flask Backend
        ↓
MySQL Database
```

---

# Backend Architecture

The backend shall follow the following flow:

```text
Route
    ↓
Application Service
    ↓
Policy
    ↓
Repository
    ↓
SQLAlchemy Model
```

---

# Layer Responsibilities

## Route Layer

Responsibilities:

* Receive HTTP requests.
* Validate request payloads using schemas.
* Invoke application services.
* Transform responses into HTTP responses.
* Return standardized API responses.

Routes shall NOT:

* Contain business logic.
* Access repositories directly.
* Manage transactions.

Example:

```python
@player_bp.post("/")
def create_player():
    dto = CreatePlayerRequestSchema().load(request.json)

    player = create_player_service.execute(dto)

    return success_response(
        data=PlayerResponseSchema().dump(player),
        message="Player created successfully."
    )
```

---

## Application Service Layer

Responsibilities:

* Orchestrate use cases.
* Coordinate repositories.
* Invoke policies.
* Manage transactions.
* Coordinate multiple aggregates.

Services shall NOT:

* Contain extensive business validation.
* Perform HTTP operations.

Examples:

```text
CreateSeasonService
RegisterTeamService
AddPlayerToRosterService
FinalizeGameService
CreatePlayoffBracketService
```

Example:

```python
class AddPlayerToRosterService:

    def execute(self, request):

        team = self.team_repository.get_by_id(request.team_id)

        player = self.player_repository.get_by_id(
            request.player_id
        )

        self.roster_policy.validate_add_player(
            team=team,
            player=player
        )

        roster = Roster(...)

        with self.uow:
            self.roster_repository.add(roster)
            self.uow.commit()

        return roster
```

---

## Policy Layer

Policies encapsulate business rules.

Responsibilities:

* Validate business rules.
* Protect aggregate invariants.

Policies shall:

* Be stateless.
* Be pure.
* Not perform database access.

Examples:

```text
SeasonPolicy
RosterPolicy
EligibilityPolicy
GamePolicy
```

Example:

```python
class RosterPolicy:

    def validate_add_player(
        self,
        team,
        player,
        division
    ):

        if team.is_roster_locked:
            raise RosterLockedError()

        if len(team.rosters) >= division.maximum_roster_size:
            raise MaximumRosterExceededError()
```

---

## Repository Layer

Repositories abstract persistence concerns.

Responsibilities:

* Retrieve entities.
* Persist entities.
* Execute complex read queries.

Repositories shall NOT:

* Contain business rules.
* Manage transactions.

Examples:

```text
SeasonRepository
PlayerRepository
GameRepository
RosterRepository
```

---

## Model Layer

Models represent domain entities.

Responsibilities:

* Maintain entity state.
* Encapsulate small invariants.
* Define relationships.

Models shall NOT:

* Query the database.
* Access repositories.

Examples:

```python
game.finalize()
game.reopen()
season.archive()
```

---

# API-First Architecture

The backend shall expose REST APIs only.

The backend shall NOT render HTML templates.

Frontend and backend shall communicate using JSON payloads.

Example:

```text
Frontend (React)
        ↓
POST /api/v1/players
        ↓
Flask API
```

---

# Frontend Architecture

Frontend technology stack:

```text
React
TypeScript
Vite
```

Responsibilities:

* UI rendering.
* Client-side routing.
* Form handling.
* State management.
* API communication.

Frontend shall NOT:

* Contain business rules.
* Bypass backend validation.

---

# API Standards

## REST Conventions

The system shall follow RESTful conventions.

Examples:

```text
GET    /api/v1/seasons
POST   /api/v1/seasons

GET    /api/v1/players/{id}

POST   /api/v1/games
POST   /api/v1/games/{id}/finalize
```

---

# Standard API Response Format

Success:

```json
{
    "message": "Player created successfully.",
    "data": {}
}
```

Validation Error:

```json
{
    "message": "Validation failed.",
    "errors": []
}
```

Server Error:

```json
{
    "message": "An unexpected error occurred."
}
```

---

# API Idempotency

Critical POST endpoints shall support idempotency.

The frontend shall provide:

```http
Idempotency-Key: <uuid>
```

Example:

```http
POST /api/v1/players

Idempotency-Key:
2b19e638-7b76-4dcb-9e1d-f2f8c0b3e8ea
```

Backend flow:

```text
Request
    ↓
Check Existing Key
    ↓
Exists?
├── Yes → Return Stored Response
└── No
      ↓
Execute Request
      ↓
Store Response
      ↓
Return Response
```

Applicable endpoints:

* Resource creation endpoints
* Finalization endpoints
* Non-repeatable operations

Suggested implementation:

```text
Decorator
Middleware
```

---

# Dependency Injection

The system shall use constructor injection.

No Dependency Injection container shall be introduced in Version 1.

Example:

```python
service = TeamService(
    team_repository,
    roster_repository,
    roster_policy,
    uow
)
```

---

# Repository Abstraction

Repositories shall be defined using Abstract Base Classes.

Example:

```python
class ITeamRepository(ABC):

    @abstractmethod
    def get_by_id(self, id):
        pass
```

Implementations:

```text
SQLAlchemyTeamRepository
SQLAlchemyPlayerRepository
```

---

# Transaction Management

Transaction management shall follow the Unit of Work pattern.

The Service Layer owns transaction boundaries.

Example:

```python
with self.uow:
    self.team_repository.add(team)
    self.audit_repository.add(log)

    self.uow.commit()
```

Responsibilities:

* Begin transaction.
* Commit transaction.
* Rollback transaction.

---

# Domain Events

Domain Events shall NOT be implemented in Version 1.

This feature may be introduced in future versions if justified.

---

# Background Processing

Background processing technologies such as:

```text
Celery
Redis
RabbitMQ
```

shall NOT be introduced in Version 1.

---

# Project Structure

```text
backend/

app/
├── api/
│   └── v1/
│       ├── season/
│       ├── player/
│       ├── game/
│       ├── team/
│       └── auth/
│
├── application/
│   ├── season/
│   │   ├── services/
│   │   ├── policies/
│   │   └── dto/
│   │
│   ├── player/
│   │   ├── services/
│   │   ├── policies/
│   │   └── dto/
│   │
│   ├── game/
│   │   ├── services/
│   │   ├── policies/
│   │   └── dto/
│   │
│   └── ...
│
├── domain/
│   ├── models/
│   ├── repositories/
│   ├── enums/
│   └── exceptions/
│
├── infrastructure/
│   ├── database/
│   ├── repositories/
│   └── unit_of_work/
│
├── schemas/
│
├── auth/
│
├── common/
│   ├── responses/
│   ├── decorators/
│   ├── idempotency/
│   └── utils/
│
├── config/
│
├── extensions/
│
└── app.py
```

---

# Testing Strategy

## Unit Tests

Scope:

* Services
* Policies

Dependencies shall be mocked.

Examples:

```text
Repositories
UnitOfWork
```

---

## Integration Tests

Scope:

* Routes
* Repositories
* Database interactions

Integration tests shall execute against a dedicated test database.

---

## Functional Testing

Functional testing shall be performed manually using:

```text
Browser
Postman
```

The system shall undergo end-to-end validation prior to release.

---

# Aggregate Roots

The following entities are Aggregate Roots:

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
