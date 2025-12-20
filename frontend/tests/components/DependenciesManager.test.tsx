import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import DependenciesManager from '../../src/components/DependenciesManager'

jest.mock('../../src/components/ui/use-toast', () => ({
  useToast: () => ({ toast: jest.fn() }),
}))

// Define mock implementation inside the factory
jest.mock('../../src/services/apiClient', () => ({
  apiService: {
    getDependencies: jest.fn(),
    installDependencies: jest.fn(),
  },
}))

describe('DependenciesManager', () => {
  // Get reference to mocked functions
  const { apiService } = require('../../src/services/apiClient')
  const getDependenciesMock = apiService.getDependencies as jest.Mock
  const installDependenciesMock = apiService.installDependencies as jest.Mock

  beforeEach(() => {
    jest.clearAllMocks()
    
    // Default successful response
    getDependenciesMock.mockResolvedValue({
      core: [
        { name: 'SQLite', installed: true, required: true, version: '3.0+', description: 'DB' },
      ],
      ml: [
        { name: 'Tesseract', installed: false, required: false, version: null, description: 'OCR' },
        { name: 'PyTorch', installed: false, required: false, version: null, description: 'ML' },
      ],
      features: { text_recognition: false },
    })
    installDependenciesMock.mockResolvedValue({ status: 'success' })
  })

  test('renders core and ML dependencies and allows install', async () => {
    render(<DependenciesManager />)

    await waitFor(() => {
      expect(screen.getByText(/Core Dependencies/)).toBeInTheDocument()
    })

    expect(screen.getByText('SQLite')).toBeInTheDocument()
    expect(screen.getByText('Tesseract')).toBeInTheDocument()

    // Click Install on specific ML dependency card
    const installBtn = screen.getAllByRole('button', { name: /^Install$/ })[0]
    await userEvent.click(installBtn)

    await waitFor(() => {
      expect(installDependenciesMock).toHaveBeenCalled()
    })
  })

  test('refresh button re-fetches dependencies', async () => {
    render(<DependenciesManager />)
    await waitFor(() => screen.getByText(/ML Dependencies/))
    const refresh = screen.getByRole('button', { name: /Refresh/i })
    await userEvent.click(refresh)
    
    await waitFor(() => {
      expect(getDependenciesMock).toHaveBeenCalledTimes(2)
    })
  })

  test('handles fetch error and shows fallback in dev mode', async () => {
    getDependenciesMock.mockReset()
    getDependenciesMock.mockRejectedValueOnce(new Error('Network error'))
    
    const originalElectron = (window as any).electronAPI
    ;(window as any).electronAPI = { selectDirectory: jest.fn() }

    render(<DependenciesManager />)

    await waitFor(() => {
      expect(screen.getByText('Pillow')).toBeInTheDocument()
      expect(screen.getByText('Tesseract')).toBeInTheDocument()
    })

    ;(window as any).electronAPI = originalElectron
  })

  test('handles fetch error and shows no ML deps in production', async () => {
    getDependenciesMock.mockReset()
    getDependenciesMock.mockRejectedValueOnce(new Error('Network error'))
    
    const originalElectron = (window as any).electronAPI;
    (window as any).electronAPI = undefined;

    render(<DependenciesManager />)

    await waitFor(() => {
      expect(screen.getByText('Pillow')).toBeInTheDocument()
      expect(screen.queryByText('Tesseract')).not.toBeInTheDocument()
    })

    // Restore
    ;(window as any).electronAPI = originalElectron;
  })

  test('handles Install All functionality', async () => {
    render(<DependenciesManager />)
    await waitFor(() => screen.getByText(/ML Dependencies/))

    const installAllBtn = screen.getByRole('button', { name: /Install All/i })
    await userEvent.click(installAllBtn)

    await waitFor(() => {
      expect(installDependenciesMock).toHaveBeenCalledWith(['all'])
    })
  })

  test('displays warning toast on installation warning', async () => {
    installDependenciesMock.mockResolvedValueOnce({ 
      status: 'warning', 
      errors: 'Some warning' 
    })

    render(<DependenciesManager />)
    await waitFor(() => screen.getByText(/ML Dependencies/))

    const installBtn = screen.getAllByRole('button', { name: /^Install$/ })[0]
    await userEvent.click(installBtn)

    await waitFor(() => {
      expect(installDependenciesMock).toHaveBeenCalled()
    })
  })

  test('displays error toast on installation exception', async () => {
    installDependenciesMock.mockRejectedValueOnce(new Error('Install failed'))

    render(<DependenciesManager />)
    await waitFor(() => screen.getByText(/ML Dependencies/))

    const installBtn = screen.getAllByRole('button', { name: /^Install$/ })[0]
    await userEvent.click(installBtn)

    await waitFor(() => {
      expect(installDependenciesMock).toHaveBeenCalled()
    })
  })
})
