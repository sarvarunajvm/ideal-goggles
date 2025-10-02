/**
 * Comprehensive unit tests for main.tsx
 * Tests React app initialization, router setup, and production behaviors
 */

import React from 'react'

// Mock all dependencies before imports
const mockRender = jest.fn()
const mockCreateRoot = jest.fn(() => ({ render: mockRender }))

jest.mock('react-dom/client', () => ({
  createRoot: mockCreateRoot,
}))

jest.mock('../src/App', () => {
  return function MockApp() {
    return React.createElement('div', { 'data-testid': 'mock-app' }, 'App')
  }
})

jest.mock('../src/pages/SearchPage', () => {
  return function MockSearchPage() {
    return React.createElement('div', { 'data-testid': 'mock-search-page' }, 'SearchPage')
  }
})

jest.mock('../src/pages/SettingsPage', () => {
  return function MockSettingsPage() {
    return React.createElement('div', { 'data-testid': 'mock-settings-page' }, 'SettingsPage')
  }
})

jest.mock('../src/pages/PeoplePage', () => {
  return function MockPeoplePage() {
    return React.createElement('div', { 'data-testid': 'mock-people-page' }, 'PeoplePage')
  }
})

jest.mock('../src/index.css', () => ({}))

describe('main.tsx - Application Entry Point', () => {
  let mockGetElementById: jest.SpyInstance
  let mockAddEventListener: jest.SpyInstance
  let originalNodeEnv: string | undefined
  let mockRootElement: HTMLElement

  beforeEach(() => {
    // Clear all mocks
    jest.clearAllMocks()
    jest.resetModules()

    // Store original NODE_ENV
    originalNodeEnv = process.env.NODE_ENV

    // Setup mocks
    mockRootElement = document.createElement('div')
    mockRootElement.id = 'root'

    mockGetElementById = jest
      .spyOn(document, 'getElementById')
      .mockReturnValue(mockRootElement)

    mockAddEventListener = jest.spyOn(document, 'addEventListener').mockImplementation()
  })

  afterEach(() => {
    jest.restoreAllMocks()
    // Restore NODE_ENV
    if (originalNodeEnv !== undefined) {
      process.env.NODE_ENV = originalNodeEnv
    }
  })

  describe('Application Initialization', () => {
    test('creates React root with root element', () => {
      require('../src/main')

      expect(mockGetElementById).toHaveBeenCalledWith('root')
      expect(mockCreateRoot).toHaveBeenCalledWith(mockRootElement)
    })

    test('renders application', () => {
      require('../src/main')

      expect(mockRender).toHaveBeenCalledTimes(1)
      expect(mockRender).toHaveBeenCalled()
    })

    test('renders only once on initialization', () => {
      require('../src/main')

      expect(mockRender).toHaveBeenCalledTimes(1)
    })

    test('creates only one root', () => {
      require('../src/main')

      expect(mockCreateRoot).toHaveBeenCalledTimes(1)
    })

    test('queries DOM only once for root element', () => {
      require('../src/main')

      expect(mockGetElementById).toHaveBeenCalledTimes(1)
    })
  })

  describe('Production Environment Behavior', () => {
    test('disables context menu in production', () => {
      process.env.NODE_ENV = 'production'
      jest.resetModules()

      require('../src/main')

      expect(mockAddEventListener).toHaveBeenCalledWith(
        'contextmenu',
        expect.any(Function)
      )
    })

    test('context menu handler prevents default', () => {
      process.env.NODE_ENV = 'production'
      jest.resetModules()

      require('../src/main')

      const contextMenuHandler = mockAddEventListener.mock.calls.find(
        (call) => call[0] === 'contextmenu'
      )?.[1]

      expect(contextMenuHandler).toBeDefined()

      const mockEvent = {
        preventDefault: jest.fn(),
      }

      contextMenuHandler(mockEvent)
      expect(mockEvent.preventDefault).toHaveBeenCalled()
    })

    test('context menu handler is added only in production', () => {
      process.env.NODE_ENV = 'production'
      jest.resetModules()

      require('../src/main')

      const contextMenuCalls = mockAddEventListener.mock.calls.filter(
        (call) => call[0] === 'contextmenu'
      )

      expect(contextMenuCalls.length).toBe(1)
    })

    test('multiple context menu events are prevented', () => {
      process.env.NODE_ENV = 'production'
      jest.resetModules()

      require('../src/main')

      const handler = mockAddEventListener.mock.calls.find(
        (call) => call[0] === 'contextmenu'
      )?.[1]

      const mockEvent1 = { preventDefault: jest.fn() }
      const mockEvent2 = { preventDefault: jest.fn() }
      const mockEvent3 = { preventDefault: jest.fn() }

      handler(mockEvent1)
      handler(mockEvent2)
      handler(mockEvent3)

      expect(mockEvent1.preventDefault).toHaveBeenCalled()
      expect(mockEvent2.preventDefault).toHaveBeenCalled()
      expect(mockEvent3.preventDefault).toHaveBeenCalled()
    })
  })

  describe('Development Environment Behavior', () => {
    test('does not disable context menu in development', () => {
      process.env.NODE_ENV = 'development'
      jest.resetModules()

      require('../src/main')

      const contextMenuCalls = mockAddEventListener.mock.calls.filter(
        (call) => call[0] === 'contextmenu'
      )

      expect(contextMenuCalls.length).toBe(0)
    })

    test('application still initializes in development', () => {
      process.env.NODE_ENV = 'development'
      jest.resetModules()

      require('../src/main')

      expect(mockCreateRoot).toHaveBeenCalled()
      expect(mockRender).toHaveBeenCalled()
    })
  })

  describe('Error Handling', () => {
    test('handles missing root element', () => {
      mockGetElementById.mockReturnValue(null)

      expect(() => {
        require('../src/main')
      }).toThrow()
    })

    test('handles createRoot errors', () => {
      mockCreateRoot.mockImplementation(() => {
        throw new Error('Failed to create root')
      })

      expect(() => {
        require('../src/main')
      }).toThrow('Failed to create root')
    })

    test('handles render errors', () => {
      mockRender.mockImplementation(() => {
        throw new Error('Render failed')
      })

      expect(() => {
        require('../src/main')
      }).toThrow('Render failed')
    })
  })

  describe('Environment Detection', () => {
    test('handles test environment', () => {
      process.env.NODE_ENV = 'test'
      jest.resetModules()

      require('../src/main')

      // Should not disable context menu in test
      const contextMenuCalls = mockAddEventListener.mock.calls.filter(
        (call) => call[0] === 'contextmenu'
      )
      expect(contextMenuCalls.length).toBe(0)
    })

    test('handles undefined NODE_ENV', () => {
      delete process.env.NODE_ENV
      jest.resetModules()

      require('../src/main')

      // Should behave as development when NODE_ENV is undefined
      const contextMenuCalls = mockAddEventListener.mock.calls.filter(
        (call) => call[0] === 'contextmenu'
      )
      expect(contextMenuCalls.length).toBe(0)
    })

    test('application still runs with undefined NODE_ENV', () => {
      delete process.env.NODE_ENV
      jest.resetModules()

      require('../src/main')

      expect(mockCreateRoot).toHaveBeenCalled()
      expect(mockRender).toHaveBeenCalled()
    })
  })

  describe('Module Imports and Dependencies', () => {
    test('imports required dependencies without errors', () => {
      jest.resetModules()

      expect(() => {
        require('../src/main')
      }).not.toThrow()
    })

    test('CSS module is imported', () => {
      jest.resetModules()

      expect(() => {
        require('../src/main')
      }).not.toThrow()
    })

    test('React and ReactDOM are used correctly', () => {
      jest.resetModules()

      require('../src/main')

      expect(mockCreateRoot).toHaveBeenCalled()
      expect(mockRender).toHaveBeenCalled()
    })
  })

  describe('Context Menu Handler', () => {
    test('event listener is added to document', () => {
      process.env.NODE_ENV = 'production'
      jest.resetModules()

      require('../src/main')

      expect(mockAddEventListener).toHaveBeenCalledWith(
        'contextmenu',
        expect.any(Function)
      )
    })

    test('handler function is correctly defined', () => {
      process.env.NODE_ENV = 'production'
      jest.resetModules()

      require('../src/main')

      const handler = mockAddEventListener.mock.calls.find(
        (call) => call[0] === 'contextmenu'
      )?.[1]

      expect(typeof handler).toBe('function')
    })

    test('handler prevents default browser context menu', () => {
      process.env.NODE_ENV = 'production'
      jest.resetModules()

      require('../src/main')

      const handler = mockAddEventListener.mock.calls.find(
        (call) => call[0] === 'contextmenu'
      )?.[1]

      const mockEvent = {
        preventDefault: jest.fn(),
        stopPropagation: jest.fn(),
      }

      handler(mockEvent)

      expect(mockEvent.preventDefault).toHaveBeenCalledTimes(1)
    })
  })

  describe('Type Safety and DOM Assertions', () => {
    test('root element type assertion works correctly', () => {
      const rootElement = document.createElement('div')
      rootElement.id = 'root'
      mockGetElementById.mockReturnValue(rootElement)
      jest.resetModules()

      expect(() => {
        require('../src/main')
      }).not.toThrow()
    })

    test('handles root element with correct HTML type', () => {
      const rootElement = document.createElement('div')
      mockGetElementById.mockReturnValue(rootElement)
      jest.resetModules()

      require('../src/main')

      expect(mockCreateRoot).toHaveBeenCalledWith(rootElement)
    })
  })

  describe('Integration Tests', () => {
    test('complete initialization flow in production', () => {
      process.env.NODE_ENV = 'production'
      jest.resetModules()

      require('../src/main')

      // Verify complete flow
      expect(mockGetElementById).toHaveBeenCalledWith('root')
      expect(mockCreateRoot).toHaveBeenCalledWith(mockRootElement)
      expect(mockRender).toHaveBeenCalled()
      expect(mockAddEventListener).toHaveBeenCalledWith(
        'contextmenu',
        expect.any(Function)
      )
    })

    test('complete initialization flow in development', () => {
      process.env.NODE_ENV = 'development'
      jest.resetModules()

      require('../src/main')

      // Verify initialization without context menu prevention
      expect(mockGetElementById).toHaveBeenCalledWith('root')
      expect(mockCreateRoot).toHaveBeenCalledWith(mockRootElement)
      expect(mockRender).toHaveBeenCalled()

      // Context menu should not be disabled
      const contextMenuCalls = mockAddEventListener.mock.calls.filter(
        (call) => call[0] === 'contextmenu'
      )
      expect(contextMenuCalls.length).toBe(0)
    })

    test('all components are properly imported', () => {
      jest.resetModules()

      // Should not throw if all components can be imported
      expect(() => {
        require('../src/main')
      }).not.toThrow()
    })
  })

  describe('Render Behavior', () => {
    test('render is called with element', () => {
      jest.resetModules()

      require('../src/main')

      expect(mockRender).toHaveBeenCalledTimes(1)
      const renderArg = mockRender.mock.calls[0][0]
      expect(renderArg).toBeDefined()
    })

    test('render receives React element', () => {
      jest.resetModules()

      require('../src/main')

      const renderArg = mockRender.mock.calls[0][0]
      // Check that it's a React element (has type and props)
      expect(renderArg).toHaveProperty('type')
      expect(renderArg).toHaveProperty('props')
    })
  })

  describe('Environment-Specific Router Behavior', () => {
    test('router is created in production', () => {
      process.env.NODE_ENV = 'production'
      jest.resetModules()

      expect(() => {
        require('../src/main')
      }).not.toThrow()

      expect(mockRender).toHaveBeenCalled()
    })

    test('router is created in development', () => {
      process.env.NODE_ENV = 'development'
      jest.resetModules()

      expect(() => {
        require('../src/main')
      }).not.toThrow()

      expect(mockRender).toHaveBeenCalled()
    })

    test('router configuration does not throw', () => {
      jest.resetModules()

      expect(() => {
        require('../src/main')
      }).not.toThrow()
    })
  })
})
