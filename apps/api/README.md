# DataPrismAI — FastAPI Backend

The API layer runs the LangGraph agentic pipeline, serves REST endpoints for
the frontend, and manages the operational Postgres database.

---

## Contents

- [Running locally](#running-locally)
- [Environment variables](#environment-variables)
- [Project layout](#project-layout)
- [Adding a new endpoint](#adding-a-new-endpoint)
- [Database migrations](#database-migrations)
- [Testing](#testing)

---

## Running locally

```bash
# From repo root
cp apps/api/.env.example apps/api/.env
cd apps/api
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload --host 0.0.0.0 --port 8010
```

The API is available at `http://localhost:8010`.
Interactive docs: `http://localhost:8010/docs`

---

## Environment variables

Copy `.env.example` to `.env` and edit as needed.
**Never commit `.env`** — it is `.gitignore`-ed.

All env vars are loaded once into `app/core/config.py` (`Settings` class).
Nothing else reads `os.getenv()` directly.

---

## Project layout

```
apps/api/
├── main.py                  # App entry point — routers, CORS, lifespan
├── .env.example             # Documented env-var template
├── requirements.txt
├── alembic.ini
├── alembic/
│   └── versions/            # Migration files (committed)
└── app/
    ├── api/                 # Route handlers
    │   ├── chat.py          # POST /chat/query  ← main NL analytics endpoint
    │   ├── semantic.py      # GET  /semantic/*  ← metric / dimension browser
    │   ├── skills.py        # GET  /skills      ← skill catalogue
    │   ├── langgraph.py     # GET  /langgraph/* ← debug / state endpoints
    │   └── store.py         # CRUD /api/store/* ← session & report persistence
    ├── core/
    │   └── config.py        # ★ ALL settings come from here
    ├── db/
    │   ├── models.py        # SQLAlchemy ORM models
    │   ├── session.py       # Engine + session factory
    │   └── starrocks.py     # StarRocks MySQL connector
    ├── graph_nodes/         # One Python file per LangGraph node:
    │   ├── guardrail_node.py
    │   ├── entity_resolver_node.py
    │   ├── planner_node.py
    │   ├── persona_node.py
    │   ├── semantic_resolver_node.py
    │   ├── vanna_sql_node.py
    │   ├── sql_validator_node.py
    │   ├── query_router_node.py
    │   ├── query_executor_node.py
    │   ├── result_evaluator_node.py
    │   ├── visualization_node.py
    │   ├── insight_node.py
    │   ├── recommendation_node.py
    │   ├── response_node.py
    │   └── persist_node.py
    ├── graph_runtime.py     # Compiles the StateGraph; defines AgentState
    ├── prompts/
    │   ├── personas/        # <name>.txt — one persona per deployment domain
    │   ├── persona_loader.py
    │   ├── prompt_builder.py
    │   └── sql_prompt_builder.py
    ├── schemas/
    │   └── chat.py          # Pydantic request/response models for /chat
    ├── semantic/            # YAML loader for metrics/dimensions/joins
    └── services/
        ├── schema_registry.py  # Auto-discovers StarRocks schema at startup
        ├── vanna_service.py    # Vanna NL-to-SQL (optional path)
        └── vanna_training_context.py
```

---

## Adding a new endpoint

1. Create `app/api/<name>.py` with an `APIRouter`.
2. Import and register in `main.py`:
   ```python
   from app.api.<name> import router as <name>_router
   app.include_router(<name>_router, prefix="/<name>", tags=["<name>"])
   ```
3. Add Pydantic models to `app/schemas/` if needed.

---

## Database migrations

```bash
# After changing an ORM model
alembic revision --autogenerate -m "describe change"

# Apply all pending migrations
alembic upgrade head

# Roll back one step
alembic downgrade -1
```

---

## Testing

```bash
pytest tests/ -v
```

Tests use a test Postgres database; set `DATABASE_URL` to a test DB in `.env`
before running. StarRocks tests are skipped if `STARROCKS_HOST` is unreachable.
