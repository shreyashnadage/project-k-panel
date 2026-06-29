'use client'

import { useState, useCallback } from 'react'
import { ResponsiveGridLayout, useContainerWidth } from 'react-grid-layout'
import type { LayoutItem } from 'react-grid-layout'
import { Settings2, Plus } from 'lucide-react'
import 'react-grid-layout/css/styles.css'

import MetricCard from './widgets/MetricCard'
import AlertsSummary from './widgets/AlertsSummary'
import InsightsSummary from './widgets/InsightsSummary'
import LoanSummary from './widgets/LoanSummary'
import WidgetTray from './WidgetTray'
import type { MetricValue, AlertListResponse, InsightListResponse, LoanRecommendation } from '@/types/analytics'

export interface WidgetDef {
  id: string
  label: string
  description: string
  defaultW: number
  defaultH: number
}

const ALL_WIDGETS: WidgetDef[] = [
  { id: 'receivables.dso', label: 'DSO', description: 'Days Sales Outstanding', defaultW: 3, defaultH: 2 },
  { id: 'payables.dpo', label: 'DPO', description: 'Days Payable Outstanding', defaultW: 3, defaultH: 2 },
  { id: 'inventory.dio', label: 'DIO', description: 'Days Inventory Outstanding', defaultW: 3, defaultH: 2 },
  { id: 'working_capital.ccc', label: 'CCC', description: 'Cash Conversion Cycle', defaultW: 3, defaultH: 2 },
  { id: 'cash_flow.fcf', label: 'FCF', description: 'Free Cash Flow', defaultW: 3, defaultH: 2 },
  { id: 'working_capital.nwc', label: 'NWC', description: 'Net Working Capital', defaultW: 3, defaultH: 2 },
  { id: 'revenue.growth', label: 'Revenue Growth', description: 'Revenue Growth Rate', defaultW: 3, defaultH: 2 },
  { id: '__alerts', label: 'Alerts Summary', description: 'Open risk alerts count', defaultW: 3, defaultH: 2 },
  { id: '__insights', label: 'Insights Summary', description: 'Unread insight count', defaultW: 3, defaultH: 2 },
  { id: '__loan', label: 'Loan Recommendations', description: 'Top loan product', defaultW: 3, defaultH: 2 },
]

const DEFAULT_VISIBLE = ALL_WIDGETS.map(w => w.id)

function buildItems(visibleIds: string[]): LayoutItem[] {
  return visibleIds.map((id, i) => {
    const def = ALL_WIDGETS.find(w => w.id === id)!
    return { i: id, x: (i % 4) * 3, y: Math.floor(i / 4) * 2, w: def.defaultW, h: def.defaultH, minW: 2, minH: 2 }
  })
}

interface WidgetGridProps {
  clientId: string
  clientBase: string
  metrics: MetricValue[]
  alerts: AlertListResponse | undefined
  insights: InsightListResponse | undefined
  loanRecs: LoanRecommendation[] | undefined
}

