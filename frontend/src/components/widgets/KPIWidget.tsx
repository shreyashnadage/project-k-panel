'use client'

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Card } from '@/components/ui/card'
import { AlertCircle } from 'lucide-react'

export default function KPIWidget() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['kpi_records'],
    queryFn: () => api.getKPIs(),
    refetchInterval: 30000,
  })

  if (isLoading) {
    return (
      <Card className="bg-slate-900/50 border-slate-800 p-6">
        <div className="space-y-4 animate-pulse">
          <div className="h-4 bg-slate-700 rounded w-3/4" />
          <div className="h-8 bg-slate-700 rounded w-1/2" />
          <div className="h-4 bg-slate-700 rounded w-3/4" />
          <div className="h-8 bg-slate-700 rounded w-1/2" />
        </div>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="bg-slate-900/50 border-red-800/50 p-6">
        <div className="flex items-center gap-2 text-red-400">
          <AlertCircle size={16} />
          <span className="text-sm">Failed to load KPIs</span>
        </div>
      </Card>
    )
  }

  return (
    <Card className="bg-slate-900/50 backdrop-blur border-slate-800 hover:border-slate-700 transition p-6">
      <h3 className="text-slate-50 font-semibold mb-4">Sync Records</h3>

      <div className="space-y-6">
        <div>
          <p className="text-sm text-slate-400 mb-1">Total Ledgers</p>
          <p className="text-3xl font-bold text-teal-400">
            {data?.total_ledgers?.toLocaleString() || '0'}
          </p>
        </div>

        <div>
          <p className="text-sm text-slate-400 mb-1">Total Vouchers</p>
          <p className="text-3xl font-bold text-teal-400">
            {data?.total_vouchers?.toLocaleString() || '0'}
          </p>
        </div>

        <div className="pt-4 border-t border-slate-700">
          <p className="text-xs text-slate-400 mb-2">
            Last sync: {data?.last_sync ? new Date(data.last_sync).toLocaleDateString() : 'Never'}
          </p>
          <div className="flex items-center gap-2">
            <div
              className={`w-3 h-3 rounded-full ${
                data?.sync_health === 'healthy'
                  ? 'bg-green-500'
                  : data?.sync_health === 'warning'
                    ? 'bg-yellow-500'
                    : 'bg-red-500'
              }`}
            />
            <span className="text-xs text-slate-400 capitalize">
              {data?.sync_health || 'unknown'}
            </span>
          </div>
        </div>
      </div>
    </Card>
  )
}
