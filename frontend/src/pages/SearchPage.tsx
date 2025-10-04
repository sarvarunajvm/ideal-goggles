import { useState } from 'react'
import {
  apiService,
  SearchResponse,
  SearchResult,
  getThumbnailBaseUrl,
} from '../services/apiClient'
import { osIntegration } from '../services/osIntegration'
import { Lightbox } from '../components/Lightbox/Lightbox'
import { useLightboxStore, LightboxPhoto } from '../stores/lightboxStore'
import { VirtualGrid } from '../components/VirtualGrid/VirtualGrid'

// shadcn/ui components
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Collapsible,
  CollapsibleContent,
} from '@/components/ui/collapsible'

// Icons
import {
  Search,
  Image as ImageIcon,
  Upload,
  Filter,
  Calendar,
  Folder,
  Clock,
  FileText,
  ExternalLink,
  AlertCircle,
  X,
  Sparkles,
} from 'lucide-react'

// Compact Search Bar Component
function CompactSearchBar({
  onSearch,
  onImageSearch,
  searchMode,
  onSearchModeChange,
  loading,
  filters,
  onFilterChange,
  filtersOpen,
  onFiltersToggle,
}: {
  onSearch: (query: string) => void
  onImageSearch: (file: File) => void
  searchMode: 'text' | 'semantic' | 'image'
  onSearchModeChange: (mode: 'text' | 'semantic' | 'image') => void
  loading: boolean
  filters: any
  onFilterChange: (filters: any) => void
  filtersOpen: boolean
  onFiltersToggle: () => void
}) {
  const [query, setQuery] = useState('')
  const [dragActive, setDragActive] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim() && searchMode !== 'image') {
      onSearch(query.trim())
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(false)

    const files = Array.from(e.dataTransfer.files)
    const imageFile = files.find(file => file.type.startsWith('image/'))

    if (imageFile && searchMode === 'image') {
      onImageSearch(imageFile)
    }
  }

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file && searchMode === 'image') {
      onImageSearch(file)
    }
  }

  const hasActiveFilters = filters.from || filters.to || filters.folder || filters.limit !== 50

  if (searchMode === 'image') {
    return (
      <div className="space-y-3">
        <div className="relative">
          <div
            className={`relative border-2 border-dashed rounded-lg p-6 text-center transition-all duration-200 ${
              dragActive
                ? 'border-primary bg-primary/10 shadow-lg shadow-primary/30'
                : 'border-primary/30 hover:border-primary/60 hover:bg-primary/5'
            }`}
            onDragEnter={e => {
              e.preventDefault()
              setDragActive(true)
            }}
            onDragLeave={e => {
              e.preventDefault()
              setDragActive(false)
            }}
            onDragOver={e => e.preventDefault()}
            onDrop={handleDrop}
          >
            <input
              type="file"
              accept="image/*"
              onChange={handleFileInput}
              className="hidden"
              id="image-upload"
            />
            <label
              htmlFor="image-upload"
              className="cursor-pointer flex flex-col items-center"
            >
              <Upload className="h-8 w-8 text-primary mb-2" />
              <p className="text-sm font-medium">Drop an image or click to browse</p>
              <p className="text-xs text-muted-foreground mt-1">
                Find photos similar to your reference image
              </p>
            </label>

            {/* Mode switcher in corner */}
            <div className="absolute top-2 left-2 flex items-center gap-1 bg-background/95 backdrop-blur rounded-lg p-1 border">
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                onClick={() => onSearchModeChange('text')}
                title="Quick Find"
              >
                <Search className="h-3.5 w-3.5" />
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                onClick={() => onSearchModeChange('semantic')}
                title="Smart Search"
              >
                <Sparkles className="h-3.5 w-3.5" />
              </Button>
              <Button
                type="button"
                variant="default"
                size="icon"
                className="h-7 w-7"
                onClick={() => onSearchModeChange('image')}
                title="Similar Photos"
              >
                <ImageIcon className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative">
          {/* Mode icons on the left */}
          <div className="absolute left-1 top-1/2 -translate-y-1/2 flex items-center gap-0.5 bg-muted/50 rounded-md p-0.5">
            <Button
              type="button"
              variant={searchMode === 'text' ? 'default' : 'ghost'}
              size="icon"
              className="h-7 w-7"
              onClick={() => onSearchModeChange('text')}
              title="Quick Find - Search by filename, date, or text"
            >
              <Search className="h-3.5 w-3.5" />
            </Button>
            <Button
              type="button"
              variant={searchMode === 'semantic' ? 'default' : 'ghost'}
              size="icon"
              className="h-7 w-7"
              onClick={() => onSearchModeChange('semantic')}
              title="Smart Search - Describe what you're looking for"
            >
              <Sparkles className="h-3.5 w-3.5" />
            </Button>
            <Button
              type="button"
              variant={searchMode === 'image' ? 'default' : 'ghost'}
              size="icon"
              className="h-7 w-7"
              onClick={() => onSearchModeChange('image')}
              title="Similar Photos - Find visually similar images"
            >
              <ImageIcon className="h-3.5 w-3.5" />
            </Button>
          </div>

          <Input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder={
              searchMode === 'semantic'
                ? 'Describe what you\'re looking for...'
                : 'Search by filename, date, or text...'
            }
            className="pl-28 pr-32 h-10"
            disabled={loading}
          />
          <div className="absolute right-1 top-1/2 -translate-y-1/2 flex items-center gap-1">
            {query && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setQuery('')}
                className="h-8 w-8 p-0"
              >
                <X className="h-3 w-3" />
              </Button>
            )}
            <Button
              type="button"
              variant={hasActiveFilters ? "default" : "ghost"}
              size="sm"
              onClick={onFiltersToggle}
              className="h-8 w-8 p-0"
              title="Advanced filters"
            >
              <Filter className={`h-3 w-3 ${hasActiveFilters ? 'text-primary-foreground' : 'text-muted-foreground'}`} />
            </Button>
            <Button
              type="submit"
              size="sm"
              disabled={!query.trim() || loading}
              className="h-8 px-3"
            >
              {loading ? (
                <div className="animate-spin rounded-full h-3 w-3 border-2 border-primary border-t-transparent" />
              ) : (
                'Search'
              )}
            </Button>
          </div>
        </div>
      </form>

      {/* Collapsible Filters */}
      <Collapsible open={filtersOpen} onOpenChange={onFiltersToggle}>
        <CollapsibleContent>
          <Card className="p-3 bg-muted/30">
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2">
                <Calendar className="h-3 w-3 text-muted-foreground" />
                <Input
                  type="date"
                  value={filters.from}
                  onChange={e => onFilterChange({ from: e.target.value })}
                  className="h-8 text-xs"
                  placeholder="From"
                />
                <span className="text-xs text-muted-foreground">to</span>
                <Input
                  type="date"
                  value={filters.to}
                  onChange={e => onFilterChange({ to: e.target.value })}
                  className="h-8 text-xs"
                  placeholder="To"
                />
              </div>

              <div className="flex items-center gap-2">
                <Folder className="h-3 w-3 text-muted-foreground" />
                <Input
                  value={filters.folder}
                  onChange={e => onFilterChange({ folder: e.target.value })}
                  placeholder="Folder path..."
                  className="h-8 w-40 text-xs"
                />
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">Limit:</span>
                <Input
                  type="number"
                  value={filters.limit}
                  onChange={e =>
                    onFilterChange({
                      limit: parseInt(e.target.value) || 50,
                    })
                  }
                  min="1"
                  max="1000"
                  className="h-8 w-16 text-xs"
                />
              </div>

              {hasActiveFilters && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() =>
                    onFilterChange({ from: '', to: '', folder: '', limit: 50 })
                  }
                  className="h-8 text-xs"
                >
                  <X className="h-3 w-3 mr-1" />
                  Clear
                </Button>
              )}
            </div>
          </Card>
        </CollapsibleContent>
      </Collapsible>
    </div>
  )
}

