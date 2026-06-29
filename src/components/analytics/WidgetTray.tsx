'use client'

import { X } from 'lucide-react'
import type { WidgetDef } from './WidgetGrid'

export default function WidgetTray({ hidden, onAdd, onClose }: {
  hidden: WidgetDef[]
  onAdd: (id: string) => void
  onClose: () => void
}) {
  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
          zIndex: 40,
        }}
      />
      {/* Panel */}
      <div style={{
        position: 'fixed', right: 0, top: 0, bottom: 0, width: 300,
        background: '#0d1b2a', borderLeft: '1px solid #1b263b',
        zIndex: 50, display: 'flex', flexDirection: 'column',
        padding: '24px 20px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
          <h3 style={{ margin: 0, fontWeight: 700, fontSize: 18, color: '#f5f0e8' }}>
            Add Widgets
          </h3>
          <button
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: '#a8b8c8', padding: 4 }}
          >
            <X size={18} />
          </button>
        </div>

        {hidden.length === 0 ? (
          <p style={{ color: '#2d3e50', fontSize: 14 }}>
            All widgets are already on the dashboard.
          </p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {hidden.map(w => (
              <div
                key={w.id}
                style={{
                  background: '#1b263b', borderRadius: 10, padding: '12px 16px',
                  border: '1px solid #2d3e50', display: 'flex', alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, fontSize: 14, color: '#f5f0e8' }}>
                    {w.label}
                  </div>
                  <div style={{ fontSize: 12, color: '#a8b8c8', marginTop: 2 }}>
                    {w.description}
                  </div>
                </div>
                <button
                  onClick={() => onAdd(w.id)}
                  style={{
                    background: '#3db8a9', border: 'none', cursor: 'pointer',
                    color: '#fff', borderRadius: 6, padding: '4px 10px',
                     fontWeight: 600, fontSize: 13,
                    flexShrink: 0, marginLeft: 12,
                  }}
                >
                  Add
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  )
}
