# Project K Panel — Claude Code Configuration

## Overview

Multi-client admin console for the Tally Sync platform. Internal tool for the startup's admin team to manage MSME clients, view their synced Tally accounting data, and trigger sync operations.

## Architecture

- **Framework**: Next.js 16 with App Router
- **Auth**: JWT Bearer tokens via `/v1/auth/login` endpoint
- **Multi-tenancy**: Admin authenticates once, then views per-client data by fetching client-specific API keys and scoping all dashboard API calls through them
- **State**: Zustand for UI state (dark mode, sidebar), React Context for per-client scoping, TanStack Query for server state

### Route Structure

```
src/app/
  login/page.tsx           — Login form
  (admin)/                 — Route group with auth guard
    layout.tsx             — Auth check + sidebar
    clients/page.tsx       — Client list (data table)
    clients/[clientId]/
      layout.tsx           — ClientContextProvider (fetches client API key)
      page.tsx             — Client dashboard (KPIs, cash flow chart)
      vouchers/page.tsx    — Voucher table + CSV export
      ledgers/page.tsx     — Ledger table + search/filter + CSV export
      devices/page.tsx     — Device cards
      sync-history/page.tsx — Sync command history + trigger panel
    settings/page.tsx      — Settings stub
```

### Key Patterns

- `scopedApi(apiKey)` in `src/lib/api.ts` — factory that creates a per-client API instance
- `ClientContextProvider` in `src/lib/client-context.tsx` — fetches client detail + API key, provides scoped API to child routes
- `useClientApi()` hook — convenience accessor for the scoped API from context
- `adminApi` namespace in `src/lib/api.ts` — admin-level endpoints (login, list clients, get client detail/API key)

## API Contract

Backend is a separate repo (cloud platform). This frontend connects via `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).

**Auth endpoints** (JWT Bearer):
- `POST /v1/auth/login` — returns access_token
- `GET /v1/auth/me` — current user info

**Admin endpoints** (JWT Bearer):
- `GET /v1/admin/clients` — list all clients
- `GET /v1/admin/clients/{id}` — client detail with devices/companies
- `GET /v1/admin/clients/{id}/api-key` — get client's device API key

**Dashboard endpoints** (x-api-key header, scoped per client):
- `GET /api/dashboard/kpis`
- `GET /api/dashboard/cash-flow`
- `GET /api/dashboard/ledgers`
- `GET /api/dashboard/vouchers`
- `GET /api/dashboard/sync-history`
- `POST /api/dashboard/sync-command`

## Working Preferences

- **Code Style**: Follow existing inline style patterns (no CSS modules yet)
- **Testing**: Vitest + React Testing Library
- **Fonts**: Outfit (headings), Inter (body), JetBrains Mono (data/monospace)
- **Color scheme**: Dark theme — slate-900 backgrounds, teal-500 accents
- **Components**: Inline in route files for now; extract when reuse emerges

## Commands

```bash
npm install          # install dependencies
npm run dev          # dev server (default port 3000)
npm run build        # production build
npm run lint         # ESLint
```
