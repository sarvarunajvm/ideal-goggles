import '@testing-library/jest-dom'

// Polyfill for TextEncoder/TextDecoder (required for React Router in Jest)
import { TextEncoder, TextDecoder } from 'util'
global.TextEncoder = TextEncoder
global.TextDecoder = TextDecoder as any

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor(_cb: any) {}
  observe() {}
  unobserve() {}
  disconnect() {}
}

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor(_cb: any) {}
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

// Polyfill minimal Request for react-router data APIs
// JSDOM does not include the full fetch API Request by default in this setup
;(global as any).Request = (global as any).Request || class Request {
  constructor(..._args: any[]) {}
}

// Ensure timers are available globally
global.setInterval = global.setInterval || jest.fn()
global.clearInterval = global.clearInterval || jest.fn()
global.setTimeout = global.setTimeout || jest.fn()
global.clearTimeout = global.clearTimeout || jest.fn()

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
