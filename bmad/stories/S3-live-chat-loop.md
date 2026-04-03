# Story S3: Live Chat Loop

## Goal
Connect the DataPrismAI UI shell to the backend chat API and support a real request-response flow.

## Scope
- backend chat endpoint
- frontend prompt submission
- dynamic rendering of assistant messages
- dynamic analysis panel updates

## Files likely impacted
- apps/api/app/api/chat.py
- apps/api/app/services/chat_service.py
- apps/api/app/schemas/chat.py
- apps/api/main.py
- apps/web/src/components/ui-shell/app-shell.tsx
- apps/web/src/components/chat/chat-workspace.tsx
- apps/web/src/components/chat/prompt-input.tsx
- apps/web/src/components/layout/top-bar.tsx
- apps/web/src/components/analysis/analysis-panel.tsx
- apps/web/src/components/analysis/analysis-tabs.tsx
- apps/web/src/lib/api.ts
- apps/web/src/types/chat.ts

## Out of scope
- real LLM integration
- real NL-to-SQL
- real chart rendering
- auth

## Acceptance Criteria
- user can submit a prompt
- backend responds through /chat/query
- assistant message renders in UI
- SQL, insights, and semantic context update in analysis panel
