export type PageType = 'dashboard' | 'vouchers' | 'ledgers' | 'devices' | 'sync-history' | 'settings'

export type VoucherType = 'Sales' | 'Purchase' | 'Receipt' | 'Payment' | 'Journal' | 'Debit Note' | 'Credit Note'

export const VOUCHER_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  'Sales':       { bg: '#3db8a915', text: '#3db8a9', border: '#3db8a940' },
  'Purchase':    { bg: '#a8b8c815', text: '#a8b8c8', border: '#a8b8c840' },
  'Receipt':     { bg: '#2a9d8f15', text: '#2a9d8f', border: '#2a9d8f40' },
  'Payment':     { bg: '#c45c4a15', text: '#c45c4a', border: '#c45c4a40' },
  'Journal':     { bg: '#d4a37315', text: '#d4a373', border: '#d4a37340' },
  'Debit Note':  { bg: '#e07a3d15', text: '#e07a3d', border: '#e07a3d40' },
  'Credit Note': { bg: '#e07a3d15', text: '#e07a3d', border: '#e07a3d40' },
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
