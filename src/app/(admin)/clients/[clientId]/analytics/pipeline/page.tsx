'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useClientContext, useAnalyticsApi } from '@/lib/client-context'
import { Zap, Play, CheckCircle, XCircle, AlertCircle, Loader } from 'lucide-react'
import type { PipelineRun } from '@/types/analytics'

const STATUS_STYLES: Record<PipelineRun['status'], { icon: React.ReactNode; bg: string; color: string; label: string }> = {
  running: { icon: <Loader size={13} />, bg: '#152a40', color: '#3db8a9', label: 'Running' },
  success: { icon: <CheckCircle size={13} />, bg: '#152a40', color: '#3db8a9', label: 'Success' },
  failed: { icon: <XCircle size={13} />, bg: '#3b1a15', color: '#c45c4a', label: 'Failed' },
  partial: { icon: <AlertCircle size={13} />, bg: '#3b2a15', color: '#e07a3d', label: 'Partial' },
}

const LAYER_LABELS: Record<string, string> = {
  l1_sync: 'L1: Sync',
  l2_normalize: 'L2: Normalize',
  l3_staging: 'L3: Stage',
  l4_analytics: 'L4: Analytics',
  l5_insight: 'L5: Insights',
  l6_action: 'L6: Actions',
  loan_eval: 'Loan Eval',
}

