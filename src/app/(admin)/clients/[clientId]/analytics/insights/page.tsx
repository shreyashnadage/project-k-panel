'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useClientContext, useAnalyticsApi } from '@/lib/client-context'
import { Lightbulb, CheckCircle } from 'lucide-react'

const CATEGORY_COLORS: Record<string, { bg: string; color: string }> = {
  cash_flow: { bg: '#152a40', color: '#3db8a9' },
  receivables: { bg: '#152a40', color: '#3db8a9' },
  payables: { bg: '#152a40', color: '#a8b8c8' },
  working_capital: { bg: '#3b2a15', color: '#e07a3d' },
  inventory: { bg: '#152a40', color: '#3db8a9' },
}

const SEVERITY_STYLES: Record<string, { bg: string; color: string }> = {
  critical: { bg: '#3b1a15', color: '#c45c4a' },
  warning: { bg: '#3b2a15', color: '#e07a3d' },
  info: { bg: '#1b263b', color: '#a8b8c8' },
}

export default function InsightsPage() {
  const { clientId, companyName } = useClientContext()
  const analyticsClient = useAnalyticsApi()
  const qc = useQueryClient()

  const [categoryFilter, setCategoryFilter] = useState('')
  const [severityFilter, setSeverityFilter] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['analytics-insights', clientId],
    queryFn: () => analyticsClient!.getInsights(clientId),
    staleTime: 60_000,
    retry: false,
    enabled: !!analyticsClient,
  })

  const markReadMutation = useMutation({
    mutationFn: (insightId: string) => analyticsClient!.markInsightRead(clientId, insightId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['analytics-insights', clientId] }),
  })

  const insights = data?.insights ?? []
  const unread = insights.filter(i => !i.is_read).length
  const categories = Array.from(new Set(insights.map(i => i.category)))
  const severities = Array.from(new Set(insights.map(i => i.severity)))

  const filtered = insights.filter(i => {
    if (categoryFilter && i.category !== categoryFilter) return false
    if (severityFilter && i.severity !== severityFilter) return false
    return true
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
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Lightbulb size={22} color='#e07a3d' />
          <h2 style={{ fontWeight: 700, fontSize: 28, color: '#f5f0e8', margin: 0 }}>
            Insights
          </h2>
          {unread > 0 && (
            <span style={{ padding: '2px 8px', borderRadius: 6, background: '#3db8a9', color: '#fff', fontSize: 12, fontWeight: 700,  }}>
              {unread} new
            </span>
          )}
        </div>
        <p style={{ color: '#a8b8c8', fontSize: 14, marginTop: 4, margin: '4px 0 0' }}>
          AI-generated findings for {companyName}
        </p>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <select
          value={categoryFilter}
          onChange={e => setCategoryFilter(e.target.value)}
          style={{
            padding: '6px 12px', borderRadius: 10, border: '1px solid #2d3e50',
            background: '#1b263b', color: '#a8b8c8',
             fontSize: 13, cursor: 'pointer',
          }}
        >
          <option value=''>All Categories</option>
          {categories.map(c => (
            <option key={c} value={c} style={{ textTransform: 'capitalize' }}>{c.replace(/_/g, ' ')}</option>
          ))}
        </select>
        <select
          value={severityFilter}
          onChange={e => setSeverityFilter(e.target.value)}
          style={{
            padding: '6px 12px', borderRadius: 10, border: '1px solid #2d3e50',
            background: '#1b263b', color: '#a8b8c8',
             fontSize: 13, cursor: 'pointer',
          }}
        >
          <option value=''>All Severities</option>
          {severities.map(s => (
            <option key={s} value={s} style={{ textTransform: 'capitalize' }}>{s}</option>
          ))}
        </select>
        {unread > 0 && (
          <button
            onClick={() => insights.filter(i => !i.is_read).forEach(i => markReadMutation.mutate(i.insight_id))}
            style={{
              padding: '6px 14px', borderRadius: 10, border: '1px solid #2d3e50',
              background: '#1b263b', color: '#a8b8c8', cursor: 'pointer',
               fontWeight: 500, fontSize: 13,
              marginLeft: 'auto',
            }}
          >
            Mark all read
          </button>
        )}
      </div>

      {/* Insight cards */}
      {isLoading ? (
        <div style={{ color: '#2d3e50', padding: 20 }}>Loading insights…</div>
      ) : filtered.length === 0 ? (
        <div style={{
          padding: '48px 24px', textAlign: 'center', borderRadius: 14,
          background: '#1b263b', border: '1px solid #2d3e50',
        }}>
          <CheckCircle size={40} color='#3db8a9' style={{ marginBottom: 12 }} />
          <div style={{ fontWeight: 600, fontSize: 18, color: '#f5f0e8' }}>No insights</div>
          <div style={{ fontSize: 14, color: '#a8b8c8', marginTop: 4 }}>
            Run the analytics pipeline to generate insights
          </div>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: 12 }}>
          {filtered.map(insight => (
            <div
              key={insight.insight_id}
              style={{
                background: '#1b263b', borderRadius: 14, padding: '16px 20px',
                border: `1px solid ${insight.is_read ? '#2d3e50' : '#2d3e50'}`,
                position: 'relative',
              }}
            >
              {!insight.is_read && (
                <div style={{
                  position: 'absolute', top: 12, right: 12,
                  width: 8, height: 8, borderRadius: '50%', background: '#3db8a9',
                }} />
              )}

              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 10 }}>
                <span style={{
                  fontSize: 10, padding: '2px 7px', borderRadius: 4,
                  background: CATEGORY_COLORS[insight.category]?.bg ?? '#1b263b',
                  color: CATEGORY_COLORS[insight.category]?.color ?? '#a8b8c8',
                  fontWeight: 600, textTransform: 'capitalize',
                }}>
                  {insight.category.replace(/_/g, ' ')}
                </span>
                <span style={{
                  fontSize: 10, padding: '2px 7px', borderRadius: 4,
                  background: SEVERITY_STYLES[insight.severity]?.bg ?? '#1b263b',
                  color: SEVERITY_STYLES[insight.severity]?.color ?? '#a8b8c8',
                  fontWeight: 600, textTransform: 'capitalize',
                }}>
                  {insight.severity}
                </span>
              </div>

              <div style={{ fontWeight: 600, fontSize: 14, color: '#f5f0e8', marginBottom: 6 }}>
                {insight.title}
              </div>
              <div style={{ fontSize: 13, color: '#a8b8c8', lineHeight: 1.6 }}>
                {insight.body}
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 12 }}>
                <span style={{ fontSize: 11, color: '#2d3e50',  }}>
                  {new Date(insight.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}
                </span>
                {!insight.is_read && (
                  <button
                    onClick={() => markReadMutation.mutate(insight.insight_id)}
                    style={{
                      padding: '3px 10px', borderRadius: 5, border: '1px solid #2d3e50',
                      background: 'transparent', color: '#a8b8c8', cursor: 'pointer',
                       fontSize: 11,
                    }}
                  >
                    Mark read
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
