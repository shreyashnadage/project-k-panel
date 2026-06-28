'use client'

import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useClientContext } from '@/lib/client-context'
import { useClientApi } from '@/hooks/useClientApi'
import { VOUCHER_COLORS } from '@/types/widgets'
import type { Voucher } from '@/types/widgets'
import { Search, ChevronLeft, ChevronRight, Download } from 'lucide-react'

const PAGE_SIZE = 10
const VOUCHER_TYPES = ['All', 'Sales', 'Purchase', 'Receipt', 'Payment', 'Journal', 'Debit Note', 'Credit Note']

function TypeBadge({ type }: { type: string }) {
  const c = VOUCHER_COLORS[type] || { bg: '#1e293b', text: '#94a3b8', border: '#334155' }
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', padding: '2px 10px', borderRadius: 20,
      fontSize: 12, fontWeight: 500, background: c.bg, color: c.text, border: `1px solid ${c.border}`,
      fontFamily: 'Inter, system-ui', whiteSpace: 'nowrap',
    }}>
      {type}
    </span>
  )
}

function formatDate(d: string) {
  try { return new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: '2-digit' }) }
  catch { return d }
}

function formatAmount(a: string) {
  const n = parseFloat(a)
  if (isNaN(n)) return a
  return n.toLocaleString('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 })
}

function downloadCSV(rows: Voucher[], filename: string) {
  const header = 'Voucher Number,Date,Party,Type,Amount'
  const csv = [header, ...rows.map(v => `"${v.voucher_number}","${v.date}","${v.party.replace(/"/g, '""')}","${v.type}","${v.amount}"`)].join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = filename; a.click()
  URL.revokeObjectURL(url)
}

export default function VouchersPage() {
  const { clientId, companyName } = useClientContext()
  const clientApi = useClientApi()
  const [apiPage, setApiPage] = useState(0)
  const [localPage, setLocalPage] = useState(0)
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('All')

  const { data, isLoading, error } = useQuery({
    queryKey: ['vouchers', clientId, apiPage],
    queryFn: () => clientApi.getVouchers(apiPage * 50, 50),
    staleTime: 30_000,
  })

  const filtered: Voucher[] = useMemo(() => {
    if (!data?.data) return []
    return data.data.filter(v => {
      const matchType = typeFilter === 'All' || v.type === typeFilter
      const q = search.toLowerCase()
      const matchSearch = !q || v.party.toLowerCase().includes(q) || v.voucher_number.toLowerCase().includes(q)
      return matchType && matchSearch
    })
  }, [data, search, typeFilter])

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE)
  const pageSlice = filtered.slice(localPage * PAGE_SIZE, (localPage + 1) * PAGE_SIZE)

  if (error) {
    return <div style={{ background: '#1e293b', border: '1px solid #ef4444', borderRadius: 12, padding: 20, color: '#f87171' }}>Failed to load vouchers.</div>
  }

  return (
    <div className="page-enter" style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div>
        <h2 style={{ fontFamily: 'Outfit, system-ui', fontWeight: 700, fontSize: 28, color: '#f1f5f9', margin: 0 }}>Vouchers</h2>
        <p style={{ color: '#64748b', fontSize: 14, marginTop: 4 }}>All synced vouchers for {companyName}</p>
      </div>

      <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 12, overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #334155', display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <h3 style={{ fontFamily: 'Outfit, system-ui', fontWeight: 600, fontSize: 16, color: '#f1f5f9', margin: 0, flex: 1 }}>Vouchers</h3>
          <div style={{ position: 'relative' }}>
            <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: '#64748b' }} />
            <input type="text" placeholder="Search party / voucher..." value={search}
              onChange={e => { setSearch(e.target.value); setLocalPage(0) }}
              style={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8, padding: '7px 12px 7px 32px', fontSize: 13, color: '#f1f5f9', fontFamily: 'Inter, system-ui', outline: 'none', width: 220 }}
            />
          </div>
          <select value={typeFilter} onChange={e => { setTypeFilter(e.target.value); setLocalPage(0) }}
            style={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8, padding: '7px 12px', fontSize: 13, color: '#f1f5f9', fontFamily: 'Inter, system-ui', outline: 'none', cursor: 'pointer' }}>
            {VOUCHER_TYPES.map(t => <option key={t}>{t}</option>)}
          </select>
          <button onClick={() => downloadCSV(filtered, `vouchers-${companyName}.csv`)}
            style={{ padding: '7px 12px', borderRadius: 8, border: '1px solid #334155', background: '#0f172a', color: '#94a3b8', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, fontFamily: 'Inter, system-ui' }}>
            <Download size={14} /> Export
          </button>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: '#0f172a' }}>
                {['#', 'Date', 'Party', 'Type', 'Amount'].map(h => (
                  <th key={h} style={{ padding: '10px 16px', textAlign: h === 'Amount' ? 'right' : 'left', fontSize: 12, fontWeight: 600, color: '#64748b', fontFamily: 'Inter, system-ui', borderBottom: '1px solid #334155', whiteSpace: 'nowrap' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {isLoading && Array.from({ length: PAGE_SIZE }).map((_, i) => (
                <tr key={i}>{Array.from({ length: 5 }).map((__, j) => <td key={j} style={{ padding: '12px 16px' }}><div className="skeleton" style={{ height: 14, width: j === 2 ? '80%' : '60%' }} /></td>)}</tr>
              ))}
              {!isLoading && pageSlice.length === 0 && (
                <tr><td colSpan={5} style={{ padding: 40, textAlign: 'center', color: '#64748b', fontSize: 14 }}>No vouchers match your filter.</td></tr>
              )}
              {!isLoading && pageSlice.map(v => (
                <tr key={v.id} style={{ borderBottom: '1px solid #1e3a3a', transition: 'background 0.1s' }}
                  onMouseEnter={e => (e.currentTarget.style.background = '#0f2f2f')} onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
                  <td style={{ padding: '12px 16px', fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: '#64748b' }}>{v.voucher_number}</td>
                  <td style={{ padding: '12px 16px', fontSize: 13, color: '#94a3b8', whiteSpace: 'nowrap' }}>{formatDate(v.date)}</td>
                  <td style={{ padding: '12px 16px', fontSize: 13, color: '#e2e8f0', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{v.party}</td>
                  <td style={{ padding: '12px 16px' }}><TypeBadge type={v.type} /></td>
                  <td style={{ padding: '12px 16px', textAlign: 'right', fontFamily: 'JetBrains Mono, monospace', fontSize: 13, color: '#f1f5f9', whiteSpace: 'nowrap' }}>{formatAmount(v.amount)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {!isLoading && filtered.length > PAGE_SIZE && (
          <div style={{ padding: '12px 20px', borderTop: '1px solid #334155', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 12, color: '#64748b' }}>Showing {localPage * PAGE_SIZE + 1}–{Math.min((localPage + 1) * PAGE_SIZE, filtered.length)} of {filtered.length}</span>
            <div style={{ display: 'flex', gap: 8 }}>
              <button onClick={() => setLocalPage(p => Math.max(0, p - 1))} disabled={localPage === 0}
                style={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 6, padding: '5px 10px', color: localPage === 0 ? '#475569' : '#94a3b8', cursor: localPage === 0 ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center' }}>
                <ChevronLeft size={14} />
              </button>
              <button onClick={() => setLocalPage(p => Math.min(totalPages - 1, p + 1))} disabled={localPage >= totalPages - 1}
                style={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 6, padding: '5px 10px', color: localPage >= totalPages - 1 ? '#475569' : '#94a3b8', cursor: localPage >= totalPages - 1 ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center' }}>
                <ChevronRight size={14} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
