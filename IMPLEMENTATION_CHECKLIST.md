# Enterprise Fintech Dashboard — Implementation Checklist

**Project**: Tally Sync Cloud Platform  
**Phase**: 0-1 (Modular Dashboard Foundation)  
**Timeline**: 2-3 weeks  
**Owner**: Frontend Team  

---

## Pre-Implementation Setup (Day 1)

### Team Alignment
- [ ] Review FINTECH_UI_IMPLEMENTATION_STRATEGY.md with engineering team
- [ ] Confirm tech stack approval (Next.js 16 + shadcn/ui + TanStack Query)
- [ ] Assign responsibilities: Frontend lead, Backend liaison, QA
- [ ] Create sprint in Jira/Linear

### Environment Setup
- [ ] Ensure Node.js 18+ installed locally
  ```bash
  node --version  # Should be >= 18.0.0
  ```
- [ ] Ensure Python 3.11+ for CloudPlatform backend
- [ ] Git clone both repos:
  - `tally-shayak` (agent + cloudplatform)
  - Create new repo: `tally-sync-dashboard` (React app)

### Knowledge Sync
- [ ] **Frontend**: Read FINTECH_UI_IMPLEMENTATION_STRATEGY.md (30 min)
- [ ] **Backend**: Read FINTECH_UI_IMPLEMENTATION_STRATEGY.md (20 min)
- [ ] **QA**: Read Phase 0-1 test plan (see Testing section below)
- [ ] **Team**: Walk through STRATEGIC_UI_UX_ANALYSIS.md highlights (60 min)

---

## Phase 0-1: Foundation Setup (Week 1)

### Day 1-2: Next.js Project Initialization

#### Step 1: Create Next.js 16 Project
```bash
# Create new Next.js app
npm create next-app@latest tally-sync-dashboard \
  --typescript \
  --tailwind \
  --eslint \
  --src-dir \
  --no-app-router  # We'll use App Router later, start with Pages for simplicity

cd tally-sync-dashboard
```

- [ ] Project created successfully
- [ ] `src/` directory structure visible
- [ ] Next.js 16.0+ confirmed in package.json
- [ ] Tailwind CSS configured

#### Step 2: Install Core Dependencies
```bash
npm install \
  @tanstack/react-query \
  zustand \
  zod \
  react-hook-form \
  axios \
  date-fns \
  lucide-react \
  clsx \
  tailwind-merge

npm install -D \
  @types/node \
  @types/react \
  tailwindcss \
  postcss \
  autoprefixer
```

- [ ] All dependencies installed
- [ ] `package-lock.json` committed
- [ ] No peer dependency warnings

#### Step 3: Setup shadcn/ui
```bash
# Initialize shadcn/ui
npx shadcn-ui@latest init

# Select defaults:
# - Style: Default
# - Base color: Slate
# - CSS variables: Yes
# - TypeScript: Yes

# Add required components
npx shadcn-ui@latest add card
npx shadcn-ui@latest add button
npx shadcn-ui@latest add table
npx shadcn-ui@latest add input
npx shadcn-ui@latest add select
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add dropdown-menu
npx shadcn-ui@latest add skeleton
npx shadcn-ui@latest add alert
```

- [ ] shadcn components installed in `src/components/ui/`
- [ ] `components.json` created
- [ ] All components render correctly
- [ ] Dark mode works by default

#### Step 4: Dark Mode Theme Setup
```typescript
// src/app.tsx or src/pages/_app.tsx
import type { AppProps } from 'next/app'

export default function App({ Component, pageProps }: AppProps) {
  return (
    <div className="dark">
      <Component {...pageProps} />
    </div>
  )
}
```

- [ ] Dark mode class applied globally
- [ ] Background is slate-950 (dark)
- [ ] Text is readable on dark background
- [ ] All components respect dark mode

#### Step 5: Configure Tailwind CSS for Fintech
```typescript
// tailwind.config.ts
import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: 'class',
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'teal': {
          '50': '#f0fdfa',
          '500': '#14b8a6',  // Primary
          '600': '#0d9488',  // Brand teal
        },
        'amber': {
          '500': '#f59e0b',
          '600': '#d97706',  // Saffron
        },
      },
    },
  },
  plugins: [],
}
export default config
```

