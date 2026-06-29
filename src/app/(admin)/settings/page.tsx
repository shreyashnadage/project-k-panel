'use client'

import { Settings } from 'lucide-react'

export default function SettingsPage() {
  return (
    <div className="page-enter">
      <h2 style={{ fontWeight: 700, fontSize: 28, color: '#f5f0e8', margin: '0 0 24px' }}>
        Settings
      </h2>
      <div style={{ background: '#1b263b', border: '1px solid #2d3e50', borderRadius: 14 }}>
        <div style={{ textAlign: 'center', padding: '64px 32px' }}>
          <div style={{ color: '#2d3e50', marginBottom: 16, display: 'flex', justifyContent: 'center' }}>
            <Settings size={48} />
          </div>
          <h3 style={{ fontWeight: 600, fontSize: 18, color: '#a8b8c8', marginBottom: 8 }}>
            Settings
          </h3>
          <p style={{ color: '#a8b8c8', fontSize: 14 }}>
            Account and system configuration coming soon.
          </p>
        </div>
      </div>
    </div>
  )
}
