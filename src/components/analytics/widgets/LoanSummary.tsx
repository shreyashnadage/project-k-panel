'use client'

import { useRouter } from 'next/navigation'
import { CreditCard } from 'lucide-react'
import type { LoanRecommendation } from '@/types/analytics'

const CONFIDENCE_COLORS: Record<string, string> = {
  high: '#3db8a9',
  medium: '#e07a3d',
  low: '#a8b8c8',
}

function formatAmount(paise: number): string {
  const inr = paise / 100
  if (inr >= 1e7) return `₹${(inr / 1e7).toFixed(1)}Cr`
  if (inr >= 1e5) return `₹${(inr / 1e5).toFixed(1)}L`
  return `₹${inr.toLocaleString('en-IN')}`
}

export default function LoanSummary({ data, clientBase, isEditMode, onRemove }: {
  data: LoanRecommendation[] | undefined
  clientBase: string
  isEditMode: boolean
  onRemove: () => void
}) {
  const router = useRouter()
  const top = data?.[0]
  const count = data?.length ?? 0

  return (
    <div
      style={{
        background: '#1b263b', borderRadius: 14, padding: '20px 24px',
        border: '1px solid #2d3e50', height: '100%', boxSizing: 'border-box',
        display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
        position: 'relative', cursor: isEditMode ? 'default' : 'pointer',
      }}
      onClick={() => !isEditMode && router.push(`${clientBase}/analytics/loan`)}
    >
      {isEditMode && (
        <button
          onClick={onRemove}
          style={{
            position: 'absolute', top: 8, right: 8,
            width: 22, height: 22, borderRadius: '50%',
            background: '#c45c4a', border: 'none', cursor: 'pointer',
            color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 14, fontWeight: 700, zIndex: 10,
          }}
        >×</button>
      )}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <CreditCard size={18} color='#3db8a9' />
        <span style={{ fontSize: 11, fontWeight: 600, color: '#a8b8c8', textTransform: 'uppercase', letterSpacing: '0.06em',  }}>
          Loan Recs
        </span>
        {count > 0 && (
          <span style={{
            marginLeft: 'auto', fontSize: 10, fontWeight: 700, padding: '1px 6px',
            borderRadius: 10, background: '#152a40', color: '#3db8a9',
          }}>
            {count} product{count !== 1 ? 's' : ''}
          </span>
        )}
      </div>
      {top ? (
        <div style={{ marginTop: 12 }}>
          <div style={{ fontSize: 20, fontWeight: 700, color: '#f5f0e8', fontFamily: 'var(--font-mono)', lineHeight: 1 }}>
            {formatAmount(top.recommended_amount_paise)}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 6 }}>
            <span style={{ fontSize: 12, color: '#a8b8c8',  }}>
              {top.product_type.replace(/_/g, ' ')}
            </span>
            <span style={{
              fontSize: 10, padding: '1px 6px', borderRadius: 4,
              background: '#0d1b2a', color: CONFIDENCE_COLORS[top.confidence] ?? '#a8b8c8',
               fontWeight: 600, textTransform: 'capitalize',
            }}>
              {top.confidence}
            </span>
          </div>
        </div>
      ) : (
        <div style={{ marginTop: 12, fontSize: 14, color: '#2d3e50',  }}>
          No recommendations
        </div>
      )}
    </div>
  )
}
