# Story S6: Structured GenBI Response

## Goal
Move DataPrismAI from freeform LLM output to structured GenBI response fields.

## Scope
- JSON-based model prompt contract
- backend JSON parsing
- fallback handling
- frontend rendering of assumptions and structured fields

## Files likely impacted
- apps/api/app/prompts/prompt_builder.py
- apps/api/app/services/response_parser.py
- apps/api/app/services/chat_service.py
- apps/api/app/schemas/chat.py
- apps/api/main.py
- apps/web/src/types/chat.ts
- apps/web/src/components/ui-shell/app-shell.tsx
- apps/web/src/components/analysis/analysis-tabs.tsx

## Out of scope
- real SQL generation
- real chart rendering
- semantic retrieval
- engine routing logic

## Acceptance Criteria
- model is asked for JSON
- backend parses structured output safely
- fallback works if parsing fails
- assumptions appear in UI
- app works on configured frontend port
