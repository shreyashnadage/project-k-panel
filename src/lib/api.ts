import axios from 'axios'
import type {
  KPIData, VouchersResponse, CashFlowData, TenantConfig, Device,
  LedgersResponse, SyncHistoryResponse, SyncCommandType,
  ClientsListResponse, ClientDetail,
} from '@/types/widgets'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === 'true'

export const apiClient = axios.create({ baseURL: BASE_URL })

apiClient.interceptors.request.use((config) => {
  const apiKey = process.env.NEXT_PUBLIC_API_KEY || 'demo-api-key'
  config.headers['x-api-key'] = apiKey
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token')
    if (token) config.headers['Authorization'] = `Bearer ${token}`
  }
  return config
})

// ─── Scoped API client factory ───────────────────────────────
function createScopedClient(apiKey: string) {
  const client = axios.create({ baseURL: BASE_URL })
  client.interceptors.request.use((config) => {
    config.headers['x-api-key'] = apiKey
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token')
      if (token) config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  })
  return client
}

export function scopedApi(apiKey: string) {
  const client = createScopedClient(apiKey)
  return {
    getKPIs: async (): Promise<KPIData> => {
      const { data } = await client.get<KPIData>('/api/dashboard/kpis')
      return data
    },
    getVouchers: async (skip = 0, limit = 50): Promise<VouchersResponse> => {
      const { data } = await client.get<VouchersResponse>(`/api/dashboard/vouchers?skip=${skip}&limit=${limit}`)
      return data
    },
    getCashFlow: async (period = 'monthly', months = 6): Promise<CashFlowData[]> => {
      const { data } = await client.get<CashFlowData[]>(`/api/dashboard/cash-flow?period=${period}&months=${months}`)
      return data
    },
    getTenantConfig: async (): Promise<TenantConfig> => {
      const { data } = await client.get<TenantConfig>('/api/dashboard/tenant-config')
      return data
    },
    getDevices: async (): Promise<Device[]> => {
      const { data } = await client.get<Device[]>('/v1/devices/list')
      return data
    },
    getLedgers: async (skip = 0, limit = 50, search?: string, parent?: string): Promise<LedgersResponse> => {
      const params = new URLSearchParams({ skip: String(skip), limit: String(limit) })
      if (search) params.set('search', search)
      if (parent) params.set('parent', parent)
      const { data } = await client.get<LedgersResponse>(`/api/dashboard/ledgers?${params}`)
      return data
    },
    getLedgerGroups: async (): Promise<string[]> => {
      const { data } = await client.get<string[]>('/api/dashboard/ledgers/groups')
      return data
    },
    getSyncHistory: async (skip = 0, limit = 50, status?: string): Promise<SyncHistoryResponse> => {
      const params = new URLSearchParams({ skip: String(skip), limit: String(limit) })
      if (status) params.set('status', status)
      const { data } = await client.get<SyncHistoryResponse>(`/api/dashboard/sync-history?${params}`)
      return data
    },
    createCommand: async (deviceId: string, commandType: SyncCommandType, cmdParams: Record<string, string> = {}) => {
      const { data } = await client.post('/v1/commands', {
        device_id: deviceId,
        command_type: commandType,
        params: cmdParams,
        created_by: 'admin-dashboard',
      })
      return data
    },
  }
}

// ─── Admin API (uses JWT, no x-api-key scoping) ─────────────
function authClient() {
  const client = axios.create({ baseURL: BASE_URL })
  client.interceptors.request.use((config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token')
      if (token) config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  })
  return client
}

export const adminApi = {
  login: async (email: string, password: string) => {
    const { data } = await axios.post(`${BASE_URL}/v1/auth/login`, { email, password })
    return data as { access_token: string; refresh_token: string; token_type: string; expires_in: number }
  },

  getMe: async () => {
    const { data } = await authClient().get('/v1/auth/me')
    return data as { client_id: string; company_name: string; email: string; status: string }
  },

  getClients: async (skip = 0, limit = 50, search?: string): Promise<ClientsListResponse> => {
    const params = new URLSearchParams({ skip: String(skip), limit: String(limit) })
    if (search) params.set('search', search)
    const { data } = await authClient().get<ClientsListResponse>(`/v1/admin/clients?${params}`)
    return data
  },

  getClientDetail: async (clientId: string): Promise<ClientDetail> => {
    const { data } = await authClient().get<ClientDetail>(`/v1/admin/clients/${clientId}`)
    return data
  },

  getClientApiKey: async (clientId: string): Promise<{ api_key: string; device_id: string; device_name: string }> => {
    const { data } = await authClient().get(`/v1/admin/clients/${clientId}/api-key`)
    return data
  },

  onboardClient: async (req: {
    company_name: string; email: string; phone?: string; gst_id?: string; plan?: string
  }): Promise<{
    client_id: string; company_name: string; email: string; status: string;
    plan: string; installation_key: string; key_expires_at: string;
  }> => {
    const { data } = await authClient().post('/v1/admin/onboard-client', req)
    return data
  },
}