- [ ] Tailwind configured with custom colors
- [ ] Teal and Amber colors match brand
- [ ] CSS variables for dark mode

#### Verification
```bash
npm run dev

# Check http://localhost:3000
# Should see:
# - Dark background (slate-950)
# - Welcome text readable
# - No console errors
```

- [ ] Dev server runs on http://localhost:3000
- [ ] No console errors
- [ ] Dark theme visible

---

### Day 3-5: Widget System Architecture

#### Step 6: Create Widget Type System
```typescript
// src/types/widgets.ts

export interface WidgetConfig {
  id: string
  component: React.ComponentType<any>
  title: string
  description: string
  icon?: React.ReactNode
  size: 'small' | 'medium' | 'large' | 'full'
  roles: ('admin' | 'finance' | 'accountant' | 'viewer')[]
  dataKey?: string
  refreshInterval?: number // ms
}

export interface WidgetLayoutConfig {
  [role: string]: WidgetConfig[]
}

export interface TenantConfig {
  id: string
  name: string
  logo?: string
  primaryColor?: string
  accentColor?: string
  features?: Record<string, boolean>
}

export interface AuthContext {
  userId?: string
  tenantId?: string
  role?: 'admin' | 'finance' | 'accountant' | 'viewer'
  token?: string
}
```

- [ ] Type file created
- [ ] TypeScript types compile without errors
- [ ] Types exported for component use

#### Step 7: Create Widget Registry
```typescript
// src/lib/widgetRegistry.ts

import { WidgetConfig, WidgetLayoutConfig } from '@/types/widgets'
import KPIWidget from '@/components/widgets/KPIWidget'
import CashFlowChartWidget from '@/components/widgets/CashFlowChartWidget'
import VouchersTableWidget from '@/components/widgets/VouchersTableWidget'

export const WIDGET_DEFINITIONS: Record<string, WidgetConfig> = {
  kpi_records: {
    id: 'kpi_records',
    component: KPIWidget,
    title: 'Sync Records',
    description: 'Total ledgers and vouchers synced',
    icon: null,
    size: 'small',
    roles: ['admin', 'finance', 'viewer'],
    dataKey: 'kpi_records',
    refreshInterval: 30000,
  },
  chart_cash_flow: {
    id: 'chart_cash_flow',
    component: CashFlowChartWidget,
    title: 'Cash Flow Trend',
    description: '30-day cash flow analysis',
    icon: null,
    size: 'large',
    roles: ['admin', 'finance'],
    dataKey: 'cash_flow',
    refreshInterval: 60000,
  },
  table_vouchers: {
    id: 'table_vouchers',
    component: VouchersTableWidget,
    title: 'Recent Vouchers',
    description: 'Latest transactions',
    icon: null,
    size: 'full',
    roles: ['admin', 'finance', 'accountant'],
    dataKey: 'vouchers',
    refreshInterval: 5000,
  },
}

export const DEFAULT_LAYOUTS: WidgetLayoutConfig = {
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

export class WidgetManager {
  static getLayout(role: string): WidgetConfig[] {
    return DEFAULT_LAYOUTS[role] || []
  }

  static getAllWidgets(): WidgetConfig[] {
    return Object.values(WIDGET_DEFINITIONS)
  }

  static getWidget(id: string): WidgetConfig | undefined {
    return WIDGET_DEFINITIONS[id]
  }
}
```

- [ ] Widget registry created
- [ ] All 3 widgets defined
- [ ] Default layouts per role configured
- [ ] WidgetManager class provides access methods

#### Step 8: Setup React Query (TanStack Query)
```typescript
// src/lib/queryClient.ts

import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      gcTime: 1000 * 60 * 10, // 10 minutes (formerly cacheTime)
      retry: 1,
      refetchOnWindowFocus: true,
    },
  },
})
```

```typescript
// src/pages/_app.tsx

import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from '@/lib/queryClient'

function MyApp({ Component, pageProps }) {
  return (
    <QueryClientProvider client={queryClient}>
      <Component {...pageProps} />
    </QueryClientProvider>
  )
}

export default MyApp
```

