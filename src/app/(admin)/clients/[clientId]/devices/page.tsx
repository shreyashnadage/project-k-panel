'use client'

import { useClientContext } from '@/lib/client-context'
import { Monitor } from 'lucide-react'
import type { ClientDeviceInfo } from '@/types/widgets'

const C = {
  navyMuted:  '#1b263b',
  borderDark: '#2d3e50',
  tealDark:   '#3db8a9',
  cream:      '#f5f0e8',
  textSec:    '#a8b8c8',
  error:      '#c45c4a',
}

function formatRelativeTime(iso: string | null): string {
  if (!iso) return 'Never'
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins} min ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { color: string; label: string }> = {
    active:   { color: '#3db8a9', label: 'Active' },
    inactive: { color: '#a8b8c8', label: 'Inactive' },
    revoked:  { color: '#c45c4a', label: 'Revoked' },
  }
  const { color, label } = map[status] ?? { color: '#a8b8c8', label: status }
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 6,
      padding: '3px 10px', borderRadius: 20, background: `${color}15`,
      border: `1px solid ${color}40`, color, fontSize: 12, fontWeight: 500,
    }}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: color, display: 'inline-block' }} />
      {label}
    </span>
  )
}

function DeviceCard({ device }: { device: ClientDeviceInfo }) {
  return (
    <div style={{
      background: C.navyMuted, border: `1px solid ${C.borderDark}`, borderRadius: 14, padding: 24,
      display: 'flex', flexDirection: 'column', gap: 12,
      transition: 'transform 0.2s ease, box-shadow 0.2s ease',
    }}
      onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 8px 24px rgba(0,0,0,0.3)' }}
      onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = 'none' }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 40, height: 40, borderRadius: 10, background: `${C.tealDark}20`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Monitor size={20} color={C.tealDark} />
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 15, color: C.cream }}>{device.device_name}</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: C.textSec, marginTop: 2 }}>{device.device_id}</div>
          </div>
        </div>
        <StatusBadge status={device.status} />
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
        {([
          ['OS', device.os_version || '—'],
          ['Agent', device.agent_version ? `v${device.agent_version}` : '—'],
          ['Last Sync', formatRelativeTime(device.last_sync_at)],
          ['Registered', device.registered_at ? new Date(device.registered_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: '2-digit' }) : '—'],
        ] as const).map(([label, value]) => (
          <div key={label}>
            <div style={{ fontSize: 11, color: C.textSec, marginBottom: 2 }}>{label}</div>
            <div style={{ fontSize: 13, color: C.cream, fontFamily: 'var(--font-mono)' }}>{value}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function DevicesPage() {
  const { companyName, devices, isLoading } = useClientContext()

  return (
    <div className="page-enter">
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ fontWeight: 700, fontSize: 28, color: C.cream, margin: 0 }}>Devices</h2>
        <p style={{ color: C.textSec, fontSize: 14, marginTop: 4 }}>Machines running the Munimco sync agent for {companyName}</p>
      </div>

      {isLoading && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 }}>
          {[1, 2].map(i => (
            <div key={i} style={{ background: C.navyMuted, border: `1px solid ${C.borderDark}`, borderRadius: 14, padding: 24 }}>
              <div className="skeleton" style={{ height: 40, width: '70%', marginBottom: 16 }} />
              <div className="skeleton" style={{ height: 14, width: '50%' }} />
            </div>
          ))}
        </div>
      )}

      {!isLoading && devices.length === 0 && (
        <div style={{ background: C.navyMuted, border: `1px solid ${C.borderDark}`, borderRadius: 14, padding: '48px 24px', textAlign: 'center' }}>
          <Monitor size={48} color={C.borderDark} style={{ marginBottom: 12 }} />
          <p style={{ fontWeight: 600, fontSize: 18, color: C.textSec, margin: '0 0 8px' }}>No devices registered</p>
          <p style={{ color: C.textSec, fontSize: 14, opacity: 0.7 }}>This client has not registered any agent devices yet.</p>
        </div>
      )}

      {!isLoading && devices.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 }}>
          {devices.map(d => <DeviceCard key={d.device_id} device={d} />)}
        </div>
      )}
    </div>
  )
}
