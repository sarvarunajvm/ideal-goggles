/**
 * Simple unit tests for Logger Utility
 * Priority: P1 (Important debugging infrastructure)
 */

import { logger } from '../../src/utils/logger'

describe('Logger Utility - Basic Tests', () => {
  let consoleInfoSpy: jest.SpyInstance
  let consoleErrorSpy: jest.SpyInstance
  let consoleWarnSpy: jest.SpyInstance
  let consoleDebugSpy: jest.SpyInstance

  beforeEach(() => {
    consoleInfoSpy = jest.spyOn(console, 'info').mockImplementation()
    consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation()
    consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation()
    consoleDebugSpy = jest.spyOn(console, 'debug').mockImplementation()
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  test('logger instance exists', () => {
    expect(logger).toBeDefined()
    expect(typeof logger.info).toBe('function')
    expect(typeof logger.error).toBe('function')
    expect(typeof logger.warn).toBe('function')
    expect(typeof logger.debug).toBe('function')
  })

  test('logger has required methods', () => {
    expect(typeof logger.generateRequestId).toBe('function')
    expect(typeof logger.startPerformance).toBe('function')
    expect(typeof logger.endPerformance).toBe('function')
    expect(typeof logger.logApiCall).toBe('function')
    expect(typeof logger.logApiResponse).toBe('function')
    expect(typeof logger.logComponentMount).toBe('function')
    expect(typeof logger.logComponentUnmount).toBe('function')
    expect(typeof logger.logComponentError).toBe('function')
    expect(typeof logger.logUserAction).toBe('function')
    expect(typeof logger.getRecentLogs).toBe('function')
    expect(typeof logger.exportLogs).toBe('function')
    expect(typeof logger.clearLogs).toBe('function')
    expect(typeof logger.downloadLogs).toBe('function')
  })

  test('generates unique request IDs', () => {
    const id1 = logger.generateRequestId()
    const id2 = logger.generateRequestId()

    expect(id1).toBeDefined()
    expect(id2).toBeDefined()
    expect(typeof id1).toBe('string')
    expect(typeof id2).toBe('string')
    expect(id1).not.toBe(id2)
  })

  test('logging methods can be called without errors', () => {
    expect(() => {
      logger.info('Test info message')
      logger.warn('Test warn message')
      logger.error('Test error message')
      logger.debug('Test debug message')
    }).not.toThrow()
  })

  test('performance tracking methods work', () => {
    expect(() => {
      logger.startPerformance('test-operation')
      logger.endPerformance('test-operation')
    }).not.toThrow()
  })

  test('API logging methods work', () => {
    const requestId = logger.generateRequestId()

    expect(() => {
      logger.logApiCall('GET', '/api/test', requestId)
      logger.logApiResponse('GET', '/api/test', requestId, 200, 100)
    }).not.toThrow()
  })

  test('component logging methods work', () => {
    expect(() => {
      logger.logComponentMount('TestComponent')
      logger.logComponentUnmount('TestComponent')
      logger.logComponentError('TestComponent', new Error('Test error'))
    }).not.toThrow()
  })

  test('user action logging works', () => {
    expect(() => {
      logger.logUserAction('click', { button: 'submit' })
    }).not.toThrow()
  })

  test('log management methods work', () => {
    expect(() => {
      const logs = logger.getRecentLogs(10)
      expect(Array.isArray(logs)).toBe(true)

      const exported = logger.exportLogs()
      expect(typeof exported).toBe('string')

      logger.clearLogs()
    }).not.toThrow()
  })

  test('download logs method exists and can be called', () => {
    // Mock DOM methods
    const createElementSpy = jest.spyOn(document, 'createElement')
    const appendChildSpy = jest.spyOn(document.body, 'appendChild')
    const removeChildSpy = jest.spyOn(document.body, 'removeChild')

    const mockElement = {
      href: '',
      download: '',
      click: jest.fn()
    }

    createElementSpy.mockReturnValue(mockElement as any)
    appendChildSpy.mockImplementation()
    removeChildSpy.mockImplementation()

    // Mock URL methods
    global.URL.createObjectURL = jest.fn(() => 'blob:test')
    global.URL.revokeObjectURL = jest.fn()

    expect(() => {
      logger.downloadLogs()
    }).not.toThrow()

    createElementSpy.mockRestore()
    appendChildSpy.mockRestore()
    removeChildSpy.mockRestore()
  })

  test('handles null and undefined gracefully', () => {
    expect(() => {
      logger.info(null as any)
      logger.info(undefined as any)
      logger.error('Error with null data', null)
      logger.warn('Warning with undefined data', undefined)
    }).not.toThrow()
  })

  test('handles complex objects', () => {
    const complexObject = {
      nested: { data: 'value' },
      array: [1, 2, 3],
      func: () => 'test'
    }

    expect(() => {
      logger.info('Complex object test', complexObject)
    }).not.toThrow()
  })
})