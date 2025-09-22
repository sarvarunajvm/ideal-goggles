import { Routes, Route } from 'react-router-dom'
import { useEffect, useMemo, useState } from 'react'
import SearchPage from './pages/SearchPage'
import SettingsPage from './pages/SettingsPage'
import PeoplePage from './pages/PeoplePage'
import { apiService } from './services/apiClient'

function App() {
  const [backendOk, setBackendOk] = useState<boolean | null>(null)
  const [logPath, setLogPath] = useState<string>('')
  const [backendPort, setBackendPort] = useState<number | null>(null)
  const backendBaseDisplay = useMemo(() => {
    const isElectron = typeof window !== 'undefined' && (window as any).electronAPI
    const port = backendPort ?? (window as any).BACKEND_PORT ?? 8000
    return isElectron ? `http://127.0.0.1:${port}` : '/api'
  }, [backendPort])

  useEffect(() => {
    let cancelled = false

    async function check() {
      try {
        if ((window as any).electronAPI?.getBackendLogPath) {
          const p = await (window as any).electronAPI.getBackendLogPath()
          if (!cancelled) setLogPath(p)
        }
        if ((window as any).electronAPI?.getBackendPort) {
          const port = await (window as any).electronAPI.getBackendPort()
          if (!cancelled) setBackendPort(port)
        }
        // Use shared API client so Electron dynamic port and web proxy are handled
        const res = await apiService.getHealth()
        if (!cancelled) setBackendOk(!!res)
      } catch {
        if (!cancelled) setBackendOk(false)
      }
    }

    check()
    const id = setInterval(check, 1000)
    return () => { cancelled = true; clearInterval(id) }
  }, [])

  // Show loading screen until backend becomes ready
  if (backendOk !== true) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-8">
        <div className="max-w-xl w-full bg-white shadow rounded-lg p-6 text-center">
          <div className="text-5xl mb-3">⏳</div>
          <h1 className="text-xl font-semibold mb-2">Starting local backend…</h1>
          <p className="text-gray-600 mb-4">The app is waiting for the local API to become available at <code>{backendBaseDisplay}</code>.</p>
          {logPath && (
            <p className="text-sm text-gray-500">
              Backend log: <span className="break-all">{logPath}</span>
            </p>
          )}
          <p className="text-sm text-gray-500 mt-2">If this persists for more than 30 seconds, quit and reopen the app.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Routes>
        <Route path="/" element={<SearchPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/people" element={<PeoplePage />} />
      </Routes>
    </div>
  )
}

export default App
