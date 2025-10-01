/**
 * Unit tests for Settings Page
 * Priority: P2 (Page-level functionality)
 */

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import SettingsPage from '../../src/pages/SettingsPage'
import { apiService } from '../../src/services/apiClient'

// Mock API service
jest.mock('../../src/services/apiClient', () => ({
  apiService: {
    getConfig: jest.fn(),
    updateConfig: jest.fn(),
    updateRoots: jest.fn(),
    startIndexing: jest.fn(),
    getIndexStatus: jest.fn(),
    getDependencies: jest.fn(),
    installDependencies: jest.fn()
  }
}))

const mockConfig = {
  roots: ['/photos', '/documents'],
  ocr_languages: ['eng', 'fra'],
  face_search_enabled: true,
  semantic_search_enabled: false,
  batch_size: 32,
  thumbnail_size: '256',
  index_version: '1.0.0'
}

const mockDependencies = {
  core: [
    {
      name: 'sqlite',
      installed: true,
      version: '3.40.0',
      required: true,
      description: 'Database engine'
    }
  ],
  ml: [
    {
      name: 'face_recognition',
      installed: false,
      version: null,
      required: false,
      description: 'Face detection and recognition'
    }
  ],
  features: {
    face_detection: false,
    ocr: true,
    semantic_search: false
  }
}

