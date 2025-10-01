/**
 * Unit tests for OS Integration Service
 * Priority: P1 (Important OS interactions)
 */

describe('OS Integration Service', () => {
  let mockElectronAPI: any

  beforeEach(() => {
    // Mock electron API
    mockElectronAPI = {
      openFile: jest.fn(),
      revealInFolder: jest.fn(),
      getBackendLogPath: jest.fn(),
      getBackendPort: jest.fn(),
      onBackendReady: jest.fn(),
      onBackendError: jest.fn(),
      checkBackendHealth: jest.fn()
    }

    ;(window as any).electronAPI = mockElectronAPI
  })

  afterEach(() => {
    delete (window as any).electronAPI
    jest.clearAllMocks()
  })

  describe('File Operations', () => {
    test('opens file in OS viewer', async () => {
      const { openFile } = await import('../../src/services/osIntegration')
      mockElectronAPI.openFile.mockResolvedValue(true)

      const result = await openFile('/path/to/photo.jpg')

      expect(mockElectronAPI.openFile).toHaveBeenCalledWith('/path/to/photo.jpg')
      expect(result).toBe(true)
    })

    test('reveals file in folder', async () => {
      const { revealInFolder } = await import('../../src/services/osIntegration')
      mockElectronAPI.revealInFolder.mockResolvedValue(true)

      const result = await revealInFolder('/path/to/photo.jpg')

      expect(mockElectronAPI.revealInFolder).toHaveBeenCalledWith('/path/to/photo.jpg')
      expect(result).toBe(true)
    })

    test('handles file operation errors', async () => {
      const { openFile } = await import('../../src/services/osIntegration')
      mockElectronAPI.openFile.mockRejectedValue(new Error('File not found'))

      await expect(openFile('/invalid/path')).rejects.toThrow('File not found')
    })
  })

  describe('Backend Management', () => {
    test('gets backend log path', async () => {
      const { getBackendLogPath } = await import('../../src/services/osIntegration')
      mockElectronAPI.getBackendLogPath.mockResolvedValue('/logs/backend.log')

      const result = await getBackendLogPath()

      expect(result).toBe('/logs/backend.log')
    })

    test('gets backend port', async () => {
      const { getBackendPort } = await import('../../src/services/osIntegration')
      mockElectronAPI.getBackendPort.mockResolvedValue(5555)

      const result = await getBackendPort()

      expect(result).toBe(5555)
    })

    test('checks backend health', async () => {
      const { checkBackendHealth } = await import('../../src/services/osIntegration')
      mockElectronAPI.checkBackendHealth.mockResolvedValue({ healthy: true })

      const result = await checkBackendHealth()

      expect(result).toEqual({ healthy: true })
    })

    test('handles backend ready event', async () => {
      const { onBackendReady } = await import('../../src/services/osIntegration')
      const callback = jest.fn()

      onBackendReady(callback)

      expect(mockElectronAPI.onBackendReady).toHaveBeenCalledWith(callback)
    })

    test('handles backend error event', async () => {
      const { onBackendError } = await import('../../src/services/osIntegration')
      const callback = jest.fn()

      onBackendError(callback)

      expect(mockElectronAPI.onBackendError).toHaveBeenCalledWith(callback)
    })
  })

  describe('Non-Electron Environment', () => {
    beforeEach(() => {
      delete (window as any).electronAPI
    })

    test('returns false for file operations in browser', async () => {
      const { openFile, revealInFolder } = await import('../../src/services/osIntegration')

      const openResult = await openFile('/path/to/file')
      const revealResult = await revealInFolder('/path/to/file')

      expect(openResult).toBe(false)
      expect(revealResult).toBe(false)
    })

    test('returns null for backend info in browser', async () => {
      const { getBackendLogPath, getBackendPort } = await import('../../src/services/osIntegration')

      const logPath = await getBackendLogPath()
      const port = await getBackendPort()

      expect(logPath).toBeNull()
      expect(port).toBeNull()
    })

    test('returns null for backend health in browser', async () => {
      const { checkBackendHealth } = await import('../../src/services/osIntegration')

      const health = await checkBackendHealth()

      expect(health).toBeNull()
    })

    test('does nothing for event handlers in browser', () => {
      const { onBackendReady, onBackendError } = require('../../src/services/osIntegration')
      const callback = jest.fn()

      // Should not throw
      expect(() => {
        onBackendReady(callback)
        onBackendError(callback)
      }).not.toThrow()

      expect(callback).not.toHaveBeenCalled()
    })
  })

  describe('isElectron Detection', () => {
    test('correctly detects Electron environment', () => {
      const { isElectron } = require('../../src/services/osIntegration')

      // With electronAPI
      ;(window as any).electronAPI = {}
      expect(isElectron()).toBe(true)

      // Without electronAPI
      delete (window as any).electronAPI
      expect(isElectron()).toBe(false)
    })
  })
})