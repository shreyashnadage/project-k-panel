'use client'

import { useState } from 'react'
import { useDashboardStore } from '@/lib/store'
import type { PageType } from '@/types/widgets'
import {
  LayoutDashboard, FileText, BookOpen, Monitor, Radio,
  Settings, LogOut, ChevronLeft, ChevronRight, Menu,
} from 'lucide-react'
import dynamic from 'next/dynamic'

const KPIWidget         = dynamic(() => import('./widgets/KPIWidget'),          { ssr: false })
const CashFlowChart     = dynamic(() => import('./widgets/CashFlowChartWidget'), { ssr: false })
const VouchersTable     = dynamic(() => import('./widgets/VouchersTableWidget'), { ssr: false })
const DevicesPage       = dynamic(() => import('./pages/DevicesPage'),           { ssr: false })
const SyncHistoryPage   = dynamic(() => import('./pages/SyncHistoryPage'),       { ssr: false })

// ─── Nav definition ───────────────────────────────────────────
const NAV: { id: PageType; label: string; Icon: React.ElementType }[] = [
  { id: 'dashboard',    label: 'Dashboard',    Icon: LayoutDashboard },
  { id: 'vouchers',     label: 'Vouchers',     Icon: FileText },
  { id: 'ledgers',      label: 'Ledgers',      Icon: BookOpen },
  { id: 'devices',      label: 'Devices',      Icon: Monitor },
  { id: 'sync-history', label: 'Sync History', Icon: Radio },
]

// ─── Helpers ──────────────────────────────────────────────────
function SyncDot({ health }: { health: 'healthy' | 'warning' | 'error' }) {
  const color = health === 'healthy' ? '#22c55e' : health === 'warning' ? '#f59e0b' : '#ef4444'
  const cls   = health === 'healthy' ? 'sync-dot--healthy' : health === 'warning' ? 'sync-dot--warning' : ''
  return (
    <span
      className={cls}
      style={{ width: 10, height: 10, borderRadius: '50%', display: 'inline-block', background: color }}
      aria-label={`Sync ${health}`}
    />
  )
}

