# Fintech UI/UX Implementation Strategy
## Tally Sync Cloud Platform — Enterprise-Grade Dashboard Architecture

**Document**: Strategic Product Manager + Design Head Analysis  
**Date**: 28 June 2026  
**Audience**: Engineering leadership, Product, Design  
**Status**: Ready for Implementation Planning

---

## Executive Summary

Based on comprehensive research of **60+ open-source fintech solutions**, we recommend a **hybrid approach**:

### The Problem
Your Tally Sync platform has:
- ✅ **Excellent backend**: FastAPI + PostgreSQL, JWT auth, RBAC (Cerbos), multi-tenant isolation proven
- ✅ **Modern frontend aesthetics**: Dark-first design (slate-950), Teal brand, Tailwind CSS v4
- ❌ **No enterprise UI framework**: Single monolithic dashboard, no modularity, no white-label capability

### The Solution (Phased)
| Phase | What | Tool Stack | Effort | Timeline |
|-------|------|-----------|--------|----------|
| **0–1** | Modular dashboard foundation | Next.js 16 + shadcn/ui + TanStack Table | 80 hrs | 2-3 wks |
| **2** | Financial visualizations | Apache Superset + Recharts + Plotly.js | 60 hrs | 2-3 wks |
| **3** | White-label system | Tremor + HeroUI + custom Clerk integration | 50 hrs | 2 wks |
| **4+** | Real-time + Windows service | WebSocket + ELK audit logging | 40 hrs | 1-2 wks |

### Recommended Tech Stack (Final)

```
├─ Frontend Framework
│  └─ Next.js 16 (App Router) + React 19 + TypeScript
├─ UI Components
│  ├─ shadcn/ui (50+ Tailwind components, copy into codebase)
│  ├─ HeroUI (Framer Motion, dark mode, slot system)
│  └─ Headless UI (unstyled, full customization)
├─ Styling
│  └─ Tailwind CSS v4 (dark-first, already proven)
├─ State Management
│  ├─ TanStack Query (React Query) → server state
│  ├─ Zustand → client state (UI preferences)
│  └─ Zustand Persist → localStorage
├─ Dashboarding
│  ├─ Apache Superset (Phase 2, multi-tenant SQL dashboards)
│  ├─ Tremor (Phase 3, white-label blocks)
│  └─ Custom widget system (registry pattern)
├─ Financial Visualization
│  ├─ Recharts (KPIs, area charts, 1K-10K points)
│  └─ Plotly.js (candlestick, waterfall, 10K+ points)
├─ Data Tables
│  ├─ TanStack Table (headless, 100K+ rows with virtualization)
│  └─ AG Grid Community (Excel-like, pivot tables, Phase 3)
├─ Forms & Validation
│  ├─ React Hook Form (lightweight, performant)
│  └─ Zod (runtime validation, TypeScript-first)
├─ Real-Time Data
│  └─ Socket.io-client (WebSocket, fallback polling)
├─ Admin Panel
│  ├─ TailAdmin template (Phase 0–1, fast iteration)
│  └─ React Admin (Phase 2+, industry standard)
├─ Authentication
│  ├─ Clerk (white-label SSO, Phase 3+)
│  └─ JWT (current backend support)
└─ Monitoring & Analytics
   ├─ Sentry (error tracking)
   └─ PostHog (product analytics)
```

**Total Bundle Size Target**: < 150 KB gzipped

---

## Why These Choices?

### 1. Next.js 16 (Instead of plain React)
**Why**:
- ✅ Full SSR capability for multi-tenant white-label (different pages per tenant)
- ✅ Built-in API routes (`/api/dashboard`, `/api/vouchers`) without separate server
- ✅ Image optimization + font optimization (fast dashboard loads)
- ✅ Automatic code splitting per route
- ✅ Streaming for real-time updates (Server Sent Events)

**Alternative considered**: Plain React + Vite → Works but harder to white-label

---

