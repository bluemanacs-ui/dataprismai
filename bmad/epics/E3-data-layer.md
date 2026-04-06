# Epic E3: Data Layer

## Goal

Provide a robust, multi-engine data layer that connects StarRocks (OLAP serving),
Postgres (operational store), and a governed semantic layer (metrics, dimensions,
joins) so the AI layer always works from accurate, governed context.

## Strategic Value

Analytics AI is only as good as the data underneath it. This epic ensures
all SQL is generated against a schema the system actually knows, and all
metrics are governed through a single semantic registry.

## Includes

### E3.1 Schema Registry

- `apps/api/app/services/schema_registry.py`
- Auto-discovers all tables and columns from StarRocks at startup
- Wraps `DESCRIBE TABLE` results into a structured SchemaRegistry object
- Used by SQL Prompt Builder and Semantic Resolver to provide real-time context

### E3.2 StarRocks Connector

- `apps/api/app/db/starrocks.py`
- Thin `mysql-connector-python` wrapper around StarRocks MySQL protocol
- Connection parameters fully driven by `STARROCKS_*` env vars
- Returns results as `list[dict]`

### E3.3 Postgres Operational Store

- `apps/api/app/db/session.py` — SQLAlchemy engine / session factory
- `apps/api/app/db/models.py` — Session, QueryLog, Report ORM models
- `alembic/` — migration history; run `alembic upgrade head` to apply
- Stores chat sessions, per-query audit logs, and report snapshots

### E3.4 Semantic Layer

- `data/semantics/` — YAML definitions for metrics, dimensions, joins
- `data/ddl/` — DDL scripts for StarRocks (raw + data products) and Postgres
- `apps/api/app/semantic/` — Python loaders that read the YAML definitions
- A Semantic Resolver node resolves user entities to governed metric names

### E3.5 Synthetic / Seed Data

- `data/synthetic/generate_banking_data.py` — generates domain-agnostic OLAP
  sample data (schema mirrors `cc_analytics`, fully configurable row counts)
- `data/scripts/bootstrap_and_load.py` — one-shot bootstrap for local dev

## Dependencies

- E1 (Platform Foundation)

## Acceptance Criteria

- [ ] SchemaRegistry populated on first request with zero manual config
- [ ] All `STARROCKS_*` and `DATABASE_URL` env vars documented in `.env.example`
- [ ] Alembic migrations idempotent — `alembic upgrade head` runs on a clean DB
- [ ] Semantic YAML validated against active schema on load (no silent mismatch)

## Status

In Progress — schema registry and DB connectors implemented; semantic loader
fully functioning; Alembic migrations current
