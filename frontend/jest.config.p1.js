/**
 * Jest configuration for P1 (Important) tests
 * These tests run in standard CI
 */

module.exports = {
  displayName: 'P1-Important',
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
  // P1 tests
  testMatch: [
    '**/tests/utils/logger.test.ts',
    '**/tests/services/osIntegration.test.ts',
    '**/tests/components/PhotoGrid.test.tsx',
    '**/tests/components/SearchPage.test.tsx'
  ]
}