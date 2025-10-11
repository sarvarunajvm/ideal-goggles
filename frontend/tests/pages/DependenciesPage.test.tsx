import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import DependenciesPage from '../../src/pages/DependenciesPage'
import { apiService, DependenciesResponse, DependencyVerificationResponse } from '../../src/services/apiClient'

// Mock API client
jest.mock('../../src/services/apiClient', () => ({
  apiService: {
    getDependencies: jest.fn(),
    verifyDependencies: jest.fn(),
    installDependencies: jest.fn(),
  },
}))

// Mock toast hooks to avoid Radix internals and capture calls
const mockToastFn = jest.fn()
jest.mock('../../src/components/ui/use-toast', () => ({
  useToast: () => ({ toasts: [], toast: mockToastFn, dismiss: jest.fn() }),
}))

const mockDependencies: DependenciesResponse = {
  core: [
    {
      name: 'SQLite',
      installed: true,
      required: true,
      version: '3.0+',
      description: 'Database for storing photo metadata',
    },
    {
      name: 'Pillow',
      installed: true,
      required: true,
      version: '10.0+',
      description: 'Image processing library',
    },
  ],
  ml: [
    {
      name: 'PyTorch',
      installed: false,
      required: false,
      version: null,
      description: 'Deep learning framework for ML models',
    },
    {
      name: 'CLIP',
      installed: false,
      required: false,
      version: null,
      description: 'Semantic search with natural language',
    },
    {
      name: 'InsightFace',
      installed: true,
      required: false,
      version: '0.7.3',
      description: 'Face detection and recognition',
    },
  ],
  features: {
    basic_search: true,
    semantic_search: false,
    face_recognition: true,
    face_detection: true,
    thumbnail_generation: true,
  },
}

const mockVerificationIssues: DependencyVerificationResponse = {
  summary: {
    all_functional: false,
    issues_found: [
      { model: 'clip', error: 'Model not loaded' },
      { model: 'pytorch', error: 'CUDA not available' },
    ],
  },
  models: {
    clip: {
      functional: false,
      error: 'Model not loaded',
      details: {
        available_memory_gb: 10,
        total_memory_gb: 16,
      },
    },
    pytorch: {
      functional: true,
      error: null,
      details: {
        available_memory_gb: 10,
        total_memory_gb: 16,
        device: 'cpu',
        model_name: 'resnet-50',
      },
    },
  },
  system: {
    memory: { total_gb: 16, available_gb: 10, percent_used: 37.5 },
    python_version: '3.11',
    platform: 'darwin',
    architecture: 'arm64',
  },
  recommendations: ['Enable CUDA for better performance'],
}

const mockVerificationAllGood: DependencyVerificationResponse = {
  summary: {
    all_functional: true,
    issues_found: [],
  },
  models: {
    clip: {
      functional: true,
      error: null,
      details: {
        available_memory_gb: 10,
        total_memory_gb: 16,
        device: 'cpu',
        model_name: 'ViT-B/32',
      },
    },
  },
  system: {
    memory: { total_gb: 16, available_gb: 12, percent_used: 25 },
    python_version: '3.11',
    platform: 'darwin',
    architecture: 'arm64',
  },
  recommendations: [],
}

