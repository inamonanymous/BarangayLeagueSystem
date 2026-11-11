# Frontend Routes and URLs

This document lists the browser pages defined by the React frontend and the backend API URLs called by those pages.

## Browser Pages

These are frontend routes. Open them on the frontend application's host (for example, `http://localhost:5173`).

| Page | URL path | Access | Description |
| --- | --- | --- | --- |
| Login | `/login` | Public | Sign in to the application. Successful login navigates to `/`. |
| Dashboard | `/` | Signed-in users | Main application page. |
| Seasons | `/seasons` | Public history; Administrator create form | View current and historical seasons; administrators can create a season. |
| Season Configuration | `/seasons/:seasonId/configuration` | Public view; Administrator edits | View sports and divisions assigned to a season; administrators manage catalog entries and assignments. |
| Add User | `/users/new` | Administrators | Create a user and assign a role. |
| Unknown path | Any other path | N/A | Redirects to `/`. |

Route definitions are in `frontend/src/App.tsx`. The Add User link is displayed only to Administrators, and the page also checks the current user's role. The backend independently enforces this permission.

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
| List divisions | `GET` | `/api/v1/catalogs/divisions` | Retrieve the division catalog. |
| Create division | `POST` | `/api/v1/catalogs/divisions` | Add a division to the catalog. Administrator access is required. |
| Assign sport to season | `POST` | `/api/v1/seasons/{id}/sports` | Add a catalog sport to a season. Administrator access is required. |
| Assign division | `POST` | `/api/v1/seasons/sports/{seasonSportId}/divisions` | Add a division to a sport in a season. Administrator access is required. |

The frontend API functions are in `frontend/src/shared/api/auth.ts`. The backend serves the API under `/api/v1`.