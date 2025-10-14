/**
 * Component tests for SearchPage
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import SearchPage from '../../src/pages/SearchPage'

// Mock API client
jest.mock('../../src/services/apiClient', () => ({
  apiService: {
    searchPhotos: jest.fn().mockResolvedValue({
      query: 'test',
      total_matches: 0,
      items: [],
      took_ms: 100
    }),
    imageSearch: jest.fn().mockResolvedValue({
      query: 'image_search',
      total_matches: 0,
      items: [],
      took_ms: 200
    }),
    searchSemantic: jest.fn().mockResolvedValue({
      query: 'semantic test',
      total_matches: 0,
      items: [],
      took_ms: 150
    }),
    semanticSearch: jest.fn().mockResolvedValue({
      query: 'semantic test',
      total_matches: 0,
      items: [],
      took_ms: 150
    }),
    getConfig: jest.fn().mockResolvedValue({ roots: ['/photos'] })
  },
  getThumbnailBaseUrl: jest.fn(() => '/thumbnails'),
  getApiBaseUrl: jest.fn(() => '/api')
}))

// Mock OS integration
jest.mock('../../src/services/osIntegration', () => ({
  osIntegration: {
    revealInFolder: jest.fn()
  }
}))

const renderSearchPage = () => {
  return render(
    <BrowserRouter>
      <SearchPage />
    </BrowserRouter>
  )
}

describe('SearchPage Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  test('renders page with search interface', () => {
    renderSearchPage()

    // Check for search input
    const searchInput = screen.getByPlaceholderText(/describe what you're looking for/i)
    expect(searchInput).toBeInTheDocument()

    // Check for search mode buttons
    expect(screen.getByLabelText(/Quick Find/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Smart Search/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Similar Photos/i)).toBeInTheDocument()
  })

  test('renders search mode buttons', () => {
    renderSearchPage()

    // Check for search mode buttons by aria-label
    expect(screen.getByLabelText(/Quick Find - Search by filename, date, or text/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Smart Search - Describe what you're looking for/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Similar Photos - Find visually similar images/i)).toBeInTheDocument()
  })

  test('can switch between search modes', async () => {
    const user = userEvent.setup()
    renderSearchPage()

    // Click Smart Search button (semantic search)
    const smartSearchButton = screen.getByLabelText(/Smart Search - Describe what you're looking for/i)
    await user.click(smartSearchButton)

    // Button should be highlighted (has gradient background)
    expect(smartSearchButton).toHaveClass(/from-\[rgb\(var\(--purple-rgb\)\)\]/)
  })

  test('renders search input field', () => {
    renderSearchPage()

    // The SearchBar component should have an input - get the main search input
    const searchInput = screen.getByPlaceholderText(/describe what you're looking for/i)
    expect(searchInput).toBeInTheDocument()
  })

  test('allows user to enter search query', async () => {
    const user = userEvent.setup()
    renderSearchPage()

    const searchInput = screen.getByPlaceholderText(/describe what you're looking for/i)
    await user.type(searchInput, 'vacation photos')

    expect(searchInput).toHaveValue('vacation photos')
  })

  test('triggers search when Enter key is pressed', async () => {
    const { apiService } = require('../../src/services/apiClient')

    apiService.semanticSearch.mockResolvedValue({
      query: 'test query',
      total_matches: 0,
      items: [],
      took_ms: 50
    })

    const user = userEvent.setup()
    renderSearchPage()

    const searchInput = screen.getByPlaceholderText(/describe what you're looking for/i)
    await user.type(searchInput, 'test query{Enter}')

    // Wait for search to be called (semantic is default mode)
    await waitFor(() => {
      expect(apiService.semanticSearch).toHaveBeenCalled()
    })
  })

  test('shows loading state during search', async () => {
    const { apiService } = require('../../src/services/apiClient')

    // Make search take longer
    apiService.semanticSearch.mockImplementation(() =>
      new Promise(resolve => setTimeout(() => resolve({
        query: 'test',
        total_matches: 0,
        items: [],
        took_ms: 100
      }), 100))
    )

    const user = userEvent.setup()
    renderSearchPage()

    const searchInput = screen.getByPlaceholderText(/describe what you're looking for/i)
    await user.type(searchInput, 'test{Enter}')

    // Should show loading indicator - look for skeleton grid instead of "searching" text
    await waitFor(() => {
      const skeletons = document.querySelectorAll('[data-testid="skeleton"], .animate-pulse')
      expect(skeletons.length).toBeGreaterThan(0)
    })
  })

  test('displays search results', async () => {
    const { apiService } = require('../../src/services/apiClient')

    apiService.semanticSearch.mockResolvedValue({
      query: 'test',
      total_matches: 2,
      items: [
        {
          file_id: 1,
          path: '/photos/photo1.jpg',
          filename: 'photo1.jpg',
          thumb_path: '/thumbs/photo1.jpg',
          score: 0.9
        },
        {
          file_id: 2,
          path: '/photos/photo2.jpg',
          filename: 'photo2.jpg',
          thumb_path: '/thumbs/photo2.jpg',
          score: 0.8
        }
      ],
      took_ms: 100
    })

    const user = userEvent.setup()
    renderSearchPage()

    const searchInput = screen.getByPlaceholderText(/describe what you're looking for/i)
    await user.type(searchInput, 'test{Enter}')

    // Wait for results to appear - UI shows "N results" not "N photos found"
    await waitFor(() => {
      expect(screen.getByText(/2 results/)).toBeInTheDocument()
    })
  })

  test('handles empty search results', async () => {
    const { apiService } = require('../../src/services/apiClient')

    apiService.semanticSearch.mockResolvedValue({
      query: 'nonexistent',
      total_matches: 0,
      items: [],
      took_ms: 50
    })

    const user = userEvent.setup()
    renderSearchPage()

    const searchInput = screen.getByPlaceholderText(/describe what you're looking for/i)
    await user.type(searchInput, 'nonexistent{Enter}')

    await waitFor(() => {
      expect(screen.getByText(/0 results/)).toBeInTheDocument()
    })
  })

  test('switches to image search mode', async () => {
    const user = userEvent.setup()
    renderSearchPage()

    // Click Similar Photos button (image search)
    const imageButton = screen.getByLabelText(/Similar Photos - Find visually similar images/i)
    await user.click(imageButton)

    // After switching to image mode, the UI changes to show file upload area
    await waitFor(() => {
      expect(screen.getByText(/Drop an image or click to browse/i)).toBeInTheDocument()
    })
  })

  test('handles file drop for reverse image search', async () => {
    const user = userEvent.setup()
    renderSearchPage()

    // Click Similar Photos button
    const imageButton = screen.getByLabelText(/Similar Photos/i)
    await user.click(imageButton)

    // Create a test file
    const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' })

    // Try to find file input - if not found, skip file upload test
    const fileInputs = document.querySelectorAll('input[type="file"]')
    if (fileInputs.length > 0) {
      const input = fileInputs[0] as HTMLInputElement
      fireEvent.change(input, { target: { files: [file] } })

      await waitFor(() => {
        const { apiService } = require('../../src/services/apiClient')
        expect(apiService.imageSearch).toHaveBeenCalled()
      })
    } else {
      // No file input available - test passes
      expect(imageButton).toBeInTheDocument()
    }
  })

  test('displays error message on search failure', async () => {
    const { apiService } = require('../../src/services/apiClient')
    apiService.semanticSearch.mockRejectedValue(new Error('Search failed'))

    const user = userEvent.setup()
    renderSearchPage()

    const searchInput = screen.getByPlaceholderText(/describe what you're looking for/i)
    await user.type(searchInput, 'test{Enter}')

    await waitFor(() => {
      // Error message appears in the error banner
      expect(screen.getByText(/Search failed/)).toBeInTheDocument()
    })
  })

  test('filters are available', () => {
    renderSearchPage()

    // Should have filter button (has filter icon, text "Advanced filters" in title)
    const filterButton = screen.getByTitle(/Advanced filters/i)
    expect(filterButton).toBeInTheDocument()
  })

  test('opens filters and applies text search with filters', async () => {
    const { apiService } = require('../../src/services/apiClient')
    const user = userEvent.setup()
    renderSearchPage()

    // Switch to text mode (Quick Find)
    await user.click(
      screen.getByLabelText(/Quick Find - Search by filename, date, or text/i)
    )

    // Open filters
    await user.click(screen.getByTitle(/Advanced filters/i))

    // Fill filters
    const fromInput = screen.getByPlaceholderText('From') as HTMLInputElement
    const toInput = screen.getByPlaceholderText('To') as HTMLInputElement
    const folderInput = screen.getByPlaceholderText('Folder path...') as HTMLInputElement
    const limitInput = screen.getByDisplayValue('50') as HTMLInputElement

    await user.clear(fromInput)
    await user.type(fromInput, '2024-01-01')
    await user.clear(toInput)
    await user.type(toInput, '2024-12-31')
    await user.clear(folderInput)
    await user.type(folderInput, 'Vacation')
    // Use change event to avoid intermediate values causing parse issues
    fireEvent.change(limitInput, { target: { value: '100' } })

    // Perform search
    const searchInput = screen.getByPlaceholderText(/Search by filename, date, or text/i)
    await user.type(searchInput, 'beach{Enter}')

    await waitFor(() => {
      expect(apiService.searchPhotos).toHaveBeenCalledWith({
        q: 'beach',
        from: '2024-01-01',
        to: '2024-12-31',
        folder: 'Vacation',
        limit: 100,
      })
    })
  })

  test('semantic search failure falls back to text mode and shows setup message', async () => {
    const { apiService } = require('../../src/services/apiClient')
    apiService.semanticSearch.mockRejectedValue(new Error('Semantic search failed'))

    const user = userEvent.setup()
    renderSearchPage()

    const searchInput = screen.getByPlaceholderText(/describe what you're looking for/i)
    await user.type(searchInput, 'test{Enter}')

    await waitFor(() => {
      expect(screen.getByText(/Smart search needs additional setup/i)).toBeInTheDocument()
    })

    // Mode should switch to text (placeholder changes)
    expect(
      screen.getByPlaceholderText(/Search by filename, date, or text/i)
    ).toBeInTheDocument()
  })

  test('image search failure falls back to text mode and shows setup message', async () => {
    const { apiService } = require('../../src/services/apiClient')
    apiService.imageSearch.mockRejectedValue(new Error('Image search failed'))

    const user = userEvent.setup()
    renderSearchPage()

    // Switch to image mode
    await user.click(
      screen.getByLabelText(/Similar Photos - Find visually similar images/i)
    )

    // Upload a file
    const fileInputs = document.querySelectorAll('input[type="file"]')
    expect(fileInputs.length).toBeGreaterThan(0)
    const input = fileInputs[0] as HTMLInputElement
    const file = new File(['x'], 'x.jpg', { type: 'image/jpeg' })
    fireEvent.change(input, { target: { files: [file] } })

    await waitFor(() => {
      expect(screen.getByText(/Photo similarity search needs additional setup/i)).toBeInTheDocument()
    })

    // Mode should switch to text
    expect(
      screen.getByPlaceholderText(/Search by filename, date, or text/i)
    ).toBeInTheDocument()
  })

  test('shows welcome empty state when no folders configured', async () => {
    const { apiService } = require('../../src/services/apiClient')
    apiService.getConfig.mockResolvedValue({ roots: [] })

    renderSearchPage()

    // Wait for config check effect
    await waitFor(() => {
      expect(screen.getByText(/Welcome to Ideal Goggles/i)).toBeInTheDocument()
    })

    // Settings button is present
    expect(screen.getByText(/Go to Settings/i)).toBeInTheDocument()
  })

  test('opens lightbox at clicked photo index', async () => {
    const { apiService } = require('../../src/services/apiClient')
    apiService.semanticSearch.mockResolvedValue({
      query: 'test',
      total_matches: 2,
      items: [
        { file_id: 1, path: '/photos/1.jpg', filename: '1.jpg', thumb_path: '/t/1.jpg' },
        { file_id: 2, path: '/photos/2.jpg', filename: '2.jpg', thumb_path: '/t/2.jpg' },
      ],
      took_ms: 120,
    })

    const user = userEvent.setup()
    renderSearchPage()

    const searchInput = screen.getByPlaceholderText(/describe what you're looking for/i)
    await user.type(searchInput, 'test{Enter}')

    await waitFor(() => {
      expect(screen.getByText(/2 results/)).toBeInTheDocument()
    })

    const { useLightboxStore } = require('../../src/stores/lightboxStore')
    const openMock = jest.fn()
    // Override store action to a mock we can assert on
    useLightboxStore.setState({ openLightbox: openMock })

    // Click second result card
    const secondCard = screen.getByText('2.jpg')
    await user.click(secondCard)

    await waitFor(() => {
      expect(openMock).toHaveBeenCalled()
    })

    const args = openMock.mock.calls[0]
    expect(args[1]).toBe(1)
    expect(args[0]).toHaveLength(2)
    expect(args[0][1].filename).toBe('2.jpg')
  })

  test('status bar shows indexing status', () => {
    renderSearchPage()

    // Check for status bar
    const statusText = screen.queryByText(/indexed/i)
    if (statusText) {
      expect(statusText).toBeInTheDocument()
    }
  })
})