// Results Grid Component
function ResultsGrid({
  results,
  onItemClick,
  onRevealInFolder,
}: {
  results: SearchResult[]
  onItemClick: (item: SearchResult) => void
  onRevealInFolder: (item: SearchResult) => void
}) {
  const thumbnailBaseUrl = getThumbnailBaseUrl()

  if (results.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <Search className="h-12 w-12 text-muted-foreground mb-4" />
        <p className="text-lg font-medium text-muted-foreground">No results found</p>
        <p className="text-sm text-muted-foreground mt-1">Try adjusting your search or filters</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-8 gap-3">
      {results.map(item => (
        <Card
          key={item.file_id}
          className="group cursor-pointer overflow-hidden transition-all duration-200 hover:shadow-lg hover:scale-[1.02]"
          onClick={() => onItemClick(item)}
        >
          <div className="relative aspect-square bg-muted">
            {item.thumb_path ? (
              <img
                src={`${thumbnailBaseUrl}/${item.thumb_path}`}
                alt={item.filename}
                className="absolute inset-0 w-full h-full object-cover"
                loading="lazy"
              />
            ) : (
              <div className="absolute inset-0 flex items-center justify-center">
                <ImageIcon className="h-8 w-8 text-muted-foreground" />
              </div>
            )}

            {/* Overlay with actions */}
            <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors duration-200">
              <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                <Button
                  size="icon"
                  variant="secondary"
                  className="h-6 w-6 backdrop-blur-sm"
                  onClick={e => {
                    e.stopPropagation()
                    onRevealInFolder(item)
                  }}
                >
                  <ExternalLink className="h-3 w-3" />
                </Button>
              </div>
            </div>

            {/* Score badge */}
            {item.score && (
              <div className="absolute top-2 left-2">
                <Badge variant="secondary" className="backdrop-blur-sm text-xs px-1 py-0">
                  {(item.score * 100).toFixed(0)}%
                </Badge>
              </div>
            )}

            {/* Text indicator */}
            {item.snippet && (
              <div className="absolute bottom-2 left-2">
                <Badge variant="secondary" className="backdrop-blur-sm px-1 py-0">
                  <FileText className="h-3 w-3" />
                </Badge>
              </div>
            )}
          </div>

          <CardContent className="p-2">
            <p className="text-xs font-medium truncate" title={item.filename}>
              {item.filename}
            </p>
            {item.shot_dt && (
              <p className="text-xs text-muted-foreground">
                {new Date(item.shot_dt).toLocaleDateString()}
              </p>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

export default function SearchPage() {
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchMode, setSearchMode] = useState<'text' | 'semantic' | 'image'>('text')
  const [filtersOpen, setFiltersOpen] = useState(false)

  // Lightbox store
  const { openLightbox } = useLightboxStore()

  // Search filters
  const [filters, setFilters] = useState({
    from: '',
    to: '',
    folder: '',
    limit: 50,
  })

  const handleSearch = async (query: string) => {
    if (!query.trim()) return

    setLoading(true)
    setError(null)

    try {
      let results: SearchResponse

      // Image mode handled separately by CompactSearchBar
      results =
        searchMode === 'semantic'
          ? await apiService.semanticSearch(query, filters.limit)
          : await apiService.searchPhotos({ q: query, ...filters })

      setSearchResults(results)
    } catch (err) {
      // Handle ML feature errors gracefully
      const errorMessage = err instanceof Error ? err.message : 'Search failed'
      if (
        errorMessage.includes('Semantic search failed') ||
        errorMessage.includes('No such file or directory')
      ) {
        setError(
          'Smart search needs additional setup. Using regular search instead.'
        )
        // Automatically switch to text search
        setSearchMode('text')
      } else {
        setError(errorMessage)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleImageSearch = async (file: File) => {
    setLoading(true)
    setError(null)

    try {
      const results = await apiService.imageSearch(file, filters.limit)
      setSearchResults(results)
    } catch (err) {
      // Handle ML feature errors gracefully
      const errorMessage =
        err instanceof Error ? err.message : 'Image search failed'
      if (
        errorMessage.includes('Image search failed') ||
        errorMessage.includes('No such file or directory')
      ) {
        setError(
          'Photo similarity search needs additional setup. Using regular search instead.'
        )
        // Automatically switch to text search
        setSearchMode('text')
      } else {
        setError(errorMessage)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleFilterChange = (newFilters: Partial<typeof filters>) => {
    if (newFilters.from === '' && newFilters.to === '' && newFilters.folder === '' && newFilters.limit === 50) {
      // Clear all filters
      setFilters({ from: '', to: '', folder: '', limit: 50 })
    } else {
      setFilters({ ...filters, ...newFilters })
    }
  }

  const handleItemClick = (item: SearchResult) => {
    if (!searchResults) return

    // Convert SearchResult[] to LightboxPhoto[]
    const lightboxPhotos: LightboxPhoto[] = searchResults.items.map(result => ({
      id: result.file_id.toString(),
      path: result.path,
      thumbnail_path: result.thumb_path ?? undefined,
      filename: result.filename,
      metadata: result.shot_dt ? { date_taken: result.shot_dt } : undefined,
      ocr_text: result.snippet ?? undefined,
      tags: result.badges,
    }))

    // Find the index of the clicked item
    const startIndex = searchResults.items.findIndex(
      r => r.file_id === item.file_id
    )

    // Open lightbox at the clicked photo
    openLightbox(lightboxPhotos, startIndex)
  }

  const handleRevealInFolder = async (item: SearchResult) => {
    try {
      await osIntegration.revealInFolder(item.path)
    } catch (error) {
      // Silent failure - error will be handled by osIntegration service
    }
  }



  return (
    <>
      {/* Compact Search Header */}
      <div className="bg-card border-b">
        <div className="p-4">
          <div className="max-w-7xl mx-auto">
            {/* Search Bar with integrated filters and mode icons */}
            <CompactSearchBar
              onSearch={handleSearch}
              onImageSearch={handleImageSearch}
              searchMode={searchMode}
              onSearchModeChange={setSearchMode}
              loading={loading}
              filters={filters}
              onFilterChange={handleFilterChange}
              filtersOpen={filtersOpen}
              onFiltersToggle={() => setFiltersOpen(!filtersOpen)}
            />
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-destructive/10 border-b border-destructive/30 p-3">
          <div className="max-w-7xl mx-auto flex items-center space-x-2">
            <AlertCircle className="h-4 w-4 text-destructive" />
            <p className="text-sm text-destructive">{error}</p>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 overflow-auto bg-background">
        <div className="max-w-[1920px] mx-auto p-4">
          {loading ? (
            // Loading skeleton
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-8 gap-3">
              {Array.from({ length: 24 }).map((_, i) => (
                <Card key={i} className="overflow-hidden">
                  <Skeleton className="aspect-square" />
                  <CardContent className="p-2">
                    <Skeleton className="h-3 w-3/4 mb-1" />
                    <Skeleton className="h-2 w-1/2" />
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : searchResults ? (
            <>
              {/* Results Header */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <h2 className="text-lg font-semibold">
                    {searchResults.items.length} results
                  </h2>
                  {searchResults.took_ms && (
                    <Badge variant="secondary" className="text-xs">
                      <Clock className="h-3 w-3 mr-1" />
                      {(searchResults.took_ms / 1000).toFixed(2)}s
                    </Badge>
                  )}
                </div>
              </div>

              {/* Results Grid */}
              <ResultsGrid
                results={searchResults.items}
                onItemClick={handleItemClick}
                onRevealInFolder={handleRevealInFolder}
              />
            </>
          ) : (
            // Empty state
            <div className="flex flex-col items-center justify-center py-24">
              <Search className="h-16 w-16 text-muted-foreground/30 mb-4" />
              <h3 className="text-xl font-semibold text-muted-foreground mb-2">
                Start searching your photos
              </h3>
              <p className="text-sm text-muted-foreground text-center max-w-md">
                Use Quick Find for filename and date searches, Smart Search to describe what you're looking for,
                or Similar Photos to find visually similar images.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Lightbox */}
      <Lightbox />
    </>
  )
}
