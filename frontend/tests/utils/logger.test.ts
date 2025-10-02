/**
 * Unit tests for Logger Utility
 * Priority: P1 (Important debugging infrastructure)
 */

import { logger, LogEntry } from '../../src/utils/logger'

describe('Logger Utility', () => {
  let consoleLogSpy: jest.SpyInstance
  let consoleErrorSpy: jest.SpyInstance
  let consoleWarnSpy: jest.SpyInstance
  let consoleInfoSpy: jest.SpyInstance
  let consoleDebugSpy: jest.SpyInstance

  beforeEach(() => {
    consoleLogSpy = jest.spyOn(console, 'log').mockImplementation()
    consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation()
    consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation()
    consoleInfoSpy = jest.spyOn(console, 'info').mockImplementation()
    consoleDebugSpy = jest.spyOn(console, 'debug').mockImplementation()

    // Clear logs for fresh tests
    logger.clearLogs()
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  describe('Basic Logging', () => {
    test('logs debug messages', () => {
      logger.debug('Debug message', { extra: 'data' })
      // Check that logs are stored in memory even if not output to console
      const recentLogs = logger.getRecentLogs(1)
      expect(recentLogs).toHaveLength(1)
      expect(recentLogs[0].level).toBe('DEBUG')
      expect(recentLogs[0].message).toBe('Debug message')
    })

    test('logs info messages', () => {
      logger.info('Info message')
      const recentLogs = logger.getRecentLogs(1)
      expect(recentLogs).toHaveLength(1)
      expect(recentLogs[0].level).toBe('INFO')
      expect(recentLogs[0].message).toBe('Info message')
      expect(consoleInfoSpy).toHaveBeenCalled()
    })

    test('logs warning messages', () => {
      logger.warn('Warning message')
      const recentLogs = logger.getRecentLogs(1)
      expect(recentLogs).toHaveLength(1)
      expect(recentLogs[0].level).toBe('WARN')
      expect(recentLogs[0].message).toBe('Warning message')
      expect(consoleWarnSpy).toHaveBeenCalled()
    })

    test('logs error messages', () => {
      const error = new Error('Test error')
      logger.error('Error occurred', error)
      const recentLogs = logger.getRecentLogs(1)
      expect(recentLogs).toHaveLength(1)
      expect(recentLogs[0].level).toBe('ERROR')
      expect(recentLogs[0].message).toBe('Error occurred')
      expect(consoleErrorSpy).toHaveBeenCalled()
    })

    test('logs with context', () => {
      logger.info('Message with context', { userId: 123 })
      const recentLogs = logger.getRecentLogs(1)
      expect(recentLogs).toHaveLength(1)
      expect(recentLogs[0].context).toEqual({ userId: 123 })
      expect(consoleInfoSpy).toHaveBeenCalled()
    })
  })

  describe('Performance Tracking', () => {
    test('starts and ends performance tracking', () => {
      logger.startPerformance('test-operation', { metadata: 'test' })
      logger.endPerformance('test-operation')

      // Should log performance info (either debug or warn depending on duration)
      const recentLogs = logger.getRecentLogs(5)
      const perfLog = recentLogs.find(log => log.message.includes('test-operation'))
      expect(perfLog).toBeDefined()
    })

    test('warns on slow operations', () => {
      // Mock performance.now to simulate slow operation
      const originalNow = performance.now
      let callCount = 0
      performance.now = jest.fn(() => {
        callCount++
        return callCount === 1 ? 0 : 2000 // 2 second duration
      })

      logger.startPerformance('slow-operation')
      logger.endPerformance('slow-operation')

      const recentLogs = logger.getRecentLogs(5)
      const slowLog = recentLogs.find(log =>
        log.message.includes('slow-operation') && log.level === 'WARN'
      )
      expect(slowLog).toBeDefined()
      expect(consoleWarnSpy).toHaveBeenCalled()

      performance.now = originalNow
    })
  })

  describe('API Logging', () => {
    test('logs API requests', () => {
      const requestId = logger.generateRequestId()
      logger.logApiCall('GET', '/api/test', requestId, null, {})

      const recentLogs = logger.getRecentLogs(5)
      const apiLog = recentLogs.find(log => log.message.includes('API Request'))
      expect(apiLog).toBeDefined()
      expect(consoleInfoSpy).toHaveBeenCalled()
    })

    test('logs API responses', () => {
      const requestId = logger.generateRequestId()
      logger.logApiResponse('GET', '/api/test', requestId, 200, 150, { data: 'response' })

      const recentLogs = logger.getRecentLogs(5)
      const apiLog = recentLogs.find(log => log.message.includes('API Response'))
      expect(apiLog).toBeDefined()
      expect(consoleInfoSpy).toHaveBeenCalled()
    })

    test('logs API errors as error level', () => {
      const requestId = logger.generateRequestId()
      logger.logApiResponse('GET', '/api/test', requestId, 500, 150, { error: 'Server Error' })

      const recentLogs = logger.getRecentLogs(5)
      const errorLog = recentLogs.find(log =>
        log.message.includes('API Response') && log.level === 'ERROR'
      )
      expect(errorLog).toBeDefined()
      expect(consoleErrorSpy).toHaveBeenCalled()
    })
  })

  describe('Component Logging', () => {
    test('logs component mount', () => {
      logger.logComponentMount('TestComponent', { prop1: 'value1' })
      const recentLogs = logger.getRecentLogs(5)
      const mountLog = recentLogs.find(log => log.message.includes('Component mounted'))
      expect(mountLog).toBeDefined()
    })

    test('logs component unmount', () => {
      logger.logComponentUnmount('TestComponent')
      const recentLogs = logger.getRecentLogs(5)
      const unmountLog = recentLogs.find(log => log.message.includes('Component unmounted'))
      expect(unmountLog).toBeDefined()
    })

    test('logs component errors', () => {
      const error = new Error('Component error')
      logger.logComponentError('TestComponent', error, { additional: 'info' })
      const recentLogs = logger.getRecentLogs(5)
      const errorLog = recentLogs.find(log => log.message.includes('Component error'))
      expect(errorLog).toBeDefined()
      expect(consoleErrorSpy).toHaveBeenCalled()
    })
  })

  describe('User Action Logging', () => {
    test('logs user actions', () => {
      logger.logUserAction('click-button', { buttonId: 'submit', page: 'login' })
      const recentLogs = logger.getRecentLogs(5)
      const userLog = recentLogs.find(log => log.message.includes('User action'))
      expect(userLog).toBeDefined()
      expect(consoleInfoSpy).toHaveBeenCalled()
    })
  })

  describe('Log Management', () => {
    test('generates unique request IDs', () => {
      const id1 = logger.generateRequestId()
      const id2 = logger.generateRequestId()

      expect(id1).toBeDefined()
      expect(id2).toBeDefined()
      expect(id1).not.toBe(id2)
    })

    test('gets recent logs', () => {
      logger.info('Test message 1')
      logger.info('Test message 2')
      logger.warn('Test warning')

      const recentLogs = logger.getRecentLogs(10)
      expect(recentLogs).toHaveLength(3)
      expect(recentLogs[0].message).toBe('Test message 1')
      expect(recentLogs[1].message).toBe('Test message 2')
      expect(recentLogs[2].message).toBe('Test warning')
    })

    test('exports logs as string', () => {
      logger.info('Export test message')
      const exported = logger.exportLogs()

      expect(exported).toContain('Export test message')
      expect(exported).toContain('[INFO]')
    })

    test('clears logs', () => {
      logger.info('Test message')
      expect(logger.getRecentLogs(10)).toHaveLength(1)

      logger.clearLogs()
      expect(logger.getRecentLogs(10)).toHaveLength(0)
    })
  })

  describe('Download Functionality', () => {
    test('creates download link for logs', () => {
      // Mock DOM methods
      const createElementSpy = jest.spyOn(document, 'createElement')
      const appendChildSpy = jest.spyOn(document.body, 'appendChild')
      const removeChildSpy = jest.spyOn(document.body, 'removeChild')

      const mockElement = {
        href: '',
        download: '',
        click: jest.fn()
      } as any

      createElementSpy.mockReturnValue(mockElement)
      appendChildSpy.mockImplementation()
      removeChildSpy.mockImplementation()

      // Mock URL methods
      const createObjectURLSpy = jest.spyOn(URL, 'createObjectURL').mockReturnValue('blob:test')
      const revokeObjectURLSpy = jest.spyOn(URL, 'revokeObjectURL').mockImplementation()

      logger.info('Download test')
      logger.downloadLogs()

      expect(createElementSpy).toHaveBeenCalledWith('a')
      expect(mockElement.click).toHaveBeenCalled()
      expect(createObjectURLSpy).toHaveBeenCalled()
      expect(revokeObjectURLSpy).toHaveBeenCalled()
    })
  })

  describe('Error Handling', () => {
    test('handles null and undefined messages gracefully', () => {
      expect(() => {
        logger.info(null as any)
        logger.info(undefined as any)
      }).not.toThrow()
    })

    test('handles errors in error logging', () => {
      const originalError = console.error
      console.error = jest.fn(() => {
        throw new Error('Console error')
      })

      expect(() => {
        logger.error('Should not throw')
      }).not.toThrow()

      console.error = originalError
    })
  })
})