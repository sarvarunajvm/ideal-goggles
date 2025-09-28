import { FullConfig } from '@playwright/test';
import { TestData } from './test-data';
import { APIClient } from './api-client';

/**
 * Global teardown for all tests
 */
async function globalTeardown(config: FullConfig) {
  console.log('Starting global test teardown...');

  try {
    // Clean up test folders
    console.log('Cleaning up test folders...');
    await TestData.cleanupTestFolders();

    // Clean up fixtures
    console.log('Cleaning up fixtures...');
    await TestData.cleanupFixtures();

    // Reset backend configuration
    const apiClient = new APIClient();
    await apiClient.initialize();

    try {
      console.log('Resetting backend configuration...');
      await apiClient.resetConfig();
    } catch (error) {
      console.warn('Failed to reset backend configuration:', error);
    } finally {
      await apiClient.dispose();
    }

    console.log('Global teardown complete');
  } catch (error) {
    console.error('Global teardown failed:', error);
    // Don't throw - we still want test results even if cleanup fails
  }
}

export default globalTeardown;