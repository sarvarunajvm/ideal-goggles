import React, { useState, useRef, useEffect } from 'react'
import { SearchResult, getThumbnailBaseUrl } from '../services/apiClient'

interface ResultsGridProps {
  results: SearchResult[]
  loading?: boolean
  totalMatches?: number
  onItemClick?: (item: SearchResult) => void
  onItemDoubleClick?: (item: SearchResult) => void
  onItemRightClick?: (item: SearchResult, event: React.MouseEvent) => void
  onRevealInFolder?: (item: SearchResult) => void
}

export default function ResultsGrid({
  results,
  loading = false,
  totalMatches,
  onItemClick,
  onItemDoubleClick,
  onItemRightClick,
  onRevealInFolder,
}: ResultsGridProps) {
  const [focusedIndex, setFocusedIndex] = useState(0)
  const gridRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Focus management for keyboard navigation
    if (gridRef.current && results.length > 0) {
      const items = gridRef.current.querySelectorAll('.result-item')
      if (items[focusedIndex]) {
        ;(items[focusedIndex] as HTMLElement).focus()
      }
    }
  }, [focusedIndex, results])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    const columns = 4 // Assuming 4 columns grid
    switch (e.key) {
      case 'ArrowRight':
        setFocusedIndex(prev => Math.min(prev + 1, results.length - 1))
        break
      case 'ArrowLeft':
        setFocusedIndex(prev => Math.max(prev - 1, 0))
        break
      case 'ArrowDown':
        setFocusedIndex(prev => Math.min(prev + columns, results.length - 1))
        break
      case 'ArrowUp':
        setFocusedIndex(prev => Math.max(prev - columns, 0))
        break
      case 'Enter':
        if (results[focusedIndex] && onItemDoubleClick) {
          onItemDoubleClick(results[focusedIndex])
        }
        break
    }
  }

  const formatTimestamp = (timestamp: string | null) => {
    if (!timestamp) return 'Unknown'
    try {
      return new Date(timestamp).toLocaleDateString()
    } catch {
      return 'Unknown'
    }
  }

  const getBadgeColor = (badge: string) => {
    const colors: Record<string, string> = {
      OCR: 'bg-primary/15 text-primary dark:bg-primary/20 dark:text-primary',
      Face: 'bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-300',
      'Photo-Match': 'bg-fuchsia-100 text-fuchsia-800 dark:bg-fuchsia-900/30 dark:text-fuchsia-300',
      EXIF: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300',
      filename: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300',
      folder: 'bg-violet-100 text-violet-800 dark:bg-violet-900/30 dark:text-violet-300',
    }
    return colors[badge] || 'bg-neutral-100 text-neutral-800 dark:bg-neutral-800/40 dark:text-neutral-200'
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64" role="status">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        <span className="sr-only">Loading...</span>
      </div>
    )
  }

  if (results.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-6xl mb-4">🔍</div>
        <h2 className="text-2xl font-semibold text-gray-700 mb-2">
          No results found
        </h2>
        <p className="text-gray-500">
          Try a different search term or adjust your filters.
        </p>
      </div>
    )
  }

  return (
    <div className="results-grid-container" data-testid="results-grid">
      {totalMatches !== undefined && (
        <div className="mb-4 text-sm text-gray-600">
          {totalMatches} photos found
        </div>
      )}

      <div
        ref={gridRef}
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
        role="grid"
        onKeyDown={handleKeyDown}
        tabIndex={0}
      >
        {results.map((item, index) => (
          <div
            key={item.file_id}
            className={`result-item bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow transition-colors cursor-pointer ${
              index === focusedIndex ? 'ring-2 ring-primary' : ''
            }`}
            onClick={() => onItemClick?.(item)}
            onDoubleClick={() => onItemDoubleClick?.(item)}
            onContextMenu={e => onItemRightClick?.(item, e)}
            role="gridcell"
            tabIndex={index === focusedIndex ? 0 : -1}
            data-testid={`result-item-${item.file_id}`}
          >
            {/* Thumbnail */}
            <div className="aspect-square relative overflow-hidden bg-gray-100">
              {item.thumb_path ? (
                <img
                  src={`${getThumbnailBaseUrl()}/${item.thumb_path}`}
                  alt={item.filename}
                  className="w-full h-full object-cover"
                  style={{ minWidth: '256px', minHeight: '256px' }}
                  loading="lazy"
                  onError={e => {
                    ;(e.target as HTMLImageElement).src =
                      'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256"%3E%3Crect width="256" height="256" fill="%23f0f0f0"/%3E%3Ctext x="128" y="128" text-anchor="middle" dominant-baseline="middle" fill="%23999" font-family="Arial" font-size="24"%3E📷%3C/text%3E%3C/svg%3E'
                  }}
                />
              ) : (
                <div
                  className="w-full h-full flex items-center justify-center text-gray-400"
                  style={{ minWidth: '256px', minHeight: '256px' }}
                >
                  <svg
                    className="w-16 h-16"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                    />
                  </svg>
                </div>
              )}

              {/* Score overlay */}
              {item.score !== undefined && (
                <div className="absolute top-2 right-2 bg-black bg-opacity-50 text-white px-2 py-1 rounded text-xs">
                  {(item.score * 100).toFixed(0)}%
                </div>
              )}
            </div>

            {/* Metadata */}
            <div className="p-4">
              <h3
                className="font-medium text-gray-900 truncate"
                title={item.path}
              >
                {item.filename}
              </h3>

              <p
                className="text-sm text-gray-500 truncate mt-1"
                title={item.folder}
              >
                {item.folder}
              </p>

              <p className="text-xs text-gray-400 mt-1">
                {formatTimestamp(item.shot_dt)}
              </p>

              {/* Badges */}
              {item.badges && item.badges.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {item.badges.map((badge, idx) => (
                    <span
                      key={idx}
                      className={`px-2 py-1 text-xs font-medium rounded ${getBadgeColor(badge)}`}
                    >
                      {badge}
                    </span>
                  ))}
                </div>
              )}

              {/* OCR Snippet */}
              {item.snippet && (
                <p
                  className="text-xs text-gray-600 mt-2 line-clamp-2"
                  title={item.snippet}
                >
                  {item.snippet}
                </p>
              )}

              {/* Context menu button */}
              <button
                onClick={e => {
                  e.stopPropagation()
                  onRevealInFolder?.(item)
                }}
                className="mt-2 text-xs text-primary hover:text-primary/80"
                title="Reveal in folder"
              >
                📁 Show in folder
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