export default function WidgetGrid({ clientId, clientBase, metrics, alerts, insights, loanRecs }: WidgetGridProps) {
  const storageKey = `analytics_layout_${clientId}`

  const [visibleIds, setVisibleIds] = useState<string[]>(() => {
    if (typeof window === 'undefined') return DEFAULT_VISIBLE
    try {
      const saved = localStorage.getItem(storageKey)
      if (saved) {
        const parsed = JSON.parse(saved) as { visible: string[]; items: LayoutItem[] }
        return parsed.visible ?? DEFAULT_VISIBLE
      }
    } catch { /* ignore */ }
    return DEFAULT_VISIBLE
  })

  const [items, setItems] = useState<LayoutItem[]>(() => {
    if (typeof window === 'undefined') return buildItems(DEFAULT_VISIBLE)
    try {
      const saved = localStorage.getItem(storageKey)
      if (saved) {
        const parsed = JSON.parse(saved) as { visible: string[]; items: LayoutItem[] }
        return parsed.items ?? buildItems(parsed.visible ?? DEFAULT_VISIBLE)
      }
    } catch { /* ignore */ }
    return buildItems(DEFAULT_VISIBLE)
  })

  const [isEditMode, setIsEditMode] = useState(false)
  const [showTray, setShowTray] = useState(false)

  const persist = useCallback((ids: string[], its: LayoutItem[]) => {
    try {
      localStorage.setItem(storageKey, JSON.stringify({ visible: ids, items: its }))
    } catch { /* ignore */ }
  }, [storageKey])

  // onLayoutChange receives Layout = readonly LayoutItem[], spread to mutable
  const handleLayoutChange = (newLayout: readonly LayoutItem[]) => {
    const next = [...newLayout]
    setItems(next)
    persist(visibleIds, next)
  }

  const removeWidget = (id: string) => {
    const nextIds = visibleIds.filter(v => v !== id)
    const nextItems = items.filter(l => l.i !== id)
    setVisibleIds(nextIds)
    setItems(nextItems)
    persist(nextIds, nextItems)
  }

  const addWidget = (id: string) => {
    const def = ALL_WIDGETS.find(w => w.id === id)!
    const nextIds = [...visibleIds, id]
    const nextItems: LayoutItem[] = [
      ...items,
      { i: id, x: 0, y: Infinity, w: def.defaultW, h: def.defaultH, minW: 2, minH: 2 },
    ]
    setVisibleIds(nextIds)
    setItems(nextItems)
    persist(nextIds, nextItems)
  }

  const metricMap = Object.fromEntries(metrics.map(m => [m.metric_code, m]))
  const hiddenWidgets = ALL_WIDGETS.filter(w => !visibleIds.includes(w.id))
  const { width, containerRef } = useContainerWidth()

  return (
    <div ref={containerRef}>
      {/* Toolbar */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginBottom: 16 }}>
        {isEditMode && (
          <button
            onClick={() => setShowTray(true)}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '7px 14px', borderRadius: 10, border: '1px solid #2d3e50',
              background: '#1b263b', color: '#a8b8c8', cursor: 'pointer',
               fontWeight: 500, fontSize: 13,
            }}
          >
            <Plus size={14} /> Add Widget
          </button>
        )}
        <button
          onClick={() => setIsEditMode(e => !e)}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            padding: '7px 14px', borderRadius: 10, border: '1px solid #2d3e50',
            background: isEditMode ? '#3db8a9' : '#1b263b',
            color: isEditMode ? '#fff' : '#a8b8c8',
            cursor: 'pointer', fontWeight: 500, fontSize: 13,
          }}
        >
          <Settings2 size={14} />
          {isEditMode ? 'Done' : 'Configure Dashboard'}
        </button>
      </div>

      {isEditMode && (
        <div style={{
          padding: '8px 16px', borderRadius: 10, marginBottom: 12,
          background: '#152a40', border: '1px solid #2d3e50',
          fontSize: 13, color: '#3db8a9',
        }}>
          Drag widgets to rearrange · Resize from corners · Click × to remove · Use "Add Widget" to restore hidden ones
        </div>
      )}

      <ResponsiveGridLayout
        className="layout"
        width={width}
        layouts={{ lg: items }}
        breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
        cols={{ lg: 12, md: 9, sm: 6, xs: 4, xxs: 2 }}
        rowHeight={80}
        dragConfig={{ enabled: isEditMode }}
        resizeConfig={{ enabled: isEditMode }}
        onLayoutChange={handleLayoutChange}
        margin={[12, 12]}
      >
        {visibleIds.map(id => (
          <div key={id}>
            {id === '__alerts' ? (
              <AlertsSummary
                data={alerts}
                clientBase={clientBase}
                isEditMode={isEditMode}
                onRemove={() => removeWidget(id)}
              />
            ) : id === '__insights' ? (
              <InsightsSummary
                data={insights}
                clientBase={clientBase}
                isEditMode={isEditMode}
                onRemove={() => removeWidget(id)}
              />
            ) : id === '__loan' ? (
              <LoanSummary
                data={loanRecs}
                clientBase={clientBase}
                isEditMode={isEditMode}
                onRemove={() => removeWidget(id)}
              />
            ) : metricMap[id] ? (
              <MetricCard
                metric={metricMap[id]}
                isEditMode={isEditMode}
                onRemove={() => removeWidget(id)}
              />
            ) : (
              <div style={{
                background: '#1b263b', borderRadius: 14, height: '100%',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                border: '1px dashed #2d3e50', color: '#2d3e50',
                 fontSize: 13,
              }}>
                No data yet
              </div>
            )}
          </div>
        ))}
      </ResponsiveGridLayout>

      {showTray && (
        <WidgetTray
          hidden={hiddenWidgets}
          onAdd={(id) => { addWidget(id); setShowTray(false) }}
          onClose={() => setShowTray(false)}
        />
      )}
    </div>
  )
}
