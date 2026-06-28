'use client'

import { Radio } from 'lucide-react'

export default function SyncHistoryPage() {
  return (
    <div className="page-enter">
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ fontFamily: 'Outfit, system-ui', fontWeight: 700, fontSize: 28, color: '#f1f5f9', margin: 0 }}>
          Sync History
        </h2>
        <p style={{ color: '#64748b', fontSize: 14, marginTop: 4 }}>
          Audit log of all synchronisation events
        </p>
      </div>
      <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 12, padding: '48px 24px', textAlign: 'center' }}>
        <Radio size={48} color="#475569" style={{ marginBottom: 12 }} />
        <p style={{ fontFamily: 'Outfit, system-ui', fontWeight: 600, fontSize: 18, color: '#94a3b8', margin: '0 0 8px' }}>
          No sync history yet
        </p>
        <p style={{ color: '#64748b', fontSize: 14 }}>
          Sync logs will appear here once your agent starts running.
        </p>
      </div>
    </div>
  )
}
