'use client'

import { useQuery } from '@tanstack/react-query'
import { useClientContext, useAnalyticsApi } from '@/lib/client-context'
import WidgetGrid from '@/components/analytics/WidgetGrid'
import { BarChart3 } from 'lucide-react'

export default function AnalyticsOverviewPage() {
  const { clientId, companyName } = useClientContext()
  const analyticsClient = useAnalyticsApi()
  const clientBase = `/clients/${clientId}`

  const { data: metricSummary, isLoading: loadingMetrics } = useQuery({
    queryKey: ['analytics-metrics', clientId],
    queryFn: () => analyticsClient!.getMetricSummary(clientId),
    staleTime: 60_000,
    retry: false,
    enabled: !!analyticsClient,
  })

  const { data: alerts } = useQuery({
    queryKey: ['analytics-alerts', clientId, 'open'],
    queryFn: () => analyticsClient!.getAlerts(clientId, 'open'),
    staleTime: 30_000,
    retry: false,
    enabled: !!analyticsClient,
  })

  const { data: insights } = useQuery({
    queryKey: ['analytics-insights', clientId],
    queryFn: () => analyticsClient!.getInsights(clientId),
    staleTime: 60_000,
    retry: false,
    enabled: !!analyticsClient,
  })

  const { data: loanRecs } = useQuery({
    queryKey: ['analytics-loan', clientId],
    queryFn: () => analyticsClient!.getLoanRecommendations(clientId),
    staleTime: 120_000,
    retry: false,
    enabled: !!analyticsClient,
  })

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
            <BarChart3 size={22} color='#3db8a9' />
            <h2 style={{ fontWeight: 700, fontSize: 28, color: '#f5f0e8', margin: 0 }}>
              Analytics
            </h2>
          </div>
          <p style={{ color: '#a8b8c8', fontSize: 14, marginTop: 4, margin: '4px 0 0' }}>
            Working capital metrics for {companyName}
            {metricSummary?.computed_at && (
              <span style={{ marginLeft: 8, color: '#2d3e50' }}>
                · Last computed {new Date(metricSummary.computed_at).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
              </span>
            )}
          </p>
        </div>

        {metricSummary?.vertical && (
          <span style={{
            padding: '4px 12px', borderRadius: 6, fontSize: 12, fontWeight: 600,
            background: '#152a40', color: '#3db8a9', border: '1px solid #2d3e50',
             textTransform: 'capitalize',
          }}>
            {metricSummary.vertical}
          </span>
        )}
      </div>

      {loadingMetrics ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
          {Array.from({ length: 8 }).map((_, i) => (
            <div
              key={i}
              style={{
                height: 120, borderRadius: 14, background: '#1b263b',
                border: '1px solid #2d3e50', animation: 'pulse 1.5s ease-in-out infinite',
              }}
            />
          ))}
        </div>
      ) : (
        <WidgetGrid
          clientId={clientId}
          clientBase={clientBase}
          metrics={metricSummary?.metrics ?? []}
          alerts={alerts}
          insights={insights}
          loanRecs={loanRecs}
        />
      )}

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
      `}</style>
    </div>
  )
}
