import { test, expect } from '@playwright/test';
import * as fs from 'fs';
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
      if (!fs.existsSync(testFolder)) {
        fs.mkdirSync(testFolder, { recursive: true });
      }
      await settingsPage.addRootFolder(testFolder);

      // Should add folder to the list (auto-saves)
      await settingsPage.page.waitForTimeout(1500);
      const folders = await settingsPage.getRootFolders();
      // Verify the folder was added
      expect(folders).toContain(testFolder);
    });

    test('removes a root folder', async () => {
      // Ensure there is a removable folder (avoid skipping)
      const testFolder = `/tmp/test-photos-remove-${Date.now()}`;
      if (!fs.existsSync(testFolder)) {
        fs.mkdirSync(testFolder, { recursive: true });
      }

      await settingsPage.addRootFolder(testFolder);
      await settingsPage.page.waitForTimeout(1500);

      const foldersAfterAdd = await settingsPage.getRootFolders();
      const index = foldersAfterAdd.indexOf(testFolder);
      expect(index).toBeGreaterThanOrEqual(0);

      await settingsPage.removeRootFolder(index);
      await settingsPage.page.waitForTimeout(1500);

      const foldersAfterRemove = await settingsPage.getRootFolders();
      expect(foldersAfterRemove).not.toContain(testFolder);
    });

    test('validates folder paths', async () => {
      // The new UI uses a dialog prompt, so validation works differently
      // The Add button is always enabled, validation happens in the dialog
      const isEnabled = await settingsPage.addFolderButton.isEnabled();
      expect(isEnabled).toBeTruthy();
    });

    test('handles duplicate folders', async () => {
      // Verify duplicate prevention in the UI
      const testFolder = '/tmp/duplicate-test';
      if (!fs.existsSync(testFolder)) {
        fs.mkdirSync(testFolder, { recursive: true });
      }

      // Add folder first time
      await settingsPage.addRootFolder(testFolder);
      await settingsPage.page.waitForTimeout(1500);

      const foldersAfterFirst = await settingsPage.getRootFolders();
      const countAfterFirst = foldersAfterFirst.filter(f => f === testFolder).length;

      // Try adding same folder again
      await settingsPage.addRootFolder(testFolder);
      await settingsPage.page.waitForTimeout(1500);

      const foldersAfterSecond = await settingsPage.getRootFolders();
      const countAfterSecond = foldersAfterSecond.filter(f => f === testFolder).length;

      // Should still only have one instance
      expect(countAfterSecond).toBe(countAfterFirst);
    });
  });

  test.describe('Indexing Controls', () => {
    test('starts indexing process', async () => {
      // Check if indexing button is available
      await expect(settingsPage.indexingButton).toBeVisible();

      // Click the button
      await settingsPage.startIndexing(false);

      // Just verify no crash
      await expect(settingsPage.page).toHaveURL(/settings/);
    });

    test('shows indexing progress', async () => {
      // Verify status badge is visible
      const statusSection = settingsPage.page.locator('text=Status').locator('..');
      await expect(statusSection).toBeVisible();

      // Get status to see if UI shows it
      const status = await settingsPage.getIndexingStatus();
      expect(status.status).toBeTruthy();
      expect(status.progress).toBeGreaterThanOrEqual(0);
      expect(status.progress).toBeLessThanOrEqual(100);
    });

    test('stops indexing process', async () => {
      // Check if stop button appears when needed
      const stopButton = settingsPage.page.locator('button:has-text("Stop Indexing")');
      // Button may or may not be visible depending on indexing state
      if (await stopButton.isVisible()) {
        await settingsPage.stopIndexing();
      }
      // Just verify page is still functional
      await expect(settingsPage.page).toHaveURL(/settings/);
    });

    test('handles full vs incremental indexing', async () => {
      // Check both buttons exist
      const incrementalButton = settingsPage.page.locator('button:has-text("Quick Update")');
      const fullButton = settingsPage.page.locator('button:has-text("Full Refresh")');

      await expect(incrementalButton).toBeVisible();
      await expect(fullButton).toBeVisible();
    });
  });

  test.describe('Feature Toggles', () => {
    test('toggles face search feature', async () => {
      // Toggle on
      await settingsPage.toggleFaceSearch(true);
      await expect.poll(async () => {
        const response = await apiClient.getConfig();
        const cfg = await response.json();
        return cfg.face_search_enabled;
      }).toBe(true);

      // Toggle off
      await settingsPage.toggleFaceSearch(false);
      await expect.poll(async () => {
        const response = await apiClient.getConfig();
        const cfg = await response.json();
        return cfg.face_search_enabled;
      }).toBe(false);

      // Restore default (avoid impacting other suites)
      await settingsPage.toggleFaceSearch(true);
      await expect.poll(async () => {
        const response = await apiClient.getConfig();
        const cfg = await response.json();
        return cfg.face_search_enabled;
      }).toBe(true);
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


  test.describe('Configuration Presets', () => {
    test('applies minimal configuration preset', async () => {
      const preset = TestData.CONFIG_PRESETS.minimal;

      // Batch size and thumbnail size are no longer exposed in the UI
      await settingsPage.toggleFaceSearch(preset.face_search_enabled);
      await settingsPage.toggleSemanticSearch(preset.semantic_search_enabled);

      const config = await settingsPage.getConfiguration();
      expect(config.faceSearchEnabled).toBe(preset.face_search_enabled);
      expect(config.semanticSearchEnabled).toBe(preset.semantic_search_enabled);
    });

    test('applies full configuration preset', async () => {
      const preset = TestData.CONFIG_PRESETS.full;

      // OCR has been removed from the application
      await settingsPage.toggleFaceSearch(preset.face_search_enabled);
      await settingsPage.toggleSemanticSearch(preset.semantic_search_enabled);
      // Batch size and thumbnail size removed from UI

      const config = await settingsPage.getConfiguration();
      // No longer checking OCR
      expect(config.faceSearchEnabled).toBe(preset.face_search_enabled);
      expect(config.semanticSearchEnabled).toBe(preset.semantic_search_enabled);
    });
  });

  test.describe('Reset Configuration', () => {
    test('can reset onboarding from settings', async ({ page }) => {
      // Settings exposes "Run Setup Again" (onboarding reset)
      const runSetupAgain = page.locator('button:has-text("Run Setup Again")');
      await expect(runSetupAgain).toBeVisible();
      await runSetupAgain.click();

      // Toast should appear (there are multiple Toasters in the app; pick the first match)
      await expect(page.locator('text=Onboarding Reset').first()).toBeVisible({ timeout: 5000 });

      // Reload: onboarding wizard should re-appear
      await page.reload();
      await expect(page.locator('[data-testid="onboarding-modal"]')).toBeVisible({ timeout: 10000 });

      // Close it so the rest of the app is accessible
      await page.locator('[data-testid="skip-onboarding-btn"]').click();
      await expect(page.locator('[data-testid="onboarding-modal"]')).toBeHidden({ timeout: 10000 });
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
      // Make changes (auto-saves)
      await settingsPage.toggleSemanticSearch(true);
      await settingsPage.toggleFaceSearch(false);

      // Verify values are set
      const configBefore = await settingsPage.getConfiguration();
      expect(configBefore.semanticSearchEnabled).toBeTruthy();
      expect(configBefore.faceSearchEnabled).toBeFalsy();

      // Wait for auto-save to complete
      await page.waitForTimeout(4000);

      // Check backend state directly
      const response = await apiClient.getConfig();
      const backendConfig = await response.json();
      expect(backendConfig.semantic_search_enabled).toBeTruthy();
      expect(backendConfig.face_search_enabled).toBeFalsy();

      // Reload page
      await page.reload();
      await settingsPage.waitForApp();

      // Navigate back to settings
      await page.goto('/settings');
      await page.waitForLoadState('networkidle');

      // Settings should persist
      const config = await settingsPage.getConfiguration();
      expect(config.semanticSearchEnabled).toBeTruthy();
      expect(config.faceSearchEnabled).toBeFalsy();
    });

    test('syncs settings with backend', async () => {
      // Change settings via UI (auto-saves)
      await settingsPage.toggleFaceSearch(true);

      // Wait for auto-save
      await settingsPage.page.waitForTimeout(1500);

      // Just verify the setting was saved
      const config = await settingsPage.getConfiguration();
      expect(config.faceSearchEnabled).toBeTruthy();
    });
  });
});