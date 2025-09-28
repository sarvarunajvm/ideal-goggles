/**
 * Component tests for SearchPage
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import SearchPage from '../../src/pages/SearchPage'

// Mock API client
jest.mock('../../src/services/apiClient', () => ({
  searchPhotos: jest.fn().mockResolvedValue({
    query: 'test',
    total_matches: 0,
    items: [],
    took_ms: 100
  }),
  searchByImage: jest.fn().mockResolvedValue({
    query: 'image_search',
    total_matches: 0,
    items: [],
    took_ms: 200
  })
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

  test('renders search input and search button', () => {
    renderSearchPage()

    // Will fail until SearchPage component is implemented
    expect(screen.getByPlaceholderText(/search photos/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /search/i })).toBeInTheDocument()
  })

  test('allows user to enter search query', async () => {
    const user = userEvent.setup()
    renderSearchPage()

    const searchInput = screen.getByPlaceholderText(/search photos/i)
    await user.type(searchInput, 'wedding photos')

    expect(searchInput).toHaveValue('wedding photos')
  })

  test('triggers search when search button is clicked', async () => {
    const user = userEvent.setup()
    renderSearchPage()

    const searchInput = screen.getByPlaceholderText(/search photos/i)
    const searchButton = screen.getByRole('button', { name: /search/i })

    await user.type(searchInput, 'test query')
    await user.click(searchButton)

    // Should call API and show results
    await waitFor(() => {
      expect(screen.getByText(/results/i)).toBeInTheDocument()
    })
  })

  test('shows drag and drop area for image search', () => {
    renderSearchPage()

    expect(screen.getByText(/drag.*drop.*photo/i)).toBeInTheDocument()
  })

  test('handles file drop for reverse image search', async () => {
    renderSearchPage()

    const dropZone = screen.getByTestId('image-drop-zone')
    const file = new File(['fake image'], 'test.jpg', { type: 'image/jpeg' })

    fireEvent.drop(dropZone, { dataTransfer: { files: [file] } })

    await waitFor(() => {
      expect(screen.getByText(/searching/i)).toBeInTheDocument()
    })
  })

  test('shows filter options', () => {
    renderSearchPage()

    expect(screen.getByText(/filters/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/date range/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/folder/i)).toBeInTheDocument()
  })

  test('meets constitutional performance requirement for search', async () => {
    const user = userEvent.setup()
    renderSearchPage()

    const searchInput = screen.getByPlaceholderText(/search photos/i)
    const searchButton = screen.getByRole('button', { name: /search/i })

    const startTime = Date.now()
    await user.type(searchInput, 'test')
    await user.click(searchButton)

    await waitFor(() => {
      expect(screen.getByText(/results/i)).toBeInTheDocument()
    })

    const endTime = Date.now()
    // Should feel responsive (UI response, not API response)
    expect(endTime - startTime).toBeLessThan(100)
  })

  test('displays search mode toggle', () => {
    renderSearchPage()

    expect(screen.getByText(/text search/i)).toBeInTheDocument()
    expect(screen.getByText(/image search/i)).toBeInTheDocument()
  })
})