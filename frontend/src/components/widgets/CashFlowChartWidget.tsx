'use client'

import dynamic from 'next/dynamic'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Card } from '@/components/ui/card'
import { AlertCircle } from 'lucide-react'

const AreaChart = dynamic(() => import('recharts').then((mod) => mod.AreaChart), {
  ssr: false,
  loading: () => <div className="h-64 bg-slate-700 animate-pulse rounded" />,
})

const Area = dynamic(() => import('recharts').then((mod) => mod.Area), {
  ssr: false,
})

const XAxis = dynamic(() => import('recharts').then((mod) => mod.XAxis), {
  ssr: false,
})

const YAxis = dynamic(() => import('recharts').then((mod) => mod.YAxis), {
  ssr: false,
})

const CartesianGrid = dynamic(() => import('recharts').then((mod) => mod.CartesianGrid), {
  ssr: false,
})

const Tooltip = dynamic(() => import('recharts').then((mod) => mod.Tooltip), {
  ssr: false,
})

const ResponsiveContainer = dynamic(() => import('recharts').then((mod) => mod.ResponsiveContainer), {
  ssr: false,
})

export default function CashFlowChartWidget() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['cash_flow'],
    queryFn: () => api.getCashFlow(),
    refetchInterval: 60000,
  })

  if (isLoading) {
    return (
      <Card className="bg-slate-900/50 border-slate-800 p-6">
        <div className="h-64 bg-slate-700 animate-pulse rounded" />
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="bg-slate-900/50 border-red-800/50 p-6">
        <div className="flex items-center gap-2 text-red-400">
          <AlertCircle size={16} />
          <span className="text-sm">Failed to load chart</span>
        </div>
      </Card>
    )
  }

  return (
    <Card className="bg-slate-900/50 backdrop-blur border-slate-800 p-6">
      <h3 className="text-slate-50 font-semibold mb-4">Cash Flow Trend</h3>

      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data || []} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="colorCash" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#0d9488" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#0d9488" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="month" stroke="#94a3b8" />
          <YAxis stroke="#94a3b8" />
          <Tooltip
            contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
            formatter={(value: any) => `₹${(value as number).toLocaleString('en-IN')}`}
          />
          <Area
            type="monotone"
            dataKey="amount"
            stroke="#0d9488"
            fillOpacity={1}
            fill="url(#colorCash)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </Card>
  )
}
