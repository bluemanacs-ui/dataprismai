# Story S9: Query Execution Abstraction

## Goal
Add a query execution abstraction layer that returns structured result previews based on engine target.

## Scope
- execution result schema
- engine-based executor selection
- mock StarRocks executor
- mock Trino executor
- chat service integration
- frontend result preview panel

## Files likely impacted
- apps/api/app/schemas/execution.py
- apps/api/app/schemas/chat.py
- apps/api/app/services/query_executor_service.py
- apps/api/app/services/chat_service.py
- apps/web/src/types/chat.ts
- apps/web/src/components/ui-shell/app-shell.tsx
- apps/web/src/components/analysis/analysis-tabs.tsx

## Out of scope
- real database connections
- chart rendering from result data
- auth and RBAC
- dbt runtime integration

## Acceptance Criteria
- engine-based execution path exists
- mock rows are returned
- result preview appears in UI
- row count and execution time are visible