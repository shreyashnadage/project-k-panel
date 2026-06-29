'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useClientContext } from '@/lib/client-context'
import { useClientApi } from '@/hooks/useClientApi'
import { adminApi } from '@/lib/api'
import { AlertTriangle, AlertCircle, Info, Bug, ChevronDown, ChevronRight, RefreshCw, Filter, Play, Clock } from 'lucide-react'

const SEVERITY_CONFIG: Record<string, { color: string; bg: string; Icon: React.ElementType; label: string }> = {
  critical: { color: '#c45c4a', bg: '#c45c4a18', Icon: AlertCircle, label: 'Critical' },
  error:    { color: '#c45c4a', bg: '#c45c4a18', Icon: AlertTriangle, label: 'Error' },
  warning:  { color: '#e07a3d', bg: '#e07a3d18', Icon: AlertTriangle, label: 'Warning' },
  info:     { color: '#3db8a9', bg: '#3db8a918', Icon: Info, label: 'Info' },
  debug:    { color: '#a8b8c8', bg: '#a8b8c818', Icon: Bug, label: 'Debug' },
}

const FREQUENCY_OPTIONS = [
  { value: 'manual', label: 'Manual' },
  { value: '1m',     label: 'Every 1 min' },
  { value: '5m',     label: 'Every 5 min' },
  { value: '15m',    label: 'Every 15 min' },
  { value: '30m',    label: 'Every 30 min' },
  { value: '1h',     label: 'Every 1 hour' },
]

const FREQ_TO_MS: Record<string, number> = {
  '1m': 60_000, '5m': 300_000, '15m': 900_000, '30m': 1_800_000, '1h': 3_600_000,
}

