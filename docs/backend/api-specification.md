# API Specification

## Overview

This document defines the REST API contract for the League Management System.

The API serves as the communication layer between the React frontend and the Flask backend.

This document includes planned API behavior. The implemented frontend endpoints
are listed in [Frontend Routes and URLs](../frontend/frontend-routes.md).

## Implemented game scheduling

- `GET /api/v1/season-sport-divisions/{assignment_id}/games` lists the division's
  games publicly, ordered by start time.
- `POST /api/v1/season-sport-divisions/{assignment_id}/games` requires an
  Administrator and an Ongoing season. It accepts `home_team_id`, `away_team_id`,
  `venue`, `starts_at`, and `ends_at`. Times are local ISO datetimes without a
  timezone offset or fractional seconds.
- Both teams must be different, active, and assigned to that division. Start must
  precede end. A normalized venue name or either team cannot overlap another
  game; adjacent times are allowed. Conflicts return HTTP 409.
- `PUT /api/v1/games/{game_id}/schedule` requires an Administrator and an
  Ongoing season. It replaces the schedule using required `venue`, `starts_at`,
  and `ends_at` fields, without changing the teams. Both the existing and new
  start times must be later than the server's current local time. The existing
  game is excluded from its own overlap check. Invalid input returns HTTP 400,
  a missing game returns 404, and a conflict returns 409.
- Cancellation, results, Rounds, and managed venues are not implemented.

## Implemented team archive and restore

- Administrator `DELETE /api/v1/season-teams/{team_id}` or `PATCH /api/v1/season-teams/{team_id}/archive` with `{"is_archived": true}` archives a team only while the season is in Registration, regardless of the configured registration dates.
- `PATCH` with `{"is_archived": false}` restores an archived team only during Registration and within the configured registration date window, if present.
- Restore returns HTTP 409 with player and team details if a roster player belongs to another active team in the same sport and season. The roster remains unchanged; remove the conflicting player from the other team before retrying.
- Invalid season status or restore window returns 400, a missing team returns 404, and Administrator authorization is required.

### API Principles

* RESTful architecture
* JSON request and response bodies
* UTF-8 encoding
* Session-based authentication (Version 1)
* Role-based authorization
* Standardized response format
* Idempotent support for critical POST requests

---

# Standard API Response Format

## Success Response

```json
{
    "message": "Operation completed successfully.",
    "data": {}
}
```

---

## Validation Error Response

HTTP Status

```text
400 Bad Request
```

```json
{
    "message": "Validation failed.",
    "errors": {
        "field_name": [
            "Validation message."
        ]
    }
}
```

---

## Unauthorized Response

HTTP Status

```text
401 Unauthorized
```

```json
{
    "message": "Authentication required."
}
```

---

## Forbidden Response

HTTP Status

```text
403 Forbidden
```

```json
{
    "message": "You do not have permission to perform this action."
}
```

---

## Resource Not Found

HTTP Status

```text
404 Not Found
```

```json
{
    "message": "Requested resource was not found."
}
```

---

## Conflict Response

HTTP Status

```text
409 Conflict
```

```json
{
    "message": "The requested operation conflicts with existing data."
}
```

---

## Internal Server Error

HTTP Status

```text
500 Internal Server Error
```

```json
{
    "message": "An unexpected error occurred."
}
```

---

# Endpoint Template

---

## HTTP_METHOD /api/v1/resource

### Description

Brief explanation of the endpoint.

---

### Authorization

| Role          | Allowed |
| ------------- | :-----: |
| Administrator |    ✅    |
| Encoder       |    ❌    |
| Viewer        |    ❌    |

---

### Request Headers

| Header                         | Required | Description                            |
| ------------------------------ | :------: | -------------------------------------- |
| Content-Type: application/json |    Yes   | JSON Request Body                      |
| Idempotency-Key                | Optional | Required only for idempotent endpoints |

---

### Path Parameters

| Name | Type    | Required | Description         |
| ---- | ------- | :------: | ------------------- |
| id   | Integer |    Yes   | Resource Identifier |

If not applicable:

```text
None
```

---

### Query Parameters

| Name      | Type    | Required | Description    |
| --------- | ------- | :------: | -------------- |
| page      | Integer |    No    | Page Number    |
| page_size | Integer |    No    | Items Per Page |
| search    | String  |    No    | Search Keyword |

If not applicable:

```text
None
```

---

### Request Body

```json
{
}
```

---

### Success Response

HTTP Status

```text
200 OK
```

```json
{
    "message": "",
    "data": {}
}
```

---

### Error Responses

#### 400 Bad Request

Reason

* Validation failed

Example

```json
{
    "message": "",
    "errors": {}
}
```

---

#### 401 Unauthorized

Reason

* Authentication required

---

#### 403 Forbidden

Reason

* User lacks permission

---

#### 404 Not Found

Reason

* Resource does not exist

---

#### 409 Conflict

Reason

* Duplicate or conflicting resource

---

### Validation Rules

* Rule 1
* Rule 2
* Rule 3

---

### Business Rules

Reference applicable Business Rules document IDs.

Example:

* BR-012
* BR-018
* BR-039

Describe any endpoint-specific rules here if needed.

---

### Idempotency

Choose one:

```text
Supported
```

or

```text
Not Applicable
```

If supported:

* Client shall provide an `Idempotency-Key` header.
* Duplicate requests shall return the original successful response.
* Business logic shall execute only once per unique key.

---

### Notes

Additional implementation notes.

Examples:

* Soft delete only.
* Related statistics are computed dynamically.
* Returns paginated results.
* Only finalized games are included.

---

# Resource Sections

The API specification should be organized by resource in the following order:

1. Authentication
2. Users
3. Roles
4. Seasons
5. Sports
6. Divisions
7. Season Sports
8. Season Sport Divisions
9. Venues
10. Players
11. Voter Registrations
12. Season Teams
13. Rosters
14. Rounds
15. Games
16. Statistic Types
17. Player Game Statistics
18. Standings
19. Playoff Brackets
20. Playoff Matches
21. Audit Logs
22. System Settings
