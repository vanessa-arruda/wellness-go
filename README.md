# wellness-go

Personal wellness assistant project to improve health habits.

## Architecture

Modular-monolith FastAPI backend (Python 3.13), PostgreSQL, SQLAlchemy 2.0 (async), Alembic migrations, JWT auth (email/password now, Google OAuth stubbed). A separate Next.js/TypeScript frontend is planned for a later pass.

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

### API

- `GET /health` — DB connectivity check
- `POST /auth/register` — email/password registration, returns a JWT access/refresh pair
- `POST /auth/login` — email/password login
- `POST /auth/refresh` — exchange a refresh token for a new pair
- `POST /auth/google` — not yet implemented (501)
- `GET /profile/me` / `PUT /profile/me` — read/upsert the current user's profile (auth required)
- `GET /exercises`, `/exercises/search`, `/exercises/{id}`, `/exercises/body-parts`, `/exercises/equipments`, `/exercises/muscles`, `/exercises/exercise-types` — proxy the ExerciseDB catalog below (auth required)
- `POST /workout-templates`, `GET /workout-templates`, `GET /workout-templates/{id}`, `PUT /workout-templates/{id}`, `DELETE /workout-templates/{id}` — template CRUD (name + ordered list of exercises with target sets/reps; auth required)
- `POST /workout-templates/{id}/schedule` — assign a template to one or more days of the week for a date range; `GET /workout-templates/schedule` — list the current user's full schedule; `DELETE /workout-templates/schedule/{entry_id}` — remove one entry (auth required)
- `POST /workout-sessions` (starts from a template), `GET /workout-sessions`, `GET /workout-sessions/{id}`, `DELETE /workout-sessions/{id}` — workout session CRUD (auth required)
- `POST /workout-sessions/{id}/sets`, `PUT /workout-sessions/{id}/sets/{set_id}`, `DELETE /workout-sessions/{id}/sets/{set_id}` — log/edit/remove one set at a time while the session is in progress; `POST /workout-sessions/{id}/finish` — mark it done (auth required)

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
