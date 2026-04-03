# Story S7: Semantic Context Resolution

## Goal
Add a governed semantic context layer that maps user questions to likely metrics, dimensions, domains, and engine targets.

## Scope
- local semantic catalog
- semantic context matcher
- prompt builder integration
- semantic context display in UI

## Files likely impacted
- apps/api/app/semantic/catalog.py
- apps/api/app/services/semantic_service.py
- apps/api/app/prompts/prompt_builder.py
- apps/api/app/services/chat_service.py
- apps/web/src/types/chat.ts
- apps/web/src/components/ui-shell/app-shell.tsx
- apps/web/src/components/analysis/analysis-tabs.tsx

## Out of scope
- real dbt integration
- real SQL generation
- query engine execution
- vector retrieval

## Acceptance Criteria
- user prompt maps to a metric
- dimensions change based on prompt keywords
- semantic context appears in the UI
- engine target can vary by metric
