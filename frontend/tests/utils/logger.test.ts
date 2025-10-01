/**
 * Unit tests for Logger Utility
 * Priority: P1 (Important debugging infrastructure)
 */

import Logger, { LogLevel, LogEntry } from '../../src/utils/logger'

describe('Logger Utility', () => {
  let logger: Logger
  let consoleLogSpy: jest.SpyInstance
  let consoleErrorSpy: jest.SpyInstance
  let consoleWarnSpy: jest.SpyInstance
  let consoleInfoSpy: jest.SpyInstance

  beforeEach(() => {
    logger = new Logger('TestLogger')
    consoleLogSpy = jest.spyOn(console, 'log').mockImplementation()
    consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation()
    consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation()
    consoleInfoSpy = jest.spyOn(console, 'info').mockImplementation()

    // Clear singleton instance for fresh tests
    Logger.clearInstance()
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  describe('Logger Creation', () => {
    test('creates logger with namespace', () => {
      const testLogger = new Logger('CustomNamespace')
      expect(testLogger.namespace).toBe('CustomNamespace')
    })

    test('singleton pattern for default instance', () => {
      const logger1 = Logger.getInstance()
      const logger2 = Logger.getInstance()
      expect(logger1).toBe(logger2)
    })

    test('sets default log level', () => {
      expect(logger.getLevel()).toBe(LogLevel.INFO)
    })
  })

  describe('Log Level Management', () => {
    test('sets and gets log level', () => {
      logger.setLevel(LogLevel.DEBUG)
      expect(logger.getLevel()).toBe(LogLevel.DEBUG)

      logger.setLevel(LogLevel.ERROR)
      expect(logger.getLevel()).toBe(LogLevel.ERROR)
    })

    test('respects log level hierarchy', () => {
      logger.setLevel(LogLevel.ERROR)

      logger.debug('debug message')
      logger.info('info message')
      logger.warn('warn message')
      logger.error('error message')

      expect(consoleLogSpy).not.toHaveBeenCalled()
      expect(consoleInfoSpy).not.toHaveBeenCalled()
      expect(consoleWarnSpy).not.toHaveBeenCalled()
      expect(consoleErrorSpy).toHaveBeenCalledTimes(1)
    })
  })

  describe('Logging Methods', () => {
    test('logs debug messages', () => {
      logger.setLevel(LogLevel.DEBUG)
      logger.debug('Debug message', { extra: 'data' })

      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('[DEBUG]'),
        expect.stringContaining('TestLogger'),
        'Debug message',
        { extra: 'data' }
      )
    })

    test('logs info messages', () => {
      logger.info('Info message')

      expect(consoleInfoSpy).toHaveBeenCalledWith(
        expect.stringContaining('[INFO]'),
        expect.stringContaining('TestLogger'),
        'Info message'
      )
    })

    test('logs warning messages', () => {
      logger.warn('Warning message')

      expect(consoleWarnSpy).toHaveBeenCalledWith(
        expect.stringContaining('[WARN]'),
        expect.stringContaining('TestLogger'),
        'Warning message'
      )
    })

    test('logs error messages', () => {
      const error = new Error('Test error')
      logger.error('Error occurred', error)

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        expect.stringContaining('[ERROR]'),
        expect.stringContaining('TestLogger'),
        'Error occurred',
        error
      )
    })

    test('logs error with stack trace', () => {
      const error = new Error('Test error')
      logger.error('Error with stack', error)

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        expect.any(String),
        expect.any(String),
        'Error with stack',
        error
      )
    })
  })

  describe('Log History', () => {
    test('maintains log history', () => {
      logger.info('First message')
      logger.warn('Second message')
      logger.error('Third message')

      const history = logger.getHistory()
      expect(history).toHaveLength(3)
      expect(history[0].message).toBe('First message')
      expect(history[1].message).toBe('Second message')
      expect(history[2].message).toBe('Third message')
    })

    test('respects max history size', () => {
      const maxSize = 100
      logger.setMaxHistorySize(maxSize)

      for (let i = 0; i < 150; i++) {
        logger.info(`Message ${i}`)
      }

      const history = logger.getHistory()
      expect(history).toHaveLength(maxSize)
      expect(history[0].message).toBe('Message 50')
      expect(history[99].message).toBe('Message 149')
    })

    test('clears log history', () => {
      logger.info('Message 1')
      logger.info('Message 2')

      expect(logger.getHistory()).toHaveLength(2)

      logger.clearHistory()
      expect(logger.getHistory()).toHaveLength(0)
    })

    test('filters history by level', () => {
      logger.setLevel(LogLevel.DEBUG)
      logger.debug('Debug msg')
      logger.info('Info msg')
      logger.warn('Warn msg')
      logger.error('Error msg')

      const errorLogs = logger.getHistory(LogLevel.ERROR)
      expect(errorLogs).toHaveLength(1)
      expect(errorLogs[0].level).toBe(LogLevel.ERROR)

      const warnAndAbove = logger.getHistory(LogLevel.WARN)
      expect(warnAndAbove).toHaveLength(2)
    })
  })

  describe('Performance Logging', () => {
    test('measures performance', () => {
      const endTimer = logger.startTimer('operation')

      // Simulate some work
      const start = Date.now()
      while (Date.now() - start < 100) {
        // Wait ~100ms
      }

      endTimer()

      expect(consoleInfoSpy).toHaveBeenCalledWith(
        expect.any(String),
        expect.any(String),
        expect.stringContaining('operation completed in'),
        expect.stringContaining('ms')
      )
    })

    test('measures async operations', async () => {
      const endTimer = logger.startTimer('async-op')

      await new Promise(resolve => setTimeout(resolve, 50))

      endTimer()

      expect(consoleInfoSpy).toHaveBeenCalledWith(
        expect.any(String),
        expect.any(String),
        expect.stringContaining('async-op completed in'),
        expect.stringMatching(/\d+ms/)
      )
    })
  })

  describe('Formatted Output', () => {
    test('formats log entries with timestamp', () => {
      const now = new Date()
      jest.spyOn(Date, 'now').mockReturnValue(now.getTime())

      logger.info('Timestamped message')

      expect(consoleInfoSpy).toHaveBeenCalledWith(
        expect.stringContaining(now.toISOString()),
        expect.any(String),
        expect.any(String)
      )
    })

    test('includes namespace in output', () => {
      const customLogger = new Logger('CustomModule')
      customLogger.info('Module message')

      expect(consoleInfoSpy).toHaveBeenCalledWith(
        expect.any(String),
        expect.stringContaining('[CustomModule]'),
        'Module message'
      )
    })

    test('handles objects and arrays', () => {
      const obj = { key: 'value', nested: { data: 123 } }
      const arr = [1, 2, 3]

      logger.info('Complex data', obj, arr)

      expect(consoleInfoSpy).toHaveBeenCalledWith(
        expect.any(String),
        expect.any(String),
        'Complex data',
        obj,
        arr
      )
    })
  })

  describe('Group Logging', () => {
    test('groups related log messages', () => {
      const groupSpy = jest.spyOn(console, 'group').mockImplementation()
      const groupEndSpy = jest.spyOn(console, 'groupEnd').mockImplementation()

      logger.group('Operation Group')
      logger.info('Step 1')
      logger.info('Step 2')
      logger.groupEnd()

      expect(groupSpy).toHaveBeenCalledWith('Operation Group')
      expect(consoleInfoSpy).toHaveBeenCalledTimes(2)
      expect(groupEndSpy).toHaveBeenCalled()
    })

    test('nested groups', () => {
      const groupSpy = jest.spyOn(console, 'group').mockImplementation()
      const groupEndSpy = jest.spyOn(console, 'groupEnd').mockImplementation()

      logger.group('Outer')
      logger.info('Outer message')
      logger.group('Inner')
      logger.info('Inner message')
      logger.groupEnd()
      logger.groupEnd()

      expect(groupSpy).toHaveBeenCalledTimes(2)
      expect(groupEndSpy).toHaveBeenCalledTimes(2)
    })
  })

  describe('Context and Metadata', () => {
    test('adds context to log entries', () => {
      logger.withContext({ userId: 123, sessionId: 'abc' })
      logger.info('User action')

      const history = logger.getHistory()
      expect(history[0].context).toEqual({
        userId: 123,
        sessionId: 'abc'
      })
    })

    test('merges multiple contexts', () => {
      logger.withContext({ userId: 123 })
      logger.withContext({ sessionId: 'abc' })
      logger.info('Merged context')

      const history = logger.getHistory()
      expect(history[0].context).toEqual({
        userId: 123,
        sessionId: 'abc'
      })
    })

    test('clears context', () => {
      logger.withContext({ userId: 123 })
      logger.clearContext()
      logger.info('No context')

      const history = logger.getHistory()
      expect(history[0].context).toBeUndefined()
    })
  })

  describe('Export and Serialization', () => {
    test('exports log history as JSON', () => {
      logger.info('Message 1')
      logger.warn('Message 2')

      const json = logger.exportAsJSON()
      const parsed = JSON.parse(json)

      expect(parsed).toHaveLength(2)
      expect(parsed[0].message).toBe('Message 1')
      expect(parsed[1].message).toBe('Message 2')
    })

    test('exports filtered logs', () => {
      logger.setLevel(LogLevel.DEBUG)
      logger.debug('Debug')
      logger.info('Info')
      logger.error('Error')

      const json = logger.exportAsJSON(LogLevel.ERROR)
      const parsed = JSON.parse(json)

      expect(parsed).toHaveLength(1)
      expect(parsed[0].message).toBe('Error')
    })

    test('downloads log file', () => {
      // Mock DOM methods
      const createElementSpy = jest.spyOn(document, 'createElement')
      const clickSpy = jest.fn()

      createElementSpy.mockReturnValue({
        click: clickSpy,
        download: '',
        href: ''
      } as any)

      logger.info('Download test')
      logger.downloadLogs()

      expect(createElementSpy).toHaveBeenCalledWith('a')
      expect(clickSpy).toHaveBeenCalled()
    })
  })

  describe('Error Handling', () => {
    test('handles null and undefined messages', () => {
      logger.info(null as any)
      logger.info(undefined as any)

      expect(consoleInfoSpy).toHaveBeenCalledTimes(2)
    })

    test('handles circular references in objects', () => {
      const circular: any = { a: 1 }
      circular.self = circular

      expect(() => {
        logger.info('Circular', circular)
      }).not.toThrow()
    })

    test('catches console errors', () => {
      consoleErrorSpy.mockImplementation(() => {
        throw new Error('Console error')
      })

      expect(() => {
        logger.error('Should not throw')
      }).not.toThrow()
    })
  })

  describe('Configuration', () => {
    test('configures from environment variables', () => {
      process.env.LOG_LEVEL = 'DEBUG'
      const envLogger = new Logger('EnvLogger')

      expect(envLogger.getLevel()).toBe(LogLevel.DEBUG)

      delete process.env.LOG_LEVEL
    })

    test('enables/disables logging', () => {
      logger.disable()
      logger.info('Should not log')

      expect(consoleInfoSpy).not.toHaveBeenCalled()

      logger.enable()
      logger.info('Should log')

      expect(consoleInfoSpy).toHaveBeenCalledTimes(1)
    })

    test('sets custom formatter', () => {
      const customFormatter = jest.fn((entry: LogEntry) => {
        return `Custom: ${entry.message}`
      })

      logger.setFormatter(customFormatter)
      logger.info('Test message')

      expect(customFormatter).toHaveBeenCalled()
    })
  })
})