- [ ] QueryClient created
- [ ] QueryClientProvider wraps app
- [ ] React Query DevTools available (optional but helpful)

#### Step 9: Setup Zustand for Client State
```typescript
// src/lib/store.ts

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { AuthContext } from '@/types/widgets'

interface DashboardStore {
  auth: AuthContext | null
  darkMode: boolean
  setAuth: (auth: AuthContext) => void
  setDarkMode: (dark: boolean) => void
}

export const useDashboardStore = create<DashboardStore>()(
  persist(
    (set) => ({
      auth: null,
      darkMode: true,
      setAuth: (auth) => set({ auth }),
      setDarkMode: (dark) => set({ darkMode: dark }),
    }),
    {
      name: 'dashboard-store',
      partialize: (state) => ({ darkMode: state.darkMode }),
    }
  )
)
```

- [ ] Zustand store created
- [ ] Auth and dark mode state available
- [ ] localStorage persistence working

#### Step 10: Create API Layer
```typescript
// src/lib/api.ts

import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add JWT token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const api = {
  // KPI endpoints
  getKPIs: (tenantId: string) =>
    apiClient.get(`/api/dashboard/kpis?tenant_id=${tenantId}`),

  // Voucher endpoints
  getVouchers: (tenantId: string, skip = 0, limit = 50) =>
    apiClient.get(`/api/dashboard/vouchers?tenant_id=${tenantId}&skip=${skip}&limit=${limit}`),

  // Cash flow endpoints
  getCashFlow: (tenantId: string, period = 'monthly') =>
    apiClient.get(`/api/dashboard/cash-flow?tenant_id=${tenantId}&period=${period}`),

  // Tenant config
  getTenantConfig: (tenantId: string) =>
    apiClient.get(`/api/tenants/${tenantId}/config`),
}

export default apiClient
```

- [ ] API client created
- [ ] JWT interceptor working
- [ ] Endpoints match backend API

#### Verification
```bash
npm run dev

# In browser console, test:
# const { useDashboardStore } = require('@/lib/store')
# const store = useDashboardStore.getState()
# store.setDarkMode(false)  # Should toggle
```

- [ ] React Query DevTools available at bottom-right
- [ ] Zustand store accessible
- [ ] No TypeScript errors

---

## Week 2: Core Widget Development

### Day 6-7: KPI Widget

#### Step 11: Create KPI Widget Component
```typescript
// src/components/widgets/KPIWidget.tsx

'use client'

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { AlertCircle } from 'lucide-react'

interface KPIData {
  total_ledgers: number
  total_vouchers: number
  last_sync: string
  sync_health: 'healthy' | 'warning' | 'error'
}

export default function KPIWidget({ data }: { data?: KPIData }) {
  const { data: kpiData, isLoading, error } = useQuery({
    queryKey: ['kpi_records'],
    queryFn: () => api.getKPIs('default-tenant'), // Replace with actual tenant ID
    enabled: !data,
  })

  const displayData = data || kpiData

  if (isLoading) {
    return (
      <Card className="bg-slate-900/50 border-slate-800">
        <CardHeader>
          <CardTitle>Sync Records</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-full" />
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="bg-slate-900/50 border-red-800">
        <CardHeader>
          <CardTitle className="text-red-400">Error</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-red-300">Failed to load KPIs</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="bg-slate-900/50 backdrop-blur border-slate-800 hover:border-slate-700 transition">
      <CardHeader>
        <CardTitle className="text-slate-50">Sync Records</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <p className="text-sm text-slate-400">Total Ledgers</p>
          <p className="text-2xl font-bold text-teal-400">
            {displayData?.total_ledgers?.toLocaleString() || '0'}
          </p>
        </div>
        <div>
          <p className="text-sm text-slate-400">Total Vouchers</p>
          <p className="text-2xl font-bold text-teal-400">
            {displayData?.total_vouchers?.toLocaleString() || '0'}
          </p>
        </div>
        <div className="pt-2 border-t border-slate-700">
          <p className="text-xs text-slate-400">
            Last sync: {displayData?.last_sync ? new Date(displayData.last_sync).toLocaleDateString() : 'Never'}
          </p>
          <div className="flex items-center gap-2 mt-1">
            <div className={`w-2 h-2 rounded-full ${
              displayData?.sync_health === 'healthy' ? 'bg-green-500' : 'bg-yellow-500'
            }`} />
            <span className="text-xs text-slate-400 capitalize">
              {displayData?.sync_health || 'unknown'}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
```

