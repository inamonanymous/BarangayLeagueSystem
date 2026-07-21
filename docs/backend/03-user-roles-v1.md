# User Roles

## Overview

This document defines the user roles and access permissions for the Barangay League Management System.

The system uses **Role-Based Access Control (RBAC)** to ensure that users can only perform actions that are appropriate for their responsibilities.

Version 1 supports three primary roles:

1. Administrator
2. Encoder
3. Viewer

Future versions may introduce additional roles as business requirements evolve.

---

# 1. Administrator

## Description

The Administrator is responsible for the overall management and operation of league tournaments.

Administrators have full access to all system modules and may override or correct records when necessary.

## Responsibilities

* Manage seasons, sports, and divisions
* Manage teams and rosters
* Manage player records
* Manage schedules and games
* Finalize games
* Manage playoff brackets
* Manage system users
* Review reports and statistics
* Correct incorrectly encoded records
* Review audit logs

## Permissions

### Can

#### User Management

* Create user accounts
* Update user accounts
* Activate and deactivate user accounts
* Assign user roles
* Reset user passwords

#### Tournament Management

* Create, update, activate, and archive seasons
* Create, update, and archive sports
* Create, update, and archive divisions

#### Team & Player Management

* Register teams
* Register players
* Manage seasonal participation
* Manage rosters

#### Schedule Management

* Create schedules
* Update schedules
* Reschedule games
* Cancel games

#### Game Management

* Record game results
* Update game results
* Edit finalized games
* Finalize games
* Reopen finalized games when necessary

#### Statistics & Playoffs

* Manage playoff brackets
* View all statistics and reports

#### Audit

* View audit logs

### Cannot

* N/A

---

# 2. Encoder

## Description

The Encoder is responsible for recording game results and player statistics based on official game sheets.

Encoders are limited to operational activities and cannot modify league configuration.

## Responsibilities

* Record game results
* Encode player statistics
* Update game records before finalization
* Review schedules and standings

## Permissions

### Can

#### Viewing

* View seasons
* View sports
* View divisions
* View teams
* View rosters
* View schedules
* View standings
* View playoff brackets

#### Game Management

* Record game scores
* Record player statistics
* Edit non-finalized games
* Update player statistics before finalization

### Cannot

* Create seasons
* Create sports
* Create divisions
* Manage users
* Archive records
* Finalize games
* Edit finalized games
* Manage playoff brackets
* View audit logs

---

# 3. Viewer

## Description

The Viewer role provides read-only access to league information.

This role is intended for players, spectators, coaches, and league followers.

## Responsibilities

* View league information
* Monitor schedules and standings
* View game results and statistics

## Permissions

### Can

* View seasons
* View sports
* View divisions
* View teams
* View team rosters
* View schedules
* View game results
* View standings
* View player statistics
* View playoff brackets

### Cannot

* Create records
* Update records
* Delete records
* Encode statistics
* Finalize games
* Manage users
* Access administrative functions

---

# Future Roles (Optional)

The following roles may be introduced in future versions if business requirements require them.

## Coach

Responsibilities:

* View own team information
* View own team statistics
* Manage own team roster

## Statistician

Responsibilities:

* Encode player statistics only

## League Commissioner

Responsibilities:

* Approve finalized games
* Review disputes
* Approve standings and playoff progression

These roles are not included in Version 1.

---

# Permission Summary

| Module                | Administrator | Encoder        | Viewer    |
| --------------------- | ------------- | -------------- | --------- |
| User Management       | Full Access   | No Access      | No Access |
| Tournament Management | Full Access   | Read Only      | Read Only |
| Team Management       | Full Access   | Read Only      | Read Only |
| Player Management     | Full Access   | Read Only      | Read Only |
| Roster Management     | Full Access   | Read Only      | Read Only |
| Schedule Management   | Full Access   | Read Only      | Read Only |
| Game Management       | Full Access   | Limited Access | Read Only |
| Statistics            | Full Access   | Read Only      | Read Only |
| Playoff Management    | Full Access   | Read Only      | Read Only |
| Audit Logs            | Full Access   | No Access      | No Access |

---

# Design Outcome

The Role-Based Access Control design ensures:

✔ Secure system access
✔ Controlled modification of records
✔ Clear separation of responsibilities
✔ Protection of finalized game records
✔ Future extensibility for additional roles

---