// ─── Sidebar ──────────────────────────────────────────────────
function Sidebar() {
  const { currentPage, setCurrentPage, sidebarCollapsed, setSidebarCollapsed } = useDashboardStore()

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

      {/* Nav items */}
      <nav style={{ flex: 1, padding: '12px 8px', overflowY: 'auto' }}>
        {NAV.map(({ id, label, Icon }) => {
          const active = currentPage === id
          return (
            <button
              key={id}
              onClick={() => setCurrentPage(id)}
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
              onMouseEnter={(e) => { if (!active) e.currentTarget.style.background = '#1e293b'; e.currentTarget.style.color = '#f1f5f9' }}
              onMouseLeave={(e) => { if (!active) { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = '#94a3b8' } }}
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
          onClick={() => setCurrentPage('settings')}
          aria-label="Settings"
          style={{
            width: '100%', display: 'flex', alignItems: 'center',
            gap: 12, padding: '10px 12px', borderRadius: 8,
            border: 'none', cursor: 'pointer', marginBottom: 2,
            background: currentPage === 'settings' ? '#14b8a6' : 'transparent',
            color: currentPage === 'settings' ? '#fff' : '#94a3b8',
            fontFamily: 'Inter, system-ui', fontWeight: 500, fontSize: 14, textAlign: 'left',
            transition: 'all 0.15s ease',
          }}
        >
          <Settings size={18} style={{ flexShrink: 0 }} />
          {!sidebarCollapsed && <span>Settings</span>}
        </button>
        <button
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

// ─── Page placeholders ────────────────────────────────────────
function EmptyState({ icon, title, message }: { icon: React.ReactNode; title: string; message: string }) {
  return (
    <div style={{ textAlign: 'center', padding: '64px 32px' }}>
      <div style={{ color: '#475569', marginBottom: 16, display: 'flex', justifyContent: 'center' }}>{icon}</div>
      <h3 style={{ fontFamily: 'Outfit, system-ui', fontWeight: 600, fontSize: 18, color: '#94a3b8', marginBottom: 8 }}>{title}</h3>
      <p style={{ color: '#64748b', fontSize: 14 }}>{message}</p>
    </div>
  )
}

// ─── Dashboard page ───────────────────────────────────────────
function DashboardPage() {
  return (
    <div className="page-enter" style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div>
        <h2 style={{ fontFamily: 'Outfit, system-ui', fontWeight: 700, fontSize: 28, color: '#f1f5f9', margin: 0 }}>
          Dashboard
        </h2>
        <p style={{ color: '#64748b', fontSize: 14, marginTop: 4 }}>
          Real-time sync metrics from your Tally installation
        </p>
      </div>

      {/* KPI row */}
      <KPIWidget />

      {/* Cash flow chart */}
      <CashFlowChart />

      {/* Recent vouchers */}
      <VouchersTable compact />
    </div>
  )
}

// ─── Vouchers full page ───────────────────────────────────────
function VouchersPage() {
  return (
    <div className="page-enter" style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div>
        <h2 style={{ fontFamily: 'Outfit, system-ui', fontWeight: 700, fontSize: 28, color: '#f1f5f9', margin: 0 }}>
          Vouchers
        </h2>
        <p style={{ color: '#64748b', fontSize: 14, marginTop: 4 }}>
          All synced vouchers from TallyPrime
        </p>
      </div>
      <VouchersTable />
    </div>
  )
}

// ─── Ledgers stub page ────────────────────────────────────────
function LedgersPage() {
  return (
    <div className="page-enter">
      <h2 style={{ fontFamily: 'Outfit, system-ui', fontWeight: 700, fontSize: 28, color: '#f1f5f9', margin: '0 0 24px' }}>
        Ledgers
      </h2>
      <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 12 }}>
        <EmptyState
          icon={<BookOpen size={48} />}
          title="No ledgers found"
          message="They'll appear here once your agent syncs."
        />
      </div>
    </div>
  )
}

// ─── Settings stub ────────────────────────────────────────────
function SettingsPage() {
  return (
    <div className="page-enter">
      <h2 style={{ fontFamily: 'Outfit, system-ui', fontWeight: 700, fontSize: 28, color: '#f1f5f9', margin: '0 0 24px' }}>
        Settings
      </h2>
      <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 12 }}>
        <EmptyState
          icon={<Settings size={48} />}
          title="Settings"
          message="Account and system configuration coming soon."
        />
      </div>
    </div>
  )
}

// ─── Root component ───────────────────────────────────────────
export default function Dashboard() {
  const { currentPage } = useDashboardStore()
  const [mobileOpen, setMobileOpen] = useState(false)

  const pageMap: Record<PageType, React.ReactNode> = {
    dashboard:     <DashboardPage />,
    vouchers:      <VouchersPage />,
    ledgers:       <LedgersPage />,
    devices:       <DevicesPage />,
    'sync-history': <SyncHistoryPage />,
    settings:      <SettingsPage />,
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#0f172a' }}>
      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 40 }}
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar — hidden on mobile unless open */}
      <div style={{ display: 'flex' }} className="hidden lg:flex">
        <Sidebar />
      </div>

      {/* Main */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        {/* Top header (mobile) */}
        <header style={{
          display: 'none',
          alignItems: 'center',
          gap: 12,
          padding: '12px 16px',
          background: '#0f172a',
          borderBottom: '1px solid #1e293b',
          position: 'sticky', top: 0, zIndex: 30,
        }} className="flex lg:hidden">
          <button onClick={() => setMobileOpen(true)} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
            <Menu size={22} />
          </button>
          <span style={{ fontFamily: 'Outfit, system-ui', fontWeight: 700, fontSize: 16, color: '#f1f5f9' }}>Tally Sync</span>
        </header>

        <main style={{ flex: 1, padding: 24, maxWidth: 1280, width: '100%' }}>
          {pageMap[currentPage]}
        </main>
      </div>
    </div>
  )
}
