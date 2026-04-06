# Epic E2: AI Layer

## Goal

Deliver a production-grade, LangGraph-based agentic pipeline that translates
natural-language analytics questions into structured responses (SQL, KPIs,
charts, narratives) using configurable LLM back-ends.

## Strategic Value

The AI layer is the primary differentiator of DataPrismAI. It must support
arbitrary business domains through persona-aware prompting and a pluggable
skill catalogue — with no use-case hardcoding inside the core pipeline.

## Includes

### E2.1 LangGraph Pipeline Runtime

- `graph_runtime.py` — 13-node StateGraph compiled at startup
- AgentState TypedDict with all fields documented
- Conditional edge logic (fast path vs full path, retry loop)

### E2.2 Guardrail & Safety

- `guardrail_node.py` — blocks greetings, off-topic, gibberish early
- `sql_validator_node.py` — blocks DDL/DML, enforces row limits
- Retry-once loop on executor failure

### E2.3 Persona-Aware Prompting

- `planner_node.py` — classifies intent and selects fast / full path
- `persona_node.py` — injects persona prompt into AgentState
- `apps/api/app/prompts/personas/` — one `.txt` per persona (any domain)

### E2.4 NL-to-SQL

- `vanna_sql_node.py` — LLM SQL generation via Vanna (optional) or direct chain
- `query_router_node.py` — routes SQL to StarRocks or Postgres
- `query_executor_node.py` — executes and returns rows

### E2.5 Visualisation & Insight

- `visualization_node.py` — recommends chart type and ECharts config
- `insight_node.py` — generates narrative summary from result rows
- `recommendation_node.py` — suggests 3 follow-up questions

### E2.6 Skill Catalogue

- `apps/api/app/skills/catalog.py` — registry of pluggable capabilities
- `skills/<name>/SKILL.md` — human-readable specification per capability
- Skill invocation via `skills_node.py` (planned)

## Dependencies

- E1 (Platform Foundation)

## Acceptance Criteria

- [ ] Pipeline finishes in < 5 s for 95th-percentile queries on local hardware
- [ ] Guardrail blocks all DDL / DML SQL strings
- [ ] Retry loop handles StarRocks connection errors without crashing
- [ ] Persona switch changes prompt without code changes (only `.env`)
- [ ] All nodes have module-level docstrings

## Status

In Progress — core pipeline implemented; skills node pending
