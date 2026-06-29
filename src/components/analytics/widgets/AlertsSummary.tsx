'use client'

import { useRouter } from 'next/navigation'
import { Bell } from 'lucide-react'
import type { AlertListResponse } from '@/types/analytics'

export default function AlertsSummary({ data, clientBase, isEditMode, onRemove }: {
  data: AlertListResponse | undefined
  clientBase: string
  isEditMode: boolean
  onRemove: () => void
}) {
  const router = useRouter()
  const critical = data?.alerts.filter(a => a.severity === 'critical').length ?? 0
  const warnings = data?.alerts.filter(a => a.severity === 'warning').length ?? 0
  const total = data?.total ?? 0

  return (
    <div
      style={{
        background: '#1b263b', borderRadius: 14, padding: '20px 24px',
        border: total > 0 ? '1px solid #3b1a15' : '1px solid #2d3e50',
        height: '100%', boxSizing: 'border-box',
        display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
        position: 'relative', cursor: isEditMode ? 'default' : 'pointer',
      }}
      onClick={() => !isEditMode && router.push(`${clientBase}/analytics/alerts`)}
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
        <Bell size={18} color={total > 0 ? '#c45c4a' : '#2d3e50'} />
        <span style={{ fontSize: 11, fontWeight: 600, color: '#a8b8c8', textTransform: 'uppercase', letterSpacing: '0.06em',  }}>
          Open Alerts
        </span>
      </div>
      <div style={{ marginTop: 12 }}>
        <div style={{ fontSize: 32, fontWeight: 700, color: total > 0 ? '#c45c4a' : '#3db8a9', fontFamily: 'var(--font-mono)', lineHeight: 1 }}>
          {total}
        </div>
        {total > 0 && (
          <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
            {critical > 0 && (
              <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 4, background: '#3b1a15', color: '#c45c4a', fontWeight: 600 }}>
                {critical} critical
              </span>
            )}
            {warnings > 0 && (
              <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 4, background: '#3b2a15', color: '#e07a3d', fontWeight: 600 }}>
                {warnings} warning
              </span>
            )}
          </div>
        )}
        {total === 0 && (
          <div style={{ fontSize: 12, color: '#3db8a9', marginTop: 4,  }}>All clear</div>
        )}
      </div>
    </div>
  )
}
