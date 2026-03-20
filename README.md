# Robust Fastapi API

Reference FastAPI API with production-oriented practices: YAML-based configuration, structured logging, request audit middleware, input sanitization (SQL injection and XSS), health checks for PostgreSQL and Redis, and Docker Compose setup.

## Concepts and roadmap

**Current**

- **Observability** – Structured logs (request/response audit, sensitive redaction) and health checks (API, database, Redis).
- **Security** – Input sanitization (SQL injection and XSS) via middleware; reject suspicious payloads before handlers.
- **Auth (local)** – JWT access/refresh plus account activation and password reset via email.
- **Auth (OAuth/PKCE)** – OAuth login with Google/Microsoft using PKCE + callback (requires session/cookies).
- **Real-time** – WebSockets and Server-Sent Events (SSE) using Redis Pub/Sub.
- **Data** – SQL CRUD (PostgreSQL) example with soft delete via `deleted_at` (UUID IDs).
- **Versioning** – API under `/v1/` to allow future backward-compatible changes.
- **Containerization** – Docker and Docker Compose for API, PostgreSQL, and Redis.


**Planned**
- **Data** – Redis cache strategy and NoSQL CRUD (future examples).
- **Integrations** – External APIs and payment providers.

## Introduction

This repository is a minimal but complete FastAPI template that follows clean architecture principles. It includes:

- **Configuration**: Settings loaded from `settings/base.yaml` with environment variable substitution (`${VAR}` and `${VAR:-default}`). A `.env` file at the project root is loaded automatically when the app starts.
- **Security**: Middleware that rejects requests containing common SQL injection or XSS patterns in query params, path, and body.
- **Observability**: Request/response logging (with sensitive field redaction) and a versioned health endpoint (`/v1/health`) that reports API, database, and Redis status.
- **API versioning**: Base routes are under `/v1/`.

## Prerequisites

- **Python** 3.13+
- **Poetry** (dependency and project management)
- **Docker** and **Docker Compose** (optional, for running the API with PostgreSQL and Redis)

## Project setup with Poetry

From the project root:

```bash
poetry install
```

Activate the environment (optional; `poetry run` works without it):

```bash
eval "$(poetry env activate)"
```

This runs `eval "$(poetry env activate)"` inside a shell. When you exit, your terminal returns to the previous state.

## Configuration

Main configuration lives in `settings/base.yaml`. Values can reference environment variables with `${VAR}` or `${VAR:-default}`. The app loads a `.env` file from the project root at startup, so variables defined there are available for substitution. When running with Docker Compose, env vars can also be set in `.env` and are passed to the API container.

## Running locally

**Option 1 – task dev (recommended)**

Starts database and Redis with Docker, then runs the API with uvicorn (reload on port 8080):

```bash
cp .env.example .env
task dev
```

**Option 2 – manual**

Start PostgreSQL and Redis (e.g. `docker compose up -d database redis`), then run the API:

```bash
cp .env.example .env
# Edit .env: POSTGRES_HOST=localhost, POSTGRES_PORT=5432, REDIS_HOST=localhost, REDIS_PORT=6380
poetry run uvicorn robust_fastapi_api.app:app --reload --port 8080
```

## Task build

Builds the API image and runs all services (API, PostgreSQL, Redis) with Docker Compose. Requires a `.env` at the project root (copy from `.env.example`). API at `http://localhost:8080`, PostgreSQL on port `5432`, Redis on port `6380`.

```bash
cp .env.example .env
task build
```

To use another env file: `docker compose --env-file .env.production up --build`.

## Main tasks

