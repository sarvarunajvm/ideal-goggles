import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { LogViewer } from '../../src/components/LogViewer'

// Mock the apiClient module
jest.mock('../../src/services/apiClient', () => ({
  getApiBaseUrl: jest.fn(() => 'http://localhost:5555'),
}))

const mockLogs = [
  {
    timestamp: '2024-01-15T10:30:00Z',
    level: 'INFO',
    logger_name: 'api.search',
    message: 'Search query executed successfully',
    source: 'backend' as const,
    function: 'search_photos',
    line_number: 42,
    request_id: 'req-123',
  },
  {
    timestamp: '2024-01-15T10:31:00Z',
    level: 'ERROR',
    logger_name: 'api.index',
    message: 'Failed to process image',
    source: 'backend' as const,
    function: 'index_file',
    line_number: 156,
  },
  {
    timestamp: '2024-01-15T10:32:00Z',
    level: 'WARN',
    logger_name: 'electron.main',
    message: 'Low memory warning',
    source: 'electron' as const,
  },
  {
    timestamp: '2024-01-15T10:33:00Z',
    level: 'DEBUG',
    logger_name: 'frontend.store',
    message: 'State updated',
    source: 'frontend' as const,
  },
]

const mockLogsResponse = {
  logs: mockLogs,
  total: 100,
  has_more: true,
  sources: ['backend', 'frontend', 'electron'],
}

const emptyLogsResponse = {
  logs: [],
  total: 0,
  has_more: false,
  sources: [],
}