function relativeTime(iso: string): string {
  const ts = new Date(iso)
  if (isNaN(ts.getTime())) return iso
  const diffMs = Date.now() - ts.getTime()
  if (diffMs < 0) return 'just now'
  const secs = Math.floor(diffMs / 1000)
  if (secs < 60) return `${secs}s ago`
  const mins = Math.floor(secs / 60)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

function formatTimestamp(iso: string): string {
  try {
    return new Date(iso).toLocaleString('en-IN', {
      day: '2-digit', month: 'short', year: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false,
    })
  } catch { return iso }
}

export default function AgentLogsPage() {
  const { clientId, companyName, deviceId, devices } = useClientContext()
  const clientApi = useClientApi()
  const queryClient = useQueryClient()

  const [severityFilter, setSeverityFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [limit, setLimit] = useState(100)
  const [selectedDeviceId, setSelectedDeviceId] = useState(deviceId || '')
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => { if (deviceId && !selectedDeviceId) setSelectedDeviceId(deviceId) }, [deviceId, selectedDeviceId])

  // Telemetry config (frequency)
  const configQuery = useQuery({
    queryKey: ['telemetry-config', clientId],
    queryFn: () => adminApi.getTelemetryConfig(clientId),
    staleTime: 60_000,
  })
  const currentFreq = configQuery.data?.frequency ?? 'manual'

  const configMutation = useMutation({
    mutationFn: (freq: string) => adminApi.updateTelemetryConfig(clientId, freq),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['telemetry-config', clientId] }),
  })

  // Manual sync trigger
  const syncMutation = useMutation({
    mutationFn: () => clientApi!.createCommand(selectedDeviceId, 'push_telemetry' as any, {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['telemetry-events', clientId] })
    },
  })

  const triggerSync = useCallback(() => {
    if (clientApi && selectedDeviceId && !syncMutation.isPending) {
      syncMutation.mutate()
      setTimeout(() => refetchEvents(), 5000)
    }
  }, [selectedDeviceId, syncMutation])

  // Auto-sync timer based on frequency
  useEffect(() => {
    if (timerRef.current) clearInterval(timerRef.current)
    const ms = FREQ_TO_MS[currentFreq]
    if (ms && selectedDeviceId) {
      triggerSync()
      timerRef.current = setInterval(triggerSync, ms)
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [currentFreq, selectedDeviceId, triggerSync])

  const { data: events, isLoading, error, refetch: refetchEvents, isFetching } = useQuery({
    queryKey: ['telemetry-events', clientId, severityFilter, typeFilter, limit],
    queryFn: () => adminApi.getTelemetryEvents(clientId, {
      severity: severityFilter || undefined,
      event_type: typeFilter || undefined,
      limit,
    }),
    staleTime: 10_000,
    refetchInterval: currentFreq === 'manual' ? false : Math.min(FREQ_TO_MS[currentFreq] ?? 30_000, 30_000),
  })

  const eventTypes = events ? [...new Set(events.map(e => e.event_type))].sort() : []

  const severityCounts = events?.reduce((acc, e) => {
    acc[e.severity] = (acc[e.severity] || 0) + 1
    return acc
  }, {} as Record<string, number>) ?? {}

  const errorCount = (severityCounts['error'] ?? 0) + (severityCounts['critical'] ?? 0)
  const warnCount = severityCounts['warning'] ?? 0

  if (!clientApi) {
    return (
      <div className="page-enter" style={{ textAlign: 'center', padding: 64 }}>
        <AlertTriangle size={48} style={{ color: '#2d3e50', marginBottom: 16 }} />
        <p style={{ color: '#f5f0e8', fontWeight: 600, fontSize: 16 }}>No active devices</p>
        <p style={{ color: '#a8b8c8', fontSize: 14, marginTop: 8 }}>This client needs a registered device before agent logs are available.</p>
      </div>
    )
  }

  return (
    <div style={{  }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 800, color: '#f5f0e8', margin: 0,  }}>
            Agent Logs
          </h1>
          <p style={{ color: '#a8b8c8', fontSize: 14, marginTop: 4 }}>
            Telemetry and error events from {companyName}&apos;s agent
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {events && (
            <span style={{
              padding: '6px 14px', borderRadius: 20, fontSize: 12, fontWeight: 600,
              background: '#1b263b', color: '#a8b8c8', border: '1px solid #2d3e50',
            }}>
              {events.length} events
            </span>
          )}
          {errorCount > 0 && (
            <span style={{
              padding: '6px 14px', borderRadius: 20, fontSize: 12, fontWeight: 600,
              background: '#c45c4a18', color: '#c45c4a', border: '1px solid #c45c4a40',
            }}>
              {errorCount} errors
            </span>
          )}
          {warnCount > 0 && (
            <span style={{
              padding: '6px 14px', borderRadius: 20, fontSize: 12, fontWeight: 600,
              background: '#e07a3d18', color: '#e07a3d', border: '1px solid #e07a3d40',
            }}>
              {warnCount} warnings
            </span>
          )}
        </div>
      </div>

      {/* Sync Controls */}
      <div style={{
        display: 'flex', gap: 12, marginBottom: 16, alignItems: 'center',
        padding: '14px 16px', borderRadius: 10, background: '#3db8a908',
        border: '1px solid #3db8a925',
      }}>
        <Clock size={16} style={{ color: '#3db8a9', flexShrink: 0 }} />
        <span style={{ fontSize: 13, fontWeight: 600, color: '#f5f0e8', marginRight: 4 }}>Log Sync:</span>

        {/* Frequency dropdown */}
        <select
          value={currentFreq}
          onChange={e => configMutation.mutate(e.target.value)}
          disabled={configMutation.isPending}
          style={{
            padding: '6px 12px', borderRadius: 10, fontSize: 12, fontWeight: 600,
            border: '1px solid #2d3e50', background: '#0d1b2a', color: '#3db8a9',
            fontFamily: 'var(--font-mono)', cursor: 'pointer',
          }}
        >
          {FREQUENCY_OPTIONS.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>

        {currentFreq !== 'manual' && (
          <span style={{ fontSize: 11, color: '#a8b8c8', fontStyle: 'italic' }}>
            Auto-syncing {FREQUENCY_OPTIONS.find(o => o.value === currentFreq)?.label.toLowerCase()}
          </span>
        )}

        <div style={{ flex: 1 }} />

        {/* Device selector */}
        {devices.length > 1 && (
          <select value={selectedDeviceId} onChange={e => setSelectedDeviceId(e.target.value)}
            style={{ padding: '6px 10px', borderRadius: 6, border: '1px solid #2d3e50', background: '#0d1b2a', color: '#f5f0e8', fontSize: 12, fontFamily: 'var(--font-mono)' }}>
            {devices.map(d => <option key={d.device_id} value={d.device_id}>{d.device_name}</option>)}
          </select>
        )}

        {/* Manual sync button */}
        <button
          onClick={triggerSync}
          disabled={syncMutation.isPending || !selectedDeviceId}
          style={{
            padding: '7px 16px', borderRadius: 10, fontSize: 12, fontWeight: 600,
            background: syncMutation.isPending ? '#0d1b2a' : '#3db8a9', color: '#fff',
            border: 'none', cursor: syncMutation.isPending ? 'wait' : 'pointer',
            display: 'flex', alignItems: 'center', gap: 6,
            opacity: syncMutation.isPending ? 0.6 : 1, transition: 'all 0.15s',
          }}
        >
          {syncMutation.isPending ? (
            <RefreshCw size={13} style={{ animation: 'spin 1s linear infinite' }} />
          ) : (
            <Play size={13} />
          )}
          {syncMutation.isPending ? 'Syncing...' : 'Sync Logs Now'}
        </button>

        {/* Refresh display */}
        <button
          onClick={() => refetchEvents()}
          disabled={isFetching}
          style={{
            padding: '7px 12px', borderRadius: 10, fontSize: 12, fontWeight: 500,
            background: 'transparent', color: '#a8b8c8', border: '1px solid #2d3e50',
            cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 5,
            opacity: isFetching ? 0.6 : 1,
          }}
        >
          <RefreshCw size={12} style={{ animation: isFetching ? 'spin 1s linear infinite' : 'none' }} />
          Refresh
        </button>
      </div>

      {syncMutation.isSuccess && (
        <p style={{ color: '#3db8a9', fontSize: 12, margin: '-8px 0 12px 0' }}>
          Push telemetry command sent to agent. Events will appear shortly.
        </p>
      )}

      {/* Filters */}
      <div style={{
        display: 'flex', gap: 12, marginBottom: 16, alignItems: 'center',
        padding: '12px 16px', borderRadius: 10, background: '#1b263b40', border: '1px solid #2d3e50',
      }}>
        <Filter size={14} style={{ color: '#a8b8c8', flexShrink: 0 }} />
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {['', 'critical', 'error', 'warning', 'info', 'debug'].map(sev => {
            const active = severityFilter === sev
            const label = sev || 'All'
            const cfg = sev ? SEVERITY_CONFIG[sev] : null
            return (
              <button key={sev} onClick={() => setSeverityFilter(sev)} style={{
                padding: '4px 12px', borderRadius: 6, fontSize: 12, fontWeight: 500,
                border: active ? '1px solid #3db8a9' : '1px solid #2d3e5060',
                background: active ? '#3db8a920' : 'transparent',
                color: active ? '#3db8a9' : (cfg?.color ?? '#a8b8c8'),
                cursor: 'pointer', fontFamily: 'var(--font-mono)',
              }}>
                {label}{severityCounts[sev] ? ` (${severityCounts[sev]})` : ''}
              </button>
            )
          })}
        </div>
        {eventTypes.length > 0 && (
          <>
            <div style={{ width: 1, height: 20, background: '#2d3e50', margin: '0 4px' }} />
            <select
              value={typeFilter}
              onChange={e => setTypeFilter(e.target.value)}
              style={{
                padding: '4px 8px', borderRadius: 6, fontSize: 12, border: '1px solid #2d3e50',
                background: '#0d1b2a', color: '#a8b8c8', fontFamily: 'var(--font-mono)',
              }}
            >
              <option value="">All types</option>
              {eventTypes.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </>
        )}
      </div>

      {/* Content */}
      {isLoading && (
        <div style={{ padding: 40, textAlign: 'center', color: '#a8b8c8' }}>Loading telemetry events...</div>
      )}
      {error && (
        <div style={{ padding: 20, background: '#c45c4a18', border: '1px solid #c45c4a40', borderRadius: 10, color: '#c45c4a', fontSize: 13 }}>
          Failed to load events: {(error as Error).message}
        </div>
      )}
      {events && events.length === 0 && (
        <div style={{
          padding: 60, textAlign: 'center', background: '#1b263b40', borderRadius: 14,
          border: '1px solid #2d3e50',
        }}>
          <Info size={32} style={{ color: '#a8b8c8', marginBottom: 12 }} />
          <p style={{ color: '#a8b8c8', fontSize: 15, fontWeight: 500, margin: 0 }}>No telemetry events yet</p>
          <p style={{ color: '#a8b8c8', fontSize: 13, marginTop: 6 }}>
            Click <strong style={{ color: '#3db8a9' }}>Sync Logs Now</strong> to pull logs from the agent,
            or set a frequency to auto-sync.
          </p>
        </div>
      )}
      {events && events.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {events.map(ev => {
            const cfg = SEVERITY_CONFIG[ev.severity] ?? SEVERITY_CONFIG.info
            const SevIcon = cfg.Icon
            const isExpanded = expandedId === ev.event_id
            const hasStack = !!ev.error_stack
            const hasError = !!ev.error_message

            return (
              <div key={ev.event_id} style={{
                background: isExpanded ? '#1b263b' : '#1b263b60',
                border: `1px solid ${isExpanded ? '#2d3e50' : '#2d3e5040'}`,
                borderRadius: 10, overflow: 'hidden', transition: 'all 0.15s',
              }}>
                <button
                  onClick={() => setExpandedId(isExpanded ? null : ev.event_id)}
                  style={{
                    width: '100%', display: 'grid',
                    gridTemplateColumns: '20px 80px 1fr 160px 100px 20px',
                    gap: 12, alignItems: 'center', padding: '10px 14px',
                    border: 'none', background: 'transparent', cursor: 'pointer',
                    textAlign: 'left',
                  }}
                >
                  <SevIcon size={14} style={{ color: cfg.color }} />
                  <span style={{
                    fontSize: 11, fontWeight: 600, fontFamily: 'var(--font-mono)',
                    padding: '2px 8px', borderRadius: 4, background: cfg.bg, color: cfg.color,
                    textAlign: 'center', textTransform: 'uppercase',
                  }}>
                    {cfg.label}
                  </span>
                  <span style={{
                    fontSize: 13, color: '#f5f0e8', fontFamily: 'var(--font-mono)',
                    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                  }}>
                    {hasError ? ev.error_message : ev.event_type}
                    {!hasError && ev.source && (
                      <span style={{ color: '#a8b8c8', marginLeft: 8 }}>({ev.source})</span>
                    )}
                  </span>
                  <span style={{ fontSize: 11, color: '#a8b8c8', fontFamily: 'var(--font-mono)' }}>
                    {formatTimestamp(ev.timestamp)}
                  </span>
                  <span style={{ fontSize: 11, color: '#a8b8c8', fontFamily: 'var(--font-mono)', textAlign: 'right' }}>
                    {relativeTime(ev.timestamp)}
                  </span>
                  {isExpanded ? <ChevronDown size={12} style={{ color: '#a8b8c8' }} /> : <ChevronRight size={12} style={{ color: '#2d3e50' }} />}
                </button>

                {isExpanded && (
                  <div style={{ padding: '0 14px 14px', borderTop: '1px solid #2d3e5040' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 12 }}>
                      <DetailField label="Event Type" value={ev.event_type} />
                      <DetailField label="Source" value={ev.source || '-'} />
                      <DetailField label="Agent ID" value={ev.agent_id} />
                      <DetailField label="Agent Version" value={ev.agent_version || '-'} />
                      <DetailField label="Hostname" value={ev.hostname || '-'} />
                      <DetailField label="Timestamp" value={formatTimestamp(ev.timestamp)} />
                      {ev.error_code && <DetailField label="Error Code" value={ev.error_code} />}
                    </div>

                    {hasError && (
                      <div style={{ marginTop: 12 }}>
                        <div style={{ fontSize: 11, color: '#a8b8c8', fontWeight: 600, marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                          Error Message
                        </div>
                        <div style={{
                          padding: '10px 14px', borderRadius: 6, background: '#c45c4a10',
                          border: '1px solid #c45c4a30', color: '#c45c4a', fontSize: 13,
                          fontFamily: 'var(--font-mono)', whiteSpace: 'pre-wrap', wordBreak: 'break-word',
                        }}>
                          {ev.error_message}
                        </div>
                      </div>
                    )}

                    {hasStack && (
                      <div style={{ marginTop: 12 }}>
                        <div style={{ fontSize: 11, color: '#a8b8c8', fontWeight: 600, marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                          Stack Trace
                        </div>
                        <pre style={{
                          padding: '12px 14px', borderRadius: 6, background: '#0d1b2a',
                          border: '1px solid #1b263b', color: '#a8b8c8', fontSize: 11,
                          fontFamily: 'var(--font-mono)', whiteSpace: 'pre-wrap',
                          wordBreak: 'break-word', maxHeight: 300, overflowY: 'auto',
                          margin: 0, lineHeight: 1.6,
                        }}>
                          {ev.error_stack}
                        </pre>
                      </div>
                    )}

                    {Object.keys(ev.data).length > 0 && (
                      <div style={{ marginTop: 12 }}>
                        <div style={{ fontSize: 11, color: '#a8b8c8', fontWeight: 600, marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                          Event Data
                        </div>
                        <pre style={{
                          padding: '12px 14px', borderRadius: 6, background: '#0d1b2a',
                          border: '1px solid #1b263b', color: '#a8b8c8', fontSize: 11,
                          fontFamily: 'var(--font-mono)', whiteSpace: 'pre-wrap',
                          maxHeight: 200, overflowY: 'auto', margin: 0, lineHeight: 1.5,
                        }}>
                          {JSON.stringify(ev.data, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {events && events.length >= limit && (
        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <button
            onClick={() => setLimit(l => l + 100)}
            style={{
              padding: '8px 20px', borderRadius: 10, fontSize: 13, fontWeight: 500,
              background: 'transparent', color: '#3db8a9', border: '1px solid #3db8a940',
              cursor: 'pointer',
            }}
          >
            Load more events
          </button>
        </div>
      )}

      <style>{`
        @keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }
      `}</style>
    </div>
  )
}

function DetailField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div style={{ fontSize: 11, color: '#a8b8c8', fontWeight: 600, marginBottom: 2, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        {label}
      </div>
      <div style={{
        fontSize: 12, color: '#a8b8c8', fontFamily: 'var(--font-mono)',
        overflow: 'hidden', textOverflow: 'ellipsis',
      }}>
        {value}
      </div>
    </div>
  )
}
