import { render, screen, waitFor, act, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import SettingsPage from '../../src/pages/SettingsPage'
jest.setTimeout(30000)

// Mock toast and Toaster dependency shape to avoid UI internals
// Create stable mock inside factory to prevent infinite loops from unstable references
jest.mock('../../src/components/ui/use-toast', () => {
  const mockToastFn = jest.fn()
  const stableReturn = { toast: mockToastFn, toasts: [] }
  return {
    useToast: () => stableReturn,
    __mockToast: mockToastFn, // Export for test assertions
  }
})

// Mock Toaster component to avoid Radix portal internals in tests
jest.mock('../../src/components/ui/toaster', () => ({
  Toaster: () => null,
}))

jest.mock('../../src/stores/onboardingStore', () => ({
  useOnboardingStore: () => ({ reset: jest.fn() }),
}))

// Mock apiService
jest.mock('../../src/services/apiClient', () => ({
  apiService: {
    getConfig: jest.fn(),
    getIndexStatus: jest.fn(),
    getDependencies: jest.fn(),
    updateRoots: jest.fn(),
    updateConfig: jest.fn(),
    startIndexing: jest.fn(),
    stopIndexing: jest.fn(),
  },
}))

// Mock electronAPI
;(window as any).electronAPI = {
  selectDirectory: jest.fn().mockResolvedValue({ canceled: false, filePaths: ['/photos'] }),
}

describe('SettingsPage', () => {
  const { apiService } = require('../../src/services/apiClient')
  const { __mockToast: actualMockToast } = require('../../src/components/ui/use-toast')

  beforeEach(() => {
    jest.clearAllMocks()
    jest.mocked(apiService.getConfig).mockResolvedValue({
      roots: [],
      ocr_enabled: false,
      ocr_languages: [],
      face_search_enabled: false,
      semantic_search_enabled: true,
    })
    jest.mocked(apiService.getIndexStatus).mockResolvedValue({
      status: 'idle',
      queued: 0,
      processed: 0,
      total: 0,
    })
    jest.mocked(apiService.getDependencies).mockResolvedValue({
      core: [],
      ml: [],
      features: { text_recognition: true },
    })
  })

  const renderPage = () =>
    render(
      <MemoryRouter>
        <SettingsPage />
      </MemoryRouter>
    )

  const flushPromises = async () => {
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })
  }

  const waitDebounce = async () => {
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 1100))
    })
  }

  test('loads initial data and shows settings UI', async () => {
    renderPage()

    expect(screen.getByText('Loading settings...')).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument()
    }, { timeout: 7000 })
    expect(screen.getByText('Settings')).toBeInTheDocument()

    expect(apiService.getConfig).toHaveBeenCalled()
    expect(apiService.getIndexStatus).toHaveBeenCalled()
    expect(apiService.getDependencies).toHaveBeenCalled()
  })

  test('adds a root folder via electronAPI and debounces save', async () => {
    renderPage()
    await flushPromises()
    await waitFor(() => {
      expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument()
    })

    const addButton = await screen.findByRole('button', { name: 'Add' }, { timeout: 10000 })

    await userEvent.click(addButton)
    await waitDebounce()

    await waitFor(() => {
      expect(apiService.updateRoots).toHaveBeenCalled()
    })
  }, 20000)

  test('toggles feature switches and triggers debounced saves', async () => {
    renderPage()
    await flushPromises()
    await waitFor(() => {
      expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument()
    })

    await screen.findByRole('button', { name: 'Add' }, { timeout: 10000 })

    // OCR toggle should exist (available in features)
    const ocrSwitch = screen.getByLabelText('Text Recognition')
    await userEvent.click(ocrSwitch)
    await waitDebounce()
    expect(apiService.updateConfig).toHaveBeenCalledWith({ 
      ocr_enabled: true,
      ocr_languages: [] 
    })

    // Semantic Search toggle
    const semanticSwitch = screen.getByLabelText('Smart Search')
    await userEvent.click(semanticSwitch)
    await waitDebounce()
    expect(apiService.updateConfig).toHaveBeenCalledWith({ semantic_search_enabled: false })

    // Face Search toggle
    const faceSwitch = screen.getByLabelText('People Search')
    await userEvent.click(faceSwitch)
    await waitDebounce()
    expect(apiService.updateConfig).toHaveBeenCalledWith({ face_search_enabled: true })
  }, 20000)

  test('selects OCR languages when OCR enabled', async () => {
    renderPage()
    await flushPromises()
    await waitFor(() => {
      expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument()
    })

    await screen.findByRole('button', { name: 'Add' }, { timeout: 10000 })

    // Enable OCR first
    await userEvent.click(screen.getByLabelText('Text Recognition'))
    await waitDebounce()

    // Select English and Tamil
    await userEvent.click(screen.getByLabelText('English'))
    await userEvent.click(screen.getByLabelText('Tamil'))
    await waitDebounce()
    expect(apiService.updateConfig).toHaveBeenCalledWith({ ocr_languages: ['eng', 'tam'] })
  }, 20000)

  test('start indexing and full refresh trigger API calls', async () => {
    renderPage()
    await flushPromises()
    await waitFor(() => {
      expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument()
    })

    await screen.findByRole('button', { name: 'Add' }, { timeout: 10000 })

    await userEvent.click(screen.getByText('Quick Update'))
    await flushPromises()
    expect(apiService.startIndexing).toHaveBeenCalledWith(false)

    await userEvent.click(screen.getByText('Full Refresh'))
    await flushPromises()
    expect(apiService.startIndexing).toHaveBeenCalledWith(true)
  }, 20000)

  test('stop indexing is shown when status is indexing and calls API', async () => {
    jest.mocked(apiService.getIndexStatus).mockResolvedValueOnce({
      status: 'indexing',
      progress: { current_phase: 'metadata', processed_files: 0, total_files: 0 },
    } as any)

    renderPage()
    await flushPromises()
    await waitFor(() => {
      expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument()
    })

    await screen.findByRole('button', { name: 'Add' }, { timeout: 10000 })

    const stopBtn = await screen.findByText('Stop Indexing', {}, { timeout: 10000 })
    await userEvent.click(stopBtn)
    expect(apiService.stopIndexing).toHaveBeenCalled()
  }, 20000)

  test('removes a root folder and debounces save', async () => {
    jest.mocked(apiService.getConfig).mockResolvedValueOnce({
      roots: ['/a', '/b'],
      ocr_enabled: false,
      ocr_languages: [],
      face_search_enabled: false,
      semantic_search_enabled: true,
    })

    renderPage()
    await flushPromises()
    await waitFor(() => {
      expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument()
    })
    await screen.findByRole('button', { name: 'Add' }, { timeout: 10000 })

    // Remove first folder
    const firstFolder = screen.getByText('/a')
    const row = firstFolder.closest('div') as HTMLElement
    const removeBtn = within(row).getByRole('button')
    await userEvent.click(removeBtn)
    await waitDebounce()
    await waitFor(() => {
      expect(apiService.updateRoots).toHaveBeenCalled()
    })
  }, 20000)

  test('shows initializing message when indexing with unknown total', async () => {
    jest.mocked(apiService.getIndexStatus).mockResolvedValueOnce({
      status: 'indexing',
      progress: { current_phase: 'metadata', processed_files: 0, total_files: 0 },
    } as any)
    renderPage()
    await flushPromises()
    await waitFor(() => {
      expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument()
    })
    await screen.findByText('Stop Indexing')
    expect(screen.getByText(/Initializing metadata/)).toBeInTheDocument()
  }, 20000)

  test('disables start buttons during indexing', async () => {
    jest.mocked(apiService.getIndexStatus).mockResolvedValueOnce({
      status: 'indexing',
      progress: { current_phase: 'metadata', processed_files: 0, total_files: 0 },
    } as any)
    renderPage()
    await flushPromises()
    await waitFor(() => {
      expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument()
    })
    const quick = (await screen.findByText('Quick Update')).closest('button') as HTMLButtonElement
    const full = (await screen.findByText('Full Refresh')).closest('button') as HTMLButtonElement
    expect(quick).toBeDisabled()
    expect(full).toBeDisabled()
  }, 20000)

  test('shows error toast when saveConfig fails', async () => {
    renderPage()
    await flushPromises()
    await waitFor(() => {
      expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument()
    })
    await screen.findByRole('button', { name: 'Add' }, { timeout: 10000 })

    jest.mocked(apiService.updateConfig).mockRejectedValueOnce(new Error('save failed'))
    // Toggle Smart Search to trigger save
    await userEvent.click(screen.getByLabelText('Smart Search'))
    await waitDebounce()
    await waitFor(() => {
      expect(actualMockToast).toHaveBeenCalledWith(expect.objectContaining({ title: 'Error' }))
    })
  }, 20000)

  test('reset onboarding triggers toast', async () => {
    renderPage()
    await flushPromises()
    await screen.findByText('Run Setup Again')
    await userEvent.click(screen.getByText('Run Setup Again'))
    expect(actualMockToast).toHaveBeenCalledWith(expect.objectContaining({ title: 'Onboarding Reset' }))
  }, 20000)
})
