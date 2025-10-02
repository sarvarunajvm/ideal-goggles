/**
 * Enhanced unit tests for OSIntegration Service
 * Priority: P1 (Critical OS integration functionality)
 */

import osIntegration from '../../src/services/osIntegration'

// Mock window globals
const mockElectronAPI = {
  getPlatform: jest.fn(),
  revealInFolder: jest.fn(),
  openExternal: jest.fn(),
  getVersion: jest.fn(),
}

// Mock navigator
const mockNavigator = {
  platform: 'Web',
  clipboard: {
    writeText: jest.fn(),
  },
}

const mockNotification = {
  permission: 'default',
  requestPermission: jest.fn(),
}

describe('OSIntegration Service', () => {
  let documentBodyAppendChild: jest.SpyInstance
  let documentBodyRemoveChild: jest.SpyInstance
  let documentCreateElement: jest.SpyInstance
  let documentExecCommand: jest.SpyInstance

  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks()

    // Re-create the clipboard mock to ensure it's fresh
    mockNavigator.clipboard = {
      writeText: jest.fn(),
    }

    // Mock DOM methods
    documentBodyAppendChild = jest.spyOn(document.body, 'appendChild').mockImplementation()
    documentBodyRemoveChild = jest.spyOn(document.body, 'removeChild').mockImplementation()
    documentCreateElement = jest.spyOn(document, 'createElement')

    // Mock execCommand properly
    documentExecCommand = jest.fn().mockReturnValue(true)
    Object.defineProperty(document, 'execCommand', {
      value: documentExecCommand,
      writable: true,
    })

    // Mock timers
    jest.useFakeTimers()

    // Setup default window and navigator mocks
    Object.defineProperty(window, 'electronAPI', {
      value: undefined,
      writable: true,
    })

    Object.defineProperty(window, 'navigator', {
      value: mockNavigator,
      writable: true,
      configurable: true,
    })

    Object.defineProperty(window, 'Notification', {
      value: Object.assign(jest.fn(), mockNotification),
      writable: true,
    })
  })

  afterEach(() => {
    jest.restoreAllMocks()
    jest.useRealTimers()
  })

  describe('Platform Detection', () => {
    test('detects Electron environment', () => {
      window.electronAPI = mockElectronAPI
      expect(osIntegration.isElectron).toBe(true)
    })

    test('detects web environment', () => {
      window.electronAPI = undefined
      expect(osIntegration.isElectron).toBe(false)
    })

    test('gets platform from Electron API', async () => {
      window.electronAPI = mockElectronAPI
      mockElectronAPI.getPlatform.mockResolvedValue('darwin')

      const platform = await osIntegration.getPlatform()
      expect(platform).toBe('darwin')
      expect(mockElectronAPI.getPlatform).toHaveBeenCalled()
    })

    test('falls back to navigator.platform in web environment', async () => {
      window.electronAPI = undefined

      const platform = await osIntegration.getPlatform()
      expect(platform).toBe('Web')
    })
  })

  describe('File Operations', () => {
    describe('Reveal in Folder', () => {
      test('uses Electron API when available', async () => {
        window.electronAPI = mockElectronAPI
        mockElectronAPI.revealInFolder.mockResolvedValue(undefined)

        await osIntegration.revealInFolder('/path/to/file.jpg')

        expect(mockElectronAPI.revealInFolder).toHaveBeenCalledWith('/path/to/file.jpg')
      })

      test('falls back to web implementation', async () => {
        window.electronAPI = undefined
        mockNavigator.clipboard.writeText.mockResolvedValue(undefined)

        await osIntegration.revealInFolder('/path/to/file.jpg')

        expect(mockNavigator.clipboard.writeText).toHaveBeenCalledWith('/path/to')
        expect(documentBodyAppendChild).toHaveBeenCalled()
      })
    })

    describe('Open External', () => {
      test('uses Electron API when available', async () => {
        window.electronAPI = mockElectronAPI
        mockElectronAPI.openExternal.mockResolvedValue(undefined)

        await osIntegration.openExternal('/path/to/file.jpg')

        expect(mockElectronAPI.openExternal).toHaveBeenCalledWith('/path/to/file.jpg')
      })

      test('falls back to web implementation', async () => {
        window.electronAPI = undefined
        mockNavigator.clipboard.writeText.mockResolvedValue(undefined)

        await osIntegration.openExternal('/path/to/file.jpg')

        expect(mockNavigator.clipboard.writeText).toHaveBeenCalledWith('/path/to/file.jpg')
        expect(documentBodyAppendChild).toHaveBeenCalled()
      })
    })
  })

  describe('Clipboard Operations', () => {
    test('copies text using modern clipboard API', async () => {
      mockNavigator.clipboard.writeText.mockResolvedValue(undefined)

      await osIntegration.copyToClipboard('test text')

      expect(mockNavigator.clipboard.writeText).toHaveBeenCalledWith('test text')
    })

    test('falls back to legacy clipboard method', async () => {
      mockNavigator.clipboard.writeText.mockRejectedValue(new Error('Not supported'))
      const mockTextArea = {
        value: '',
        focus: jest.fn(),
        select: jest.fn(),
      }
      documentCreateElement.mockReturnValue(mockTextArea as any)

      await osIntegration.copyToClipboard('test text')

      expect(mockTextArea.value).toBe('test text')
      expect(mockTextArea.focus).toHaveBeenCalled()
      expect(mockTextArea.select).toHaveBeenCalled()
      expect(documentExecCommand).toHaveBeenCalledWith('copy')
      expect(documentBodyAppendChild).toHaveBeenCalledWith(mockTextArea)
      expect(documentBodyRemoveChild).toHaveBeenCalledWith(mockTextArea)
    })

    test('handles clipboard fallback errors gracefully', async () => {
      mockNavigator.clipboard.writeText.mockRejectedValue(new Error('Not supported'))
      documentExecCommand.mockImplementation(() => {
        throw new Error('Copy failed')
      })

      await expect(osIntegration.copyToClipboard('test text')).resolves.not.toThrow()
    })
  })

  describe('Version Management', () => {
    test('gets version from Electron API', async () => {
      window.electronAPI = mockElectronAPI
      mockElectronAPI.getVersion.mockResolvedValue('1.2.3')

      const version = await osIntegration.getVersion()
      expect(version).toBe('1.2.3')
      expect(mockElectronAPI.getVersion).toHaveBeenCalled()
    })

    test('returns web version fallback', async () => {
      window.electronAPI = undefined

      const version = await osIntegration.getVersion()
      expect(version).toBe('1.0.0-web')
    })
  })

  describe('Feature Availability', () => {
    test('checks revealInFolder feature availability', () => {
      window.electronAPI = mockElectronAPI
      expect(osIntegration.isFeatureAvailable('revealInFolder')).toBe(true)

      window.electronAPI = undefined
      expect(osIntegration.isFeatureAvailable('revealInFolder')).toBe(false)
    })

    test('checks openExternal feature availability', () => {
      window.electronAPI = mockElectronAPI
      expect(osIntegration.isFeatureAvailable('openExternal')).toBe(true)

      window.electronAPI = undefined
      expect(osIntegration.isFeatureAvailable('openExternal')).toBe(false)
    })

    test('checks clipboard feature availability', () => {
      expect(osIntegration.isFeatureAvailable('clipboard')).toBe(true)

      Object.defineProperty(navigator, 'clipboard', { value: undefined })
      expect(osIntegration.isFeatureAvailable('clipboard')).toBe(false)
    })

    test('returns false for unknown features', () => {
      expect(osIntegration.isFeatureAvailable('unknown' as any)).toBe(false)
    })
  })

  describe('Desktop Notifications', () => {
    test('shows notification when permission granted', async () => {
      mockNotification.permission = 'granted'
      const NotificationSpy = jest.fn()
      window.Notification = Object.assign(NotificationSpy, mockNotification)

      await osIntegration.showNotification('Title', 'Body', 'icon.png')

      expect(NotificationSpy).toHaveBeenCalledWith('Title', {
        body: 'Body',
        icon: 'icon.png',
      })
    })

    test('requests permission when default', async () => {
      mockNotification.permission = 'default'
      mockNotification.requestPermission.mockResolvedValue('granted')
      const NotificationSpy = jest.fn()
      window.Notification = Object.assign(NotificationSpy, mockNotification)

      await osIntegration.showNotification('Title', 'Body')

      expect(mockNotification.requestPermission).toHaveBeenCalled()
      expect(NotificationSpy).toHaveBeenCalledWith('Title', {
        body: 'Body',
        icon: undefined,
      })
    })

    test('does not show notification when permission denied', async () => {
      mockNotification.permission = 'denied'
      const NotificationSpy = jest.fn()
      window.Notification = Object.assign(NotificationSpy, mockNotification)

      await osIntegration.showNotification('Title', 'Body')

      expect(NotificationSpy).not.toHaveBeenCalled()
    })

    test('handles environments without Notification API', async () => {
      delete (window as any).Notification

      await expect(osIntegration.showNotification('Title', 'Body')).resolves.not.toThrow()
    })
  })

  describe('Desktop Feature Notifications', () => {
    test('shows and auto-removes desktop feature notification', async () => {
      window.electronAPI = undefined
      mockNavigator.clipboard.writeText.mockResolvedValue(undefined)

      const mockNotificationDiv = {
        className: '',
        innerHTML: '',
        remove: jest.fn(),
        parentElement: true,
      }
      documentCreateElement.mockReturnValue(mockNotificationDiv as any)

      await osIntegration.revealInFolder('/test/file.jpg')

      expect(documentCreateElement).toHaveBeenCalledWith('div')
      expect(documentBodyAppendChild).toHaveBeenCalledWith(mockNotificationDiv)
      expect(mockNotificationDiv.innerHTML).toContain('File reveal')

      // Fast-forward timer
      jest.advanceTimersByTime(5000)
      expect(mockNotificationDiv.remove).toHaveBeenCalled()
    })

    test('handles notification removal when element already removed', async () => {
      window.electronAPI = undefined
      mockNavigator.clipboard.writeText.mockResolvedValue(undefined)

      const mockNotificationDiv = {
        className: '',
        innerHTML: '',
        remove: jest.fn(),
        parentElement: null, // Element already removed
      }
      documentCreateElement.mockReturnValue(mockNotificationDiv as any)

      await osIntegration.revealInFolder('/test/file.jpg')

      jest.advanceTimersByTime(5000)
      expect(mockNotificationDiv.remove).not.toHaveBeenCalled()
    })
  })

  describe('Error Handling', () => {
    test('throws error for unimplemented showFileProperties', async () => {
      await expect(osIntegration.showFileProperties()).rejects.toThrow(
        'File properties not yet implemented'
      )
    })

    test('handles Electron API errors gracefully', async () => {
      window.electronAPI = mockElectronAPI
      mockElectronAPI.revealInFolder.mockRejectedValue(new Error('Electron error'))

      await expect(osIntegration.revealInFolder('/test/file.jpg')).rejects.toThrow('Electron error')
    })

    test('handles clipboard API errors gracefully', async () => {
      mockNavigator.clipboard.writeText.mockRejectedValue(new Error('Clipboard error'))
      const mockTextArea = {
        value: '',
        focus: jest.fn(),
        select: jest.fn(),
      }
      documentCreateElement.mockReturnValue(mockTextArea as any)

      await expect(osIntegration.copyToClipboard('test')).resolves.not.toThrow()
    })
  })

  describe('Path Handling', () => {
    test('extracts folder path correctly for Unix paths', async () => {
      window.electronAPI = undefined
      mockNavigator.clipboard.writeText.mockResolvedValue(undefined)

      await osIntegration.revealInFolder('/home/user/documents/file.txt')

      expect(mockNavigator.clipboard.writeText).toHaveBeenCalledWith('/home/user/documents')
    })

    test('extracts folder path correctly for Windows paths', async () => {
      window.electronAPI = undefined
      mockNavigator.clipboard.writeText.mockResolvedValue(undefined)

      await osIntegration.revealInFolder('C:/Users/user/documents/file.txt')

      expect(mockNavigator.clipboard.writeText).toHaveBeenCalledWith('C:/Users/user/documents')
    })

    test('handles file in root directory', async () => {
      window.electronAPI = undefined
      mockNavigator.clipboard.writeText.mockResolvedValue(undefined)

      await osIntegration.revealInFolder('/file.txt')

      expect(mockNavigator.clipboard.writeText).toHaveBeenCalledWith('')
    })
  })
})