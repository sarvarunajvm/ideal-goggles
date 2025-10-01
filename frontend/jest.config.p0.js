/**
 * Jest configuration for P0 (Critical) tests
 * These tests run in quick CI and must pass for deployment
 */

module.exports = {
  displayName: 'P0-Critical',
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  roots: ['<rootDir>'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@shared/(.*)$': '<rootDir>/../shared/$1',
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    '\\.(jpg|jpeg|png|gif|svg)$': '<rootDir>/tests/__mocks__/fileMock.js'
  },
  setupFilesAfterEnv: ['<rootDir>/tests/setup.ts'],
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/main.tsx',
    '!src/vite-env.d.ts'
  ],
  coverageThreshold: {
    global: {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90
    }
  },
  globals: {
    'import.meta': {
      env: {
        DEV: false,
        VITE_LOG_LEVEL: 'INFO'
      }
    }
  },
  // Only run P0 tests
  testMatch: [
    '**/tests/services/apiClient.test.ts',
    '**/tests/components/App.test.tsx',
    '**/tests/components/SearchBar.test.tsx',
    '**/tests/components/ResultsGrid.test.tsx'
  ],
  // Fail fast on first test failure in CI
  bail: process.env.CI ? 1 : 0,
  // Verbose output in CI
  verbose: process.env.CI ? true : false
}