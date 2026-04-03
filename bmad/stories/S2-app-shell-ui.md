# Story S2: App Shell UI

## Goal
Create the first DataPrismAI application shell with navigation, chat workspace, analysis panel, and prompt input.

## Scope
- top bar
- sidebar
- chat panel
- right analysis panel
- prompt input

## Files likely impacted
- apps/web/src/app/page.tsx
- apps/web/src/components/layout/*
- apps/web/src/components/chat/*
- apps/web/src/components/analysis/*
- apps/web/src/components/ui-shell/*

## Out of scope
- live API chat integration
- chart rendering engine
- SQL rendering logic
- auth

## Acceptance Criteria
- app renders a three-column shell on desktop
- chat workspace is visible
- right analysis panel is visible
- prompt input is visible
- DataPrismAI branding is shown
