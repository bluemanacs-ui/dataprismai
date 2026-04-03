# Story S10: Chart Recommendation and Rendering

## Goal
Add chart recommendation and real chart rendering based on query result shape.

## Scope
- backend chart recommendation service
- chart config in chat response
- frontend chart renderer
- live chart in analysis panel

## Files likely impacted
- apps/api/app/schemas/chart.py
- apps/api/app/schemas/chat.py
- apps/api/app/services/chart_service.py
- apps/api/app/services/chat_service.py
- apps/web/src/types/chat.ts
- apps/web/src/components/ui-shell/app-shell.tsx
- apps/web/src/components/analysis/chart-view.tsx
- apps/web/src/components/analysis/analysis-tabs.tsx

## Out of scope
- real database execution
- chart customization UI
- dashboard saving
- multi-chart layouts

## Acceptance Criteria
- chart config is generated on backend
- chart renders in frontend
- line chart works for time series
- bar chart works for grouped comparisons
- fallback is safe when no chart data exists