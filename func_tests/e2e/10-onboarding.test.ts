import { test, expect } from '@playwright/test';

test.describe('Onboarding Wizard E2E Test', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to app
    await page.goto('/');
    
    // Clear localStorage to force onboarding
    await page.evaluate(() => {
      localStorage.clear();
    });
    
    // Reload to apply cleared storage
    await page.reload();
    await page.waitForLoadState('domcontentloaded');
  });

  test('should display onboarding wizard on first launch', async ({ page }) => {
    // Check that onboarding modal is visible
    const modal = page.locator('[data-testid="onboarding-modal"]');
    await expect(modal).toBeVisible({ timeout: 10000 });

    // Verify welcome step is shown
    const welcomeStep = page.locator('[data-testid="welcome-step"]');
    await expect(welcomeStep).toBeVisible();

    // Check welcome content
    await expect(page.locator('text=Welcome to Ideal Goggles')).toBeVisible();
    await expect(page.locator('text=Find any photo in seconds, just by describing it')).toBeVisible();
  });

  test('should navigate through onboarding steps', async ({ page }) => {
    // Step 1: Welcome - Click Get Started
    const getStartedBtn = page.locator('[data-testid="get-started-btn"]');
    await expect(getStartedBtn).toBeVisible();
    await getStartedBtn.click();

    // Step 2: Folder Selection
    const folderStep = page.locator('[data-testid="folder-selection-step"]');
    await expect(folderStep).toBeVisible({ timeout: 5000 });

    // Add a test folder using manual input (Web fallback)
    const addFolderBtn = page.locator('[data-testid="add-folder-btn"]');
    await addFolderBtn.click();

    // The manual input should appear since window.electronAPI is undefined
    const manualInput = page.locator('input[placeholder="/path/to/your/photos"]');
    await expect(manualInput).toBeVisible();
    
    // Enter a dummy path
    const testPath = '/tmp/test-photos-onboarding';
    await manualInput.fill(testPath);
    await manualInput.press('Enter');

    // Verify folder was added to list
    await expect(page.getByText(testPath)).toBeVisible({ timeout: 5000 });

    // Setup mocks for indexing BEFORE navigating to that step
    await page.route('**/index/start', async route => {
      await route.fulfill({ status: 200, body: JSON.stringify({ status: 'started' }) });
    });

    // Mock status polling to simulate completion
    await page.route('**/index/status', async route => {
      await route.fulfill({ 
        status: 200, 
        body: JSON.stringify({ 
          status: 'completed',
          progress: { processed_files: 10, total_files: 10, current_phase: 'completed' },
          errors: [],
          estimated_completion: null
        }) 
      });
    });
    
    // Also mock roots config to avoid FS errors on backend
    await page.route('**/config/roots', async route => {
      await route.fulfill({ status: 200, body: JSON.stringify({ success: true }) });
    });

    // Click Continue
    const continueBtn = page.locator('[data-testid="continue-btn"]');
    await continueBtn.click();

    // Step 3: Indexing
    const indexingStep = page.locator('[data-testid="indexing-step"]');
    await expect(indexingStep).toBeVisible({ timeout: 5000 });
    
    // Wait for indexing to complete or at least start
    // We check for the step container which confirms we are on the right step
    await expect(indexingStep).toBeVisible();

    // Wait for completion (handled by polling the mocked status)
    // The UI should show "All done!" when complete
    await expect(page.locator('text=All done!')).toBeVisible({ timeout: 10000 });

    // Click Continue after indexing
    const indexContinueBtn = page.locator('[data-testid="continue-after-index-btn"]');
    await expect(indexContinueBtn).toBeEnabled();
    await indexContinueBtn.click();

    // Step 4: Complete
    const completeStep = page.locator('[data-testid="complete-step"]');
    await expect(completeStep).toBeVisible({ timeout: 5000 });

    // Verify completion message
    await expect(page.locator("text=You're All Set!")).toBeVisible();

    // Click Start Using button
    const startBtn = page.locator('[data-testid="start-using-btn"]');
    await startBtn.click();

    // Verify onboarding modal is closed
    await expect(page.locator('[data-testid="onboarding-modal"]')).not.toBeVisible({ timeout: 5000 });

    // Verify main search page is visible
    await expect(page.locator('[data-testid="search-page"]')).toBeVisible();
  });

  test('should allow skipping onboarding', async ({ page }) => {
    // Wait for onboarding
    await expect(page.locator('[data-testid="onboarding-modal"]')).toBeVisible({ timeout: 10000 });

    // Look for skip button
    const skipBtn = page.locator('[data-testid="skip-onboarding-btn"]');
    if (await skipBtn.isVisible()) {
      await skipBtn.click();

      // Verify onboarding closes
      await expect(page.locator('[data-testid="onboarding-modal"]')).not.toBeVisible({ timeout: 5000 });
      
      // Verify main search page is visible
      await expect(page.locator('[data-testid="search-page"]')).toBeVisible();
    }
  });

  test('should validate folder selection', async ({ page }) => {
    // Navigate to folder step
    await page.locator('[data-testid="get-started-btn"]').click();
    
    // Try to continue without selecting folders
    const continueBtn = page.locator('[data-testid="continue-btn"]');
    const isDisabled = await continueBtn.isDisabled();

    // Button should be disabled without folders
    expect(isDisabled).toBe(true);
  });
});