describe('Settings Page', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    ;(apiService.getConfig as jest.Mock).mockResolvedValue(mockConfig)
    ;(apiService.getDependencies as jest.Mock).mockResolvedValue(mockDependencies)
    ;(apiService.getIndexStatus as jest.Mock).mockResolvedValue({
      status: 'idle',
      progress: { total_files: 0, processed_files: 0, current_phase: 'idle' },
      errors: []
    })
  })

  const renderSettingsPage = () => {
    return render(
      <MemoryRouter>
        <SettingsPage />
      </MemoryRouter>
    )
  }

  test('renders settings page with sections', async () => {
    renderSettingsPage()

    expect(screen.getByText(/Settings/i)).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText(/Index Paths/i)).toBeInTheDocument()
      expect(screen.getByText(/ML Features/i)).toBeInTheDocument()
      expect(screen.getByText(/Index Management/i)).toBeInTheDocument()
    })
  })

  test('loads and displays configuration', async () => {
    renderSettingsPage()

    await waitFor(() => {
      expect(apiService.getConfig).toHaveBeenCalled()
    })

    await waitFor(() => {
      expect(screen.getByText('/photos')).toBeInTheDocument()
      expect(screen.getByText('/documents')).toBeInTheDocument()
    })
  })

  test('adds new index path', async () => {
    const user = userEvent.setup()
    ;(apiService.updateRoots as jest.Mock).mockResolvedValue({})

    renderSettingsPage()

    await waitFor(() => {
      expect(screen.getByText('/photos')).toBeInTheDocument()
    })

    const addButton = screen.getByText(/Add Path/i)
    await user.click(addButton)

    const input = screen.getByPlaceholderText(/Enter path/i)
    await user.type(input, '/new/path')

    const saveButton = screen.getByText(/Save/i)
    await user.click(saveButton)

    await waitFor(() => {
      expect(apiService.updateRoots).toHaveBeenCalledWith([
        '/photos',
        '/documents',
        '/new/path'
      ])
    })
  })

  test('removes index path', async () => {
    const user = userEvent.setup()
    ;(apiService.updateRoots as jest.Mock).mockResolvedValue({})

    renderSettingsPage()

    await waitFor(() => {
      expect(screen.getByText('/photos')).toBeInTheDocument()
    })

    const removeButtons = screen.getAllByText(/Remove/i)
    await user.click(removeButtons[0])

    await waitFor(() => {
      expect(apiService.updateRoots).toHaveBeenCalledWith(['/documents'])
    })
  })

  test('toggles face search feature', async () => {
    const user = userEvent.setup()
    ;(apiService.updateConfig as jest.Mock).mockResolvedValue({})

    renderSettingsPage()

    await waitFor(() => {
      expect(screen.getByLabelText(/Face Search/i)).toBeInTheDocument()
    })

    const toggle = screen.getByLabelText(/Face Search/i)
    await user.click(toggle)

    await waitFor(() => {
      expect(apiService.updateConfig).toHaveBeenCalledWith({
        face_search_enabled: false
      })
    })
  })

  test('toggles semantic search feature', async () => {
    const user = userEvent.setup()
    ;(apiService.updateConfig as jest.Mock).mockResolvedValue({})

    renderSettingsPage()

    await waitFor(() => {
      expect(screen.getByLabelText(/Semantic Search/i)).toBeInTheDocument()
    })

    const toggle = screen.getByLabelText(/Semantic Search/i)
    await user.click(toggle)

    await waitFor(() => {
      expect(apiService.updateConfig).toHaveBeenCalledWith({
        semantic_search_enabled: true
      })
    })
  })

  test('updates thumbnail size', async () => {
    const user = userEvent.setup()
    ;(apiService.updateConfig as jest.Mock).mockResolvedValue({})

    renderSettingsPage()

    await waitFor(() => {
      expect(screen.getByLabelText(/Thumbnail Size/i)).toBeInTheDocument()
    })

    const select = screen.getByLabelText(/Thumbnail Size/i)
    await user.selectOptions(select, '512')

    await waitFor(() => {
      expect(apiService.updateConfig).toHaveBeenCalledWith({
        thumbnail_size: '512'
      })
    })
  })

  test('updates batch size', async () => {
    const user = userEvent.setup()
    ;(apiService.updateConfig as jest.Mock).mockResolvedValue({})

    renderSettingsPage()

    await waitFor(() => {
      expect(screen.getByLabelText(/Batch Size/i)).toBeInTheDocument()
    })

    const input = screen.getByLabelText(/Batch Size/i)
    await user.clear(input)
    await user.type(input, '64')

    const saveButton = screen.getByText(/Save/i)
    await user.click(saveButton)

    await waitFor(() => {
      expect(apiService.updateConfig).toHaveBeenCalledWith({
        batch_size: 64
      })
    })
  })

  test('starts full indexing', async () => {
    const user = userEvent.setup()
    ;(apiService.startIndexing as jest.Mock).mockResolvedValue({ status: 'started' })

    renderSettingsPage()

    await waitFor(() => {
      expect(screen.getByText(/Start Full Index/i)).toBeInTheDocument()
    })

    const button = screen.getByText(/Start Full Index/i)
    await user.click(button)

    await waitFor(() => {
      expect(apiService.startIndexing).toHaveBeenCalledWith(true)
    })
  })

  test('starts incremental indexing', async () => {
    const user = userEvent.setup()
    ;(apiService.startIndexing as jest.Mock).mockResolvedValue({ status: 'started' })

    renderSettingsPage()

    await waitFor(() => {
      expect(screen.getByText(/Update Index/i)).toBeInTheDocument()
    })

    const button = screen.getByText(/Update Index/i)
    await user.click(button)

    await waitFor(() => {
      expect(apiService.startIndexing).toHaveBeenCalledWith(false)
    })
  })

  test('shows indexing progress', async () => {
    ;(apiService.getIndexStatus as jest.Mock).mockResolvedValue({
      status: 'running',
      progress: {
        total_files: 1000,
        processed_files: 500,
        current_phase: 'processing'
      },
      errors: []
    })

    renderSettingsPage()

    await waitFor(() => {
      expect(screen.getByText(/50%/)).toBeInTheDocument()
      expect(screen.getByText(/500 \/ 1000/)).toBeInTheDocument()
    })
  })

  test('displays dependency status', async () => {
    renderSettingsPage()

    await waitFor(() => {
      expect(apiService.getDependencies).toHaveBeenCalled()
    })

    await waitFor(() => {
      expect(screen.getByText('sqlite')).toBeInTheDocument()
      expect(screen.getByText('face_recognition')).toBeInTheDocument()
      expect(screen.getByText(/Installed/i)).toBeInTheDocument()
      expect(screen.getByText(/Not installed/i)).toBeInTheDocument()
    })
  })

  test('installs ML dependencies', async () => {
    const user = userEvent.setup()
    ;(apiService.installDependencies as jest.Mock).mockResolvedValue({
      status: 'installing'
    })

    renderSettingsPage()

    await waitFor(() => {
      expect(screen.getByText('face_recognition')).toBeInTheDocument()
    })

    const installButton = screen.getByText(/Install/i)
    await user.click(installButton)

    await waitFor(() => {
      expect(apiService.installDependencies).toHaveBeenCalledWith(['face_recognition'])
    })
  })

  test('handles configuration load error', async () => {
    ;(apiService.getConfig as jest.Mock).mockRejectedValue(
      new Error('Failed to load config')
    )

    renderSettingsPage()

    await waitFor(() => {
      expect(screen.getByText(/Error loading settings/i)).toBeInTheDocument()
    })
  })

  test('handles save error', async () => {
    const user = userEvent.setup()
    ;(apiService.updateConfig as jest.Mock).mockRejectedValue(
      new Error('Failed to save')
    )

    renderSettingsPage()

    await waitFor(() => {
      expect(screen.getByLabelText(/Face Search/i)).toBeInTheDocument()
    })

    const toggle = screen.getByLabelText(/Face Search/i)
    await user.click(toggle)

    await waitFor(() => {
      expect(screen.getByText(/Failed to save settings/i)).toBeInTheDocument()
    })
  })
})