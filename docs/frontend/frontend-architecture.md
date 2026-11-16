# Frontend Architecture

## Current implementation

The frontend is a React and TypeScript single-page application built with Vite.
[main.tsx](../../frontend/src/main.tsx) provides React Router and a TanStack
Query client; [App.tsx](../../frontend/src/App.tsx) defines browser routes.
See [Frontend Routes and URLs](frontend-routes.md) for pages and API endpoints.

Feature-specific pages and components live in `frontend/src/features/`.
Shared API functions, layout, and components are under `frontend/src/shared/`.
The season configuration feature contains the nested team, roster, and game
schedule sections; there are no separate game or standings pages yet.

## Data flow and state

Components call API functions using Axios and session cookies. TanStack Query
manages server data and mutations; local React state manages selections, forms,
and feedback. The backend independently enforces permissions and business
rules, even where the UI hides or disables actions.

On the season configuration page, sport, division, and team tabs control which
queries are enabled. The selected division loads teams and games; the selected
team loads its roster and, when permitted, available players. Season-page data
has a one-minute freshness period. Relevant mutations invalidate queries, and
**Refresh data** requests an immediate refresh; stale data is not polled or
pushed automatically. Hidden tab panels remain mounted to preserve drafts.

## Styling and validation

The application uses its shared stylesheet, React component state, and
client-side form checks. API errors are displayed to the user; authoritative
validation remains on the backend. The frontend build runs TypeScript checks
and Vite. Planned improvements and limitations are tracked in the
[project roadmap](../checklist.md) and [implementation tracker](../backend/implementation-alignment.md).
