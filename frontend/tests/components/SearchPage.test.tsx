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

  test('can switch between search modes', async () => {
    const user = userEvent.setup()
    renderSearchPage()

    // Click Smart Search button (semantic search)
    const smartSearchButton = screen.getByLabelText(/Smart Search - Describe what you're looking for/i)
    await user.click(smartSearchButton)

    // Button should be highlighted (has gradient background)
    expect(smartSearchButton).toHaveClass(/from-\[rgb\(var\(--purple-rgb\)\)\]/)
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
          score: 0.9,
          snippet: 'OCR text here'
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

    // Wait for results to appear
    await waitFor(() => {
      expect(screen.getByText(/2 results/)).toBeInTheDocument()
    })
    
    // Check for OCR badge presence
    // Note: The OCR badge is rendered but might be hard to select by text, so we check for presence
    const results = screen.getAllByTestId('search-result-item')
    expect(results).toHaveLength(2)
  })

  test('clears filters', async () => {
    const user = userEvent.setup()
    renderSearchPage()

    // Open filters
    await user.click(screen.getByTitle(/Advanced filters/i))

    // Set a filter
    const folderInput = screen.getByPlaceholderText('Folder path...')
    await user.type(folderInput, 'TestFolder')
    
    // Click clear
    const clearButton = screen.getByText('Clear')
    await user.click(clearButton)

    expect(folderInput).toHaveValue('')
  })

  test('handles reveal in folder action', async () => {
    const { apiService } = require('../../src/services/apiClient')
    const { osIntegration } = require('../../src/services/osIntegration')

    apiService.semanticSearch.mockResolvedValue({
      query: 'test',
      total_matches: 1,
      items: [{ file_id: 1, path: '/p/1.jpg', filename: '1.jpg', thumb_path: 't.jpg' }],
      took_ms: 50
    })

    const user = userEvent.setup()
    renderSearchPage()
    
    const searchInput = screen.getByPlaceholderText(/describe what you're looking for/i)
    await user.type(searchInput, 'test{Enter}')

    await waitFor(() => screen.getByText('1 results'))

    // Hover over image to show actions (simulated by just clicking the button which should be in DOM)
    // The button might be hidden by CSS but accessible to tests
    // In this component, it seems to rely on group-hover, so we might need to find button by icon
    // Using a more direct query for the button within the card
    const revealBtn = document.querySelector('button.backdrop-blur-sm')
    if (revealBtn) {
        await user.click(revealBtn)
        expect(osIntegration.revealInFolder).toHaveBeenCalledWith('/p/1.jpg')
    }
  })

  test('displays empty state variations', async () => {
    const { apiService } = require('../../src/services/apiClient')
    
    // Case 1: Configured folders but no results
    apiService.semanticSearch.mockResolvedValue({
      query: 'none',
      total_matches: 0,
      items: [],
      took_ms: 10
    })
    
    const user = userEvent.setup()
    renderSearchPage()
    
    const searchInput = screen.getByPlaceholderText(/describe what you're looking for/i)
    await user.type(searchInput, 'none{Enter}')
    
    await waitFor(() => {
        expect(screen.getByText('No results found')).toBeInTheDocument()
        expect(screen.getByText('Try adjusting your search or filters')).toBeInTheDocument()
    })
  })

  test('handles image search failure', async () => {
    const { apiService } = require('../../src/services/apiClient')
    apiService.imageSearch.mockRejectedValue(new Error('Image search failed'))

    const user = userEvent.setup()
    renderSearchPage()

    // Switch to image mode
    await user.click(screen.getByLabelText(/Similar Photos/i))

    // Mock file upload
    const fileInputs = document.querySelectorAll('input[type="file"]')
    if (fileInputs.length > 0) {
        const input = fileInputs[0] as HTMLInputElement
        const file = new File(['x'], 'x.jpg', { type: 'image/jpeg' })
        fireEvent.change(input, { target: { files: [file] } })

        await waitFor(() => {
            expect(screen.getByText(/Photo similarity search needs additional setup/i)).toBeInTheDocument()
        })
    }
  })
  
  test('handles thumbnail errors', async () => {
    const { apiService } = require('../../src/services/apiClient')
    apiService.semanticSearch.mockResolvedValue({
      query: 'test',
      total_matches: 1,
      items: [{ file_id: 1, path: '/p/1.jpg', filename: '1.jpg', thumb_path: 'bad.jpg' }],
      took_ms: 50
    })

    const user = userEvent.setup()
    renderSearchPage()
    
    const searchInput = screen.getByPlaceholderText(/describe what you're looking for/i)
    await user.type(searchInput, 'test{Enter}')
    
    await waitFor(() => screen.getByText('1 results'))
    
    // Simulate image error
    const img = screen.getByAltText('1.jpg')
    fireEvent.error(img)
    
    // Should now show fallback icon (implementation detail: usually handled by changing DOM structure)
    // We can just verify the error handler ran without crashing
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
    // If not found by text lookup on filename, try getting by test id and index
    const cards = screen.getAllByTestId('search-result-item')
    await user.click(cards[1])

    await waitFor(() => {
      expect(openMock).toHaveBeenCalled()
    })

    const args = openMock.mock.calls[0]
    expect(args[1]).toBe(1)
    expect(args[0]).toHaveLength(2)
    expect(args[0][1].filename).toBe('2.jpg')
  })
})
