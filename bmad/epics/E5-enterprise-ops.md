# Epic E5: Enterprise Operations

## Goal

Make DataPrismAI production-deployable: configuration is fully environment-
driven, secrets never hard-coded, Docker Compose spins up all services with
one command, and enough logging / health-check infrastructure exists for
operations teams to monitor the platform.

## Strategic Value

This epic is what separates a demo from a deployable product. Without it
the platform is tied to a single developer laptop; with it the same codebase
runs in any cloud or on-premises environment by changing environment variables.

## Includes

### E5.1 Environment Configuration

- `apps/api/.env.example` — documented template for all 20+ API env vars
- `apps/web/.env.example` — documented template for frontend env vars
- `apps/api/app/core/config.py` — single `Settings` class; no env var reads
  outside this module
- `.env` files are `.gitignore`-ed; `.env.example` files are committed

### E5.2 Docker Compose Stack

- `infra/docker-compose.yml` — single file to launch:
  - Postgres 16 (`:5432`)
  - StarRocks allin1 (`:9030` MySQL, `:8030` HTTP)
  - Redis 7 (`:6379`)
  - Ollama (`:11434` internal, `:11435` host)
- `infra/README.md` — explains ports, credentials, data volumes

### E5.3 Health & Observability

- `GET /healthz` endpoint in `main.py` — returns service versions and DB status
- Structured logging via Python `logging` with ISO timestamps
- All node entry/exit logged at DEBUG level with elapsed time

### E5.4 Alembic Migrations

- `apps/api/alembic/` — version-controlled Postgres schema history
- `alembic upgrade head` — safe to run on any existing DB
- New DDL must always come with a corresponding migration file

### E5.5 CI/CD (Planned)

- GitHub Actions workflow (`.github/workflows/`) — lint, test, Docker build
- Branch protection on `main`; all merges via PR

## Dependencies

- E1, E2, E3, E4

## Acceptance Criteria

- [ ] `docker compose up -d` starts all services with zero manual steps
- [ ] `cp apps/api/.env.example apps/api/.env && uvicorn main:app` boots cleanly
- [ ] No secrets in source control (CI secret scanning passes)
- [ ] `/healthz` returns 200 with all component statuses
- [ ] `pytest apps/api/tests/` passes after fresh `docker compose up`

## Status

In Progress — Docker Compose operational; env example files created;
CI/CD and `/healthz` pending
