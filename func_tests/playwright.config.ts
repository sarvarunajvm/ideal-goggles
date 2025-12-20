import { defineConfig, devices } from '@playwright/test';
import * as path from 'path';

/**
 * Playwright configuration for integration tests
 * Tests the complete Ideal Goggles application including frontend and backend
 */
const useExistingServer = !!process.env.USE_EXISTING_SERVER;

export default defineConfig({
  testDir: './e2e',

  /* Maximum time one test can run for */
  timeout: 60 * 1000,

  /* Run tests in files in parallel */
  fullyParallel: false,

  /* Fail the build on CI if you accidentally left test.only in the source code */
  forbidOnly: !!process.env.CI,

  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,

  /* Opt out of parallel tests on CI */
  workers: 1,

  /* Reporter to use */
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
    ['blob', { outputDir: 'blob-report' }],
    ['list']
  ],

  /* Shared settings for all the projects below */
  use: {
    /* Base URL to use in actions like `await page.goto('/')` */
    // Use 127.0.0.1 to avoid IPv6 ::1 resolution issues (Vite/uvicorn may bind differently).
    baseURL: 'http://127.0.0.1:3333',

    /* Collect trace when retrying the failed test */
    trace: 'on-first-retry',

    /* Capture screenshot on failure */
    screenshot: 'only-on-failure',

    /* Record video on failure */
    video: 'retain-on-failure',

    /* Maximum time each action can take */
    actionTimeout: 15 * 1000,

    /* Viewport size */
    viewport: { width: 1280, height: 720 },
  },

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    }
  ],

  /* Folder for test artifacts such as screenshots, videos, traces, etc. */
  outputDir: 'test-results/',

  /* Run your local dev server before starting the tests */
  webServer: useExistingServer
    ? undefined
    : [
        {
          // Use exec so Playwright can reliably terminate the dev server (avoid orphaned vite processes)
          command:
            'cd .. && exec node node_modules/vite/bin/vite.js --config frontend/vite.config.ts --host 127.0.0.1 --port 3333',
          // Use explicit URL (127.0.0.1) so we don't get tripped up by an unrelated ::1 listener on localhost
          url: 'http://127.0.0.1:3333',
          timeout: 120 * 1000,
          reuseExistingServer: !!process.env.REUSE_EXISTING_SERVER,
        },
        {
          // Use exec so Playwright can reliably terminate the backend (avoid orphaned python processes)
          command: 'cd ../backend && python3 init_test_db.py && exec python3 -m src.main',
          // Use explicit URL (127.0.0.1) for the same reason as above
          url: 'http://127.0.0.1:5555/health',
          timeout: 120 * 1000,
          reuseExistingServer: !!process.env.REUSE_EXISTING_SERVER,
          env: {
            DATABASE_URL: 'sqlite+aiosqlite:///test_data/photos.db',
            // Enable backend test-mode hooks (e.g. predictable People enrollment without real faces)
            E2E_TEST: '1',
            // Ensure backend settings parsing isn't broken by Playwright/Node DEBUG envs
            DEBUG: 'false',
          },
        },
      ],

  /* Global setup and teardown */
  globalSetup: path.join(__dirname, 'helpers', 'global-setup.ts'),
  globalTeardown: path.join(__dirname, 'helpers', 'global-teardown.ts'),
});
