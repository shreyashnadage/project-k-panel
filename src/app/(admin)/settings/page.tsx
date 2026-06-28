'use client'

import { Settings } from 'lucide-react'

export default function SettingsPage() {
  return (
    <div className="page-enter">
      <h2 style={{ fontFamily: 'Outfit, system-ui', fontWeight: 700, fontSize: 28, color: '#f1f5f9', margin: '0 0 24px' }}>
        Settings
      </h2>
      <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 12 }}>
        <div style={{ textAlign: 'center', padding: '64px 32px' }}>
          <div style={{ color: '#475569', marginBottom: 16, display: 'flex', justifyContent: 'center' }}>
            <Settings size={48} />
          </div>
          <h3 style={{ fontFamily: 'Outfit, system-ui', fontWeight: 600, fontSize: 18, color: '#94a3b8', marginBottom: 8 }}>
            Settings
          </h3>
          <p style={{ color: '#64748b', fontSize: 14 }}>
            Account and system configuration coming soon.
          </p>
        </div>
      </div>
    </div>
  )
}
