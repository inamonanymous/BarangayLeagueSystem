# Frontend Routes and URLs

This document lists the browser pages defined by the React frontend and the backend API URLs called by those pages.

## Browser Pages

These are frontend routes. Open them on the frontend application's host (for example, `http://localhost:5173`).

| Page | URL path | Access | Description |
| --- | --- | --- | --- |
| Login | `/login` | Public | Sign in to the application. Successful login navigates to `/`. |
| Dashboard | `/` | Public | Main application page; displays current account details when signed in. |
| Seasons | `/seasons` | Public history; Administrator create form | View current and historical seasons; administrators can create a season. |
| Season Configuration | `/seasons/:seasonId/configuration` | Public view; Administrator edits | View sports and divisions assigned to a season; administrators manage catalog entries and assignments. |
| Players | `/players` | Administrators | Create, view, edit, archive, and restore permanent player profiles. |
| Team Registration | Within `/seasons/:seasonId/configuration` | Public list; Administrator registration | View teams under each division; administrators register teams during the season's registration period. |
| Game Schedule | Within `/seasons/:seasonId/configuration` | Public list; Administrator scheduling | View division games; administrators schedule and reschedule games when the season is Ongoing. |
| Add User | `/users/new` | Administrators | Create a user and assign a role. |
| Unknown path | Any other path | N/A | Redirects to `/`. |

Route definitions are in `frontend/src/App.tsx`. The Add User link is displayed only to Administrators, and the page also checks the current user's role. The backend independently enforces this permission.

On the season configuration page, use the sport, division, and team tabs to focus on one roster at a time. Archived teams remain available in the team tabs for restoration, and the game schedule is shown for the selected division. Tabs also support the arrow, Home, and End keys.

The page loads teams and schedules only for the selected division, and rosters and available players only for the selected team. Data is cached in memory for one minute and refreshed after related changes in this app; older data is rechecked when returning to the page, selecting a tab, or refocusing the browser. Changes made elsewhere are not pushed live, so use **Refresh data** to check immediately. A browser reload starts with a new in-memory cache.

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
| Get season configuration | `GET` | `/api/v1/seasons/{id}/configuration` | Retrieve the season's assigned sports and divisions. |
| List sports | `GET` | `/api/v1/catalogs/sports` | Retrieve the sport catalog. |
| Create sport | `POST` | `/api/v1/catalogs/sports` | Add a sport to the catalog. Administrator access is required. |
| Update sport | `PUT` | `/api/v1/catalogs/sports/{sportId}` | Edit a catalog sport. Administrator access is required. |
| Delete sport | `DELETE` | `/api/v1/catalogs/sports/{sportId}` | Delete an unused catalog sport. Assigned sports return a conflict. |
| List divisions | `GET` | `/api/v1/catalogs/divisions` | Retrieve the division catalog. |
| Create division | `POST` | `/api/v1/catalogs/divisions` | Add a division to the catalog. Administrator access is required. |
| Update division | `PUT` | `/api/v1/catalogs/divisions/{divisionId}` | Edit a catalog division. Administrator access is required. |
| Delete division | `DELETE` | `/api/v1/catalogs/divisions/{divisionId}` | Delete an unused catalog division. Assigned divisions return a conflict. |
| Assign sport to season | `POST` | `/api/v1/seasons/{id}/sports` | Add a catalog sport to a season. Administrator access is required. |
| Assign division | `POST` | `/api/v1/seasons/sports/{seasonSportId}/divisions` | Add a division to a sport in a season. Administrator access is required. |
| Remove sport assignment | `DELETE` | `/api/v1/seasons/{seasonId}/sports/{seasonSportId}` | Remove the season link and its division links; the catalog sport remains. Administrator access is required. |
| Remove division assignment | `DELETE` | `/api/v1/seasons/sports/{seasonSportId}/divisions/{assignmentId}` | Remove a division link; the catalog division remains. Administrator access is required. |
| List teams in division | `GET` | `/api/v1/season-sport-divisions/{assignmentId}/teams` | Retrieve teams for a season-specific division. |
| Register team | `POST` | `/api/v1/season-sport-divisions/{assignmentId}/teams` | Register a team during the season's Registration status/window. Administrator access is required. |
| List games | `GET` | `/api/v1/season-sport-divisions/{assignmentId}/games` | List scheduled games in a division. |
| Schedule game | `POST` | `/api/v1/season-sport-divisions/{assignmentId}/games` | Schedule two active teams during Ongoing; requires an Administrator. |
| Reschedule game | `PUT` | `/api/v1/games/{gameId}/schedule` | Update a game's venue and times before its start; requires an Administrator and an Ongoing season. |
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