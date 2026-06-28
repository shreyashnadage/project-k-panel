'use client'

import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { VOUCHER_COLORS } from '@/types/widgets'
import { Search, ChevronLeft, ChevronRight } from 'lucide-react'
import type { Voucher } from '@/types/widgets'

const PAGE_SIZE = 10

const VOUCHER_TYPES = ['All', 'Sales', 'Purchase', 'Receipt', 'Payment', 'Journal', 'Debit Note', 'Credit Note']

function TypeBadge({ type }: { type: string }) {
  const c = VOUCHER_COLORS[type] || { bg: '#1e293b', text: '#94a3b8', border: '#334155' }
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center',
      padding: '2px 10px', borderRadius: 20,
      fontSize: 12, fontWeight: 500,
      background: c.bg, color: c.text, border: `1px solid ${c.border}`,
      fontFamily: 'Inter, system-ui', whiteSpace: 'nowrap',
    }}>
      {type}
    </span>
  )
}

function formatDate(d: string) {
  try {
    return new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: '2-digit' })
  } catch { return d }
}

function formatAmount(a: string) {
  const n = parseFloat(a)
  if (isNaN(n)) return a
  return n.toLocaleString('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 })
}

interface Props { compact?: boolean }

export default function VouchersTableWidget({ compact }: Props) {
  const [apiPage, setApiPage] = useState(0)
  const [localPage, setLocalPage] = useState(0)
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('All')

  const { data, isLoading, error } = useQuery({
    queryKey: ['vouchers', apiPage],
    queryFn: () => api.getVouchers(apiPage * 50, 50),
    staleTime: 30_000,
    refetchInterval: compact ? undefined : 30_000,
  })

  const filtered: Voucher[] = useMemo(() => {
    if (!data?.data) return []
    return data.data.filter((v) => {
      const matchType = typeFilter === 'All' || v.type === typeFilter
      const q = search.toLowerCase()
      const matchSearch = !q || v.party.toLowerCase().includes(q) || v.voucher_number.toLowerCase().includes(q)
      return matchType && matchSearch
    })
  }, [data, search, typeFilter])

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE)
  const pageSlice = filtered.slice(localPage * PAGE_SIZE, (localPage + 1) * PAGE_SIZE)

  const showRows = compact ? filtered.slice(0, 5) : pageSlice

  if (error) {
    return (
      <div style={{ background: '#1e293b', border: '1px solid #ef4444', borderRadius: 12, padding: 20, color: '#f87171', fontSize: 14 }}>
        Failed to load vouchers.
      </div>
    )
  }

  return (
    <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 12, overflow: 'hidden' }}>
      {/* Header */}
      <div style={{ padding: '16px 20px', borderBottom: '1px solid #334155', display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
        <h3 style={{ fontFamily: 'Outfit, system-ui', fontWeight: 600, fontSize: 16, color: '#f1f5f9', margin: 0, flex: 1 }}>
          {compact ? 'Recent Vouchers' : 'Vouchers'}
        </h3>

        {!compact && (
          <>
            {/* Search */}
            <div style={{ position: 'relative' }}>
              <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: '#64748b' }} />
              <input
                type="text"
                placeholder="Search party / voucher..."
                value={search}
                onChange={(e) => { setSearch(e.target.value); setLocalPage(0) }}
                style={{
                  background: '#0f172a', border: '1px solid #334155', borderRadius: 8,
                  padding: '7px 12px 7px 32px', fontSize: 13, color: '#f1f5f9',
                  fontFamily: 'Inter, system-ui', outline: 'none', width: 220,
                }}
              />
            </div>

            {/* Type filter */}
            <select
              value={typeFilter}
              onChange={(e) => { setTypeFilter(e.target.value); setLocalPage(0) }}
              style={{
                background: '#0f172a', border: '1px solid #334155', borderRadius: 8,
                padding: '7px 12px', fontSize: 13, color: '#f1f5f9',
                fontFamily: 'Inter, system-ui', outline: 'none', cursor: 'pointer',
              }}
            >
              {VOUCHER_TYPES.map((t) => <option key={t}>{t}</option>)}
            </select>
          </>
        )}
      </div>

      {/* Table */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: '#0f172a' }}>
              {['#', 'Date', 'Party', 'Type', 'Amount'].map((h) => (
                <th key={h} style={{
                  padding: '10px 16px', textAlign: h === 'Amount' ? 'right' : 'left',
                  fontSize: 12, fontWeight: 600, color: '#64748b',
                  fontFamily: 'Inter, system-ui', borderBottom: '1px solid #334155',
                  whiteSpace: 'nowrap',
                }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {isLoading && Array.from({ length: compact ? 5 : PAGE_SIZE }).map((_, i) => (
              <tr key={i}>
                {Array.from({ length: 5 }).map((__, j) => (
                  <td key={j} style={{ padding: '12px 16px' }}>
                    <div className="skeleton" style={{ height: 14, width: j === 2 ? '80%' : '60%' }} />
                  </td>
                ))}
              </tr>
            ))}

            {!isLoading && showRows.length === 0 && (
              <tr>
                <td colSpan={5} style={{ padding: '40px', textAlign: 'center', color: '#64748b', fontSize: 14 }}>
                  {search || typeFilter !== 'All' ? 'No vouchers match your filter.' : 'No vouchers found.'}
                </td>
              </tr>
            )}

            {!isLoading && showRows.map((v, i) => (
              <tr
                key={v.id}
                style={{
                  borderBottom: '1px solid #1e3a3a',
                  transition: 'background 0.1s',
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = '#0f2f2f'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
              >
                <td style={{ padding: '12px 16px', fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: '#64748b' }}>
                  {v.voucher_number}
                </td>
                <td style={{ padding: '12px 16px', fontSize: 13, color: '#94a3b8', whiteSpace: 'nowrap' }}>
                  {formatDate(v.date)}
                </td>
                <td style={{ padding: '12px 16px', fontSize: 13, color: '#e2e8f0', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {v.party}
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <TypeBadge type={v.type} />
                </td>
                <td style={{ padding: '12px 16px', textAlign: 'right', fontFamily: 'JetBrains Mono, monospace', fontSize: 13, color: '#f1f5f9', whiteSpace: 'nowrap' }}>
                  {formatAmount(v.amount)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {!compact && !isLoading && filtered.length > PAGE_SIZE && (
        <div style={{
          padding: '12px 20px', borderTop: '1px solid #334155',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <span style={{ fontSize: 12, color: '#64748b', fontFamily: 'Inter, system-ui' }}>
            Showing {localPage * PAGE_SIZE + 1}–{Math.min((localPage + 1) * PAGE_SIZE, filtered.length)} of {filtered.length}
          </span>
          <div style={{ display: 'flex', gap: 8 }}>
            <button
              onClick={() => setLocalPage(p => Math.max(0, p - 1))}
              disabled={localPage === 0}
              style={{
                background: '#0f172a', border: '1px solid #334155', borderRadius: 6,
                padding: '5px 10px', color: localPage === 0 ? '#475569' : '#94a3b8',
                cursor: localPage === 0 ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center',
              }}
            >
              <ChevronLeft size={14} />
            </button>
            <button
              onClick={() => setLocalPage(p => Math.min(totalPages - 1, p + 1))}
              disabled={localPage >= totalPages - 1}
              style={{
                background: '#0f172a', border: '1px solid #334155', borderRadius: 6,
                padding: '5px 10px', color: localPage >= totalPages - 1 ? '#475569' : '#94a3b8',
                cursor: localPage >= totalPages - 1 ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center',
              }}
            >
              <ChevronRight size={14} />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