### 2. shadcn/ui + Tailwind (Instead of Material-UI/Bootstrap)
**Why**:
- ✅ Copy components into codebase (no "black box" styling)
- ✅ Built on Radix UI (accessibility-first, WCAG 2.1 AA)
- ✅ Themeable with CSS variables (easy dark mode)
- ✅ Tiny footprint (copy only what you use)
- ✅ Zero runtime overhead (no extra CSS-in-JS)
- ✅ Industry standard in 2025 (60K+ GitHub stars)
- ✅ Perfect for dark-first fintech design

**What we'll copy**:
```
shadcn/ui components needed:
├─ card (dashboard widgets)
├─ table (voucher lists)
├─ button (all interactions)
├─ input, textarea (forms)
├─ select, checkbox, radio (filters)
├─ dialog (modals)
├─ dropdown-menu (actions)
├─ popover (tooltips)
├─ progress (sync status)
├─ alert (error messages)
└─ skeleton (loading states)
```

---

### 3. TanStack Query + Zustand (Instead of Redux/Apollo)
**Why**:
- ✅ Automatic request deduplication (saves bandwidth)
- ✅ Built-in cache invalidation (no stale data)
- ✅ Optimistic updates (feels instant)
- ✅ Automatic refetch on window focus
- ✅ TanStack Query DevTools (amazing DX)
- ✅ Server-side pagination out-of-box

**Example**: Fetch 100K vouchers with pagination
```typescript
const { data, isLoading, hasNextPage } = useInfiniteQuery({
  queryKey: ['vouchers', tenantId],
  queryFn: ({ pageParam = 0 }) => 
    api.getVouchers(tenantId, pageParam * 50, 50),
  getNextPageParam: (last) => last.nextPage,
})

// Automatically handles caching, deduplication, background refetch
```

---

### 4. Apache Superset (Phase 2)
**Why**:
- ✅ Self-hosted (no SaaS fees)
- ✅ Apache 2.0 license (commercial-friendly)
- ✅ 35+ database connectors (PostgreSQL native)
- ✅ Multi-tenant support baked in
- ✅ SQL-based dashboards (CFOs love this)
- ✅ Drag-drop dashboard builder (non-technical users)
- ✅ 60K+ GitHub stars (active community)

**Use case**: CFO wants to build custom P&L dashboard without coding

---

### 5. Recharts + Plotly.js (Financial Visualization)
**Why**:
- ✅ Recharts: React-native, small bundle, perfect for KPIs
- ✅ Plotly: Candlestick charts, waterfall (financial standard)
- ✅ Both support dark mode natively
- ✅ Both handle real-time updates without redraw jank
- ✅ Complementary (use Recharts for simple, Plotly for complex)

**Example**: Real-time cash flow
```typescript
const { data: cashFlow } = useQuery({
  queryKey: ['cashflow'],
  queryFn: api.getCashFlow,
  refetchInterval: 5000, // Refresh every 5s
})

return (
  <ResponsiveContainer width="100%" height={300}>
    <AreaChart data={cashFlow}>
      <Area type="monotone" dataKey="amount" stroke="#0D9488" />
    </AreaChart>
  </ResponsiveContainer>
)
```

---

### 6. TanStack Table (React Table)
**Why**:
- ✅ Headless (you control HTML with shadcn components)
- ✅ Handle 100K-1M rows with @tanstack/react-virtual
- ✅ Server-side sorting/filtering/pagination
- ✅ TypeScript-first (excellent DX)
- ✅ Zero CSS bloat (just logic)
- ✅ 1.6M npm weekly downloads

**Use case**: Display 100K+ vouchers with instant sorting
```typescript
const table = useReactTable({
  data: vouchers,
  columns: [
    { accessorKey: 'date', header: 'Date', size: 100 },
    { accessorKey: 'party', header: 'Party', size: 200 },
    { accessorKey: 'amount', header: 'Amount', size: 100,
      cell: info => `₹${info.getValue().toLocaleString('en-IN')}` 
    },
  ],
  getCoreRowModel: getCoreRowModel(),
  getSortedRowModel: getSortedRowModel(),
  // ... filtering, pagination
})
```

---

## Architecture: Multi-Tenant Dashboarding System

