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
    active:   { color: '#3db8a9', label: 'Active' },
    inactive: { color: '#a8b8c8', label: 'Inactive' },
    error:    { color: '#c45c4a', label: 'Error' },
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
      background: '#1b263b', border: '1px solid #2d3e50', borderRadius: 14, padding: 24,
      display: 'flex', flexDirection: 'column', gap: 12,
      transition: 'transform 0.2s ease, box-shadow 0.2s ease',
    }}
      onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 8px 24px rgba(0,0,0,0.3)' }}
      onMouseLeave={(e) => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = 'none' }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 40, height: 40, borderRadius: 10, background: '#3db8a920', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Monitor size={20} color="#3db8a9" />
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 15, color: '#f5f0e8' }}>
              {device.device_name}
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: '#a8b8c8', marginTop: 2 }}>
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
            <div style={{ fontSize: 11, color: '#a8b8c8', marginBottom: 2 }}>{label}</div>
            <div style={{ fontSize: 13, color: '#f5f0e8', fontFamily: 'var(--font-mono)' }}>{value}</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
        <button style={{
          flex: 1, padding: '8px', borderRadius: 10, border: '1px solid #2d3e50',
          background: 'transparent', color: '#a8b8c8', fontSize: 13, cursor: 'pointer',
           display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
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
        <h2 style={{ fontWeight: 700, fontSize: 28, color: '#f5f0e8', margin: 0 }}>
          Devices
        </h2>
        <p style={{ color: '#a8b8c8', fontSize: 14, marginTop: 4 }}>
          Windows machines running the Tally Sync agent
        </p>
      </div>

      {isLoading && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 }}>
          {[1, 2].map((i) => (
            <div key={i} style={{ background: '#1b263b', border: '1px solid #2d3e50', borderRadius: 14, padding: 24 }}>
              <div className="skeleton" style={{ height: 40, width: '70%', marginBottom: 16 }} />
              <div className="skeleton" style={{ height: 14, width: '50%', marginBottom: 8 }} />
              <div className="skeleton" style={{ height: 14, width: '60%' }} />
            </div>
          ))}
        </div>
      )}

      {error && (
        <div style={{ background: '#1b263b', border: '1px solid #c45c4a', borderRadius: 14, padding: 24, color: '#c45c4a' }}>
          Could not load devices. Ensure you are authenticated with a valid access token.
        </div>
      )}

      {!isLoading && !error && (!data || data.length === 0) && (
        <div style={{ background: '#1b263b', border: '1px solid #2d3e50', borderRadius: 14, padding: '48px 24px', textAlign: 'center' }}>
          <Monitor size={48} color="#2d3e50" style={{ marginBottom: 12 }} />
          <p style={{ fontWeight: 600, fontSize: 18, color: '#a8b8c8', margin: '0 0 8px' }}>
            No devices registered
          </p>
          <p style={{ color: '#a8b8c8', fontSize: 14 }}>
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
