/**
 * Unit tests for People Page
 * Priority: P2 (Page-level functionality)
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import PeoplePage from '../../src/pages/PeoplePage'
import { apiService } from '../../src/services/apiClient'

// Mock API service
jest.mock('../../src/services/apiClient', () => ({
  apiService: {
    getPeople: jest.fn(),
    createPerson: jest.fn(),
    searchFaces: jest.fn()
  }
}))

const mockPeople = [
  {
    id: 1,
    name: 'John Doe',
    sample_count: 5,
    last_seen: '2024-01-15T10:00:00Z'
  },
  {
    id: 2,
    name: 'Jane Smith',
    sample_count: 3,
    last_seen: '2024-01-14T15:30:00Z'
  }
]

describe('People Page', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    ;(apiService.getPeople as jest.Mock).mockResolvedValue(mockPeople)
  })

  const renderPeoplePage = () => {
    return render(
      <MemoryRouter>
        <PeoplePage />
      </MemoryRouter>
    )
  }

  test('renders people page with header', async () => {
    renderPeoplePage()

    expect(screen.getByText(/People/i)).toBeInTheDocument()
    expect(screen.getByText(/Manage recognized people/i)).toBeInTheDocument()
  })

  test('loads and displays people list', async () => {
    renderPeoplePage()

    await waitFor(() => {
      expect(apiService.getPeople).toHaveBeenCalled()
    })

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
      expect(screen.getByText('Jane Smith')).toBeInTheDocument()
    })
  })

  test('displays person sample count', async () => {
    renderPeoplePage()

    await waitFor(() => {
      expect(screen.getByText(/5 samples/i)).toBeInTheDocument()
      expect(screen.getByText(/3 samples/i)).toBeInTheDocument()
    })
  })

  test('handles empty people list', async () => {
    ;(apiService.getPeople as jest.Mock).mockResolvedValue([])
    renderPeoplePage()

    await waitFor(() => {
      expect(screen.getByText(/No people found/i)).toBeInTheDocument()
    })
  })

  test('handles loading state', () => {
    renderPeoplePage()

    expect(screen.getByText(/Loading/i)).toBeInTheDocument()
  })

  test('handles error state', async () => {
    ;(apiService.getPeople as jest.Mock).mockRejectedValue(
      new Error('Failed to load people')
    )

    renderPeoplePage()

    await waitFor(() => {
      expect(screen.getByText(/Error loading people/i)).toBeInTheDocument()
    })
  })

  test('opens add person dialog', async () => {
    const user = userEvent.setup()
    renderPeoplePage()

    const addButton = await screen.findByText(/Add Person/i)
    await user.click(addButton)

    expect(screen.getByText(/Create New Person/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/Person name/i)).toBeInTheDocument()
  })

  test('creates new person', async () => {
    const user = userEvent.setup()
    ;(apiService.createPerson as jest.Mock).mockResolvedValue({
      id: 3,
      name: 'New Person'
    })

    renderPeoplePage()

    const addButton = await screen.findByText(/Add Person/i)
    await user.click(addButton)

    const nameInput = screen.getByPlaceholderText(/Person name/i)
    await user.type(nameInput, 'New Person')

    const createButton = screen.getByRole('button', { name: /Create/i })
    await user.click(createButton)

    await waitFor(() => {
      expect(apiService.createPerson).toHaveBeenCalledWith('New Person', [])
    })
  })

  test('searches for person faces', async () => {
    const user = userEvent.setup()
    ;(apiService.searchFaces as jest.Mock).mockResolvedValue({
      items: [],
      total_matches: 10
    })

    renderPeoplePage()

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    const searchButton = screen.getAllByText(/Search/i)[0]
    await user.click(searchButton)

    await waitFor(() => {
      expect(apiService.searchFaces).toHaveBeenCalledWith(1, 100)
    })
  })

  test('filters people by name', async () => {
    const user = userEvent.setup()
    renderPeoplePage()

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    const searchInput = screen.getByPlaceholderText(/Search people/i)
    await user.type(searchInput, 'John')

    expect(screen.getByText('John Doe')).toBeInTheDocument()
    expect(screen.queryByText('Jane Smith')).not.toBeInTheDocument()
  })

  test('sorts people by name', async () => {
    const user = userEvent.setup()
    renderPeoplePage()

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    const sortButton = screen.getByText(/Sort by Name/i)
    await user.click(sortButton)

    const peopleNames = screen.getAllByTestId('person-name')
    expect(peopleNames[0]).toHaveTextContent('Jane Smith')
    expect(peopleNames[1]).toHaveTextContent('John Doe')
  })

  test('sorts people by sample count', async () => {
    const user = userEvent.setup()
    renderPeoplePage()

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    const sortButton = screen.getByText(/Sort by Samples/i)
    await user.click(sortButton)

    const peopleNames = screen.getAllByTestId('person-name')
    expect(peopleNames[0]).toHaveTextContent('John Doe') // 5 samples
    expect(peopleNames[1]).toHaveTextContent('Jane Smith') // 3 samples
  })

  test('handles pagination', async () => {
    const manyPeople = Array.from({ length: 25 }, (_, i) => ({
      id: i + 1,
      name: `Person ${i + 1}`,
      sample_count: i,
      last_seen: '2024-01-15T10:00:00Z'
    }))

    ;(apiService.getPeople as jest.Mock).mockResolvedValue(manyPeople)

    const user = userEvent.setup()
    renderPeoplePage()

    await waitFor(() => {
      expect(screen.getByText('Person 1')).toBeInTheDocument()
    })

    // Should show first 20 items
    expect(screen.getByText('Person 1')).toBeInTheDocument()
    expect(screen.getByText('Person 20')).toBeInTheDocument()
    expect(screen.queryByText('Person 21')).not.toBeInTheDocument()

    // Click next page
    const nextButton = screen.getByText(/Next/i)
    await user.click(nextButton)

    expect(screen.queryByText('Person 1')).not.toBeInTheDocument()
    expect(screen.getByText('Person 21')).toBeInTheDocument()
  })

  test('deletes person with confirmation', async () => {
    const user = userEvent.setup()
    renderPeoplePage()

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    const deleteButton = screen.getAllByText(/Delete/i)[0]
    await user.click(deleteButton)

    // Confirm deletion
    const confirmButton = screen.getByRole('button', { name: /Confirm/i })
    await user.click(confirmButton)

    await waitFor(() => {
      expect(screen.queryByText('John Doe')).not.toBeInTheDocument()
    })
  })

  test('cancels person deletion', async () => {
    const user = userEvent.setup()
    renderPeoplePage()

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    const deleteButton = screen.getAllByText(/Delete/i)[0]
    await user.click(deleteButton)

    // Cancel deletion
    const cancelButton = screen.getByRole('button', { name: /Cancel/i })
    await user.click(cancelButton)

    expect(screen.getByText('John Doe')).toBeInTheDocument()
  })

  test('shows person details on click', async () => {
    const user = userEvent.setup()
    renderPeoplePage()

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    const personCard = screen.getByText('John Doe').closest('div')!
    await user.click(personCard)

    expect(screen.getByText(/Last seen:/i)).toBeInTheDocument()
    expect(screen.getByText(/Sample photos/i)).toBeInTheDocument()
  })
})