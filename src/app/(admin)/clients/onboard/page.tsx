'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { adminApi } from '@/lib/api'
import { ArrowLeft, Building2, Mail, Phone, Hash, Check, Copy, Key, AlertCircle } from 'lucide-react'

type Step = 'form' | 'success'

interface OnboardResult {
  client_id: string
  company_name: string
  email: string
  status: string
  plan: string
  installation_key: string
  key_expires_at: string
}

export default function OnboardClientPage() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const [step, setStep] = useState<Step>('form')
  const [result, setResult] = useState<OnboardResult | null>(null)
  const [copied, setCopied] = useState(false)

  const [form, setForm] = useState({
    company_name: '',
    email: '',
    phone: '',
    gst_id: '',
    plan: 'trial',
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  const mutation = useMutation({
    mutationFn: () => adminApi.onboardClient({
      company_name: form.company_name,
      email: form.email,
      phone: form.phone || undefined,
      gst_id: form.gst_id || undefined,
      plan: form.plan,
    }),
    onSuccess: (data) => {
      setResult(data)
      setStep('success')
      queryClient.invalidateQueries({ queryKey: ['admin-clients'] })
    },
  })

  const validate = (): boolean => {
    const e: Record<string, string> = {}
    if (!form.company_name.trim() || form.company_name.trim().length < 3) e.company_name = 'Company name must be at least 3 characters'
    if (!form.email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = 'Enter a valid email address'
    if (form.gst_id && form.gst_id.length !== 15) e.gst_id = 'GST number must be 15 characters'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (validate()) mutation.mutate()
  }

  const copyKey = () => {
    if (result) {
      navigator.clipboard.writeText(result.installation_key)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const inputStyle = (field: string) => ({
    width: '100%',
    padding: '12px 14px 12px 40px',
    borderRadius: 10,
    border: `1px solid ${errors[field] ? '#c45c4a' : '#2d3e50'}`,
    background: '#0d1b2a',
    color: '#f5f0e8',
    
    fontSize: 14,
    outline: 'none',
    transition: 'border-color 0.15s',
    boxSizing: 'border-box' as const,
  })

  if (step === 'success' && result) {
    return (
      <div className="page-enter" style={{ maxWidth: 560, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 24 }}>
        <div style={{ textAlign: 'center', padding: '12px 0' }}>
          <div style={{
            width: 64, height: 64, borderRadius: 16, background: '#3db8a920',
            display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px',
          }}>
            <Check size={32} color="#3db8a9" />
          </div>
          <h2 style={{ fontWeight: 700, fontSize: 24, color: '#f5f0e8', margin: '0 0 4px' }}>
            Client Onboarded
          </h2>
          <p style={{ color: '#a8b8c8', fontSize: 14 }}>
            {result.company_name} is ready. Share the installation key below.
          </p>
        </div>

        {/* Installation Key Card */}
        <div style={{
          background: '#1b263b', border: '2px solid #3db8a940', borderRadius: 14, padding: 24,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <Key size={16} color="#3db8a9" />
            <span style={{ fontWeight: 600, fontSize: 13, color: '#a8b8c8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Installation Key
            </span>
          </div>

          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12,
            background: '#0d1b2a', borderRadius: 10, padding: '14px 16px', border: '1px solid #2d3e50',
          }}>
            <code style={{
              fontFamily: 'var(--font-mono)', fontSize: 20, fontWeight: 700,
              color: '#3db8a9', letterSpacing: '0.08em',
            }}>
              {result.installation_key}
            </code>
            <button
              onClick={copyKey}
              style={{
                padding: '8px 14px', borderRadius: 6, border: '1px solid #2d3e50',
                background: copied ? '#3db8a920' : '#1b263b',
                color: copied ? '#3db8a9' : '#a8b8c8',
                cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6,
                fontSize: 13, fontWeight: 500, transition: 'all 0.15s', flexShrink: 0,
              }}
            >
              {copied ? <Check size={14} /> : <Copy size={14} />}
              {copied ? 'Copied' : 'Copy'}
            </button>
          </div>

          <div style={{ marginTop: 14, display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
              <span style={{ color: '#a8b8c8' }}>Expires</span>
              <span style={{ color: '#a8b8c8', fontFamily: 'var(--font-mono)' }}>
                {new Date(result.key_expires_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
              <span style={{ color: '#a8b8c8' }}>Client ID</span>
              <span style={{ color: '#a8b8c8', fontFamily: 'var(--font-mono)' }}>{result.client_id}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
              <span style={{ color: '#a8b8c8' }}>Plan</span>
              <span style={{ color: '#a8b8c8', textTransform: 'capitalize' }}>{result.plan}</span>
            </div>
          </div>
        </div>

        {/* Instructions */}
        <div style={{ background: '#1b263b', border: '1px solid #2d3e50', borderRadius: 14, padding: 20 }}>
          <h3 style={{ fontWeight: 600, fontSize: 15, color: '#f5f0e8', margin: '0 0 12px' }}>
            Next Steps
          </h3>
          <ol style={{ margin: 0, paddingLeft: 20, display: 'flex', flexDirection: 'column', gap: 8, color: '#a8b8c8', fontSize: 13, lineHeight: 1.5 }}>
            <li>Download the Tally Sync Agent installer (.exe)</li>
            <li>Run the installer on the client's Windows machine where TallyPrime is installed</li>
            <li>Enter the installation key <strong style={{ color: '#3db8a9' }}>{result.installation_key}</strong> when prompted</li>
            <li>The agent will register and begin syncing data automatically</li>
          </ol>
        </div>

        <div style={{ display: 'flex', gap: 12 }}>
          <button
            onClick={() => router.push('/clients')}
            style={{
              flex: 1, padding: '12px', borderRadius: 10, border: '1px solid #2d3e50',
              background: '#1b263b', color: '#f5f0e8', cursor: 'pointer',
               fontSize: 14, fontWeight: 500,
            }}
          >
            Back to Clients
          </button>
          <button
            onClick={() => router.push(`/clients/${result.client_id}`)}
            style={{
              flex: 1, padding: '12px', borderRadius: 10, border: 'none',
              background: '#3db8a9', color: '#0d1b2a', cursor: 'pointer',
               fontSize: 14, fontWeight: 600,
            }}
          >
            View Client Dashboard
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="page-enter" style={{ maxWidth: 560, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Header */}
      <div>
        <button
          onClick={() => router.push('/clients')}
          style={{
            display: 'flex', alignItems: 'center', gap: 6, background: 'none', border: 'none',
            color: '#a8b8c8', cursor: 'pointer', padding: 0, fontSize: 13, marginBottom: 12,
          }}
        >
          <ArrowLeft size={14} /> Back to Clients
        </button>
        <h2 style={{ fontWeight: 700, fontSize: 28, color: '#f5f0e8', margin: 0 }}>
          Onboard New Client
        </h2>
        <p style={{ color: '#a8b8c8', fontSize: 14, marginTop: 4 }}>
          Register an MSME business and generate an installation key for their Tally Sync agent.
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        <div style={{ background: '#1b263b', border: '1px solid #2d3e50', borderRadius: 14, padding: 24, display: 'flex', flexDirection: 'column', gap: 18 }}>
          <h3 style={{ fontWeight: 600, fontSize: 16, color: '#f5f0e8', margin: 0 }}>
            Business Details
          </h3>

          {/* Company Name */}
          <div>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#a8b8c8', marginBottom: 6 }}>
              Company Name <span style={{ color: '#c45c4a' }}>*</span>
            </label>
            <div style={{ position: 'relative' }}>
              <Building2 size={16} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: '#a8b8c8' }} />
              <input
                value={form.company_name}
                onChange={e => setForm({ ...form, company_name: e.target.value })}
                placeholder="e.g. Sharma Traders Pvt Ltd"
                style={inputStyle('company_name')}
              />
            </div>
            {errors.company_name && <p style={{ color: '#c45c4a', fontSize: 12, marginTop: 4 }}>{errors.company_name}</p>}
          </div>

          {/* Email */}
          <div>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#a8b8c8', marginBottom: 6 }}>
              Email <span style={{ color: '#c45c4a' }}>*</span>
            </label>
            <div style={{ position: 'relative' }}>
              <Mail size={16} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: '#a8b8c8' }} />
              <input
                type="email"
                value={form.email}
                onChange={e => setForm({ ...form, email: e.target.value })}
                placeholder="owner@company.com"
                style={inputStyle('email')}
              />
            </div>
            {errors.email && <p style={{ color: '#c45c4a', fontSize: 12, marginTop: 4 }}>{errors.email}</p>}
          </div>

          {/* Phone */}
          <div>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#a8b8c8', marginBottom: 6 }}>
              Phone
            </label>
            <div style={{ position: 'relative' }}>
              <Phone size={16} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: '#a8b8c8' }} />
              <input
                value={form.phone}
                onChange={e => setForm({ ...form, phone: e.target.value })}
                placeholder="+91-9876543210"
                style={inputStyle('phone')}
              />
            </div>
          </div>

          {/* GST ID */}
          <div>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#a8b8c8', marginBottom: 6 }}>
              GST Number
            </label>
            <div style={{ position: 'relative' }}>
              <Hash size={16} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: '#a8b8c8' }} />
              <input
                value={form.gst_id}
                onChange={e => setForm({ ...form, gst_id: e.target.value.toUpperCase() })}
                placeholder="18AABCU12345K1Z5"
                maxLength={15}
                style={inputStyle('gst_id')}
              />
            </div>
            {errors.gst_id && <p style={{ color: '#c45c4a', fontSize: 12, marginTop: 4 }}>{errors.gst_id}</p>}
          </div>

          {/* Plan */}
          <div>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#a8b8c8', marginBottom: 6 }}>
              Plan
            </label>
            <div style={{ display: 'flex', gap: 10 }}>
              {['trial', 'basic', 'professional'].map(p => (
                <button
                  key={p}
                  type="button"
                  onClick={() => setForm({ ...form, plan: p })}
                  style={{
                    flex: 1, padding: '10px 14px', borderRadius: 10, cursor: 'pointer',
                    border: `1px solid ${form.plan === p ? '#3db8a9' : '#2d3e50'}`,
                    background: form.plan === p ? '#3db8a915' : '#0d1b2a',
                    color: form.plan === p ? '#3db8a9' : '#a8b8c8',
                     fontSize: 13, fontWeight: 500,
                    textTransform: 'capitalize', transition: 'all 0.15s',
                  }}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Error */}
        {mutation.isError && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: 10, padding: '12px 16px',
            borderRadius: 10, background: '#c45c4a15', border: '1px solid #c45c4a40',
          }}>
            <AlertCircle size={16} color="#c45c4a" />
            <span style={{ color: '#c45c4a', fontSize: 13 }}>
              {(mutation.error as Error & { response?: { data?: { detail?: string } } })?.response?.data?.detail || (mutation.error as Error).message}
            </span>
          </div>
        )}

        {/* Submit */}
        <button
          type="submit"
          disabled={mutation.isPending}
          style={{
            padding: '14px', borderRadius: 10, border: 'none',
            background: mutation.isPending ? '#3db8a980' : '#3db8a9',
            color: '#0d1b2a', cursor: mutation.isPending ? 'wait' : 'pointer',
             fontSize: 15, fontWeight: 600,
            transition: 'background 0.15s',
          }}
        >
          {mutation.isPending ? 'Creating...' : 'Create Client & Generate Key'}
        </button>
      </form>
    </div>
  )
}
