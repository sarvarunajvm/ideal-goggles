import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
// Vitest to Jest conversion
import { MemoryRouter } from 'react-router-dom'
import SearchPage from '../../src/pages/SearchPage'
import { apiService } from '../../src/services/apiClient'
import { osIntegration } from '../../src/services/osIntegration'

// Mock dependencies
jest.mock('../../src/services/apiClient', () => ({
  apiService: {
    searchPhotos: jest.fn(),
    semanticSearch: jest.fn(),
    imageSearch: jest.fn(),
  },
  getThumbnailBaseUrl: jest.fn(() => 'http://localhost:5555/thumbnails'),
}))

jest.mock('../../src/services/osIntegration', () => ({
  osIntegration: {
    revealInFolder: jest.fn(),
  },
}))

jest.mock('../../src/components/PreviewDrawer', () => ({
  default: ({ item, isOpen, onClose, onNext, onPrevious }: any) => {
    if (!isOpen) return null
    return (
      <div data-testid="preview-drawer">
        <div>{item?.filename}</div>
        <button onClick={onClose}>Close Preview</button>
        {onNext && <button onClick={onNext}>Next</button>}
        {onPrevious && <button onClick={onPrevious}>Previous</button>}
      </div>
    )
  },
}))

const mockSearchResults = {
  query: 'test query',
  total_matches: 25,
  took_ms: 150,
  items: [
    {
      file_id: 1,
      path: '/photos/photo1.jpg',
      folder: '/photos',
      filename: 'photo1.jpg',
      thumb_path: 'thumb1.jpg',
      shot_dt: '2024-01-15T10:00:00Z',
      score: 0.95,
      badges: ['landscape', 'sunset'],
      snippet: null,
    },
    {
      file_id: 2,
      path: '/photos/photo2.jpg',
      folder: '/photos',
      filename: 'photo2.jpg',
      thumb_path: 'thumb2.jpg',
      shot_dt: '2024-01-16T14:30:00Z',
      score: 0.87,
      badges: ['portrait'],
      snippet: 'text found in image',
    },
    {
      file_id: 3,
      path: '/photos/photo3.jpg',
      folder: '/photos',
      filename: 'photo3.jpg',
      thumb_path: null,
      shot_dt: null,
      score: 0.75,
      badges: [],
      snippet: null,
    },
  ],
}

