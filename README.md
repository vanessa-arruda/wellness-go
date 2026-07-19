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
