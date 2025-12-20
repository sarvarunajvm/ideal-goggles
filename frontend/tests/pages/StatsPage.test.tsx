import { render, screen, waitFor, act } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import StatsPage from '../../src/pages/StatsPage'

// Use fake timers only within specific tests to avoid leaks

// Mock apiService
jest.mock('../../src/services/apiClient', () => ({
  apiService: {
    getConfig: jest.fn(),
    getIndexStats: jest.fn(),
  },
}))

describe('StatsPage', () => {
  const { apiService } = require('../../src/services/apiClient')

  const makeStats = (overrides: Partial<any> = {}) => ({
    database: {
      total_photos: 100,
      indexed_photos: 60,
      photos_with_embeddings: 55,
      total_faces: 120,
    },
    ...overrides,
  })

  beforeEach(() => {
    jest.clearAllMocks()
  })

  const renderPage = () =>
    render(
      <MemoryRouter>
        <StatsPage />
      </MemoryRouter>
    )

  test('shows loading then renders stats view with computed percentages', async () => {
    jest.mocked(apiService.getConfig).mockResolvedValue({ roots: ['/photos'] })
    jest.mocked(apiService.getIndexStats).mockResolvedValue(makeStats())

    renderPage()

    // Loading UI visible first
    expect(screen.getByText('Loading statistics...')).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText('Library Statistics')).toBeInTheDocument()
    })

    // Key headline cards present
    expect(screen.getByText('Total Photos')).toBeInTheDocument()
    expect(screen.getByText('Indexed')).toBeInTheDocument()
    expect(screen.getByText('Searchable')).toBeInTheDocument()
    expect(screen.getByText('Faces Detected')).toBeInTheDocument()

    // Percentage texts based on 60/100 and 55/100
    expect(screen.getByText('60.0% complete')).toBeInTheDocument()
    expect(screen.getByText('55.0% searchable')).toBeInTheDocument()

    // Health badge shows Fair for 55%
    expect(screen.getByText('55%')).toBeInTheDocument()
    expect(screen.getByText(/Fair|Good|Poor/)).toBeInTheDocument()
  })

  test('shows stale data warning when no folders configured but stats exist', async () => {
    jest.mocked(apiService.getConfig).mockResolvedValue({ roots: [] })
    jest.mocked(apiService.getIndexStats).mockResolvedValue(makeStats())

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('No Photo Folders Configured')).toBeInTheDocument()
    })

    expect(screen.getByText(/Previous session data/)).toBeInTheDocument()
  })

  test('shows no statistics available when stats are null after loading', async () => {
    jest.mocked(apiService.getConfig).mockResolvedValue({ roots: ['/photos'] })
    jest.mocked(apiService.getIndexStats).mockResolvedValue(null as any)

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('No statistics available')).toBeInTheDocument()
    })
  })

  test('shows error state with reload button', async () => {
    jest.mocked(apiService.getConfig).mockResolvedValue({ roots: ['/photos'] })
    jest.mocked(apiService.getIndexStats).mockRejectedValue(new Error('boom'))


    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Failed to load statistics')).toBeInTheDocument()
      expect(screen.getByText('boom')).toBeInTheDocument()
    })

    // Try again button is visible
    expect(screen.getByText('Try again')).toBeInTheDocument()
  })

  test('sets interval to refresh stats and clears it on unmount', async () => {
    jest.useFakeTimers()
    jest.mocked(apiService.getConfig).mockResolvedValue({ roots: ['/photos'] })
    jest.mocked(apiService.getIndexStats).mockResolvedValue(makeStats())

    const { unmount } = renderPage()

    // Fast-forward timers to trigger one interval tick
    await act(async () => {
      jest.advanceTimersByTime(30000)
    })

    expect(apiService.getIndexStats).toHaveBeenCalledTimes(2)

    // Unmount and ensure no further calls after time advance
    unmount()
    await act(async () => {
      jest.advanceTimersByTime(60000)
    })
    expect(apiService.getIndexStats).toHaveBeenCalledTimes(2)
    jest.useRealTimers()
  })
})
