# Story S12: Skills Marketplace UI

## Goal
Expose BMAD-aligned skills as a visible marketplace inside DataPrismAI.

## Scope
- backend skill catalog
- skills API
- frontend skills marketplace
- sidebar navigation to skills view
- skill cards with status, version, owner, scope, and guardrails

## Files likely impacted
- apps/api/app/skills/catalog.py
- apps/api/app/schemas/skills.py
- apps/api/app/api/skills.py
- apps/api/main.py
- apps/web/src/types/chat.ts
- apps/web/src/lib/api.ts
- apps/web/src/components/skills/skills-panel.tsx
- apps/web/src/components/ui-shell/app-shell.tsx
- apps/web/src/components/layout/sidebar.tsx

## Out of scope
- editing skills
- runtime skill loading from filesystem
- BMAD doc rendering
- role-based access for skills

## Acceptance Criteria
- skills endpoint exists
- skills marketplace view loads
- skill cards display metadata
- sidebar can navigate to skills view