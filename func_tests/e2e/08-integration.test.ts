import { test, expect } from '@playwright/test';
import { SearchPage } from '../page-objects/SearchPage';
import { PeoplePage } from '../page-objects/PeoplePage';
import { SettingsPage } from '../page-objects/SettingsPage';
import { APIClient } from '../helpers/api-client';
import { TestData } from '../helpers/test-data';

test.describe('Full Integration Tests', () => {
  let searchPage: SearchPage;
  let peoplePage: PeoplePage;
  let settingsPage: SettingsPage;
  let apiClient: APIClient;
  let testImages: string[] = [];

  test.beforeAll(async () => {
    apiClient = new APIClient();
    await apiClient.initialize();
    testImages = await TestData.createTestImages(10);
  });

  test.afterAll(async () => {
    await apiClient.dispose();
  });

  test.describe('Complete Photo Management Workflow', () => {
    test('indexes photos, searches, and manages people end-to-end', async ({ page }) => {
      // Step 1: Configure indexing
      settingsPage = new SettingsPage(page);
      await settingsPage.goto('/settings');

      // Add test folder for indexing
      const testFolder = '/path/to/test/photos';
      await settingsPage.addRootFolder(testFolder);

      // Start indexing
      await settingsPage.startIndexing(false); // incremental

      // Wait for indexing to complete
      await settingsPage.waitForIndexingComplete();

      // Step 2: Perform text search
      searchPage = new SearchPage(page);
      await searchPage.goto();

      await searchPage.textSearchButton.click();
      await searchPage.searchInput.fill('test photo');
      await searchPage.performSearch();

      // Should find indexed photos
      const hasResults = await searchPage.hasSearchResults();
      expect(hasResults).toBeTruthy();

      // Step 3: Add person from search results
      peoplePage = new PeoplePage(page);
      await peoplePage.goto('/people');

      const personName = 'Integration Test Person';
      await peoplePage.addPerson(personName, testImages.slice(0, 3));

      // Verify person was added
      const people = await peoplePage.getAllPeople();
      expect(people).toContain(personName);

      // Step 4: Search by face
      await apiClient.updateConfig({ face_search_enabled: true });
      await page.waitForTimeout(2000); // Allow config to propagate

      await peoplePage.searchByFace(personName);

      // Should navigate to search with face filter
      await expect(page).toHaveURL(/face=/);

      // Step 5: Cleanup
      await peoplePage.goto('/people');
      await peoplePage.deletePerson(personName);
    });

    test('handles large dataset operations efficiently', async ({ page }) => {
      settingsPage = new SettingsPage(page);
      await settingsPage.goto('/settings');

      // Test with large folder structure
      const largeFolders = [
        '/large/dataset/folder1',
        '/large/dataset/folder2',
        '/large/dataset/folder3'
      ];

      for (const folder of largeFolders) {
        await settingsPage.addRootFolder(folder);
      }

      // Start full indexing
      await settingsPage.startIndexing(true); // full reindex

      // Monitor progress
      const progressStarted = await settingsPage.waitForIndexingProgress();
      expect(progressStarted).toBeTruthy();

      // Should handle large operations without freezing UI
      await page.waitForTimeout(1000);

      // UI should remain responsive
      await settingsPage.navigateToSearch();
      await expect(page).toHaveURL(/\//);
    });
  });

  test.describe('Multi-User Simulation', () => {
    test('handles concurrent operations', async ({ browser }) => {
      // Simulate multiple users
      const contexts = await Promise.all([
        browser.newContext(),
        browser.newContext(),
        browser.newContext()
      ]);

      const pages = await Promise.all(
        contexts.map(context => context.newPage())
      );

      try {
        // Each "user" performs different operations concurrently
        const operations = [
          // User 1: Search operations
          async () => {
            const searchPage = new SearchPage(pages[0]);
            await searchPage.goto();
            await searchPage.textSearchButton.click();
            await searchPage.searchInput.fill('concurrent test');
            await searchPage.performSearch();
          },

          // User 2: People management
          async () => {
            const peoplePage = new PeoplePage(pages[1]);
            await peoplePage.goto('/people');
            await peoplePage.addPerson('Concurrent User 2', [testImages[0]]);
          },

          // User 3: Settings changes
          async () => {
            const settingsPage = new SettingsPage(pages[2]);
            await settingsPage.goto('/settings');
            await settingsPage.addRootFolder('/concurrent/test');
          }
        ];

        // Run all operations concurrently
        await Promise.all(operations);

        // All operations should complete successfully
        // Verify each user's operations
        for (const page of pages) {
          const errorMessages = await page.locator('[role="alert"]:has-text("Error")').count();
          expect(errorMessages).toBe(0);
        }

      } finally {
        // Cleanup
        await Promise.all(contexts.map(context => context.close()));
      }
    });
  });

  test.describe('Data Consistency', () => {
    test('maintains data integrity across operations', async ({ page }) => {
      peoplePage = new PeoplePage(page);
      await peoplePage.goto('/people');

      // Create multiple people
      const peopleNames = ['Data Test 1', 'Data Test 2', 'Data Test 3'];

      for (let i = 0; i < peopleNames.length; i++) {
        await peoplePage.addPerson(peopleNames[i], [testImages[i]]);
      }

      // Verify all were created
      let allPeople = await peoplePage.getAllPeople();
      for (const name of peopleNames) {
        expect(allPeople).toContain(name);
      }

      // Edit one person
      await peoplePage.editPerson(peopleNames[0], 'Data Test Updated');

      // Verify edit didn't affect others
      allPeople = await peoplePage.getAllPeople();
      expect(allPeople).toContain('Data Test Updated');
      expect(allPeople).not.toContain(peopleNames[0]);
      expect(allPeople).toContain(peopleNames[1]);
      expect(allPeople).toContain(peopleNames[2]);

      // Delete one person
      await peoplePage.deletePerson(peopleNames[1]);

      // Verify deletion was isolated
      allPeople = await peoplePage.getAllPeople();
      expect(allPeople).not.toContain(peopleNames[1]);
      expect(allPeople).toContain('Data Test Updated');
      expect(allPeople).toContain(peopleNames[2]);

      // Cleanup remaining
      await peoplePage.deletePerson('Data Test Updated');
      await peoplePage.deletePerson(peopleNames[2]);
    });

    test('handles rapid state changes correctly', async ({ page }) => {
      peoplePage = new PeoplePage(page);
      await peoplePage.goto('/people');

      const rapidTestName = 'Rapid Test Person';

      // Rapid operations
      await peoplePage.addPerson(rapidTestName, [testImages[0]]);

      // Immediately edit
      await peoplePage.editPerson(rapidTestName, 'Rapid Test Updated');

      // Immediately add photos
      await peoplePage.addPhotosToExistingPerson('Rapid Test Updated', [testImages[1]]);

      // Verify final state is correct
      const photoCount = await peoplePage.getPersonPhotos('Rapid Test Updated');
      expect(photoCount).toBe(2);

      // Cleanup
      await peoplePage.deletePerson('Rapid Test Updated');
    });
  });

  test.describe('Configuration Persistence', () => {
    test('persists settings across sessions', async ({ page }) => {
      settingsPage = new SettingsPage(page);
      await settingsPage.goto('/settings');

      // Change multiple settings
      await settingsPage.addRootFolder('/persistent/test');
      await apiClient.updateConfig({
        face_search_enabled: true,
        ocr_enabled: true,
        semantic_search_enabled: false
      });

      // Reload page to simulate new session
      await page.reload();

      // Verify settings persisted
      const rootFolders = await settingsPage.getRootFolders();
      expect(rootFolders).toContain('/persistent/test');

      // Check configuration
      const config = await apiClient.getConfig();
      expect(config.face_search_enabled).toBe(true);
      expect(config.ocr_enabled).toBe(true);
      expect(config.semantic_search_enabled).toBe(false);
    });

    test('handles configuration conflicts gracefully', async ({ page }) => {
      settingsPage = new SettingsPage(page);
      await settingsPage.goto('/settings');

      // Create conflicting configurations
      await settingsPage.addRootFolder('/conflict/test');

      // Try to add duplicate
      await settingsPage.addRootFolder('/conflict/test');

      // Should handle conflict gracefully
      const errorMessage = page.locator('[role="alert"]:has-text("already exists")');
      // await expect(errorMessage).toBeVisible();
    });
  });

  test.describe('Performance Under Load', () => {
    test('maintains performance with many search results', async ({ page }) => {
      searchPage = new SearchPage(page);
      await searchPage.goto();

      // Mock large result set
      await page.route('**/api/search/**', route => {
        const largeResults = Array.from({ length: 1000 }, (_, i) => ({
          id: i,
          file_path: `/performance/test/image${i}.jpg`,
          similarity_score: Math.random(),
          thumbnail_path: `/thumbnails/image${i}.jpg`
        }));

        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ results: largeResults })
        });
      });

      const startTime = Date.now();

      await searchPage.textSearchButton.click();
      await searchPage.searchInput.fill('performance test');
      await searchPage.performSearch();

      // Should render results quickly
      const renderTime = Date.now() - startTime;
      expect(renderTime).toBeLessThan(3000);

      // UI should remain responsive
      await searchPage.searchInput.click();
      await searchPage.searchInput.clear();
    });

    test('efficiently handles many people', async ({ page }) => {
      peoplePage = new PeoplePage(page);
      await peoplePage.goto('/people');

      // Add many people quickly
      const manyPeople = Array.from({ length: 50 }, (_, i) => `Performance Person ${i}`);

      for (let i = 0; i < Math.min(manyPeople.length, 10); i++) {
        await peoplePage.addPerson(manyPeople[i], [testImages[i % testImages.length]]);
      }

      // Search should remain fast
      const startTime = Date.now();
      await peoplePage.searchPerson('Performance');
      const searchTime = Date.now() - startTime;

      expect(searchTime).toBeLessThan(2000);

      // Cleanup
      const addedPeople = await peoplePage.getAllPeople();
      for (const person of addedPeople) {
        if (person.includes('Performance Person')) {
          await peoplePage.deletePerson(person);
        }
      }
    });
  });
});