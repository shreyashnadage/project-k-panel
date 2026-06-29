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
      background: '#0d1b2a', border: '1px solid #2d3e50', borderRadius: 10,
      padding: '10px 14px', fontSize: 13,
    }}>
      <div style={{ color: '#a8b8c8', marginBottom: 4 }}>{label}</div>
      <div style={{ color: '#3db8a9', fontWeight: 600 }}>
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
    <div style={{ background: '#1b263b', border: '1px solid #2d3e50', borderRadius: 14, padding: 24 }}>
      <div style={{ marginBottom: 20 }}>
        <h3 style={{ fontWeight: 600, fontSize: 16, color: '#f5f0e8', margin: 0 }}>
          Cash Flow
        </h3>
        <p style={{ fontSize: 12, color: '#a8b8c8', marginTop: 2 }}>Monthly transaction volume (last 6 months)</p>
      </div>

      {isLoading && (
        <div style={{ height: 280, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div className="skeleton" style={{ width: '100%', height: 280, borderRadius: 10 }} />
        </div>
      )}

      {error && (
        <div style={{ height: 280, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#c45c4a', fontSize: 14 }}>
          Failed to load chart data.
        </div>
      )}

      {!isLoading && !error && (
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="tealGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#3db8a9" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#3db8a9" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#2d3e50" vertical={false} />
            <XAxis
              dataKey="month"
              tick={{ fill: '#a8b8c8', fontSize: 12,  }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tickFormatter={formatINR}
              tick={{ fill: '#a8b8c8', fontSize: 12, fontFamily: 'var(--font-mono)' }}
              axisLine={false}
              tickLine={false}
              width={60}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#2d3e50', strokeWidth: 1 }} />
            <Area
              type="monotone"
              dataKey="amount"
              stroke="#3db8a9"
              strokeWidth={2}
              fill="url(#tealGrad)"
              dot={{ fill: '#3db8a9', r: 4, strokeWidth: 0 }}
              activeDot={{ r: 6, fill: '#2a9d8f' }}
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
