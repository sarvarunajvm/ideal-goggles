import { useRouteError, isRouteErrorResponse, useNavigate } from 'react-router-dom'
import { AlertCircle, Home, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

export function RouteErrorBoundary() {
  const error = useRouteError()
  const navigate = useNavigate()

  let errorMessage: string
  let errorStatus: number | string = 'Error'

  if (isRouteErrorResponse(error)) {
    errorStatus = error.status
    errorMessage = error.statusText || error.data?.message || 'An error occurred'

    // Handle 404 specifically
    if (error.status === 404) {
      errorMessage = 'The page you are looking for does not exist'
    }
  } else if (error instanceof Error) {
    errorMessage = error.message
  } else {
    errorMessage = 'An unexpected error occurred'
  }

  const handleGoHome = () => {
    navigate('/')
  }

  const handleReload = () => {
    window.location.reload()
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-8">
      <Card className="max-w-md w-full">
        <CardHeader>
          <div className="flex justify-center mb-4">
            <AlertCircle className="h-16 w-16 text-destructive" />
          </div>
          <CardTitle className="text-center">
            {typeof errorStatus === 'number' ? `Error ${errorStatus}` : errorStatus}
          </CardTitle>
          <CardDescription className="text-center">
            {errorMessage}
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          {import.meta.env.DEV && error instanceof Error && error.stack && (
            <details className="text-left">
              <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-700 mb-2">
                Show error details
              </summary>
              <pre className="text-xs bg-gray-100 p-3 rounded overflow-auto max-h-40">
                {error.stack}
              </pre>
            </details>
          )}

          <div className="flex flex-col sm:flex-row gap-3">
            <Button onClick={handleGoHome} className="flex items-center space-x-2 flex-1 !bg-gradient-to-r !from-[rgb(var(--gold-rgb))] !to-[rgb(var(--gold-rgb))] hover:!from-[rgb(var(--gold-rgb))]/80 hover:!to-[rgb(var(--gold-rgb))]/80 !text-black !border-[rgb(var(--gold-rgb))]/50 !shadow-[var(--shadow-gold)] hover:!shadow-[var(--shadow-gold)] hover:scale-105 !font-semibold transition-all">
              <Home className="h-4 w-4" />
              <span>Go Home</span>
            </Button>

            <Button onClick={handleReload} className="flex items-center space-x-2 flex-1 !bg-gradient-to-r !from-[rgb(var(--cyan-rgb))] !to-[rgb(var(--cyan-rgb))] hover:!from-[rgb(var(--cyan-rgb))]/80 hover:!to-[rgb(var(--cyan-rgb))]/80 !text-black !border-[rgb(var(--cyan-rgb))]/50 !shadow-[var(--shadow-cyan)] hover:!shadow-[var(--shadow-cyan)] hover:scale-105 !font-semibold transition-all">
              <RefreshCw className="h-4 w-4" />
              <span>Reload</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
