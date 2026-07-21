# wellness-go

Personal wellness assistant project to improve health habits.

## Architecture

Modular-monolith FastAPI backend (Python 3.13), PostgreSQL, SQLAlchemy 2.0 (async), Alembic migrations, JWT auth (email/password now, Google OAuth stubbed). A separate Next.js/TypeScript frontend (`frontend/`) consumes the backend over HTTP/JSON only.

## Backend

### Prerequisites

- Python 3.13
- Docker (for Postgres + containerized backend)

### Local setup (without Docker)

```bash
cd backend
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env  # fill in DATABASE_URL, JWT_SECRET, etc.
alembic upgrade head
uvicorn app.main:app --reload
```

### Running with Docker Compose

```bash
docker compose up --build
```

This starts Postgres and the backend together. On a fresh database volume, run migrations once the containers are up:

```bash
docker compose exec backend alembic upgrade head
```

### Tests

```bash
cd backend
source .venv/bin/activate
python -m pytest
```

Tests run against a separate `wellness_test` Postgres database (see `backend/tests/conftest.py`) with per-test transaction rollback for isolation.

### CI

`.github/workflows/backend-tests.yml` runs on every push/PR: `ruff check`, `ruff format --check`, a from-scratch `alembic upgrade head` against a throwaway database (catches a broken migration chain, not just "works on my already-migrated dev DB"), then the full pytest suite against its own Postgres service container.

`.github/workflows/frontend-tests.yml` runs on every push/PR: `tsc --noEmit`, `eslint`, `prettier --check`, then `next build` — same checks as the local pre-commit hook below, so a commit that passes locally should always pass CI.

### Local git hooks

Run once per clone to enable them (git hooks are local-only, not something a repo can activate on its own):

```bash
make install-hooks
```

This points git at the versioned `.githooks/` directory, enabling:

- **`commit-msg`** — rejects commits whose message doesn't match `type(wellness-go): description` (type is one of `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`).
- **`pre-commit`** — rejects the commit if either app fails its checks:
  - `backend/`: `ruff check` (lint, including a hard 120-character line-length limit via `E501`) and `ruff format --check`.
  - `frontend/`: `tsc --noEmit`, `eslint` (including a hard 120-character `max-len` — Prettier's `printWidth` alone doesn't cover comments or unbreakable strings, so `max-len` is the real enforcement, scoped off `src/components/ui/**` since shadcn's long Tailwind `className` strings aren't meant to be wrapped), and `prettier --check`.

Other Makefile targets: `make lint` / `make format` / `make format-check` / `make test` (backend); `make frontend-lint` / `make frontend-format` / `make frontend-format-check` / `make frontend-build` (frontend); `make check` runs everything both CI workflows run.

### API

