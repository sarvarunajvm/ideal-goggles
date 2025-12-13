/**
 * LogViewer Component
 * Unified log viewer for backend, frontend, and Electron logs
 */

import { useEffect, useState } from 'react'
import { getApiBaseUrl } from '../services/apiClient'

interface LogLine {
  timestamp: string
  level: string
  logger_name: string
  message: string
  source: 'backend' | 'frontend' | 'electron'
  function?: string
  line_number?: number
  request_id?: string
}

interface LogsResponse {
  logs: LogLine[]
  total: number
  has_more: boolean
  sources: string[]
}

export function LogViewer() {
  const [logs, setLogs] = useState<LogLine[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filters, setFilters] = useState({
    source: 'all',
    level: 'all',
    search: '',
  })
  const [total, setTotal] = useState(0)
  const [hasMore, setHasMore] = useState(false)

  useEffect(() => {
    fetchLogs()
  }, [filters])

  const fetchLogs = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const params = new URLSearchParams({
        source: filters.source,
        level: filters.level,
        limit: '100',
        offset: '0',
      })
      
      if (filters.search) {
        params.append('search', filters.search)
      }
      
      const response = await fetch(`${getApiBaseUrl()}/logs/fetch?${params}`)
      
      if (!response.ok) {
        throw new Error(`Failed to fetch logs: ${response.statusText}`)
      }
      
      const data: LogsResponse = await response.json()
      setLogs(data.logs)
      setTotal(data.total)
      setHasMore(data.has_more)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const getLevelColor = (level: string): string => {
    switch (level) {
      case 'DEBUG':
        return 'text-gray-500'
      case 'INFO':
        return 'text-blue-500'
      case 'WARN':
        return 'text-yellow-500'
      case 'ERROR':
        return 'text-red-500'
      default:
        return 'text-gray-400'
    }
  }

  const getSourceBadge = (source: string): string => {
    switch (source) {
      case 'backend':
        return 'bg-purple-100 text-purple-800'
      case 'frontend':
        return 'bg-green-100 text-green-800'
      case 'electron':
        return 'bg-blue-100 text-blue-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-900">
      {/* Header */}
      <div className="border-b border-gray-200 dark:border-gray-700 p-4">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          System Logs
        </h2>
        
        {/* Filters */}
        <div className="flex gap-4 flex-wrap">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Source
            </label>
            <select
              value={filters.source}
              onChange={(e) => setFilters({ ...filters, source: e.target.value })}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            >
              <option value="all">All Sources</option>
              <option value="backend">Backend</option>
              <option value="frontend">Frontend</option>
              <option value="electron">Electron</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Level
            </label>
            <select
              value={filters.level}
              onChange={(e) => setFilters({ ...filters, level: e.target.value })}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            >
              <option value="all">All Levels</option>
              <option value="DEBUG">Debug</option>
              <option value="INFO">Info</option>
              <option value="WARN">Warning</option>
              <option value="ERROR">Error</option>
            </select>
          </div>
          
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Search
            </label>
            <input
              type="text"
              placeholder="Search logs..."
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400"
            />
          </div>
          
          <div className="flex items-end">
            <button
              onClick={fetchLogs}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
            >
              Refresh
            </button>
          </div>
        </div>
        
        {/* Stats */}
        <div className="mt-3 text-sm text-gray-600 dark:text-gray-400">
          Showing {logs.length} of {total} logs
          {hasMore && ' (more available)'}
        </div>
      </div>

      {/* Log Entries */}
      <div className="flex-1 overflow-auto p-4 font-mono text-xs">
        {loading && (
          <div className="text-center text-gray-500 py-8">Loading logs...</div>
        )}
        
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-4 text-red-800 dark:text-red-200">
            <strong>Error:</strong> {error}
          </div>
        )}
        
        {!loading && !error && logs.length === 0 && (
          <div className="text-center text-gray-500 py-8">No logs found</div>
        )}
        
        {!loading && !error && logs.length > 0 && (
          <div className="space-y-1">
            {logs.map((log, index) => (
              <div
                key={index}
                className="group hover:bg-gray-50 dark:hover:bg-gray-800 p-2 rounded border-l-4"
                style={{
                  borderLeftColor:
                    log.level === 'ERROR'
                      ? '#ef4444'
                      : log.level === 'WARN'
                      ? '#f59e0b'
                      : log.level === 'INFO'
                      ? '#3b82f6'
                      : '#9ca3af',
                }}
              >
                <div className="flex items-start gap-2">
                  {/* Timestamp */}
                  <span className="text-gray-500 dark:text-gray-400 whitespace-nowrap">
                    {log.timestamp}
                  </span>
                  
                  {/* Source Badge */}
                  <span
                    className={`px-2 py-0.5 rounded text-xs font-medium ${getSourceBadge(
                      log.source
                    )}`}
                  >
                    {log.source}
                  </span>
                  
                  {/* Level */}
                  <span className={`font-semibold ${getLevelColor(log.level)} w-12`}>
                    {log.level}
                  </span>
                  
                  {/* Logger Name */}
                  <span className="text-gray-600 dark:text-gray-400 truncate max-w-[200px]">
                    {log.logger_name}
                  </span>
                  
                  {/* Function:Line */}
                  {log.function && (
                    <span className="text-gray-500 dark:text-gray-500 text-xs">
                      {log.function}:{log.line_number}
                    </span>
                  )}
                  
                  {/* Message */}
                  <span className="flex-1 text-gray-900 dark:text-gray-100 break-words">
                    {log.message}
                  </span>
                  
                  {/* Request ID */}
                  {log.request_id && (
                    <span className="text-gray-400 dark:text-gray-600 text-xs">
                      [{log.request_id}]
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
