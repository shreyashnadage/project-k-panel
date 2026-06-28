'use client'

import { usePathname, useRouter } from 'next/navigation'
import { useDashboardStore } from '@/lib/store'
import {
  LayoutDashboard, FileText, BookOpen, Monitor, Radio,
  Settings, LogOut, ChevronLeft, ChevronRight, Users, ArrowLeft,
} from 'lucide-react'

interface NavItem {
  path: string
  label: string
  Icon: React.ElementType
}

export default function AdminSidebar({ clientName }: { clientName?: string }) {
  const pathname = usePathname()
  const router = useRouter()
  const { sidebarCollapsed, setSidebarCollapsed, clearAuth } = useDashboardStore()

  const isClientView = pathname.startsWith('/clients/') && pathname.split('/').length >= 3
  const clientBase = isClientView ? pathname.split('/').slice(0, 3).join('/') : ''

  const adminNav: NavItem[] = [
    { path: '/clients', label: 'Clients', Icon: Users },
  ]

  const clientNav: NavItem[] = [
    { path: clientBase, label: 'Dashboard', Icon: LayoutDashboard },
    { path: `${clientBase}/vouchers`, label: 'Vouchers', Icon: FileText },
    { path: `${clientBase}/ledgers`, label: 'Ledgers', Icon: BookOpen },
    { path: `${clientBase}/devices`, label: 'Devices', Icon: Monitor },
    { path: `${clientBase}/sync-history`, label: 'Sync History', Icon: Radio },
  ]

  const nav = isClientView ? clientNav : adminNav

  const isActive = (path: string) => {
    if (isClientView && path === clientBase) {
      return pathname === clientBase
    }
    return pathname === path || pathname.startsWith(path + '/')
  }

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    clearAuth()
    router.push('/login')
  }

  return (
    <aside
      style={{
        width: sidebarCollapsed ? 64 : 240,
        background: '#0f172a',
        borderRight: '1px solid #1e293b',
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        position: 'sticky',
        top: 0,
        transition: 'width 0.2s ease',
        flexShrink: 0,
      }}
    >
      {/* Logo */}
      <div style={{ padding: '24px 20px 20px', borderBottom: '1px solid #1e293b' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10, flexShrink: 0,
            background: 'linear-gradient(135deg, #14b8a6, #0d9488)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#fff', fontWeight: 800, fontSize: 14,
            fontFamily: 'Outfit, system-ui, sans-serif',
          }}>
            TS
          </div>
          {!sidebarCollapsed && (
            <span style={{ fontFamily: 'Outfit, system-ui', fontWeight: 700, fontSize: 16, color: '#f1f5f9', whiteSpace: 'nowrap' }}>
              Tally Sync
            </span>
          )}
        </div>
      </div>

      {/* Back to clients + client name */}
      {isClientView && (
        <div style={{ padding: '12px 8px 4px' }}>
          <button
            onClick={() => router.push('/clients')}
            style={{
              width: '100%', display: 'flex', alignItems: 'center', gap: 8,
              padding: '8px 12px', borderRadius: 8, border: 'none', cursor: 'pointer',
              background: 'transparent', color: '#64748b',
              fontFamily: 'Inter, system-ui', fontWeight: 500, fontSize: 13,
              textAlign: 'left', transition: 'all 0.15s',
            }}
            onMouseEnter={e => { e.currentTarget.style.color = '#f1f5f9'; e.currentTarget.style.background = '#1e293b' }}
            onMouseLeave={e => { e.currentTarget.style.color = '#64748b'; e.currentTarget.style.background = 'transparent' }}
          >
            <ArrowLeft size={14} />
            {!sidebarCollapsed && 'All Clients'}
          </button>
          {!sidebarCollapsed && clientName && (
            <div style={{
              padding: '6px 12px', fontSize: 12, fontWeight: 600, color: '#14b8a6',
              fontFamily: 'Inter, system-ui', overflow: 'hidden', textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}>
              {clientName}
            </div>
          )}
        </div>
      )}

      {/* Nav items */}
      <nav style={{ flex: 1, padding: '12px 8px', overflowY: 'auto' }}>
        {nav.map(({ path, label, Icon }) => {
          const active = isActive(path)
          return (
            <button
              key={path}
              onClick={() => router.push(path)}
              aria-label={label}
              title={sidebarCollapsed ? label : undefined}
              style={{
                width: '100%', display: 'flex', alignItems: 'center',
                gap: 12, padding: '10px 12px', borderRadius: 8,
                border: 'none', cursor: 'pointer', marginBottom: 2,
                background: active ? '#14b8a6' : 'transparent',
                color: active ? '#ffffff' : '#94a3b8',
                fontFamily: 'Inter, system-ui', fontWeight: 500, fontSize: 14,
                transition: 'all 0.15s ease',
                textAlign: 'left',
              }}
              onMouseEnter={e => { if (!active) { e.currentTarget.style.background = '#1e293b'; e.currentTarget.style.color = '#f1f5f9' } }}
              onMouseLeave={e => { if (!active) { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = '#94a3b8' } }}
            >
              <Icon size={18} style={{ flexShrink: 0 }} />
              {!sidebarCollapsed && <span style={{ whiteSpace: 'nowrap' }}>{label}</span>}
            </button>
          )
        })}
      </nav>

      {/* Bottom items */}
      <div style={{ padding: '8px 8px 12px', borderTop: '1px solid #1e293b' }}>
        <button
          onClick={() => router.push('/settings')}
          aria-label="Settings"
          style={{
            width: '100%', display: 'flex', alignItems: 'center',
            gap: 12, padding: '10px 12px', borderRadius: 8,
            border: 'none', cursor: 'pointer', marginBottom: 2,
            background: pathname === '/settings' ? '#14b8a6' : 'transparent',
            color: pathname === '/settings' ? '#fff' : '#94a3b8',
            fontFamily: 'Inter, system-ui', fontWeight: 500, fontSize: 14, textAlign: 'left',
            transition: 'all 0.15s ease',
          }}
        >
          <Settings size={18} style={{ flexShrink: 0 }} />
          {!sidebarCollapsed && <span>Settings</span>}
        </button>
        <button
          onClick={handleLogout}
          aria-label="Logout"
          style={{
            width: '100%', display: 'flex', alignItems: 'center',
            gap: 12, padding: '10px 12px', borderRadius: 8,
            border: 'none', cursor: 'pointer',
            background: 'transparent', color: '#94a3b8',
            fontFamily: 'Inter, system-ui', fontWeight: 500, fontSize: 14, textAlign: 'left',
            transition: 'all 0.15s ease',
          }}
        >
          <LogOut size={18} style={{ flexShrink: 0 }} />
          {!sidebarCollapsed && <span>Logout</span>}
        </button>
      </div>

      {/* Collapse toggle */}
      <button
        onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
        aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        style={{
          position: 'absolute', top: 80, right: -12,
          width: 24, height: 24, borderRadius: '50%',
          border: '1px solid #334155', background: '#1e293b',
          color: '#94a3b8', cursor: 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 10,
        }}
      >
        {sidebarCollapsed ? <ChevronRight size={12} /> : <ChevronLeft size={12} />}
      </button>
    </aside>
  )
}
