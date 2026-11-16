# Technology Stack

> **Stack plan and current status:** This document includes proposed tools and
> deployment choices. The current backend uses Python 3.10 in the existing
> development environment, Flask-Session (not Flask-Login), SQLAlchemy,
> Flask-Migrate, and Marshmallow. The frontend uses React, TypeScript, Vite,
> Axios, React Router, TanStack Query, and a shared CSS stylesheet. Swagger,
> Docker, Vitest, persistent API idempotency, and a production deployment are
> not currently set up. See the [README](../../README.md) for setup and the
> [implementation tracker](implementation-alignment.md) for known gaps.

## Overview

This document defines the technologies, frameworks, libraries, and tools used by the League Management System.

The selected technology stack prioritizes:

* Maintainability
* Simplicity
* Developer productivity
* Testability
* Scalability
* Low operational cost

---

# System Architecture

```text
Frontend (React SPA)
        ↓ HTTP/JSON
Backend (Flask REST API)
        ↓
MySQL Database
```

---

# Backend Stack

## Programming Language

| Technology | Version |
| ---------- | ------- |
| Python     | 3.10 in the existing development environment |

---

## Web Framework

| Technology | Purpose            |
| ---------- | ------------------ |
| Flask      | REST API Framework |

Reason:

* Lightweight.
* Highly extensible.
* Large ecosystem.
* Suitable for solo development.

---

## ORM

| Technology       | Purpose                   |
| ---------------- | ------------------------- |
| Flask-SQLAlchemy | Object Relational Mapping |

Reason:

* Simplifies database interaction.
* Integrates naturally with Flask.
* Reduces boilerplate.

---

## Database Migration

| Technology | Purpose                    |
| ---------- | -------------------------- |
| Alembic    | Database schema migrations |

Reason:

* Version-controlled database changes.
* Safe schema evolution.

---

## Request / Response Serialization

| Technology  | Purpose                      |
| ----------- | ---------------------------- |
| Marshmallow | Validation and serialization |

Responsibilities:

* Request validation.
* Response serialization.
* DTO transformation.

---

## Authentication

| Technology  | Purpose                |
| ----------- | ---------------------- |
| Flask-Session | Server-side session storage |

Version 1 Authentication Strategy:

```text
Session Authentication
Cookie-based Authentication
```

Future versions may introduce:

```text
JWT Authentication
Refresh Tokens
```

---

## API Documentation (planned)

| Technology        | Purpose           |
| ----------------- | ----------------- |
| Swagger / OpenAPI | API Documentation |

Purpose:

* Interactive API exploration.
* API testing.
* Contract documentation.

Recommended Library:

```text
Flask-Smorest
```

Features:

* Automatic OpenAPI generation.
* Swagger UI.
* Marshmallow integration.

---

# Frontend Stack

## Frontend Framework

| Technology | Purpose                  |
| ---------- | ------------------------ |
| React      | User Interface Framework |

---

## Programming Language

| Technology | Purpose                        |
| ---------- | ------------------------------ |
| TypeScript | Type-safe frontend development |

Reason:

* Better refactoring support.
* Reduced runtime errors.
* Improved maintainability.

---

## Build Tool

| Technology | Purpose             |
| ---------- | ------------------- |
| Vite       | Frontend build tool |

Reason:

* Fast development experience.
* Modern tooling.

---

## Styling Framework (proposed)

| Technology | Purpose              |
| ---------- | -------------------- |
| Bootstrap  | Proposed UI styling framework; current UI uses a shared CSS stylesheet |

Reason:

* Rapid development.
* Responsive design.
* Minimal CSS overhead.

---

## Routing

| Technology   | Purpose             |
| ------------ | ------------------- |
| React Router | Client-side routing |

---

## HTTP Client

| Technology | Purpose           |
| ---------- | ----------------- |
| Axios      | API communication |

Responsibilities:

* HTTP requests.
* Request interceptors.
* Authentication handling.
* Global error handling.

---

## Frontend State Management

| Technology        | Purpose                 |
| ----------------- | ----------------------- |
| React Context API | Global state management |

Currently, TanStack Query manages server-state caching; component state manages
local UI state.

Version 1 shall not use:

```text
Redux
MobX
Zustand
```

These may be introduced in future versions if needed.

---

# Database Stack

| Technology | Purpose             |
| ---------- | ------------------- |
| MySQL      | Relational Database |

Reason:

* Mature ecosystem.
* Widely supported.
* Suitable for transactional systems.

---

# Testing Stack

## Backend Testing

| Technology | Purpose                      |
| ---------- | ---------------------------- |
| Pytest     | Unit and integration testing |

Testing Scope:

```text
Unit Tests
Integration Tests
Service Tests
Repository Tests
API Tests
```

---

## Frontend Testing (planned)

| Technology | Purpose               |
| ---------- | --------------------- |
| Vitest     | Frontend unit testing |

---

## Manual Testing

Tools:

```text
Browser
Postman
Swagger UI
```

---

# Containerization

## Container Platform (planned)

| Technology     | Purpose                       |
| -------------- | ----------------------------- |
| Docker         | Containerization              |
| Docker Compose | Multi-container orchestration |

Containerized Services:

```text
Backend
Frontend
MySQL
```

Purpose:

* Simplified development environment.
* Consistent deployments.
* Easier onboarding.

---

# Deployment

## Version 1 Deployment Target

```text
PythonAnywhere
```

Reason:

* Free tier available.
* Easy deployment.
* Minimal infrastructure management.

Future deployment targets may include:

```text
DigitalOcean
Hetzner
AWS EC2
```

---

# Logging

Application logging shall NOT be implemented in Version 1.

Only default Flask and server logs shall be utilized.

Centralized logging may be introduced in future versions.

---

# Caching

The frontend currently uses TanStack Query's in-memory cache. Season-page data
is fresh for one minute and can be manually refreshed. A separate server-side
cache has not been introduced.

Potential future technologies:

```text
Redis
Memcached
```

---

# Development Tools

## Recommended IDE

```text
Visual Studio Code
```

Recommended Extensions:

```text
Python
Pylance
ESLint
Prettier
Docker
GitLens
```

---

# Version Control

| Technology | Purpose            |
| ---------- | ------------------ |
| Git        | Source Control     |
| GitHub     | Repository Hosting |

---

# API Standards

Communication between frontend and backend shall use:

```text
HTTP/JSON
UTF-8 Encoding
REST Architecture
```

API responses shall follow a standardized response structure.

---

# Security Standards

Version 1 security targets (not all implemented):

* Session Authentication
* Password Hashing
* Authorization by Role
* CSRF Protection (planned)
* Input Validation
* Persistent API Idempotency (planned)

Future enhancements:

```text
JWT
Rate Limiting
Multi-Factor Authentication
```
