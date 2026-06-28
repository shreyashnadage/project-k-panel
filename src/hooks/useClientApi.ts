'use client'

import { useClientContext } from '@/lib/client-context'

export function useClientApi() {
  const { clientApi } = useClientContext()
  if (!clientApi) throw new Error('Client API not available — no active device for this client')
  return clientApi
}
