'use client'

import { use } from 'react'
import { ClientContextProvider, useClientContext } from '@/lib/client-context'
import AdminSidebar from '@/components/AdminSidebar'

function ClientShell({ children }: { children: React.ReactNode }) {
  const { companyName, isLoading, error } = useClientContext()

  if (isLoading) {
    return (
      <div style={{ display: 'flex', minHeight: '100vh', background: '#0f172a' }}>
        <AdminSidebar clientName="Loading..." />
        <main style={{ flex: 1, padding: 24, maxWidth: 1280, width: '100%', minWidth: 0 }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div className="skeleton" style={{ height: 32, width: 200 }} />
            <div className="skeleton" style={{ height: 200, width: '100%' }} />
          </div>
        </main>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#0f172a' }}>
      <AdminSidebar clientName={companyName} />
      <main style={{ flex: 1, padding: 24, maxWidth: 1280, width: '100%', minWidth: 0 }}>
        {error && (
          <div style={{
            padding: '12px 16px', borderRadius: 8, marginBottom: 16,
            background: '#f59e0b15', border: '1px solid #f59e0b40', color: '#fbbf24', fontSize: 13,
          }}>
            {error}
          </div>
        )}
        {children}
      </main>
    </div>
  )
}

export default function ClientLayout({
  children,
  params,
}: {
  children: React.ReactNode
  params: Promise<{ clientId: string }>
}) {
  const { clientId } = use(params)

  return (
    <ClientContextProvider clientId={clientId}>
      <ClientShell>{children}</ClientShell>
    </ClientContextProvider>
  )
}
