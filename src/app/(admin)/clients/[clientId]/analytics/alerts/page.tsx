'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useClientContext, useAnalyticsApi } from '@/lib/client-context'
import { Bell, CheckCircle, Clock, XCircle } from 'lucide-react'

const SEVERITY_STYLES: Record<string, { bg: string; color: string; label: string }> = {
  critical: { bg: '#3b1a15', color: '#c45c4a', label: 'Critical' },
  warning: { bg: '#3b2a15', color: '#e07a3d', label: 'Warning' },
}

const STATUS_STYLES: Record<string, { bg: string; color: string }> = {
  open: { bg: '#152a40', color: '#3db8a9' },
  acknowledged: { bg: '#1b263b', color: '#a8b8c8' },
  resolved: { bg: '#152a40', color: '#3db8a9' },
  snoozed: { bg: '#152a40', color: '#a8b8c8' },
}

const DETECTOR_LABELS: Record<string, string> = {
  liquidity_shortfall: 'Liquidity',
  concentration_risk: 'Concentration',
  aging_deterioration: 'Aging',
  payable_cliff: 'Payable Cliff',
  sales_decline: 'Sales Decline',
  ccc_stretch: 'CCC Stretch',
}

export default function AlertsPage() {
  const { clientId, companyName } = useClientContext()
  const analyticsClient = useAnalyticsApi()
  const qc = useQueryClient()

  const [statusFilter, setStatusFilter] = useState<'open' | 'all'>('open')
  const [detectorFilter, setDetectorFilter] = useState('')
  const [snoozeAlertId, setSnoozeAlertId] = useState<string | null>(null)
  const [snoozeUntil, setSnoozeUntil] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['analytics-alerts', clientId, statusFilter],
    queryFn: () => analyticsClient!.getAlerts(clientId, statusFilter),
    staleTime: 15_000,
    retry: false,
    enabled: !!analyticsClient,
  })

  const updateMutation = useMutation({
    mutationFn: ({ alertId, status, snoozed_until }: { alertId: string; status: string; snoozed_until?: string }) =>
      analyticsClient!.updateAlert(clientId, alertId, { status: status as 'acknowledged' | 'resolved' | 'snoozed', snoozed_until }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['analytics-alerts', clientId] })
      setSnoozeAlertId(null)
      setSnoozeUntil('')
    },
  })

  const alerts = data?.alerts ?? []
  const filtered = detectorFilter ? alerts.filter(a => a.detector_code === detectorFilter) : alerts
  const detectors = Array.from(new Set(alerts.map(a => a.detector_code)))

  if (!analyticsClient) {
    return (
      <div className="page-enter" style={{ textAlign: 'center', padding: 64 }}>
        <p style={{ color: '#f5f0e8', fontWeight: 600, fontSize: 16 }}>No active devices</p>
        <p style={{ color: '#a8b8c8', fontSize: 14, marginTop: 8 }}>This client needs a registered device before analytics are available.</p>
      </div>
    )
  }

  return (
    <div className="page-enter" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Bell size={22} color='#c45c4a' />
          <h2 style={{ fontWeight: 700, fontSize: 28, color: '#f5f0e8', margin: 0 }}>
            Alerts
          </h2>
          {data && data.total > 0 && (
            <span style={{ padding: '2px 8px', borderRadius: 6, background: '#3b1a15', color: '#c45c4a', fontSize: 12, fontWeight: 700,  }}>
              {data.total}
            </span>
          )}
        </div>
        <p style={{ color: '#a8b8c8', fontSize: 14, marginTop: 4, margin: '4px 0 0' }}>
          Risk alerts for {companyName}
        </p>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {(['open', 'all'] as const).map(s => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            style={{
              padding: '6px 14px', borderRadius: 10, border: '1px solid #2d3e50',
              background: statusFilter === s ? '#3db8a9' : '#1b263b',
              color: statusFilter === s ? '#fff' : '#a8b8c8',
               fontWeight: 500, fontSize: 13,
              cursor: 'pointer', textTransform: 'capitalize',
            }}
          >
            {s === 'open' ? 'Open' : 'All'}
          </button>
        ))}
        <div style={{ width: 1, background: '#2d3e50', margin: '0 4px' }} />
        <select
          value={detectorFilter}
          onChange={e => setDetectorFilter(e.target.value)}
          style={{
            padding: '6px 12px', borderRadius: 10, border: '1px solid #2d3e50',
            background: '#1b263b', color: '#a8b8c8',
             fontSize: 13, cursor: 'pointer',
          }}
        >
          <option value=''>All Detectors</option>
          {detectors.map(d => (
            <option key={d} value={d}>{DETECTOR_LABELS[d] ?? d}</option>
          ))}
        </select>
      </div>

      {/* Alert list */}
      {isLoading ? (
        <div style={{ color: '#2d3e50', padding: 20 }}>Loading alerts…</div>
      ) : filtered.length === 0 ? (
        <div style={{
          padding: '48px 24px', textAlign: 'center', borderRadius: 14,
          background: '#1b263b', border: '1px solid #2d3e50',
        }}>
          <CheckCircle size={40} color='#3db8a9' style={{ marginBottom: 12 }} />
          <div style={{ fontWeight: 600, fontSize: 18, color: '#f5f0e8' }}>All clear</div>
          <div style={{ fontSize: 14, color: '#a8b8c8', marginTop: 4 }}>No alerts match the current filter</div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {filtered.map(alert => (
            <div
              key={alert.alert_id}
              style={{
                background: '#1b263b', borderRadius: 14, padding: '16px 20px',
                border: `1px solid ${alert.severity === 'critical' ? '#3b1a15' : '#2d3e50'}`,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                    <span style={{
                      fontSize: 11, padding: '2px 8px', borderRadius: 4,
                      background: SEVERITY_STYLES[alert.severity]?.bg ?? '#1b263b',
                      color: SEVERITY_STYLES[alert.severity]?.color ?? '#a8b8c8',
                      fontWeight: 700,
                    }}>
                      {SEVERITY_STYLES[alert.severity]?.label ?? alert.severity}
                    </span>
                    <span style={{
                      fontSize: 11, padding: '2px 8px', borderRadius: 4,
                      background: STATUS_STYLES[alert.status]?.bg ?? '#1b263b',
                      color: STATUS_STYLES[alert.status]?.color ?? '#a8b8c8',
                      fontWeight: 600, textTransform: 'capitalize',
                    }}>
                      {alert.status}
                    </span>
                    <span style={{ fontSize: 11, color: '#2d3e50',  }}>
                      {DETECTOR_LABELS[alert.detector_code] ?? alert.detector_code}
                    </span>
                  </div>
                  <div style={{ fontWeight: 600, fontSize: 15, color: '#f5f0e8', marginTop: 8 }}>
                    {alert.title}
                  </div>
                  <div style={{ fontSize: 13, color: '#a8b8c8', marginTop: 4 }}>
                    {alert.description}
                  </div>
                  <div style={{ fontSize: 11, color: '#2d3e50', marginTop: 6 }}>
                    {new Date(alert.created_at).toLocaleString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>

                {alert.status === 'open' && (
                  <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                    <button
                      onClick={() => updateMutation.mutate({ alertId: alert.alert_id, status: 'acknowledged' })}
                      title='Acknowledge'
                      style={{
                        padding: '6px 10px', borderRadius: 7, border: '1px solid #2d3e50',
                        background: '#0d1b2a', color: '#a8b8c8', cursor: 'pointer',
                        display: 'flex', alignItems: 'center', gap: 4,
                         fontSize: 12,
                      }}
                    >
                      <CheckCircle size={13} /> Ack
                    </button>
                    <button
                      onClick={() => setSnoozeAlertId(alert.alert_id)}
                      title='Snooze'
                      style={{
                        padding: '6px 10px', borderRadius: 7, border: '1px solid #2d3e50',
                        background: '#0d1b2a', color: '#a8b8c8', cursor: 'pointer',
                        display: 'flex', alignItems: 'center', gap: 4,
                         fontSize: 12,
                      }}
                    >
                      <Clock size={13} /> Snooze
                    </button>
                    <button
                      onClick={() => updateMutation.mutate({ alertId: alert.alert_id, status: 'resolved' })}
                      title='Resolve'
                      style={{
                        padding: '6px 10px', borderRadius: 7, border: '1px solid #152a40',
                        background: '#152a40', color: '#3db8a9', cursor: 'pointer',
                        display: 'flex', alignItems: 'center', gap: 4,
                         fontSize: 12,
                      }}
                    >
                      <XCircle size={13} /> Resolve
                    </button>
                  </div>
                )}
              </div>

              {/* Snooze picker */}
              {snoozeAlertId === alert.alert_id && (
                <div style={{
                  marginTop: 12, padding: '12px 16px', borderRadius: 10,
                  background: '#0d1b2a', border: '1px solid #2d3e50',
                  display: 'flex', alignItems: 'center', gap: 10,
                }}>
                  <span style={{ fontSize: 13, color: '#a8b8c8' }}>Snooze until:</span>
                  <input
                    type='datetime-local'
                    value={snoozeUntil}
                    onChange={e => setSnoozeUntil(e.target.value)}
                    style={{
                      padding: '4px 8px', borderRadius: 6, border: '1px solid #2d3e50',
                      background: '#1b263b', color: '#f5f0e8',
                      fontSize: 13,
                    }}
                  />
                  <button
                    onClick={() => updateMutation.mutate({ alertId: alert.alert_id, status: 'snoozed', snoozed_until: new Date(snoozeUntil).toISOString() })}
                    disabled={!snoozeUntil}
                    style={{
                      padding: '5px 12px', borderRadius: 6, border: 'none',
                      background: '#3db8a9', color: '#fff', cursor: 'pointer',
                       fontWeight: 600, fontSize: 13,
                    }}
                  >
                    Confirm
                  </button>
                  <button
                    onClick={() => setSnoozeAlertId(null)}
                    style={{
                      padding: '5px 12px', borderRadius: 6, border: '1px solid #2d3e50',
                      background: 'transparent', color: '#a8b8c8', cursor: 'pointer',
                       fontSize: 13,
                    }}
                  >
                    Cancel
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
