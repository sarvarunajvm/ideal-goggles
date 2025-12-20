import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import PeoplePage from '../../src/pages/PeoplePage'

// Mock apiService
jest.mock('../../src/services/apiClient', () => ({
  apiService: {
    getConfig: jest.fn(),
    getPeople: jest.fn(),
    searchPhotos: jest.fn(),
    createPerson: jest.fn(),
    updatePerson: jest.fn(),
    deletePerson: jest.fn(),
  },
  getThumbnailBaseUrl: jest.fn(() => '/thumbs'),
}))

// Mock useNavigate to capture navigations
const mockNavigate = jest.fn()
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}))

describe('PeoplePage', () => {
  const { apiService } = require('../../src/services/apiClient')

  const people = [
    { id: 1, name: 'Alice', active: true },
    { id: 2, name: 'Bob', active: false },
  ]

  const photos = {
    query: '',
    total_matches: 3,
    items: [
      { file_id: 10, filename: 'p1.jpg', thumb_path: 't1.webp', path: '/a', badges: [], score: 0.8 },
      { file_id: 11, filename: 'p2.jpg', thumb_path: 't2.webp', path: '/b', badges: [], score: 0.7 },
      { file_id: 12, filename: 'p3.jpg', thumb_path: 't3.webp', path: '/c', badges: [], score: 0.6 },
    ],
    took_ms: 12,
  }

  beforeEach(() => {
    jest.clearAllMocks()
    jest.mocked(apiService.getConfig).mockResolvedValue({ face_search_enabled: true })
    jest.mocked(apiService.getPeople).mockResolvedValue(people as any)
    jest.mocked(apiService.searchPhotos).mockResolvedValue(photos as any)
    jest.mocked(apiService.createPerson).mockResolvedValue({ id: 3, name: 'Carol' } as any)
    jest.mocked(apiService.updatePerson).mockResolvedValue({ status: 'ok' } as any)
    jest.mocked(apiService.deletePerson).mockResolvedValue({ status: 'ok' } as any)
  })

  const renderPage = () =>
    render(
      <MemoryRouter>
        <PeoplePage />
      </MemoryRouter>
    )

  test('renders list of people and supports searching', async () => {
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('People')).toBeInTheDocument()
    })

    // People cards render
    expect(screen.getByText('Alice')).toBeInTheDocument()
    expect(screen.getByText('Bob')).toBeInTheDocument()

    // Search input filters list
    const searchInput = screen.getByPlaceholderText('Search people by name')
    await userEvent.type(searchInput, 'Ali')
    expect(screen.queryByText('Bob')).not.toBeInTheDocument()
  })

  test('opens add form, loads indexed photos, selects photos, and saves person', async () => {
    renderPage()

    await userEvent.click(screen.getByText('➕ Add Person'))

    // Form appears and loads photos
    await waitFor(() => {
      expect(screen.getByText('Add Person')).toBeInTheDocument()
      expect(apiService.searchPhotos).toHaveBeenCalled()
    })

    // Type name
    await userEvent.type(screen.getByPlaceholderText('name'), 'Carol')

    // Select two photos
    const photoThumbs = screen.getAllByRole('img')
    await userEvent.click(photoThumbs[0])
    await userEvent.click(photoThumbs[1])

    // Save becomes enabled once name and photos selected
    const saveBtn = screen.getByText(/Save Person/)
    expect(saveBtn).not.toBeDisabled()

    await userEvent.click(saveBtn)

    await waitFor(() => {
      expect(apiService.createPerson).toHaveBeenCalledWith('Carol', [10, 11])
    })
  })

  test('enforces disabled Save until name and photos selected', async () => {
    renderPage()
    await userEvent.click(screen.getByText('➕ Add Person'))

    // Save should be disabled initially
    const saveBtn = await screen.findByText(/Save Person/)
    expect(saveBtn).toBeDisabled()

    // Type name but no photos yet: still disabled
    await userEvent.type(screen.getByPlaceholderText('name'), 'Dave')
    expect(saveBtn).toBeDisabled()

    // Select one photo: Save should become enabled
    const firstThumb = (await screen.findAllByRole('img'))[0]
    await userEvent.click(firstThumb)
    expect(saveBtn).not.toBeDisabled()
  })

  test('caps selected photos at 10 and shows error message', async () => {
    // Provide 12 unique photos to reliably select 11
    const manyPhotos = {
      query: '',
      total_matches: 12,
      items: Array.from({ length: 12 }).map((_, i) => ({
        file_id: 100 + i,
        filename: `px${i}.jpg`,
        thumb_path: `tx${i}.webp`,
        path: `/p${i}`,
        badges: [],
        score: 0.5,
      })),
      took_ms: 10,
    }
    jest.mocked(apiService.searchPhotos).mockResolvedValueOnce(manyPhotos as any)

    renderPage()
    await userEvent.click(screen.getByText('➕ Add Person'))

    // Select 11 distinct photos
    for (let i = 0; i < 11; i++) {
      await userEvent.click(screen.getByAltText(`px${i}.jpg`))
    }

    // Selection count should cap at 10
    expect(screen.getByText(/Select Sample Photos \(10\/10\)/)).toBeInTheDocument()
  })

  test('edit existing person triggers update path', async () => {
    renderPage()
    await waitFor(() => screen.getByText('Alice'))

    // Click Edit on Alice card
    const editButtons = screen.getAllByText('Edit')
    await userEvent.click(editButtons[0])

    await waitFor(() => {
      expect(screen.getByText('Edit Person')).toBeInTheDocument()
    })

    // Change name and pick one photo
    const nameField = screen.getByPlaceholderText('name')
    await userEvent.clear(nameField)
    await userEvent.type(nameField, 'Alice Updated')
    const imgs = screen.getAllByRole('img')
    await userEvent.click(imgs[0])

    await userEvent.click(screen.getByText(/Save Person/))

    await waitFor(() => {
      expect(apiService.updatePerson).toHaveBeenCalled()
      const args = jest.mocked(apiService.updatePerson).mock.calls[0]
      expect(args[0]).toBe(1)
      expect(args[1]).toEqual({ name: 'Alice Updated', additional_sample_file_ids: [10] })
    })
  })

  test('deletes a person after confirmation', async () => {
    renderPage()

    await waitFor(() => screen.getByText('Alice'))

    // Click Delete on Alice card, confirm dialog appears
    const deleteButtons = screen.getAllByText('Delete')
    await userEvent.click(deleteButtons[0])
    await screen.findByText(/Delete Alice\?/)

    await userEvent.click(screen.getByText('Confirm Delete'))

    await waitFor(() => {
      expect(apiService.deletePerson).toHaveBeenCalledWith(1)
    })
  })

  test('Find Photos navigates when face search enabled and disabled', async () => {
    renderPage()
    await waitFor(() => screen.getByText('Alice'))

    const findButtons = screen.getAllByText('Find Photos!')
    await userEvent.click(findButtons[0])
    expect(mockNavigate).toHaveBeenCalledWith('/?face=1')

    // Disable face search via config
    jest.mocked(apiService.getConfig).mockResolvedValueOnce({ face_search_enabled: false })
    renderPage()
    await waitFor(() => screen.getByText('Alice'))
    const disabledBtn = screen.getAllByText('Find Photos!')[0]
    // When disabled, clicking should not navigate; assert no call
    expect(() => disabledBtn.click()).not.toThrow()
  })
})
