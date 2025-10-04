import { useState, useEffect } from 'react'
import { SearchResult, getThumbnailBaseUrl } from '../services/apiClient'

interface PreviewDrawerProps {
  item: SearchResult | null
  isOpen: boolean
  onClose: () => void
  onRevealInFolder?: (item: SearchResult) => void
  onNext?: () => void
  onPrevious?: () => void
}

export default function PreviewDrawer({
  item,
  isOpen,
  onClose,
  onRevealInFolder,
  onNext,
  onPrevious,
}: PreviewDrawerProps) {
  const [imageError, setImageError] = useState(false)

  useEffect(() => {
    setImageError(false)
  }, [item])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return

      switch (e.key) {
        case 'Escape':
          onClose()
          break
        case 'ArrowRight':
          onNext?.()
          break
        case 'ArrowLeft':
          onPrevious?.()
          break
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose, onNext, onPrevious])

  if (!isOpen || !item) return null

  const formatTimestamp = (timestamp: string | null) => {
    if (!timestamp) return 'Unknown'
    try {
      return new Date(timestamp).toLocaleString()
    } catch {
      return 'Unknown'
    }
  }

  const getBadgeColor = (badge: string) => {
    const colors: Record<string, string> = {
      OCR: '[background:var(--gradient-gold)] text-black',
      Face: '[background:var(--gradient-red)] text-white',
      'Photo-Match': '[background:var(--gradient-purple)] text-white',
      EXIF: '[background:var(--gradient-cyan)] text-black',
      filename: '[background:var(--gradient-green)] text-black',
      folder: '[background:var(--gradient-pink)] text-white',
    }
    return colors[badge] || 'bg-primary/20 text-primary'
  }

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-card rounded-lg shadow-2xl shadow-primary/20 border border-primary/20 max-w-4xl max-h-[90vh] w-full mx-4 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-primary/20">
          <h2
            className="text-lg font-semibold text-foreground truncate"
            title={item.filename}
          >
            {item.filename}
          </h2>
          <div className="flex items-center space-x-2">
            {onPrevious && (
              <button
                onClick={onPrevious}
                className="p-2 text-primary hover:text-primary-foreground rounded-lg hover:bg-primary transition-all"
                title="Previous photo (←)"
              >
                ←
              </button>
            )}
            {onNext && (
              <button
                onClick={onNext}
                className="p-2 text-primary hover:text-primary-foreground rounded-lg hover:bg-primary transition-all"
                title="Next photo (→)"
              >
                →
              </button>
            )}
            <button
              onClick={onClose}
              className="p-2 text-primary hover:text-primary-foreground rounded-lg hover:bg-primary transition-all"
              title="Close (Esc)"
            >
              ✕
            </button>
          </div>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Image Preview */}
          <div className="flex-1 flex items-center justify-center bg-black p-4">
            {!imageError && item.thumb_path ? (
              <img
                src={`${getThumbnailBaseUrl()}/${item.thumb_path}`}
                alt={item.filename}
                className="max-w-full max-h-full object-contain"
                onError={() => setImageError(true)}
              />
            ) : (
              <div className="flex flex-col items-center text-muted-foreground">
                <div className="text-8xl mb-4">📷</div>
                <p className="text-lg">Preview not available</p>
              </div>
            )}
          </div>

          {/* Sidebar with details */}
          <div className="w-80 border-l border-primary/20 bg-card overflow-y-auto">
            <div className="p-4 space-y-6">
              {/* Basic Info */}
              <div>
                <h3 className="text-sm font-medium text-primary mb-3">
                  File Information
                </h3>
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="text-muted-foreground">Path:</span>
                    <p className="text-foreground break-all">{item.path}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Folder:</span>
                    <p className="text-foreground break-all">{item.folder}</p>
                  </div>
                  {item.shot_dt && (
                    <div>
                      <span className="text-muted-foreground">Date Taken:</span>
                      <p className="text-foreground">
                        {formatTimestamp(item.shot_dt)}
                      </p>
                    </div>
                  )}
                  <div>
                    <span className="text-muted-foreground">Relevance Score:</span>
                    <p className="text-foreground">
                      {(item.score * 100).toFixed(1)}%
                    </p>
                  </div>
                </div>
              </div>

              {/* Badges */}
              {item.badges.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-primary mb-3">
                    Match Types
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {item.badges.map((badge, index) => (
                      <span
                        key={index}
                        className={`px-3 py-1 text-sm rounded-full ${getBadgeColor(badge)}`}
                      >
                        {badge}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Snippet */}
              {item.snippet && (
                <div>
                  <h3 className="text-sm font-medium text-gray-900 mb-3">
                    Text Match
                  </h3>
                  <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <p className="text-sm text-yellow-800">"{item.snippet}"</p>
                  </div>
                </div>
              )}

              {/* Actions */}
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-3">
                  Actions
                </h3>
                <div className="space-y-2">
                  <button
                    onClick={() => onRevealInFolder?.(item)}
                    className="w-full px-4 py-2 text-sm rounded-lg transition-colors flex items-center justify-center space-x-2 bg-primary text-primary-foreground hover:bg-primary/90"
                  >
                    <span>📁</span>
                    <span>Reveal in Folder</span>
                  </button>

                  <button
                    onClick={() => navigator.clipboard.writeText(item.path)}
                    className="w-full px-4 py-2 text-sm bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors flex items-center justify-center space-x-2"
                  >
                    <span>📋</span>
                    <span>Copy File Path</span>
                  </button>

                  <button
                    onClick={() => {
                      // Open original image in default viewer
                      window.open(`file://${item.path}`, '_blank')
                    }}
                    className="w-full px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center space-x-2"
                  >
                    <span>👁️</span>
                    <span>Open in Viewer</span>
                  </button>
                </div>
              </div>

              {/* Keyboard shortcuts help */}
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-3">
                  Keyboard Shortcuts
                </h3>
                <div className="text-xs text-gray-600 space-y-1">
                  <div className="flex justify-between">
                    <span>Next photo:</span>
                    <span className="font-mono bg-gray-200 px-1 rounded">
                      →
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Previous photo:</span>
                    <span className="font-mono bg-gray-200 px-1 rounded">
                      ←
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Close:</span>
                    <span className="font-mono bg-gray-200 px-1 rounded">
                      Esc
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