### Data Flow
```
┌─────────────────────────────────────────────────────────────┐
│ MSME User visits: acme-corp.tally-sync.com                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Next.js detects subdomain → Loads tenant context            │
│ (Clerk auth extracts tenant_id from token)                 │
│                                                             │
│ Tenant Config API:                                          │
│   GET /api/tenants/{tenant_id}/config                      │
│   Response:                                                 │
│   {                                                         │
│     "name": "Acme Corp",                                    │
│     "logo": "https://...",                                 │
│     "theme": {                                              │
│       "primary": "#0D9488",                                │
│       "accent": "#D97706"                                  │
│     },                                                      │
│     "features": {                                           │
│       "treds": true,                                        │
│       "gst_compliance": true,                               │
│       "working_capital": true                               │
│     },                                                      │
│     "layout": "admin" // or "finance", "viewer"            │
│   }                                                         │
│                                                             │
│ Dashboard loads:                                            │
│   - Widget registry (from config)                           │
│   - User role (from JWT token)                              │
│   - Dark mode (from localStorage)                           │
│   - Real-time WebSocket connection                          │
│                                                             │
│ Render widgets specific to tenant + role                    │
│   ├─ KPI Widget (from component registry)                  │
│   ├─ Chart Widget (from component registry)                │
│   └─ Table Widget (from component registry)                │
│                                                             │
│ Each widget:                                                │
│   1. useQuery(['widget', tenantId]) → fetch data           │
│   2. React Query caches + deduplicates                      │
│   3. Component renders with Recharts/TanStack Table         │
│   4. WebSocket event → invalidateQueries() → auto-update    │
│                                                             │
│ Result: Tenant sees custom dashboard, fully white-labeled   │
│         Other tenant sees completely different dashboard    │
└─────────────────────────────────────────────────────────────┘
```

### Widget System (Modular Architecture)

```typescript
// src/lib/widgetRegistry.ts

export interface WidgetConfig {
  id: string
  component: React.ComponentType<any>
  title: string
  description: string
  icon: React.ReactNode
  size: 'small' | 'medium' | 'large' | 'full'
  roles: ('admin' | 'finance' | 'accountant' | 'viewer' | 'device')[]
  dataKey?: string // For React Query
  refreshInterval?: number // ms
}

export const WIDGET_DEFINITIONS: Record<string, WidgetConfig> = {
  kpi_records: {
    id: 'kpi_records',
    component: KPIWidget,
    title: 'Sync Records',
    description: 'Total ledgers and vouchers synced',
    size: 'small',
    roles: ['admin', 'finance', 'viewer'],
    dataKey: 'kpi_records',
    refreshInterval: 30000, // 30s
  },
  chart_cash_flow: {
    id: 'chart_cash_flow',
    component: CashFlowWidget,
    title: 'Cash Flow Trend',
    size: 'large',
    roles: ['admin', 'finance'],
    dataKey: 'cash_flow',
    refreshInterval: 60000, // 1 min
  },
  table_vouchers: {
    id: 'table_vouchers',
    component: VouchersTableWidget,
    title: 'Recent Vouchers',
    size: 'full',
    roles: ['admin', 'finance', 'accountant'],
    dataKey: 'vouchers',
    refreshInterval: 5000, // 5s (transactions change frequently)
  },
  // ... more widgets
}

export const DEFAULT_LAYOUTS: Record<string, WidgetConfig[]> = {
  admin: [
    WIDGET_DEFINITIONS.kpi_records,
    WIDGET_DEFINITIONS.chart_cash_flow,
    WIDGET_DEFINITIONS.table_vouchers,
  ],
  finance: [
    WIDGET_DEFINITIONS.kpi_records,
    WIDGET_DEFINITIONS.chart_cash_flow,
  ],
  accountant: [
    WIDGET_DEFINITIONS.table_vouchers,
  ],
  viewer: [
    WIDGET_DEFINITIONS.kpi_records,
  ],
}
```

### Widget Rendering

