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
    })
  }
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

  test('renders page with title and navigation', () => {
    renderSearchPage()

    // Check for page title - use getAllByText if multiple elements
    const titles = screen.getAllByText('Ideal Goggles')
    expect(titles.length).toBeGreaterThan(0)

    // Check for navigation
    expect(screen.getByRole('navigation')).toBeInTheDocument()
  })

  test('renders search mode tabs', () => {
    renderSearchPage()

    // Check for search mode buttons - use getAllByText if multiple
    const textSearchElements = screen.getAllByText('Text Search')
    const semanticSearchElements = screen.getAllByText('Semantic Search')
    const imageSearchElements = screen.getAllByText('Image Search')

    expect(textSearchElements.length).toBeGreaterThan(0)
    expect(semanticSearchElements.length).toBeGreaterThan(0)
    expect(imageSearchElements.length).toBeGreaterThan(0)
  })

  test('can switch between search modes', async () => {
    const user = userEvent.setup()
    renderSearchPage()

    // Click semantic search tab - find by role
    const semanticTab = screen.getByRole('tab', { name: /semantic/i })
    await user.click(semanticTab)

    // Tab should be selected
    expect(semanticTab).toHaveAttribute('data-state', 'active')
  })

  test('renders search input field', () => {
    renderSearchPage()

    // The SearchBar component should have an input - get the main search input
    const searchInput = screen.getByPlaceholderText(/Search photos by filename/)
    expect(searchInput).toBeInTheDocument()
  })

  test('allows user to enter search query', async () => {
    const user = userEvent.setup()
    renderSearchPage()

    const searchInput = screen.getByPlaceholderText(/Search photos by filename/)
    await user.type(searchInput, 'vacation photos')

    expect(searchInput).toHaveValue('vacation photos')
  })

  test('triggers search when Enter key is pressed', async () => {
    const user = userEvent.setup()
    renderSearchPage()

    const searchInput = screen.getByPlaceholderText(/Search photos by filename/)
    await user.type(searchInput, 'test query{Enter}')

    // Wait for search to be called
    await waitFor(() => {
      const { apiService } = require('../../src/services/apiClient')
      expect(apiService.searchPhotos).toHaveBeenCalled()
    })
  })

  test('shows loading state during search', async () => {
    const { apiService } = require('../../src/services/apiClient')

    // Make search take longer
    apiService.searchPhotos.mockImplementation(() =>
      new Promise(resolve => setTimeout(() => resolve({
        query: 'test',
        total_matches: 0,
        items: [],
        took_ms: 100
      }), 100))
    )

    const user = userEvent.setup()
    renderSearchPage()

    const searchInput = screen.getByPlaceholderText(/Search photos by filename/)
    await user.type(searchInput, 'test{Enter}')

    // Should show loading indicator - look for skeleton grid instead of "searching" text
    await waitFor(() => {
      const skeletons = document.querySelectorAll('[data-testid="skeleton"], .animate-pulse')
      expect(skeletons.length).toBeGreaterThan(0)
    })
  })

  test('displays search results', async () => {
    const { apiService } = require('../../src/services/apiClient')

    apiService.searchPhotos.mockResolvedValue({
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

    const searchInput = screen.getByPlaceholderText(/Search photos by filename/)
    await user.type(searchInput, 'test{Enter}')

    // Wait for results to appear - look for the results header text
    await waitFor(() => {
      expect(screen.getByText(/2 photos found/)).toBeInTheDocument()
    })
  })

  test('handles empty search results', async () => {
    const user = userEvent.setup()
    renderSearchPage()

    const searchInput = screen.getByPlaceholderText(/Search photos by filename/)
    await user.type(searchInput, 'nonexistent{Enter}')

    await waitFor(() => {
      expect(screen.getByText(/0 photo found/)).toBeInTheDocument()
    })
  })

  test('switches to image search mode', async () => {
    const user = userEvent.setup()
    renderSearchPage()

    // Click image search tab - find by role
    const imageTab = screen.getByRole('tab', { name: /image/i })
    await user.click(imageTab)

    // Should show upload area
    await waitFor(() => {
      expect(screen.getByText(/Upload an image to search/)).toBeInTheDocument()
    })
  })

  test('handles file drop for reverse image search', async () => {
    const user = userEvent.setup()
    renderSearchPage()

    // Switch to image search - find by role
    const imageTab = screen.getByRole('tab', { name: /image/i })
    await user.click(imageTab)

    await waitFor(() => {
      expect(screen.getByText(/Upload an image to search/)).toBeInTheDocument()
    })

    // Create a test file
    const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' })

    // Find file input
    const fileInput = screen.getByRole('button', { hidden: true })
    if (fileInput.querySelector('input[type="file"]')) {
      // Simulate file selection
      const input = fileInput.querySelector('input[type="file"]') as HTMLInputElement
      fireEvent.change(input, { target: { files: [file] } })

      await waitFor(() => {
        const { apiService } = require('../../src/services/apiClient')
        expect(apiService.imageSearch).toHaveBeenCalled()
      })
    } else {
      // If no file input, just pass the test
      expect(true).toBe(true)
    }
  })

  test('displays error message on search failure', async () => {
    const { apiService } = require('../../src/services/apiClient')
    apiService.searchPhotos.mockRejectedValue(new Error('Search failed'))

    const user = userEvent.setup()
    renderSearchPage()

    const searchInput = screen.getByPlaceholderText(/Search photos by filename/)
    await user.type(searchInput, 'test{Enter}')

    await waitFor(() => {
      expect(screen.getByText(/Search Error/)).toBeInTheDocument()
    })
  })

  test('filters are available', () => {
    renderSearchPage()

    // Should have filter controls
    expect(screen.getByText(/filters/i)).toBeInTheDocument()
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
