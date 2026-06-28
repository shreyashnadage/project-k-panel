'use client'

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Monitor, RefreshCw } from 'lucide-react'
import type { Device } from '@/types/widgets'

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

function StatusBadge({ status }: { status: Device['status'] }) {
  const map = {
    active:   { color: '#22c55e', label: 'Active' },
    inactive: { color: '#64748b', label: 'Inactive' },
    error:    { color: '#ef4444', label: 'Error' },
  }
  const { color, label } = map[status]
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 6,
      padding: '3px 10px', borderRadius: 20,
      background: `${color}15`, border: `1px solid ${color}40`,
      color, fontSize: 12, fontWeight: 500,
    }}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: color, display: 'inline-block' }} />
      {label}
    </span>
  )
}

function DeviceCard({ device }: { device: Device }) {
  return (
    <div style={{
      background: '#1e293b', border: '1px solid #334155', borderRadius: 12, padding: 24,
      display: 'flex', flexDirection: 'column', gap: 12,
      transition: 'transform 0.2s ease, box-shadow 0.2s ease',
    }}
      onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 8px 24px rgba(0,0,0,0.3)' }}
      onMouseLeave={(e) => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = 'none' }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 40, height: 40, borderRadius: 10, background: '#14b8a620', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Monitor size={20} color="#14b8a6" />
          </div>
          <div>
            <div style={{ fontFamily: 'Outfit, system-ui', fontWeight: 700, fontSize: 15, color: '#f1f5f9' }}>
              {device.device_name}
            </div>
            <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 11, color: '#64748b', marginTop: 2 }}>
              {device.device_id}
            </div>
          </div>
        </div>
        <StatusBadge status={device.status} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
        {[
          ['OS', device.os_version || '—'],
          ['Agent', device.agent_version ? `v${device.agent_version}` : '—'],
          ['Last Sync', formatRelativeTime(device.last_sync_at)],
          ['IP', device.last_ip || '—'],
        ].map(([label, value]) => (
          <div key={label}>
            <div style={{ fontSize: 11, color: '#64748b', marginBottom: 2 }}>{label}</div>
            <div style={{ fontSize: 13, color: '#e2e8f0', fontFamily: 'JetBrains Mono, monospace' }}>{value}</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
        <button style={{
          flex: 1, padding: '8px', borderRadius: 8, border: '1px solid #334155',
          background: 'transparent', color: '#94a3b8', fontSize: 13, cursor: 'pointer',
          fontFamily: 'Inter, system-ui', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
        }}>
          <RefreshCw size={13} /> Rotate Key
        </button>
      </div>
    </div>
  )
}

export default function DevicesPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['devices'],
    queryFn: api.getDevices,
    staleTime: 60_000,
  })

  return (
    <div className="page-enter">
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ fontFamily: 'Outfit, system-ui', fontWeight: 700, fontSize: 28, color: '#f1f5f9', margin: 0 }}>
          Devices
        </h2>
        <p style={{ color: '#64748b', fontSize: 14, marginTop: 4 }}>
          Windows machines running the Tally Sync agent
        </p>
      </div>

      {isLoading && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 }}>
          {[1, 2].map((i) => (
            <div key={i} style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 12, padding: 24 }}>
              <div className="skeleton" style={{ height: 40, width: '70%', marginBottom: 16 }} />
              <div className="skeleton" style={{ height: 14, width: '50%', marginBottom: 8 }} />
              <div className="skeleton" style={{ height: 14, width: '60%' }} />
            </div>
          ))}
        </div>
      )}

      {error && (
        <div style={{ background: '#1e293b', border: '1px solid #ef4444', borderRadius: 12, padding: 24, color: '#f87171' }}>
          Could not load devices. Ensure you are authenticated with a valid access token.
        </div>
      )}

      {!isLoading && !error && (!data || data.length === 0) && (
        <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 12, padding: '48px 24px', textAlign: 'center' }}>
          <Monitor size={48} color="#475569" style={{ marginBottom: 12 }} />
          <p style={{ fontFamily: 'Outfit, system-ui', fontWeight: 600, fontSize: 18, color: '#94a3b8', margin: '0 0 8px' }}>
            No devices registered
          </p>
          <p style={{ color: '#64748b', fontSize: 14 }}>
            Install the agent on your Windows PC to get started.
          </p>
        </div>
      )}

      {!isLoading && data && data.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 }}>
          {data.map((device) => <DeviceCard key={device.device_id} device={device} />)}
        </div>
      )}
    </div>
  )
}
