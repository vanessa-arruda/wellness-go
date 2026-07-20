# Changelog

All notable changes to this project are documented here, grouped by date.

## 2026-07-19

- Added backend project scaffold (`backend/`): FastAPI app, `core` module (config, async DB session, JWT/password security helpers).
- Added `auth` module: `User` model, register/login/refresh service logic, `POST /auth/register`, `/login`, `/refresh` endpoints, and a stubbed `POST /auth/google` (501).
- Added `GET /health` endpoint with a DB connectivity check.
- Added `.env.example`, `backend/Dockerfile`, and root `docker-compose.yml` (Postgres 16 + backend) for local development.
- Added Alembic setup wired to the app's async engine, with the first migration creating the `users` table.
- Added pytest suite (`backend/tests/`) covering health and the full register/login/refresh flow, using an isolated test database with per-test transaction rollback.
- Fixed missing `email-validator` dependency required by `EmailStr` schemas.
- Fixed `passlib`/`bcrypt` incompatibility by pinning `bcrypt<4.1`.
- Added README setup guide and this CHANGELOG.
- Fixed `docker-compose.yml` `db` port collision with a native local Postgres by remapping to host `5433`.
- Added `profile` module: `Profile` model (display name, unit preference, date of birth, height), `GET /profile/me`, `PUT /profile/me` (upsert), and a migration creating the `profiles` table.
- Added `get_current_user` auth dependency (JWT bearer token → `User`) to support authenticated endpoints beyond `auth` itself.
- Added `exercises` module proxying the ExerciseDB (AscendAPI) catalog on RapidAPI instead of storing exercise data locally: `GET /exercises`, `/exercises/search`, `/exercises/{id}`, `/exercises/body-parts`, `/exercises/equipments`, `/exercises/muscles`, `/exercises/exercise-types`, with a process-local TTL cache to stay within the Basic plan's 2,000 requests/month cap.
- Documented the ExerciseDB integration and its plan limits in README.md.
- Added `workout_templates` module: `WorkoutTemplate` + `TemplateExercise` (denormalized ExerciseDB snapshot, no local exercises table to FK against) with full CRUD, and `ScheduleEntry` for assigning a template to specific days of the week over a date range.
- Added weekly workout scheduling with conflict detection: creating an overlapping schedule returns `409` with the conflicting entries; `"override": true` replaces it by **splitting** the conflicting entry around the new date range instead of deleting it, preserving history outside the overridden window.
- Migration creating `workout_templates`, `template_exercises`, `schedule_entries` tables.
- Updated `docs/Architecture.md` to match what's actually built: `exercises` is a proxy (not a local catalog), documented the weekly-scheduling design, and corrected the package manager entry from `uv`/`poetry` to `venv`+`pip`.
- Added `workout_sessions` module: `WorkoutSession` (started from a template, `finished_at` nullable while in progress) + `LoggedSet` (denormalized exercise snapshot, one set logged at a time, `set_number` auto-incrementing per exercise). `POST/GET/DELETE /workout-sessions`, `POST/PUT/DELETE /workout-sessions/{id}/sets/{set_id}`, `POST /workout-sessions/{id}/finish`. Each logged set is persisted immediately, not batched at finish; skipping a template exercise is allowed; sets can be corrected via PUT at any time, including after finishing. Migration creating `workout_sessions`, `logged_sets` tables.
- Added `measurements` module: `WeightEntry` (weight_kg, recorded_at) and `BodyMeasurement` (neck, chest, waist, navel, hips, left/right arm, left/right thigh, left/right calf — all cm) as independent resources with their own dates, since weight is logged far more often than a full measurement pass. Every `BodyMeasurement` field except `recorded_at` is optional, so partial logs (e.g. just waist) are fully supported. Full CRUD under `/measurements/weight` and `/measurements/body`. Migration creating `weight_entries`, `body_measurements` tables.
- Added `mood` module: `MoodEntry` with a `moods` array field (Postgres `mood_tag[]`) supporting multiple tags per check-in from a fixed set of 15 (positive/reflective/negative), plus an optional note. One check-in per day, enforced via a `(user_id, recorded_at)` unique constraint — a duplicate date returns `409`. Full CRUD under `/mood`. Migration creating `mood_entries`.

## 2026-07-20

- Added `dashboard` module (read-only, no tables of its own): `/dashboard/weight-history` and `/body-measurement-history` (ascending, date-filterable) for charting; `/dashboard/today` as a single-call home-screen snapshot (today's scheduled template, whether a session was completed today, today's mood, latest weight); `/dashboard/workout-stats` (session count/rate + per-exercise volume trend within a date range) and `/dashboard/personal-records` (all-time bests per exercise, not date-scoped); `/dashboard/adherence` (scheduled-vs-completed workout days over a range, with a per-day breakdown); and per-resource CSV export (`/dashboard/export/weight.csv`, `/body-measurements.csv`, `/mood.csv`, `/workout-sessions.csv`).
- Added CI: `.github/workflows/backend-tests.yml` runs `ruff check`, verifies the full Alembic migration chain applies cleanly against a from-scratch database (not just the already-migrated dev DB), then runs the full pytest suite — all against a Postgres service container, on every push/PR.
- Fixed CSV injection (CWE-1236) in `dashboard`'s CSV export endpoints: user-supplied free text (mood `note`, workout `exercise_id`/`exercise_name`) was written unescaped into exported cells, so a value starting with `=`/`+`/`-`/`@` could execute as a spreadsheet formula if the export was later opened by the user or someone they shared it with. Found via a security review before merge. Fixed centrally in the shared `_csv_response` helper (prefixes any cell starting with a formula-trigger character with `'`), covering all four export endpoints rather than patching fields individually.
