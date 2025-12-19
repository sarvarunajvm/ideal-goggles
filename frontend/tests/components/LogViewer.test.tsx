import { render, screen, waitFor, within } from '@testing-library/react'
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
    mockFetch = jest.fn()
    global.fetch = mockFetch
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockLogsResponse),
    })
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  describe('Initial Rendering', () => {
    it('shows loading state initially', () => {
      render(<LogViewer />)
      expect(screen.getByText('Loading logs...')).toBeInTheDocument()
    })

    it('renders header with title', async () => {
      render(<LogViewer />)
      
      await waitFor(() => {
        expect(screen.getByText('System Logs')).toBeInTheDocument()
      })
    })

    it('renders filter controls', async () => {
      render(<LogViewer />)
      
      await waitFor(() => {
        expect(screen.getByText('Source')).toBeInTheDocument()
        expect(screen.getByText('Level')).toBeInTheDocument()
        expect(screen.getByText('Search')).toBeInTheDocument()
        expect(screen.getByPlaceholderText('Search logs...')).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /refresh/i })).toBeInTheDocument()
      })
    })

    it('fetches logs on mount with default filters', async () => {
      render(<LogViewer />)
      
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          'http://localhost:5555/logs/fetch?source=all&level=all&limit=100&offset=0'
        )
      })
    })
  })

  describe('Log Display', () => {
    it('displays log entries after loading', async () => {
      render(<LogViewer />)
      
      await waitFor(() => {
        expect(screen.getByText('Search query executed successfully')).toBeInTheDocument()
        expect(screen.getByText('Failed to process image')).toBeInTheDocument()
        expect(screen.getByText('Low memory warning')).toBeInTheDocument()
        expect(screen.getByText('State updated')).toBeInTheDocument()
      })
    })

    it('displays log count statistics', async () => {
      render(<LogViewer />)
      
      await waitFor(() => {
        expect(screen.getByText(/Showing 4 of 100 logs/)).toBeInTheDocument()
        expect(screen.getByText(/\(more available\)/)).toBeInTheDocument()
      })
    })

    it('displays timestamps for each log', async () => {
      render(<LogViewer />)
      
      await waitFor(() => {
        expect(screen.getByText('2024-01-15T10:30:00Z')).toBeInTheDocument()
      })
    })

    it('displays source badges for each log', async () => {
      render(<LogViewer />)
      
      await waitFor(() => {
        expect(screen.getAllByText('backend').length).toBeGreaterThan(0)
        expect(screen.getByText('electron')).toBeInTheDocument()
        expect(screen.getByText('frontend')).toBeInTheDocument()
      })
    })

    it('displays log levels with correct styling', async () => {
      render(<LogViewer />)
      
      await waitFor(() => {
        expect(screen.getByText('INFO')).toBeInTheDocument()
        expect(screen.getByText('ERROR')).toBeInTheDocument()
        expect(screen.getByText('WARN')).toBeInTheDocument()
        expect(screen.getByText('DEBUG')).toBeInTheDocument()
      })
    })

    it('displays logger names', async () => {
      render(<LogViewer />)
      
      await waitFor(() => {
        expect(screen.getByText('api.search')).toBeInTheDocument()
        expect(screen.getByText('api.index')).toBeInTheDocument()
      })
    })

    it('displays function and line number when available', async () => {
      render(<LogViewer />)
      
      await waitFor(() => {
        expect(screen.getByText('search_photos:42')).toBeInTheDocument()
        expect(screen.getByText('index_file:156')).toBeInTheDocument()
      })
    })

    it('displays request_id when available', async () => {
      render(<LogViewer />)
      
      await waitFor(() => {
        expect(screen.getByText('[req-123]')).toBeInTheDocument()
      })
    })
  })

  describe('Filter Functionality', () => {
    it('changes source filter and re-fetches logs', async () => {
      const user = userEvent.setup()
      render(<LogViewer />)
      
      await waitFor(() => {
        expect(screen.getByText('System Logs')).toBeInTheDocument()
      })

      // Clear initial fetch count
      mockFetch.mockClear()

      const sourceSelect = screen.getAllByRole('combobox')[0]
      await user.selectOptions(sourceSelect, 'backend')
      
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('source=backend')
        )
      })
    })

    it('changes level filter and re-fetches logs', async () => {
      const user = userEvent.setup()
      render(<LogViewer />)
      
      await waitFor(() => {
        expect(screen.getByText('System Logs')).toBeInTheDocument()
      })

      mockFetch.mockClear()

      const levelSelect = screen.getAllByRole('combobox')[1]
      await user.selectOptions(levelSelect, 'ERROR')
      
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('level=ERROR')
        )
      })
    })

    it('updates search filter and includes it in request', async () => {
      const user = userEvent.setup()
      render(<LogViewer />)
      
      await waitFor(() => {
        expect(screen.getByText('System Logs')).toBeInTheDocument()
      })

      mockFetch.mockClear()

      const searchInput = screen.getByPlaceholderText('Search logs...')
      await user.type(searchInput, 'error')
      
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('search=error')
        )
      })
    })

    it('refresh button re-fetches logs', async () => {
      const user = userEvent.setup()
      render(<LogViewer />)
      
      await waitFor(() => {
        expect(screen.getByText('System Logs')).toBeInTheDocument()
      })

      mockFetch.mockClear()

      await user.click(screen.getByRole('button', { name: /refresh/i }))
      
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled()
      })
    })
  })

  describe('Empty State', () => {
    it('displays no logs message when logs array is empty', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(emptyLogsResponse),
      })

      render(<LogViewer />)
      
      await waitFor(() => {
        expect(screen.getByText('No logs found')).toBeInTheDocument()
      })
    })

    it('displays count as 0 when no logs', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(emptyLogsResponse),
      })

      render(<LogViewer />)
      
      await waitFor(() => {
        expect(screen.getByText(/Showing 0 of 0 logs/)).toBeInTheDocument()
      })
    })
  })

  describe('Error Handling', () => {
    it('displays error message when fetch fails', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        statusText: 'Internal Server Error',
      })

      render(<LogViewer />)
      
      await waitFor(() => {
        expect(screen.getByText(/Error:/)).toBeInTheDocument()
        expect(screen.getByText(/Failed to fetch logs: Internal Server Error/)).toBeInTheDocument()
      })
    })

    it('displays error message when network error occurs', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'))

      render(<LogViewer />)
      
      await waitFor(() => {
        expect(screen.getByText(/Error:/)).toBeInTheDocument()
        expect(screen.getByText(/Network error/)).toBeInTheDocument()
      })
    })

    it('handles unknown error type gracefully', async () => {
      mockFetch.mockRejectedValue('Unknown error')

      render(<LogViewer />)
      
      await waitFor(() => {
        expect(screen.getByText(/Error:/)).toBeInTheDocument()
        expect(screen.getByText('Unknown error')).toBeInTheDocument()
      })
    })

    it('clears error state on successful retry', async () => {
      const user = userEvent.setup()
      
      // First call fails
      mockFetch.mockResolvedValueOnce({
        ok: false,
        statusText: 'Server Error',
      })

      render(<LogViewer />)
      
      await waitFor(() => {
        expect(screen.getByText(/Error:/)).toBeInTheDocument()
      })

      // Next call succeeds
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockLogsResponse),
      })

      await user.click(screen.getByRole('button', { name: /refresh/i }))

      await waitFor(() => {
        expect(screen.queryByText(/Error:/)).not.toBeInTheDocument()
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
      
      await waitFor(() => {
        const logEntry = container.querySelector('[style*="border-left-color"]')
        expect(logEntry).toBeInTheDocument()
        expect(logEntry).toHaveStyle({ borderLeftColor: '#ef4444' }) // red for ERROR
      })
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
      
      await waitFor(() => {
        const logEntry = container.querySelector('[style*="border-left-color"]')
        expect(logEntry).toBeInTheDocument()
        expect(logEntry).toHaveStyle({ borderLeftColor: '#3b82f6' }) // blue for INFO
      })
    })
  })

  describe('Select Options', () => {
    it('source select has all required options', async () => {
      render(<LogViewer />)
      
      await waitFor(() => {
        expect(screen.getByText('System Logs')).toBeInTheDocument()
      })

      const sourceSelect = screen.getAllByRole('combobox')[0]
      const options = within(sourceSelect).getAllByRole('option')
      
      expect(options).toHaveLength(4)
      expect(options.map(o => o.textContent)).toEqual([
        'All Sources',
        'Backend',
        'Frontend',
        'Electron',
      ])
    })

    it('level select has all required options', async () => {
      render(<LogViewer />)
      
      await waitFor(() => {
        expect(screen.getByText('System Logs')).toBeInTheDocument()
      })

      const levelSelect = screen.getAllByRole('combobox')[1]
      const options = within(levelSelect).getAllByRole('option')
      
      expect(options).toHaveLength(5)
      expect(options.map(o => o.textContent)).toEqual([
        'All Levels',
        'Debug',
        'Info',
        'Warning',
        'Error',
      ])
    })
  })

  describe('has_more indicator', () => {
    it('shows "more available" when has_more is true', async () => {
      render(<LogViewer />)
      
      await waitFor(() => {
        expect(screen.getByText(/\(more available\)/)).toBeInTheDocument()
      })
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
      
      await waitFor(() => {
        expect(screen.queryByText(/\(more available\)/)).not.toBeInTheDocument()
      })
    })
  })
})
