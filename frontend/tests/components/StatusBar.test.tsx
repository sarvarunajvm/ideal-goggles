import { render, screen, waitFor, act } from '@testing-library/react'
import StatusBar from '../../src/components/StatusBar'

jest.mock('../../src/services/apiClient', () => ({
  apiService: {
    getIndexStatus: jest.fn(),
    getIndexStats: jest.fn(),
  },
}))

describe('StatusBar', () => {
  const { apiService } = require('../../src/services/apiClient')
  const getIndexStatusMock = apiService.getIndexStatus as jest.Mock
  const getIndexStatsMock = apiService.getIndexStats as jest.Mock

  beforeEach(() => {
    jest.clearAllMocks()
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  test('shows indexing status with progress', async () => {
    getIndexStatusMock.mockResolvedValue({
      status: 'indexing',
      progress: { total_files: 100, processed_files: 30, current_phase: 'thumbnails' },
      errors: [],
    })
    getIndexStatsMock.mockResolvedValue({
      database: { indexed_photos: 30 },
    })

    render(<StatusBar />)

    await waitFor(() => {
      expect(screen.getByText('Creating thumbnails')).toBeInTheDocument()
      const progressElements = screen.getAllByText('30/100')
      expect(progressElements.length).toBeGreaterThan(0)
      expect(screen.getByText('(30%)')).toBeInTheDocument()
    })
  })

  test('shows idle status with indexed count', async () => {
    getIndexStatusMock.mockResolvedValue({
      status: 'idle',
      progress: { total_files: 100, processed_files: 100, current_phase: 'completed' },
      errors: [],
    })
    getIndexStatsMock.mockResolvedValue({
      database: { indexed_photos: 150 },
    })

    render(<StatusBar />)

    await waitFor(() => {
      expect(screen.getByText('150 photos indexed')).toBeInTheDocument()
    })
  })

  test('shows error status', async () => {
    getIndexStatusMock.mockResolvedValue({
      status: 'error',
      progress: { total_files: 0, processed_files: 0, current_phase: 'error' },
      errors: ['Failed to read file', 'Database locked'],
    })
    getIndexStatsMock.mockResolvedValue({
      database: { indexed_photos: 0 },
    })

    render(<StatusBar />)

    await waitFor(() => {
      expect(screen.getByText(/2 errors/)).toBeInTheDocument()
    })
  })

  test('handles disconnected state', async () => {
    getIndexStatusMock.mockRejectedValue(new Error('Network error'))

    render(<StatusBar />)

    await waitFor(() => {
      expect(screen.getByText('Disconnected')).toBeInTheDocument()
    })
  })

  test('falls back to progress count when stats fail', async () => {
    getIndexStatusMock.mockResolvedValue({
      status: 'idle',
      progress: { total_files: 50, processed_files: 50, current_phase: 'completed' },
      errors: [],
    })
    getIndexStatsMock.mockRejectedValue(new Error('Stats failed'))

    render(<StatusBar />)

    await waitFor(() => {
      expect(screen.getByText('50 photos indexed')).toBeInTheDocument()
    })
  })

  test('polls for status updates', async () => {
    jest.useFakeTimers()
    
    getIndexStatusMock
      .mockResolvedValueOnce({
        status: 'idle',
        progress: { total_files: 0, processed_files: 0, current_phase: 'idle' },
        errors: [],
      })
      .mockResolvedValueOnce({
        status: 'indexing',
        progress: { total_files: 10, processed_files: 1, current_phase: 'scanning' },
        errors: [],
      })
    
    getIndexStatsMock.mockResolvedValue({ database: { indexed_photos: 0 } })

    render(<StatusBar />)

    // First render - idle
    await waitFor(() => {
      expect(getIndexStatusMock).toHaveBeenCalledTimes(1)
    })

    // Advance time by 5 seconds
    act(() => {
      jest.advanceTimersByTime(5000)
    })

    await waitFor(() => {
      expect(getIndexStatusMock).toHaveBeenCalledTimes(2)
      expect(screen.getByText('Scanning photos')).toBeInTheDocument()
    })
  })
})
