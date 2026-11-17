# Frontend Routes and URLs

This document lists the browser pages defined by the React frontend and the backend API URLs called by those pages.

## Browser Pages

These are frontend routes. Open them on the frontend application's host (for example, `http://localhost:5173`).

| Page | URL path | Access | Description |
| --- | --- | --- | --- |
| Login | `/login` | Public | Sign in to the application. Successful login navigates to `/`. |
| Dashboard | `/` | Public | Main application page; displays current account details when signed in. |
| Seasons | `/seasons` | Public history; Administrator create form | View current and historical seasons; administrators can create a season. |
| Season Configuration | `/seasons/:seasonId/configuration` | Public view; Administrator edits | View and manage this season's sports and divisions. |
| Players | `/players` | Administrators | Create, view, edit, archive, and restore permanent player profiles. |
| Team Registration | Within `/seasons/:seasonId/configuration` | Public list; Administrator registration | View teams under each division; administrators register teams during the season's registration period. |
| Game Schedule and Standings | Within `/seasons/:seasonId/configuration` | Public view; Administrator/Encoder actions | Configure sport statistics, record scores and player participation, and finalize or reopen results as permitted. |
| Add User | `/users/new` | Administrators | Create a user and assign a role. |
| Unknown path | Any other path | N/A | Redirects to `/`. |

Route definitions are in `frontend/src/App.tsx`. The Add User link is displayed only to Administrators, and the page also checks the current user's role. The backend independently enforces this permission.

On the season configuration page, use the sport, division, and team tabs to focus on one roster at a time. Archived teams remain available in the team tabs for restoration, and the game schedule is shown for the selected division. Tabs also support the arrow, Home, and End keys.

The page loads teams and schedules only for the selected division, and rosters and available players only for the selected team. Data is cached in memory for one minute and refreshed after related changes in this app; older data is rechecked when returning to the page, selecting a tab, or refocusing the browser. Changes made elsewhere are not pushed live, so use **Refresh data** to check immediately. A browser reload starts with a new in-memory cache.

