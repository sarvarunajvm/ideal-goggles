import React, { useState, useEffect, useRef, useCallback } from 'react'

interface Photo {
  id: number
  path: string
  thumbnail?: string
  name?: string
  date?: string
  size?: number
  url?: string
  title?: string
}

interface PhotoGridProps {
  photos: Photo[]
  loading?: boolean
  onPhotoClick?: (photo: Photo) => void
  onPhotoSelect?: (photos: Photo[]) => void
  onLoadMore?: () => void
  hasMore?: boolean
  selectable?: boolean
  showSelectAll?: boolean
  layout?: 'grid' | 'masonry' | 'list'
  columns?: number
}

const PhotoGrid: React.FC<PhotoGridProps> = ({
  photos,
  loading = false,
  onPhotoClick,
  onPhotoSelect,
  onLoadMore,
  hasMore = false,
  selectable = false,
  showSelectAll = false,
  layout = 'grid',
  columns = 4,
}) => {
  const [selectedPhotos, setSelectedPhotos] = useState<Set<number>>(new Set())
  const [hoveredPhoto, setHoveredPhoto] = useState<number | null>(null)
  const [zoomedPhoto, setZoomedPhoto] = useState<Photo | null>(null)
  const [focusedIndex, setFocusedIndex] = useState<number>(0)
  const loadMoreRef = useRef<HTMLDivElement>(null)
  const gridRef = useRef<HTMLDivElement>(null)

  // Handle selection changes
  useEffect(() => {
    if (onPhotoSelect && selectable) {
      const selected = photos.filter(p => selectedPhotos.has(p.id))
      onPhotoSelect(selected)
    }
  }, [selectedPhotos, photos, onPhotoSelect, selectable])

  // Lazy loading with Intersection Observer
  useEffect(() => {
    if (!hasMore || !onLoadMore || loading) return

    const observer = new IntersectionObserver(
      entries => {
        if (entries[0].isIntersecting) {
          onLoadMore()
        }
      },
      { threshold: 0.1 }
    )

    if (loadMoreRef.current) {
      observer.observe(loadMoreRef.current)
    }

    return () => observer.disconnect()
  }, [hasMore, onLoadMore, loading])

  const handlePhotoClick = useCallback(
    (photo: Photo) => {
      if (selectable) {
        setSelectedPhotos(prev => {
          const newSet = new Set(prev)
          if (newSet.has(photo.id)) {
            newSet.delete(photo.id)
          } else {
            newSet.add(photo.id)
          }
          return newSet
        })
      } else if (onPhotoClick) {
        onPhotoClick(photo)
      }
    },
    [selectable, onPhotoClick]
  )

  const handleSelectAll = useCallback(() => {
    if (selectedPhotos.size === photos.length) {
      setSelectedPhotos(new Set())
    } else {
      setSelectedPhotos(new Set(photos.map(p => p.id)))
    }
  }, [photos, selectedPhotos.size])

  const handleDoubleClick = useCallback((photo: Photo) => {
    setZoomedPhoto(photo)
  }, [])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (!photos.length) return

      switch (e.key) {
        case 'ArrowRight':
          setFocusedIndex(prev => Math.min(prev + 1, photos.length - 1))
          break
        case 'ArrowLeft':
          setFocusedIndex(prev => Math.max(prev - 1, 0))
          break
        case 'ArrowDown':
          setFocusedIndex(prev => Math.min(prev + columns, photos.length - 1))
          break
        case 'ArrowUp':
          setFocusedIndex(prev => Math.max(prev - columns, 0))
          break
        case 'Enter':
        case ' ':
          e.preventDefault()
          handlePhotoClick(photos[focusedIndex])
          break
      }
    },
    [photos, focusedIndex, columns, handlePhotoClick]
  )

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return ''
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + ' ' + sizes[i]
  }

  const getGridClass = () => {
    switch (layout) {
      case 'masonry':
        return 'columns-1 sm:columns-2 md:columns-3 lg:columns-4 gap-4'
      case 'list':
        return 'flex flex-col space-y-2'
      default:
        return `grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-${columns} gap-4`
    }
  }

  if (loading && photos.length === 0) {
    return (
      <div className="flex justify-center items-center h-64" role="status">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        <span className="sr-only">Loading...</span>
      </div>
    )
  }

  if (!loading && photos.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <svg
          className="mx-auto h-12 w-12 text-gray-400"
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
        <p className="mt-2">No photos found</p>
      </div>
    )
  }

  return (
    <div className="photo-grid-container">
      {selectable && showSelectAll && (
        <div className="mb-4 flex items-center">
          <input
            type="checkbox"
            checked={selectedPhotos.size === photos.length && photos.length > 0}
            onChange={handleSelectAll}
            className="mr-2"
            aria-label="Select all photos"
          />
          <label>
            Select All ({selectedPhotos.size}/{photos.length})
          </label>
        </div>
      )}

      <div
        ref={gridRef}
        className={getGridClass()}
        role="grid"
        onKeyDown={handleKeyDown}
        tabIndex={0}
      >
        {photos.map((photo, index) => (
          <div
            key={photo.id}
            className={`photo-item relative group cursor-pointer transition-all ${
              layout === 'list'
                ? 'flex items-center space-x-4 p-2 hover:bg-gray-50'
                : ''
            } ${focusedIndex === index ? 'ring-2 ring-primary' : ''}`}
            onClick={() => handlePhotoClick(photo)}
            onDoubleClick={() => handleDoubleClick(photo)}
            onMouseEnter={() => setHoveredPhoto(photo.id)}
            onMouseLeave={() => setHoveredPhoto(null)}
            role="gridcell"
            aria-selected={selectedPhotos.has(photo.id)}
            tabIndex={index === focusedIndex ? 0 : -1}
          >
            {selectable && (
              <input
                type="checkbox"
                checked={selectedPhotos.has(photo.id)}
                onChange={e => {
                  e.stopPropagation()
                  setSelectedPhotos(prev => {
                    const newSet = new Set(prev)
                    if (newSet.has(photo.id)) {
                      newSet.delete(photo.id)
                    } else {
                      newSet.add(photo.id)
                    }
                    return newSet
                  })
                }}
                onClick={e => e.stopPropagation()}
                className="absolute top-2 left-2 z-10"
                aria-label={`Select ${photo.name || `photo ${photo.id}`}`}
              />
            )}

            <img
              src={photo.thumbnail || photo.url || photo.path}
              alt={photo.name || photo.title || `Photo ${photo.id}`}
              className={`w-full h-auto object-cover rounded-lg ${
                layout === 'list' ? 'w-20 h-20' : ''
              }`}
              loading="lazy"
              onMouseEnter={() => setHoveredPhoto(photo.id)}
              onMouseLeave={() => setHoveredPhoto(null)}
            />

            {hoveredPhoto === photo.id && (
              <div className="absolute inset-0 bg-black bg-opacity-50 flex flex-col justify-between p-2 rounded-lg">
                <div className="text-white text-sm">
                  <p className="truncate">{photo.name || photo.title}</p>
                  <p>{photo.date}</p>
                  <p>{formatFileSize(photo.size)}</p>
                </div>
                <a
                  href={photo.thumbnail || photo.url || photo.path}
                  download={photo.name || `photo-${photo.id}`}
                  onClick={e => e.stopPropagation()}
                  className="self-end bg-white text-gray-800 px-2 py-1 rounded text-sm hover:bg-gray-200"
                  aria-label={`Download ${photo.name || `photo ${photo.id}`}`}
                >
                  Download
                </a>
              </div>
            )}

            {selectedPhotos.has(photo.id) && (
              <div className="absolute inset-0 rounded-lg pointer-events-none bg-primary/20"></div>
            )}
          </div>
        ))}
      </div>

      {hasMore && (
        <div
          ref={loadMoreRef}
          className="h-20 flex justify-center items-center"
        >
          {loading ? (
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          ) : (
            <button
              onClick={onLoadMore}
              className="px-4 py-2 rounded bg-primary text-primary-foreground hover:bg-primary/90"
            >
              Load More
            </button>
          )}
        </div>
      )}

      {zoomedPhoto && (
        <div
          className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50"
          onClick={() => setZoomedPhoto(null)}
        >
          <img
            src={zoomedPhoto.path || zoomedPhoto.url || zoomedPhoto.thumbnail}
            alt={zoomedPhoto.name || `Photo ${zoomedPhoto.id}`}
            className="max-w-full max-h-full"
          />
        </div>
      )}
    </div>
  )
}

export default PhotoGrid