- [ ] Component created and exported
- [ ] Uses React Query to fetch data
- [ ] Shows loading skeleton
- [ ] Shows error state
- [ ] Displays KPIs with proper formatting

#### Step 12: Create Cash Flow Chart Widget
```typescript
// src/components/widgets/CashFlowChartWidget.tsx

'use client'

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import dynamic from 'next/dynamic'

// Dynamic import to avoid SSR issues
const AreaChart = dynamic(() => 
  import('recharts').then(mod => mod.AreaChart),
  { ssr: false, loading: () => <Skeleton className="h-64 w-full" /> }
)
const Area = dynamic(() => 
  import('recharts').then(mod => mod.Area),
  { ssr: false }
)
const XAxis = dynamic(() => 
  import('recharts').then(mod => mod.XAxis),
  { ssr: false}
)
const YAxis = dynamic(() => 
  import('recharts').then(mod => mod.YAxis),
  { ssr: false }
)
const CartesianGrid = dynamic(() => 
  import('recharts').then(mod => mod.CartesianGrid),
  { ssr: false }
)
const Tooltip = dynamic(() => 
  import('recharts').then(mod => mod.Tooltip),
  { ssr: false }
)
const ResponsiveContainer = dynamic(() => 
  import('recharts').then(mod => mod.ResponsiveContainer),
  { ssr: false }
)

export default function CashFlowChartWidget() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['cash_flow'],
    queryFn: () => api.getCashFlow('default-tenant'),
  })

  if (isLoading) return <Skeleton className="h-64 w-full" />
  if (error) return <div className="text-red-400">Error loading chart</div>

  return (
    <Card className="bg-slate-900/50 backdrop-blur border-slate-800">
      <CardHeader>
        <CardTitle className="text-slate-50">Cash Flow Trend</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorCash" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#0d9488" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="#0d9488" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="month" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" />
            <Tooltip 
              contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
              formatter={(value) => `₹${(value as number).toLocaleString('en-IN')}`}
            />
            <Area 
              type="monotone" 
              dataKey="amount" 
              stroke="#0d9488" 
              fillOpacity={1} 
              fill="url(#colorCash)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
```

- [ ] Recharts installed
- [ ] Chart component renders
- [ ] Dynamic imports prevent SSR errors
- [ ] Chart responsive to window resize

