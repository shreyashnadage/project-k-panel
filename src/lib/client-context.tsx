'use client'

import { createContext, useContext, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { adminApi, scopedApi, analyticsApi } from '@/lib/api'
import type { ClientDetail, ClientDeviceInfo } from '@/types/widgets'

interface ClientContextValue {
  clientId: string
  companyName: string
  apiKey: string | null
  deviceId: string | null
  devices: ClientDeviceInfo[]
  detail: ClientDetail | null
  isLoading: boolean
  error: string | null
  clientApi: ReturnType<typeof scopedApi> | null
  analyticsClient: ReturnType<typeof analyticsApi> | null
}

const ClientContext = createContext<ClientContextValue | null>(null)

export function ClientContextProvider({
  clientId,
  children,
}: {
  clientId: string
  children: React.ReactNode
}) {
  const detailQuery = useQuery({
    queryKey: ['admin-client-detail', clientId],
    queryFn: () => adminApi.getClientDetail(clientId),
    staleTime: 60_000,
  })

  const apiKeyQuery = useQuery({
    queryKey: ['admin-client-apikey', clientId],
    queryFn: () => adminApi.getClientApiKey(clientId),
    staleTime: 120_000,
    retry: false,
  })

  const apiKey = apiKeyQuery.data?.api_key ?? null
  const deviceId = apiKeyQuery.data?.device_id ?? null

  const clientApiInstance = useMemo(
    () => (apiKey ? scopedApi(apiKey) : null),
    [apiKey],
  )

  const analyticsClientInstance = useMemo(
    () => (apiKey ? analyticsApi(apiKey) : null),
    [apiKey],
  )

  const value: ClientContextValue = {
    clientId,
    companyName: detailQuery.data?.company_name ?? 'Loading...',
    apiKey,
    deviceId,
    devices: detailQuery.data?.devices ?? [],
    detail: detailQuery.data ?? null,
    isLoading: detailQuery.isLoading || apiKeyQuery.isLoading,
    error: apiKeyQuery.error
      ? 'No active devices for this client'
      : detailQuery.error
        ? 'Failed to load client'
        : null,
    clientApi: clientApiInstance,
    analyticsClient: analyticsClientInstance,
  }

  return (
    <ClientContext.Provider value={value}>
      {children}
    </ClientContext.Provider>
  )
}

export function useClientContext() {
  const ctx = useContext(ClientContext)
  if (!ctx) throw new Error('useClientContext must be used within ClientContextProvider')
  return ctx
}

export function useAnalyticsApi() {
  const { analyticsClient } = useClientContext()
  return analyticsClient
}
