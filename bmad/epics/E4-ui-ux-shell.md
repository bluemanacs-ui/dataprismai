# Epic E4: UI / UX Shell

## Goal

Deliver an enterprise-grade, theme-aware analytics chat shell built with
Next.js 15 + Tailwind CSS that replicates a premium AI assistant experience
(iMessage-style chat bubbles, live ECharts visualisations, drill-down data
explorer, inline SQL view, and PDF export).

## Strategic Value

A polished, fast UI reduces time-to-insight for business users. All colours,
fonts, and layout elements are fully configurable through CSS custom properties
and environment variables — no recode required per deployment.

## Includes

### E4.1 App Shell

- `apps/web/src/app/layout.tsx` + `app-shell.tsx`
- Left sidebar: logo, skill launch buttons, conversation history
- Main pane: chat workspace + right explorer panel
- Top bar: theme switcher (Dark / Dawn), persona selector

### E4.2 Chat Workspace

- `components/chat/chat-workspace.tsx` — message list + prompt input
- `components/chat/message-card.tsx` — user bubble (blue pill) / AI bubble (green card)
- `components/chat/prompt-input.tsx` — expanding textarea, voice button, send button
- PDF export: captures ECharts canvas → embeds as PNG in `jspdf` document

### E4.3 ECharts Visualisation

- `components/charts/echo-chart.tsx` — generic ECharts wrapper
- Chart type recommended by the AI pipeline (`chart_config` in response)
- Canvas renderer for pixel-perfect PDF export

### E4.4 Data Explorer Panel

- `components/explorer/explorer-panel.tsx`
- 5 tabs: Datasets ▸ Profiling ▸ Data Models (ERD) ▸ Semantic Layer ▸ History
- ERD rendered as native SVG (no external graph library)
- FK lines as cubic bezier curves with arrowheads

### E4.5 Theme System

- `app/globals.css` — CSS custom property variables per theme block
- Three themes: `:root` (dark default), `.theme-dawn` (light), `.theme-dark` (alias)
- Configurable AI bubble colours so contrast is guaranteed in light mode

## Dependencies

- E1, E2

## Acceptance Criteria

- [ ] Chat sends query and receives structured response in < 6 s locally
- [ ] PDF export includes chart image (not blank canvas)
- [ ] Light mode AI bubble passes WCAG AA contrast ratio
- [ ] Removing / replacing a theme requires only CSS var changes
- [ ] TypeScript strict mode — zero `any` escapes in components

## Status

Complete — all core UI features implemented; PDF fix and theme vars applied