// ─── Legacy api object (kept for backward compat during migration) ──
const MOCK_KPI: KPIData = {
  total_ledgers: 234, total_vouchers: 1589,
  last_sync: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
  sync_health: 'healthy', recent_syncs: 42,
}
const MOCK_CASH_FLOW: CashFlowData[] = [
  { month: '2026-01', amount: 450000 }, { month: '2026-02', amount: 520000 },
  { month: '2026-03', amount: 480000 }, { month: '2026-04', amount: 610000 },
  { month: '2026-05', amount: 580000 }, { month: '2026-06', amount: 720000 },
]
const MOCK_VOUCHERS = [
  { id: 1, voucher_number: 'V-001', date: '2026-06-28', party: 'Sharma Traders Pvt Ltd', amount: '45000.00', type: 'Sales' },
  { id: 2, voucher_number: 'V-002', date: '2026-06-27', party: 'Patel Industries', amount: '32500.00', type: 'Purchase' },
]
const MOCK_DEVICES: Device[] = [{
  device_id: 'dev_001', device_name: 'OFFICE-PC-01', status: 'active',
  registered_at: '2026-06-01T10:00:00Z', last_sync_at: new Date(Date.now() - 1000 * 60 * 120).toISOString(),
  last_ip: '192.168.1.100', os_version: 'Windows 11 Build 26200', agent_version: '0.4.0',
}]
const delay = (ms: number) => new Promise(r => setTimeout(r, ms))

export const api = {
  getKPIs: async (): Promise<KPIData> => {
    if (USE_MOCK) { await delay(400); return MOCK_KPI }
    const { data } = await apiClient.get<KPIData>('/api/dashboard/kpis')
    return data
  },
  getVouchers: async (skip = 0, limit = 50): Promise<VouchersResponse> => {
    if (USE_MOCK) { await delay(300); return { data: MOCK_VOUCHERS.slice(skip, skip + limit), total: MOCK_VOUCHERS.length, skip, limit } }
    const { data } = await apiClient.get<VouchersResponse>(`/api/dashboard/vouchers?skip=${skip}&limit=${limit}`)
    return data
  },
  getCashFlow: async (period = 'monthly', months = 6): Promise<CashFlowData[]> => {
    if (USE_MOCK) { await delay(350); return MOCK_CASH_FLOW }
    const { data } = await apiClient.get<CashFlowData[]>(`/api/dashboard/cash-flow?period=${period}&months=${months}`)
    return data
  },
  getTenantConfig: async (): Promise<TenantConfig> => {
    if (USE_MOCK) return { id: 'demo', name: 'Sharma Traders Pvt Ltd', logo: null, primaryColor: '#14b8a6', accentColor: '#f59e0b' }
    const { data } = await apiClient.get<TenantConfig>('/api/dashboard/tenant-config')
    return data
  },
  getDevices: async (): Promise<Device[]> => {
    if (USE_MOCK) { await delay(300); return MOCK_DEVICES }
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
    const { data } = await apiClient.get<Device[]>('/v1/devices/list', {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    return data
  },
  getLedgers: async (skip = 0, limit = 50, search?: string, parent?: string): Promise<LedgersResponse> => {
    const params = new URLSearchParams({ skip: String(skip), limit: String(limit) })
    if (search) params.set('search', search)
    if (parent) params.set('parent', parent)
    const { data } = await apiClient.get<LedgersResponse>(`/api/dashboard/ledgers?${params}`)
    return data
  },
  getLedgerGroups: async (): Promise<string[]> => {
    const { data } = await apiClient.get<string[]>('/api/dashboard/ledgers/groups')
    return data
  },
  getSyncHistory: async (skip = 0, limit = 50, status?: string): Promise<SyncHistoryResponse> => {
    const params = new URLSearchParams({ skip: String(skip), limit: String(limit) })
    if (status) params.set('status', status)
    const { data } = await apiClient.get<SyncHistoryResponse>(`/api/dashboard/sync-history?${params}`)
    return data
  },
  createCommand: async (deviceId: string, commandType: SyncCommandType, cmdParams: Record<string, string> = {}) => {
    const { data } = await apiClient.post('/v1/commands', {
      device_id: deviceId, command_type: commandType, params: cmdParams, created_by: 'dashboard',
    })
    return data
  },
}

export default apiClient
