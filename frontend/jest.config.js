module.exports = {
  testEnvironment: 'jsdom',
  testEnvironmentOptions: {
    url: 'http://example.com/',
  },
  preset: 'ts-jest',
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json'],
  transform: {
    '^.+\\.(ts|tsx)$': ['ts-jest', {
      tsconfig: '<rootDir>/tsconfig.test.json',
      diagnostics: false,
    }],
  },
  moduleNameMapper: {
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    '^@/(.*)$': '<rootDir>/src/$1',
    '.*config/constants$': '<rootDir>/tests/mocks/constants.ts',
  },
  testMatch: [
    '<rootDir>/tests/**/*.(test|spec).(ts|tsx|js|jsx)',
    '<rootDir>/src/**/*.(test|spec).(ts|tsx|js|jsx)',
  ],
  collectCoverageFrom: [
    'src/**/*.(ts|tsx|js|jsx)',
    // Exclude files that don't need unit tests
    '!src/**/*.d.ts',                    // Type definitions
    '!src/main.tsx',                      // Entry point (integration test territory)
    '!src/App.tsx',                       // Router config (E2E territory)
    '!src/vite-env.d.ts',                // Vite types
    '!src/types/**',                     // Type definitions directory
    '!src/components/ui/**',              // Third-party UI library (shadcn/ui)
    '!src/lib/*-variants.ts',            // CSS variant definitions
    '!src/utils/logger.ts',              // Logger uses import.meta incompatible with Jest, mocked globally
    '!src/config/**',                    // Configuration constants
    '!src/config/',                      // Config files
    // Pure presentational components (no business logic)
    '!src/components/VirtualGrid/LoadingSkeleton.tsx',
    '!src/components/VirtualGrid/VirtualGridItem.tsx',
    '!src/components/Lightbox/LightboxNavigation.tsx',
    '!src/components/Lightbox/LightboxImage.tsx',
    '!src/components/Lightbox/LightboxMetadata.tsx',
    '!src/components/OnboardingWizard/WelcomeStep.tsx',
    '!src/components/OnboardingWizard/CompleteStep.tsx',
  ],
  moduleDirectories: ['node_modules', '<rootDir>/'],
  testPathIgnorePatterns: [
    '<rootDir>/tests/e2e/',
    '<rootDir>/node_modules/',
    '<rootDir>/dist',
    '<rootDir>/dist-electron'
  ],
  coverageThreshold: {
    global: {
      statements: 80,
      branches: 75,
      functions: 80,
      lines: 80,
    },
  },
  setupFilesAfterEnv: ['<rootDir>/tests/setupTests.ts'],
  reporters: [
    'default',
    ['jest-junit', {
      outputDirectory: '<rootDir>/test-results',  // Relative to rootDir (frontend/)
      outputName: 'junit-20.xml',  // Matches Node version 20
      classNameTemplate: '{filepath}',
      titleTemplate: '{title}',
      ancestorSeparator: ' > ',
      usePathForSuiteName: true,
    }],
  ],
};