describe('SearchPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  const renderComponent = () => {
    return render(
      <MemoryRouter>
        <SearchPage />
      </MemoryRouter>
    )
  }

  describe('Initial Rendering', () => {
    it('should render search mode tabs', () => {
      renderComponent()
      expect(screen.getByText('Text Search')).toBeInTheDocument()
      expect(screen.getByText('Semantic')).toBeInTheDocument()
      expect(screen.getByText('Image')).toBeInTheDocument()
    })

    it('should render text search as default mode', () => {
      renderComponent()
      expect(screen.getByPlaceholderText(/Search photos by filename/i)).toBeInTheDocument()
    })

    it('should render filter section', () => {
      renderComponent()
      expect(screen.getByText('Filters:')).toBeInTheDocument()
    })

    it('should render empty state message', () => {
      renderComponent()
      expect(screen.getByText('Search Your Photos')).toBeInTheDocument()
      expect(screen.getByText(/Enter a search term above/i)).toBeInTheDocument()
    })
  })

  describe('Text Search', () => {
    it('should allow typing in search input', async () => {
      const user = userEvent.setup()
      renderComponent()

      const searchInput = screen.getByPlaceholderText(/Search photos by filename/i)
      await user.type(searchInput, 'vacation photos')

      expect(searchInput).toHaveValue('vacation photos')
    })

    it('should execute text search on form submit', async () => {
      jest.mocked(apiService.searchPhotos).mockResolvedValue(mockSearchResults)

      const user = userEvent.setup()
      renderComponent()

      const searchInput = screen.getByPlaceholderText(/Search photos by filename/i)
      await user.type(searchInput, 'test query')

      const searchButton = screen.getByRole('button', { name: /Search/i })
      await user.click(searchButton)

      await waitFor(() => {
        expect(apiService.searchPhotos).toHaveBeenCalledWith({
          q: 'test query',
          from: '',
          to: '',
          folder: '',
          limit: 50,
        })
      })
    })

    it('should display search results', async () => {
      jest.mocked(apiService.searchPhotos).mockResolvedValue(mockSearchResults)

      const user = userEvent.setup()
      renderComponent()

      const searchInput = screen.getByPlaceholderText(/Search photos by filename/i)
      await user.type(searchInput, 'test query')
      await user.click(screen.getByRole('button', { name: /Search/i }))

      await waitFor(() => {
        expect(screen.getByText('photo1.jpg')).toBeInTheDocument()
        expect(screen.getByText('photo2.jpg')).toBeInTheDocument()
        expect(screen.getByText('photo3.jpg')).toBeInTheDocument()
      })
    })

    it('should show loading state during search', async () => {
      jest.mocked(apiService.searchPhotos).mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve(mockSearchResults), 100))
      )

      const user = userEvent.setup()
      renderComponent()

      const searchInput = screen.getByPlaceholderText(/Search photos by filename/i)
      await user.type(searchInput, 'test query')
      await user.click(screen.getByRole('button', { name: /Search/i }))

      // Should show skeleton loaders
      await waitFor(() => {
        expect(screen.getAllByRole('presentation').length).toBeGreaterThan(0)
      })
    })

    it('should show total matches count', async () => {
      jest.mocked(apiService.searchPhotos).mockResolvedValue(mockSearchResults)

      const user = userEvent.setup()
      renderComponent()

      const searchInput = screen.getByPlaceholderText(/Search photos by filename/i)
      await user.type(searchInput, 'test query')
      await user.click(screen.getByRole('button', { name: /Search/i }))

      await waitFor(() => {
        expect(screen.getByText(/25 photos found/i)).toBeInTheDocument()
      })
    })

    it('should show search duration', async () => {
      jest.mocked(apiService.searchPhotos).mockResolvedValue(mockSearchResults)

      const user = userEvent.setup()
      renderComponent()

      const searchInput = screen.getByPlaceholderText(/Search photos by filename/i)
      await user.type(searchInput, 'test query')
      await user.click(screen.getByRole('button', { name: /Search/i }))

      await waitFor(() => {
        expect(screen.getByText('150ms')).toBeInTheDocument()
      })
    })

    it('should disable search button when input is empty', () => {
      renderComponent()
      const searchButton = screen.getByRole('button', { name: /Search/i })
      expect(searchButton).toBeDisabled()
    })

    it('should handle search errors', async () => {
      jest.mocked(apiService.searchPhotos).mockRejectedValue(new Error('Search failed'))

      const user = userEvent.setup()
      renderComponent()

      const searchInput = screen.getByPlaceholderText(/Search photos by filename/i)
      await user.type(searchInput, 'test query')
      await user.click(screen.getByRole('button', { name: /Search/i }))

      await waitFor(() => {
        expect(screen.getByText('Search Error')).toBeInTheDocument()
        expect(screen.getByText('Search failed')).toBeInTheDocument()
      })
    })
  })

  describe('Semantic Search', () => {
    it('should switch to semantic search mode', async () => {
      const user = userEvent.setup()
      renderComponent()

      const semanticTab = screen.getByText('Semantic')
      await user.click(semanticTab)

      expect(screen.getByPlaceholderText(/Describe what you're looking for/i)).toBeInTheDocument()
    })

    it('should execute semantic search', async () => {
      jest.mocked(apiService.semanticSearch).mockResolvedValue(mockSearchResults)

      const user = userEvent.setup()
      renderComponent()

      await user.click(screen.getByText('Semantic'))

      const searchInput = screen.getByPlaceholderText(/Describe what you're looking for/i)
      await user.type(searchInput, 'sunset at the beach')
      await user.click(screen.getByRole('button', { name: /Search/i }))

      await waitFor(() => {
        expect(apiService.semanticSearch).toHaveBeenCalledWith('sunset at the beach', 50)
      })
    })

    it('should handle semantic search errors gracefully', async () => {
      jest.mocked(apiService.semanticSearch).mockRejectedValue(
        new Error('Semantic search failed')
      )

      const user = userEvent.setup()
      renderComponent()

      await user.click(screen.getByText('Semantic'))

      const searchInput = screen.getByPlaceholderText(/Describe what you're looking for/i)
      await user.type(searchInput, 'test')
      await user.click(screen.getByRole('button', { name: /Search/i }))

      await waitFor(() => {
        expect(screen.getByText(/Semantic search is not available/i)).toBeInTheDocument()
      })
    })

    it('should switch back to text search after semantic search error', async () => {
      jest.mocked(apiService.semanticSearch).mockRejectedValue(
        new Error('Semantic search failed')
      )

      const user = userEvent.setup()
      renderComponent()

      await user.click(screen.getByText('Semantic'))

      const searchInput = screen.getByPlaceholderText(/Describe what you're looking for/i)
      await user.type(searchInput, 'test')
      await user.click(screen.getByRole('button', { name: /Search/i }))

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Search photos by filename/i)).toBeInTheDocument()
      })
    })
  })

  describe('Image Search', () => {
    it('should switch to image search mode', async () => {
      const user = userEvent.setup()
      renderComponent()

      const imageTab = screen.getByText('Image')
      await user.click(imageTab)

      expect(screen.getByText('Upload an image to search')).toBeInTheDocument()
    })

    it('should handle file upload via input', async () => {
      jest.mocked(apiService.imageSearch).mockResolvedValue(mockSearchResults)

      const user = userEvent.setup()
      renderComponent()

      await user.click(screen.getByText('Image'))

      const file = new File(['dummy content'], 'query.jpg', { type: 'image/jpeg' })
      const input = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement

      await user.upload(input, file)

      await waitFor(() => {
        expect(apiService.imageSearch).toHaveBeenCalledWith(file, 50)
      })
    })

    it('should handle drag and drop', async () => {
      jest.mocked(apiService.imageSearch).mockResolvedValue(mockSearchResults)

      renderComponent()

      const user = userEvent.setup()
      await user.click(screen.getByText('Image'))

      const dropZone = screen.getByText('Upload an image to search').closest('div')!

      const file = new File(['dummy content'], 'query.jpg', { type: 'image/jpeg' })

      fireEvent.dragEnter(dropZone)
      fireEvent.drop(dropZone, {
        dataTransfer: {
          files: [file],
        },
      })

      await waitFor(() => {
        expect(apiService.imageSearch).toHaveBeenCalledWith(file, 50)
      })
    })

    it('should ignore non-image files in drag and drop', async () => {
      renderComponent()

      const user = userEvent.setup()
      await user.click(screen.getByText('Image'))

      const dropZone = screen.getByText('Upload an image to search').closest('div')!

      const file = new File(['dummy content'], 'document.pdf', { type: 'application/pdf' })

      fireEvent.drop(dropZone, {
        dataTransfer: {
          files: [file],
        },
      })

      await waitFor(() => {
        expect(apiService.imageSearch).not.toHaveBeenCalled()
      })
    })

    it('should handle image search errors', async () => {
      jest.mocked(apiService.imageSearch).mockRejectedValue(new Error('Image search failed'))

      const user = userEvent.setup()
      renderComponent()

      await user.click(screen.getByText('Image'))

      const file = new File(['dummy content'], 'query.jpg', { type: 'image/jpeg' })
      const input = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement

      await user.upload(input, file)

      await waitFor(() => {
        expect(screen.getByText(/Image search is not available/i)).toBeInTheDocument()
      })
    })
  })

  describe('Search Filters', () => {
    it('should apply date from filter', async () => {
      jest.mocked(apiService.searchPhotos).mockResolvedValue(mockSearchResults)

      const user = userEvent.setup()
      renderComponent()

      const dateFromInput = screen.getByPlaceholderText('From')
      await user.type(dateFromInput, '2024-01-01')

      const searchInput = screen.getByPlaceholderText(/Search photos by filename/i)
      await user.type(searchInput, 'test')
      await user.click(screen.getByRole('button', { name: /Search/i }))

      await waitFor(() => {
        expect(apiService.searchPhotos).toHaveBeenCalledWith({
          q: 'test',
          from: '2024-01-01',
          to: '',
          folder: '',
          limit: 50,
        })
      })
    })

    it('should apply date to filter', async () => {
      jest.mocked(apiService.searchPhotos).mockResolvedValue(mockSearchResults)

      const user = userEvent.setup()
      renderComponent()

      const dateToInput = screen.getByPlaceholderText('To')
      await user.type(dateToInput, '2024-12-31')

      const searchInput = screen.getByPlaceholderText(/Search photos by filename/i)
      await user.type(searchInput, 'test')
      await user.click(screen.getByRole('button', { name: /Search/i }))

      await waitFor(() => {
        expect(apiService.searchPhotos).toHaveBeenCalledWith({
          q: 'test',
          from: '',
          to: '2024-12-31',
          folder: '',
          limit: 50,
        })
      })
    })

    it('should apply folder filter', async () => {
      jest.mocked(apiService.searchPhotos).mockResolvedValue(mockSearchResults)

      const user = userEvent.setup()
      renderComponent()

      const folderInput = screen.getByPlaceholderText('Folder path...')
      await user.type(folderInput, '/photos/vacation')

      const searchInput = screen.getByPlaceholderText(/Search photos by filename/i)
      await user.type(searchInput, 'test')
      await user.click(screen.getByRole('button', { name: /Search/i }))

      await waitFor(() => {
        expect(apiService.searchPhotos).toHaveBeenCalledWith({
          q: 'test',
          from: '',
          to: '',
          folder: '/photos/vacation',
          limit: 50,
        })
      })
    })

    it('should apply limit filter', async () => {
      jest.mocked(apiService.searchPhotos).mockResolvedValue(mockSearchResults)

      const user = userEvent.setup()
      renderComponent()

      const limitInput = screen.getByRole('spinbutton')
      await user.clear(limitInput)
      await user.type(limitInput, '100')

      const searchInput = screen.getByPlaceholderText(/Search photos by filename/i)
      await user.type(searchInput, 'test')
      await user.click(screen.getByRole('button', { name: /Search/i }))

      await waitFor(() => {
        expect(apiService.searchPhotos).toHaveBeenCalledWith({
          q: 'test',
          from: '',
          to: '',
          folder: '',
          limit: 100,
        })
      })
    })

    it('should show clear filters button when filters are applied', async () => {
      const user = userEvent.setup()
      renderComponent()

      const dateFromInput = screen.getByPlaceholderText('From')
      await user.type(dateFromInput, '2024-01-01')

      expect(screen.getByText('Clear Filters')).toBeInTheDocument()
    })

    it('should clear all filters when clicking clear button', async () => {
      const user = userEvent.setup()
      renderComponent()

      const dateFromInput = screen.getByPlaceholderText('From')
      const dateToInput = screen.getByPlaceholderText('To')
      const folderInput = screen.getByPlaceholderText('Folder path...')

      await user.type(dateFromInput, '2024-01-01')
      await user.type(dateToInput, '2024-12-31')
      await user.type(folderInput, '/photos')

      const clearButton = screen.getByText('Clear Filters')
      await user.click(clearButton)

      expect(dateFromInput).toHaveValue('')
      expect(dateToInput).toHaveValue('')
      expect(folderInput).toHaveValue('')
    })
  })

  describe('Search Results Display', () => {
    it('should display photo thumbnails', async () => {
      jest.mocked(apiService.searchPhotos).mockResolvedValue(mockSearchResults)

      const user = userEvent.setup()
      renderComponent()

      await user.type(screen.getByPlaceholderText(/Search photos by filename/i), 'test')
      await user.click(screen.getByRole('button', { name: /Search/i }))

      await waitFor(() => {
        const images = screen.getAllByRole('img')
        expect(images.length).toBeGreaterThan(0)
      })
    })

    it('should display photo metadata', async () => {
      jest.mocked(apiService.searchPhotos).mockResolvedValue(mockSearchResults)

      const user = userEvent.setup()
      renderComponent()

      await user.type(screen.getByPlaceholderText(/Search photos by filename/i), 'test')
      await user.click(screen.getByRole('button', { name: /Search/i }))

      await waitFor(() => {
        expect(screen.getByText('/photos')).toBeInTheDocument()
        expect(screen.getByText('95%')).toBeInTheDocument()
      })
    })

    it('should display photo badges', async () => {
      jest.mocked(apiService.searchPhotos).mockResolvedValue(mockSearchResults)

      const user = userEvent.setup()
      renderComponent()

      await user.type(screen.getByPlaceholderText(/Search photos by filename/i), 'test')
      await user.click(screen.getByRole('button', { name: /Search/i }))

      await waitFor(() => {
        expect(screen.getByText('landscape')).toBeInTheDocument()
        expect(screen.getByText('sunset')).toBeInTheDocument()
        expect(screen.getByText('portrait')).toBeInTheDocument()
      })
    })

    it('should limit displayed badges to 2 plus count', async () => {
      const resultsWithManyBadges = {
        ...mockSearchResults,
        items: [
          {
            ...mockSearchResults.items[0],
            badges: ['tag1', 'tag2', 'tag3', 'tag4', 'tag5'],
          },
        ],
      }

      jest.mocked(apiService.searchPhotos).mockResolvedValue(resultsWithManyBadges)

      const user = userEvent.setup()
      renderComponent()

      await user.type(screen.getByPlaceholderText(/Search photos by filename/i), 'test')
      await user.click(screen.getByRole('button', { name: /Search/i }))

      await waitFor(() => {
        expect(screen.getByText('+3')).toBeInTheDocument()
      })
    })

    it('should show text badge for items with snippets', async () => {
      jest.mocked(apiService.searchPhotos).mockResolvedValue(mockSearchResults)

      const user = userEvent.setup()
      renderComponent()

      await user.type(screen.getByPlaceholderText(/Search photos by filename/i), 'test')
      await user.click(screen.getByRole('button', { name: /Search/i }))

      await waitFor(() => {
        expect(screen.getByText('Text')).toBeInTheDocument()
      })
    })

    it('should handle photos without thumbnails', async () => {
      jest.mocked(apiService.searchPhotos).mockResolvedValue(mockSearchResults)

      const user = userEvent.setup()
      renderComponent()

      await user.type(screen.getByPlaceholderText(/Search photos by filename/i), 'test')
      await user.click(screen.getByRole('button', { name: /Search/i }))

      await waitFor(() => {
        expect(screen.getByText('photo3.jpg')).toBeInTheDocument()
      })
    })
  })

  describe('Result Interactions', () => {
    it('should open preview drawer when clicking on result', async () => {
      jest.mocked(apiService.searchPhotos).mockResolvedValue(mockSearchResults)

      const user = userEvent.setup()
      renderComponent()

      await user.type(screen.getByPlaceholderText(/Search photos by filename/i), 'test')
      await user.click(screen.getByRole('button', { name: /Search/i }))

      await waitFor(() => {
        expect(screen.getByText('photo1.jpg')).toBeInTheDocument()
      })

      const resultCard = screen.getByText('photo1.jpg').closest('div')!
      await user.click(resultCard)

      expect(screen.getByTestId('preview-drawer')).toBeInTheDocument()
    })

    it('should reveal in folder when clicking reveal button', async () => {
      jest.mocked(apiService.searchPhotos).mockResolvedValue(mockSearchResults)
      jest.mocked(osIntegration.revealInFolder).mockResolvedValue()

      const user = userEvent.setup()
      renderComponent()

      await user.type(screen.getByPlaceholderText(/Search photos by filename/i), 'test')
      await user.click(screen.getByRole('button', { name: /Search/i }))

      await waitFor(() => {
        expect(screen.getByText('photo1.jpg')).toBeInTheDocument()
      })

      const revealButtons = screen.getAllByRole('button')
      const revealButton = revealButtons.find(btn =>
        btn.querySelector('svg') && btn.getAttribute('class')?.includes('backdrop-blur')
      )

      await user.click(revealButton!)

      await waitFor(() => {
        expect(osIntegration.revealInFolder).toHaveBeenCalledWith('/photos/photo1.jpg')
      })
    })

    it('should navigate through results in preview', async () => {
      jest.mocked(apiService.searchPhotos).mockResolvedValue(mockSearchResults)

      const user = userEvent.setup()
      renderComponent()

      await user.type(screen.getByPlaceholderText(/Search photos by filename/i), 'test')
      await user.click(screen.getByRole('button', { name: /Search/i }))

      await waitFor(() => {
        expect(screen.getByText('photo1.jpg')).toBeInTheDocument()
      })

      const resultCard = screen.getByText('photo1.jpg').closest('div')!
      await user.click(resultCard)

      const nextButton = screen.getByText('Next')
      await user.click(nextButton)

      expect(screen.getByText('photo2.jpg')).toBeInTheDocument()
    })

    it('should navigate backwards through results in preview', async () => {
      jest.mocked(apiService.searchPhotos).mockResolvedValue(mockSearchResults)

      const user = userEvent.setup()
      renderComponent()

      await user.type(screen.getByPlaceholderText(/Search photos by filename/i), 'test')
      await user.click(screen.getByRole('button', { name: /Search/i }))

      await waitFor(() => {
        expect(screen.getByText('photo2.jpg')).toBeInTheDocument()
      })

      const resultCard = screen.getByText('photo2.jpg').closest('div')!
      await user.click(resultCard)

      const previousButton = screen.getByText('Previous')
      await user.click(previousButton)

      expect(screen.getByText('photo1.jpg')).toBeInTheDocument()
    })

    it('should wrap around when navigating past last item', async () => {
      jest.mocked(apiService.searchPhotos).mockResolvedValue(mockSearchResults)

      const user = userEvent.setup()
      renderComponent()

      await user.type(screen.getByPlaceholderText(/Search photos by filename/i), 'test')
      await user.click(screen.getByRole('button', { name: /Search/i }))

      await waitFor(() => {
        expect(screen.getByText('photo3.jpg')).toBeInTheDocument()
      })

      const resultCard = screen.getByText('photo3.jpg').closest('div')!
      await user.click(resultCard)

      const nextButton = screen.getByText('Next')
      await user.click(nextButton)

      // Should wrap to first item
      expect(screen.getByText('photo1.jpg')).toBeInTheDocument()
    })

    it('should close preview drawer', async () => {
      jest.mocked(apiService.searchPhotos).mockResolvedValue(mockSearchResults)

      const user = userEvent.setup()
      renderComponent()

      await user.type(screen.getByPlaceholderText(/Search photos by filename/i), 'test')
      await user.click(screen.getByRole('button', { name: /Search/i }))

      await waitFor(() => {
        expect(screen.getByText('photo1.jpg')).toBeInTheDocument()
      })

      const resultCard = screen.getByText('photo1.jpg').closest('div')!
      await user.click(resultCard)

      const closeButton = screen.getByText('Close Preview')
      await user.click(closeButton)

      expect(screen.queryByTestId('preview-drawer')).not.toBeInTheDocument()
    })
  })

  describe('Empty States', () => {
    it('should show empty state when no results found', async () => {
      jest.mocked(apiService.searchPhotos).mockResolvedValue({
        query: 'test',
        total_matches: 0,
        took_ms: 50,
        items: [],
      })

      const user = userEvent.setup()
      renderComponent()

      await user.type(screen.getByPlaceholderText(/Search photos by filename/i), 'test')
      await user.click(screen.getByRole('button', { name: /Search/i }))

      await waitFor(() => {
        expect(screen.getByText('0 photos found')).toBeInTheDocument()
      })
    })
  })

  describe('Error Handling', () => {
    it('should handle network errors', async () => {
      jest.mocked(apiService.searchPhotos).mockRejectedValue(new Error('Network error'))

      const user = userEvent.setup()
      renderComponent()

      await user.type(screen.getByPlaceholderText(/Search photos by filename/i), 'test')
      await user.click(screen.getByRole('button', { name: /Search/i }))

      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument()
      })
    })

    it('should handle reveal in folder errors silently', async () => {
      jest.mocked(apiService.searchPhotos).mockResolvedValue(mockSearchResults)
      jest.mocked(osIntegration.revealInFolder).mockRejectedValue(new Error('Failed'))

      const user = userEvent.setup()
      renderComponent()

      await user.type(screen.getByPlaceholderText(/Search photos by filename/i), 'test')
      await user.click(screen.getByRole('button', { name: /Search/i }))

      await waitFor(() => {
        expect(screen.getByText('photo1.jpg')).toBeInTheDocument()
      })

      const revealButtons = screen.getAllByRole('button')
      const revealButton = revealButtons.find(btn =>
        btn.querySelector('svg') && btn.getAttribute('class')?.includes('backdrop-blur')
      )

      await user.click(revealButton!)

      // Should not throw or show error
      expect(screen.getByText('photo1.jpg')).toBeInTheDocument()
    })
  })

  describe('Edge Cases', () => {
    it('should handle empty search query gracefully', async () => {
      renderComponent()

      const searchButton = screen.getByRole('button', { name: /Search/i })
      expect(searchButton).toBeDisabled()
    })

    it('should trim whitespace from search query', async () => {
      jest.mocked(apiService.searchPhotos).mockResolvedValue(mockSearchResults)

      const user = userEvent.setup()
      renderComponent()

      await user.type(screen.getByPlaceholderText(/Search photos by filename/i), '  test query  ')
      await user.click(screen.getByRole('button', { name: /Search/i }))

      await waitFor(() => {
        expect(apiService.searchPhotos).toHaveBeenCalledWith({
          q: 'test query',
          from: '',
          to: '',
          folder: '',
          limit: 50,
        })
      })
    })

    it('should not show next/previous buttons for single result', async () => {
      jest.mocked(apiService.searchPhotos).mockResolvedValue({
        ...mockSearchResults,
        items: [mockSearchResults.items[0]],
        total_matches: 1,
      })

      const user = userEvent.setup()
      renderComponent()

      await user.type(screen.getByPlaceholderText(/Search photos by filename/i), 'test')
      await user.click(screen.getByRole('button', { name: /Search/i }))

      await waitFor(() => {
        expect(screen.getByText('photo1.jpg')).toBeInTheDocument()
      })

      const resultCard = screen.getByText('photo1.jpg').closest('div')!
      await user.click(resultCard)

      expect(screen.queryByText('Next')).not.toBeInTheDocument()
      expect(screen.queryByText('Previous')).not.toBeInTheDocument()
    })

    it('should handle invalid limit values', async () => {
      const user = userEvent.setup()
      renderComponent()

      const limitInput = screen.getByRole('spinbutton')
      await user.clear(limitInput)
      await user.type(limitInput, '0')

      // Should reset to default or minimum
      expect(limitInput).toHaveValue(50)
    })

    it('should prevent search when loading', async () => {
      jest.mocked(apiService.searchPhotos).mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve(mockSearchResults), 1000))
      )

      const user = userEvent.setup()
      renderComponent()

      await user.type(screen.getByPlaceholderText(/Search photos by filename/i), 'test')
      const searchButton = screen.getByRole('button', { name: /Search/i })
      await user.click(searchButton)

      // Button should be disabled during loading
      expect(searchButton).toBeDisabled()
    })

    it('should handle concurrent searches by using latest results', async () => {
      let resolveFirst: any
      let resolveSecond: any

      const firstPromise = new Promise(resolve => { resolveFirst = resolve })
      const secondPromise = new Promise(resolve => { resolveSecond = resolve })

      jest.mocked(apiService.searchPhotos)
        .mockImplementationOnce(() => firstPromise as any)
        .mockImplementationOnce(() => secondPromise as any)

      const user = userEvent.setup()
      renderComponent()

      // Start first search
      await user.type(screen.getByPlaceholderText(/Search photos by filename/i), 'first')
      await user.click(screen.getByRole('button', { name: /Search/i }))

      // Start second search
      await user.clear(screen.getByPlaceholderText(/Search photos by filename/i))
      await user.type(screen.getByPlaceholderText(/Search photos by filename/i), 'second')
      await user.click(screen.getByRole('button', { name: /Search/i }))

      // Resolve second search first
      resolveSecond({
        query: 'second',
        total_matches: 1,
        took_ms: 50,
        items: [mockSearchResults.items[1]],
      })

      await waitFor(() => {
        expect(screen.getByText('photo2.jpg')).toBeInTheDocument()
      })

      // Resolve first search (should be ignored)
      resolveFirst(mockSearchResults)

      // Should still show second search results
      expect(screen.getByText('photo2.jpg')).toBeInTheDocument()
    })

    it('should handle drag leave event', async () => {
      renderComponent()

      const user = userEvent.setup()
      await user.click(screen.getByText('Image'))

      const dropZone = screen.getByText('Upload an image to search').closest('div')!

      fireEvent.dragEnter(dropZone)
      fireEvent.dragLeave(dropZone)

      // Should reset drag state (visually)
      expect(dropZone).toBeInTheDocument()
    })

    it('should handle empty file list in image upload', async () => {
      renderComponent()

      const user = userEvent.setup()
      await user.click(screen.getByText('Image'))

      const input = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement

      fireEvent.change(input, { target: { files: [] } })

      // Should not crash
      expect(screen.getByText('Upload an image to search')).toBeInTheDocument()
    })
  })

  describe('Search Mode Badge', () => {
    it('should display current search mode badge in results', async () => {
      jest.mocked(apiService.searchPhotos).mockResolvedValue(mockSearchResults)

      const user = userEvent.setup()
      renderComponent()

      await user.type(screen.getByPlaceholderText(/Search photos by filename/i), 'test')
      await user.click(screen.getByRole('button', { name: /Search/i }))

      await waitFor(() => {
        expect(screen.getByText('text search')).toBeInTheDocument()
      })
    })

    it('should show semantic badge for semantic searches', async () => {
      jest.mocked(apiService.semanticSearch).mockResolvedValue(mockSearchResults)

      const user = userEvent.setup()
      renderComponent()

      await user.click(screen.getByText('Semantic'))
      await user.type(screen.getByPlaceholderText(/Describe what you're looking for/i), 'test')
      await user.click(screen.getByRole('button', { name: /Search/i }))

      await waitFor(() => {
        expect(screen.getByText('semantic search')).toBeInTheDocument()
      })
    })

    it('should show image badge for image searches', async () => {
      jest.mocked(apiService.imageSearch).mockResolvedValue(mockSearchResults)

      const user = userEvent.setup()
      renderComponent()

      await user.click(screen.getByText('Image'))

      const file = new File(['dummy content'], 'query.jpg', { type: 'image/jpeg' })
      const input = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement
      await user.upload(input, file)

      await waitFor(() => {
        expect(screen.getByText('image search')).toBeInTheDocument()
      })
    })
  })
})
