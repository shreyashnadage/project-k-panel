'use client'

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Database, FileText, Clock, Activity } from 'lucide-react'

function formatIndianNumber(n: number) {
  return n.toLocaleString('en-IN')
}

function formatRelativeTime(iso: string | null): string {
  if (!iso) return 'Never'
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins} min ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

interface KPICardProps {
  label: string
  value: string
  icon: React.ReactNode
  accentColor: string
  sub?: string
  loading?: boolean
}

function KPICard({ label, value, icon, accentColor, sub, loading }: KPICardProps) {
  if (loading) {
    return (
      <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 12, padding: 24 }}>
        <div className="skeleton" style={{ height: 16, width: '60%', marginBottom: 16 }} />
        <div className="skeleton" style={{ height: 40, width: '75%', marginBottom: 8 }} />
        <div className="skeleton" style={{ height: 12, width: '40%' }} />
      </div>
    )
  }
  return (
    <div
      style={{
        background: '#1e293b', border: '1px solid #334155', borderRadius: 12,
        padding: 24, transition: 'transform 0.2s ease, box-shadow 0.2s ease',
      }}
      onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 8px 24px rgba(0,0,0,0.3)' }}
      onMouseLeave={(e) => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = 'none' }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
        <div style={{
          width: 36, height: 36, borderRadius: 8, background: `${accentColor}20`,
          display: 'flex', alignItems: 'center', justifyContent: 'center', color: accentColor,
        }}>
          {icon}
        </div>
        <span style={{ fontFamily: 'Inter, system-ui', fontSize: 13, fontWeight: 500, color: '#94a3b8' }}>{label}</span>
      </div>
      <div style={{ fontFamily: 'Outfit, system-ui', fontWeight: 800, fontSize: 36, lineHeight: 1, color: '#f1f5f9', marginBottom: 6 }}>
        {value}
      </div>
      {sub && <div style={{ fontSize: 12, color: '#64748b', fontFamily: 'Inter, system-ui' }}>{sub}</div>}
    </div>
  )
}

function SyncHealthCard({ health, lastSync, loading }: { health?: string; lastSync?: string | null; loading: boolean }) {
  if (loading) {
    return (
      <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 12, padding: 24 }}>
        <div className="skeleton" style={{ height: 16, width: '60%', marginBottom: 16 }} />
        <div className="skeleton" style={{ height: 32, width: '80%' }} />
      </div>
    )
  }
  const dotColor    = health === 'healthy' ? '#22c55e' : health === 'warning' ? '#f59e0b' : '#ef4444'
  const dotCls      = health === 'healthy' ? 'sync-dot--healthy' : health === 'warning' ? 'sync-dot--warning' : ''
  const statusLabel = health === 'healthy' ? 'All systems go' : health === 'warning' ? 'Needs attention' : 'Check agent'

  return (
    <div
      style={{
        background: '#1e293b', border: '1px solid #334155', borderRadius: 12,
        padding: 24, transition: 'transform 0.2s ease, box-shadow 0.2s ease',
      }}
      onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 8px 24px rgba(0,0,0,0.3)' }}
      onMouseLeave={(e) => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = 'none' }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
        <div style={{ width: 36, height: 36, borderRadius: 8, background: `${dotColor}20`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Activity size={18} color={dotColor} />
        </div>
        <span style={{ fontFamily: 'Inter, system-ui', fontSize: 13, fontWeight: 500, color: '#94a3b8' }}>Sync Health</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
        <span className={dotCls} style={{ width: 10, height: 10, borderRadius: '50%', background: dotColor, display: 'inline-block', flexShrink: 0 }} />
        <span style={{ fontFamily: 'Outfit, system-ui', fontWeight: 700, fontSize: 22, color: dotColor }}>{statusLabel}</span>
      </div>
      <div style={{ fontSize: 12, color: '#64748b', fontFamily: 'Inter, system-ui' }}>
        Last sync: {formatRelativeTime(lastSync ?? null)}
      </div>
    </div>
  )
}

export default function KPIWidget() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['kpis'],
    queryFn: api.getKPIs,
    staleTime: 60_000,
    refetchInterval: 60_000,
  })

  if (error) {
    return (
      <div style={{ background: '#1e293b', border: '1px solid #ef4444', borderRadius: 12, padding: 20, color: '#f87171', fontSize: 14 }}>
        Unable to fetch KPI data — check API connection.
      </div>
    )
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
      <KPICard label="Total Ledgers"  value={!data ? '—' : data.total_ledgers.toLocaleString('en-IN')}  icon={<Database size={18} />}  accentColor="#14b8a6" loading={isLoading} />
      <KPICard label="Total Vouchers" value={!data ? '—' : data.total_vouchers.toLocaleString('en-IN')} icon={<FileText size={18} />}  accentColor="#f59e0b" loading={isLoading} />
      <KPICard label="Last Sync"      value={!data ? '—' : formatRelativeTime(data.last_sync)}          icon={<Clock size={18} />}     accentColor="#3b82f6" loading={isLoading} />
      <SyncHealthCard health={data?.sync_health} lastSync={data?.last_sync} loading={isLoading} />
    </div>
  )
}
