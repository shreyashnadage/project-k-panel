'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { adminApi } from '@/lib/api'
import { Search, Users, Building2, Wifi, WifiOff, UserPlus } from 'lucide-react'

function formatRelativeTime(iso: string | null): string {
  if (!iso) return 'Never'
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

const STATUS_COLORS: Record<string, { bg: string; text: string; border: string; label: string }> = {
  active:               { bg: '#dcfce720', text: '#4ade80', border: '#22c55e40', label: 'Active' },
  pending_verification: { bg: '#fef3c720', text: '#fbbf24', border: '#f59e0b40', label: 'Pending' },
  suspended:            { bg: '#fee2e220', text: '#f87171', border: '#ef444440', label: 'Suspended' },
  inactive:             { bg: '#33415520', text: '#94a3b8', border: '#33415540', label: 'Inactive' },
}

export default function ClientsListPage() {
  const router = useRouter()
  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')

  const { data, isLoading, error } = useQuery({
    queryKey: ['admin-clients', search],
    queryFn: () => adminApi.getClients(0, 100, search || undefined),
    staleTime: 30_000,
  })

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setSearch(searchInput)
  }

  return (
    <div className="page-enter" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h2 style={{ fontFamily: 'Outfit, system-ui', fontWeight: 700, fontSize: 28, color: '#f1f5f9', margin: 0 }}>
            Clients
          </h2>
          <p style={{ color: '#64748b', fontSize: 14, marginTop: 4 }}>
            Onboarded MSME businesses using Tally Sync
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 13, color: '#94a3b8', background: '#1e293b', padding: '6px 14px', borderRadius: 8, border: '1px solid #334155' }}>
            {data?.total ?? '—'} clients
          </div>
          <button
            onClick={() => router.push('/clients/onboard')}
            style={{
              display: 'flex', alignItems: 'center', gap: 6, padding: '8px 16px',
              borderRadius: 8, border: 'none', background: '#14b8a6', color: '#0f172a',
              cursor: 'pointer', fontFamily: 'Inter, system-ui', fontSize: 13, fontWeight: 600,
            }}
          >
            <UserPlus size={15} /> Onboard Client
          </button>
        </div>
      </div>

      {/* Search */}
      <form onSubmit={handleSearch} style={{ display: 'flex', maxWidth: 400, position: 'relative' }}>
        <Search size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: '#64748b' }} />
        <input
          value={searchInput}
          onChange={e => setSearchInput(e.target.value)}
          placeholder="Search by company name or email..."
          style={{
            flex: 1, padding: '10px 12px 10px 36px', borderRadius: 8,
            border: '1px solid #334155', background: '#0f172a', color: '#f1f5f9',
            fontFamily: 'Inter, system-ui', fontSize: 14, outline: 'none',
          }}
        />
      </form>

      {/* Table */}
      <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 12, overflow: 'hidden' }}>
        {isLoading ? (
          <div style={{ padding: 48 }}>
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="skeleton" style={{ height: 52, background: '#334155', marginBottom: 2, borderRadius: 0 }} />
            ))}
          </div>
        ) : error ? (
          <div style={{ textAlign: 'center', padding: 64 }}>
            <p style={{ color: '#ef4444' }}>Failed to load clients. Check your authentication.</p>
          </div>
        ) : !data?.clients.length ? (
          <div style={{ textAlign: 'center', padding: 64 }}>
            <Users size={48} style={{ color: '#475569', marginBottom: 16 }} />
            <p style={{ color: '#94a3b8', fontWeight: 600, fontSize: 16 }}>No clients found</p>
            <p style={{ color: '#64748b', fontSize: 14 }}>
              {search ? 'Try a different search term.' : 'Register your first MSME client to get started.'}
            </p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'Inter, system-ui', fontSize: 14 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #334155' }}>
                  {['Company', 'Status', 'Plan', 'Devices', 'Last Sync', 'Created'].map(h => (
                    <th key={h} style={{
                      padding: '12px 16px', textAlign: 'left', color: '#94a3b8',
                      fontWeight: 600, fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.05em',
                    }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.clients.map(c => {
                  const status = STATUS_COLORS[c.status] ?? STATUS_COLORS.inactive
                  return (
                    <tr
                      key={c.client_id}
                      onClick={() => router.push(`/clients/${c.client_id}`)}
                      style={{ borderBottom: '1px solid #1e293b', cursor: 'pointer', transition: 'background 0.1s' }}
                      onMouseEnter={e => (e.currentTarget.style.background = '#263348')}
                      onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                    >
                      <td style={{ padding: '14px 16px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                          <div style={{
                            width: 36, height: 36, borderRadius: 8, flexShrink: 0,
                            background: '#14b8a615', display: 'flex', alignItems: 'center', justifyContent: 'center',
                          }}>
                            <Building2 size={16} color="#14b8a6" />
                          </div>
                          <div>
                            <div style={{ fontWeight: 600, color: '#f1f5f9' }}>{c.company_name}</div>
                            <div style={{ fontSize: 12, color: '#64748b', marginTop: 1 }}>{c.email}</div>
                          </div>
                        </div>
                      </td>
                      <td style={{ padding: '14px 16px' }}>
                        <span style={{
                          display: 'inline-flex', alignItems: 'center', gap: 6,
                          padding: '3px 10px', borderRadius: 20, fontSize: 12, fontWeight: 500,
                          background: status.bg, color: status.text, border: `1px solid ${status.border}`,
                        }}>
                          <span style={{ width: 6, height: 6, borderRadius: '50%', background: status.text, display: 'inline-block' }} />
                          {status.label}
                        </span>
                      </td>
                      <td style={{ padding: '14px 16px', color: '#94a3b8', fontSize: 13, textTransform: 'capitalize' }}>
                        {c.plan}
                      </td>
                      <td style={{ padding: '14px 16px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          {c.device_count > 0
                            ? <Wifi size={14} color="#22c55e" />
                            : <WifiOff size={14} color="#64748b" />
                          }
                          <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 13, color: c.device_count > 0 ? '#f1f5f9' : '#64748b' }}>
                            {c.device_count}
                          </span>
                        </div>
                      </td>
                      <td style={{ padding: '14px 16px', fontFamily: 'JetBrains Mono, monospace', fontSize: 13, color: '#94a3b8' }}>
                        {formatRelativeTime(c.last_sync_at)}
                      </td>
                      <td style={{ padding: '14px 16px', fontSize: 13, color: '#64748b' }}>
                        {c.created_at ? new Date(c.created_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: '2-digit' }) : '-'}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
