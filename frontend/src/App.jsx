import { useState } from 'react'

const API_BASE = 'http://localhost:8000'

const RiskBadge = ({ level }) => {
  const colors = {
    CRITICAL: 'bg-red-100 text-red-800 border-red-300',
    HIGH:     'bg-orange-100 text-orange-800 border-orange-300',
    MODERATE: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    LOW:      'bg-green-100 text-green-800 border-green-300',
    STABLE:   'bg-green-100 text-green-800 border-green-300',
    SAFE:     'bg-green-100 text-green-800 border-green-300',
    UNKNOWN:  'bg-gray-100 text-gray-800 border-gray-300',
  }
  return (
    <span className={`px-3 py-1 rounded-full text-sm font-semibold border ${colors[level] || colors.UNKNOWN}`}>
      {level}
    </span>
  )
}

export default function App() {
  const [pharmaResult, setPharmaResult] = useState(null)
  const [icuResult, setIcuResult] = useState(null)
  const [pharmaLoading, setPharmaLoading] = useState(false)
  const [icuLoading, setIcuLoading] = useState(false)
  const [error, setError] = useState(null)

  const runPolypharmacy = async () => {
    setPharmaLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/tools/polypharmacy`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patient_id: 'patient-001' })
      })
      const data = await res.json()
      setPharmaResult(data)
    } catch (e) {
      setError('Could not connect to SafeGuard360 backend. Make sure the server is running.')
    }
    setPharmaLoading(false)
  }

  const runICU = async () => {
    setIcuLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/tools/icu-warning`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patient_id: 'patient-001' })
      })
      const data = await res.json()
      setIcuResult(data)
    } catch (e) {
      setError('Could not connect to SafeGuard360 backend. Make sure the server is running.')
    }
    setIcuLoading(false)
  }

  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', background: '#f8fafc', minHeight: '100vh', padding: '32px' }}>
      <div style={{ maxWidth: 1100, margin: '0 auto' }}>

        {/* HEADER */}
        <div style={{ marginBottom: 32 }}>
          <h1 style={{ fontSize: 28, fontWeight: 700, color: '#0f172a', margin: 0 }}>
            SafeGuard360
            <span style={{ fontSize: 14, fontWeight: 400, color: '#64748b', marginLeft: 12 }}>
              Patient Safety Agent
            </span>
          </h1>
          <p style={{ color: '#64748b', marginTop: 6 }}>
            Patient: Ramesh Sharma · Age 73 · Type 2 Diabetes, Hypertension, CKD Stage 3
          </p>
        </div>

        {error && (
          <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 10, padding: '12px 16px', marginBottom: 24, color: '#b91c1c' }}>
            {error}
          </div>
        )}

        {/* TWO TOOL PANELS */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 32 }}>

          {/* POLYPHARMACY PANEL */}
          <div style={{ background: '#fff', borderRadius: 16, border: '1px solid #e2e8f0', padding: 24 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
              <span style={{ fontSize: 24 }}>💊</span>
              <h2 style={{ fontSize: 18, fontWeight: 600, color: '#0f172a', margin: 0 }}>Polypharmacy Checker</h2>
            </div>
            <p style={{ color: '#64748b', fontSize: 14, marginBottom: 20 }}>
              Analyzes 6 active medications for dangerous drug-drug interactions using Groq AI.
            </p>
            <button
              onClick={runPolypharmacy}
              disabled={pharmaLoading}
              style={{
                background: pharmaLoading ? '#94a3b8' : '#ef4444',
                color: '#fff', border: 'none', borderRadius: 8,
                padding: '10px 20px', fontWeight: 600, cursor: pharmaLoading ? 'not-allowed' : 'pointer',
                fontSize: 14, width: '100%', marginBottom: 20
              }}
            >
              {pharmaLoading ? 'Analyzing medications...' : 'Run Polypharmacy Check'}
            </button>

            {pharmaResult && (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                  <span style={{ fontWeight: 600, fontSize: 14 }}>Overall Risk:</span>
                  <RiskBadge level={pharmaResult.risk_level} />
                </div>

                {pharmaResult.interactions_found?.length > 0 && (
                  <div style={{ marginBottom: 16 }}>
                    <div style={{ fontWeight: 600, fontSize: 13, color: '#374151', marginBottom: 8 }}>
                      Interactions Found ({pharmaResult.interactions_found.length}):
                    </div>
                    {pharmaResult.interactions_found.map((i, idx) => (
                      <div key={idx} style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, padding: 12, marginBottom: 8 }}>
                        <div style={{ fontWeight: 600, color: '#b91c1c', fontSize: 13 }}>
                          {i.drug_a} + {i.drug_b}
                          <span style={{ marginLeft: 8, fontSize: 11, background: '#fee2e2', padding: '2px 8px', borderRadius: 100 }}>
                            {i.severity}
                          </span>
                        </div>
                        <div style={{ color: '#6b7280', fontSize: 12, marginTop: 4 }}>{i.clinical_consequence}</div>
                        <div style={{ color: '#374151', fontSize: 12, marginTop: 4, fontStyle: 'italic' }}>{i.recommendation}</div>
                      </div>
                    ))}
                  </div>
                )}

                {pharmaResult.patient_explanation && (
                  <div style={{ background: '#f0f9ff', border: '1px solid #bae6fd', borderRadius: 8, padding: 12 }}>
                    <div style={{ fontWeight: 600, fontSize: 12, color: '#0369a1', marginBottom: 4 }}>For Patient:</div>
                    <div style={{ fontSize: 13, color: '#0c4a6e' }}>{pharmaResult.patient_explanation}</div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* ICU PANEL */}
          <div style={{ background: '#fff', borderRadius: 16, border: '1px solid #e2e8f0', padding: 24 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
              <span style={{ fontSize: 24 }}>📈</span>
              <h2 style={{ fontSize: 18, fontWeight: 600, color: '#0f172a', margin: 0 }}>ICU Early Warning</h2>
            </div>
            <p style={{ color: '#64748b', fontSize: 14, marginBottom: 20 }}>
              Monitors real-time vitals and detects early sepsis and deterioration patterns.
            </p>
            <button
              onClick={runICU}
              disabled={icuLoading}
              style={{
                background: icuLoading ? '#94a3b8' : '#0ea5e9',
                color: '#fff', border: 'none', borderRadius: 8,
                padding: '10px 20px', fontWeight: 600, cursor: icuLoading ? 'not-allowed' : 'pointer',
                fontSize: 14, width: '100%', marginBottom: 20
              }}
            >
              {icuLoading ? 'Analyzing vitals...' : 'Run ICU Warning Check'}
            </button>

            {icuResult && (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
                  <span style={{ fontWeight: 600, fontSize: 14 }}>Risk Level:</span>
                  <RiskBadge level={icuResult.risk_level} />
                  {icuResult.escalation_required && (
                    <span style={{ background: '#fee2e2', color: '#b91c1c', fontSize: 11, fontWeight: 700, padding: '2px 10px', borderRadius: 100 }}>
                      ESCALATE NOW
                    </span>
                  )}
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 12 }}>
                  <div style={{ background: '#f8fafc', borderRadius: 8, padding: '8px 12px', fontSize: 13 }}>
                    <span style={{ color: '#64748b' }}>NEWS2 Score: </span>
                    <span style={{ fontWeight: 700, color: icuResult.news2_score >= 6 ? '#ef4444' : '#22c55e' }}>
                      {icuResult.news2_score}/10
                    </span>
                  </div>
                  <div style={{ background: '#f8fafc', borderRadius: 8, padding: '8px 12px', fontSize: 13 }}>
                    <span style={{ color: '#64748b' }}>Sepsis Risk: </span>
                    <span style={{ fontWeight: 700 }}>{icuResult.sepsis_risk}</span>
                  </div>
                </div>

                {icuResult.nurse_alert && (
                  <div style={{ background: '#fff7ed', border: '1px solid #fed7aa', borderRadius: 8, padding: 12, marginBottom: 12 }}>
                    <div style={{ fontWeight: 700, fontSize: 12, color: '#c2410c', marginBottom: 4 }}>NURSE ALERT:</div>
                    <div style={{ fontSize: 13, color: '#7c2d12' }}>{icuResult.nurse_alert}</div>
                  </div>
                )}

                {icuResult.recommended_actions?.length > 0 && (
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 6 }}>Recommended Actions:</div>
                    {icuResult.recommended_actions.map((a, i) => (
                      <div key={i} style={{ fontSize: 12, color: '#374151', padding: '4px 0', borderBottom: '1px solid #f1f5f9' }}>
                        {i + 1}. {a}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* FOOTER */}
        <div style={{ textAlign: 'center', color: '#94a3b8', fontSize: 12, paddingTop: 16, borderTop: '1px solid #e2e8f0' }}>
          SafeGuard360 · Agents Assemble Hackathon 2026 · Built with Groq + Prompt Opinion + FHIR R4
        </div>
      </div>
    </div>
  )
}
