# Story S15: Vanna SQL Integration

## Goal
Replace the current homegrown SQL generation path with a Vanna-backed NL-to-SQL path while preserving validator and UI behavior.

## Scope
- add Vanna service
- add semantic training context builder
- prefer Vanna for SQL generation
- keep existing fallback path

## Files likely impacted
- apps/api/app/core/config.py
- apps/api/app/services/vanna_training_context.py
- apps/api/app/services/vanna_service.py
- apps/api/app/services/sql_generation_service.py
- apps/api/.env
- apps/api/requirements.txt

## Out of scope
- real database training from live schema
- removing current fallback SQL generation
- UI redesign
- execution engine changes

## Acceptance Criteria
- Vanna can be enabled by config
- Vanna is tried first for SQL generation
- fallback path still works
- DataPrismAI UI remains unchanged