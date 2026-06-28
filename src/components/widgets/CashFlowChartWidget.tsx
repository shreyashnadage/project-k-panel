'use client'

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer,
} from 'recharts'
import type { CashFlowData } from '@/types/widgets'

function formatINR(n: number) {
  if (n >= 10_00_000) return `₹${(n / 10_00_000).toFixed(1)}L`
  if (n >= 1_000) return `₹${(n / 1_000).toFixed(0)}K`
  return `₹${n}`
}

function formatMonth(m: string) {
  const [y, mo] = m.split('-')
  const label = new Date(parseInt(y), parseInt(mo) - 1, 1)
    .toLocaleString('en-IN', { month: 'short' })
  return `${label} '${y.slice(2)}`
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: '#0f172a', border: '1px solid #334155', borderRadius: 8,
      padding: '10px 14px', fontSize: 13, fontFamily: 'Inter, system-ui',
    }}>
      <div style={{ color: '#94a3b8', marginBottom: 4 }}>{label}</div>
      <div style={{ color: '#14b8a6', fontWeight: 600 }}>
        {payload[0].value.toLocaleString('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })}
      </div>
    </div>
  )
}

export default function CashFlowChartWidget() {
  const { data, isLoading, error } = useQuery<CashFlowData[]>({
    queryKey: ['cash_flow'],
    queryFn: () => api.getCashFlow('monthly', 6),
    staleTime: 5 * 60_000,
    refetchInterval: 60_000,
  })

  const chartData = (data ?? []).map((d) => ({
    month: formatMonth(d.month),
    amount: d.amount,
  }))

  return (
    <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 12, padding: 24 }}>
      <div style={{ marginBottom: 20 }}>
        <h3 style={{ fontFamily: 'Outfit, system-ui', fontWeight: 600, fontSize: 16, color: '#f1f5f9', margin: 0 }}>
          Cash Flow
        </h3>
        <p style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>Monthly transaction volume (last 6 months)</p>
      </div>

      {isLoading && (
        <div style={{ height: 280, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div className="skeleton" style={{ width: '100%', height: 280, borderRadius: 8 }} />
        </div>
      )}

      {error && (
        <div style={{ height: 280, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#f87171', fontSize: 14 }}>
          Failed to load chart data.
        </div>
      )}

      {!isLoading && !error && (
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="tealGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#14b8a6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#14b8a6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e3a3a" vertical={false} />
            <XAxis
              dataKey="month"
              tick={{ fill: '#64748b', fontSize: 12, fontFamily: 'Inter, system-ui' }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tickFormatter={formatINR}
              tick={{ fill: '#64748b', fontSize: 12, fontFamily: 'JetBrains Mono, monospace' }}
              axisLine={false}
              tickLine={false}
              width={60}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#334155', strokeWidth: 1 }} />
            <Area
              type="monotone"
              dataKey="amount"
              stroke="#14b8a6"
              strokeWidth={2}
              fill="url(#tealGrad)"
              dot={{ fill: '#14b8a6', r: 4, strokeWidth: 0 }}
              activeDot={{ r: 6, fill: '#0d9488' }}
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
