# Workflows and Use Cases

## Overview

This document defines the primary business workflows and use cases of the Barangay League Management System.

The workflows describe how users interact with the system to accomplish league-related tasks.

Version 1 focuses on supporting manual league administration while maintaining flexibility for future enhancements.

---

# 1. Create Season

## Actor

Administrator

## Description

Allows an administrator to create a new league season.

## Preconditions

* Administrator is authenticated.
* Required sports and divisions exist.

## Main Flow

1. Administrator navigates to the Season Management module.
2. Administrator selects "Create Season".
3. Administrator enters season information.
4. Administrator assigns supported sports and divisions.
5. System validates the input.
6. System creates the season with an initial status of `PLANNING`.

## Postconditions

* New season is successfully created.

---

# 2. Register Team to Season

## Actor

Administrator

## Description

Allows an administrator to register an existing team to a specific season and division.

## Preconditions

* Season exists.
* Team exists.
* Season is open for registration.

## Main Flow

1. Administrator selects a season.
2. Administrator selects a team.
3. Administrator selects the sport and division.
4. System validates eligibility.
5. System registers the team to the season.

## Postconditions

* Team becomes an official participant of the season.

---

# 3. Register Player

## Actor

Administrator

## Description

Allows an administrator to create player records.

## Preconditions

* Administrator is authenticated.

## Main Flow

1. Administrator navigates to Player Management.
2. Administrator enters player information.
3. System validates duplicate records.
4. System saves the player record.

## Postconditions

* Player is available for future roster assignments.

---

# 4. Assign Player to Team Roster

## Actor

Administrator

## Description

Allows an administrator to assign players to a team's seasonal roster.

## Preconditions

* Team is registered in a season.
* Player exists.
* Season roster is open.

## Main Flow

1. Administrator selects a participating team.
2. Administrator selects players.
3. Administrator assigns jersey numbers.
4. System validates roster rules.
5. System saves roster assignments.

## Postconditions

* Players become eligible to participate in games.

---

# 5. Create Game Schedule

## Actor

Administrator

## Description

Allows an administrator to manually create game schedules.

## Preconditions

* Season is active.
* Teams are registered.

## Main Flow

1. Administrator selects season, sport, and division.
2. Administrator selects two participating teams.
3. Administrator selects date, time, and venue.
4. System validates schedule conflicts.
5. System creates the schedule.

## Postconditions

* Scheduled game becomes visible to users.

---

# 6. Record Game Results

## Actor

Encoder

## Description

Allows an encoder to record game scores and player statistics.

## Preconditions

* Game schedule exists.
* Game status is not finalized.

## Main Flow

1. Encoder selects a scheduled game.
2. Encoder enters final scores.
3. Encoder records player statistics.
4. System validates encoded data.
5. System saves the game record.

## Postconditions

* Game data is stored.
* Game remains editable until finalized.

---

# 7. Finalize Game

## Actor

Administrator

## Description

Allows an administrator to officially finalize a game.

## Preconditions

* Game results have been encoded.
* Game is not yet finalized.

## Main Flow

1. Administrator reviews game information.
2. Administrator selects "Finalize Game".
3. System validates game completeness.
4. System marks the game as `FINALIZED`.
5. System updates standings and statistics.

## Postconditions

* Game becomes official.
* Standings are recalculated.
* Encoders can no longer edit the game.

---

# 8. Reopen Finalized Game

## Actor

Administrator

## Description

Allows an administrator to reopen finalized games for corrections.

## Preconditions

* Game status is `FINALIZED`.

## Main Flow

1. Administrator selects a finalized game.
2. Administrator selects "Reopen Game".
3. Administrator provides a reason.
4. System changes the game status to `FOR_ENCODING`.

## Postconditions

* Game becomes editable again.
* System records the action in the audit log.

---

# 9. View Standings

## Actors

Administrator, Encoder, Viewer

## Description

Allows users to view current team standings.

## Preconditions

* Finalized games exist.

## Main Flow

1. User selects season, sport, and division.
2. System retrieves standings.
3. System displays rankings.

## Postconditions

* User can view updated standings.

---

# 10. Create Playoff Bracket

## Actor

Administrator

## Description

Allows an administrator to manually create playoff brackets.

## Preconditions

* Regular season has concluded.

## Main Flow

1. Administrator selects the season and division.
2. Administrator manually selects qualified teams.
3. Administrator manually assigns seeds.
4. System generates playoff matchups.

## Postconditions

* Playoff bracket is created.

---

# 11. Record Playoff Results

## Actor

Encoder

## Description

Allows an encoder to record playoff game results.

## Preconditions

* Playoff bracket exists.
* Playoff game has been scheduled.

## Main Flow

1. Encoder selects playoff game.
2. Encoder records scores and player statistics.
3. Administrator finalizes the game.
4. System advances the winning team.

## Postconditions

* Bracket progression is updated.

---

# 12. Archive Season

## Actor

Administrator

## Description

Allows an administrator to archive completed seasons.

## Preconditions

* Season status is `COMPLETED`.

## Main Flow

1. Administrator selects a completed season.
2. Administrator confirms archival.
3. System archives the season.

## Postconditions

* Season becomes read-only.
* Historical records remain accessible.

---

# Season Lifecycle

A season progresses through the following statuses:

```text
PLANNING
    ↓
REGISTRATION
    ↓
ONGOING
    ↓
COMPLETED
    ↓
ARCHIVED
```

---

# Game Lifecycle

A game progresses through the following statuses:

```text
SCHEDULED
    ↓
FOR_ENCODING
    ↓
FINALIZED
```

Additional statuses:

```text
CANCELLED
POSTPONED
```

Only `FINALIZED` games affect standings and statistics.

---

# Design Outcome

The workflow design ensures:

✔ Clear separation of responsibilities
✔ Controlled game finalization process
✔ Historical record preservation
✔ Consistent standings computation
✔ Extensibility for future tournament formats

---
