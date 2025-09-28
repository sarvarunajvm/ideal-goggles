import { test, expect } from '@playwright/test';
import { SearchPage } from '../page-objects/SearchPage';
import { SettingsPage } from '../page-objects/SettingsPage';
import { PeoplePage } from '../page-objects/PeoplePage';
import { APIClient } from '../helpers/api-client';
import { TestData } from '../helpers/test-data';

test.describe('End-to-End Workflows', () => {
  let searchPage: SearchPage;
  let settingsPage: SettingsPage;
  let peoplePage: PeoplePage;
  let apiClient: APIClient;

  test.beforeAll(async () => {
    apiClient = new APIClient();
    await apiClient.initialize();
  });

  test.afterAll(async () => {
    await apiClient.dispose();
  });

  test('complete photo indexing and search workflow', async ({ page }) => {
    // 1. Navigate to settings
    settingsPage = new SettingsPage(page);
    await settingsPage.goto('/settings');

    // 2. Add root folders
    const testFolders = JSON.parse(process.env.TEST_FOLDERS || '[]');
    if (testFolders.length > 0) {
      await settingsPage.addRootFolder(testFolders[0]);
    }

    // 3. Configure search features
    await settingsPage.toggleSemanticSearch(true);
    await settingsPage.toggleFaceSearch(true);
    await settingsPage.setBatchSize(50);

    // 4. Start indexing
    await settingsPage.startIndexing(true);

    // 5. Wait for indexing to start
    await settingsPage.waitForIndexingStart();

    // 6. Navigate to search while indexing
    searchPage = new SearchPage(page);
    await searchPage.navigateToSearch();

    // 7. Perform searches with different modes
    await searchPage.performTextSearch('test');
    await searchPage.performSemanticSearch('beautiful landscape photo');

    // 8. Go back to settings to check indexing status
    await settingsPage.navigateToSettings();
    const status = await settingsPage.getIndexingStatus();
    expect(status.status).toBeTruthy();
  });

  test('person enrollment and face search workflow', async ({ page }) => {
    // 1. Create test images
    const testImages = await TestData.createTestImages(5);

    // 2. Navigate to people page
    peoplePage = new PeoplePage(page);
    await peoplePage.goto('/people');

    // 3. Add a new person
    const personName = 'Workflow Test Person';
    await peoplePage.addPerson(personName, testImages.slice(0, 3));

    // 4. Verify person was added
    const people = await peoplePage.getAllPeople();
    expect(people).toContain(personName);

    // 5. Search for this person's photos
    await peoplePage.searchByFace(personName);

    // 6. Should redirect to search page with face filter
    await expect(page).toHaveURL(/face=/);

    // 7. Verify search page is functional
    searchPage = new SearchPage(page);
    await expect(searchPage.navBar).toBeVisible();
  });

  test('configuration and search optimization workflow', async ({ page }) => {
    settingsPage = new SettingsPage(page);
    searchPage = new SearchPage(page);

    // 1. Start with minimal configuration
    await settingsPage.goto('/settings');
    const minimalPreset = TestData.CONFIG_PRESETS.minimal;
    await settingsPage.toggleOCR(minimalPreset.ocr_enabled);
    await settingsPage.toggleFaceSearch(minimalPreset.face_search_enabled);
    await settingsPage.toggleSemanticSearch(minimalPreset.semantic_search_enabled);
    await settingsPage.setBatchSize(minimalPreset.batch_size);

    // 2. Test search with minimal config
    await searchPage.navigateToSearch();
    await searchPage.performTextSearch('test minimal');

    // 3. Upgrade to full configuration
    await settingsPage.navigateToSettings();
    const fullPreset = TestData.CONFIG_PRESETS.full;
    await settingsPage.toggleOCR(fullPreset.ocr_enabled);
    await settingsPage.toggleFaceSearch(fullPreset.face_search_enabled);
    await settingsPage.toggleSemanticSearch(fullPreset.semantic_search_enabled);
    await settingsPage.setBatchSize(fullPreset.batch_size);

    // 4. Test enhanced search capabilities
    await searchPage.navigateToSearch();
    await searchPage.performSemanticSearch('complex scene with text');

    // 5. Verify all search modes are available
    await searchPage.textSearchButton.click();
    await expect(searchPage.textSearchButton).toHaveClass(/bg-blue-600/);

    await searchPage.semanticSearchButton.click();
    await expect(searchPage.semanticSearchButton).toHaveClass(/bg-blue-600/);

    await searchPage.imageSearchButton.click();
    await expect(searchPage.uploadArea).toBeVisible();
  });

  test('error recovery workflow', async ({ page }) => {
    settingsPage = new SettingsPage(page);
    searchPage = new SearchPage(page);

    // 1. Simulate backend connection issues
    await page.route('**/api/health', route => {
      route.abort('failed');
    });

    await searchPage.goto();

    // 2. App should show disconnected state
    const statusClass = await searchPage.connectionStatus.first().getAttribute('class');
    expect(statusClass).toContain('bg-red-500');

    // 3. Restore connection
    await page.unroute('**/api/health');

    // 4. Refresh and verify recovery
    await page.reload();
    await searchPage.waitForConnection();

    // 5. Verify functionality is restored
    await searchPage.performTextSearch('recovery test');
    await expect(searchPage.navBar).toBeVisible();
  });

  test('multi-user workflow simulation', async ({ page, context }) => {
    // Simulate multiple users by opening multiple tabs
    const pages = [page];

    // Create additional pages (tabs)
    for (let i = 0; i < 2; i++) {
      const newPage = await context.newPage();
      pages.push(newPage);
    }

    // Each "user" performs different actions
    const workflows = pages.map(async (p, index) => {
      if (index === 0) {
        // User 1: Settings configuration
        const settings = new SettingsPage(p);
        await settings.goto('/settings');
        await settings.toggleOCR(true);
      } else if (index === 1) {
        // User 2: Search operations
        const search = new SearchPage(p);
        await search.goto();
        await search.performTextSearch(`user ${index} test`);
      } else {
        // User 3: People management
        const people = new PeoplePage(p);
        await people.goto('/people');
        const testImage = await TestData.createTestImage(`user-${index}.png`);
        await people.addPerson(`User ${index}`, [testImage]);
      }
    });

    // Execute all workflows concurrently
    await Promise.all(workflows);

    // Verify all pages are still functional
    for (const p of pages) {
      const nav = p.locator('nav');
      await expect(nav).toBeVisible();
    }

    // Close additional pages
    for (let i = 1; i < pages.length; i++) {
      await pages[i].close();
    }
  });

  test('data migration workflow', async ({ page }) => {
    settingsPage = new SettingsPage(page);

    // 1. Set up initial configuration
    await settingsPage.goto('/settings');
    const initialFolders = ['/tmp/old-photos'];
    for (const folder of initialFolders) {
      await settingsPage.addRootFolder(folder);
    }

    // 2. Start indexing old data
    await settingsPage.startIndexing(true);
    await settingsPage.waitForIndexingStart();

    // 3. Add new folders (simulating migration)
    const newFolders = ['/tmp/new-photos', '/tmp/migrated-photos'];
    for (const folder of newFolders) {
      await settingsPage.addRootFolder(folder);
    }

    // 4. Re-index with new data
    await settingsPage.startIndexing(true);

    // 5. Remove old folders
    const allFolders = await settingsPage.getRootFolders();
    const oldFolderIndex = allFolders.indexOf(initialFolders[0]);
    if (oldFolderIndex >= 0) {
      await settingsPage.removeRootFolder(oldFolderIndex);
    }

    // 6. Verify configuration is updated
    const finalFolders = await settingsPage.getRootFolders();
    expect(finalFolders).not.toContain(initialFolders[0]);
  });

  test('performance optimization workflow', async ({ page }) => {
    settingsPage = new SettingsPage(page);
    searchPage = new SearchPage(page);

    // 1. Start with default settings
    await settingsPage.goto('/settings');
    const defaultBatchSize = 50;
    await settingsPage.setBatchSize(defaultBatchSize);

    // 2. Measure search performance
    await searchPage.navigateToSearch();
    const startTime = Date.now();
    await searchPage.performTextSearch('performance test');
    const baselineTime = Date.now() - startTime;

    // 3. Optimize settings for performance
    await settingsPage.navigateToSettings();
    await settingsPage.setBatchSize(100);
    await settingsPage.setThumbnailSize('small');
    await settingsPage.toggleOCR(false); // Disable heavy features

    // 4. Re-measure performance
    await searchPage.navigateToSearch();
    const optimizedStartTime = Date.now();
    await searchPage.performTextSearch('performance test optimized');
    const optimizedTime = Date.now() - optimizedStartTime;

    // 5. Performance should be reasonable
    expect(optimizedTime).toBeLessThan(5000); // Should complete within 5 seconds
  });

  test('accessibility workflow', async ({ page }) => {
    // Test keyboard navigation through the entire app
    searchPage = new SearchPage(page);
    await searchPage.goto();

    // 1. Tab through navigation
    await page.keyboard.press('Tab');
    let focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(focusedElement).toBeTruthy();

    // 2. Navigate to settings using keyboard
    for (let i = 0; i < 10; i++) {
      await page.keyboard.press('Tab');
      const element = await page.evaluate(() => document.activeElement?.textContent);
      if (element?.includes('Settings')) {
        await page.keyboard.press('Enter');
        break;
      }
    }

    // 3. Verify navigation worked
    await expect(page).toHaveURL(/settings/);

    // 4. Test form controls with keyboard
    settingsPage = new SettingsPage(page);
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.type('/tmp/keyboard-test');

    // 5. Submit with Enter
    await page.keyboard.press('Enter');

    // 6. Navigate back to search
    await page.keyboard.press('Shift+Tab');
    for (let i = 0; i < 10; i++) {
      await page.keyboard.press('Shift+Tab');
      const element = await page.evaluate(() => document.activeElement?.textContent);
      if (element?.includes('Search')) {
        await page.keyboard.press('Enter');
        break;
      }
    }

    await expect(page).toHaveURL(/\/$/);
  });
});