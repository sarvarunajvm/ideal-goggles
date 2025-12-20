/**
 * LogViewer Component
 * Unified log viewer for backend, frontend, and Electron logs
 */

import { useEffect, useState } from 'react'
import { getApiBaseUrl } from '../services/apiClient'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
} from '@/components/ui/select'
import { RefreshCw, Search, AlertCircle, Info, Terminal } from 'lucide-react'

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

  // Debounce all filter changes
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchLogs()
    }, 300)
    return () => clearTimeout(timer)
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

  const getLevelColorClass = (level: string) => {
    switch (level) {
      case 'ERROR':
        return 'text-destructive border-destructive/50 bg-destructive/10'
      case 'WARN':
        return 'text-orange-500 border-orange-500/50 bg-orange-500/10'
      case 'INFO':
        return 'text-blue-500 border-blue-500/50 bg-blue-500/10'
      case 'DEBUG':
        return 'text-muted-foreground border-muted/50 bg-muted/10'
      default:
        return 'text-foreground border-border bg-card'
    }
  }

  const getSourceColor = (source: string) => {
    switch (source) {
      case 'backend':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300'
      case 'frontend':
        return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
      case 'electron':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300'
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300'
    }
  }

  return (
    <Card className="h-full flex flex-col shadow-sm">
      <CardHeader className="pb-3 border-b">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <CardTitle className="text-lg font-medium flex items-center gap-2">
            <Terminal className="h-5 w-5" />
            Log Entries
            {total > 0 && (
              <span className="text-sm font-normal text-muted-foreground ml-2">
                ({total} entries)
              </span>
            )}
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={fetchLogs}
              disabled={loading}
              className="h-9"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-4">
          <div className="md:col-span-2">
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search logs..."
                value={filters.search}
                onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                className="pl-9"
              />
            </div>
          </div>
          
          <div>
            <Select
              value={filters.source}
              onValueChange={(v) => setFilters({ ...filters, source: v })}
            >
              <SelectTrigger>
                <span className="truncate">
                  {filters.source === 'all' ? 'All Sources' : filters.source}
                </span>
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Sources</SelectItem>
                <SelectItem value="backend">Backend</SelectItem>
                <SelectItem value="frontend">Frontend</SelectItem>
                <SelectItem value="electron">Electron</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Select
              value={filters.level}
              onValueChange={(v) => setFilters({ ...filters, level: v })}
            >
              <SelectTrigger>
                <span className="truncate">
                  {filters.level === 'all' ? 'All Levels' : filters.level}
                </span>
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Levels</SelectItem>
                <SelectItem value="DEBUG">Debug</SelectItem>
                <SelectItem value="INFO">Info</SelectItem>
                <SelectItem value="WARN">Warning</SelectItem>
                <SelectItem value="ERROR">Error</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex-1 overflow-hidden p-0 bg-muted/5">
        {loading && logs.length === 0 ? (
          <div className="flex items-center justify-center h-64 text-muted-foreground">
            <RefreshCw className="h-6 w-6 animate-spin mr-2" />
            Loading logs...
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center h-64 text-destructive p-4 text-center">
            <AlertCircle className="h-8 w-8 mb-2" />
            <p className="font-medium">Failed to load logs</p>
            <p className="text-sm opacity-80">{error}</p>
            <Button variant="outline" size="sm" onClick={fetchLogs} className="mt-4">
              Try Again
            </Button>
          </div>
        ) : logs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
            <Info className="h-8 w-8 mb-2 opacity-50" />
            <p>No logs found matching your filters</p>
          </div>
        ) : (
          <div className="h-full overflow-auto p-4 space-y-2 font-mono text-sm">
            {logs.map((log, index) => (
              <div
                key={index}
                className={`p-3 rounded-lg border flex flex-col sm:flex-row gap-2 sm:gap-4 items-start hover:bg-card/50 transition-colors ${getLevelColorClass(
                  log.level
                )}`}
              >
                <div className="flex flex-col sm:w-48 shrink-0 gap-1">
                  <span className="text-xs opacity-70">
                    {new Date(log.timestamp).toLocaleString()}
                  </span>
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded uppercase font-bold tracking-wider border ${
                      log.level === 'ERROR' ? 'border-destructive/30 bg-destructive/10' :
                      log.level === 'WARN' ? 'border-orange-500/30 bg-orange-500/10' :
                      log.level === 'INFO' ? 'border-blue-500/30 bg-blue-500/10' :
                      'border-muted/30 bg-muted/10'
                    }`}>
                      {log.level}
                    </span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${getSourceColor(log.source)}`}>
                      {log.source}
                    </span>
                  </div>
                </div>

                <div className="flex-1 min-w-0 space-y-1">
                  <div className="flex items-center gap-2 text-xs opacity-60">
                    <span className="font-semibold truncate">
                      {log.logger_name}
                    </span>
                    {log.function && (
                      <>
                        <span>•</span>
                        <span className="truncate">
                          {log.function}:{log.line_number}
                        </span>
                      </>
                    )}
                    {log.request_id && (
                      <>
                        <span>•</span>
                        <span className="truncate font-mono">
                          {log.request_id.substring(0, 8)}
                        </span>
                      </>
                    )}
                  </div>
                  <p className="whitespace-pre-wrap break-words leading-relaxed">
                    {log.message}
                  </p>
                </div>
              </div>
            ))}
            
            {hasMore && (
              <div className="text-center py-4 text-xs text-muted-foreground">
                Only showing the most recent 100 logs. Use search to find specific entries.
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
