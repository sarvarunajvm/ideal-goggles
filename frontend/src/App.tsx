import { Outlet } from 'react-router-dom'
import { useEffect, useState } from 'react'
import Layout from './components/Layout'
import { apiService } from './services/apiClient'
import { OnboardingWizard } from './components/OnboardingWizard/OnboardingWizard'
import { useOnboardingStore } from './stores/onboardingStore'
import { Toaster } from './components/ui/toaster'

function App() {
  const [backendOk, setBackendOk] = useState<boolean | null>(null)
  const { completed: onboardingCompleted, skipOnboarding } = useOnboardingStore()

  useEffect(() => {
    let cancelled = false
    let intervalId: NodeJS.Timeout | null = null

    async function check() {
      try {
        // Use shared API client with fixed port 5555
        // Use index/status instead of health since health check may fail due to missing ML models
        const res = await apiService.getIndexStatus()
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
      cancelled = true
      if (intervalId) clearInterval(intervalId)
    }
  }, [])

  // Show loading screen until backend becomes ready
  if (backendOk !== true) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-background to-primary/5 p-8">
        <div className="max-w-md w-full">
          {/* Logo and Brand */}
          <div className="flex flex-col items-center mb-8">
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-yellow-400 to-orange-400 rounded-full blur-2xl opacity-30 animate-pulse"></div>
              <div className="relative flex items-center justify-center w-20 h-20 bg-gradient-to-r from-yellow-400 to-orange-400 rounded-2xl shadow-2xl shadow-orange-500/30 animate-bounce">
                <svg className="w-12 h-12 text-black" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
            </div>
            <h1 className="text-3xl font-bold mt-6 bg-gradient-to-r from-yellow-400 to-orange-400 bg-clip-text text-transparent">
              Ideal Goggles
            </h1>
          </div>

          {/* Loading Content */}
          <div className="bg-card/80 backdrop-blur-sm shadow-2xl rounded-2xl p-8 text-center border border-orange-500/20">
            <h2 className="text-2xl font-semibold mb-3 text-foreground">
              Getting everything ready...
            </h2>
            <p className="text-muted-foreground mb-6">
              We're preparing your photo library for lightning-fast searches
            </p>

            {/* Progress Indicator */}
            <div className="flex justify-center mb-6">
              <div className="flex space-x-2">
                <div className="w-3 h-3 bg-yellow-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-3 h-3 bg-orange-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-3 h-3 bg-yellow-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            </div>

            {/* Status Message */}
            <div className="bg-muted/50 rounded-lg p-3 mb-4">
              <p className="text-sm text-muted-foreground">
                ✨ Setting up your personal photo search engine
              </p>
            </div>

            {/* Help Text */}
            <p className="text-xs text-muted-foreground">
              This usually takes just a few seconds. If it takes longer than expected,
              try closing and reopening the app.
            </p>
          </div>
        </div>
      </div>
    )
  }

  const shouldShowOnboarding = !onboardingCompleted && !skipOnboarding

  return (
    <>
      {shouldShowOnboarding && <OnboardingWizard />}
      <Layout>
        <Outlet />
      </Layout>
      <Toaster />
    </>
  )
}

export default App
