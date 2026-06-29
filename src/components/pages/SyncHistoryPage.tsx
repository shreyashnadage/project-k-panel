'use client'

import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { SyncCommandType } from '@/types/widgets'
import {
  Radio, ChevronLeft, ChevronRight, Play, Send,
} from 'lucide-react'

const PAGE_SIZE = 15

const RAG: Record<string, { dot: string; dotClass: string; label: string; bg: string; text: string }> = {
  pending:   { dot: '#e07a3d', dotClass: 'sync-dot--pending',   label: 'Waiting',     bg: '#e07a3d18', text: '#e07a3d' },
  fetched:   { dot: '#3db8a9', dotClass: 'sync-dot--fetched',   label: 'In Progress', bg: '#3db8a918', text: '#3db8a9' },
  completed: { dot: '#3db8a9', dotClass: 'sync-dot--completed', label: 'Done',        bg: '#3db8a918', text: '#3db8a9' },
  failed:    { dot: '#c45c4a', dotClass: 'sync-dot--failed',    label: 'Failed',      bg: '#c45c4a18', text: '#c45c4a' },
}

const COMMAND_LABELS: Record<string, string> = {
  sync_ledgers: 'Sync Ledgers',
  sync_ledgers_by_group: 'Ledgers by Group',
  sync_ledger_one: 'Single Ledger',
  sync_groups: 'Sync Groups',
  sync_vouchers: 'Sync Vouchers',
  sync_vouchers_by_type: 'Vouchers by Type',
  sync_stock: 'Sync Stock',
  sync_stock_by_group: 'Stock by Group',
  sync_full: 'Full Sync',
  health_check: 'Health Check',
}

const QUICK_COMMANDS: { type: SyncCommandType; label: string; description: string }[] = [
  { type: 'sync_ledgers',  label: 'Sync Ledgers',  description: 'Pull all ledger accounts' },
  { type: 'sync_vouchers', label: 'Sync Vouchers', description: 'Pull recent transactions' },
  { type: 'sync_groups',   label: 'Sync Groups',   description: 'Pull account group hierarchy' },
  { type: 'sync_stock',    label: 'Sync Stock',     description: 'Pull inventory items' },
  { type: 'health_check',  label: 'Health Check',   description: 'Verify Tally connectivity' },
]

const DEVICE_ID = 'device-e2e-001'

function relativeTime(iso: string | null): string {
  if (!iso) return '-'
  const ts = new Date(iso)
  if (isNaN(ts.getTime())) return '-'
  // If the timestamp has no timezone info, treat as UTC
  const utcMs = iso.endsWith('Z') || iso.includes('+') ? ts.getTime() : ts.getTime() - ts.getTimezoneOffset() * 60000
  const diffMs = Date.now() - utcMs
  if (diffMs < 0) return 'just now'
  const secs = Math.floor(diffMs / 1000)
  if (secs < 5) return 'just now'
  if (secs < 60) return `${secs}s ago`
  const mins = Math.floor(secs / 60)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  return `${days}d ago`
}

