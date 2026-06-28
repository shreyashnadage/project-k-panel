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

export interface LedgerItem {
  id: number
  name: string
  parent: string | null
  ledger_type: string | null
  opening_balance: string | null
  closing_balance: string | null
}

export interface LedgersResponse {
  data: LedgerItem[]
  total: number
  skip: number
  limit: number
}

export interface SyncCommandItem {
  id: string
  command_type: string
  status: string
  params: Record<string, string> | null
  created_at: string
  fetched_at: string | null
  completed_at: string | null
  result: Record<string, unknown> | null
  error_message: string | null
}

export interface SyncHistoryResponse {
  data: SyncCommandItem[]
  total: number
  skip: number
  limit: number
}

export type SyncCommandType =
  | 'sync_ledgers'
  | 'sync_ledgers_by_group'
  | 'sync_groups'
  | 'sync_vouchers'
  | 'sync_vouchers_by_type'
  | 'sync_stock'
  | 'sync_stock_by_group'
  | 'sync_full'
  | 'health_check'

export interface ClientSummary {
  client_id: string
  company_name: string
  email: string
  phone: string | null
  gst_id: string | null
  status: 'pending_verification' | 'active' | 'suspended' | 'inactive'
  plan: string
  device_count: number
  last_sync_at: string | null
  created_at: string | null
}

export interface ClientsListResponse {
  clients: ClientSummary[]
  total: number
}

export interface ClientDeviceInfo {
  device_id: string
  device_name: string
  status: string
  os_version: string | null
  agent_version: string | null
  last_sync_at: string | null
  registered_at: string | null
}

export interface ClientCompanyInfo {
  id: number
  company_name: string
  company_guid: string | null
  device_id: string
  is_active: boolean
  last_synced_at: string | null
}

export interface ClientDetail extends ClientSummary {
  devices: ClientDeviceInfo[]
  companies: ClientCompanyInfo[]
}
