'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useDashboardStore } from '@/lib/store'
import { adminApi } from '@/lib/api'
import { LogIn } from 'lucide-react'

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
      background: '#0f172a',
    }}>
      <div style={{
        width: 400, background: '#1e293b', border: '1px solid #334155',
        borderRadius: 16, padding: 40,
      }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{
            width: 56, height: 56, borderRadius: 14, margin: '0 auto 16px',
            background: 'linear-gradient(135deg, #14b8a6, #0d9488)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#fff', fontWeight: 800, fontSize: 20,
            fontFamily: 'Outfit, system-ui',
          }}>
            TS
          </div>
          <h1 style={{
            fontFamily: 'Outfit, system-ui', fontWeight: 700, fontSize: 24,
            color: '#f1f5f9', margin: '0 0 4px',
          }}>
            Tally Sync Admin
          </h1>
          <p style={{ color: '#64748b', fontSize: 14 }}>Sign in to the admin console</p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#94a3b8', marginBottom: 6 }}>
              Email
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="admin@company.com"
              style={{
                width: '100%', padding: '10px 14px', borderRadius: 8,
                border: '1px solid #334155', background: '#0f172a', color: '#f1f5f9',
                fontFamily: 'Inter, system-ui', fontSize: 14, outline: 'none',
                boxSizing: 'border-box',
              }}
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#94a3b8', marginBottom: 6 }}>
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Enter password"
              style={{
                width: '100%', padding: '10px 14px', borderRadius: 8,
                border: '1px solid #334155', background: '#0f172a', color: '#f1f5f9',
                fontFamily: 'Inter, system-ui', fontSize: 14, outline: 'none',
                boxSizing: 'border-box',
              }}
            />
          </div>

          {error && (
            <div style={{
              padding: '10px 14px', borderRadius: 8, background: '#ef444420',
              border: '1px solid #ef444440', color: '#f87171', fontSize: 13,
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              padding: '12px', borderRadius: 8, border: 'none',
              background: loading ? '#0d948880' : '#14b8a6',
              color: '#fff', fontFamily: 'Inter, system-ui', fontWeight: 600,
              fontSize: 14, cursor: loading ? 'wait' : 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
              transition: 'background 0.15s',
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
