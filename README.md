# DataPrismAI

> **Enterprise GenBI analytics chatbot** — natural-language questions answered with
> governed SQL, live charts, KPI cards, and narrative insights, powered by a local
> LangGraph agentic pipeline and Ollama LLMs.

---

## Table of Contents

1. [What it does](#what-it-does)
2. [Architecture overview](#architecture-overview)
3. [Quick start](#quick-start)
4. [Folder structure](#folder-structure)
5. [Configuration reference](#configuration-reference)
6. [Changing the data domain](#changing-the-data-domain)
7. [Adding a new AI skill](#adding-a-new-ai-skill)
8. [BMAD project structure](#bmad-project-structure)
9. [Development workflow](#development-workflow)
10. [Contributing](#contributing)

---

## What it does

DataPrismAI lets any business user type a question like _"Which product category
drove the most revenue last quarter?"_ and receive:

- **SQL** — generated, validated, and executed against your OLAP store (StarRocks)
- **Chart** — ECharts visualisation recommended and configured by the AI
- **KPI cards** — headline metrics extracted from the result set
- **Narrative** — 2–4 sentence insight summary with trend callouts
- **Follow-ups** — three suggested next questions

Everything is driven by local LLMs (Ollama), so no data leaves the environment.

---

## Architecture overview

```
Browser (Next.js 15)
  └── /api proxy  ──►  FastAPI (port 8010)
                            │
                     LangGraph 13-node pipeline
                            │
              ┌─────────────┼─────────────────┐
              ▼             ▼                 ▼
         StarRocks       Postgres          Ollama
        (OLAP/serving)  (sessions,      (LLM inference)
                         audit logs)
```

Key components:

| Layer          | Technology                      | Entry point                       |
| -------------- | ------------------------------- | --------------------------------- |
| Frontend       | Next.js 15 + Tailwind + ECharts | `apps/web/src/app/layout.tsx`     |
| API            | FastAPI 0.135 + Pydantic        | `apps/api/main.py`                |
| AI pipeline    | LangGraph 1.1 (13 nodes)        | `apps/api/app/graph_runtime.py`   |
| OLAP store     | StarRocks allin1                | Docker `infra/docker-compose.yml` |
| Metadata       | Postgres 16 + Alembic           | `apps/api/app/db/`                |
| LLM            | Ollama (qwen2.5:7b default)     | Docker                            |
| Semantic layer | YAML metrics/dims/joins         | `data/semantics/`                 |

---

## Quick start

### Prerequisites

- Docker Desktop (WSL2 backend on Windows) or Docker Engine on Linux/macOS
- Python 3.11+
- Node.js 20+
- Ollama CLI (or pull model inside the Docker container)

### 1 — Start infrastructure

```bash
cd infra
docker compose up -d
```

This starts Postgres, StarRocks, Redis, and Ollama. Pull the LLM model:

```bash
docker exec dataprismai-ollama ollama pull qwen2.5:7b
```

### 2 — Configure environment

```bash
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env.local
# Edit both files if your ports/credentials differ from the defaults
```

### 3 — Bootstrap the database

```bash
cd apps/api
pip install -r requirements.txt
alembic upgrade head            # create Postgres tables
```

### 4 — Load sample data (optional)

```bash
cd data/synthetic
python generate_synthetic_data.py --rows 50000
python fast_load.py             # loads into StarRocks
```

### 5 — Start the services

```bash
# In terminal 1
cd apps/api && uvicorn main:app --reload --host 0.0.0.0 --port 8010

# In terminal 2
cd apps/web && npm install && npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

---

## Folder structure

```
dataprismai/
├── apps/
│   ├── api/                    # FastAPI backend
│   │   ├── main.py             # App entry point, router registration
│   │   ├── .env.example        # All supported env vars (documented)
│   │   ├── requirements.txt
│   │   ├── alembic/            # Postgres migration history
│   │   └── app/
│   │       ├── api/            # FastAPI route handlers
│   │       ├── core/
│   │       │   └── config.py   # ★ Single source of truth for all settings
│   │       ├── db/             # SQLAlchemy models + StarRocks connector
│   │       ├── graph_nodes/    # One file per LangGraph node
│   │       ├── graph_runtime.py# LangGraph pipeline definition
│   │       ├── prompts/        # Prompt builders + persona text files
│   │       ├── schemas/        # Pydantic request/response models
│   │       ├── semantic/       # Semantic layer YAML loaders
│   │       ├── services/       # SchemaRegistry, Vanna, etc.
│   │       └── skills/         # Skill catalogue (catalog.py)
│   └── web/                    # Next.js 15 frontend
│       ├── .env.example
│       └── src/
│           ├── app/            # Next.js App Router pages
│           ├── components/
│           │   ├── chat/       # Chat workspace, message cards, prompt input
│           │   ├── charts/     # ECharts wrapper
│           │   ├── explorer/   # Data explorer panel (5 tabs + native SVG ERD)
│           │   └── ui/         # Shared primitives (buttons, badges, etc.)
│           ├── lib/            # API client, hooks, utilities
│           └── types/          # Shared TypeScript types
├── bmad/                       # BMAD project artefacts
│   ├── prd.md                  # Product Requirements Document
│   ├── architecture.md
│   ├── epics/                  # E1–E5 epics
│   └── stories/                # S1–S15 user stories
├── data/
│   ├── ddl/                    # StarRocks + Postgres DDL scripts
│   ├── scripts/                # Bootstrap helpers
│   ├── semantics/              # Metric / dimension / join YAML
│   └── synthetic/              # Data generators
├── infra/
│   ├── docker-compose.yml      # Full local dev stack
│   └── README.md
└── skills/                     # Human-readable SKILL.md per capability
    ├── chart-recommender/
    ├── insight-generator/
    ├── nl2sql/
    ├── query-router/
    └── sql-validator/
```

---

## Configuration reference

All configuration is in environment variables. Copy the example files and
edit to match your environment:

```bash
cp apps/api/.env.example  apps/api/.env
cp apps/web/.env.example  apps/web/.env.local
```

Key variables:

| Variable             | Default                     | Description                     |
| -------------------- | --------------------------- | ------------------------------- |
| `OLLAMA_HOST`        | `http://localhost:11434`    | Ollama server URL               |
| `OLLAMA_MODEL`       | `qwen2.5:7b`                | Model tag to use for generation |
| `USE_VANNA`          | `false`                     | Enable Vanna SQL path           |
| `STARROCKS_HOST`     | `localhost`                 | StarRocks FE host               |
| `STARROCKS_DATABASE` | `cc_analytics`              | OLAP database name              |
| `DATABASE_URL`       | `postgresql://...`          | Postgres connection string      |
| `ALLOWED_ORIGINS`    | `http://localhost:3000,...` | Comma-separated CORS origins    |

Full reference: [apps/api/.env.example](apps/api/.env.example)

---

## Changing the data domain

DataPrismAI is **not hardcoded to any specific dataset**. To use it with your
own data:

1. **Point StarRocks** at your database: set `STARROCKS_DATABASE` in `.env`.
2. **Run the schema registry**: it auto-discovers all tables on startup — no
   manual schema files required.
3. **Update semantic YAML** in `data/semantics/` to define your metrics,
   dimensions, and joins.
4. **Change the persona** (optional): add a `.txt` file in
   `apps/api/app/prompts/personas/` and set `PERSONA` in `.env`.
5. **Load data**: use `data/scripts/bootstrap_and_load.py` or your own pipeline.

---

## Adding a new AI skill

1. Create `skills/<name>/SKILL.md` — define inputs, outputs, guardrails.
2. Create `apps/api/app/graph_nodes/<name>_node.py` — implement the node
   function `(state: AgentState) -> dict`.
3. Register it in `apps/api/app/graph_runtime.py`:
   ```python
   graph.add_node("<name>", <name>_node)
   graph.add_edge("previous_node", "<name>")
   ```
4. Add it to `apps/api/app/skills/catalog.py`.

---

## BMAD project structure

```
bmad/
├── project-brief.md    # One-page problem statement
├── prd.md              # Product Requirements Document
├── architecture.md     # Technical architecture decisions
├── story-map.md        # Full story mapping grid
├── epics/
│   ├── E1-platform-foundation.md
│   ├── E2-ai-layer.md
│   ├── E3-data-layer.md
│   ├── E4-ui-ux-shell.md
│   └── E5-enterprise-ops.md
└── stories/
    └── S1–S15 *.md     # Detailed user stories with AC
```

---

## Development workflow

```bash
# Run all tests
cd apps/api && pytest tests/ -v

# Check TypeScript
cd apps/web && npx tsc --noEmit

# Apply new DB migrations
cd apps/api && alembic upgrade head

# Lint Python
cd apps/api && ruff check app/
```

---

## Contributing

This project uses the BMAD framework. All new features start as a story in
`bmad/stories/`. Implementation is tracked via Git commits referencing the
story ID (e.g. `feat(S16): add health-check endpoint`).

See [bmad/prd.md](bmad/prd.md) for the current backlog priorities.