- `GET /health` — DB connectivity check
- `POST /auth/register` — email/password registration, returns `{access_token, token_type}`; sets the refresh token as an httpOnly cookie (see below)
- `POST /auth/login` — email/password login, same response/cookie shape as register
- `POST /auth/refresh` — reads the refresh token from the cookie (no body), returns a new access token and rotates the cookie
- `POST /auth/logout` — clears the refresh-token cookie
- `POST /auth/google` — not yet implemented (501)
- `GET /profile/me` / `PUT /profile/me` — read/upsert the current user's profile (auth required)
- `GET /exercises`, `/exercises/search`, `/exercises/{id}`, `/exercises/body-parts`, `/exercises/equipments`, `/exercises/muscles`, `/exercises/exercise-types` — proxy the ExerciseDB catalog below (auth required)
- `POST /workout-templates`, `GET /workout-templates`, `GET /workout-templates/{id}`, `PUT /workout-templates/{id}`, `DELETE /workout-templates/{id}` — template CRUD (name + ordered list of exercises with target sets/reps; auth required)
- `POST /workout-templates/{id}/schedule` — assign a template to one or more days of the week for a date range; `GET /workout-templates/schedule` — list the current user's full schedule; `DELETE /workout-templates/schedule/{entry_id}` — remove one entry (auth required)
- `POST /workout-sessions` (starts from a template), `GET /workout-sessions`, `GET /workout-sessions/{id}`, `DELETE /workout-sessions/{id}` — workout session CRUD (auth required)
- `POST /workout-sessions/{id}/sets`, `PUT /workout-sessions/{id}/sets/{set_id}`, `DELETE /workout-sessions/{id}/sets/{set_id}` — log/edit/remove one set at a time while the session is in progress; `POST /workout-sessions/{id}/finish` — mark it done (auth required)
- `POST/GET /measurements/weight`, `PUT/DELETE /measurements/weight/{id}` — weight history (auth required)
- `POST/GET /measurements/body`, `PUT/DELETE /measurements/body/{id}` — body circumference measurements (auth required)
- `POST/GET /mood`, `PUT/DELETE /mood/{id}` — mood check-ins, one per day (auth required)
- `GET /dashboard/weight-history`, `/dashboard/body-measurement-history` — chronological (ascending), optionally filtered by `start_date`/`end_date` (auth required)
- `GET /dashboard/today` — today's scheduled template, whether a session was completed today, today's mood, latest weight (auth required)
- `GET /dashboard/workout-stats`, `/dashboard/personal-records` — session count/rate + per-exercise volume trend over a date range, and all-time PRs per exercise (auth required)
- `GET /dashboard/adherence` — scheduled vs. completed workout days over a date range, with a per-day breakdown (auth required)
- `GET /dashboard/export/weight.csv`, `/body-measurements.csv`, `/mood.csv`, `/workout-sessions.csv` — per-resource data export (auth required)

### Auth token strategy

Matches Architecture.md's original decision (the initial implementation had drifted from it — both tokens were returned in the JSON body with no cookies at all; fixed when frontend work started since the frontend needs to build against the correct contract). The **access token** is short-lived (15 min default) and returned in the JSON response body — the frontend holds it in memory only, never `localStorage`, since anything JS-readable is readable by an XSS payload too. The **refresh token** is set as an `HttpOnly` cookie (`Path=/auth`, `SameSite=Lax`) — JavaScript can never read it, so even a successful XSS can't exfiltrate it; the browser just sends it automatically on requests to `/auth/*`. `COOKIE_SECURE` must be `True` in production (HTTPS) — it's `False` by default only because browsers refuse `Secure` cookies over plain local HTTP. `CORSMiddleware` is configured with `allow_credentials=True` and an explicit `FRONTEND_ORIGIN` (required — credentials mode disallows the `*` wildcard origin).

Known follow-up for whenever frontend and backend deploy to genuinely different domains (not just different local ports, which browsers treat as the same "site" for cookie purposes): `SameSite=Lax` won't be sent on cross-site fetch requests, so it'll need to become `SameSite=None` (paired with `Secure=True`, which is mandatory for `None`).

### Exercise catalog (ExerciseDB)

The exercise catalog isn't stored in our own database — the backend proxies [ExerciseDB (AscendAPI) on RapidAPI](https://rapidapi.com/ascendapi/api/edb-with-videos-and-images-by-ascendapi) so users pick from a real catalog instead of us maintaining one. The RapidAPI key is server-side only (`EXERCISEDB_API_KEY` in `backend/.env`) and never reaches the frontend; responses are cached in-process (1 hour for exercise lists, 24 hours for reference data like body parts/equipment) since the plan below allows caching and has a hard monthly cap.

Current subscription: **Basic Plan**

| Limit | Value |
| --- | --- |
| Requests | 2,000 / month (hard limit) |
| Exercise library size | 200 |
| Media calls | Unlimited |
| Videos / images | Included, watermarked |
| Caching | Allowed |
| Languages | English translations |

A **Custom Enterprise Plan** exists with 3D exercise videos, descriptive step images, and a 1,000 requests/hour rate limit, for if the Basic plan's 200-exercise library or monthly cap becomes limiting.

### Workout scheduling

A workout template (e.g. "A", "B") can be assigned to specific days of the week over a date range — e.g. template A on Mon/Wed, template B on Tue/Thu, both from 2026-07-20 through some end date. Scheduling a day that's already claimed by another schedule in an overlapping date range returns `409` with the conflicting entries; resubmitting with `"override": true` replaces it. Overriding **splits** the conflicting entry around the new range rather than deleting it outright — e.g. replacing "Mondays from Aug 1 onward" only truncates the old entry to end July 31, it doesn't erase the Mondays before that.

