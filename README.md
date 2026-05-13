# HireAI Copilot Backend (W4)

FastAPI backend for the HireAI Copilot recruitment platform.

## Stack

- FastAPI
- SQLAlchemy 2.0 (async)
- PostgreSQL (asyncpg)
- Alembic
- Pydantic v2
- JWT (python-jose)

## Structure

- `app/main.py`: FastAPI application entrypoint and router wiring.
- `app/core/`: Config, security, middleware, exception handlers.
- `app/db/`: SQLAlchemy base/session and seed initialization.
- `app/models/`: ORM models for users, candidates, jobs, applications, scores.
- `app/schemas/`: Pydantic request/response models.
- `app/api/`: Route modules.
- `alembic/`: Migration environment and versions.

## Quick Start

1. Create and activate a virtual environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Ensure PostgreSQL is running and `DATABASE_URL` in `.env` is correct.
4. Apply migrations:
   - `alembic upgrade head`
5. Start API:
   - `uvicorn app.main:app --reload`

## Docker Run

If you want everything in containers, use Docker Compose so the API can reach PostgreSQL by service name.

1. Build and start both services:
   - `docker compose up --build`
2. Open the API at:
   - `http://127.0.0.1:8000`
3. Open Swagger UI at:
   - `http://127.0.0.1:8000/docs`

Why this is needed:

- `localhost` inside a container means the container itself, not your machine.
- The Compose file connects the API to the database service using `db:5432`.
- This avoids the `Connection refused` error you hit with plain `docker run`.

## Week 1 Endpoints

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me` (Bearer token)
- `GET /api/candidates`
- `GET /api/jobs`

## Docs

- Swagger UI: `/docs`
- OpenAPI JSON: `/api/openapi.json`

## Seeded Credentials

If no users exist, startup seeds:

- email: `recruiter@hireai.com`
- password: `admin123`
