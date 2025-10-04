import { SearchResponse, getThumbnailBaseUrl } from '../services/apiClient'

interface SearchResultsProps {
  results: SearchResponse
}

export default function SearchResults({ results }: SearchResultsProps) {
  const { query, total_matches, items, took_ms } = results

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
      text: 'bg-primary/15 text-primary dark:bg-primary/20 dark:text-primary',
      filename: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300',
      folder: 'bg-violet-100 text-violet-800 dark:bg-violet-900/30 dark:text-violet-300',
      metadata: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300',
      semantic: 'bg-teal-100 text-teal-800 dark:bg-teal-900/30 dark:text-teal-300',
      visual: 'bg-fuchsia-100 text-fuchsia-800 dark:bg-fuchsia-900/30 dark:text-fuchsia-300',
      face: 'bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-300',
    }
    return colors[badge] || 'bg-neutral-100 text-neutral-800 dark:bg-neutral-800/40 dark:text-neutral-200'
  }

  if (total_matches === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-6xl mb-4">🔍</div>
        <h2 className="text-2xl font-semibold text-gray-700 mb-2">
          No photos found
        </h2>
        <p className="text-gray-500">
          Try a different search term or adjust your filters.
        </p>
      </div>
    )
  }

  return (
    <div>
      {/* Results Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">
            {total_matches.toLocaleString()} photo
            {total_matches !== 1 ? 's' : ''} found
          </h2>
          <p className="text-sm text-gray-500">
            Search for "{query}" completed in {took_ms}ms
          </p>
        </div>
      </div>

      {/* Results Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {items.map(item => (
          <div
            key={item.file_id}
            className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow"
          >
            {/* Image Preview */}
            <div className="aspect-square bg-gray-100 flex items-center justify-center">
              {item.thumb_path ? (
                <img
                  src={`${getThumbnailBaseUrl()}/${item.thumb_path}`}
                  alt={item.filename}
                  className="w-full h-full object-cover"
                  onError={e => {
                    ;(e.target as HTMLImageElement).style.display = 'none'
                    ;(
                      e.target as HTMLImageElement
                    ).nextElementSibling!.classList.remove('hidden')
                  }}
                />
              ) : null}
              <div
                className={`text-6xl text-gray-400 ${item.thumb_path ? 'hidden' : ''}`}
              >
                📷
              </div>
            </div>

            {/* Photo Info */}
            <div className="p-4">
              <h3
                className="font-medium text-gray-900 truncate mb-2"
                title={item.filename}
              >
                {item.filename}
              </h3>

              <div className="space-y-2 text-sm text-gray-600">
                <div className="flex items-center space-x-2">
                  <span>📁</span>
                  <span className="truncate" title={item.folder}>
                    {item.folder.replace(/^.*\//, '')}
                  </span>
                </div>

                {item.shot_dt && (
                  <div className="flex items-center space-x-2">
                    <span>📅</span>
                    <span>{formatTimestamp(item.shot_dt)}</span>
                  </div>
                )}

                <div className="flex items-center space-x-2">
                  <span>⭐</span>
                  <span>Score: {(item.score * 100).toFixed(1)}%</span>
                </div>
              </div>

              {/* Badges */}
              {item.badges.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-3">
                  {item.badges.map((badge, index) => (
                    <span
                      key={index}
                      className={`px-2 py-1 text-xs rounded-full ${getBadgeColor(badge)}`}
                    >
                      {badge}
                    </span>
                  ))}
                </div>
              )}

              {/* Snippet */}
              {item.snippet && (
                <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded text-sm">
                  <span className="text-yellow-800">"{item.snippet}"</span>
                </div>
              )}

              {/* Actions */}
              <div className="mt-4 flex space-x-2">
                <button
                  onClick={() => {
                    // Open file location
                    navigator.clipboard.writeText(item.path)
                  }}
                  className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
                  title="Copy file path"
                >
                  📋 Copy Path
                </button>
                <button
                  onClick={() => {
                    // View full image
                    window.open(`file://${item.path}`, '_blank')
                  }}
                  className="px-3 py-1 text-xs rounded transition-colors bg-primary/15 text-primary hover:bg-primary/25"
                >
                  👁️ View
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Load More (if needed) */}
      {items.length < total_matches && (
        <div className="text-center mt-8">
          <button className="px-6 py-2 rounded-lg transition-colors bg-primary text-primary-foreground hover:bg-primary/90">
            Load More Photos
          </button>
        </div>
      )}
    </div>
  )
}
