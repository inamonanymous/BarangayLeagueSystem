# Frontend Architecture

## Current implementation

The frontend is a React and TypeScript single-page application built with Vite.
[main.tsx](../../frontend/src/main.tsx) provides React Router and a TanStack
Query client; [App.tsx](../../frontend/src/App.tsx) defines browser routes.
See [Frontend Routes and URLs](frontend-routes.md) for pages and API endpoints.

Feature-specific pages and components live in `frontend/src/features/`.
Shared API functions, layout, and components are under `frontend/src/shared/`.
The season workspace separates setup, teams and rosters, schedule, results, and
standings. A dedicated game page contains scores and player statistics. The
main layout uses a desktop sidebar and a collapsible mobile menu.

## Data flow and state

Components call API functions using Axios and session cookies. TanStack Query
manages server data and mutations; local React state manages selections, forms,
and feedback. The backend independently enforces permissions and business
rules, even where the UI hides or disables actions.

Each workspace section has its own sport and division selection. The selected
division loads the data needed by the current section; the selected team loads
its roster and, when permitted, available players. Setup and team tabs keep
their hidden panels mounted, but navigating to another section or game page
discards unsaved form drafts. Season data has a one-minute freshness period.
Relevant mutations invalidate queries, and **Refresh data** requests an
immediate refresh; stale data is not polled or pushed automatically.

## Styling and validation

The application uses its shared stylesheet, React component state, and
client-side form checks. API errors are displayed to the user; authoritative
validation remains on the backend. The frontend build runs TypeScript checks
and Vite. Planned improvements and limitations are tracked in the
[project roadmap](../checklist.md) and [implementation tracker](../backend/implementation-alignment.md).
