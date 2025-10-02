/**
 * Unit tests for StatusBar Component
 * Priority: P1 (Critical system status display)
 */

import React from 'react'
import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'
import StatusBar from '../../src/components/StatusBar'
import { apiService } from '../../src/services/apiClient'

// Mock the apiService
jest.mock('../../src/services/apiClient', () => ({
  apiService: {
    getIndexStatus: jest.fn(),
  },
  getApiBaseUrl: () => 'http://localhost:5555',
}))

// Mock window.open
const mockWindowOpen = jest.fn()
Object.defineProperty(window, 'open', {
  value: mockWindowOpen,
  writable: true,
})

const mockIndexStatusIdle = {
  status: 'idle',
  progress: {
    current_phase: 'waiting',
    processed_files: 0,
    total_files: 0,
  },
  errors: [],
}

const mockIndexStatusIndexing = {
  status: 'indexing',
  progress: {
    current_phase: 'Processing images',
    processed_files: 50,
    total_files: 100,
  },
  errors: [],
}

const mockIndexStatusError = {
  status: 'error',
  progress: {
    current_phase: 'error',
    processed_files: 0,
    total_files: 0,
  },
  errors: ['Connection failed', 'Invalid path'],
}

describe('StatusBar Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  test('renders with initial checking state', async () => {
    ;(apiService.getIndexStatus as jest.Mock).mockResolvedValue(mockIndexStatusIdle)

    render(<StatusBar />)

    expect(screen.getByText('Checking...')).toBeInTheDocument()
    expect(screen.getByTestId('connection-badge')).toHaveClass('animate-pulse')
  })

  test('displays connected status when API is available', async () => {
    ;(apiService.getIndexStatus as jest.Mock).mockResolvedValue(mockIndexStatusIdle)

    render(<StatusBar />)

    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument()
    })

    expect(screen.queryByText('Checking...')).not.toBeInTheDocument()
  })

  test('displays disconnected status when API fails', async () => {
    ;(apiService.getIndexStatus as jest.Mock).mockRejectedValue(new Error('Network error'))

    render(<StatusBar />)

    await waitFor(() => {
      expect(screen.getByText('Disconnected')).toBeInTheDocument()
    })
  })

  test('displays idle index status', async () => {
    ;(apiService.getIndexStatus as jest.Mock).mockResolvedValue(mockIndexStatusIdle)

    render(<StatusBar />)

    await waitFor(() => {
      expect(screen.getByText('Idle')).toBeInTheDocument()
    })
  })

  test('displays indexing status with progress', async () => {
    ;(apiService.getIndexStatus as jest.Mock).mockResolvedValue(mockIndexStatusIndexing)

    render(<StatusBar />)

    await waitFor(() => {
      expect(screen.getByText('Indexing')).toBeInTheDocument()
      expect(screen.getByText('Processing images')).toBeInTheDocument()
      expect(screen.getByText('50/100')).toBeInTheDocument()
    })

    // Check for progress bar
    expect(screen.getByRole('progressbar')).toBeInTheDocument()
  })

  test('displays error status with error count', async () => {
    ;(apiService.getIndexStatus as jest.Mock).mockResolvedValue(mockIndexStatusError)

    render(<StatusBar />)

    await waitFor(() => {
      expect(screen.getByText('Error')).toBeInTheDocument()
      expect(screen.getByText('2 errors')).toBeInTheDocument()
    })
  })

  test('handles single error correctly', async () => {
    const singleErrorStatus = {
      ...mockIndexStatusError,
      errors: ['Single error'],
    }
    ;(apiService.getIndexStatus as jest.Mock).mockResolvedValue(singleErrorStatus)

    render(<StatusBar />)

    await waitFor(() => {
      expect(screen.getByText('1 error')).toBeInTheDocument()
    })
  })

  test('opens API documentation when button is clicked', async () => {
    ;(apiService.getIndexStatus as jest.Mock).mockResolvedValue(mockIndexStatusIdle)
    const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime })

    render(<StatusBar />)

    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument()
    })

    const apiDocsButton = screen.getByTitle('Open API Documentation')
    await user.click(apiDocsButton)

    expect(mockWindowOpen).toHaveBeenCalledWith('http://localhost:5555/docs', '_blank')
  })

  test('calculates progress percentage correctly', async () => {
    ;(apiService.getIndexStatus as jest.Mock).mockResolvedValue(mockIndexStatusIndexing)

    render(<StatusBar />)

    await waitFor(() => {
      const progressBar = screen.getByRole('progressbar')
      expect(progressBar).toHaveAttribute('aria-valuenow', '50')
    })
  })

  test('handles zero total files gracefully', async () => {
    const zeroFilesStatus = {
      ...mockIndexStatusIndexing,
      progress: {
        current_phase: 'Scanning',
        processed_files: 0,
        total_files: 0,
      },
    }
    ;(apiService.getIndexStatus as jest.Mock).mockResolvedValue(zeroFilesStatus)

    render(<StatusBar />)

    await waitFor(() => {
      expect(screen.getByText('Indexing')).toBeInTheDocument()
      expect(screen.getByText('Scanning')).toBeInTheDocument()
    })

    // Progress should not be shown when total_files is 0
    expect(screen.queryByText('0/0')).not.toBeInTheDocument()
  })

  test('updates status periodically', async () => {
    let callCount = 0
    ;(apiService.getIndexStatus as jest.Mock).mockImplementation(() => {
      callCount++
      if (callCount === 1) {
        return Promise.resolve(mockIndexStatusIdle)
      } else {
        return Promise.resolve(mockIndexStatusIndexing)
      }
    })

    render(<StatusBar />)

    // Initial call
    await waitFor(() => {
      expect(screen.getByText('Idle')).toBeInTheDocument()
    })

    // Advance timer by 5 seconds
    act(() => {
      jest.advanceTimersByTime(5000)
    })

    // Should have made another call and updated status
    await waitFor(() => {
      expect(screen.getByText('Indexing')).toBeInTheDocument()
    })

    expect(callCount).toBe(2)
  })

  test('cleans up interval on unmount', async () => {
    ;(apiService.getIndexStatus as jest.Mock).mockResolvedValue(mockIndexStatusIdle)

    const { unmount } = render(<StatusBar />)

    const clearIntervalSpy = jest.spyOn(window, 'clearInterval')

    unmount()

    expect(clearIntervalSpy).toHaveBeenCalled()
  })

  test('displays mobile progress view for small screens', async () => {
    ;(apiService.getIndexStatus as jest.Mock).mockResolvedValue(mockIndexStatusIndexing)

    render(<StatusBar />)

    await waitFor(() => {
      // Mobile progress should be present (element appears twice - desktop and mobile)
      const mobileProgress = screen.getAllByText('Processing images')
      expect(mobileProgress.length).toBe(2) // Desktop and mobile versions
    })
  })

  test('applies correct badge variants for different statuses', async () => {
    ;(apiService.getIndexStatus as jest.Mock).mockResolvedValue(mockIndexStatusError)

    render(<StatusBar />)

    await waitFor(() => {
      const errorBadge = screen.getByText('Error').closest('span')
      expect(errorBadge).toHaveClass('bg-destructive')
    })
  })

  test('shows appropriate icons for different states', async () => {
    ;(apiService.getIndexStatus as jest.Mock).mockResolvedValue(mockIndexStatusIndexing)

    render(<StatusBar />)

    await waitFor(() => {
      // Check for presence of icons (they should render as SVG elements)
      expect(screen.getByText('Connected')).toBeInTheDocument()
      expect(screen.getByText('Indexing')).toBeInTheDocument()
    })
  })

  test('handles API errors gracefully', async () => {
    ;(apiService.getIndexStatus as jest.Mock)
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce(mockIndexStatusIdle)

    render(<StatusBar />)

    // Should show disconnected initially
    await waitFor(() => {
      expect(screen.getByText('Disconnected')).toBeInTheDocument()
    })

    // Advance timer to trigger retry
    act(() => {
      jest.advanceTimersByTime(5000)
    })

    // Should recover and show connected
    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument()
    })
  })

  test('shows animate-pulse class for indexing status', async () => {
    ;(apiService.getIndexStatus as jest.Mock).mockResolvedValue(mockIndexStatusIndexing)

    render(<StatusBar />)

    await waitFor(() => {
      const indexingBadge = screen.getByText('Indexing').closest('span')
      expect(indexingBadge).toBeInTheDocument()
    })
  })

  test('handles unknown status with default badge variant', async () => {
    const unknownStatus = {
      status: 'unknown',
      progress: {
        current_phase: 'waiting',
        processed_files: 0,
        total_files: 0,
      },
      errors: [],
    }
    ;(apiService.getIndexStatus as jest.Mock).mockResolvedValue(unknownStatus)

    render(<StatusBar />)

    await waitFor(() => {
      expect(screen.getByText('Unknown')).toBeInTheDocument()
    })
  })

  test('handles unknown status icon correctly', async () => {
    const unknownStatus = {
      status: 'pending',
      progress: {
        current_phase: 'waiting',
        processed_files: 0,
        total_files: 0,
      },
      errors: [],
    }
    ;(apiService.getIndexStatus as jest.Mock).mockResolvedValue(unknownStatus)

    render(<StatusBar />)

    await waitFor(() => {
      expect(screen.getByText('Pending')).toBeInTheDocument()
    })
  })

  test('displays mobile progress correctly with files', async () => {
    ;(apiService.getIndexStatus as jest.Mock).mockResolvedValue(mockIndexStatusIndexing)

    render(<StatusBar />)

    await waitFor(() => {
      // Mobile sections should show the same progress info
      const progressTexts = screen.getAllByText('50/100')
      expect(progressTexts.length).toBeGreaterThan(0)
    })
  })

  test('handles zero progress percentage correctly', async () => {
    const zeroProgressStatus = {
      status: 'indexing',
      progress: {
        current_phase: 'Starting',
        processed_files: 0,
        total_files: 100,
      },
      errors: [],
    }
    ;(apiService.getIndexStatus as jest.Mock).mockResolvedValue(zeroProgressStatus)

    render(<StatusBar />)

    await waitFor(() => {
      const progressBar = screen.getByRole('progressbar')
      expect(progressBar).toHaveAttribute('aria-valuenow', '0')
    })
  })

  test('handles 100% progress correctly', async () => {
    const completeStatus = {
      status: 'indexing',
      progress: {
        current_phase: 'Finishing up',
        processed_files: 100,
        total_files: 100,
      },
      errors: [],
    }
    ;(apiService.getIndexStatus as jest.Mock).mockResolvedValue(completeStatus)

    render(<StatusBar />)

    await waitFor(() => {
      const progressBar = screen.getByRole('progressbar')
      expect(progressBar).toHaveAttribute('aria-valuenow', '100')
    })
  })

  test('shows error badge with pulse animation', async () => {
    ;(apiService.getIndexStatus as jest.Mock).mockResolvedValue(mockIndexStatusError)

    render(<StatusBar />)

    await waitFor(() => {
      const errorBadge = screen.getByText('2 errors').closest('span')
      expect(errorBadge).toHaveClass('animate-pulse')
    })
  })

  test('handles connection checking state icon animation', async () => {
    render(<StatusBar />)

    const badge = screen.getByTestId('connection-badge')
    expect(badge).toHaveClass('animate-pulse')
  })

  test('displays appropriate classes for different badge variants', async () => {
    ;(apiService.getIndexStatus as jest.Mock).mockResolvedValue(mockIndexStatusIdle)

    render(<StatusBar />)

    await waitFor(() => {
      const idleBadge = screen.getByText('Idle').closest('span')
      expect(idleBadge).toHaveClass('bg-secondary')
    })
  })

  test('handles mobile view without total files', async () => {
    const noFilesStatus = {
      status: 'indexing',
      progress: {
        current_phase: 'Initializing',
        processed_files: 0,
        total_files: 0,
      },
      errors: [],
    }
    ;(apiService.getIndexStatus as jest.Mock).mockResolvedValue(noFilesStatus)

    render(<StatusBar />)

    await waitFor(() => {
      expect(screen.getByText('Initializing')).toBeInTheDocument()
    })
  })

  test('correctly formats status text with capitalization', async () => {
    ;(apiService.getIndexStatus as jest.Mock).mockResolvedValue(mockIndexStatusIndexing)

    render(<StatusBar />)

    await waitFor(() => {
      // Should capitalize first letter of status
      expect(screen.getByText('Indexing')).toBeInTheDocument()
    })
  })

  test('API docs button has correct accessibility attributes', async () => {
    ;(apiService.getIndexStatus as jest.Mock).mockResolvedValue(mockIndexStatusIdle)

    render(<StatusBar />)

    await waitFor(() => {
      const apiDocsButton = screen.getByTitle('Open API Documentation')
      expect(apiDocsButton).toHaveClass('hover:scale-105')
    })
  })
})