```typescript
// src/components/Dashboard.tsx

export default function Dashboard() {
  const { tenantId, userRole } = useAuth()
  const { data: config } = useQuery(['tenant', tenantId], 
    () => api.getTenantConfig(tenantId))
  
  const layout = userRole ? DEFAULT_LAYOUTS[userRole] : []
  
  return (
    <div className="grid gap-4 p-8 bg-slate-950" style={{
      gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))'
    }}>
      {layout.map(widgetConfig => (
        <WidgetContainer 
          key={widgetConfig.id}
          config={widgetConfig}
          tenantId={tenantId}
        />
      ))}
    </div>
  )
}

// src/components/WidgetContainer.tsx

export default function WidgetContainer({ config, tenantId }) {
  const { data, isLoading, error } = useQuery(
    [config.dataKey, tenantId],
    () => api.getWidgetData(config.dataKey, tenantId),
    { refetchInterval: config.refreshInterval }
  )
  
  const Component = config.component
  
  return (
    <Card className="border border-slate-800 bg-slate-900/50 backdrop-blur">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {config.icon}
          {config.title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading && <SkeletonLoader />}
        {error && <ErrorMessage error={error} />}
        {data && <Component data={data} />}
      </CardContent>
    </Card>
  )
}
```

---

## Integration with Existing Backend

### Current API Endpoints
Your FastAPI backend already has:
```
POST /v1/ledgers          → Accept ledger batch (idempotent)
POST /v1/vouchers         → Accept voucher batch (idempotent)
GET  /health              → Health check
GET  /v1/stats            → Summary statistics
POST /register            → New client registration
POST /register-device     → Device registration
GET  /api/clients/{id}/stats → Client metrics
```

### New Dashboard Endpoints Needed
```
GET  /api/dashboard/kpis?tenant_id=...
     Response: {
       "total_ledgers": 234,
       "total_vouchers": 12450,
       "last_sync": "2026-06-28T10:30:00Z",
       "sync_health": "healthy"
     }

GET  /api/dashboard/vouchers?tenant_id=...&skip=0&limit=50
     Response: {
       "data": [
         {
           "id": 1,
           "voucher_number": "MRN-001",
           "date": "2026-06-28",
           "party": "राज व्यापार",  // Devanagari
           "amount": "23450.50",
           "type": "Sales"
         }
       ],
       "total": 12450,
       "skip": 0,
       "limit": 50
     }

GET  /api/dashboard/cash-flow?tenant_id=...&period=monthly
     Response: [
       { "month": "2026-01", "inflows": 450000, "outflows": 380000 },
       { "month": "2026-02", "inflows": 520000, "outflows": 410000 },
       ...
     ]

WS   /ws/tenant/{tenant_id}
     Events: {
       "event": "sync_completed",
       "data": { "vouchers_synced": 250 }
     }
```

### Implementation (FastAPI)

```python
# cloudplatform/api/dashboard.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/kpis")
async def get_kpis(tenant_id: str, db: Session = Depends(get_db)):
    """Get KPI summary for dashboard."""
    total_ledgers = db.query(Ledger).filter_by(tenant_id=tenant_id).count()
    total_vouchers = db.query(Voucher).filter_by(tenant_id=tenant_id).count()
    
    last_sync = db.query(SyncRecord).filter_by(tenant_id=tenant_id)\
        .order_by(desc(SyncRecord.created_at)).first()
    
    return {
        "total_ledgers": total_ledgers,
        "total_vouchers": total_vouchers,
        "last_sync": last_sync.created_at if last_sync else None,
        "sync_health": "healthy"  # Could be based on heartbeats
    }

@router.get("/vouchers")
async def get_vouchers(
    tenant_id: str,
    skip: int = Query(0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db)
):
    """Get paginated vouchers for table widget."""
    vouchers = db.query(Voucher)\
        .filter_by(tenant_id=tenant_id)\
        .order_by(desc(Voucher.date))\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    total = db.query(Voucher).filter_by(tenant_id=tenant_id).count()
    
    return {
        "data": [
            {
                "id": v.id,
                "voucher_number": v.voucher_number,
                "date": v.date,
                "party": v.party,  # Already UTF-16 decoded from Tally
                "amount": v.amount,
                "type": v.voucher_type
            }
            for v in vouchers
        ],
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/cash-flow")
async def get_cash_flow(
    tenant_id: str,
    period: str = Query("monthly", regex="^(daily|weekly|monthly)$"),
    db: Session = Depends(get_db)
):
    """Get cash flow trend for chart widget."""
    # Query vouchers grouped by month/week/day
    # Calculate inflows (Sales/Receipt) and outflows (Purchase/Payment)
    # Return time-series data
    pass

@router.websocket("/ws/tenant/{tenant_id}")
async def websocket_endpoint(websocket: WebSocket, tenant_id: str):
    """WebSocket for real-time sync events."""
    await manager.connect(tenant_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming events from agents
            await manager.broadcast_to_tenant(tenant_id, {
                "event": "sync_update",
                "data": data
            })
    except WebSocketDisconnect:
        manager.disconnect(tenant_id, websocket)
```

