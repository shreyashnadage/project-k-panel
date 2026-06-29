'use client'

import { usePathname, useRouter } from 'next/navigation'
import { useDashboardStore } from '@/lib/store'
import {
  LayoutDashboard, FileText, BookOpen, Monitor, Radio, AlertTriangle,
  Settings, LogOut, ChevronLeft, ChevronRight, Users, ArrowLeft,
  BarChart3, Bell, Lightbulb, CreditCard, Zap,
} from 'lucide-react'

const C = {
  navy:        '#0d1b2a',
  navyMuted:   '#1b263b',
  navyElev:    '#152a40',
  tealDark:    '#3db8a9',
  cream:       '#f5f0e8',
  textSecDark: '#a8b8c8',
  borderDark:  '#2d3e50',
}

interface NavItem {
  path: string
  label: string
  Icon: React.ElementType
}

interface NavSection {
  title?: string
  items: NavItem[]
}

export default function AdminSidebar({ clientName }: { clientName?: string }) {
  const pathname = usePathname()
  const router = useRouter()
  const { sidebarCollapsed, setSidebarCollapsed, clearAuth } = useDashboardStore()

  const isClientView = pathname.startsWith('/clients/') && pathname.split('/').length >= 3
  const clientBase = isClientView ? pathname.split('/').slice(0, 3).join('/') : ''

  const adminSections: NavSection[] = [
    { items: [{ path: '/clients', label: 'Clients', Icon: Users }] },
  ]

  const clientSections: NavSection[] = [
    {
      items: [
        { path: clientBase, label: 'Dashboard', Icon: LayoutDashboard },
        { path: `${clientBase}/vouchers`, label: 'Vouchers', Icon: FileText },
        { path: `${clientBase}/ledgers`, label: 'Ledgers', Icon: BookOpen },
        { path: `${clientBase}/devices`, label: 'Devices', Icon: Monitor },
        { path: `${clientBase}/sync-history`, label: 'Sync History', Icon: Radio },
        { path: `${clientBase}/agent-logs`, label: 'Agent Logs', Icon: AlertTriangle },
      ],
    },
    {
      title: 'Analytics Engine',
      items: [
        { path: `${clientBase}/analytics`, label: 'Overview', Icon: BarChart3 },
        { path: `${clientBase}/analytics/alerts`, label: 'Alerts', Icon: Bell },
        { path: `${clientBase}/analytics/insights`, label: 'Insights', Icon: Lightbulb },
        { path: `${clientBase}/analytics/loan`, label: 'Loan Recs', Icon: CreditCard },
        { path: `${clientBase}/analytics/pipeline`, label: 'Pipeline', Icon: Zap },
      ],
    },
  ]

  const sections = isClientView ? clientSections : adminSections

  const isActive = (path: string) => {
    if (isClientView && path === clientBase) return pathname === clientBase
    if (isClientView && path === `${clientBase}/analytics`) return pathname === `${clientBase}/analytics`
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
        background: C.navy,
        borderRight: `1px solid ${C.borderDark}`,
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        position: 'sticky',
        top: 0,
        transition: 'width 0.2s ease',
        flexShrink: 0,
      }}
    >
      {/* Wordmark */}
      <div style={{ padding: '24px 20px 20px', borderBottom: `1px solid ${C.borderDark}` }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10, flexShrink: 0,
            background: C.tealDark,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: C.navy, fontWeight: 700, fontSize: 14,
          }}>
            Mc
          </div>
          {!sidebarCollapsed && (
            <span style={{ fontWeight: 700, fontSize: 16, color: C.cream, whiteSpace: 'nowrap' }}>
              <span style={{ color: C.cream }}>Munim</span>
              <span style={{ color: C.tealDark }}>Co</span>
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
              background: 'transparent', color: C.textSecDark,
              fontWeight: 500, fontSize: 13,
              textAlign: 'left', transition: 'all 0.15s',
            }}
            onMouseEnter={e => { e.currentTarget.style.color = C.cream; e.currentTarget.style.background = C.navyMuted }}
            onMouseLeave={e => { e.currentTarget.style.color = C.textSecDark; e.currentTarget.style.background = 'transparent' }}
          >
            <ArrowLeft size={14} />
            {!sidebarCollapsed && 'All Clients'}
          </button>
          {!sidebarCollapsed && clientName && (
            <div style={{
              padding: '6px 12px', fontSize: 12, fontWeight: 600, color: C.tealDark,
              overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
            }}>
              {clientName}
            </div>
          )}
        </div>
      )}

      {/* Nav items */}
      <nav style={{ flex: 1, padding: '12px 8px', overflowY: 'auto' }}>
        {sections.map((section, si) => (
          <div key={si}>
            {section.title && !sidebarCollapsed && (
              <div style={{
                padding: '12px 12px 4px',
                fontSize: 10, fontWeight: 700, letterSpacing: '0.08em',
                color: C.borderDark, textTransform: 'uppercase',
                marginTop: si > 0 ? 8 : 0,
              }}>
                {section.title}
              </div>
            )}
            {section.title && sidebarCollapsed && si > 0 && (
              <div style={{ height: 1, background: C.borderDark, margin: '8px 4px' }} />
            )}
            {section.items.map(({ path, label, Icon }) => {
              const active = isActive(path)
              return (
                <button
                  key={path}
                  onClick={() => router.push(path)}
                  aria-label={label}
                  title={sidebarCollapsed ? label : undefined}
                  style={{
                    width: '100%', display: 'flex', alignItems: 'center',
                    gap: 12, padding: active ? '10px 12px 10px 9px' : '10px 12px',
                    borderRadius: 8, border: 'none', cursor: 'pointer', marginBottom: 2,
                    borderLeft: active ? `3px solid ${C.tealDark}` : '3px solid transparent',
                    background: active ? C.navyElev : 'transparent',
                    color: active ? C.cream : C.textSecDark,
                    fontWeight: 500, fontSize: 14,
                    transition: 'all 0.15s ease',
                    textAlign: 'left',
                  }}
                  onMouseEnter={e => { if (!active) { e.currentTarget.style.background = C.navyMuted; e.currentTarget.style.color = C.cream } }}
                  onMouseLeave={e => { if (!active) { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = C.textSecDark } }}
                >
                  <Icon size={18} style={{ flexShrink: 0 }} />
                  {!sidebarCollapsed && <span style={{ whiteSpace: 'nowrap' }}>{label}</span>}
                </button>
              )
            })}
          </div>
        ))}
      </nav>

      {/* Bottom items */}
      <div style={{ padding: '8px 8px 12px', borderTop: `1px solid ${C.borderDark}` }}>
        <button
          onClick={() => router.push('/settings')}
          aria-label="Settings"
          style={{
            width: '100%', display: 'flex', alignItems: 'center',
            gap: 12, padding: pathname === '/settings' ? '10px 12px 10px 9px' : '10px 12px',
            borderRadius: 8, border: 'none', cursor: 'pointer', marginBottom: 2,
            borderLeft: pathname === '/settings' ? `3px solid ${C.tealDark}` : '3px solid transparent',
            background: pathname === '/settings' ? C.navyElev : 'transparent',
            color: pathname === '/settings' ? C.cream : C.textSecDark,
            fontWeight: 500, fontSize: 14, textAlign: 'left',
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
            border: 'none', cursor: 'pointer', borderLeft: '3px solid transparent',
            background: 'transparent', color: C.textSecDark,
            fontWeight: 500, fontSize: 14, textAlign: 'left',
            transition: 'all 0.15s ease',
          }}
          onMouseEnter={e => { e.currentTarget.style.background = C.navyMuted; e.currentTarget.style.color = C.cream }}
          onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = C.textSecDark }}
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
          border: `1px solid ${C.borderDark}`, background: C.navyMuted,
          color: C.textSecDark, cursor: 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 10,
        }}
      >
        {sidebarCollapsed ? <ChevronRight size={12} /> : <ChevronLeft size={12} />}
      </button>
    </aside>
  )
}
