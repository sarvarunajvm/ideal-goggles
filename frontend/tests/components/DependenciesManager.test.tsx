import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import DependenciesManager from '../../src/components/DependenciesManager'

jest.mock('../../src/components/ui/use-toast', () => ({
  useToast: () => ({ toast: jest.fn() }),
}))

jest.mock('../../src/services/apiClient', () => ({
  apiService: {
    getDependencies: jest.fn().mockResolvedValue({
      core: [
        { name: 'SQLite', installed: true, required: true, version: '3.0+', description: 'DB' },
      ],
      ml: [
        { name: 'Tesseract', installed: false, required: false, version: null, description: 'OCR' },
      ],
      features: { text_recognition: false },
    }),
    installDependencies: jest.fn().mockResolvedValue({ status: 'success' }),
  },
}))

describe('DependenciesManager', () => {
  test('renders core and ML dependencies and allows install', async () => {
    render(<DependenciesManager />)

    await waitFor(() => {
      expect(screen.getByText(/Core Dependencies/)).toBeInTheDocument()
    })

    expect(screen.getByText('SQLite')).toBeInTheDocument()
    expect(screen.getByText('Tesseract')).toBeInTheDocument()

    // Click Install on specific ML dependency card
    const installBtn = screen.getByRole('button', { name: /^Install$/ })
    await userEvent.click(installBtn)

    await waitFor(() => {
      const { apiService } = require('../../src/services/apiClient')
      expect(apiService.installDependencies).toHaveBeenCalled()
    })
  })

  test('refresh button re-fetches dependencies', async () => {
    const { apiService } = require('../../src/services/apiClient')
    render(<DependenciesManager />)
    await waitFor(() => screen.getByText(/ML Dependencies/))
    const refresh = screen.getByRole('button', { name: /Refresh/i })
    await userEvent.click(refresh)
    await waitFor(() => {
      expect(apiService.getDependencies).toHaveBeenCalledTimes(2)
    })
  })
})
