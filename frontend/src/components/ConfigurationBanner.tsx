import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { apiService } from '../services/apiClient'
import { X, FolderOpen } from 'lucide-react'
import { Button } from '@/components/ui/button'

export default function ConfigurationBanner() {
  const [showBanner, setShowBanner] = useState(false)
  const [dismissed, setDismissed] = useState(false)

  useEffect(() => {
    const checkConfig = async () => {
      try {
        const config = await apiService.getConfig()
        const hasFolders = config.roots && config.roots.length > 0

        // Check if user has previously dismissed the banner this session
        const isDismissed = sessionStorage.getItem('config-banner-dismissed') === 'true'

        setShowBanner(!hasFolders && !isDismissed)
      } catch (error) {
        console.error('Failed to check configuration:', error)
      }
    }

    checkConfig()
    // Check every 30 seconds in case folders are added (reduced frequency for better performance)
    const interval = setInterval(checkConfig, 30000)
    return () => clearInterval(interval)
  }, [dismissed])

  const handleDismiss = () => {
    setDismissed(true)
    setShowBanner(false)
    sessionStorage.setItem('config-banner-dismissed', 'true')
  }

  if (!showBanner) {
    return null
  }

  return (
    <div className="bg-gradient-to-r from-yellow-500/20 to-orange-500/20 border-b border-yellow-500/30 px-4 py-3 shadow-lg">
      <div className="max-w-[1920px] mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-3 flex-1">
          <div className="flex-shrink-0">
            <FolderOpen className="h-5 w-5 text-yellow-500" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-yellow-100">
              No photo folders configured
            </p>
            <p className="text-xs text-yellow-200/80 mt-0.5">
              Add your photo folders to start searching and organizing your photos
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-3 ml-4">
          <Link to="/settings">
            <Button
              size="sm"
              className="!bg-gradient-to-r !from-[rgb(var(--gold-rgb))] !to-[rgb(var(--gold-rgb))] hover:!from-[rgb(var(--gold-rgb))]/80 hover:!to-[rgb(var(--gold-rgb))]/80 !text-black !border-[rgb(var(--gold-rgb))]/50 !shadow-[var(--shadow-gold)] hover:!shadow-[var(--shadow-gold)] hover:scale-105 !font-semibold transition-all"
            >
              Go to Settings
            </Button>
          </Link>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleDismiss}
            className="text-yellow-200 hover:text-yellow-100 hover:bg-yellow-500/20"
            aria-label="Dismiss banner"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}