#### Step 13: Create Vouchers Table Widget
```typescript
// src/components/widgets/VouchersTableWidget.tsx

'use client'

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useState } from 'react'

interface Voucher {
  id: number
  voucher_number: string
  date: string
  party: string
  amount: string
  type: string
}

export default function VouchersTableWidget() {
  const [page, setPage] = useState(0)
  const pageSize = 10

  const { data, isLoading, error } = useQuery({
    queryKey: ['vouchers', page],
    queryFn: () => api.getVouchers('default-tenant', page * pageSize, pageSize),
  })

  if (isLoading) {
    return (
      <Card className="bg-slate-900/50 border-slate-800">
        <CardHeader>
          <CardTitle>Recent Vouchers</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-64 w-full" />
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="bg-slate-900/50 border-red-800">
        <CardHeader>
          <CardTitle className="text-red-400">Error</CardTitle>
        </CardHeader>
      </Card>
    )
  }

  return (
    <Card className="bg-slate-900/50 backdrop-blur border-slate-800">
      <CardHeader>
        <CardTitle className="text-slate-50">Recent Vouchers</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow className="border-slate-700 hover:bg-transparent">
              <TableHead className="text-slate-400">Date</TableHead>
              <TableHead className="text-slate-400">Voucher</TableHead>
              <TableHead className="text-slate-400">Party</TableHead>
              <TableHead className="text-slate-400">Type</TableHead>
              <TableHead className="text-slate-400 text-right">Amount</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data?.data?.map((voucher: Voucher) => (
              <TableRow key={voucher.id} className="border-slate-700 hover:bg-slate-800/50">
                <TableCell className="text-slate-300">{voucher.date}</TableCell>
                <TableCell className="text-slate-300 font-mono">{voucher.voucher_number}</TableCell>
                <TableCell className="text-slate-300">{voucher.party}</TableCell>
                <TableCell>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    voucher.type === 'Sales' ? 'bg-green-900/30 text-green-400' :
                    voucher.type === 'Purchase' ? 'bg-red-900/30 text-red-400' :
                    'bg-slate-700/30 text-slate-400'
                  }`}>
                    {voucher.type}
                  </span>
                </TableCell>
                <TableCell className="text-right text-slate-300">
                  ₹{parseFloat(voucher.amount).toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        
        {/* Pagination */}
        <div className="flex justify-between items-center mt-4 pt-4 border-t border-slate-700">
          <button
            onClick={() => setPage(Math.max(0, page - 1))}
            disabled={page === 0}
            className="px-3 py-1 text-sm rounded bg-slate-700 text-slate-300 disabled:opacity-50"
          >
            Previous
          </button>
          <span className="text-xs text-slate-400">
            Page {page + 1} of {Math.ceil((data?.total || 0) / pageSize)}
          </span>
          <button
            onClick={() => setPage(page + 1)}
            disabled={(page + 1) * pageSize >= (data?.total || 0)}
            className="px-3 py-1 text-sm rounded bg-slate-700 text-slate-300 disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </CardContent>
    </Card>
  )
}
```

- [ ] Table component displays vouchers
- [ ] Currency formatted as ₹ with en-IN locale
- [ ] Pagination working
- [ ] Color-coded transaction types

#### Verification
```bash
npm run dev

# Test each widget:
# - KPI loads and shows numbers
# - Chart renders with data
# - Table shows vouchers with proper formatting
# - No console errors
```

---

### Day 8-9: Dashboard Layout & Integration

#### Step 14: Create Dashboard Container
```typescript
// src/components/Dashboard.tsx

'use client'

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useDashboardStore } from '@/lib/store'
import { WIDGET_DEFINITIONS, DEFAULT_LAYOUTS } from '@/lib/widgetRegistry'
import { WidgetContainer } from './WidgetContainer'
import { Skeleton } from '@/components/ui/skeleton'

export default function Dashboard() {
  const { auth } = useDashboardStore()
  const tenantId = auth?.tenantId || 'default-tenant'
  const userRole = (auth?.role || 'viewer') as keyof typeof DEFAULT_LAYOUTS

  const { data: config, isLoading: configLoading } = useQuery({
    queryKey: ['tenant-config', tenantId],
    queryFn: () => api.getTenantConfig(tenantId),
  })

  if (configLoading) {
    return (
      <div className="grid gap-4 p-8 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
        {[...Array(3)].map((_, i) => (
          <Skeleton key={i} className="h-64" />
        ))}
      </div>
    )
  }

  const layout = DEFAULT_LAYOUTS[userRole] || []

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <header className="border-b border-slate-800 p-8">
        <h1 className="text-2xl font-bold text-slate-50">
          {config?.name || 'Dashboard'}
        </h1>
        <p className="text-sm text-slate-400 mt-1">Role: {userRole}</p>
      </header>

      {/* Dashboard Grid */}
      <main className="p-8">
        <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
          {layout.map((widgetConfig) => (
            <WidgetContainer
              key={widgetConfig.id}
              config={widgetConfig}
              tenantId={tenantId}
            />
          ))}
        </div>
      </main>
    </div>
  )
}
```

- [ ] Dashboard component created
- [ ] Uses widget registry to load widgets
- [ ] Role-based layout filtering working
- [ ] Header shows tenant name

#### Step 15: Create Widget Container
```typescript
// src/components/WidgetContainer.tsx