[Taskipy](https://github.com/taskipy/taskipy) tasks in `pyproject.toml`. Run with `task <name>`.

| Task | Description |
|------|-------------|
| `format` | Format code with ruff |
| `build` | Format, then build and run API + database + Redis with Docker Compose |
| `dev` | Format, start database and Redis containers, then run API with uvicorn (reload, port 8080) |
| `test` | Format, then run pytest with coverage (robust_fastapi_api, fail under 90%) |

## Endpoints

- `GET /v1/health` – Health check (API status plus database and Redis: `ok`, `error`, or `disabled`)
- `POST /v1/auth/login` – Login with email/password (returns access + refresh tokens)
- `POST /v1/auth/validate` – Validate current access token (returns `user_id` and `token_valid`)
- `POST /v1/auth/refresh` – Refresh access token using the current refresh token
- `POST /v1/auth/logout` – Logout (invalidates access + refresh versions)
- `POST /v1/auth/password-reset/request` – Request password reset (sends email with verification code)
- `POST /v1/auth/password-reset/verify` – Verify password reset code
- `POST /v1/auth/password-reset/confirm` – Confirm password reset (sets new password)
- `POST /v1/users/me` – Create/update an unverified account + send activation email
- `POST /v1/users/activate?token=...` – Activate account using activation token from email
- `GET /v1/users/me` – Get current user info (requires access token)
- `POST /v1/books` – Create a book record
- `GET /v1/books` – List active books (soft-deleted are excluded)
- `GET /v1/books/{book_id}` – Get a single active book
- `PATCH /v1/books/{book_id}` – Update book fields (name / read status)
- `DELETE /v1/books/{book_id}` – Soft delete (`deleted_at` is set)
- `GET /v1/sse/books` – Server-Sent Events stream (notifies on book changes)
- `WS /v1/ws/chat` – WebSocket chat room (broadcast; send JSON `{"user": "name", "message": "text"}`)
- `GET /docs` – Swagger UI
- `GET /redoc` – ReDoc

## Directory structure

```
robust-fastapi-api/
├── settings/
│   └── base.yaml              # Main config (env var substitution)
├── src/
│   └── robust_fastapi_api/
│       ├── app.py             # FastAPI app, middleware, router registration
│       ├── health.py          # Health router (GET /v1/health)
│       ├── domain/
│       │   ├── auth/          # Auth example (JWT login + activation + password reset)
│       │   │   ├── routers/
│       │   │   │   └── auth_router.py
│       │   │   └── services/
│       │   │       └── auth_service.py
│       │   └── users/         # Users example (unverified users + activation + users/me)
│       │       ├── routers/
│       │       │   └── users_router.py
│       │       ├── services/
│       │       │   ├── unverified_user_service.py
│       │       │   └── user_service.py
│       │       ├── repositories/
│       │       │   ├── user_repository.py
│       │       │   ├── unverified_user_repository.py
│       │       │   └── oauth_token_repository.py
│       │       ├── models/
│       │       │   ├── user_model.py
│       │       │   ├── unverified_user_model.py
│       │       │   └── oauth_token_model.py
│       │       └── schemas/
│       │           └── models.py
│       │   ├── crud/          # CRUD example (books read, with soft delete via `deleted_at`)
│       │   │   ├── routers/
│       │   │   │   └── book_router.py
│       │   │   ├── services/
│       │   │   │   └── book_service.py
│       │   │   ├── repositories/
│       │   │   │   └── book_repository.py
│       │   │   ├── models/
│       │   │   │   └── book_model.py
│       │   │   └── schemas/
│       │   │       └── book_schemas.py
│       │   └── sse/           # SSE example (GET /v1/sse/books)
│       │       ├── sse_router.py
│       │       └── sse_service.py
│       │   └── socket/        # WebSocket chat (GET /v1/ws/chat)
│       │       ├── socket_router.py
│       │       └── socket_service.py
│       ├── core/
│       │   ├── settings/      # YAML loader, Pydantic settings
│       │   ├── logging.py     # Structlog configuration
│       │   ├── health.py      # Database and Redis check functions
│       │   ├── datetime.py    # Timezone-aware datetime helpers
│       │   ├── db/
│       │   │   ├── base.py
│       │   │   └── session.py
│       │   ├── redis/
│       │   │   └── session.py
│       │   ├── email/
│       │   │   ├── email.py
│       │   │   └── templates/
│       │   │       ├── account_activation.html
│       │   │       └── password_reset.html
│       │   └── security/
│       │       ├── sanitizer.py  # SQL/XSS pattern detection
│       │       ├── token.py
│       │       └── password.py
│       └── middleware/
│           ├── log_request.py # Request/response audit logging
│           └── sanitize.py   # Input sanitization middleware
├── tests/
├── docker-compose.yml
├── Dockerfile
├── entrypoint.sh
├── pyproject.toml
├── poetry.lock
├── .env.example
└── README.md
```
