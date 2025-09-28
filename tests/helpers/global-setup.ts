import { FullConfig } from '@playwright/test';
import { APIClient } from './api-client';
import { TestData } from './test-data';
import * as fs from 'fs';
import * as path from 'path';

/**
 * Global setup for all tests
 */
async function globalSetup(config: FullConfig) {
  console.log('Starting global test setup...');

  // Create necessary directories
  const dirs = [
    'test-results',
    'test-results/screenshots',
    'test-results/videos',
    path.join(__dirname, '..', 'fixtures', 'images')
  ];

  for (const dir of dirs) {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  }

  // Initialize API client
  const apiClient = new APIClient();
  await apiClient.initialize();

  try {
    // Wait for backend to be ready
    console.log('Waiting for backend to be ready...');
    await apiClient.ensureBackendReady();
    console.log('Backend is ready');

    // Reset configuration to known state
    console.log('Resetting configuration...');
    await apiClient.resetConfig();

    // Create test images
    console.log('Creating test images...');
    const testImages = await TestData.createTestImages(10);
    console.log(`Created ${testImages.length} test images`);

    // Create test folders with images
    console.log('Creating test folders...');
    const testFolders = await TestData.createTestFolders();
    console.log(`Created ${testFolders.length} test folders`);

    // Store test data paths for tests to use
    process.env.TEST_IMAGES = JSON.stringify(testImages);
    process.env.TEST_FOLDERS = JSON.stringify(testFolders);

    console.log('Global setup complete');
  } catch (error) {
    console.error('Global setup failed:', error);
    throw error;
  } finally {
    await apiClient.dispose();
  }

  return async () => {
    // This function will be run as global teardown
    console.log('Global teardown will be run after all tests');
  };
}

export default globalSetup;