The page shows refresh progress and the result. If it detects the old shared-catalog response, it stops instead of using catalog IDs as division IDs. Back up and migrate the database and restart the backend; see the [migration guidance](../backend/implementation-alignment.md#season-owned-sports-and-divisions).

## Backend API URLs

The frontend Axios client uses `/api/v1` as its base path and sends session cookies. These are API requests, not browser pages.

| Action | Method | URL path | Used for |
| --- | --- | --- | --- |
| Login | `POST` | `/api/v1/auth/login` | Submit username and password. |
| Current user | `GET` | `/api/v1/auth/me` | Retrieve the signed-in user's account and role. |
| Logout | `POST` | `/api/v1/auth/logout` | End the current session. |
| Create user | `POST` | `/api/v1/users/` | Create an account. Administrator access is required. |
| List seasons | `GET` | `/api/v1/seasons/` | Retrieve current and historical seasons. |
| Create season | `POST` | `/api/v1/seasons/` | Create a season. Administrator access is required. |
| Change season status | `PATCH` | `/api/v1/seasons/{id}/status` | Advance a season through its allowed lifecycle. Administrator access is required. |
| Get season configuration | `GET` | `/api/v1/seasons/{id}/configuration` | Retrieve the season's sports and divisions. |
| Create sport | `POST` | `/api/v1/seasons/{id}/sports` | Create a season-owned sport. Administrator access is required. |
| Edit sport | `PUT` | `/api/v1/seasons/{seasonId}/sports/{seasonSportId}` | Edit a season-owned sport. Administrator access is required. |
| Create division | `POST` | `/api/v1/seasons/sports/{seasonSportId}/divisions` | Create a division within the sport. Administrator access is required. |
| Edit division | `PUT` | `/api/v1/seasons/sports/{seasonSportId}/divisions/{assignmentId}` | Edit the division. Administrator access is required. |
| Remove sport | `DELETE` | `/api/v1/seasons/{seasonId}/sports/{seasonSportId}` | Remove the sport and its divisions if none have registered teams. |
| Remove division | `DELETE` | `/api/v1/seasons/sports/{seasonSportId}/divisions/{assignmentId}` | Remove the division if it has no registered teams. |
| List teams in division | `GET` | `/api/v1/season-sport-divisions/{assignmentId}/teams` | Retrieve teams for a season-specific division. |
| Register team | `POST` | `/api/v1/season-sport-divisions/{assignmentId}/teams` | Register a team during the season's Registration status/window. Administrator access is required. |
| List games | `GET` | `/api/v1/season-sport-divisions/{assignmentId}/games` | List scheduled games in a division. |
| Schedule game | `POST` | `/api/v1/season-sport-divisions/{assignmentId}/games` | Schedule two active teams during Ongoing; requires an Administrator. |
| Reschedule game | `PUT` | `/api/v1/games/{gameId}/schedule` | Update a game's venue and times before its start; requires an Administrator and an Ongoing season. |
| Enter result | `PUT` | `/api/v1/games/{gameId}/result` | Enter non-tied scores after the scheduled end; Administrator or Encoder, Ongoing season. |
| Sport statistics | `GET` / `PUT` | `/api/v1/season-sports/{sportId}/statistics-configuration` | View or configure required statistics and score matching; only an Administrator may update. |
| Game statistics | `GET` / `PUT` | `/api/v1/games/{gameId}/statistics` | View or save participation and statistics; Administrator or Encoder saves after the game ends in an Ongoing season. |
| Finalize result | `POST` | `/api/v1/games/{gameId}/finalize` | Administrator finalizes an entered result. |
| Reopen result | `POST` | `/api/v1/games/{gameId}/reopen` | Administrator reopens with a reason and records prior finalization details. |
| View standings | `GET` | `/api/v1/season-sport-divisions/{assignmentId}/standings` | Public wins and losses derived from finalized games. |
| Edit team | `PUT` | `/api/v1/season-teams/{teamId}` | Edit team details during Registration. Administrator access is required. |
| Archive/restore team | `DELETE` / `PATCH` | `/api/v1/season-teams/{teamId}` / `/api/v1/season-teams/{teamId}/archive` | Administrator only; Registration status required. Restore also requires the registration window and no conflicting active-team roster assignment. |
| List players | `GET` | `/api/v1/players/` | List active player profiles; Administrators only. Use `?include_archived=true` to include archived profiles. |
| Create player | `POST` | `/api/v1/players/` | Create a permanent player profile. Administrator access is required. |
| Read player | `GET` | `/api/v1/players/{playerId}` | Retrieve a player profile. Administrator access is required. |
| Edit player | `PUT` | `/api/v1/players/{playerId}` | Edit a permanent player profile. Administrator access is required. |
| Archive/restore player | `DELETE` / `PATCH` | `/api/v1/players/{playerId}` / `/api/v1/players/{playerId}/archive` | Soft-archive or restore a player. Administrator access is required. |
| List roster | `GET` | `/api/v1/season-teams/{teamId}/roster` | List roster entries for a team. |
| List available roster players | `GET` | `/api/v1/season-teams/{teamId}/available-players` | List active players not assigned to an active team in the same sport and season; Administrator access is required. |
| Add roster player | `POST` | `/api/v1/season-teams/{teamId}/roster` | Assign a player and jersey number; adult voter verification is required. Administrator access is required. |
| Edit roster entry | `PUT` | `/api/v1/season-teams/{teamId}/roster/{rosterId}` | Change a jersey number during Registration. Administrator access is required. |
| Remove roster entry | `DELETE` | `/api/v1/season-teams/{teamId}/roster/{rosterId}` | Remove the player-team link without deleting the player. Administrator access is required. |

Frontend API functions are grouped in `frontend/src/shared/api/`. The backend serves the API under `/api/v1`.