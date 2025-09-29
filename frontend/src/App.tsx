import { Routes, Route } from 'react-router-dom'
import { useEffect, useMemo, useState } from 'react'
import SearchPage from './pages/SearchPage'
import SettingsPage from './pages/SettingsPage'
import PeoplePage from './pages/PeoplePage'
import Layout from './components/Layout'
import { apiService } from './services/apiClient'

function App() {
  const [backendOk, setBackendOk] = useState<boolean | null>(null)
  const [logPath, setLogPath] = useState<string>('')
  const backendBaseDisplay = useMemo(() => {
    const isElectron = typeof window !== 'undefined' && window.electronAPI
    return isElectron ? 'http://127.0.0.1:5555' : '/api'
  }, [])

  useEffect(() => {
    let cancelled = false
    let intervalId: NodeJS.Timeout | null = null

    async function check() {
      try {
        const api = window.electronAPI
        if (api?.getBackendLogPath) {
          const p = await api.getBackendLogPath()
          if (!cancelled) setLogPath(p)
        }
        // Use shared API client with fixed port 5555
        const res = await apiService.getHealth()
        if (!cancelled) {
          setBackendOk(!!res)
          // Once backend is ready, stop the frequent polling
          if (res && intervalId) {
            clearInterval(intervalId)
            intervalId = null
          }
        }
      } catch {
        if (!cancelled) setBackendOk(false)
      }
    }

    check()
    // Only poll frequently while backend is not ready
    // Once ready, StatusBar components handle periodic health checks
    intervalId = setInterval(check, 1000)
    return () => {
      cancelled = true;
      if (intervalId) clearInterval(intervalId)
    }
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
    <Layout>
      <Routes>
        <Route path="/" element={<SearchPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/people" element={<PeoplePage />} />
      </Routes>
    </Layout>
  )
}

export default App
