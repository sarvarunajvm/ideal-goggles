import { useState, useRef } from 'react'

interface SearchBarProps {
  onSearch: (query: string) => void
  onImageSearch: (file: File) => void
  searchMode: 'text' | 'semantic' | 'image'
  loading: boolean
}

export default function SearchBar({
  onSearch,
  onImageSearch,
  searchMode,
  loading,
}: SearchBarProps) {
  const [query, setQuery] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchMode !== 'image' && query.trim()) {
      onSearch(query.trim())
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file && file.type.startsWith('image/')) {
      onImageSearch(file)
    }
  }

  const handleImageUpload = () => {
    fileInputRef.current?.click()
  }

  const placeholderText = {
    text: 'Search by filename, folder, or content...',
    semantic:
      'Describe what you\'re looking for (e.g., "sunset over mountains", "people at wedding")...',
    image: 'Click to upload an image for visual similarity search...',
  }

  return (
    <div className="w-full">
      {searchMode === 'image' ? (
        <div
          onClick={handleImageUpload}
          className={`w-full p-4 border-2 border-dashed rounded-lg cursor-pointer transition-all ${
            loading
              ? 'border-border/30 bg-muted/30 cursor-not-allowed'
                : 'border-primary/30 hover:border-primary/60 hover:bg-primary/5 hover:shadow-lg hover:shadow-primary/10'
          }`}
        >
          <div className="text-center">
            <div className="text-4xl mb-2">📸</div>
            <p className="text-lg font-medium text-foreground">
              {loading ? 'Processing image...' : 'Upload an image to search'}
            </p>
            <p className="text-sm text-muted-foreground mt-1">
              Click here or drag and drop an image file
            </p>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            className="hidden"
            disabled={loading}
          />
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="relative">
          <div className="relative">
            <input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder={placeholderText[searchMode]}
              disabled={loading}
              className={`w-full px-4 py-3 pr-12 text-lg border border-border/50 rounded-lg transition-all bg-input text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-primary focus:border-primary focus:shadow-lg focus:shadow-primary/20 ${
                loading ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className={`absolute right-2 top-1/2 transform -translate-y-1/2 px-4 py-2 rounded-md transition-all ${
                loading || !query.trim()
                  ? 'bg-muted text-muted-foreground cursor-not-allowed'
                  : 'bg-primary text-primary-foreground hover:bg-primary/90 shadow-md hover:shadow-lg hover:shadow-primary/25'
              }`}
            >
              {loading ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-foreground"></div>
              ) : (
                '🔍'
              )}
            </button>
          </div>
        </form>
      )}
    </div>
  )
}
