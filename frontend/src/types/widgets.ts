export type PageType = 'overview' | 'tally-sync' | 'msme' | 'treds' | 'activity' | 'health' | 'settings'

export interface WidgetConfig {
  id: string
  component: React.ComponentType<any>
  title: string
  description: string
  size: 'small' | 'medium' | 'large' | 'full'
  roles: ('admin' | 'finance' | 'accountant' | 'viewer')[]
  dataKey?: string
  refreshInterval?: number
}

export interface WidgetLayoutConfig {
  widgets: WidgetConfig[]
}

export interface TenantConfig {
  id: string
  name: string
  logo?: string
  primaryColor?: string
  accentColor?: string
}

export interface AuthContext {
  userId?: string
  tenantId?: string
  role?: 'admin' | 'finance' | 'accountant' | 'viewer'
}

export interface KPIData {
  total_ledgers: number
  total_vouchers: number
  last_sync: string
  sync_health: 'healthy' | 'warning' | 'error'
}

export interface Voucher {
  id: number
  voucher_number: string
  date: string
  party: string
  amount: string
  type: string
}

export interface VouchersResponse {
  data: Voucher[]
  total: number
  skip: number
  limit: number
}

export interface CashFlowData {
  month: string
  amount: number
}