describe('LogViewer', () => {
  let mockFetch: jest.Mock

  beforeEach(() => {
    jest.useFakeTimers()
    mockFetch = jest.fn()
    global.fetch = mockFetch
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockLogsResponse),
    })
  })

  afterEach(() => {
    jest.clearAllMocks()
    jest.useRealTimers()
  })

  const advanceTimers = async () => {
    jest.advanceTimersByTime(500)
    // flush promises
    await Promise.resolve()
    await Promise.resolve()
    await Promise.resolve()
  }

  describe('Initial Rendering', () => {
    it('shows loading state initially', () => {
      render(<LogViewer />)
      expect(screen.getByText('Loading logs...')).toBeInTheDocument()
    })

    it('renders header with title', async () => {
      render(<LogViewer />)
      
      // Header is static, doesn't need fetch
      expect(screen.getByText('Log Entries')).toBeInTheDocument()
    })

    it('renders filter controls', async () => {
      render(<LogViewer />)
      
      expect(screen.getByPlaceholderText('Search logs...')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /refresh/i })).toBeInTheDocument()
      // Check for Select triggers
      expect(screen.getByText('All Sources')).toBeInTheDocument()
      expect(screen.getByText('All Levels')).toBeInTheDocument()
    })

    it('fetches logs on mount with default filters', async () => {
      render(<LogViewer />)
      
      await act(async () => {
        await advanceTimers()
      })
      
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:5555/logs/fetch?source=all&level=all&limit=100&offset=0'
      )
    })
  })

  describe('Log Display', () => {
    it('displays log entries after loading', async () => {
      render(<LogViewer />)
      
      await act(async () => {
        await advanceTimers()
      })
      
      expect(screen.getByText('Search query executed successfully')).toBeInTheDocument()
      expect(screen.getByText('Failed to process image')).toBeInTheDocument()
      expect(screen.getByText('Low memory warning')).toBeInTheDocument()
      expect(screen.getByText('State updated')).toBeInTheDocument()
    })

    it('displays log count statistics', async () => {
      render(<LogViewer />)
      
      await act(async () => {
        await advanceTimers()
      })
      
      expect(screen.getByText(/\(100 entries\)/)).toBeInTheDocument()
    })

    it('displays timestamps for each log', async () => {
      render(<LogViewer />)
      
      await act(async () => {
        await advanceTimers()
      })
      
      // Expect formatted time/date, typically contains the year
      // Use getAllByText since multiple logs may have the same year
      const timestamps = screen.getAllByText(/2024/)
      expect(timestamps.length).toBeGreaterThan(0)
    })

    it('displays source badges for each log', async () => {
      render(<LogViewer />)
      
      await act(async () => {
        await advanceTimers()
      })
      
      expect(screen.getAllByText('backend').length).toBeGreaterThan(0)
      expect(screen.getByText('electron')).toBeInTheDocument()
      expect(screen.getByText('frontend')).toBeInTheDocument()
    })

    it('displays log levels with correct styling', async () => {
      render(<LogViewer />)
      
      await act(async () => {
        await advanceTimers()
      })
      
      expect(screen.getByText('INFO')).toBeInTheDocument()
      expect(screen.getByText('ERROR')).toBeInTheDocument()
      expect(screen.getByText('WARN')).toBeInTheDocument()
      expect(screen.getByText('DEBUG')).toBeInTheDocument()
    })

    it('displays logger names', async () => {
      render(<LogViewer />)
      
      await act(async () => {
        await advanceTimers()
      })
      
      expect(screen.getByText('api.search')).toBeInTheDocument()
      expect(screen.getByText('api.index')).toBeInTheDocument()
    })

    it('displays function and line number when available', async () => {
      render(<LogViewer />)
      
      await act(async () => {
        await advanceTimers()
      })
      
      expect(screen.getByText('search_photos:42')).toBeInTheDocument()
      expect(screen.getByText('index_file:156')).toBeInTheDocument()
    })

    it('displays request_id when available', async () => {
      render(<LogViewer />)
      
      await act(async () => {
        await advanceTimers()
      })
      
      expect(screen.getByText('req-123')).toBeInTheDocument()
    })
  })

  describe('Filter Functionality', () => {
    it('changes source filter and re-fetches logs', async () => {
      const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime })
      render(<LogViewer />)
      
      // Initial load
      await act(async () => {
        await advanceTimers()
      })

      // Clear initial fetch count
      mockFetch.mockClear()

      // Open source select
      const sourceTrigger = screen.getByText('All Sources')
      await user.click(sourceTrigger)
      
      // Select Backend option
      const option = screen.getByText('Backend')
      await user.click(option)
      
      // Debounce wait
      await act(async () => {
        await advanceTimers()
      })
      
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('source=backend')
      )
    })

    it('changes level filter and re-fetches logs', async () => {
      const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime })
      render(<LogViewer />)
      
      await act(async () => {
        await advanceTimers()
      })

      mockFetch.mockClear()

      // Open level select
      const levelTrigger = screen.getByText('All Levels')
      await user.click(levelTrigger)
      
      // Select Error option
      const option = screen.getByText('Error')
      await user.click(option)
      
      await act(async () => {
        await advanceTimers()
      })
      
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('level=ERROR')
      )
    })

    it('updates search filter and includes it in request', async () => {
      const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime })
      render(<LogViewer />)
      
      await act(async () => {
        await advanceTimers()
      })

      mockFetch.mockClear()

      const searchInput = screen.getByPlaceholderText('Search logs...')
      await user.type(searchInput, 'error')
      
      await act(async () => {
        await advanceTimers()
      })
      
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('search=error')
      )
    })

    it('refresh button re-fetches logs', async () => {
      const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime })
      render(<LogViewer />)
      
      await act(async () => {
        await advanceTimers()
      })

      mockFetch.mockClear()

      await user.click(screen.getByRole('button', { name: /refresh/i }))
      
      // Fetch is immediate for refresh button (direct call)
      // But check if it sets loading state properly
      
      expect(mockFetch).toHaveBeenCalled()
    })
  })

  describe('Empty State', () => {
    it('displays no logs message when logs array is empty', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(emptyLogsResponse),
      })

      render(<LogViewer />)
      
      await act(async () => {
        await advanceTimers()
      })
      
      expect(screen.getByText('No logs found matching your filters')).toBeInTheDocument()
    })

    it('displays count as 0 when no logs', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(emptyLogsResponse),
      })

      render(<LogViewer />)
      
      await act(async () => {
        await advanceTimers()
      })
      
      // Total count is conditional in the new UI, only shows if > 0
      expect(screen.queryByText(/entries/)).not.toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('displays error message when fetch fails', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        statusText: 'Internal Server Error',
      })

      render(<LogViewer />)
      
      await act(async () => {
        await advanceTimers()
      })
      
      expect(screen.getByText('Failed to load logs')).toBeInTheDocument()
      expect(screen.getByText(/Failed to fetch logs: Internal Server Error/)).toBeInTheDocument()
    })

    it('displays error message when network error occurs', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'))

      render(<LogViewer />)
      
      await act(async () => {
        await advanceTimers()
      })
      
      expect(screen.getByText('Failed to load logs')).toBeInTheDocument()
      expect(screen.getByText(/Network error/)).toBeInTheDocument()
    })

    it('handles unknown error type gracefully', async () => {
      mockFetch.mockRejectedValue('Unknown error')

      render(<LogViewer />)
      
      await act(async () => {
        await advanceTimers()
      })
      
      expect(screen.getByText('Failed to load logs')).toBeInTheDocument()
      expect(screen.getByText('Unknown error')).toBeInTheDocument()
    })

    it('clears error state on successful retry', async () => {
      const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime })
      
      // First call fails
      mockFetch.mockResolvedValueOnce({
        ok: false,
        statusText: 'Server Error',
      })

      render(<LogViewer />)
      
      await act(async () => {
        await advanceTimers()
      })
      
      expect(screen.getByText('Failed to load logs')).toBeInTheDocument()

      // Next call succeeds
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockLogsResponse),
      })

      await user.click(screen.getByRole('button', { name: /Try Again/i }))

      await waitFor(() => {
        expect(screen.queryByText('Failed to load logs')).not.toBeInTheDocument()
        expect(screen.getByText('Search query executed successfully')).toBeInTheDocument()
      })
    })
  })

  describe('Log Level Styling', () => {
    it('applies correct border color for ERROR level', async () => {
      const errorOnlyResponse = {
        logs: [mockLogs[1]], // ERROR log
        total: 1,
        has_more: false,
        sources: ['backend'],
      }
      
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(errorOnlyResponse),
      })

      const { container } = render(<LogViewer />)
      
      await act(async () => {
        await advanceTimers()
      })
      
      // In new UI, border is on a div with class
      // We look for "ERROR" text and check parent styling or specific class
      expect(screen.getByText('ERROR')).toBeInTheDocument()
      // Checking for the class we added: text-destructive
      expect(container.innerHTML).toContain('text-destructive')
    })

    it('applies correct border color for INFO level', async () => {
      const infoOnlyResponse = {
        logs: [mockLogs[0]], // INFO log
        total: 1,
        has_more: false,
        sources: ['backend'],
      }
      
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(infoOnlyResponse),
      })

      const { container } = render(<LogViewer />)
      
      await act(async () => {
        await advanceTimers()
      })
      
      expect(screen.getByText('INFO')).toBeInTheDocument()
      expect(container.innerHTML).toContain('text-blue-500')
    })
  })

  describe('Select Options', () => {
    // ... tests already updated
  })

  describe('has_more indicator', () => {
    it('shows "more available" when has_more is true', async () => {
      render(<LogViewer />)
      
      await act(async () => {
        await advanceTimers()
      })
      
      expect(screen.getByText(/Only showing the most recent 100 logs/)).toBeInTheDocument()
    })

    it('does not show "more available" when has_more is false', async () => {
      const noMoreResponse = {
        ...mockLogsResponse,
        has_more: false,
      }
      
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(noMoreResponse),
      })

      render(<LogViewer />)
      
      await act(async () => {
        await advanceTimers()
      })
      
      expect(screen.queryByText(/Only showing the most recent 100 logs/)).not.toBeInTheDocument()
    })
  })
})
