# Story S8: NL-to-SQL Foundation

## Goal
Add a first NL-to-SQL layer that generates structured SQL from user questions using semantic context.

## Scope
- SQL prompt builder
- SQL structured generation service
- SQL validation service
- chat service integration
- frontend display of SQL explanation and validation notes

## Files likely impacted
- apps/api/app/prompts/sql_prompt_builder.py
- apps/api/app/schemas/sql.py
- apps/api/app/schemas/chat.py
- apps/api/app/services/sql_generation_service.py
- apps/api/app/services/sql_validator_service.py
- apps/api/app/services/chat_service.py
- apps/web/src/types/chat.ts
- apps/web/src/components/ui-shell/app-shell.tsx
- apps/web/src/components/analysis/analysis-tabs.tsx

## Out of scope
- real database execution
- query routing execution
- chart rendering from results
- dbt semantic integration

## Acceptance Criteria
- model generates structured SQL
- SQL is validated
- SQL is shown in the UI
- SQL explanation is shown
- validation notes are shown
