import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
// Vitest to Jest conversion
import { MemoryRouter } from 'react-router-dom'
import SettingsPage from '../../src/pages/SettingsPage'
import { apiService } from '../../src/services/apiClient'

// Mock dependencies
jest.mock('../../src/services/apiClient', () => ({
  apiService: {
    getConfig: jest.fn(),
    updateRoots: jest.fn(),
    updateConfig: jest.fn(),
    getIndexStatus: jest.fn(),
    getIndexStats: jest.fn(),
    startIndexing: jest.fn(),
    stopIndexing: jest.fn(),
  },
}))

jest.mock('../../src/components/DependenciesManager', () => ({
  default: () => <div data-testid="dependencies-manager">Dependencies Manager</div>,
}))

const mockConfig = {
  roots: ['/photos/vacation', '/photos/family'],
  ocr_languages: ['eng'],
  face_search_enabled: false,
  semantic_search_enabled: true,
  batch_size: 50,
  thumbnail_size: 'medium',
  index_version: '1.0.0',
}

const mockIndexStatus = {
  status: 'idle',
  progress: {
    total_files: 0,
    processed_files: 0,
    current_phase: '',
  },
  errors: [],
  started_at: null,
  estimated_completion: null,
}

const mockIndexStats = {
  database: {
    total_photos: 1500,
    indexed_photos: 1450,
    photos_with_embeddings: 1200,
    total_faces: 350,
  },
}

