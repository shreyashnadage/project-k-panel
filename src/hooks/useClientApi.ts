'use client'

import { useClientContext } from '@/lib/client-context'
import { scopedApi } from '@/lib/api'

export function useClientApi(): ReturnType<typeof scopedApi> | null {
  const { clientApi } = useClientContext()
  return clientApi
}
