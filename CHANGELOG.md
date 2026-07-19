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