### Workout sessions

A session always starts from a template. Sets are logged one at a time as the workout happens (`POST /workout-sessions/{id}/sets`) — each call persists immediately, nothing is held until the end. `set_number` auto-increments per exercise within the session. Skipping a template exercise entirely is fine — it just has no logged sets. Mistakes can be fixed via `PUT .../sets/{set_id}` at any point, including after the session is finished. `POST /workout-sessions/{id}/finish` just stamps a `finished_at` timestamp and blocks further *new* sets — the data was already saved as you went.

### Measurements

Weight (`/measurements/weight`) and body circumference measurements (`/measurements/body`) are separate resources with independent dates, since weight is typically logged far more often than a full measurement pass. Body measurements track neck, chest, waist, navel (umbilical — distinct from waist), hips, left/right arm, left/right thigh, and left/right calf, all in cm. Every field except `recorded_at` is optional — logging just `waist_cm` leaves the rest `null`, no need to fill in a full set every time.

### Mood

One check-in per day (`user_id` + `recorded_at` is unique — a second `POST` for the same date returns `409`), but each check-in can carry **multiple** mood tags rather than a single value, since a day is rarely just one feeling. Tags are a fixed set of 15, stored as a Postgres array column (`mood_tag[]`): positive (joyful, peaceful, hopeful, energetic, confident), reflective (nostalgic, contemplative, inspired, relieved, curious), and negative (anxious, frustrated, gloomy, tense, irritable). An optional free-text `note` rounds it out.

### Dashboard

Read-only aggregation over the other modules — no tables of its own. `/dashboard/today` gives a single-call snapshot for a home screen. `/dashboard/workout-stats` groups logged-set volume (`weight × reps`) by exercise and by day within a date range, for progress charts; `/dashboard/personal-records` is deliberately **not** date-scoped, since PRs are conventionally all-time bests. `/dashboard/adherence` expands `schedule_entries` into actual calendar dates within a range and checks whether *any* session was completed on each one (lenient — not strictly matched to the scheduled template), returning both a summary percentage and a per-day breakdown for a calendar view. CSV exports are one file per resource, matching how the data is already split by module, and cover a user's full history (not date-filtered).

## Frontend

Next.js 16 (App Router) + TypeScript + Tailwind CSS + shadcn/ui, in `frontend/`. Talks to the backend only over HTTP/JSON (`NEXT_PUBLIC_API_URL`) — never imports backend code.

### Prerequisites

- Node.js 20+ (`.nvmrc` pins `20.20.2` — run `nvm use` in `frontend/` if you use nvm)

### Local setup

```bash
cd frontend
npm install
cp .env.example .env.local  # NEXT_PUBLIC_API_URL, defaults to http://localhost:8000
npm run dev
```

Requires the backend running (see above) with `FRONTEND_ORIGIN=http://localhost:3000` in `backend/.env` (already the default) for CORS to allow the browser calls.

### Auth flow

The access token lives in memory only (React context, `src/lib/auth-context.tsx`) — never `localStorage`. The refresh token is the backend's `HttpOnly` cookie (see backend's Auth token strategy above); the frontend never reads or stores it directly, the browser just attaches it automatically on calls to the backend with `credentials: 'include'`. On mount, `AuthProvider` attempts a silent `POST /auth/refresh` to restore a session across page reloads. `fetchWithAuth` (exposed via `useAuth()`) wraps API calls, retrying once through a fresh refresh on a `401`. `ProtectedRoute` (`src/components/protected-route.tsx`) redirects to `/login` if no session after the initial load resolves.

### Pages (first vertical slice)

- `/login`, `/register` — email/password forms
- `/dashboard` — today's scheduled workout, completion status, today's mood, latest weight (calls `GET /dashboard/today`)
- `/` redirects to `/dashboard`, which redirects to `/login` if unauthenticated

Everything else the backend exposes (exercises, templates, sessions, measurements, mood logging, full dashboard stats) has no frontend yet.
