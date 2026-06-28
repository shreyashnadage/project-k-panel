'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Card } from '@/components/ui/card'
import { AlertCircle } from 'lucide-react'

export default function VouchersTableWidget() {
  const [page, setPage] = useState(0)
  const pageSize = 10

  const { data, isLoading, error } = useQuery({
    queryKey: ['vouchers', page],
    queryFn: () => api.getVouchers(page * pageSize, pageSize),
    refetchInterval: 5000,
  })

  if (isLoading) {
    return (
      <Card className="bg-slate-900/50 border-slate-800 p-6">
        <div className="space-y-3 animate-pulse">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-12 bg-slate-700 rounded" />
          ))}
        </div>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="bg-slate-900/50 border-red-800/50 p-6">
        <div className="flex items-center gap-2 text-red-400">
          <AlertCircle size={16} />
          <span className="text-sm">Failed to load vouchers</span>
        </div>
      </Card>
    )
  }

  const totalPages = Math.ceil((data?.total || 0) / pageSize)

  return (
    <Card className="bg-slate-900/50 backdrop-blur border-slate-800 p-6">
      <h3 className="text-slate-50 font-semibold mb-4">Recent Vouchers</h3>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700">
              <th className="text-left px-4 py-2 text-slate-400 font-medium">Date</th>
              <th className="text-left px-4 py-2 text-slate-400 font-medium">Voucher</th>
              <th className="text-left px-4 py-2 text-slate-400 font-medium">Party</th>
              <th className="text-left px-4 py-2 text-slate-400 font-medium">Type</th>
              <th className="text-right px-4 py-2 text-slate-400 font-medium">Amount</th>
            </tr>
          </thead>
          <tbody>
            {data?.data?.map((voucher) => (
              <tr key={voucher.id} className="border-b border-slate-700/50 hover:bg-slate-800/30">
                <td className="px-4 py-3 text-slate-300">{voucher.date}</td>
                <td className="px-4 py-3 text-slate-300 font-mono">{voucher.voucher_number}</td>
                <td className="px-4 py-3 text-slate-300">{voucher.party}</td>
                <td className="px-4 py-3">
                  <span
                    className={`px-2 py-1 rounded text-xs font-medium ${
                      voucher.type === 'Sales'
                        ? 'bg-green-900/30 text-green-400'
                        : voucher.type === 'Purchase'
                          ? 'bg-red-900/30 text-red-400'
                          : 'bg-slate-700/30 text-slate-400'
                    }`}
                  >
                    {voucher.type}
                  </span>
                </td>
                <td className="text-right px-4 py-3 text-slate-300">
                  ₹{parseFloat(voucher.amount).toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex justify-between items-center mt-4 pt-4 border-t border-slate-700">
        <button
          onClick={() => setPage(Math.max(0, page - 1))}
          disabled={page === 0}
          className="px-3 py-2 text-sm rounded bg-slate-700 text-slate-300 hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed transition"
        >
          Previous
        </button>
        <span className="text-xs text-slate-400">
          Page {page + 1} of {totalPages || 1}
        </span>
        <button
          onClick={() => setPage(page + 1)}
          disabled={(page + 1) * pageSize >= (data?.total || 0)}
          className="px-3 py-2 text-sm rounded bg-slate-700 text-slate-300 hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed transition"
        >
          Next
        </button>
      </div>
    </Card>
  )
}
