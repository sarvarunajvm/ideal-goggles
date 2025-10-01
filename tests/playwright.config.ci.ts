import { defineConfig } from '@playwright/test';
import baseConfig from './playwright.config';

/**
 * CI-specific Playwright configuration
 * Runs only P0 (critical) tests for faster CI/CD
 */
export default defineConfig({
  ...baseConfig,

  // CI-specific overrides
  testDir: './e2e',

  // Only run P0 tests in CI
  grep: /@P0/,

  // Faster timeout for CI
  timeout: 30 * 1000,

  // Less retries in CI
  retries: 1,

  // Single worker for stability
  workers: 1,

  // No parallel execution in CI
  fullyParallel: false,

  // Simpler reporter for CI
  reporter: [
    ['list'],
    ['junit', { outputFile: 'test-results/junit.xml' }],
    ['html', { outputFolder: 'playwright-report', open: 'never' }]
  ],

  // Only test on Chromium in CI for speed
  projects: [
    {
      name: 'chromium',
      use: {
        ...baseConfig.projects[0].use,
        screenshot: 'only-on-failure',
        video: 'retain-on-failure',
        trace: 'on-first-retry',
      },
    },
  ],

  // CI optimizations
  use: {
    ...baseConfig.use,
    actionTimeout: 10 * 1000,
    navigationTimeout: 20 * 1000,
  },
});