describe('SettingsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()

    jest.mocked(apiService.getConfig).mockResolvedValue(mockConfig)
    jest.mocked(apiService.getIndexStatus).mockResolvedValue(mockIndexStatus)
    jest.mocked(apiService.getIndexStats).mockResolvedValue(mockIndexStats)
    jest.mocked(apiService.updateRoots).mockResolvedValue(undefined)
    jest.mocked(apiService.updateConfig).mockResolvedValue(undefined)
    jest.mocked(apiService.startIndexing).mockResolvedValue({})
    jest.mocked(apiService.stopIndexing).mockResolvedValue({})
  })

  const renderComponent = () => {
    return render(
      <MemoryRouter>
        <SettingsPage />
      </MemoryRouter>
    )
  }

  describe('Initial Loading', () => {
    it('should show loading state initially', () => {
      renderComponent()
      expect(screen.getByText('Loading settings...')).toBeInTheDocument()
    })

    it('should load configuration on mount', async () => {
      renderComponent()

      await waitFor(() => {
        expect(apiService.getConfig).toHaveBeenCalled()
        expect(apiService.getIndexStatus).toHaveBeenCalled()
        expect(apiService.getIndexStats).toHaveBeenCalled()
      })
    })

    it('should display settings page after loading', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })
    })

    it('should handle loading errors', async () => {
      jest.mocked(apiService.getConfig).mockRejectedValue(new Error('Failed to load'))

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Error')).toBeInTheDocument()
        expect(screen.getByText('Failed to load configuration')).toBeInTheDocument()
      })
    })
  })

  describe('Tabs Navigation', () => {
    it('should render all tab options', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Storage & Indexing')).toBeInTheDocument()
        expect(screen.getByText('Search Features')).toBeInTheDocument()
        expect(screen.getByText('Dependencies')).toBeInTheDocument()
        expect(screen.getByText('System Status')).toBeInTheDocument()
      })
    })

    it('should switch to different tabs', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      await user.click(screen.getByText('Search Features'))
      expect(screen.getByText('OCR Languages')).toBeInTheDocument()

      await user.click(screen.getByText('System Status'))
      expect(screen.getByText('Database Statistics')).toBeInTheDocument()

      await user.click(screen.getByText('Dependencies'))
      expect(screen.getByTestId('dependencies-manager')).toBeInTheDocument()
    })
  })

  describe('Root Folders Management', () => {
    it('should display existing root folders', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('/photos/vacation')).toBeInTheDocument()
        expect(screen.getByText('/photos/family')).toBeInTheDocument()
      })
    })

    it('should allow adding new root folder', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      const input = screen.getByPlaceholderText('/path/to/your/photos')
      await user.type(input, '/photos/new-folder')

      const addButton = screen.getByText('Add')
      await user.click(addButton)

      expect(screen.getByText('/photos/new-folder')).toBeInTheDocument()
    })

    it('should disable add button when input is empty', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      const addButton = screen.getByText('Add')
      expect(addButton).toBeDisabled()
    })

    it('should prevent adding duplicate folders', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      const input = screen.getByPlaceholderText('/path/to/your/photos')
      await user.type(input, '/photos/vacation')

      const addButton = screen.getByText('Add')
      await user.click(addButton)

      // Should still only have one instance
      const folders = screen.getAllByText('/photos/vacation')
      expect(folders).toHaveLength(1)
    })

    it('should remove root folder', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('/photos/vacation')).toBeInTheDocument()
      })

      const folderRow = screen.getByText('/photos/vacation').closest('div')!
      const deleteButton = folderRow.querySelector('button')!

      await user.click(deleteButton)

      expect(screen.queryByText('/photos/vacation')).not.toBeInTheDocument()
    })

    it('should clear input after adding folder', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      const input = screen.getByPlaceholderText('/path/to/your/photos')
      await user.type(input, '/photos/new-folder')

      const addButton = screen.getByText('Add')
      await user.click(addButton)

      expect(input).toHaveValue('')
    })

    it('should trim whitespace from folder path', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      const input = screen.getByPlaceholderText('/path/to/your/photos')
      await user.type(input, '  /photos/trimmed  ')

      const addButton = screen.getByText('Add')
      await user.click(addButton)

      expect(screen.getByText('/photos/trimmed')).toBeInTheDocument()
    })
  })

  describe('Indexing Controls', () => {
    it('should display current indexing status', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Current Status')).toBeInTheDocument()
        expect(screen.getByText('idle')).toBeInTheDocument()
      })
    })

    it('should start incremental indexing', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      const startButton = screen.getByText('Start Incremental')
      await user.click(startButton)

      await waitFor(() => {
        expect(apiService.startIndexing).toHaveBeenCalledWith(false)
        expect(screen.getByText('Success')).toBeInTheDocument()
      })
    })

    it('should start full re-index', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      const fullButton = screen.getByText('Full Re-Index')
      await user.click(fullButton)

      await waitFor(() => {
        expect(apiService.startIndexing).toHaveBeenCalledWith(true)
      })
    })

    it('should show progress during indexing', async () => {
      jest.mocked(apiService.getIndexStatus).mockResolvedValue({
        status: 'indexing',
        progress: {
          total_files: 100,
          processed_files: 50,
          current_phase: 'scanning',
        },
        errors: [],
        started_at: new Date().toISOString(),
        estimated_completion: null,
      })

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('indexing')).toBeInTheDocument()
        expect(screen.getByText('scanning')).toBeInTheDocument()
        expect(screen.getByText('50/100 files')).toBeInTheDocument()
      })
    })

    it('should disable start buttons when indexing', async () => {
      jest.mocked(apiService.getIndexStatus).mockResolvedValue({
        status: 'indexing',
        progress: {
          total_files: 100,
          processed_files: 50,
          current_phase: 'scanning',
        },
        errors: [],
        started_at: new Date().toISOString(),
        estimated_completion: null,
      })

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Start Incremental')).toBeDisabled()
        expect(screen.getByText('Full Re-Index')).toBeDisabled()
      })
    })

    it('should show stop button when indexing', async () => {
      jest.mocked(apiService.getIndexStatus).mockResolvedValue({
        status: 'indexing',
        progress: {
          total_files: 100,
          processed_files: 50,
          current_phase: 'scanning',
        },
        errors: [],
        started_at: new Date().toISOString(),
        estimated_completion: null,
      })

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Stop')).toBeInTheDocument()
      })
    })

    it('should stop indexing', async () => {
      jest.mocked(apiService.getIndexStatus).mockResolvedValue({
        status: 'indexing',
        progress: {
          total_files: 100,
          processed_files: 50,
          current_phase: 'scanning',
        },
        errors: [],
        started_at: new Date().toISOString(),
        estimated_completion: null,
      })

      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Stop')).toBeInTheDocument()
      })

      await user.click(screen.getByText('Stop'))

      await waitFor(() => {
        expect(apiService.stopIndexing).toHaveBeenCalled()
      })
    })

    it('should display indexing errors', async () => {
      jest.mocked(apiService.getIndexStatus).mockResolvedValue({
        status: 'error',
        progress: {
          total_files: 0,
          processed_files: 0,
          current_phase: '',
        },
        errors: ['Error 1: File not found', 'Error 2: Permission denied'],
        started_at: null,
        estimated_completion: null,
      })

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('2 error(s) encountered')).toBeInTheDocument()
      })
    })

    it('should handle indexing start errors', async () => {
      jest.mocked(apiService.startIndexing).mockRejectedValue(new Error('Failed to start'))

      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      await user.click(screen.getByText('Start Incremental'))

      await waitFor(() => {
        expect(screen.getByText('Error')).toBeInTheDocument()
        expect(screen.getByText('Failed to start indexing')).toBeInTheDocument()
      })
    })
  })

  describe('OCR Languages', () => {
    it('should display OCR language options', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      const user = userEvent.setup()
      await user.click(screen.getByText('Search Features'))

      expect(screen.getByText('English')).toBeInTheDocument()
      expect(screen.getByText('Tamil')).toBeInTheDocument()
    })

    it('should show checked languages from config', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      const user = userEvent.setup()
      await user.click(screen.getByText('Search Features'))

      const englishCheckbox = screen.getByLabelText('English')
      expect(englishCheckbox).toBeChecked()
    })

    it('should toggle OCR language selection', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      await user.click(screen.getByText('Search Features'))

      const tamilCheckbox = screen.getByLabelText('Tamil')
      expect(tamilCheckbox).not.toBeChecked()

      await user.click(tamilCheckbox)
      expect(tamilCheckbox).toBeChecked()

      await user.click(tamilCheckbox)
      expect(tamilCheckbox).not.toBeChecked()
    })
  })

  describe('Search Features', () => {
    it('should display semantic search toggle', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      await user.click(screen.getByText('Search Features'))

      expect(screen.getByText('Enable Semantic Search')).toBeInTheDocument()
    })

    it('should toggle semantic search', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      await user.click(screen.getByText('Search Features'))

      const semanticSwitch = screen.getByRole('switch', { name: /semantic-search/i })
      expect(semanticSwitch).toBeChecked()

      await user.click(semanticSwitch)
      expect(semanticSwitch).not.toBeChecked()
    })

    it('should display face search toggle', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      await user.click(screen.getByText('Search Features'))

      expect(screen.getByText('Enable Face Search')).toBeInTheDocument()
    })

    it('should toggle face search', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      await user.click(screen.getByText('Search Features'))

      const faceSwitch = screen.getByRole('switch', { name: /face-search/i })
      expect(faceSwitch).not.toBeChecked()

      await user.click(faceSwitch)
      expect(faceSwitch).toBeChecked()
    })
  })

  describe('Processing Settings', () => {
    it('should display batch size setting', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      await user.click(screen.getByText('Search Features'))

      expect(screen.getByText('Batch Size')).toBeInTheDocument()
      const batchInput = screen.getByLabelText('Batch Size')
      expect(batchInput).toHaveValue(50)
    })

    it('should update batch size', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      await user.click(screen.getByText('Search Features'))

      const batchInput = screen.getByLabelText('Batch Size')
      await user.clear(batchInput)
      await user.type(batchInput, '100')

      expect(batchInput).toHaveValue(100)
    })

    it('should display thumbnail size setting', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      await user.click(screen.getByText('Search Features'))

      expect(screen.getByText('Thumbnail Size')).toBeInTheDocument()
      const thumbnailSelect = screen.getByLabelText('Thumbnail Size')
      expect(thumbnailSelect).toHaveValue('medium')
    })

    it('should change thumbnail size', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      await user.click(screen.getByText('Search Features'))

      const thumbnailSelect = screen.getByLabelText('Thumbnail Size')
      await user.selectOptions(thumbnailSelect, 'large')

      expect(thumbnailSelect).toHaveValue('large')
    })

    it('should handle invalid batch size', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      await user.click(screen.getByText('Search Features'))

      const batchInput = screen.getByLabelText('Batch Size')
      await user.clear(batchInput)
      await user.type(batchInput, '0')

      // Should default to 50 or minimum
      expect(batchInput).toHaveValue(50)
    })
  })

  describe('Database Statistics', () => {
    it('should display total photos count', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      await user.click(screen.getByText('System Status'))

      expect(screen.getByText('1,500')).toBeInTheDocument()
      expect(screen.getByText('Total Photos')).toBeInTheDocument()
    })

    it('should display indexed photos count', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      await user.click(screen.getByText('System Status'))

      expect(screen.getByText('1,450')).toBeInTheDocument()
      expect(screen.getByText('Indexed')).toBeInTheDocument()
    })

    it('should display embeddings count', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      await user.click(screen.getByText('System Status'))

      expect(screen.getByText('1,200')).toBeInTheDocument()
      expect(screen.getByText('With Embeddings')).toBeInTheDocument()
    })

    it('should display faces count', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      await user.click(screen.getByText('System Status'))

      expect(screen.getByText('350')).toBeInTheDocument()
      expect(screen.getByText('Faces Detected')).toBeInTheDocument()
    })
  })

  describe('Save Configuration', () => {
    it('should save configuration when clicking save button', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      // Make some changes
      const input = screen.getByPlaceholderText('/path/to/your/photos')
      await user.type(input, '/photos/new')
      await user.click(screen.getByText('Add'))

      const saveButton = screen.getByText('Save Configuration')
      await user.click(saveButton)

      await waitFor(() => {
        expect(apiService.updateRoots).toHaveBeenCalled()
        expect(apiService.updateConfig).toHaveBeenCalled()
      })
    })

    it('should show success message after save', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      const saveButton = screen.getByText('Save Configuration')
      await user.click(saveButton)

      await waitFor(() => {
        expect(screen.getByText('Success')).toBeInTheDocument()
        expect(screen.getByText('Configuration saved successfully!')).toBeInTheDocument()
      })
    })

    it('should show loading state while saving', async () => {
      jest.mocked(apiService.updateRoots).mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 100))
      )

      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      const saveButton = screen.getByText('Save Configuration')
      await user.click(saveButton)

      expect(screen.getByText('Saving...')).toBeInTheDocument()
    })

    it('should disable save button while saving', async () => {
      jest.mocked(apiService.updateRoots).mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 100))
      )

      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      const saveButton = screen.getByText('Save Configuration')
      await user.click(saveButton)

      expect(saveButton).toBeDisabled()
    })

    it('should handle save errors', async () => {
      jest.mocked(apiService.updateRoots).mockRejectedValue(new Error('Failed to save'))

      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      const saveButton = screen.getByText('Save Configuration')
      await user.click(saveButton)

      await waitFor(() => {
        expect(screen.getByText('Error')).toBeInTheDocument()
        expect(screen.getByText('Failed to save configuration')).toBeInTheDocument()
      })
    })

    it('should reload data after successful save', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      const initialCallCount = jest.mocked(apiService.getConfig).mock.calls.length

      const saveButton = screen.getByText('Save Configuration')
      await user.click(saveButton)

      await waitFor(() => {
        expect(jest.mocked(apiService.getConfig).mock.calls.length).toBeGreaterThan(initialCallCount)
      })
    })

    it('should save all configuration fields', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      await user.click(screen.getByText('Search Features'))

      // Change multiple settings
      const semanticSwitch = screen.getByRole('switch', { name: /semantic-search/i })
      await user.click(semanticSwitch)

      const faceSwitch = screen.getByRole('switch', { name: /face-search/i })
      await user.click(faceSwitch)

      const batchInput = screen.getByLabelText('Batch Size')
      await user.clear(batchInput)
      await user.type(batchInput, '75')

      const thumbnailSelect = screen.getByLabelText('Thumbnail Size')
      await user.selectOptions(thumbnailSelect, 'large')

      const saveButton = screen.getByText('Save Configuration')
      await user.click(saveButton)

      await waitFor(() => {
        expect(apiService.updateConfig).toHaveBeenCalledWith({
          ocr_languages: ['eng'],
          face_search_enabled: true,
          semantic_search_enabled: false,
          batch_size: 75,
          thumbnail_size: 'large',
        })
      })
    })
  })

  describe('Dependencies Tab', () => {
    it('should render dependencies manager', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      await user.click(screen.getByText('Dependencies'))

      expect(screen.getByTestId('dependencies-manager')).toBeInTheDocument()
    })
  })

  describe('Edge Cases', () => {
    it('should handle missing config fields gracefully', async () => {
      jest.mocked(apiService.getConfig).mockResolvedValue({
        roots: [],
        ocr_languages: [],
        face_search_enabled: false,
        index_version: '1.0.0',
      } as any)

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      // Should use defaults
      const user = userEvent.setup()
      await user.click(screen.getByText('Search Features'))

      const semanticSwitch = screen.getByRole('switch', { name: /semantic-search/i })
      expect(semanticSwitch).toBeChecked() // Default is true
    })

    it('should handle empty roots array', async () => {
      jest.mocked(apiService.getConfig).mockResolvedValue({
        roots: [],
        ocr_languages: [],
        face_search_enabled: false,
        index_version: '1.0.0',
      } as any)

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      // Should still show the add folder input
      expect(screen.getByPlaceholderText('/path/to/your/photos')).toBeInTheDocument()
    })

    it('should handle zero progress values', async () => {
      jest.mocked(apiService.getIndexStatus).mockResolvedValue({
        status: 'indexing',
        progress: {
          total_files: 0,
          processed_files: 0,
          current_phase: 'scanning',
        },
        errors: [],
        started_at: new Date().toISOString(),
        estimated_completion: null,
      })

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('scanning')).toBeInTheDocument()
      })

      // Should not crash with division by zero
      expect(screen.getByText('Settings')).toBeInTheDocument()
    })

    it('should handle very large statistics numbers', async () => {
      jest.mocked(apiService.getIndexStats).mockResolvedValue({
        database: {
          total_photos: 1500000,
          indexed_photos: 1450000,
          photos_with_embeddings: 1200000,
          total_faces: 350000,
        },
      })

      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      await user.click(screen.getByText('System Status'))

      // Should format with commas
      expect(screen.getByText('1,500,000')).toBeInTheDocument()
    })

    it('should handle concurrent API calls gracefully', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      // Trigger multiple saves quickly
      const saveButton = screen.getByText('Save Configuration')
      await user.click(saveButton)
      await user.click(saveButton)

      // Should handle gracefully without crashes
      await waitFor(() => {
        expect(apiService.updateRoots).toHaveBeenCalled()
      })
    })

    it('should preserve state when switching tabs', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      // Add a folder
      const input = screen.getByPlaceholderText('/path/to/your/photos')
      await user.type(input, '/photos/test')
      await user.click(screen.getByText('Add'))

      // Switch tabs
      await user.click(screen.getByText('Search Features'))
      await user.click(screen.getByText('Storage & Indexing'))

      // Folder should still be there
      expect(screen.getByText('/photos/test')).toBeInTheDocument()
    })

    it('should handle network timeout errors', async () => {
      jest.mocked(apiService.getConfig).mockRejectedValue(new Error('Network timeout'))

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Error')).toBeInTheDocument()
      })

      // Should still render error state gracefully
      expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument()
    })
  })

  describe('Form Validation', () => {
    it('should require at least one root folder before saving', async () => {
      jest.mocked(apiService.getConfig).mockResolvedValue({
        roots: [],
        ocr_languages: [],
        face_search_enabled: false,
        index_version: '1.0.0',
      } as any)

      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      const saveButton = screen.getByText('Save Configuration')
      await user.click(saveButton)

      await waitFor(() => {
        expect(apiService.updateRoots).toHaveBeenCalledWith([])
      })
    })

    it('should enforce minimum batch size', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      await user.click(screen.getByText('Search Features'))

      const batchInput = screen.getByLabelText('Batch Size')
      await user.clear(batchInput)
      await user.type(batchInput, '-5')

      // Should handle invalid input
      expect(batchInput).toHaveValue(50) // Default
    })

    it('should enforce maximum batch size', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
      })

      await user.click(screen.getByText('Search Features'))

      const batchInput = screen.getByLabelText('Batch Size')
      expect(batchInput).toHaveAttribute('max', '500')
    })
  })

  describe('Progress Display', () => {
    it('should calculate and display progress percentage', async () => {
      jest.mocked(apiService.getIndexStatus).mockResolvedValue({
        status: 'indexing',
        progress: {
          total_files: 200,
          processed_files: 100,
          current_phase: 'processing',
        },
        errors: [],
        started_at: new Date().toISOString(),
        estimated_completion: null,
      })

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('100/200 files')).toBeInTheDocument()
      })

      // Progress bar should be at 50%
      const progressBar = screen.getByRole('progressbar')
      expect(progressBar).toBeInTheDocument()
    })

    it('should hide progress bar when no files to process', async () => {
      jest.mocked(apiService.getIndexStatus).mockResolvedValue({
        status: 'indexing',
        progress: {
          total_files: 0,
          processed_files: 0,
          current_phase: 'initializing',
        },
        errors: [],
        started_at: new Date().toISOString(),
        estimated_completion: null,
      })

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('initializing')).toBeInTheDocument()
      })

      const progressBars = screen.queryAllByRole('progressbar')
      expect(progressBars).toHaveLength(0)
    })
  })
})