export default function PipelinePage() {
  const { clientId, companyName } = useClientContext()
  const analyticsClient = useAnalyticsApi()
  const qc = useQueryClient()
  const [triggerMessage, setTriggerMessage] = useState('')

  const { data: runs, isLoading } = useQuery({
    queryKey: ['pipeline-runs', clientId],
    queryFn: () => analyticsClient!.getPipelineRuns(clientId),
    staleTime: 5_000,
    enabled: !!analyticsClient,
    refetchInterval: (query) => {
      const data = query.state.data as PipelineRun[] | undefined
      return data?.some(r => r.status === 'running') ? 4_000 : 30_000
    },
    retry: false,
  })

  const triggerMutation = useMutation({
    mutationFn: () => analyticsClient!.triggerPipeline(clientId),
    onSuccess: (res) => {
      setTriggerMessage(res.message ?? 'Pipeline queued')
      qc.invalidateQueries({ queryKey: ['pipeline-runs', clientId] })
      setTimeout(() => setTriggerMessage(''), 5000)
    },
  })

  const hasRunning = runs?.some(r => r.status === 'running') ?? false

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
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Zap size={22} color='#e07a3d' />
            <h2 style={{ fontWeight: 700, fontSize: 28, color: '#f5f0e8', margin: 0 }}>
              Pipeline
            </h2>
            {hasRunning && (
              <span style={{
                display: 'flex', alignItems: 'center', gap: 4,
                padding: '2px 8px', borderRadius: 6, background: '#152a40', color: '#3db8a9',
                fontSize: 12, fontWeight: 700,
                animation: 'pulse 1.5s ease-in-out infinite',
              }}>
                Running
              </span>
            )}
          </div>
          <p style={{ color: '#a8b8c8', fontSize: 14, marginTop: 4, margin: '4px 0 0' }}>
            Analytics pipeline for {companyName}
          </p>
        </div>

        <button
          onClick={() => triggerMutation.mutate()}
          disabled={triggerMutation.isPending || hasRunning}
          style={{
            display: 'flex', alignItems: 'center', gap: 7,
            padding: '10px 20px', borderRadius: 9, border: 'none',
            background: (triggerMutation.isPending || hasRunning) ? '#2d3e50' : 'linear-gradient(135deg, #3db8a9, #2a9d8f)',
            color: (triggerMutation.isPending || hasRunning) ? '#a8b8c8' : '#fff',
            cursor: (triggerMutation.isPending || hasRunning) ? 'not-allowed' : 'pointer',
             fontWeight: 600, fontSize: 14,
          }}
        >
          {triggerMutation.isPending
            ? <Loader size={15} style={{ animation: 'spin 1s linear infinite' }} />
            : <Play size={15} />
          }
          {triggerMutation.isPending ? 'Triggering…' : hasRunning ? 'Already Running' : 'Trigger Run'}
        </button>
      </div>

      {triggerMessage && (
        <div style={{
          padding: '10px 16px', borderRadius: 10,
          background: '#152a40', border: '1px solid #3db8a9',
          color: '#3db8a9', fontSize: 13,
        }}>
          {triggerMessage}
        </div>
      )}

      {/* Pipeline architecture hint */}
      <div style={{
        display: 'flex', gap: 0, background: '#1b263b', borderRadius: 10,
        border: '1px solid #2d3e50', overflow: 'hidden',
      }}>
        {['L1 Sync', 'L2 Normalize', 'L3 Stage', 'L4 Analytics', 'L5 Insights', 'L6 Actions'].map((label, i, arr) => (
          <div
            key={label}
            style={{
              flex: 1, padding: '8px 6px', textAlign: 'center',
               fontSize: 11, fontWeight: 600, color: '#2d3e50',
              borderRight: i < arr.length - 1 ? '1px solid #2d3e50' : 'none',
            }}
          >
            {label}
          </div>
        ))}
      </div>

      {/* Run history */}
      <div>
        <div style={{ fontWeight: 600, fontSize: 13, color: '#a8b8c8', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 10 }}>
          Recent Runs
        </div>

        {isLoading ? (
          <div style={{ color: '#2d3e50', padding: 20 }}>Loading run history…</div>
        ) : !runs || runs.length === 0 ? (
          <div style={{
            padding: '36px 24px', textAlign: 'center', borderRadius: 14,
            background: '#1b263b', border: '1px solid #2d3e50', color: '#2d3e50',
             fontSize: 14,
          }}>
            No pipeline runs yet. Trigger one above.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {runs.map(run => {
              const st = STATUS_STYLES[run.status]
              return (
                <div
                  key={run.run_id}
                  style={{
                    background: '#1b263b', borderRadius: 10, padding: '14px 18px',
                    border: `1px solid ${run.status === 'failed' ? '#3b1a15' : '#2d3e50'}`,
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{
                        display: 'flex', alignItems: 'center', gap: 4,
                        padding: '3px 9px', borderRadius: 5,
                        background: st.bg, color: st.color,
                        fontSize: 11, fontWeight: 700,
                      }}>
                        {st.icon} {st.label}
                      </span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: '#2d3e50' }}>
                        {run.run_id.slice(0, 8)}…
                      </span>
                      {run.layer_reached && (
                        <span style={{ fontSize: 11, color: '#2d3e50',  }}>
                          reached {LAYER_LABELS[run.layer_reached] ?? run.layer_reached}
                        </span>
                      )}
                    </div>
                    <span style={{ fontSize: 12, color: '#2d3e50' }}>
                      {new Date(run.started_at).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
                      {run.finished_at && (
                        <> · {Math.round((new Date(run.finished_at).getTime() - new Date(run.started_at).getTime()) / 1000)}s</>
                      )}
                    </span>
                  </div>

                  <div style={{ display: 'flex', gap: 16, marginTop: 10, flexWrap: 'wrap' }}>
                    <span style={{ fontSize: 12, color: '#a8b8c8' }}>
                      <span style={{ color: '#f5f0e8', fontWeight: 600 }}>{run.vouchers_pulled}</span> vouchers
                    </span>
                    <span style={{ fontSize: 12, color: '#a8b8c8' }}>
                      <span style={{ color: '#f5f0e8', fontWeight: 600 }}>{run.metrics_computed}</span> metrics
                    </span>
                    <span style={{ fontSize: 12, color: '#a8b8c8' }}>
                      <span style={{ color: run.alerts_raised > 0 ? '#c45c4a' : '#f5f0e8', fontWeight: 600 }}>{run.alerts_raised}</span> alerts
                    </span>
                  </div>

                  {run.error_message && (
                    <div style={{
                      marginTop: 10, padding: '8px 12px', borderRadius: 6,
                      background: '#0d1b2a', border: '1px solid #3b1a15',
                      fontFamily: 'var(--font-mono)', fontSize: 12, color: '#c45c4a',
                    }}>
                      {run.error_message}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      <style>{`
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  )
}
