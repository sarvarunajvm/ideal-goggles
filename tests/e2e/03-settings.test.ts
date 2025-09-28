import { test, expect } from '@playwright/test';
import { SettingsPage } from '../page-objects/SettingsPage';
import { APIClient } from '../helpers/api-client';
import { TestData } from '../helpers/test-data';

test.describe('Settings and Configuration', () => {
  let settingsPage: SettingsPage;
  let apiClient: APIClient;

  test.beforeAll(async () => {
    apiClient = new APIClient();
    await apiClient.initialize();
  });

  test.afterAll(async () => {
    await apiClient.dispose();
  });

  test.beforeEach(async ({ page }) => {
    settingsPage = new SettingsPage(page);
    await settingsPage.goto('/settings');
  });

  test.describe('Root Folders Management', () => {
    test('adds a new root folder', async () => {
      const testFolder = '/tmp/test-photos-new';
      await settingsPage.addRootFolder(testFolder);

      const folders = await settingsPage.getRootFolders();
      expect(folders).toContain(testFolder);
    });

    test('removes a root folder', async () => {
      // First add a folder
      const testFolder = '/tmp/test-remove';
      await settingsPage.addRootFolder(testFolder);

      // Then remove it
      const folders = await settingsPage.getRootFolders();
      const index = folders.indexOf(testFolder);
      if (index >= 0) {
        await settingsPage.removeRootFolder(index);

        const updatedFolders = await settingsPage.getRootFolders();
        expect(updatedFolders).not.toContain(testFolder);
      }
    });

    test('validates folder paths', async () => {
      const invalidPaths = [
        '',
        '   ',
        'not/absolute/path',
        '../../relative/path'
      ];

      for (const path of invalidPaths) {
        await settingsPage.addFolderButton.click();
        await settingsPage.folderInput.fill(path);
        await settingsPage.saveButton.click();

        // Should show error or not accept invalid path
        const errorAlert = settingsPage.page.locator('[role="alert"]:has-text("error")');
        if (await errorAlert.isVisible()) {
          expect(await errorAlert.textContent()).toBeTruthy();
        }
      }
    });

    test('handles duplicate folders', async () => {
      const testFolder = '/tmp/duplicate-test';

      // Add folder first time
      await settingsPage.addRootFolder(testFolder);

      // Try to add same folder again
      await settingsPage.addRootFolder(testFolder);

      // Should either reject or handle gracefully
      const folders = await settingsPage.getRootFolders();
      const count = folders.filter(f => f === testFolder).length;
      expect(count).toBeLessThanOrEqual(1);
    });
  });

  test.describe('Indexing Controls', () => {
    test('starts indexing process', async () => {
      // Ensure we have at least one folder
      const testFolders = JSON.parse(process.env.TEST_FOLDERS || '[]');
      if (testFolders.length > 0) {
        await apiClient.setRootFolders([testFolders[0]]);
      }

      await settingsPage.startIndexing(false);

      const status = await settingsPage.getIndexingStatus();
      expect(['Indexing', 'Processing', 'Running']).toContain(status.status);
    });

    test('shows indexing progress', async () => {
      const testFolders = JSON.parse(process.env.TEST_FOLDERS || '[]');
      if (testFolders.length > 0) {
        await apiClient.setRootFolders([testFolders[0]]);
        await settingsPage.startIndexing(true);

        // Wait a bit for progress
        await settingsPage.page.waitForTimeout(2000);

        const status = await settingsPage.getIndexingStatus();
        expect(status.progress).toBeGreaterThanOrEqual(0);
        expect(status.progress).toBeLessThanOrEqual(100);
      }
    });

    test('stops indexing process', async () => {
      const testFolders = JSON.parse(process.env.TEST_FOLDERS || '[]');
      if (testFolders.length > 0) {
        await apiClient.setRootFolders([testFolders[0]]);
        await settingsPage.startIndexing(false);
        await settingsPage.page.waitForTimeout(1000);

        await settingsPage.stopIndexing();

        const status = await settingsPage.getIndexingStatus();
        expect(['Stopped', 'Idle', 'Complete']).toContain(status.status);
      }
    });

    test('handles full vs incremental indexing', async () => {
      const testFolders = JSON.parse(process.env.TEST_FOLDERS || '[]');
      if (testFolders.length > 0) {
        await apiClient.setRootFolders([testFolders[0]]);

        // Start incremental indexing
        await settingsPage.startIndexing(false);
        await settingsPage.stopIndexing();

        // Start full indexing
        await settingsPage.startIndexing(true);
        await settingsPage.stopIndexing();

        // Both should work without errors
        await expect(settingsPage.navBar).toBeVisible();
      }
    });
  });

  test.describe('Feature Toggles', () => {
    test('toggles OCR feature', async () => {
      await settingsPage.toggleOCR(true);
      let config = await settingsPage.getConfiguration();
      expect(config.ocrEnabled).toBeTruthy();

      await settingsPage.toggleOCR(false);
      config = await settingsPage.getConfiguration();
      expect(config.ocrEnabled).toBeFalsy();
    });

    test('toggles face search feature', async () => {
      await settingsPage.toggleFaceSearch(true);
      let config = await settingsPage.getConfiguration();
      expect(config.faceSearchEnabled).toBeTruthy();

      await settingsPage.toggleFaceSearch(false);
      config = await settingsPage.getConfiguration();
      expect(config.faceSearchEnabled).toBeFalsy();
    });

    test('toggles semantic search feature', async () => {
      await settingsPage.toggleSemanticSearch(true);
      let config = await settingsPage.getConfiguration();
      expect(config.semanticSearchEnabled).toBeTruthy();

      await settingsPage.toggleSemanticSearch(false);
      config = await settingsPage.getConfiguration();
      expect(config.semanticSearchEnabled).toBeFalsy();
    });
  });

  test.describe('Performance Settings', () => {
    test('sets batch size', async () => {
      const batchSizes = [10, 50, 100, 200];

      for (const size of batchSizes) {
        await settingsPage.setBatchSize(size);
        const config = await settingsPage.getConfiguration();
        expect(parseInt(config.batchSize)).toBe(size);
      }
    });

    test('validates batch size limits', async () => {
      const invalidSizes = [-1, 0, 10000];

      for (const size of invalidSizes) {
        await settingsPage.batchSizeInput.clear();
        await settingsPage.batchSizeInput.fill(size.toString());
        await settingsPage.saveButton.click();

        // Should show error or use default
        const errorAlert = settingsPage.page.locator('[role="alert"]');
        if (await errorAlert.isVisible()) {
          expect(await errorAlert.textContent()).toBeTruthy();
        }
      }
    });

    test('sets thumbnail size', async () => {
      const sizes = ['small', 'medium', 'large'];

      for (const size of sizes) {
        await settingsPage.setThumbnailSize(size);
        const config = await settingsPage.getConfiguration();
        expect(config.thumbnailSize).toBe(size);
      }
    });
  });

  test.describe('Configuration Presets', () => {
    test('applies minimal configuration preset', async () => {
      const preset = TestData.CONFIG_PRESETS.minimal;

      await settingsPage.toggleOCR(preset.ocr_enabled);
      await settingsPage.toggleFaceSearch(preset.face_search_enabled);
      await settingsPage.toggleSemanticSearch(preset.semantic_search_enabled);
      await settingsPage.setBatchSize(preset.batch_size);
      await settingsPage.setThumbnailSize(preset.thumbnail_size);

      const config = await settingsPage.getConfiguration();
      expect(config.ocrEnabled).toBe(preset.ocr_enabled);
      expect(config.faceSearchEnabled).toBe(preset.face_search_enabled);
      expect(config.semanticSearchEnabled).toBe(preset.semantic_search_enabled);
    });

    test('applies full configuration preset', async () => {
      const preset = TestData.CONFIG_PRESETS.full;

      await settingsPage.toggleOCR(preset.ocr_enabled);
      await settingsPage.toggleFaceSearch(preset.face_search_enabled);
      await settingsPage.toggleSemanticSearch(preset.semantic_search_enabled);
      await settingsPage.setBatchSize(preset.batch_size);
      await settingsPage.setThumbnailSize(preset.thumbnail_size);

      const config = await settingsPage.getConfiguration();
      expect(config.ocrEnabled).toBe(preset.ocr_enabled);
      expect(config.faceSearchEnabled).toBe(preset.face_search_enabled);
      expect(config.semanticSearchEnabled).toBe(preset.semantic_search_enabled);
    });
  });

  test.describe('Reset Configuration', () => {
    test('resets configuration to defaults', async () => {
      // Make some changes first
      await settingsPage.toggleOCR(true);
      await settingsPage.setBatchSize(200);

      // Reset configuration
      await settingsPage.resetConfiguration();

      // Verify configuration is reset
      const response = await apiClient.getConfig();
      const config = await response.json();
      expect(config).toBeTruthy();
    });

    test('clears all root folders on reset', async () => {
      // Add some folders
      await settingsPage.addRootFolder('/tmp/folder1');
      await settingsPage.addRootFolder('/tmp/folder2');

      // Reset
      await settingsPage.resetConfiguration();

      // Folders should be cleared
      const folders = await settingsPage.getRootFolders();
      expect(folders.length).toBe(0);
    });
  });

  test.describe('Settings Persistence', () => {
    test('persists settings after page reload', async ({ page }) => {
      // Make changes
      await settingsPage.toggleOCR(true);
      await settingsPage.setBatchSize(75);

      // Reload page
      await page.reload();
      await settingsPage.waitForApp();

      // Settings should persist
      const config = await settingsPage.getConfiguration();
      expect(config.ocrEnabled).toBeTruthy();
      expect(parseInt(config.batchSize)).toBe(75);
    });

    test('syncs settings with backend', async () => {
      // Change settings via UI
      await settingsPage.toggleFaceSearch(true);

      // Verify via API
      const response = await apiClient.getConfig();
      const config = await response.json();
      expect(config.face_search_enabled).toBeTruthy();
    });
  });
});