export default function SyncHistoryPage() {
  const [skip, setSkip] = useState(0)
  const [statusFilter, setStatusFilter] = useState('')
  const [, setTick] = useState(0)
  const queryClient = useQueryClient()

  // Force re-render every second so relative timestamps stay fresh
  useEffect(() => {
    const id = setInterval(() => setTick(t => t + 1), 1000)
    return () => clearInterval(id)
  }, [])

  const { data, isLoading, error } = useQuery({
    queryKey: ['sync-history', skip, statusFilter],
    queryFn: () => api.getSyncHistory(skip, PAGE_SIZE, statusFilter || undefined),
    staleTime: 2_000,
    refetchInterval: (query) => {
      const d = query.state.data
      const hasActive = d?.data.some(c => c.status === 'pending' || c.status === 'fetched')
      return hasActive ? 3_000 : 15_000
    },
  })

  const triggerMutation = useMutation({
    mutationFn: (cmd: { type: SyncCommandType; params?: Record<string, string> }) =>
      api.createCommand(DEVICE_ID, cmd.type, cmd.params ?? {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sync-history'] })
      queryClient.invalidateQueries({ queryKey: ['kpis'] })
    },
  })

  const total = data?.total ?? 0
  const totalPages = Math.ceil(total / PAGE_SIZE)
  const currentPage = Math.floor(skip / PAGE_SIZE) + 1

  const fmtDuration = (created: string, completed: string | null) => {
    if (!completed) return '-'
    const ms = new Date(completed).getTime() - new Date(created).getTime()
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(1)}s`
  }

  // Count active commands for the header badge
  const activeCount = data?.data.filter(c => c.status === 'pending' || c.status === 'fetched').length ?? 0

  if (error) {
    return (
      <div style={{ textAlign: 'center', padding: 64 }}>
        <p style={{ color: '#c45c4a' }}>Failed to load sync history: {(error as Error).message}</p>
      </div>
    )
  }

  return (
    <div className="page-enter" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2 style={{ fontWeight: 700, fontSize: 28, color: '#f5f0e8', margin: 0 }}>
            Sync History
          </h2>
          <p style={{ color: '#a8b8c8', fontSize: 14, marginTop: 4 }}>
            Command history and quick-trigger sync actions
          </p>
        </div>
        {activeCount > 0 && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: 8,
            padding: '6px 14px', borderRadius: 10,
            background: '#152a40', border: '1px solid #2d3e5044',
          }}>
            <span className="sync-dot--fetched" style={{
              width: 8, height: 8, borderRadius: '50%', background: '#3db8a9', display: 'inline-block',
            }} />
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: '#3db8a9' }}>
              {activeCount} active
            </span>
          </div>
        )}
      </div>

      {/* Quick actions */}
      <div style={{ background: '#1b263b', border: '1px solid #2d3e50', borderRadius: 14, padding: 20 }}>
        <h3 style={{ fontWeight: 600, fontSize: 16, color: '#f5f0e8', margin: '0 0 14px' }}>
          <Play size={16} style={{ verticalAlign: '-2px', marginRight: 8, color: '#3db8a9' }} />
          Trigger Sync
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 10 }}>
          {QUICK_COMMANDS.map(cmd => (
            <button
              key={cmd.type}
              disabled={triggerMutation.isPending}
              onClick={() => {
                const params: Record<string, string> = { company_name: 'Bhrama Enterprises' }
                if (cmd.type === 'sync_vouchers') {
                  params.from_date = '20260601'
                  params.to_date = '20260630'
                }
                triggerMutation.mutate({ type: cmd.type, params })
              }}
              style={{
                padding: '12px 14px', borderRadius: 10, border: '1px solid #2d3e50',
                background: '#0d1b2a', cursor: triggerMutation.isPending ? 'wait' : 'pointer',
                textAlign: 'left', transition: 'all 0.15s',
              }}
              onMouseEnter={e => { e.currentTarget.style.borderColor = '#3db8a9' }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = '#2d3e50' }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                <Send size={14} style={{ color: '#3db8a9' }} />
                <span style={{ fontWeight: 600, fontSize: 13, color: '#f5f0e8' }}>{cmd.label}</span>
              </div>
              <span style={{ fontSize: 12, color: '#a8b8c8' }}>{cmd.description}</span>
            </button>
          ))}
        </div>
        {triggerMutation.isSuccess && (
          <p style={{ color: '#3db8a9', fontSize: 13, marginTop: 10 }}>
            Command queued. The agent will pick it up within 15s.
          </p>
        )}
        {triggerMutation.isError && (
          <p style={{ color: '#c45c4a', fontSize: 13, marginTop: 10 }}>
            Failed: {(triggerMutation.error as Error).message}
          </p>
        )}
      </div>

      {/* Filter bar */}
      <div style={{ display: 'flex', gap: 8 }}>
        {['', 'pending', 'fetched', 'completed', 'failed'].map(s => (
          <button
            key={s}
            onClick={() => { setStatusFilter(s); setSkip(0) }}
            style={{
              padding: '6px 14px', borderRadius: 6, fontSize: 13, fontWeight: 500,
              border: '1px solid ' + (statusFilter === s ? '#3db8a9' : '#2d3e50'),
              background: statusFilter === s ? '#3db8a922' : 'transparent',
              color: statusFilter === s ? '#3db8a9' : '#a8b8c8',
              cursor: 'pointer',
            }}
          >
            {s || 'All'}
          </button>
        ))}
      </div>

      {/* Table */}
      <div style={{ background: '#1b263b', border: '1px solid #2d3e50', borderRadius: 14, overflow: 'hidden' }}>
        {isLoading ? (
          <div style={{ padding: 48, textAlign: 'center' }}>
            {[1, 2, 3].map(i => (
              <div key={i} className="shimmer" style={{ height: 44, background: '#2d3e50', marginBottom: 2 }} />
            ))}
          </div>
        ) : !data?.data.length ? (
          <div style={{ textAlign: 'center', padding: 64 }}>
            <Radio size={48} style={{ color: '#2d3e50', marginBottom: 16 }} />
            <p style={{ color: '#a8b8c8', fontWeight: 600, fontSize: 16 }}>No sync commands yet</p>
            <p style={{ color: '#a8b8c8', fontSize: 14 }}>Use the buttons above to trigger a sync.</p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #2d3e50' }}>
                  {['', 'Command', 'Status', 'When', 'Duration', 'Result'].map(h => (
                    <th key={h} style={{
                      padding: h === '' ? '12px 0 12px 16px' : '12px 16px',
                      textAlign: 'left', color: '#a8b8c8', fontWeight: 600, fontSize: 12,
                      textTransform: 'uppercase', letterSpacing: '0.05em',
                      width: h === '' ? 28 : undefined,
                    }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.data.map(cmd => {
                  const rag = RAG[cmd.status] ?? RAG.pending
                  const isActive = cmd.status === 'pending' || cmd.status === 'fetched'
                  return (
                    <tr key={cmd.id}
                      style={{
                        borderBottom: '1px solid #1b263b',
                        background: isActive ? rag.bg : 'transparent',
                      }}
                      onMouseEnter={e => { e.currentTarget.style.background = isActive ? rag.bg : '#152a40' }}
                      onMouseLeave={e => { e.currentTarget.style.background = isActive ? rag.bg : 'transparent' }}
                    >
                      {/* RAG dot */}
                      <td style={{ padding: '12px 0 12px 16px', width: 28 }}>
                        <span
                          className={rag.dotClass}
                          style={{
                            width: 10, height: 10, borderRadius: '50%',
                            background: rag.dot, display: 'inline-block',
                          }}
                        />
                      </td>
                      <td style={{ padding: '12px 16px' }}>
                        <div style={{ color: '#f5f0e8', fontWeight: 500 }}>
                          {COMMAND_LABELS[cmd.command_type] ?? cmd.command_type}
                        </div>
                        {cmd.params && Object.keys(cmd.params).length > 0 && (
                          <div style={{ fontSize: 12, color: '#a8b8c8', marginTop: 2, fontFamily: 'var(--font-mono)' }}>
                            {Object.entries(cmd.params).map(([k, v]) => `${k}=${v}`).join(', ')}
                          </div>
                        )}
                      </td>
                      <td style={{ padding: '12px 16px' }}>
                        <span style={{
                          fontSize: 12, fontWeight: 600, color: rag.text,
                        }}>
                          {rag.label}
                        </span>
                      </td>
                      <td style={{ padding: '12px 16px', fontSize: 13, fontFamily: 'var(--font-mono)' }}>
                        <span style={{ color: isActive ? rag.text : '#a8b8c8' }}>
                          {relativeTime(cmd.created_at)}
                        </span>
                      </td>
                      <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)', fontSize: 13, color: '#a8b8c8' }}>
                        {fmtDuration(cmd.created_at, cmd.completed_at)}
                      </td>
                      <td style={{ padding: '12px 16px', fontSize: 13, color: '#a8b8c8', maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {cmd.error_message
                          ? <span style={{ color: '#c45c4a' }}>{cmd.error_message}</span>
                          : cmd.result
                            ? JSON.stringify(cmd.result)
                            : isActive
                              ? <span style={{ color: rag.text, fontStyle: 'italic' }}>
                                  {cmd.status === 'pending' ? 'Waiting for agent...' : 'Executing...'}
                                </span>
                              : '-'
                        }
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', borderTop: '1px solid #2d3e50' }}>
            <span style={{ color: '#a8b8c8', fontSize: 13 }}>
              {skip + 1}–{Math.min(skip + PAGE_SIZE, total)} of {total}
            </span>
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                disabled={skip === 0}
                onClick={() => setSkip(Math.max(0, skip - PAGE_SIZE))}
                style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid #2d3e50', background: '#0d1b2a', color: skip === 0 ? '#2d3e50' : '#f5f0e8', cursor: skip === 0 ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', gap: 4, fontSize: 13 }}
              >
                <ChevronLeft size={14} /> Prev
              </button>
              <span style={{ padding: '6px 12px', fontSize: 13, color: '#a8b8c8' }}>{currentPage} / {totalPages}</span>
              <button
                disabled={skip + PAGE_SIZE >= total}
                onClick={() => setSkip(skip + PAGE_SIZE)}
                style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid #2d3e50', background: '#0d1b2a', color: skip + PAGE_SIZE >= total ? '#2d3e50' : '#f5f0e8', cursor: skip + PAGE_SIZE >= total ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', gap: 4, fontSize: 13 }}
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