'use client'

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { WidgetConfig } from '@/types/widgets'
import { Skeleton } from '@/components/ui/skeleton'
import { AlertCircle } from 'lucide-react'

interface Props {
  config: WidgetConfig
  tenantId: string
}

export function WidgetContainer({ config, tenantId }: Props) {
  const getQueryFn = () => {
    switch (config.dataKey) {
      case 'kpi_records':
        return () => api.getKPIs(tenantId)
      case 'cash_flow':
        return () => api.getCashFlow(tenantId)
      case 'vouchers':
        return () => api.getVouchers(tenantId)
      default:
        return () => Promise.resolve({})
    }
  }

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: [config.dataKey, tenantId],
    queryFn: getQueryFn(),
    refetchInterval: config.refreshInterval || 30000,
    enabled: !!config.dataKey,
  })

  const Component = config.component

  if (isLoading) {
    return <Skeleton className="h-64 rounded-lg bg-slate-800" />
  }

  if (error) {
    return (
      <div className="p-4 rounded-lg border border-red-800 bg-red-900/20">
        <div className="flex items-center gap-2 text-red-400">
          <AlertCircle size={16} />
          <span className="text-sm">Failed to load {config.title}</span>
        </div>
      </div>
    )
  }

  return <Component data={data} />
}
```

- [ ] Widget container handles data loading
- [ ] Shows loading skeleton
- [ ] Shows error state
- [ ] Auto-refetch based on config

#### Step 16: Create Home Page
```typescript
// src/pages/index.tsx

import Dashboard from '@/components/Dashboard'

export default function Home() {
  return <Dashboard />
}
```

- [ ] Home page renders dashboard
- [ ] URL is http://localhost:3000

---

### Day 10: Backend API Integration

#### Step 17: Add Dashboard Endpoints to FastAPI

```python
# cloudplatform/api/dashboard.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta

from cloudplatform.db.models import Ledger, Voucher, SyncRecord, Tenant
from cloudplatform.db.database import get_db

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
        "last_sync": last_sync.created_at.isoformat() if last_sync else None,
        "sync_health": "healthy" if last_sync and (datetime.utcnow() - last_sync.created_at).days < 7 else "warning"
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
                "party": v.party,
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
    # For MVP: return mock data
    # In production: query vouchers and aggregate by period
    
    return [
        {"month": "2026-01", "amount": 450000},
        {"month": "2026-02", "amount": 520000},
        {"month": "2026-03", "amount": 480000},
        {"month": "2026-04", "amount": 610000},
        {"month": "2026-05", "amount": 580000},
        {"month": "2026-06", "amount": 720000},
    ]

@router.get("/tenants/{tenant_id}/config")
async def get_tenant_config(tenant_id: str, db: Session = Depends(get_db)):
    """Get tenant configuration for white-label."""
    tenant = db.query(Tenant).filter_by(id=tenant_id).first()
    
    if not tenant:
        return {
            "id": tenant_id,
            "name": "Default Tenant",
            "logo": None,
            "primaryColor": "#0d9488",
            "accentColor": "#d97706",
            "features": {
                "treds": True,
                "gst_compliance": True,
                "working_capital": True
            }
        }
    
    return {
        "id": tenant.id,
        "name": tenant.name,
        "logo": None,
        "primaryColor": "#0d9488",
        "accentColor": "#d97706",
        "features": {
            "treds": True,
            "gst_compliance": True,
            "working_capital": True
        }
    }

```

**In cloudplatform/main.py**, add the router:
```python
from cloudplatform.api.dashboard import router as dashboard_router

# Include routers
app.include_router(dashboard_router)
```

- [ ] Dashboard endpoints added to FastAPI
- [ ] `/api/dashboard/kpis` returns mock data
- [ ] `/api/dashboard/vouchers` returns paginated data
- [ ] `/api/dashboard/cash-flow` returns time-series
- [ ] `/api/tenants/{id}/config` returns tenant config
- [ ] No errors in backend logs

#### Step 18: Environment Configuration
```bash
# Create .env.local in frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_TENANT_ID=default-tenant
```

- [ ] `.env.local` created
- [ ] API URL points to local backend
- [ ] Frontend can reach backend

---

## Week 2-3: Testing & Verification

#### Step 19: Manual Testing Checklist

```
Dashboard Load:
  [ ] Homepage loads without errors
  [ ] Dark theme applied globally
  [ ] Responsive on desktop/tablet/mobile
  
