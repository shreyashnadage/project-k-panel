'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { TestModeState, SimulationInfo, DatasetSummary } from '@/lib/api'

interface Props {
  clientApi: {
    getTestMode: () => Promise<TestModeState>
    setTestMode: (mode: 'live' | 'test', simulationId?: number) => Promise<TestModeState>
    getSimulations: () => Promise<SimulationInfo[]>
    ingestSimData: (simulationId: number) => Promise<{ simulation_id: number; data_source: string; ingested: Record<string, number> }>
    getTestDatasets: () => Promise<DatasetSummary[]>
    purgeTestDataset: (simulationId: number) => Promise<{ deleted: Record<string, number> }>
  }
  clientId: string
}

export default function TestModeBanner({ clientApi, clientId }: Props) {
  const qc = useQueryClient()
  const [open, setOpen] = useState(false)
  const [ingesting, setIngesting] = useState<number | null>(null)
  const [purging, setPurging] = useState<number | null>(null)
  const [ingestResult, setIngestResult] = useState<{ sim_id: number; counts: Record<string, number> } | null>(null)

  const { data: modeState } = useQuery({
    queryKey: ['test-mode', clientId],
    queryFn: () => clientApi.getTestMode(),
    staleTime: 30_000,
  })

  const { data: simulations } = useQuery({
    queryKey: ['test-simulations', clientId],
    queryFn: () => clientApi.getSimulations(),
    enabled: open && (modeState?.simulator_available ?? false),
    staleTime: 60_000,
  })

  const { data: datasets } = useQuery({
    queryKey: ['test-datasets', clientId],
    queryFn: () => clientApi.getTestDatasets(),
    enabled: open,
    staleTime: 30_000,
  })

  const setModeMutation = useMutation({
    mutationFn: ({ mode, simId }: { mode: 'live' | 'test'; simId?: number }) =>
      clientApi.setTestMode(mode, simId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['test-mode', clientId] })
      // Invalidate all dashboard queries so they reload with new data_source
      qc.invalidateQueries({ queryKey: ['kpis'] })
      qc.invalidateQueries({ queryKey: ['vouchers'] })
      qc.invalidateQueries({ queryKey: ['cash-flow'] })
      qc.invalidateQueries({ queryKey: ['ledgers'] })
    },
  })

  const handleIngest = async (simId: number) => {
    setIngesting(simId)
    setIngestResult(null)
    try {
      const result = await clientApi.ingestSimData(simId)
      setIngestResult({ sim_id: simId, counts: result.ingested })
      qc.invalidateQueries({ queryKey: ['test-datasets', clientId] })
    } catch (e) {
      console.error('Ingest failed', e)
    } finally {
      setIngesting(null)
    }
  }

  const handlePurge = async (simId: number) => {
    if (!confirm(`Delete all data for simulation ${simId}? This cannot be undone.`)) return
    setPurging(simId)
    try {
      await clientApi.purgeTestDataset(simId)
      qc.invalidateQueries({ queryKey: ['test-datasets', clientId] })
      qc.invalidateQueries({ queryKey: ['test-mode', clientId] })
      qc.invalidateQueries({ queryKey: ['kpis'] })
      qc.invalidateQueries({ queryKey: ['vouchers'] })
    } finally {
      setPurging(null)
    }
  }

  const isTestMode = modeState?.mode === 'test'

  return (
    <>
      {/* ── Live/Test mode indicator in header ── */}
      {isTestMode ? (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 12,
          padding: '10px 16px', borderRadius: 8, marginBottom: 16,
          background: '#78350f20', border: '1px solid #d9770680',
          color: '#fbbf24', fontSize: 13,
        }}>
          <span style={{ fontSize: 16 }}>⚠</span>
          <span style={{ flex: 1 }}>
            <strong>Test Mode</strong>
            {modeState.simulation_name && (
              <> — showing simulated data from <em>{modeState.simulation_name}</em></>
            )}
          </span>
          <button
            onClick={() => setModeMutation.mutate({ mode: 'live' })}
            disabled={setModeMutation.isPending}
            style={{
              padding: '4px 12px', borderRadius: 6, border: '1px solid #f59e0b80',
              background: 'transparent', color: '#fbbf24', cursor: 'pointer', fontSize: 12,
            }}
          >
            {setModeMutation.isPending ? '…' : 'Go Live'}
          </button>
          <button
            onClick={() => setOpen(true)}
            style={{
              padding: '4px 12px', borderRadius: 6, border: '1px solid #f59e0b40',
              background: 'transparent', color: '#f59e0b', cursor: 'pointer', fontSize: 12,
            }}
          >
            Manage
          </button>
        </div>
      ) : (
        modeState && (
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 12 }}>
            <button
              onClick={() => setOpen(true)}
              style={{
                padding: '4px 12px', borderRadius: 6, fontSize: 12,
                background: '#1e293b', border: '1px solid #334155',
                color: '#94a3b8', cursor: 'pointer',
              }}
            >
              Test Mode
            </button>
          </div>
        )
      )}

      {/* ── Modal ── */}
      {open && (
        <div
          onClick={(e) => { if (e.target === e.currentTarget) setOpen(false) }}
          style={{
            position: 'fixed', inset: 0, background: '#00000080',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            zIndex: 1000,
          }}
        >
          <div style={{
            background: '#1e293b', border: '1px solid #334155', borderRadius: 12,
            width: 560, maxHeight: '80vh', overflow: 'hidden', display: 'flex', flexDirection: 'column',
          }}>
            {/* Header */}
            <div style={{
              padding: '16px 20px', borderBottom: '1px solid #334155',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            }}>
              <span style={{ color: '#f1f5f9', fontWeight: 600, fontSize: 15 }}>Test Mode</span>
              <button onClick={() => setOpen(false)} style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: 18 }}>✕</button>
            </div>

            <div style={{ overflowY: 'auto', padding: 20, display: 'flex', flexDirection: 'column', gap: 20 }}>
              {/* Simulator status */}
              <div style={{ fontSize: 12, color: '#64748b' }}>
                {modeState?.simulator_available
                  ? `Simulator connected at ${modeState.simulator_url}`
                  : 'Simulator not connected — SIMULATOR_URL not configured on backend'}
              </div>

              {/* Available simulations */}
              {modeState?.simulator_available && (
                <section>
                  <div style={{ color: '#94a3b8', fontSize: 12, fontWeight: 600, marginBottom: 10, textTransform: 'uppercase', letterSpacing: 1 }}>Available Simulations</div>
                  {!simulations ? (
                    <div style={{ color: '#64748b', fontSize: 13 }}>Loading…</div>
                  ) : simulations.length === 0 ? (
                    <div style={{ color: '#64748b', fontSize: 13 }}>No simulations found</div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                      {simulations.map(sim => {
                        const isActive = modeState.mode === 'test' && modeState.simulation_id === sim.id
                        const alreadyIngested = datasets?.some(d => d.simulation_id === sim.id) ?? false
                        return (
                          <div key={sim.id} style={{
                            padding: '10px 12px', borderRadius: 8, display: 'flex', alignItems: 'center', gap: 10,
                            background: isActive ? '#78350f20' : '#0f172a',
                            border: `1px solid ${isActive ? '#d9770680' : '#1e293b'}`,
                          }}>
                            <div style={{ flex: 1 }}>
                              <div style={{ color: '#e2e8f0', fontSize: 13 }}>{sim.name}</div>
                              {sim.company_name && <div style={{ color: '#64748b', fontSize: 11 }}>{sim.company_name as string}</div>}
                            </div>
                            {!alreadyIngested && (
                              <button
                                onClick={() => handleIngest(sim.id)}
                                disabled={ingesting === sim.id}
                                style={{
                                  padding: '4px 10px', borderRadius: 6, fontSize: 12,
                                  background: '#0f4', border: 'none', color: '#000', cursor: 'pointer', opacity: ingesting === sim.id ? 0.6 : 1,
                                }}
                              >
                                {ingesting === sim.id ? 'Ingesting…' : 'Ingest'}
                              </button>
                            )}
                            {alreadyIngested && !isActive && (
                              <button
                                onClick={() => setModeMutation.mutate({ mode: 'test', simId: sim.id })}
                                disabled={setModeMutation.isPending}
                                style={{
                                  padding: '4px 10px', borderRadius: 6, fontSize: 12,
                                  background: '#0369a1', border: 'none', color: '#fff', cursor: 'pointer',
                                }}
                              >
                                View
                              </button>
                            )}
                            {isActive && (
                              <span style={{ fontSize: 11, color: '#fbbf24', padding: '2px 8px', border: '1px solid #fbbf2440', borderRadius: 4 }}>Active</span>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  )}
                </section>
              )}

              {/* Ingest result */}
              {ingestResult && (
                <div style={{
                  padding: '10px 12px', borderRadius: 8,
                  background: '#14532d20', border: '1px solid #16a34a40', color: '#86efac', fontSize: 12,
                }}>
                  Ingested sim:{ingestResult.sim_id} — {Object.entries(ingestResult.counts).map(([k, v]) => `${v} ${k}`).join(', ')}
                </div>
              )}

              {/* Ingested datasets */}
              <section>
                <div style={{ color: '#94a3b8', fontSize: 12, fontWeight: 600, marginBottom: 10, textTransform: 'uppercase', letterSpacing: 1 }}>Ingested Datasets</div>
                {!datasets || datasets.length === 0 ? (
                  <div style={{ color: '#64748b', fontSize: 13 }}>No test datasets ingested yet</div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {datasets.map(ds => (
                      <div key={ds.data_source} style={{
                        padding: '10px 12px', borderRadius: 8, display: 'flex', alignItems: 'center', gap: 10,
                        background: '#0f172a', border: '1px solid #1e293b',
                      }}>
                        <div style={{ flex: 1 }}>
                          <div style={{ color: '#e2e8f0', fontSize: 13 }}>
                            {ds.simulation_name ?? ds.data_source}
                          </div>
                          <div style={{ color: '#64748b', fontSize: 11 }}>
                            {ds.ledgers} ledgers · {ds.vouchers} vouchers · {ds.stock_items} stock items
                          </div>
                        </div>
                        <button
                          onClick={() => handlePurge(ds.simulation_id)}
                          disabled={purging === ds.simulation_id}
                          style={{
                            padding: '4px 10px', borderRadius: 6, fontSize: 12,
                            background: 'transparent', border: '1px solid #ef444440',
                            color: '#f87171', cursor: 'pointer',
                          }}
                        >
                          {purging === ds.simulation_id ? 'Deleting…' : 'Purge'}
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </section>

              {/* Switch to live */}
              {isTestMode && (
                <button
                  onClick={() => { setModeMutation.mutate({ mode: 'live' }); setOpen(false) }}
                  style={{
                    padding: '8px 16px', borderRadius: 8, fontSize: 13,
                    background: '#334155', border: '1px solid #475569',
                    color: '#e2e8f0', cursor: 'pointer', width: '100%',
                  }}
                >
                  Switch to Live Data
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  )
}