describe('DependenciesPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    jest.mocked(apiService.getDependencies).mockResolvedValue(mockDependencies)
    jest.mocked(apiService.verifyDependencies).mockResolvedValue(mockVerificationIssues)
    jest.mocked(apiService.installDependencies).mockResolvedValue({ status: 'success' })
  })

  const renderComponent = () => {
    return render(
      <MemoryRouter>
        <DependenciesPage />
      </MemoryRouter>
    )
  }

  it('shows loading state initially and then renders content', async () => {
    renderComponent()

    // Initial loading UI
    expect(screen.getByText('Loading dependencies...')).toBeInTheDocument()

    // After data loads
    await waitFor(() => {
      expect(screen.getByText('Dependencies')).toBeInTheDocument()
      expect(apiService.getDependencies).toHaveBeenCalled()
      expect(apiService.verifyDependencies).toHaveBeenCalled()
    })

    // Core components
    expect(screen.getByText('Core Components (Required)')).toBeInTheDocument()
    expect(screen.getByText('SQLite')).toBeInTheDocument()
    expect(screen.getByText('Pillow')).toBeInTheDocument()

    // ML components section and badges/buttons
    expect(screen.getByText('Machine Learning Components')).toBeInTheDocument()
    expect(screen.getByText('PyTorch')).toBeInTheDocument()
    expect(screen.getByText('CLIP')).toBeInTheDocument()
    expect(screen.getByText('InsightFace')).toBeInTheDocument()
    // Not installed items show a badge
    expect(screen.getAllByText('Not Installed').length).toBeGreaterThan(0)

    // Features grid
    expect(screen.getByText('Available Features')).toBeInTheDocument()
    expect(screen.getByText('Basic Search')).toBeInTheDocument()
    expect(screen.getByText('Semantic Search')).toBeInTheDocument()
  })

  it('renders verification results in Model Status', async () => {
    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Model Status')).toBeInTheDocument()
    })

    // Should render entries from verification.models
    expect(screen.getByText('clip')).toBeInTheDocument()
    expect(screen.getByText('pytorch')).toBeInTheDocument()
    // Non-functional model shows error text (appears in alert and card)
    expect(screen.getAllByText('Model not loaded').length).toBeGreaterThan(0)
  })

  it('clicking Verify triggers re-verification and shows success toast when all functional', async () => {
    const user = userEvent.setup()
    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Dependencies')).toBeInTheDocument()
    })

    // Next verification returns all good
    jest.mocked(apiService.verifyDependencies).mockResolvedValueOnce(mockVerificationAllGood)

    await user.click(screen.getByText('Verify'))

    await waitFor(() => {
      expect(apiService.verifyDependencies).toHaveBeenCalledTimes(2)
      expect(mockToastFn).toHaveBeenCalled()
    })

    const lastToastCall = mockToastFn.mock.calls[mockToastFn.mock.calls.length - 1][0]
    expect(lastToastCall.title).toBe('All Systems Ready')
  })

  it('clicking Refresh reloads dependencies', async () => {
    const user = userEvent.setup()
    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Dependencies')).toBeInTheDocument()
    })

    await user.click(screen.getByText('Refresh'))

    await waitFor(() => {
      expect(apiService.getDependencies).toHaveBeenCalledTimes(2)
    })
  })

  it('installs a specific ML component and refreshes state afterwards', async () => {
    const user = userEvent.setup()
    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('CLIP')).toBeInTheDocument()
    })

    // Make install take a moment so the progress UI renders
    jest
      .mocked(apiService.installDependencies)
      .mockImplementationOnce(
        () => new Promise(resolve => setTimeout(() => resolve({ status: 'success' }), 30))
      )

    // Click the Install button for CLIP (second not-installed item)
    await user.click(screen.getAllByText('Install')[1])

    // Progress card should appear during install flow
    await screen.findByText(/Installing/i)

    await waitFor(() => {
      expect(apiService.installDependencies).toHaveBeenCalledWith(['clip'])
      // After success, dependencies and verification should be refreshed
      expect(apiService.getDependencies).toHaveBeenCalledTimes(2)
      expect(apiService.verifyDependencies).toHaveBeenCalledTimes(2)
    })
  })

  it('installs all ML dependencies when clicking Install All ML', async () => {
    const user = userEvent.setup()
    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Machine Learning Components')).toBeInTheDocument()
    })

    // Button should be visible because not all ML are installed
    const installAllBtn = screen.getByText('Install All ML')
    expect(installAllBtn).toBeInTheDocument()

    await user.click(installAllBtn)

    await waitFor(() => {
      expect(apiService.installDependencies).toHaveBeenCalledWith(['all'])
      expect(apiService.getDependencies).toHaveBeenCalledTimes(2)
      expect(apiService.verifyDependencies).toHaveBeenCalledTimes(2)
    })
  })

  it('shows error toast when verification fails', async () => {
    const user = userEvent.setup()
    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Dependencies')).toBeInTheDocument()
    })

    jest.mocked(apiService.verifyDependencies).mockRejectedValueOnce(new Error('boom'))

    await user.click(screen.getByText('Verify'))

    await waitFor(() => {
      expect(mockToastFn).toHaveBeenCalled()
      const lastToastCall = mockToastFn.mock.calls[mockToastFn.mock.calls.length - 1][0]
      expect(lastToastCall.title).toBe('Verification Failed')
    })
  })
})
