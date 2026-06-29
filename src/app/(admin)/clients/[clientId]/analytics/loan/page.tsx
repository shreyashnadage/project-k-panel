'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useClientContext, useAnalyticsApi } from '@/lib/client-context'
import { CreditCard, ChevronDown, ChevronUp, CheckCircle, XCircle } from 'lucide-react'
import type { LoanEvidenceResponse } from '@/types/analytics'

const CONFIDENCE_STYLES: Record<string, { bg: string; color: string; border: string }> = {
  high: { bg: '#152a40', color: '#3db8a9', border: '#2a9d8f' },
  medium: { bg: '#3b2a15', color: '#e07a3d', border: '#e07a3d' },
  low: { bg: '#1b263b', color: '#a8b8c8', border: '#2d3e50' },
}

function formatAmount(paise: number): string {
  const inr = paise / 100
  if (inr >= 1e7) return `₹${(inr / 1e7).toFixed(2)} Crore`
  if (inr >= 1e5) return `₹${(inr / 1e5).toFixed(2)} Lakh`
  return `₹${inr.toLocaleString('en-IN')}`
}

function EvidencePanel({ recoId, clientId }: { recoId: string; clientId: string }) {
  const analyticsClient = useAnalyticsApi()
  const { data, isLoading } = useQuery<LoanEvidenceResponse>({
    queryKey: ['loan-evidence', clientId, recoId],
    queryFn: () => analyticsClient!.getLoanEvidence(clientId, recoId),
    staleTime: 300_000,
    retry: false,
    enabled: !!analyticsClient,
  })

  if (isLoading) {
    return (
      <div style={{ padding: '16px 0', color: '#2d3e50', fontSize: 13 }}>
        Loading evidence…
      </div>
    )
  }

  return (
    <div style={{ marginTop: 16, borderTop: '1px solid #2d3e50', paddingTop: 16 }}>
      {/* Eligibility rules */}
      {data?.eligibility && data.eligibility.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontWeight: 600, fontSize: 12, color: '#a8b8c8', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>
            Eligibility Criteria
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {data.eligibility.map(rule => (
              <div
                key={rule.rule_code}
                style={{
                  display: 'flex', alignItems: 'flex-start', gap: 8, padding: '8px 12px',
                  borderRadius: 7, background: '#0d1b2a',
                  border: `1px solid ${rule.passed ? '#152a40' : '#3b1a15'}`,
                }}
              >
                {rule.passed
                  ? <CheckCircle size={14} color='#3db8a9' style={{ flexShrink: 0, marginTop: 1 }} />
                  : <XCircle size={14} color='#c45c4a' style={{ flexShrink: 0, marginTop: 1 }} />
                }
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, fontSize: 13, color: '#f5f0e8' }}>
                    {rule.rule_name}
                  </div>
                  <div style={{ fontSize: 12, color: '#a8b8c8', marginTop: 2 }}>
                    {rule.detail}
                  </div>
                </div>
                {rule.weight > 0 && (
                  <span style={{ fontSize: 11, color: '#2d3e50', flexShrink: 0 }}>
                    ×{rule.weight}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Evidence */}
      {data?.evidence && data.evidence.length > 0 && (
        <div>
          <div style={{ fontWeight: 600, fontSize: 12, color: '#a8b8c8', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>
            Supporting Evidence
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {data.evidence.map((ev, i) => (
              <div
                key={i}
                style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '6px 12px', borderRadius: 6, background: '#0d1b2a',
                }}
              >
                <span style={{ fontSize: 12, color: '#a8b8c8' }}>
                  {ev.description}
                </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: '#3db8a9' }}>
                  {typeof ev.value === 'number' ? ev.value.toFixed(2) : String(ev.value)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default function LoanPage() {
  const { clientId, companyName } = useClientContext()
  const analyticsClient = useAnalyticsApi()
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const { data: recs, isLoading } = useQuery({
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
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <CreditCard size={22} color='#3db8a9' />
          <h2 style={{ fontWeight: 700, fontSize: 28, color: '#f5f0e8', margin: 0 }}>
            Loan Recommendations
          </h2>
        </div>
        <p style={{ color: '#a8b8c8', fontSize: 14, marginTop: 4, margin: '4px 0 0' }}>
          Working capital products for {companyName}
        </p>
      </div>

      {isLoading ? (
        <div style={{ color: '#2d3e50', padding: 20 }}>Loading recommendations…</div>
      ) : !recs || recs.length === 0 ? (
        <div style={{
          padding: '48px 24px', textAlign: 'center', borderRadius: 14,
          background: '#1b263b', border: '1px solid #2d3e50',
        }}>
          <CreditCard size={40} color='#2d3e50' style={{ marginBottom: 12 }} />
          <div style={{ fontWeight: 600, fontSize: 18, color: '#f5f0e8' }}>No recommendations</div>
          <div style={{ fontSize: 14, color: '#a8b8c8', marginTop: 4 }}>
            Run the analytics pipeline to generate loan recommendations
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {recs.map(rec => {
            const conf = CONFIDENCE_STYLES[rec.confidence] ?? CONFIDENCE_STYLES.low
            const expanded = expandedId === rec.reco_id
            return (
              <div
                key={rec.reco_id}
                style={{
                  background: '#1b263b', borderRadius: 14,
                  border: `1px solid ${conf.border}`,
                  overflow: 'hidden',
                }}
              >
                <div style={{ padding: '20px 24px' }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                        <span style={{ fontWeight: 700, fontSize: 15, color: '#f5f0e8', textTransform: 'capitalize' }}>
                          {rec.product_type.replace(/_/g, ' ')}
                        </span>
                        <span style={{
                          fontSize: 11, padding: '2px 8px', borderRadius: 4,
                          background: conf.bg, color: conf.color,
                          fontWeight: 700, textTransform: 'capitalize',
                        }}>
                          {rec.confidence} confidence
                        </span>
                      </div>
                      <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 24, color: '#3db8a9', marginBottom: 8 }}>
                        {formatAmount(rec.recommended_amount_paise)}
                      </div>
                      <div style={{ fontSize: 13, color: '#a8b8c8', lineHeight: 1.6 }}>
                        {rec.rationale}
                      </div>
                    </div>
                  </div>

                  {rec.valid_until && (
                    <div style={{ marginTop: 10, fontSize: 11, color: '#2d3e50',  }}>
                      Valid until {new Date(rec.valid_until).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                    </div>
                  )}

                  <button
                    onClick={() => setExpandedId(expanded ? null : rec.reco_id)}
                    style={{
                      marginTop: 12, display: 'flex', alignItems: 'center', gap: 4,
                      padding: '5px 0', border: 'none', background: 'transparent',
                      color: '#3db8a9', cursor: 'pointer',
                       fontWeight: 500, fontSize: 13,
                    }}
                  >
                    {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                    {expanded ? 'Hide' : 'View'} eligibility & evidence
                  </button>
                </div>

                {expanded && (
                  <div style={{ padding: '0 24px 20px' }}>
                    <EvidencePanel recoId={rec.reco_id} clientId={clientId} />
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
