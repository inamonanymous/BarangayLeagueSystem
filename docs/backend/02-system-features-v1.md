# System Features

## Overview

This document defines the functional features provided by the Barangay League Management System.

The system is organized into business modules to ensure maintainability, scalability, and clear separation of responsibilities.

Version 1 focuses on supporting basketball and volleyball tournaments while allowing future expansion to additional sports.

---

# 1. Authentication & User Management Module

## Description

This module is responsible for securing access to the system and managing system users.

## Features

### Authentication

* User login
* User logout
* JWT-based authentication
* Password change

### User Management

* Create user accounts
* Update user accounts
* Activate user accounts
* Deactivate user accounts
* Assign user roles
* Reset user passwords

### Access Control

* Role-based access control (RBAC)
* Restrict access to authorized features

---

# 2. Tournament Management Module

## Description

This module manages league seasons, sports, and divisions.

## Features

### Season Management

* Create seasons
* Update seasons
* Activate seasons
* Deactivate seasons
* Archive seasons
* View historical seasons

### Sport Management

* Create sports
* Update sports
* Archive sports
* View supported sports

### Division Management

* Create divisions
* Update divisions
* Archive divisions
* View divisions per sport and season

---

# 3. Team Management Module

## Description

This module manages participating teams and their seasonal participation.

## Features

### Team Registration

* Register teams
* Update team information
* Archive teams
* View team history

### Season Participation

* Register teams to seasons
* Assign teams to divisions
* View participating teams per season

---

# 4. Player Management Module

## Description

This module manages player information and player history.

## Features

### Player Registration

* Register players
* Update player information
* Archive players
* Search existing players

### Player History

* View player participation history
* View career statistics
* View season statistics

---

# 5. Roster Management Module

## Description

This module manages player assignments to teams for a specific season.

## Features

* Assign players to seasonal rosters
* Remove players from rosters
* Manage jersey numbers
* View team rosters
* Validate roster eligibility

---

# 6. Schedule Management Module

## Description

This module manages league schedules.

## Features

* Create game schedules
* Update schedules
* Reschedule games
* Cancel games
* View schedules

### Schedule Filters

Schedules may be filtered by:

* Season
* Sport
* Division
* Team

---

# 7. Game Management Module

## Description

This module manages game execution and result encoding.

## Features

### Game Results

* Record game scores
* Update game results
* Finalize game results
* View completed games

### Player Statistics

* Record player statistics
* Update player statistics
* View game box scores

---

# 8. Statistics Module

## Description

This module generates statistical information for players, teams, and leagues.

## Features

### Player Statistics

* Compute player averages
* Compute season statistics
* Compute career statistics

### Team Statistics

* Compute team standings
* Compute team win-loss records

### Leaderboards

Generate statistical leaderboards such as:

* Top Scorer
* Top Rebounder
* Top Assist Leader
* Top Block Leader
* Top Steal Leader

---

# 9. Playoff Management Module

## Description

This module manages playoff tournaments and bracket progression.

## Features

* Create playoff brackets
* Generate playoff matchups
* Seed teams automatically
* Seed teams manually
* Advance winners automatically
* Record playoff game results
* View playoff brackets

---

# 10. Reporting Module

## Description

This module provides reports and summaries for league administrators.

## Features

* View standings reports
* View player reports
* View team reports
* View game reports
* View season reports

---

# 11. Audit Module

## Description

This module records important system activities for accountability and traceability.

## Features

* Record user activities
* Track record modifications
* View audit logs

---

# Design Outcome

The system provides the following core capabilities:

✔ Secure user authentication
✔ Tournament administration
✔ Team and player management
✔ Schedule and game management
✔ Statistics computation
✔ Playoff bracket management
✔ Historical record tracking
✔ Audit and accountability support

---
