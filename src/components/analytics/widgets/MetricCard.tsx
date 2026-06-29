'use client'

import type { MetricValue } from '@/types/analytics'

const METRIC_META: Record<string, { label: string; description: string; thresholds?: { warn: number; crit: number }; higherIsBetter?: boolean }> = {
  'receivables.dso': { label: 'DSO', description: 'Days Sales Outstanding', thresholds: { warn: 45, crit: 60 } },
  'payables.dpo': { label: 'DPO', description: 'Days Payable Outstanding', thresholds: { warn: 15, crit: 7 }, higherIsBetter: true },
  'inventory.dio': { label: 'DIO', description: 'Days Inventory Outstanding', thresholds: { warn: 60, crit: 90 } },
  'working_capital.ccc': { label: 'CCC', description: 'Cash Conversion Cycle', thresholds: { warn: 45, crit: 75 } },
  'cash_flow.fcf': { label: 'FCF', description: 'Free Cash Flow', higherIsBetter: true },
  'working_capital.nwc': { label: 'NWC', description: 'Net Working Capital', higherIsBetter: true },
  'revenue.growth': { label: 'Revenue Growth', description: 'Revenue Growth Rate', thresholds: { warn: 0, crit: -10 }, higherIsBetter: true },
}

function formatValue(metric: MetricValue): string {
  if (metric.value_numeric === null) return '—'
  const v = metric.value_numeric
  switch (metric.unit) {
    case 'days': return `${v.toFixed(1)}d`
    case 'percent': return `${v.toFixed(1)}%`
    case 'inr_paise': {
      const inr = v / 100
      if (Math.abs(inr) >= 1e7) return `₹${(inr / 1e7).toFixed(1)}Cr`
      if (Math.abs(inr) >= 1e5) return `₹${(inr / 1e5).toFixed(1)}L`
      return `₹${inr.toLocaleString('en-IN')}`
    }
    case 'ratio': return v.toFixed(2)
    default: return v.toFixed(1)
  }
}

function getSeverityColor(metric: MetricValue): string {
  const meta = METRIC_META[metric.metric_code]
  if (!meta?.thresholds || metric.value_numeric === null) return '#3db8a9'
  const v = metric.value_numeric
  const { warn, crit } = meta.thresholds
  const higher = meta.higherIsBetter ?? false
  if (higher) {
    if (v <= crit) return '#c45c4a'
    if (v <= warn) return '#e07a3d'
    return '#3db8a9'
  } else {
    if (v >= crit) return '#c45c4a'
    if (v >= warn) return '#e07a3d'
    return '#3db8a9'
  }
}

export default function MetricCard({ metric, isEditMode, onRemove }: {
  metric: MetricValue
  isEditMode: boolean
  onRemove: () => void
}) {
  const meta = METRIC_META[metric.metric_code] ?? { label: metric.metric_code, description: '' }
  const color = getSeverityColor(metric)
  const formatted = formatValue(metric)

  return (
    <div style={{
      background: '#1b263b', borderRadius: 14, padding: '20px 24px',
      border: '1px solid #2d3e50', height: '100%', boxSizing: 'border-box',
      display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
      position: 'relative', overflow: 'hidden',
    }}>
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
      <div style={{ borderLeft: `3px solid ${color}`, paddingLeft: 12 }}>
        <div style={{ fontSize: 11, fontWeight: 600, color: '#a8b8c8', textTransform: 'uppercase', letterSpacing: '0.06em',  }}>
          {meta.label}
        </div>
        <div style={{ fontSize: 28, fontWeight: 700, color: '#f5f0e8', fontFamily: 'var(--font-mono)', marginTop: 6, lineHeight: 1 }}>
          {formatted}
        </div>
      </div>
      <div style={{ fontSize: 12, color: '#2d3e50', marginTop: 12 }}>
        {meta.description}
        {metric.period_end && (
          <span style={{ marginLeft: 6, color: '#2d3e50' }}>
            · as of {new Date(metric.period_end).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}
          </span>
        )}
      </div>
    </div>
  )
}
