import '@testing-library/jest-dom'

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor(cb: any) {}
  observe() {}
  unobserve() {}
  disconnect() {}
}

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor(cb: any) {}
  observe() { return null }
  unobserve() { return null }
  disconnect() { return null }
  root = null
  rootMargin = ''
  thresholds = []
  takeRecords = () => []
}

// Mock window.electron API
global.window = Object.create(window);
Object.defineProperty(window, 'electron', {
  value: undefined,
  writable: true
})

// Mock fetch globally
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    status: 200,
    json: () => Promise.resolve({}),
    text: () => Promise.resolve(''),
    blob: () => Promise.resolve(new Blob()),
    headers: new Headers(),
  } as Response)
)

// Mock the logger module
jest.mock('../src/utils/logger', () => ({
  logger: {
    debug: jest.fn(),
    info: jest.fn(),
    warn: jest.fn(),
    error: jest.fn(),
    startPerformance: jest.fn(),
    endPerformance: jest.fn(),
    logApiCall: jest.fn(),
    logApiResponse: jest.fn(),
    logComponentMount: jest.fn(),
    logComponentUnmount: jest.fn(),
    logComponentError: jest.fn(),
    logUserAction: jest.fn(),
    generateRequestId: jest.fn(() => 'test-request-id'),
    exportLogs: jest.fn(() => ''),
    downloadLogs: jest.fn(),
    clearLogs: jest.fn(),
    getRecentLogs: jest.fn(() => []),
  }
}))

// Clean up after each test
afterEach(() => {
  jest.clearAllMocks()
})

// Suppress console errors during tests
const originalError = console.error
beforeAll(() => {
  console.error = (...args: any[]) => {
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('Warning: ReactDOM.render') ||
       args[0].includes('Warning: An update to') ||
       args[0].includes('Warning: useLayoutEffect'))
    ) {
      return
    }
    originalError.call(console, ...args)
  }
})

afterAll(() => {
  console.error = originalError
})
