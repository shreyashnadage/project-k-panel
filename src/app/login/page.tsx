'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useDashboardStore } from '@/lib/store'
import { adminApi } from '@/lib/api'
import { LogIn } from 'lucide-react'

const C = {
  navy:       '#0d1b2a',
  navyMuted:  '#1b263b',
  borderDark: '#2d3e50',
  tealDark:   '#3db8a9',
  cream:      '#f5f0e8',
  textSec:    '#a8b8c8',
  error:      '#c45c4a',
}

export default function LoginPage() {
  const router = useRouter()
  const { setAccessToken, setAdminUser } = useDashboardStore()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const tokens = await adminApi.login(email, password)
      localStorage.setItem('access_token', tokens.access_token)
      setAccessToken(tokens.access_token)

      const me = await adminApi.getMe()
      setAdminUser({ clientId: me.client_id, email: me.email, companyName: me.company_name })
      router.push('/clients')
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Login failed'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: C.navy,
    }}>
      <div style={{
        width: 400, background: C.navyMuted, border: `1px solid ${C.borderDark}`,
        borderRadius: 20, padding: 40,
      }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{
            width: 56, height: 56, borderRadius: 14, margin: '0 auto 16px',
            background: C.tealDark,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: C.navy, fontWeight: 700, fontSize: 22,
          }}>
            Mc
          </div>
          <h1 style={{
            fontWeight: 700, fontSize: 24,
            color: C.cream, margin: '0 0 4px',
          }}>
            <span style={{ color: C.cream }}>Munim</span>
            <span style={{ color: C.tealDark }}>Co</span>
            <span style={{ color: C.cream }}> Panel</span>
          </h1>
          <p style={{ color: C.textSec, fontSize: 14, margin: 0 }}>Sign in to the admin console</p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: C.textSec, marginBottom: 6 }}>
              Email
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="admin@company.com"
              style={{
                width: '100%', padding: '10px 14px', borderRadius: 10,
                border: `1px solid ${C.borderDark}`, background: C.navy, color: C.cream,
                fontSize: 14, outline: 'none', boxSizing: 'border-box',
              }}
              onFocus={e => { e.currentTarget.style.borderColor = C.tealDark; e.currentTarget.style.boxShadow = `0 0 0 2px ${C.tealDark}33` }}
              onBlur={e => { e.currentTarget.style.borderColor = C.borderDark; e.currentTarget.style.boxShadow = 'none' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: C.textSec, marginBottom: 6 }}>
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Enter password"
              style={{
                width: '100%', padding: '10px 14px', borderRadius: 10,
                border: `1px solid ${C.borderDark}`, background: C.navy, color: C.cream,
                fontSize: 14, outline: 'none', boxSizing: 'border-box',
              }}
              onFocus={e => { e.currentTarget.style.borderColor = C.tealDark; e.currentTarget.style.boxShadow = `0 0 0 2px ${C.tealDark}33` }}
              onBlur={e => { e.currentTarget.style.borderColor = C.borderDark; e.currentTarget.style.boxShadow = 'none' }}
            />
          </div>

          {error && (
            <div style={{
              padding: '10px 14px', borderRadius: 10, background: `${C.error}20`,
              border: `1px solid ${C.error}40`, color: C.error, fontSize: 13,
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              padding: '12px', borderRadius: 10, border: 'none',
              background: loading ? `${C.tealDark}80` : C.tealDark,
              color: C.navy, fontWeight: 600,
              fontSize: 14, cursor: loading ? 'wait' : 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
              transition: 'opacity 0.15s',
            }}
          >
            <LogIn size={16} />
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  )
}
