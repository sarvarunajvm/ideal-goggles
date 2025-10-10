import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
// Vitest to Jest conversion
import { MemoryRouter } from 'react-router-dom'
import PeoplePage from '../../src/pages/PeoplePage'
import { apiService } from '../../src/services/apiClient'

// Mock dependencies
jest.mock('../../src/services/apiClient', () => ({
  apiService: {
    getConfig: jest.fn(),
  },
}))

jest.mock('react-router-dom', () => {
  const actual = jest.requireActual('react-router-dom')
  return {
    ...actual,
    useNavigate: jest.fn(),
  }
})

const mockNavigate = jest.fn()

describe('PeoplePage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    jest.useFakeTimers()

    // Mock useNavigate
    const { useNavigate } = require('react-router-dom')
    useNavigate.mockReturnValue(mockNavigate)

    // Mock getConfig
    jest.mocked(apiService.getConfig).mockResolvedValue({
      roots: [],
      ocr_languages: [],
      face_search_enabled: true,
      index_version: '1.0.0',
    })

    // Mock URL.createObjectURL
    global.URL.createObjectURL = jest.fn(() => 'blob:mock-url')
    global.URL.revokeObjectURL = jest.fn()
  })

  afterEach(() => {
    jest.runOnlyPendingTimers()
    jest.useRealTimers()
  })

  const renderComponent = () => {
    return render(
      <MemoryRouter>
        <PeoplePage />
      </MemoryRouter>
    )
  }

  describe('Initial Rendering', () => {
    it('should render the page title', async () => {
      renderComponent()
      expect(screen.getByText('People')).toBeInTheDocument()
    })

    it('should render add person button', async () => {
      renderComponent()
      expect(screen.getByText('➕ Add Person')).toBeInTheDocument()
    })

    it('should render search input', async () => {
      renderComponent()
      expect(screen.getByPlaceholderText('Search people by name')).toBeInTheDocument()
    })

    it('should check face search enabled status on mount', async () => {
      renderComponent()
      await waitFor(() => {
        expect(apiService.getConfig).toHaveBeenCalled()
      })
    })
  })

  describe('Add Person Form', () => {
    it('should open add person form when clicking add button', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      const addButton = screen.getByText('➕ Add Person')
      await user.click(addButton)

      expect(screen.getByText('Add Person')).toBeInTheDocument()
      expect(screen.getByLabelText('Name')).toBeInTheDocument()
      expect(screen.getByText('Upload Photos')).toBeInTheDocument()
    })

    it('should allow entering person name', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))
      const nameInput = screen.getByLabelText('Name')
      await user.type(nameInput, 'John Doe')

      expect(nameInput).toHaveValue('John Doe')
    })

    it('should show error when saving without name', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))
      const saveButton = screen.getByText('Save Person')
      await user.click(saveButton)

      expect(screen.getByText('Person name cannot be empty')).toBeInTheDocument()
    })

    it('should show error when saving without photos', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))
      const nameInput = screen.getByLabelText('Name')
      await user.type(nameInput, 'John Doe')

      const saveButton = screen.getByText('Save Person')
      await user.click(saveButton)

      expect(screen.getByText('At least one photo is required')).toBeInTheDocument()
    })

    it('should handle file upload', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))

      const file = new File(['dummy content'], 'test.jpg', { type: 'image/jpeg' })
      const input = document.getElementById('new-person-file') as HTMLInputElement

      await user.upload(input, file)

      expect(global.URL.createObjectURL).toHaveBeenCalled()
    })

    it('should display uploaded photos in gallery', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))

      const file = new File(['dummy content'], 'test.jpg', { type: 'image/jpeg' })
      const input = document.getElementById('new-person-file') as HTMLInputElement
      await user.upload(input, file)

      const gallery = screen.getByTestId('photo-gallery')
      expect(gallery).toBeInTheDocument()
      expect(gallery.querySelector('img')).toBeInTheDocument()
    })

    it('should create new person when form is valid', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))

      const nameInput = screen.getByLabelText('Name')
      await user.type(nameInput, 'John Doe')

      const file = new File(['dummy content'], 'test.jpg', { type: 'image/jpeg' })
      const input = document.getElementById('new-person-file') as HTMLInputElement
      await user.upload(input, file)

      const saveButton = screen.getByText('Save Person')
      await user.click(saveButton)

      // Should show in people list
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument()
      })
    })

    it('should close form after successful save', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))

      const nameInput = screen.getByLabelText('Name')
      await user.type(nameInput, 'John Doe')

      const file = new File(['dummy content'], 'test.jpg', { type: 'image/jpeg' })
      const input = document.getElementById('new-person-file') as HTMLInputElement
      await user.upload(input, file)

      const saveButton = screen.getByText('Save Person')
      await user.click(saveButton)

      await waitFor(() => {
        expect(screen.queryByText('Add Person')).not.toBeInTheDocument()
      })
    })

    it('should show toast notification after save', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))

      const nameInput = screen.getByLabelText('Name')
      await user.type(nameInput, 'John Doe')

      const file = new File(['dummy content'], 'test.jpg', { type: 'image/jpeg' })
      const input = document.getElementById('new-person-file') as HTMLInputElement
      await user.upload(input, file)

      const saveButton = screen.getByText('Save Person')
      await user.click(saveButton)

      expect(screen.getByText('Saved')).toBeInTheDocument()
    })

    it('should hide toast after timeout', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))

      const nameInput = screen.getByLabelText('Name')
      await user.type(nameInput, 'John Doe')

      const file = new File(['dummy content'], 'test.jpg', { type: 'image/jpeg' })
      const input = document.getElementById('new-person-file') as HTMLInputElement
      await user.upload(input, file)

      const saveButton = screen.getByText('Save Person')
      await user.click(saveButton)

      expect(screen.getByText('Saved')).toBeInTheDocument()

      jest.advanceTimersByTime(1200)

      await waitFor(() => {
        expect(screen.queryByText('Saved')).not.toBeInTheDocument()
      })
    })

    it('should cancel form and reset state', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))

      const nameInput = screen.getByLabelText('Name')
      await user.type(nameInput, 'John Doe')

      const cancelButton = screen.getByText('Cancel')
      await user.click(cancelButton)

      expect(screen.queryByText('Add Person')).not.toBeInTheDocument()

      // Reopen form to verify reset
      await user.click(screen.getByText('➕ Add Person'))
      const nameInputAgain = screen.getByLabelText('Name')
      expect(nameInputAgain).toHaveValue('')
    })

    it('should handle multiple file uploads', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))

      const files = [
        new File(['content1'], 'test1.jpg', { type: 'image/jpeg' }),
        new File(['content2'], 'test2.jpg', { type: 'image/jpeg' }),
      ]
      const input = document.getElementById('new-person-file') as HTMLInputElement
      await user.upload(input, files)

      const gallery = screen.getByTestId('photo-gallery')
      const images = gallery.querySelectorAll('img')
      expect(images).toHaveLength(2)
    })
  })

  describe('Search Functionality', () => {
    it('should filter people by name', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      // Add two people
      await user.click(screen.getByText('➕ Add Person'))
      await user.type(screen.getByLabelText('Name'), 'John Doe')
      const file1 = new File(['content'], 'test.jpg', { type: 'image/jpeg' })
      await user.upload(document.getElementById('new-person-file') as HTMLInputElement, file1)
      await user.click(screen.getByText('Save Person'))

      await user.click(screen.getByText('➕ Add Person'))
      await user.type(screen.getByLabelText('Name'), 'Jane Smith')
      const file2 = new File(['content'], 'test.jpg', { type: 'image/jpeg' })
      await user.upload(document.getElementById('new-person-file') as HTMLInputElement, file2)
      await user.click(screen.getByText('Save Person'))

      // Search for John
      const searchInput = screen.getByPlaceholderText('Search people by name')
      await user.type(searchInput, 'John')

      expect(screen.getByText('John Doe')).toBeInTheDocument()
      expect(screen.queryByText('Jane Smith')).not.toBeInTheDocument()
    })

    it('should be case insensitive', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))
      await user.type(screen.getByLabelText('Name'), 'John Doe')
      const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' })
      await user.upload(document.getElementById('new-person-file') as HTMLInputElement, file)
      await user.click(screen.getByText('Save Person'))

      const searchInput = screen.getByPlaceholderText('Search people by name')
      await user.type(searchInput, 'JOHN')

      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    it('should show all people when search is cleared', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))
      await user.type(screen.getByLabelText('Name'), 'John Doe')
      const file1 = new File(['content'], 'test.jpg', { type: 'image/jpeg' })
      await user.upload(document.getElementById('new-person-file') as HTMLInputElement, file1)
      await user.click(screen.getByText('Save Person'))

      await user.click(screen.getByText('➕ Add Person'))
      await user.type(screen.getByLabelText('Name'), 'Jane Smith')
      const file2 = new File(['content'], 'test.jpg', { type: 'image/jpeg' })
      await user.upload(document.getElementById('new-person-file') as HTMLInputElement, file2)
      await user.click(screen.getByText('Save Person'))

      const searchInput = screen.getByPlaceholderText('Search people by name')
      await user.type(searchInput, 'John')
      expect(screen.queryByText('Jane Smith')).not.toBeInTheDocument()

      await user.clear(searchInput)
      expect(screen.getByText('John Doe')).toBeInTheDocument()
      expect(screen.getByText('Jane Smith')).toBeInTheDocument()
    })
  })

  describe('Person Details', () => {
    it('should display person card with details', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))
      await user.type(screen.getByLabelText('Name'), 'John Doe')
      const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' })
      await user.upload(document.getElementById('new-person-file') as HTMLInputElement, file)
      await user.click(screen.getByText('Save Person'))

      const personCard = screen.getByTestId('person-item')
      expect(personCard).toBeInTheDocument()
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    it('should show photo count', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))
      await user.type(screen.getByLabelText('Name'), 'John Doe')
      const files = [
        new File(['content1'], 'test1.jpg', { type: 'image/jpeg' }),
        new File(['content2'], 'test2.jpg', { type: 'image/jpeg' }),
      ]
      await user.upload(document.getElementById('new-person-file') as HTMLInputElement, files)
      await user.click(screen.getByText('Save Person'))

      expect(screen.getByText('2 sample photos')).toBeInTheDocument()
    })

    it('should show singular photo text for one photo', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))
      await user.type(screen.getByLabelText('Name'), 'John Doe')
      const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' })
      await user.upload(document.getElementById('new-person-file') as HTMLInputElement, file)
      await user.click(screen.getByText('Save Person'))

      expect(screen.getByText('1 sample photo')).toBeInTheDocument()
    })

    it('should show enrolled date', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))
      await user.type(screen.getByLabelText('Name'), 'John Doe')
      const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' })
      await user.upload(document.getElementById('new-person-file') as HTMLInputElement, file)
      await user.click(screen.getByText('Save Person'))

      const enrolledDate = screen.getByTestId('enrolled-date')
      expect(enrolledDate).toBeInTheDocument()
      expect(enrolledDate.textContent).toContain('Added')
    })

    it('should show active badge', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))
      await user.type(screen.getByLabelText('Name'), 'John Doe')
      const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' })
      await user.upload(document.getElementById('new-person-file') as HTMLInputElement, file)
      await user.click(screen.getByText('Save Person'))

      expect(screen.getByText('Active')).toBeInTheDocument()
    })
  })

  describe('Person Selection and Details', () => {
    it('should expand person details when clicking card', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))
      await user.type(screen.getByLabelText('Name'), 'John Doe')
      const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' })
      await user.upload(document.getElementById('new-person-file') as HTMLInputElement, file)
      await user.click(screen.getByText('Save Person'))

      const personCard = screen.getByTestId('person-item')
      await user.click(personCard)

      expect(screen.getByText('Photos')).toBeInTheDocument()
      expect(screen.getByText('Delete John Doe?')).toBeInTheDocument()
    })

    it('should show photo gallery in expanded view', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))
      await user.type(screen.getByLabelText('Name'), 'John Doe')
      const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' })
      await user.upload(document.getElementById('new-person-file') as HTMLInputElement, file)
      await user.click(screen.getByText('Save Person'))

      const personCard = screen.getByTestId('person-item')
      await user.click(personCard)

      const galleries = screen.getAllByTestId('photo-gallery')
      expect(galleries.length).toBeGreaterThan(0)
    })

    it('should allow uploading additional photos to existing person', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))
      await user.type(screen.getByLabelText('Name'), 'John Doe')
      const file1 = new File(['content'], 'test.jpg', { type: 'image/jpeg' })
      await user.upload(document.getElementById('new-person-file') as HTMLInputElement, file1)
      await user.click(screen.getByText('Save Person'))

      const personCard = screen.getByTestId('person-item')
      await user.click(personCard)

      // Get the person's file input from the expanded view
      const fileInputs = document.querySelectorAll('input[type="file"]')
      const personFileInput = Array.from(fileInputs).find(input =>
        input.id.startsWith('file-')
      ) as HTMLInputElement

      const file2 = new File(['content2'], 'test2.jpg', { type: 'image/jpeg' })
      await user.upload(personFileInput, file2)

      expect(global.URL.createObjectURL).toHaveBeenCalled()
    })
  })

  describe('Edit Person', () => {
    it('should open edit form when clicking edit button', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))
      await user.type(screen.getByLabelText('Name'), 'John Doe')
      const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' })
      await user.upload(document.getElementById('new-person-file') as HTMLInputElement, file)
      await user.click(screen.getByText('Save Person'))

      const editButton = screen.getByText('Edit')
      await user.click(editButton)

      expect(screen.getByText('Edit Person')).toBeInTheDocument()
      expect(screen.getByLabelText('Name')).toHaveValue('John Doe')
    })

    it('should update person when saving edited form', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))
      await user.type(screen.getByLabelText('Name'), 'John Doe')
      const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' })
      await user.upload(document.getElementById('new-person-file') as HTMLInputElement, file)
      await user.click(screen.getByText('Save Person'))

      const editButton = screen.getByText('Edit')
      await user.click(editButton)

      const nameInput = screen.getByLabelText('Name')
      await user.clear(nameInput)
      await user.type(nameInput, 'Jane Doe')

      await user.click(screen.getByText('Save Person'))

      await waitFor(() => {
        expect(screen.getByText('Jane Doe')).toBeInTheDocument()
        expect(screen.queryByText('John Doe')).not.toBeInTheDocument()
      })
    })
  })

  describe('Delete Person', () => {
    it('should show delete confirmation when clicking delete', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))
      await user.type(screen.getByLabelText('Name'), 'John Doe')
      const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' })
      await user.upload(document.getElementById('new-person-file') as HTMLInputElement, file)
      await user.click(screen.getByText('Save Person'))

      const deleteButton = screen.getByText('Delete')
      await user.click(deleteButton)

      expect(screen.getByText('Delete John Doe?')).toBeInTheDocument()
      expect(screen.getByText('Confirm Delete')).toBeInTheDocument()
    })

    it('should delete person when confirmed', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))
      await user.type(screen.getByLabelText('Name'), 'John Doe')
      const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' })
      await user.upload(document.getElementById('new-person-file') as HTMLInputElement, file)
      await user.click(screen.getByText('Save Person'))

      const deleteButton = screen.getByText('Delete')
      await user.click(deleteButton)

      const confirmButton = screen.getByText('Confirm Delete')
      await user.click(confirmButton)

      await waitFor(() => {
        expect(screen.queryByText('John Doe')).not.toBeInTheDocument()
      })
    })

    it('should show deleted toast after deletion', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))
      await user.type(screen.getByLabelText('Name'), 'John Doe')
      const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' })
      await user.upload(document.getElementById('new-person-file') as HTMLInputElement, file)
      await user.click(screen.getByText('Save Person'))

      const deleteButton = screen.getByText('Delete')
      await user.click(deleteButton)

      const confirmButton = screen.getByText('Confirm Delete')
      await user.click(confirmButton)

      expect(screen.getByText('Deleted')).toBeInTheDocument()
    })

    it('should cancel deletion', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))
      await user.type(screen.getByLabelText('Name'), 'John Doe')
      const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' })
      await user.upload(document.getElementById('new-person-file') as HTMLInputElement, file)
      await user.click(screen.getByText('Save Person'))

      const deleteButton = screen.getByText('Delete')
      await user.click(deleteButton)

      const cancelButton = screen.getAllByText('Cancel').find(btn =>
        btn.textContent === 'Cancel' && btn.closest('[role="button"]')
      )
      await user.click(cancelButton!)

      expect(screen.getByText('John Doe')).toBeInTheDocument()
      expect(screen.queryByText('Delete John Doe?')).not.toBeInTheDocument()
    })
  })

  describe('Photo Management', () => {
    it('should show remove button on photo hover', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))
      await user.type(screen.getByLabelText('Name'), 'John Doe')
      const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' })
      await user.upload(document.getElementById('new-person-file') as HTMLInputElement, file)
      await user.click(screen.getByText('Save Person'))

      const personCard = screen.getByTestId('person-item')
      await user.click(personCard)

      const removeButton = screen.getByTestId('remove-photo')
      expect(removeButton).toBeInTheDocument()
    })

    it('should show photo removal confirmation', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))
      await user.type(screen.getByLabelText('Name'), 'John Doe')
      const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' })
      await user.upload(document.getElementById('new-person-file') as HTMLInputElement, file)
      await user.click(screen.getByText('Save Person'))

      const personCard = screen.getByTestId('person-item')
      await user.click(personCard)

      const removeButton = screen.getByTestId('remove-photo')
      await user.click(removeButton)

      expect(screen.getByText('Remove this photo?')).toBeInTheDocument()
      expect(screen.getByText('Confirm')).toBeInTheDocument()
    })

    it('should remove photo when confirmed', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))
      await user.type(screen.getByLabelText('Name'), 'John Doe')
      const files = [
        new File(['content1'], 'test1.jpg', { type: 'image/jpeg' }),
        new File(['content2'], 'test2.jpg', { type: 'image/jpeg' }),
      ]
      await user.upload(document.getElementById('new-person-file') as HTMLInputElement, files)
      await user.click(screen.getByText('Save Person'))

      expect(screen.getByText('2 sample photos')).toBeInTheDocument()

      const personCard = screen.getByTestId('person-item')
      await user.click(personCard)

      const removeButton = screen.getByTestId('remove-photo')
      await user.click(removeButton)

      const confirmButton = screen.getByText('Confirm')
      await user.click(confirmButton)

      await waitFor(() => {
        expect(screen.getByText('1 sample photo')).toBeInTheDocument()
      })
    })

    it('should cancel photo removal', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))
      await user.type(screen.getByLabelText('Name'), 'John Doe')
      const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' })
      await user.upload(document.getElementById('new-person-file') as HTMLInputElement, file)
      await user.click(screen.getByText('Save Person'))

      const personCard = screen.getByTestId('person-item')
      await user.click(personCard)

      const removeButton = screen.getByTestId('remove-photo')
      await user.click(removeButton)

      const cancelButtons = screen.getAllByText('Cancel')
      const photoRemovalCancel = cancelButtons.find(btn =>
        btn.closest('div')?.textContent?.includes('Remove this photo?')
      )
      await user.click(photoRemovalCancel!)

      expect(screen.queryByText('Remove this photo?')).not.toBeInTheDocument()
    })
  })

  describe('Face Search Integration', () => {
    it('should navigate to search when clicking search photos button', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))
      await user.type(screen.getByLabelText('Name'), 'John Doe')
      const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' })
      await user.upload(document.getElementById('new-person-file') as HTMLInputElement, file)
      await user.click(screen.getByText('Save Person'))

      const searchButton = screen.getByText('Search Photos of this Person')
      await user.click(searchButton)

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalled()
      })
    })

    it('should disable search button when face search is disabled', async () => {
      jest.mocked(apiService.getConfig).mockResolvedValue({
        roots: [],
        ocr_languages: [],
        face_search_enabled: false,
        index_version: '1.0.0',
      })

      const user = userEvent.setup({ delay: null })
      renderComponent()

      // Wait for config to load
      await waitFor(() => {
        expect(apiService.getConfig).toHaveBeenCalled()
      })

      jest.advanceTimersByTime(1000)

      await user.click(screen.getByText('➕ Add Person'))
      await user.type(screen.getByLabelText('Name'), 'John Doe')
      const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' })
      await user.upload(document.getElementById('new-person-file') as HTMLInputElement, file)
      await user.click(screen.getByText('Save Person'))

      const searchButton = screen.getByText('Search Photos of this Person')
      expect(searchButton).toBeDisabled()
    })

    it('should poll config status periodically', async () => {
      renderComponent()

      expect(apiService.getConfig).toHaveBeenCalledTimes(1)

      jest.advanceTimersByTime(1000)
      await waitFor(() => {
        expect(apiService.getConfig).toHaveBeenCalledTimes(2)
      })

      jest.advanceTimersByTime(1000)
      await waitFor(() => {
        expect(apiService.getConfig).toHaveBeenCalledTimes(3)
      })
    })

    it('should handle config polling errors silently', async () => {
      jest.mocked(apiService.getConfig).mockRejectedValue(new Error('Config error'))

      renderComponent()

      await waitFor(() => {
        expect(apiService.getConfig).toHaveBeenCalled()
      })

      // Should not throw or show error
      expect(screen.getByText('People')).toBeInTheDocument()
    })
  })

  describe('Edge Cases', () => {
    it('should handle empty file list gracefully', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))

      const input = document.getElementById('new-person-file') as HTMLInputElement
      fireEvent.change(input, { target: { files: null } })

      // Should not crash
      expect(screen.getByText('Add Person')).toBeInTheDocument()
    })

    it('should trim whitespace from person name', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))
      await user.type(screen.getByLabelText('Name'), '  John Doe  ')
      const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' })
      await user.upload(document.getElementById('new-person-file') as HTMLInputElement, file)
      await user.click(screen.getByText('Save Person'))

      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    it('should prevent saving with whitespace-only name', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))
      await user.type(screen.getByLabelText('Name'), '   ')
      const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' })
      await user.upload(document.getElementById('new-person-file') as HTMLInputElement, file)
      await user.click(screen.getByText('Save Person'))

      expect(screen.getByText('Person name cannot be empty')).toBeInTheDocument()
    })

    it('should handle clicking save person button multiple times', async () => {
      const user = userEvent.setup({ delay: null })
      renderComponent()

      await user.click(screen.getByText('➕ Add Person'))
      await user.type(screen.getByLabelText('Name'), 'John Doe')
      const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' })
      await user.upload(document.getElementById('new-person-file') as HTMLInputElement, file)

      const saveButton = screen.getByText('Save Person')
      await user.click(saveButton)
      await user.click(saveButton)

      // Should only create one person
      const peopleList = screen.getByTestId('people-list')
      const personCards = peopleList.querySelectorAll('[data-testid="person-item"]')
      expect(personCards).toHaveLength(1)
    })
  })
})
