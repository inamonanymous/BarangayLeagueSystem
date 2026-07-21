# API Specification

## Overview

This document defines the REST API contract for the League Management System.

The API serves as the communication layer between the React frontend and the Flask backend.

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
