# DataPrismAI Architecture

## Frontend
- Next.js
- Tailwind
- ChatGPT-style chat UX
- Explorer, SQL, chart, and insights panels

## Backend
- FastAPI
- LangChain as thin LLM/tool layer
- Service-oriented modules

## Query Engines
- Trino for federation and exploratory queries
- StarRocks for accelerated serving and repeated KPI workloads

## Semantic Layer
- dbt + semantic models
- governed metrics, dimensions, entities, joins

## AI Layer
- Local model runtime support
- persona-aware prompting
- skills-based orchestration through BMAD-defined capabilities

## Delivery Model
- BMAD for brief, PRD, architecture, epics, stories
- `SKILL.md` per capability
- Git/GitHub for controlled incremental changes
```
