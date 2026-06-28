export type PageType = 'dashboard' | 'vouchers' | 'ledgers' | 'devices' | 'sync-history' | 'settings'

export type VoucherType = 'Sales' | 'Purchase' | 'Receipt' | 'Payment' | 'Journal' | 'Debit Note' | 'Credit Note'

export const VOUCHER_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  'Sales':       { bg: '#dcfce7', text: '#166534', border: '#86efac' },
  'Purchase':    { bg: '#dbeafe', text: '#1e3a8a', border: '#93c5fd' },
  'Receipt':     { bg: '#d1fae5', text: '#065f46', border: '#6ee7b7' },
  'Payment':     { bg: '#fee2e2', text: '#991b1b', border: '#fca5a5' },
  'Journal':     { bg: '#f3e8ff', text: '#581c87', border: '#c4b5fd' },
  'Debit Note':  { bg: '#fef3c7', text: '#92400e', border: '#fcd34d' },
  'Credit Note': { bg: '#fce7f3', text: '#9d174d', border: '#f9a8d4' },
}

export interface KPIData {
  total_ledgers: number
  total_vouchers: number
  last_sync: string | null
  sync_health: 'healthy' | 'warning' | 'error'
  recent_syncs?: number
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

export interface TenantConfig {
  id: string
  name: string
  logo?: string | null
  primaryColor?: string
  accentColor?: string
}

export interface Device {
  device_id: string
  device_name: string
  status: 'active' | 'inactive' | 'error'
  registered_at: string
  last_sync_at: string | null
  last_ip: string | null
  os_version: string | null
  agent_version: string | null
}
