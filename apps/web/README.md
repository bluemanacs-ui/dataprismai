# DataPrismAI — Next.js Frontend

The web application shell: iMessage-style chat interface, ECharts
visualisations, native-SVG data-model ERD, PDF export, and a three-theme CSS
system (dark, dawn, theme-dark).

---

## Contents

- [Running locally](#running-locally)
- [Environment variables](#environment-variables)
- [Project layout](#project-layout)
- [Theme system](#theme-system)
- [Adding a new chat card type](#adding-a-new-chat-card-type)
- [PDF export](#pdf-export)

---

## Running locally

```bash
cp apps/web/.env.example apps/web/.env.local
cd apps/web
npm install
npm run dev          # Turbopack dev server → http://localhost:3000
```

The API is proxied through Next.js rewrites (`/api` → `http://localhost:8010`),
so browser requests never hit the API port directly.

---

## Environment variables

| Variable                   | Default       | Description                                 |
| -------------------------- | ------------- | ------------------------------------------- |
| `NEXT_PUBLIC_API_BASE_URL` | `/api`        | Base path for all API calls in `lib/api.ts` |
| `NEXT_PUBLIC_APP_NAME`     | `DataPrismAI` | App title in the browser tab                |

Set them in `.env.local` (development) or as build-time env vars in production.

---

## Project layout

```
apps/web/src/
├── app/
│   ├── layout.tsx           # Root layout — theme wrapper, fonts
│   ├── page.tsx             # Home → renders AppShell
│   └── globals.css          # ★ ALL CSS custom properties and theme blocks
├── components/
│   ├── app-shell.tsx        # Top-level layout: sidebar + chat + explorer
│   ├── chat/
│   │   ├── chat-workspace.tsx   # Message list + thinking indicator
│   │   ├── message-card.tsx     # User bubble (blue) / AI bubble (green) + PDF
│   │   └── prompt-input.tsx     # Expanding textarea + send / voice buttons
│   ├── charts/
│   │   └── echo-chart.tsx       # Generic ECharts wrapper (canvas renderer)
│   ├── explorer/
│   │   └── explorer-panel.tsx   # 5-tab data explorer + native SVG ERD
│   ├── sql/
│   │   └── sql-viewer.tsx       # Syntax-highlighted SQL panel
│   └── ui/                      # Shared primitives (buttons, badges, cards)
├── lib/
│   ├── api.ts               # Typed API client for all backend calls
│   └── hooks/               # React hooks (useChat, useTheme, …)
└── types/
    └── index.ts             # Shared TypeScript interfaces
```

---

## Theme system

All colours are CSS custom properties defined in `src/app/globals.css`. There
are three theme blocks:

| Selector      | When applied            | Description         |
| ------------- | ----------------------- | ------------------- |
| `:root`       | Default (no class)      | Dark theme          |
| `.theme-dawn` | Added to `<html>` by UI | Light / dawn theme  |
| `.theme-dark` | Alias for dark          | Explicit dark class |

**To change AI bubble colours** (per theme):

```css
/* in globals.css */
:root {
  --ai-bubble-bg: linear-gradient(160deg, #0a2e1a 0%, #071c10 100%);
  --ai-bubble-border: rgba(0, 165, 81, 0.25);
  --ai-bubble-border-left: #00a551;
  --ai-label-color: #4ade80;
}
.theme-dawn {
  --ai-bubble-bg: linear-gradient(160deg, #e6f5ee 0%, #d4ede0 100%);
  /* … */
}
```

**To add a new theme:**

1. Add a new CSS block `.theme-<name> { --var: value; … }` to `globals.css`.
2. Add a button in `app-shell.tsx` that sets `document.documentElement.className = "theme-<name>"`.

---

## Adding a new chat card type

`message-card.tsx` renders content from `ChatQueryResponse`. To add a new
card type (e.g. a map card):

1. Add the field to `ChatQueryResponse` in `types/index.ts`.
2. Add the field to the Pydantic model in `apps/api/app/schemas/chat.py`.
3. Add a new rendering block inside the AI bubble section of `message-card.tsx`.

---

## PDF export

`downloadPDF()` in `message-card.tsx`:

1. Queries the DOM for a `<canvas>` element (ECharts canvas renderer).
2. Calls `.toDataURL("image/png")` to get a base-64 PNG.
3. Uses `jspdf` to create a portrait A4 document with the chart image.

> **Note:** The chart must use the ECharts **canvas** renderer (set via
> `echarts-for-react`'s `opts={{ renderer: "canvas" }}`). The SVG renderer
> produces an `<svg>` element which cannot be captured this way.
