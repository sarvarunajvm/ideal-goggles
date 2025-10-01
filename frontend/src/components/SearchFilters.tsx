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
        className="flex items-center space-x-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
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
        <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Date Range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                From Date
              </label>
              <input
                type="date"
                value={filters.from}
                onChange={e => handleChange('from', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                To Date
              </label>
              <input
                type="date"
                value={filters.to}
                onChange={e => handleChange('to', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Folder Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Folder
              </label>
              <input
                type="text"
                placeholder="Filter by folder..."
                value={filters.folder}
                onChange={e => handleChange('folder', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Results Limit */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Results Limit
              </label>
              <select
                value={filters.limit}
                onChange={e => handleChange('limit', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
              className="px-4 py-2 text-sm bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
            >
              Clear All Filters
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
