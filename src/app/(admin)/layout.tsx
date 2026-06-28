'use client'

import { useEffect, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useDashboardStore } from '@/lib/store'
import AdminSidebar from '@/components/AdminSidebar'

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const { accessToken } = useDashboardStore()
  const [checked, setChecked] = useState(false)

  useEffect(() => {
    const token = accessToken || localStorage.getItem('access_token')
    if (!token) {
      router.replace('/login')
    } else {
      setChecked(true)
    }
  }, [accessToken, router])

  if (!checked) return null

  // Client sub-pages render their own layout with sidebar (via [clientId]/layout.tsx)
  const isClientView = /^\/clients\/[^/]+/.test(pathname)
  if (isClientView) {
    return <>{children}</>
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#0f172a' }}>
      <AdminSidebar />
      <main style={{ flex: 1, padding: 24, maxWidth: 1280, width: '100%', minWidth: 0 }}>
        {children}
      </main>
    </div>
  )
}
