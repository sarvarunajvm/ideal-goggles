import { useState, useEffect } from 'react'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import {
  Wifi,
  WifiOff,
  Loader2,
  Zap,
  CheckCircle,
  XCircle,
  Pause,
  AlertCircle,
} from 'lucide-react'
import { apiService, IndexStatus } from '../services/apiClient'

export default function StatusBar() {
  const [indexStatus, setIndexStatus] = useState<IndexStatus | null>(null)
  const [indexedCount, setIndexedCount] = useState<number>(0)
  const [healthStatus, setHealthStatus] = useState<
    'connected' | 'disconnected' | 'checking'
  >('checking')

  useEffect(() => {
    // Check health and index status every 5 seconds
    const checkStatus = async () => {
      try {
        // Only check index status since health endpoint may fail due to missing ML models
        const index = await apiService.getIndexStatus()

        // Also get the actual indexed count from stats
        try {
          const stats = await apiService.getIndexStats()
          const database = stats.database as { indexed_photos?: number }
          setIndexedCount(database?.indexed_photos ?? 0)
        } catch {
          // If stats fails, fall back to index status count
          setIndexedCount(index.progress.processed_files)
        }

        setHealthStatus('connected')
        setIndexStatus(index)
      } catch (error) {
        setHealthStatus('disconnected')
        setIndexStatus(null)
      }
    }

    checkStatus()
    const interval = setInterval(checkStatus, 5000)

    return () => clearInterval(interval)
  }, [])

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'indexing':
        return 'default'
      case 'error':
        return 'destructive'
      case 'idle':
        return 'secondary'
      default:
        return 'outline'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'indexing':
        return Zap
      case 'error':
        return XCircle
      case 'idle':
        return CheckCircle
      default:
        return Pause
    }
  }

  const getConnectionIcon = () => {
    switch (healthStatus) {
      case 'connected':
        return Wifi
      case 'disconnected':
        return WifiOff
      default:
        return Loader2
    }
  }

  // Map connection state to badge variant
  // Using icon + text; badge variant helper intentionally unused
  // const getConnectionBadgeVariant = () => {
  //   switch (healthStatus) {
  //     case 'connected':
  //       return 'secondary'
  //     case 'disconnected':
  //       return 'destructive'
  //     default:
  //       return 'outline'
  //   }
  // }

  const getConnectionText = () => {
    switch (healthStatus) {
      case 'connected':
        return 'Connected'
      case 'disconnected':
        return 'Disconnected'
      default:
        return 'Checking...'
    }
  }

  const getProgressPercentage = () => {
    if (
      !indexStatus ||
      indexStatus.status !== 'indexing' ||
      indexStatus.progress.total_files === 0
    ) {
      return 0
    }
    return (
      (indexStatus.progress.processed_files /
        indexStatus.progress.total_files) *
      100
    )
  }

  return (
    <footer className="bg-card/95 backdrop-blur-sm border-t border-border/50 px-4 py-2 shrink-0 shadow-inner">
      <div className="flex items-center justify-between text-xs sm:text-sm">
        {/* Index Status - Left Side */}
        <div className="flex items-center space-x-3">
          {indexStatus && indexStatus.status === 'indexing' && (
            <>
              <Badge
                variant={getStatusBadgeVariant(indexStatus.status)}
                className="transition-all duration-300 bg-gradient-to-r from-amber-500/20 to-orange-500/20 border-amber-500/50"
              >
                {(() => {
                  const IconComponent = getStatusIcon(indexStatus.status)
                  return (
                    <>
                      <IconComponent
                        className={`w-3 h-3 mr-1.5 text-amber-400 animate-pulse`}
                      />
                      <span className="text-amber-400">Indexing</span>
                    </>
                  )
                })()}
              </Badge>

              {indexStatus.status === 'indexing' && (
                <div className="flex items-center space-x-2">
                  <span className="text-muted-foreground text-xs">
                    {(() => {
                      const phase = indexStatus.progress.current_phase?.toLowerCase();
                      // Show clearer phase labels to avoid confusion
                      const phaseLabels: Record<string, string> = {
                        discovery: 'Discovering photos',
                        scanning: 'Scanning photos',
                        thumbnails: 'Creating thumbnails',
                        metadata: 'Extracting metadata',
                        ocr: 'Processing text (OCR)',
                        embeddings: 'Building search index',
                        faces: 'Detecting faces',
                        tagging: 'Adding tags',
                      };
                      return phaseLabels[phase] || phase?.replace(/_/g, ' ') || 'Processing';
                    })()}
                  </span>
                  {indexStatus.progress.total_files > 0 && (
                    <>
                      <div className="w-20">
                        <Progress
                          value={getProgressPercentage()}
                          className="h-1.5"
                        />
                      </div>
                      <span className="text-xs font-medium" title={`Phase: ${indexStatus.progress.current_phase}`}>
                        {indexStatus.progress.processed_files.toLocaleString()}/
                        {indexStatus.progress.total_files.toLocaleString()}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        ({Math.round(getProgressPercentage())}%)
                      </span>
                    </>
                  )}
                </div>
              )}
            </>
          )}

          {/* Show indexed count when not actively indexing */}
          {indexStatus && indexStatus.status !== 'indexing' && (
            <div className="flex items-center space-x-2 text-xs text-muted-foreground">
              <CheckCircle className="h-3 w-3 text-green-400" />
              <span>
                {indexedCount.toLocaleString()} photos indexed
              </span>
            </div>
          )}

          {indexStatus &&
           indexStatus.errors.length > 0 &&
           // Don't show "No root paths configured" as an error - it's a configuration state
           !indexStatus.errors.every(err => err.includes('No root paths configured')) && (
            <Popover>
              <PopoverTrigger asChild>
                <Badge
                  variant="destructive"
                  className="animate-pulse cursor-pointer hover:bg-destructive/80 transition-colors"
                >
                  <AlertCircle className="w-3 h-3 mr-1.5" />
                  {indexStatus.errors.length} error
                  {indexStatus.errors.length !== 1 ? 's' : ''}
                </Badge>
              </PopoverTrigger>
              <PopoverContent className="w-80" align="start">
                <div className="space-y-2">
                  <div className="flex items-center space-x-2 text-sm font-semibold">
                    <AlertCircle className="h-4 w-4 text-destructive" />
                    <span>Error Details</span>
                  </div>
                  <div className="space-y-2">
                    {indexStatus.errors.map((error, index) => (
                      <div key={index} className="text-sm">
                        <div className="p-2 bg-destructive/10 border border-destructive/20 rounded text-destructive-foreground">
                          {error}
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="text-xs text-muted-foreground pt-2 border-t">
                    Click outside to dismiss
                  </div>
                </div>
              </PopoverContent>
            </Popover>
          )}
        </div>

        {/* Connection Status - Right Side */}
        <div className="flex items-center">
          <div
            className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-all duration-300 ${
              healthStatus === 'connected'
                ? 'bg-green-500/20 text-green-400 border border-green-500/50 shadow-md shadow-green-500/20'
                : healthStatus === 'disconnected'
                ? 'bg-red-500/20 text-red-400 border border-red-500/50 shadow-md shadow-red-500/20'
                : 'bg-muted text-muted-foreground border border-border animate-pulse'
            }`}
            data-testid="connection-badge"
          >
            {(() => {
              const IconComponent = getConnectionIcon()
              return (
                <>
                  <IconComponent
                    className={`w-3 h-3 mr-1.5 ${
                      healthStatus === 'checking' ? 'animate-spin' : ''
                    }`}
                  />
                  {getConnectionText()}
                </>
              )
            })()}
          </div>
        </div>
      </div>

      {/* Mobile-friendly indexing progress */}
      {indexStatus && indexStatus.status === 'indexing' && (
        <div className="sm:hidden mt-2 pb-1">
          <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
            <span>{indexStatus.progress.current_phase}</span>
            {indexStatus.progress.total_files > 0 && (
              <span>
                {indexStatus.progress.processed_files}/
                {indexStatus.progress.total_files}
              </span>
            )}
          </div>
          {indexStatus.progress.total_files > 0 && (
            <Progress value={getProgressPercentage()} className="h-1" />
          )}
        </div>
      )}
    </footer>
  )
}
