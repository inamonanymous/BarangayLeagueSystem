# Barangay League System

A work-in-progress league management application for organizing seasons, sports, divisions, teams, players, and rosters. The backend uses Flask and SQLAlchemy; the frontend uses React and TypeScript.

## Current progress

- Session login and role-protected administrative actions.
- Season lifecycle, sport and division catalogs, and season configuration.
- Team registration and management, player profiles, and team rosters.
- A roster-readiness check before moving a season to Ongoing.
- Optional season-level adult voter verification, using player voter IDs recorded by season year.
- Manual game scheduling and rescheduling for Ongoing seasons, with team and venue overlap checks.
- Game score entry, Administrator finalization and reopening, and division win/loss standings computed from finalized results.
- Administrator-configured sport statistics, Played/DNP game participation, and score reconciliation before finalization.
- Season workspace with a status-based overview and separate setup, teams, schedule, results, and standings sections; game details include scores and player statistics.
- A desktop sidebar and collapsible mobile navigation, with selective loading and a manual refresh for cached season data.
- Development-only sample teams and players, with a read-only verification command.

Game cancellation, managed venues, season/career statistics, and playoffs are **not implemented yet**. Statistics require the latest database migration; back up and restore-test your database before upgrading. See the [project roadmap](docs/checklist.md), [backend checklist](docs/backend/checklist.md), and [implementation alignment tracker](docs/backend/implementation-alignment.md) for details and known gaps. The V1 design documents describe targets, not necessarily implemented behavior.

For feature-by-feature diagrams and code entry points, see the [current system flowcharts](docs/diagrams/system-feature-flowcharts.md), including [PlantUML previews](docs/diagrams/system-feature-flowcharts.md#plantuml-flowcharts-for-vs-code).

## Requirements

- Python 3.10 (used in the existing development environment).
- Node.js compatible with the locked frontend dependencies: Node 20.19.x or 22.12+.
- A MySQL database and an existing Administrator account for administrative actions.

**Fresh database limitation:** the first migration expects a pre-existing legacy `users` table. There is currently no supported clean-database migration or first-administrator bootstrap workflow. Use an existing development database, or resolve those prerequisites before attempting a fresh setup. Do not run `repair_db.py` as a setup shortcut: it is a legacy repair script, not a supported bootstrap procedure.

## Local development on Windows

Run these commands from the repository root in PowerShell:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
Set-Location frontend
npm ci
```

`npm ci` replaces the contents of `frontend\node_modules`. This repository currently tracks installed dependencies, so review the repository hygiene warning below before running it in an existing checkout.

In a new terminal, set a development database URL and secret for the current process, then start the backend:

```powershell
Set-Location backend
$env:DATABASE_URL = "mysql+pymysql://<user>:<password>@localhost:3306/<database>"
$env:SECRET_KEY = "<local-development-secret>"
..\.venv\Scripts\python.exe -m flask --app wsgi run
```

Replace the placeholders with local values; do not commit credentials. Alternatively, the backend loads environment variables from `.env`. Without `DATABASE_URL`, it defaults to a local MySQL database named `barangayleague`. The backend serves the API at `http://127.0.0.1:5000/api/v1`; its health endpoint is `/api/v1/health/`.

In another terminal:

```powershell
Set-Location frontend
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api` requests to the backend on port 5000. Use an existing Administrator account to manage seasons, teams, players, and rosters; the application does not currently provision the first account.

To view the app on another device connected to the same trusted Wi-Fi network, run `npm start` from `frontend` instead of `npm run dev`. Vite will listen on the network interface. On the computer running the app, use `ipconfig` to find the Wi-Fi adapter's IPv4 address; on the other device, open `http://<computer-ip>:5173` (for example, `http://192.168.1.20:5173`). Allow the connection on **Private networks** if Windows Firewall prompts you. Keep the backend running on the computer: Vite proxies the other device's `/api` requests to `127.0.0.1:5000`, so the backend does not need to be exposed separately. Do not port-forward or expose the development server to the public internet.

For an existing database with the required legacy schema, back up the database and review its migration state before running `..\.venv\Scripts\python.exe -m flask --app wsgi db upgrade` from `backend`. The migration chain is not a complete fresh-install solution. The voter-rule migration defaults existing seasons to non-strict and does not import historical eligibility numbers; an administrator must enter year-specific IDs manually.

Administrators can enable the adult voter requirement when creating a season or
while it is in Planning. Player profiles can be created without an ID. For a
strict season, record the player's voter ID for that season's year on the
Players page and verify it once per season when adding them to a roster.
Verification is reused across sports. Changing the ID requires re-verification;
unverified adults prevent a strict season from moving to Ongoing. Verification
is a manual administrator check, not an external voter-registry lookup.

## Session cleanup

Sessions are stored in `backend\flask_session`. Size-based eviction is disabled;
expired files remain until cleaned up. Stop **all** application servers using
this directory before running the cleanup, so a session cannot be refreshed
while its file is being removed:

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m flask --app wsgi cleanup-expired-sessions --confirm-stopped
```

The command removes expired session files only. It can be scheduled during a
maintenance window when all servers are stopped. Monitor disk usage, since
files accumulate if cleanup is not run. Do not delete the whole directory while
the app is running; doing so would log users out.

## Testing

From `backend`, run the backend suite against its in-memory SQLite testing configuration:

```powershell
..\.venv\Scripts\python.exe -m pytest
```

From `frontend`, run the TypeScript check and production build:

```powershell
npm run build
```

## Demo data

Demo scripts run only when explicitly invoked, not on application startup or browser refresh. They use the configured development `DATABASE_URL`; **never run them against production**.

The team seed requires the existing `DEMO - Registration Season 2027` season to be in Registration and within its registration window, plus an active Administrator ID. It creates fictional Junior and Senior teams and players. For strict seasons, adult demo players receive explicitly fictional voter details marked as verified by that Administrator. From `backend`:

```powershell
..\.venv\Scripts\python.exe seed_demo_teams.py --actor-id <administrator-user-id>
..\.venv\Scripts\python.exe seed_demo_teams.py --check
```

Reruns skip existing entries and may create missing ones. `--check` is read-only and reports sample-data problems and incomplete active teams. Operations commit as they run, so an error can leave partial demo data. The older `seed_demo_seasons.py` creates fixed-date demo seasons and has season-status and registration-window prerequisites; see the [alignment tracker](docs/backend/implementation-alignment.md) before using it.

## Repository structure

- `backend/` - Flask API, application services and policies, models, migrations, tests, and demo scripts.
- `frontend/` - React application and shared API client.
- `docs/` - project roadmap, architecture, workflows, and implementation tracker.

## Before uploading

This repository currently tracks generated dependencies, Python bytecode, frontend build outputs, and Flask session files. Review tracked files and remove runtime/session data and generated dependencies from version control before publishing; adding ignore rules alone will not untrack existing files. Session files may contain sensitive authentication state. Do not commit credentials, `.env` files, or real player data. These cleanup steps have not yet been performed.
