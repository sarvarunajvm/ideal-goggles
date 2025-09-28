/**
 * Global setup for end-to-end tests
 */

import { chromium, FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  console.log('Setting up global test environment...');

  // Launch browser to verify services are running
  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // Wait for frontend to be ready
    await page.goto('http://localhost:5173', { waitUntil: 'networkidle' });
    console.log('Frontend is ready');

    // Check if backend is responding
    try {
      const response = await page.request.get('http://localhost:55555/health');
      if (response.ok()) {
        console.log('Backend is ready');
      } else {
        console.warn('Backend health check failed, but continuing with tests');
      }
    } catch (error) {
      console.warn('Backend not available, tests will use mocked APIs');
    }

    // Set up test data if needed
    await setupTestData(page);

  } catch (error) {
    console.error('Global setup failed:', error);
    throw error;
  } finally {
    await browser.close();
  }
}

async function setupTestData(page: any) {
  // Create test database or seed data if needed
  console.log('Setting up test data...');

  // This could include:
  // - Creating test photo library
  // - Setting up test users
  // - Initializing test configuration
  // For now, we'll rely on mocked APIs in individual tests
}

export default globalSetup;
