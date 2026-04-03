# Story S11: Metric Catalog and Data Explorer

## Goal
Add a discoverable metric catalog and explorer experience to DataPrismAI.

## Scope
- semantic catalog API
- frontend explorer panel
- metric cards with domain, engine, dimensions, and definition
- explorer search
- sidebar navigation between chat and explorer

## Files likely impacted
- apps/api/app/schemas/semantic.py
- apps/api/app/api/semantic.py
- apps/api/main.py
- apps/web/src/types/chat.ts
- apps/web/src/lib/api.ts
- apps/web/src/components/explorer/explorer-panel.tsx
- apps/web/src/components/ui-shell/app-shell.tsx
- apps/web/src/components/layout/sidebar.tsx

## Out of scope
- dbt integration
- editing semantic models
- lineage graph
- saved explorer views

## Acceptance Criteria
- semantic catalog endpoint exists
- explorer view loads metrics
- search filters metrics
- sidebar can switch between chat and explorer
