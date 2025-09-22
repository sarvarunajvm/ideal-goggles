/**
 * Global teardown for end-to-end tests
 */

import { FullConfig } from '@playwright/test';

async function globalTeardown(config: FullConfig) {
  console.log('Cleaning up global test environment...');

  try {
    // Clean up test data
    await cleanupTestData();

    // Close any persistent connections
    // (Playwright handles browser cleanup automatically)

    console.log('Global teardown completed');
  } catch (error) {
    console.error('Global teardown failed:', error);
    // Don't throw - we want tests to complete even if cleanup fails
  }
}

async function cleanupTestData() {
  // Clean up any test data created during setup
  console.log('Cleaning up test data...');

  // This could include:
  // - Removing test photo library
  // - Cleaning test database
  // - Resetting test configuration
  // For now, we don't have persistent test data to clean up
}

export default globalTeardown;