KPI Widget:
  [ ] Loads data from API
  [ ] Shows correct numbers
  [ ] Last sync date formatted correctly
  [ ] Status indicator shows
  
Chart Widget:
  [ ] Chart renders
  [ ] Area chart fills correctly
  [ ] Tooltip shows on hover
  [ ] Responsive to window resize
  
Table Widget:
  [ ] Displays vouchers
  [ ] Currency formatted: ₹123,456.78
  [ ] Party names (including Devanagari) render correctly
  [ ] Pagination buttons work
  [ ] Color-coded transaction types
  
Multi-Role:
  [ ] Set auth.role = 'admin' → all widgets shown
  [ ] Set auth.role = 'finance' → only finance widgets shown
  [ ] Set auth.role = 'viewer' → only KPI shown
  
Dark Mode:
  [ ] Background is slate-950
  [ ] Text is readable
  [ ] Cards have glass effect
  [ ] All icons visible
```

#### Step 20: Performance Testing
```bash
# Lighthouse audit in Chrome DevTools
npm run build

# Expected scores:
# Performance: 85+
# Accessibility: 90+
# Best Practices: 90+
# SEO: 90+
```

- [ ] Production build succeeds
- [ ] Bundle size < 200 KB gzipped
- [ ] Lighthouse scores acceptable

#### Step 21: Browser Compatibility
```
Test on:
  [ ] Chrome 120+
  [ ] Firefox 121+
  [ ] Safari 17+
  [ ] Edge 120+
  
Verify:
  [ ] No console errors
  [ ] All widgets render
  [ ] Responsive layout works
  [ ] Dark theme colors correct
```

---

## Deliverables Checklist

### Phase 0-1 Deliverables
- [ ] Next.js 16 + TypeScript project
- [ ] shadcn/ui components integrated
- [ ] Tailwind CSS configured (dark-first)
- [ ] Widget registry system working
- [ ] React Query + Zustand integrated
- [ ] 3 core widgets (KPI, Chart, Table)
- [ ] Dashboard layout responsive
- [ ] API integration working
- [ ] Backend endpoints implemented
- [ ] Environment configuration complete
- [ ] Manual testing passed
- [ ] Performance optimized

### Documentation
- [ ] README.md with setup instructions
- [ ] Component documentation
- [ ] API documentation
- [ ] Widget registry documentation

### Code Quality
- [ ] No TypeScript errors
- [ ] ESLint checks passing
- [ ] Code formatted with Prettier
- [ ] Git commits with clear messages

---

## Troubleshooting

### Issue: "Cannot find module '@/components/ui/card'"
**Solution**: Ensure shadcn/ui components installed:
```bash
npx shadcn-ui@latest add card
```

### Issue: "API request failing with CORS error"
**Solution**: Add CORS headers to FastAPI:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: "Dark mode not applying"
**Solution**: Check `src/pages/_app.tsx` has dark class wrapper:
```typescript
<div className="dark">
  <Component {...pageProps} />
</div>
```

### Issue: "Recharts not rendering"
**Solution**: Use dynamic import:
```typescript
const AreaChart = dynamic(() => 
  import('recharts').then(mod => mod.AreaChart),
  { ssr: false }
)
```

---

## Next Steps (Phase 2)

After Phase 0-1 completion:
1. Install Recharts: `npm install recharts`
2. Install Plotly: `npm install plotly.js react-plotly.js`
3. Implement 5+ financial widgets
4. Deploy Apache Superset
5. Begin Phase 2 testing

---

**Phase 0-1 Status**: Ready to implement  
**Estimated Duration**: 2-3 weeks  
**Team**: 1 Frontend + 1 Backend + 1 QA  
**Next Review**: After widget implementations complete

**Questions?** Check FINTECH_UI_IMPLEMENTATION_STRATEGY.md
