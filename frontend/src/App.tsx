import { useEffect, useState } from 'react'

const API_BASE = 'http://localhost:8000'

function App() {
  const [health, setHealth] = useState<string>('checking…')

  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then((res) => res.json())
      .then((data) => setHealth(data.status === 'ok' ? '✅ API connected' : '⚠️ unexpected response'))
      .catch(() => setHealth('❌ API unreachable'))
  }, [])

  return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-6 p-8">
      <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
        MULESHIELD
      </h1>
      <p className="text-lg text-slate-400">Mule-Account Risk Intelligence Platform</p>
      <div className="mt-4 rounded-xl border border-slate-700 bg-slate-800/60 px-6 py-4 backdrop-blur">
        <span className="text-sm text-slate-300">Backend status:&nbsp;</span>
        <span className="font-medium">{health}</span>
      </div>
    </div>
  )
}

export default App
