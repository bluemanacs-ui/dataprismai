# Story S14: Inline Rich Chat Cards

## Goal
Refactor the main DataPrismAI experience so charts, insights, and details appear inline inside assistant messages.

## Scope
- embedded charts inside assistant cards
- inline insight blocks
- collapsible SQL, assumptions, semantic context, and result preview
- richer assistant message payloads
- preserve existing right-side analysis panel for now

## Files likely impacted
- apps/web/src/types/chat.ts
- apps/web/src/components/chat/message-card.tsx
- apps/web/src/components/chat/chat-workspace.tsx
- apps/web/src/components/chat/inline-chart-card.tsx
- apps/web/src/components/chat/message-details.tsx
- apps/web/src/components/ui-shell/app-shell.tsx

## Out of scope
- Vanna integration
- right panel removal
- saved report persistence
- auth

## Acceptance Criteria
- assistant messages can show embedded charts
- insights appear inline
- SQL and assumptions can be expanded inline
- result preview appears inline
- conversation feels chat-first rather than side-panel-first
