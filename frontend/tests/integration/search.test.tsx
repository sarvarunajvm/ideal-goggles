/**
 * Frontend integration tests with mock API
 */

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import App from '../../src/App'

// Mock API client with realistic responses
const mockApiResponses = {
  searchPhotos: {
    query: 'wedding smith 2023',
    total_matches: 3,
    items: [
      {
        file_id: 1,
        path: '/photos/2023/weddings/smith-johnson/ceremony.jpg',
        folder: '/photos/2023/weddings/smith-johnson',
        filename: 'ceremony.jpg',
        thumb_path: 'cache/thumbs/abc123.webp',
        shot_dt: '2023-06-15T14:30:00Z',
        score: 0.95,
        badges: ['OCR', 'EXIF'],
        snippet: 'Smith Johnson Wedding Ceremony'
      },
      {
        file_id: 2,
        path: '/photos/2023/weddings/smith-johnson/reception.jpg',
        folder: '/photos/2023/weddings/smith-johnson',
        filename: 'reception.jpg',
        thumb_path: 'cache/thumbs/def456.webp',
        shot_dt: '2023-06-15T18:00:00Z',
        score: 0.88,
        badges: ['OCR'],
        snippet: 'Reception venue Smith family'
      }
    ],
    took_ms: 150
  }
}

jest.mock('../../src/services/apiClient', () => ({
  searchPhotos: jest.fn().mockResolvedValue(mockApiResponses.searchPhotos),
  getConfig: jest.fn().mockResolvedValue({
    roots: ['/photos'],
    ocr_languages: ['eng', 'tam'],
    face_search_enabled: false,
    index_version: '1.0.0'
  })
}))

const renderApp = () => {
  return render(
    <BrowserRouter>
      <App />
    </BrowserRouter>
  )
}

describe('Search Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  test('complete text search workflow from quickstart scenario', async () => {
    const user = userEvent.setup()
    renderApp()

    // Will fail until components are implemented
    // This test validates quickstart.md Scenario 1

    // Given: A studio has 500,000 photos indexed
    // When: Operator searches for "wedding Smith 2023"
    const searchInput = screen.getByPlaceholderText(/search photos/i)
    await user.type(searchInput, 'wedding smith 2023')

    const searchButton = screen.getByRole('button', { name: /search/i })
    await user.click(searchButton)

    // Then: Relevant photos appear within 2 seconds with thumbnails and folder paths
    await waitFor(() => {
      expect(screen.getByText('ceremony.jpg')).toBeInTheDocument()
      expect(screen.getByText('reception.jpg')).toBeInTheDocument()
      expect(screen.getByText('/photos/2023/weddings/smith-johnson')).toBeInTheDocument()
    }, { timeout: 2000 })

    // Verify badges are displayed
    expect(screen.getByText('OCR')).toBeInTheDocument()
    expect(screen.getByText('EXIF')).toBeInTheDocument()

    // Verify search performance indicator
    expect(screen.getByText(/150ms/i)).toBeInTheDocument()
  })

  test('double-click opens photo in default viewer', async () => {
    const user = userEvent.setup()

    // Mock Electron API
    const mockElectron = {
      ipcRenderer: {
        invoke: jest.fn().mockResolvedValue(true)
      }
    }
    ;(window as any).electron = mockElectron

    renderApp()

    // Perform search first
    const searchInput = screen.getByPlaceholderText(/search photos/i)
    await user.type(searchInput, 'wedding')
    await user.click(screen.getByRole('button', { name: /search/i }))

    await waitFor(() => {
      expect(screen.getByText('ceremony.jpg')).toBeInTheDocument()
    })

    // Double-click on first result
    const firstResult = screen.getByTestId('result-item-1')
    await user.dblClick(firstResult)

    // Should call Electron API to open file
    expect(mockElectron.ipcRenderer.invoke).toHaveBeenCalledWith(
      'open-file',
      '/photos/2023/weddings/smith-johnson/ceremony.jpg'
    )
  })

  test('right-click reveals photo in file explorer', async () => {
    const user = userEvent.setup()

    // Mock Electron API
    const mockElectron = {
      ipcRenderer: {
        invoke: jest.fn().mockResolvedValue(true)
      }
    }
    ;(window as any).electron = mockElectron

    renderApp()

    // Perform search and get results
    const searchInput = screen.getByPlaceholderText(/search photos/i)
    await user.type(searchInput, 'wedding')
    await user.click(screen.getByRole('button', { name: /search/i }))

    await waitFor(() => {
      expect(screen.getByText('ceremony.jpg')).toBeInTheDocument()
    })

    // Right-click on first result
    const firstResult = screen.getByTestId('result-item-1')
    await user.rightClick(firstResult)

    // Should show context menu
    expect(screen.getByText(/reveal in folder/i)).toBeInTheDocument()

    // Click "Reveal in folder"
    await user.click(screen.getByText(/reveal in folder/i))

    // Should call Electron API
    expect(mockElectron.ipcRenderer.invoke).toHaveBeenCalledWith(
      'reveal-file',
      '/photos/2023/weddings/smith-johnson/ceremony.jpg'
    )
  })

  test('search mode toggle between text and image search', async () => {
    const user = userEvent.setup()
    renderApp()

    // Should start in text search mode
    expect(screen.getByText(/text search/i)).toHaveClass('active')

    // Switch to image search mode
    await user.click(screen.getByText(/image search/i))

    // Should show drag-drop area instead of text input
    expect(screen.getByText(/drag.*drop.*photo/i)).toBeInTheDocument()
    expect(screen.queryByPlaceholderText(/search photos/i)).not.toBeInTheDocument()
  })

  test('keyboard navigation works correctly', async () => {
    const user = userEvent.setup()
    renderApp()

    // Perform search to get results
    const searchInput = screen.getByPlaceholderText(/search photos/i)
    await user.type(searchInput, 'test')
    await user.click(screen.getByRole('button', { name: /search/i }))

    await waitFor(() => {
      expect(screen.getByText('ceremony.jpg')).toBeInTheDocument()
    })

    // Tab to results grid
    await user.tab()
    await user.tab() // Navigate to grid

    // Arrow keys should work
    await user.keyboard('{ArrowRight}')
    expect(screen.getByTestId('result-item-2')).toHaveFocus()

    // Enter should open photo
    await user.keyboard('{Enter}')
    // Should trigger open action
  })

  test('application meets constitutional privacy requirements', () => {
    renderApp()

    // Should not make any external network requests
    expect(fetch).not.toHaveBeenCalled()

    // Should show privacy-compliant configuration
    expect(screen.queryByText(/cloud/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/upload/i)).not.toBeInTheDocument()
  })
})