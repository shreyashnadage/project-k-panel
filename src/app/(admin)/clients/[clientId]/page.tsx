'use client'

import { useClientContext } from '@/lib/client-context'
import { useQuery } from '@tanstack/react-query'
import { Database, FileText, Clock, Activity, AreaChart as AreaChartIcon } from 'lucide-react'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer,
} from 'recharts'

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

function KPICard({ label, value, icon, accentColor, sub, loading }: {
  label: string; value: string; icon: React.ReactNode; accentColor: string; sub?: string; loading?: boolean
}) {
  if (loading) {
    return (
      <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 12, padding: 24 }}>
        <div className="skeleton" style={{ height: 16, width: '60%', marginBottom: 16 }} />
        <div className="skeleton" style={{ height: 40, width: '75%' }} />
      </div>
    )
  }
  return (
    <div
      style={{
        background: '#1e293b', border: '1px solid #334155', borderRadius: 12,
        padding: 24, transition: 'transform 0.2s ease, box-shadow 0.2s ease',
      }}
      onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 8px 24px rgba(0,0,0,0.3)' }}
      onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = 'none' }}
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

function formatINR(n: number) {
  if (n >= 10_00_000) return `₹${(n / 10_00_000).toFixed(1)}L`
  if (n >= 1_000) return `₹${(n / 1_000).toFixed(0)}K`
  return `₹${n}`
}

function formatMonth(m: string) {
  const [y, mo] = m.split('-')
  const label = new Date(parseInt(y), parseInt(mo) - 1, 1).toLocaleString('en-IN', { month: 'short' })
  return `${label} '${y.slice(2)}`
}

export default function ClientDashboardPage() {
  const { clientId, companyName, clientApi, error: ctxError } = useClientContext()

  const { data: kpis, isLoading: kpiLoading } = useQuery({
    queryKey: ['kpis', clientId],
    queryFn: () => clientApi!.getKPIs(),
    enabled: !!clientApi,
    staleTime: 60_000,
    refetchInterval: 60_000,
  })

  const { data: cashFlow, isLoading: cfLoading } = useQuery({
    queryKey: ['cash_flow', clientId],
    queryFn: () => clientApi!.getCashFlow('monthly', 6),
    enabled: !!clientApi,
    staleTime: 5 * 60_000,
  })

  const chartData = (cashFlow ?? []).map(d => ({ month: formatMonth(d.month), amount: d.amount }))

  if (ctxError) {
    return (
      <div className="page-enter" style={{ textAlign: 'center', padding: 64 }}>
        <p style={{ color: '#f59e0b', fontSize: 16 }}>{ctxError}</p>
        <p style={{ color: '#64748b', fontSize: 14, marginTop: 8 }}>This client may not have any registered devices yet.</p>
      </div>
    )
  }

  return (
    <div className="page-enter" style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div>
        <h2 style={{ fontFamily: 'Outfit, system-ui', fontWeight: 700, fontSize: 28, color: '#f1f5f9', margin: 0 }}>
          {companyName}
        </h2>
        <p style={{ color: '#64748b', fontSize: 14, marginTop: 4 }}>
          Client dashboard — sync metrics and data overview
        </p>
      </div>

      {/* KPI Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
        <KPICard label="Total Ledgers" value={kpiLoading ? '—' : (kpis?.total_ledgers ?? 0).toLocaleString('en-IN')} icon={<Database size={18} />} accentColor="#14b8a6" loading={kpiLoading} />
        <KPICard label="Total Vouchers" value={kpiLoading ? '—' : (kpis?.total_vouchers ?? 0).toLocaleString('en-IN')} icon={<FileText size={18} />} accentColor="#f59e0b" loading={kpiLoading} />
        <KPICard label="Last Sync" value={kpiLoading ? '—' : formatRelativeTime(kpis?.last_sync ?? null)} icon={<Clock size={18} />} accentColor="#3b82f6" loading={kpiLoading} />
        <KPICard
          label="Sync Health"
          value={kpiLoading ? '—' : kpis?.sync_health === 'healthy' ? 'Healthy' : kpis?.sync_health === 'warning' ? 'Warning' : 'Error'}
          icon={<Activity size={18} />}
          accentColor={kpis?.sync_health === 'healthy' ? '#22c55e' : kpis?.sync_health === 'warning' ? '#f59e0b' : '#ef4444'}
          loading={kpiLoading}
          sub={kpiLoading ? undefined : `Last sync: ${formatRelativeTime(kpis?.last_sync ?? null)}`}
        />
      </div>

      {/* Cash Flow */}
      <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 12, padding: 24 }}>
        <h3 style={{ fontFamily: 'Outfit, system-ui', fontWeight: 600, fontSize: 16, color: '#f1f5f9', margin: '0 0 4px' }}>
          Cash Flow
        </h3>
        <p style={{ fontSize: 12, color: '#64748b', marginTop: 0, marginBottom: 20 }}>Monthly transaction volume (last 6 months)</p>

        {cfLoading ? (
          <div className="skeleton" style={{ height: 280, borderRadius: 8 }} />
        ) : chartData.length === 0 ? (
          <div style={{ height: 280, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b' }}>
            No cash flow data available.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="tealGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#14b8a6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#14b8a6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e3a3a" vertical={false} />
              <XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tickFormatter={formatINR} tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} width={60} />
              <Tooltip
                contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8, fontSize: 13 }}
                labelStyle={{ color: '#94a3b8' }}
                itemStyle={{ color: '#14b8a6' }}
                formatter={(v) => [Number(v).toLocaleString('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }), 'Amount']}
              />
              <Area type="monotone" dataKey="amount" stroke="#14b8a6" strokeWidth={2} fill="url(#tealGrad)" dot={{ fill: '#14b8a6', r: 4, strokeWidth: 0 }} />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}