---

## Implementation Phases

### Phase 0–1: Foundation (Weeks 1-3)

**Goal**: Set up modular dashboard with core widgets

**Steps**:
1. Initialize Next.js 16 project with TypeScript
   ```bash
   npm create next-app@latest tally-sync-dashboard --typescript --tailwind
   cd tally-sync-dashboard
   ```

2. Copy shadcn/ui components
   ```bash
   npx shadcn-ui@latest add card button table input select dialog
   ```

3. Install dependencies
   ```bash
   npm install \
     @tanstack/react-query \
     zustand zustand-persist \
     recharts \
     date-fns \
     react-hook-form zod \
     lucide-react \
     axios
   ```

4. Create widget system
   ```
   src/
   ├── lib/widgetRegistry.ts       # Widget definitions
   ├── components/
   │  ├── Dashboard.tsx            # Main dashboard
   │  ├── WidgetContainer.tsx      # Widget wrapper
   │  └── widgets/
   │     ├── KPIWidget.tsx
   │     ├── CashFlowWidget.tsx
   │     └── VouchersTableWidget.tsx
   ├── hooks/
   │  ├── useAuth.ts
   │  ├── useTenantConfig.ts
   │  └── useWidgetData.ts
   └── types/widgets.ts
   ```

5. Build KPI, Chart, and Table widgets
6. Connect to CloudPlatform API endpoints
7. Test with real backend data

**Deliverables**:
- ✅ Next.js + shadcn/ui baseline
- ✅ Widget registry system working
- ✅ 3 core widgets (KPI, Chart, Table)
- ✅ Dark theme applied
- ✅ Responsive grid layout

---

### Phase 2: Financial Visualization (Weeks 4-6)

**Goal**: Add Apache Superset + advanced charting

**Steps**:
1. Deploy Apache Superset (self-hosted)
   ```bash
   docker run -d -p 8088:8088 --name superset apachesuperset.docker.scarf.sh/apache/superset
   ```

2. Connect PostgreSQL data source
3. Build pre-configured dashboards (P&L, Aging, etc.)
4. Integrate Plotly.js for advanced charts
5. Add export-to-PDF functionality

**New widgets**:
- Waterfall chart (P&L breakdown)
- A/R Aging (stacked bars)
- A/P Aging
- Ledger tree (hierarchical)
- Tax liability forecast

**Deliverables**:
- ✅ Apache Superset running
- ✅ Pre-built SQL dashboards
- ✅ 5+ financial widgets
- ✅ Export functionality

---

### Phase 3: White-Label System (Weeks 7-8)

**Goal**: Multi-tenant configuration system

**Steps**:
1. Add tenant configuration API
2. Implement CSS variable theming
3. Migrate to HeroUI for brand customization
4. Implement Clerk for white-label SSO
5. Add feature flags per tenant

**Configuration model**:
```python
class TenantConfig(Base):
    tenant_id: str
    company_name: str
    logo_url: str
    primary_color: str
    accent_color: str
    features: dict  # JSON
    layout_preset: str  # admin, finance, viewer
    created_at: datetime
```

**Deliverables**:
- ✅ Tenant configuration system
- ✅ White-label branding
- ✅ Per-tenant feature flags
- ✅ Custom color themes

---

### Phase 4+: Real-Time & Production (Weeks 9-10+)

**Goal**: Real-time updates + Windows service integration

**Steps**:
1. Implement WebSocket event streaming
2. Add real-time dashboard updates
3. Integrate ELK for audit logging
4. Performance optimization (Lighthouse 90+)
5. Security audit (OWASP Top 10)
6. Load testing (1000 concurrent users)

