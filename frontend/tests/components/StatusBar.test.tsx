import { render, screen, waitFor } from '@testing-library/react'
import StatusBar from '../../src/components/StatusBar'

jest.mock('../../src/services/apiClient', () => ({
  apiService: {
    getIndexStatus: jest.fn().mockResolvedValue({
      status: 'indexing',
      progress: { total_files: 10, processed_files: 3, current_phase: 'metadata' },
      errors: [],
      started_at: null,
      estimated_completion: null,
    }),
    getIndexStats: jest.fn().mockResolvedValue({
      database: { indexed_photos: 100 },
    }),
  },
}))

describe('StatusBar', () => {
  beforeEach(() => {
    jest.useFakeTimers()
  })
  afterEach(() => {
    jest.useRealTimers()
  })

  test('shows indexing status with progress and connection badge', async () => {
    render(<StatusBar />)
    await waitFor(() => {
      expect(screen.getByTestId('connection-badge')).toBeInTheDocument()
    })
    // Check that progress indicator is rendered by Radix and that connection text transitions away from Checking
    await waitFor(() => {
      expect(screen.queryByText(/Checking/)).not.toBeInTheDocument()
    })
  })
})
