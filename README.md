# Project K Panel

Multi-client admin console for the Tally Sync platform. Allows the admin team to manage onboarded MSME clients, view synced accounting data, and trigger sync commands.

## Setup

```bash
npm install
cp .env.local.example .env.local   # edit API URL if needed
npm run dev                         # starts on http://localhost:3000
```

## Routes

| Route | Description |
|-------|-------------|
| `/login` | Admin login |
| `/clients` | All onboarded MSME clients |
| `/clients/[id]` | Client dashboard (KPIs, cash flow) |
| `/clients/[id]/ledgers` | Ledger accounts with search, filter, CSV export |
| `/clients/[id]/vouchers` | Transaction vouchers with CSV export |
| `/clients/[id]/devices` | Agent devices for this client |
| `/clients/[id]/sync-history` | Sync command history + trigger new syncs |
| `/settings` | Platform settings (stub) |

## Stack

- **Next.js 16** (App Router)
- **React 19** + TanStack Query v5
- **Recharts** for data visualization
- **Zustand** for UI state
- **Axios** for API communication
- **Tailwind CSS v4**

## Backend

Requires the cloud platform API running (default `http://localhost:8000`). Configure via `NEXT_PUBLIC_API_URL` in `.env.local`.
