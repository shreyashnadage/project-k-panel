'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Search, ChevronLeft, ChevronRight, BookOpen } from 'lucide-react'

const PAGE_SIZE = 15

export default function LedgersPage() {
  const [skip, setSkip] = useState(0)
  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [parentFilter, setParentFilter] = useState('')

  const { data, isLoading, error } = useQuery({
    queryKey: ['ledgers', skip, search, parentFilter],
    queryFn: () => api.getLedgers(skip, PAGE_SIZE, search || undefined, parentFilter || undefined),
    staleTime: 30_000,
  })

  const { data: groups } = useQuery({
    queryKey: ['ledger-groups'],
    queryFn: () => api.getLedgerGroups(),
    staleTime: 120_000,
  })

  const total = data?.total ?? 0
  const totalPages = Math.ceil(total / PAGE_SIZE)
  const currentPage = Math.floor(skip / PAGE_SIZE) + 1

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setSearch(searchInput)
    setSkip(0)
  }

  const fmtBalance = (v: string | null) => {
    if (!v) return '-'
    const n = parseFloat(v.replace(/,/g, ''))
    if (isNaN(n)) return v
    const abs = Math.abs(n)
    const formatted = abs.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    if (n < 0) return `(${formatted}) Cr`
    if (n > 0) return `${formatted} Dr`
    return formatted
  }

  if (error) {
    return (
      <div style={{ textAlign: 'center', padding: 64 }}>
        <p style={{ color: '#ef4444' }}>Failed to load ledgers: {(error as Error).message}</p>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h2 style={{ fontFamily: 'Outfit, system-ui', fontWeight: 700, fontSize: 28, color: '#f1f5f9', margin: 0 }}>
            Ledgers
          </h2>
          <p style={{ color: '#64748b', fontSize: 14, marginTop: 4 }}>
            Chart of accounts synced from TallyPrime
          </p>
        </div>
        <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 13, color: '#94a3b8', background: '#1e293b', padding: '6px 14px', borderRadius: 8, border: '1px solid #334155' }}>
          {total} records
        </div>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        <form onSubmit={handleSearch} style={{ display: 'flex', flex: 1, minWidth: 220, position: 'relative' }}>
          <Search size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: '#64748b' }} />
          <input
            value={searchInput}
            onChange={e => setSearchInput(e.target.value)}
            placeholder="Search by name or group..."
            style={{
              flex: 1, padding: '10px 12px 10px 36px', borderRadius: 8,
              border: '1px solid #334155', background: '#0f172a', color: '#f1f5f9',
              fontFamily: 'Inter, system-ui', fontSize: 14, outline: 'none',
            }}
          />
        </form>
        <select
          value={parentFilter}
          onChange={e => { setParentFilter(e.target.value); setSkip(0) }}
          style={{
            padding: '10px 14px', borderRadius: 8, border: '1px solid #334155',
            background: '#0f172a', color: '#f1f5f9', fontFamily: 'Inter, system-ui',
            fontSize: 14, minWidth: 180, cursor: 'pointer', outline: 'none',
          }}
        >
          <option value="">All Groups</option>
          {(groups ?? []).map(g => <option key={g} value={g}>{g}</option>)}
        </select>
      </div>

      {/* Table */}
      <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 12, overflow: 'hidden' }}>
        {isLoading ? (
          <div style={{ padding: 48, textAlign: 'center' }}>
            <div className="shimmer" style={{ width: 200, height: 20, borderRadius: 6, margin: '0 auto 16px', background: '#334155' }} />
            {[1, 2, 3, 4, 5].map(i => (
              <div key={i} className="shimmer" style={{ height: 44, background: '#334155', marginBottom: 2 }} />
            ))}
          </div>
        ) : !data?.data.length ? (
          <div style={{ textAlign: 'center', padding: 64 }}>
            <BookOpen size={48} style={{ color: '#475569', marginBottom: 16 }} />
            <p style={{ color: '#94a3b8', fontWeight: 600, fontSize: 16 }}>No ledgers found</p>
            <p style={{ color: '#64748b', fontSize: 14 }}>
              {search || parentFilter ? 'Try adjusting your filters.' : 'They\'ll appear here once your agent syncs.'}
            </p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'Inter, system-ui', fontSize: 14 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #334155' }}>
                  {['Ledger Name', 'Group', 'Type', 'Opening Balance', 'Closing Balance'].map(h => (
                    <th key={h} style={{ padding: '12px 16px', textAlign: 'left', color: '#94a3b8', fontWeight: 600, fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.data.map(l => (
                  <tr key={l.id} style={{ borderBottom: '1px solid #1e293b' }}
                    onMouseEnter={e => (e.currentTarget.style.background = '#263348')}
                    onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                  >
                    <td style={{ padding: '12px 16px', color: '#f1f5f9', fontWeight: 500 }}>{l.name}</td>
                    <td style={{ padding: '12px 16px', color: '#94a3b8' }}>{l.parent || '-'}</td>
                    <td style={{ padding: '12px 16px' }}>
                      {l.ledger_type ? (
                        <span style={{ padding: '3px 10px', borderRadius: 6, fontSize: 12, fontWeight: 600, background: '#1e3a5f', color: '#7dd3fc', border: '1px solid #2563eb33' }}>
                          {l.ledger_type}
                        </span>
                      ) : '-'}
                    </td>
                    <td style={{ padding: '12px 16px', fontFamily: 'JetBrains Mono, monospace', fontSize: 13, color: '#94a3b8', textAlign: 'right' }}>
                      {fmtBalance(l.opening_balance)}
                    </td>
                    <td style={{ padding: '12px 16px', fontFamily: 'JetBrains Mono, monospace', fontSize: 13, color: '#f1f5f9', textAlign: 'right', fontWeight: 500 }}>
                      {fmtBalance(l.closing_balance)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', borderTop: '1px solid #334155' }}>
            <span style={{ color: '#64748b', fontSize: 13 }}>
              Showing {skip + 1}–{Math.min(skip + PAGE_SIZE, total)} of {total}
            </span>
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                disabled={skip === 0}
                onClick={() => setSkip(Math.max(0, skip - PAGE_SIZE))}
                style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid #334155', background: '#0f172a', color: skip === 0 ? '#475569' : '#f1f5f9', cursor: skip === 0 ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', gap: 4, fontSize: 13 }}
              >
                <ChevronLeft size={14} /> Prev
              </button>
              <span style={{ padding: '6px 12px', fontSize: 13, color: '#94a3b8' }}>
                {currentPage} / {totalPages}
              </span>
              <button
                disabled={skip + PAGE_SIZE >= total}
                onClick={() => setSkip(skip + PAGE_SIZE)}
                style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid #334155', background: '#0f172a', color: skip + PAGE_SIZE >= total ? '#475569' : '#f1f5f9', cursor: skip + PAGE_SIZE >= total ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', gap: 4, fontSize: 13 }}
              >
                Next <ChevronRight size={14} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
