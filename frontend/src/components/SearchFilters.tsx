import { useState } from 'react'

interface SearchFilters {
  from: string
  to: string
  folder: string
  limit: number
}

interface SearchFiltersProps {
  filters: SearchFilters
  onChange: (filters: Partial<SearchFilters>) => void
}

export default function SearchFilters({
  filters,
  onChange,
}: SearchFiltersProps) {
  const [showFilters, setShowFilters] = useState(false)

  const handleChange = (key: string, value: string | number) => {
    onChange({ [key]: value })
  }

  return (
    <div className="mt-4">
      {/* Toggle Filters */}
      <button
        onClick={() => setShowFilters(!showFilters)}
        className="flex items-center space-x-2 text-sm text-muted-foreground hover:text-primary transition-colors"
      >
        <span>🔧</span>
        <span>Filters</span>
        <span
          className={`transform transition-transform ${showFilters ? 'rotate-180' : ''}`}
        >
          ▼
        </span>
      </button>

      {/* Filters Panel */}
      {showFilters && (
        <div className="mt-4 p-4 bg-card rounded-lg border border-border/50">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Date Range */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                From Date
              </label>
              <input
                type="date"
                value={filters.from}
                onChange={e => handleChange('from', e.target.value)}
                className="w-full px-3 py-2 border border-border/50 rounded-md bg-input text-foreground focus:ring-2 focus:ring-primary focus:border-primary transition-all"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                To Date
              </label>
              <input
                type="date"
                value={filters.to}
                onChange={e => handleChange('to', e.target.value)}
                className="w-full px-3 py-2 border border-border/50 rounded-md bg-input text-foreground focus:ring-2 focus:ring-primary focus:border-primary transition-all"
              />
            </div>

            {/* Folder Filter */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                Folder
              </label>
              <input
                type="text"
                placeholder="Filter by folder..."
                value={filters.folder}
                onChange={e => handleChange('folder', e.target.value)}
                className="w-full px-3 py-2 border border-border/50 rounded-md bg-input text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-primary focus:border-primary transition-all"
              />
            </div>

            {/* Results Limit */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                Results Limit
              </label>
              <select
                value={filters.limit}
                onChange={e => handleChange('limit', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-border/50 rounded-md bg-input text-foreground focus:ring-2 focus:ring-primary focus:border-primary transition-all"
              >
                <option value={10}>10 photos</option>
                <option value={25}>25 photos</option>
                <option value={50}>50 photos</option>
                <option value={100}>100 photos</option>
                <option value={200}>200 photos</option>
              </select>
            </div>
          </div>

          {/* Clear Filters */}
          <div className="mt-4">
            <button
              onClick={() =>
                onChange({ from: '', to: '', folder: '', limit: 50 })
              }
              className="px-4 py-2 text-sm bg-muted text-muted-foreground rounded-md hover:bg-muted/80 hover:text-foreground transition-all"
            >
              Clear All Filters
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
