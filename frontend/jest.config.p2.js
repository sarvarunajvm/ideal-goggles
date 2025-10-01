/**
 * Jest configuration for P2 (Nice-to-have) tests
 * These tests run in full CI/CD pipeline
 */

module.exports = {
  displayName: 'P2-Nice-to-have',
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
  // P2 tests - pages and integration tests
  testMatch: [
    '**/tests/pages/*.test.tsx',
    '**/tests/integration/*.test.ts',
    '**/tests/basic.test.js'
  ]
}