League Management System
Documentation Roadmap
==============================================

BACKEND DOCUMENTATION
----------------------------------------------

[x] Project Overview

[x] System Features

[x] User Roles

[x] Business Rules

[x] Database Design

[x] ERD

[x] Architecture Design

[x] Tech Stack

[x] API Specification (Template)

----------------------------------------------

FRONTEND DOCUMENTATION
----------------------------------------------

[x] Frontend Overview

[x] Frontend Architecture

[ ] Frontend Tech Stack

[ ] Frontend Coding Standards

----------------------------------------------

ENGINEERING GUIDELINES
----------------------------------------------

(Decision Trees removed)

----------------------------------------------

DIAGRAMS
----------------------------------------------

[x] Use Case Diagram

[x] Component Diagram

Activity Diagrams

[ ] Authentication

[ ] Create Season

[ ] Register Team

[ ] Create Player

[ ] Manage Roster

[ ] Schedule Game

[ ] Encode Game Statistics

[ ] Finalize Game

Sequence Diagrams

[ ] Authentication

[ ] Create Player

[ ] Register Team

[ ] Schedule Game

[ ] Encode Game Statistics

[ ] Finalize Game

[ ] View Standings

----------------------------------------------

FOUNDATION (Before Coding)
----------------------------------------------

Backend

[x] Initialize Flask Project

[x] Folder Structure

[x] Configuration

[x] Environment Variables

[x] SQLAlchemy

[x] Alembic (migration chain exists; fresh-install users-table prerequisite is tracked)

[x] Marshmallow

[x] Session Authentication

[x] Error Handling

[x] API Response Helpers

[ ] Logging

[x] Testing Setup

Frontend

[x] Initialize React Project

[ ] Tailwind CSS

[x] React Router

[x] Axios

[x] TanStack Query

[ ] React Hook Form (dependency present; current forms use controlled inputs)

[ ] TanStack Table

[x] Lucide React

[x] Folder Structure

[ ] Shared Components (partial; shared API and layout exist)

----------------------------------------------

IMPLEMENTATION
----------------------------------------------

| Sprint | Status | Implemented scope / remaining |
| --- | --- | --- |
| 1. Authentication | Complete | Session login/logout/current-user; tested. |
| 2. Users and Roles | Partial | Role-based access and Administrator-created users; list, edit, activation, and password reset remain. |
| 3. Sports, Seasons, Divisions | Partial | Season lifecycle, reusable Sport/Division catalogs, and season assignments; stronger database enforcement and UX remain. |
| 4. Venues, Players, Eligibility | Partial | Player CRUD/archive and season voter eligibility exist; VoterRegistration source and Venues remain. |
| 5. Teams and Rosters | Partial | Team CRUD/archive and roster add/list/jersey update/remove exist; minimum roster activation rule remains. |
| 6. Rounds and Games | Planned | No models or workflows yet. |
| 7. Statistics and Standings | Planned | No models or workflows yet. |
| 8. Playoff Brackets | Planned | No models or workflows yet. |
| 9. Dashboard and Reports | Partial | A basic authenticated dashboard exists; league data/reporting remains planned. |

----------------------------------------------

TESTING
----------------------------------------------

[~] Unit Testing (auth, catalogs, and season slices covered; full domain coverage remains)

[~] Integration Testing (implemented API slices covered; broader workflows remain)

[ ] Functional Testing

[ ] Regression Testing

----------------------------------------------

DEPLOYMENT
----------------------------------------------

[ ] Production Configuration

[ ] MySQL Production Database

[ ] Deploy Flask Backend

[ ] Deploy React Frontend

[ ] Documentation Update

[ ] Version 1 Release