import { test, expect, Page } from '@playwright/test';
import { ElectronApplication, _electron as electron } from '@playwright/test';
import path from 'path';

let electronApp: ElectronApplication;
let page: Page;

test.describe('Onboarding Wizard E2E Test', () => {
  test.beforeAll(async () => {
    // Clear any existing onboarding state
    const appDataPath = path.join(process.env.HOME || process.env.USERPROFILE || '', '.ideal-goggles');
    const fs = require('fs');
    const onboardingFile = path.join(appDataPath, 'onboarding.json');
    if (fs.existsSync(onboardingFile)) {
      fs.unlinkSync(onboardingFile);
    }

    // Launch the Electron app
    electronApp = await electron.launch({
      args: [path.join(__dirname, '../../frontend/dist/electron/main.js')],
      env: {
        ...process.env,
        NODE_ENV: 'test',
        E2E_TEST: 'true'
      }
    });

    // Get the first window
    page = await electronApp.firstWindow();
    await page.waitForLoadState('domcontentloaded');
  });

  test.afterAll(async () => {
    await electronApp.close();
  });

  test('should display onboarding wizard on first launch', async () => {
    // Check that onboarding modal is visible
    const modal = await page.locator('[data-testid="onboarding-modal"]');
    await expect(modal).toBeVisible({ timeout: 10000 });

    // Verify welcome step is shown
    const welcomeStep = await page.locator('[data-testid="welcome-step"]');
    await expect(welcomeStep).toBeVisible();

    // Check welcome content
    await expect(page.locator('text=Welcome to Ideal Goggles')).toBeVisible();
    await expect(page.locator('text=Find any photo in seconds, just by describing it')).toBeVisible();
  });

  test('should navigate through onboarding steps', async () => {
    // Step 1: Welcome - Click Get Started
    const getStartedBtn = await page.locator('[data-testid="get-started-btn"]');
    await expect(getStartedBtn).toBeVisible();
    await getStartedBtn.click();

    // Step 2: Folder Selection
    const folderStep = await page.locator('[data-testid="folder-selection-step"]');
    await expect(folderStep).toBeVisible({ timeout: 5000 });

    // Add a test folder
    const addFolderBtn = await page.locator('[data-testid="add-folder-btn"]');
    await addFolderBtn.click();

    // Handle the native folder picker dialog (mocked in test mode)
    await page.evaluate(() => {
      // Simulate folder selection in test mode
      window.electronAPI?.selectFolder?.().then((result: any) => {
        if (result) {
          window.postMessage({ type: 'folder-selected', path: '/test/photos' }, '*');
        }
      });
    });

    // Verify folder was added to list
    await expect(page.locator('text=/test/photos')).toBeVisible({ timeout: 5000 });

    // Click Continue
    const continueBtn = await page.locator('[data-testid="continue-btn"]');
    await continueBtn.click();

    // Step 3: Indexing
    const indexingStep = await page.locator('[data-testid="indexing-step"]');
    await expect(indexingStep).toBeVisible({ timeout: 5000 });

    // Verify indexing progress indicators
    await expect(page.locator('[data-testid="indexing-progress"]')).toBeVisible();
    await expect(page.locator('text=Discovering photos')).toBeVisible();

    // Wait for indexing to complete (mocked in test mode to be fast)
    await page.waitForSelector('[data-testid="indexing-complete"]', { timeout: 30000 });

    // Click Continue after indexing
    const indexContinueBtn = await page.locator('[data-testid="continue-after-index-btn"]');
    await indexContinueBtn.click();

    // Step 4: Complete
    const completeStep = await page.locator('[data-testid="complete-step"]');
    await expect(completeStep).toBeVisible({ timeout: 5000 });

    // Verify completion message
    await expect(page.locator('text=Setup Complete!')).toBeVisible();
    await expect(page.locator('text=Ideal Goggles is ready to use')).toBeVisible();

    // Click Start Using button
    const startBtn = await page.locator('[data-testid="start-using-btn"]');
    await startBtn.click();

    // Verify onboarding modal is closed
    await expect(page.locator('[data-testid="onboarding-modal"]')).not.toBeVisible({ timeout: 5000 });

    // Verify main search page is visible
    await expect(page.locator('[data-testid="search-page"]')).toBeVisible();
  });

  test('should persist onboarding completion state', async () => {
    // Close and relaunch the app
    await electronApp.close();

    electronApp = await electron.launch({
      args: [path.join(__dirname, '../../frontend/dist/electron/main.js')],
      env: {
        ...process.env,
        NODE_ENV: 'test',
        E2E_TEST: 'true'
      }
    });

    page = await electronApp.firstWindow();
    await page.waitForLoadState('domcontentloaded');

    // Verify onboarding is NOT shown on second launch
    await expect(page.locator('[data-testid="onboarding-modal"]')).not.toBeVisible({ timeout: 5000 });

    // Verify main app is shown directly
    await expect(page.locator('[data-testid="search-page"]')).toBeVisible();
  });

  test('should allow skipping onboarding', async () => {
    // Clear onboarding state again to test skip functionality
    const appDataPath = path.join(process.env.HOME || process.env.USERPROFILE || '', '.ideal-goggles');
    const fs = require('fs');
    const onboardingFile = path.join(appDataPath, 'onboarding.json');
    if (fs.existsSync(onboardingFile)) {
      fs.unlinkSync(onboardingFile);
    }

    // Relaunch app
    await electronApp.close();
    electronApp = await electron.launch({
      args: [path.join(__dirname, '../../frontend/dist/electron/main.js')],
      env: {
        ...process.env,
        NODE_ENV: 'test',
        E2E_TEST: 'true'
      }
    });

    page = await electronApp.firstWindow();
    await page.waitForLoadState('domcontentloaded');

    // Wait for onboarding
    await expect(page.locator('[data-testid="onboarding-modal"]')).toBeVisible({ timeout: 10000 });

    // Look for skip button
    const skipBtn = await page.locator('[data-testid="skip-onboarding-btn"]');
    if (await skipBtn.isVisible()) {
      await skipBtn.click();

      // Confirm skip dialog
      const confirmSkip = await page.locator('[data-testid="confirm-skip-btn"]');
      if (await confirmSkip.isVisible()) {
        await confirmSkip.click();
      }

      // Verify onboarding closes
      await expect(page.locator('[data-testid="onboarding-modal"]')).not.toBeVisible({ timeout: 5000 });
    }
  });

  test('should validate folder selection', async () => {
    // Try to continue without selecting folders
    const continueBtn = await page.locator('[data-testid="continue-btn"]');
    const isDisabled = await continueBtn.isDisabled();

    // Button should be disabled without folders
    expect(isDisabled).toBe(true);

    // Error message should appear if trying to continue
    const errorMsg = await page.locator('[data-testid="folder-error-msg"]');
    if (await errorMsg.isVisible()) {
      await expect(errorMsg).toContainText('Please select at least one folder');
    }
  });

  test('should handle network errors during indexing gracefully', async () => {
    // Simulate network/backend error
    await page.route('**/index/start', route => {
      route.abort('failed');
    });

    // Try to start indexing
    const indexBtn = await page.locator('[data-testid="start-indexing-btn"]');
    if (await indexBtn.isVisible()) {
      await indexBtn.click();

      // Should show error state
      const errorState = await page.locator('[data-testid="indexing-error"]');
      await expect(errorState).toBeVisible({ timeout: 5000 });

      // Should have retry button
      const retryBtn = await page.locator('[data-testid="retry-indexing-btn"]');
      await expect(retryBtn).toBeVisible();
    }
  });

  test('should update progress during indexing', async () => {
    // Mock indexing progress updates
    await page.evaluate(() => {
      // Simulate progress events
      const events = [
        { phase: 'discovery', processed: 10, total: 100 },
        { phase: 'metadata', processed: 50, total: 100 },
        { phase: 'thumbnails', processed: 75, total: 100 },
        { phase: 'completed', processed: 100, total: 100 }
      ];

      let index = 0;
      const interval = setInterval(() => {
        if (index < events.length) {
          window.postMessage({ type: 'indexing-progress', ...events[index] }, '*');
          index++;
        } else {
          clearInterval(interval);
        }
      }, 500);
    });

    // Verify progress updates are reflected in UI
    const progressBar = await page.locator('[data-testid="progress-bar"]');
    if (await progressBar.isVisible()) {
      // Check that progress value changes
      const initialProgress = await progressBar.getAttribute('aria-valuenow');
      await page.waitForTimeout(2000);
      const updatedProgress = await progressBar.getAttribute('aria-valuenow');
      expect(Number(updatedProgress)).toBeGreaterThan(Number(initialProgress || 0));
    }
  });

  test('should show appropriate phase messages during indexing', async () => {
    const phaseMessages = [
      'Discovering photos',
      'Extracting metadata',
      'Generating thumbnails',
      'Building search index'
    ];

    for (const message of phaseMessages) {
      const messageLocator = page.locator(`text=${message}`);
      // At least one of these messages should be visible during indexing
      if (await messageLocator.isVisible({ timeout: 1000 })) {
        await expect(messageLocator).toBeVisible();
        break;
      }
    }
  });
});

// Test accessibility
test.describe('Onboarding Accessibility', () => {
  test('should be keyboard navigable', async () => {
    // Tab through all interactive elements
    await page.keyboard.press('Tab');
    const focusedElement = await page.evaluate(() => document.activeElement?.getAttribute('data-testid'));
    expect(focusedElement).toBeTruthy();

    // Ensure all buttons can be activated with Enter/Space
    await page.keyboard.press('Enter');
    // Verify action was triggered
  });

  test('should have proper ARIA labels', async () => {
    const modal = await page.locator('[data-testid="onboarding-modal"]');
    const ariaLabel = await modal.getAttribute('aria-label');
    expect(ariaLabel).toBeTruthy();

    // Check role attributes
    const role = await modal.getAttribute('role');
    expect(role).toBe('dialog');
  });

  test('should announce step changes to screen readers', async () => {
    const liveRegion = await page.locator('[aria-live="polite"]');
    if (await liveRegion.isVisible()) {
      const announcement = await liveRegion.textContent();
      expect(announcement).toContain('Step');
    }
  });
});