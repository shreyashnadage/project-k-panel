'use client'

import { useRouter } from 'next/navigation'
import { Lightbulb } from 'lucide-react'
import type { InsightListResponse } from '@/types/analytics'

export default function InsightsSummary({ data, clientBase, isEditMode, onRemove }: {
  data: InsightListResponse | undefined
  clientBase: string
  isEditMode: boolean
  onRemove: () => void
}) {
  const router = useRouter()
  const unread = data?.insights.filter(i => !i.is_read).length ?? 0
  const total = data?.total ?? 0

  return (
    <div
      style={{
        background: '#1b263b', borderRadius: 14, padding: '20px 24px',
        border: '1px solid #2d3e50', height: '100%', boxSizing: 'border-box',
        display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
        position: 'relative', cursor: isEditMode ? 'default' : 'pointer',
      }}
      onClick={() => !isEditMode && router.push(`${clientBase}/analytics/insights`)}
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
        <Lightbulb size={18} color='#e07a3d' />
        <span style={{ fontSize: 11, fontWeight: 600, color: '#a8b8c8', textTransform: 'uppercase', letterSpacing: '0.06em',  }}>
          Insights
        </span>
        {unread > 0 && (
          <span style={{
            marginLeft: 'auto', fontSize: 10, fontWeight: 700, padding: '1px 6px',
            borderRadius: 10, background: '#3db8a9', color: '#fff',
          }}>
            {unread} new
          </span>
        )}
      </div>
      <div style={{ marginTop: 12 }}>
        <div style={{ fontSize: 32, fontWeight: 700, color: '#f5f0e8', fontFamily: 'var(--font-mono)', lineHeight: 1 }}>
          {total}
        </div>
        <div style={{ fontSize: 12, color: '#2d3e50', marginTop: 4,  }}>
          {unread > 0 ? `${unread} unread` : 'All read'}
        </div>
      </div>
    </div>
  )
}