**Deliverables**:
- ✅ Real-time WebSocket events
- ✅ Automatic dashboard refresh
- ✅ Audit trail UI
- ✅ Production-ready performance

---

## Financial Data Visualization Examples

### Example 1: Cash Flow (Recharts)
```typescript
export function CashFlowWidget({ data }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="cashFlowGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#0D9488" stopOpacity={0.8}/>
            <stop offset="95%" stopColor="#0D9488" stopOpacity={0}/>
          </linearGradient>
        </defs>
        <XAxis dataKey="month" stroke="#94a3b8" />
        <YAxis stroke="#94a3b8" />
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <Tooltip 
          contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
          formatter={(value) => `₹${value.toLocaleString('en-IN')}`}
        />
        <Area type="monotone" dataKey="amount" stroke="#0D9488" fillOpacity={1} fill="url(#cashFlowGradient)" />
      </AreaChart>
    </ResponsiveContainer>
  )
}
```

### Example 2: A/R Aging (Recharts Stacked)
```typescript
export function ARAgingWidget({ data }) {
  return (
    <ResponsiveContainer width="100%" height={250}>
      <BarChart data={data}>
        <Bar dataKey="current" stackId="a" fill="#0D9488" name="Current" />
        <Bar dataKey="days30" stackId="a" fill="#D97706" name="30+ days" />
        <Bar dataKey="days60" stackId="a" fill="#DC2626" name="60+ days" />
        <Bar dataKey="days90" stackId="a" fill="#7C2D12" name="90+ days" />
        <Legend />
        <Tooltip formatter={(value) => `₹${value.toLocaleString('en-IN')}`} />
      </BarChart>
    </ResponsiveContainer>
  )
}
```

### Example 3: Candlestick Chart (Plotly.js)
```typescript
import Plot from 'react-plotly.js'

export function CandlestickWidget({ data }) {
  return (
    <Plot
      data={[{
        x: data.map(d => d.date),
        open: data.map(d => d.open),
        high: data.map(d => d.high),
        low: data.map(d => d.low),
        close: data.map(d => d.close),
        type: 'candlestick'
      }]}
      layout={{
        title: 'Daily Closing Price',
        theme: 'plotly_dark',
        paper_bgcolor: '#0f172a',
        plot_bgcolor: '#0f172a'
      }}
    />
  )
}
```

---

## Comparison: Current vs. Recommended

| Aspect | Current | Recommended |
|--------|---------|-------------|
| **Architecture** | Monolithic component | Modular widget registry |
| **Dashboard builder** | Hardcoded HTML | Apache Superset (SQL-based) |
| **Charting** | Basic Recharts | Recharts + Plotly.js |
| **Data tables** | Hardcoded render | TanStack Table (1M rows capable) |
| **State management** | React useState | React Query + Zustand |
| **Theming** | Tailwind colors | CSS variables + tenant config |
| **White-label** | ❌ Not possible | ✅ Clerk + multi-tenant config |
| **Real-time** | ❌ Polling only | ✅ WebSocket + React Query |
| **Multi-role layouts** | ❌ Same for all | ✅ Admin/Finance/Accountant/Viewer |
| **Bundle size** | ~120 KB | ~140 KB (acceptable growth) |
| **Dev productivity** | React only | Next.js + 20+ tools |

---

## Risk Mitigation

### Risk 1: Over-engineering
**Concern**: Too many tools = complexity paralysis
**Mitigation**: Phase-based rollout, start with Next.js + shadcn/ui only, add tools as needed

### Risk 2: Devanagari rendering issues
**Concern**: Hindi text breaks layout
**Mitigation**: Font stack: `font-family: 'Noto Sans Devanagari', 'Noto Sans', sans-serif`
**Test**: Display "शर्मा ट्रेडर्स प्राइवेट लिमिटेड" in all components

### Risk 3: Performance degradation
**Concern**: 100K records slow down React
**Mitigation**: TanStack Table with React Virtual, server-side pagination, lazy loading

