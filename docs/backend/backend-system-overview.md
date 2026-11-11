# Backend System Overview

## 1. Overall structure

This backend is a Flask application organized in layers:

- Routes: handle incoming HTTP requests
- Services: contain business logic
- Models: define database tables and behavior
- Extensions: initialize Flask, SQLAlchemy, migrations, and sessions

The main entry point is:
- [backend/wsgi.py](../wsgi.py)

The app factory is created in:
- [backend/app/__init__.py](../app/__init__.py)

---

## 2. Request flow

A request usually follows this path:

Route -> Service -> Model/Database -> Response

Example:
1. A request reaches a route in the API package
2. The route calls a service
3. The service queries or updates the database through models
4. The route returns a JSON response

---

## 3. Main backend folders

### app/api/v1
Contains API routes grouped by feature.

Current example:
- [backend/app/api/v1/auth/routes.py](../app/api/v1/auth/routes.py)

### app/application
Contains application logic and services.

Current example:
- [backend/app/application/auth/services.py](../app/application/auth/services.py)

### app/domain/models
Contains database models.

Current examples:
- [backend/app/domain/models/user.py](../app/domain/models/user.py)
- [backend/app/domain/models/role.py](../app/domain/models/role.py)

### app/extensions
Initializes shared Flask extensions like SQLAlchemy and Flask Session.

### app/config
Stores configuration for development, testing, production, and base settings.

---

## 4. Current authentication flow

The current auth flow is centered around login/logout and current user retrieval.

### Login flow
1. The client sends a request to /api/v1/auth/login
2. The route reads the username and password from the request body
3. The AuthService checks:
   - whether the user exists
   - whether the password is correct
   - whether the account is active
4. If valid, the route stores the user in the session
5. The API returns a success response with the user data

### Logout flow
1. The client calls /api/v1/auth/logout
2. The route clears the session
3. The API returns a success response

### Current user flow
1. The client calls /api/v1/auth/me
2. The route reads the session user id
3. It loads the user from the database
4. It returns the user data if authenticated

---

## 5. Important files to know

### Entry and app setup
- [backend/wsgi.py](../wsgi.py)
- [backend/app/__init__.py](../app/__init__.py)
- [backend/app/api/v1/__init__.py](../app/api/v1/__init__.py)

### Auth
- [backend/app/api/v1/auth/routes.py](../app/api/v1/auth/routes.py)
- [backend/app/application/auth/services.py](../app/application/auth/services.py)

### Models
- [backend/app/domain/models/user.py](../app/domain/models/user.py)
- [backend/app/domain/models/role.py](../app/domain/models/role.py)

### Shared helpers
- [backend/app/application/common/responses/api_response.py](../app/application/common/responses/api_response.py)
- [backend/app/application/common/utils/base_classes.py](../app/application/common/utils/base_classes.py)

---

## 6. How to read the code

When learning the system, use this order:
1. Read the route file
2. Follow the service it calls
3. Inspect the model it uses
4. Check the response helper if needed

This keeps the flow understandable and predictable.

---

## 7. Current implementation status

The current backend focus is around:
- authentication
- user and role modeling
- base application structure

The roadmap for future implementation is tracked in:
- [docs/checklist.md](../../checklist.md)