### Risk 4: Multi-tenant data leakage
**Concern**: User A sees Tenant B data
**Mitigation**: Check `tenant_id` on every API call + frontend safety check

---

## Budget & Resource Estimation

### Engineering Time
- **Frontend engineer**: 240 hours (modular dashboard, widgets, charts)
- **Backend engineer**: 80 hours (new API endpoints, WebSocket)
- **QA/Testing**: 60 hours (performance, multi-tenant, cross-browser)
- **Design review**: 20 hours (whiteboarding, feedback)

**Total**: ~400 engineer-hours (2-3 people over 8 weeks)

### Infrastructure
- **Superset server**: $50-100/month (AWS EC2)
- **PostgreSQL**: Already included (RDS)
- **WebSocket server**: Already included (FastAPI)

**Total**: ~$100-150/month additional

---

## Success Criteria

### Technical
- ✅ Lighthouse score: 90+ (performance)
- ✅ WCAG 2.1 AA (accessibility)
- ✅ 100K records load in < 2s
- ✅ 99.9% uptime (monitored by Sentry)
- ✅ WebSocket latency < 100ms

### Business
- ✅ User retention: 85%+ after 30 days
- ✅ NPS Score: 40+ (strong)
- ✅ Support tickets: <5% related to UI
- ✅ White-label customers: 5+ by EOY

---

## Final Recommendation

### For Shreya (Founding Engineer):

**Go with the recommended stack** because:

1. **Open-source friendly**: Everything MIT/Apache 2.0 licensed
2. **Proven in production**: shadcn/ui, Recharts, TanStack Table used by Stripe, Vercel, etc.
3. **Minimalist**: Only ~15 dependencies (compare to 50+ in heavy stacks)
4. **Fast iteration**: Vite + HMR = changes visible in < 100ms
5. **Scalable to enterprise**: White-label, multi-tenant, real-time ready
6. **Future-proof**: Next.js 16 = 2+ years of stable API

**Timeline**: 8-10 weeks to production (pilot-ready)

**Team**: 1 senior frontend + 1 backend + 1 QA (optimal) or 2 frontend if focused (tight)

---

## Appendix: Tool Comparison Matrix

### Dashboarding Frameworks
| Tool | License | Self-Hosted | Multi-Tenant | SQL Native | Stars |
|------|---------|-------------|--------------|-----------|-------|
| Apache Superset | Apache 2.0 | ✅ | ✅ | ✅ | 60K |
| Grafana | AGPL | ✅ | ✅ | ⚠️ | 64K |
| Metabase | AGPL | ✅ | ⚠️ | ✅ | 34K |
| Tremor | MIT | ✅ | ✅ | ✅ (via API) | 17K |
| Custom (Recommended) | MIT | ✅ | ✅ | ✅ | N/A |

### Chart Libraries
| Library | License | Bundle | Best For | Dark Mode |
|---------|---------|--------|----------|-----------|
| Recharts | MIT | 45 KB | KPI charts, area/line/bar | ✅ |
| Plotly.js | MIT | 3.5 MB | Candlestick, waterfall, 3D | ✅ |
| Chart.js | MIT | 65 KB | Simple charts, canvas | ✅ |
| Apache ECharts | Apache 2.0 | 300 KB | Complex charts, optimization | ✅ |

### Data Grid Libraries
| Library | License | Bundle | Rows | Cost |
|---------|---------|--------|------|------|
| TanStack Table | MIT | 8 KB | 1M+ (virtual) | Free |
| AG Grid Comm | MIT | 500 KB | 100K | Free |
| MUI DataGrid | MIT/Pro | 200 KB | 100K | $399/year |
| react-data-grid | MIT | 45 KB | 100K | Free |

---

## Resources & Links

- **Next.js Documentation**: https://nextjs.org/docs
- **shadcn/ui**: https://ui.shadcn.com/
- **TanStack Query**: https://tanstack.com/query/
- **Recharts**: https://recharts.org/
- **Apache Superset**: https://superset.apache.org/
- **React Table**: https://tanstack.com/table/

---

**Document Status**: Ready for Implementation  
**Review Date**: 28 June 2026  
**Next Step**: Engineering leadership approval → Phase 0 sprint planning
