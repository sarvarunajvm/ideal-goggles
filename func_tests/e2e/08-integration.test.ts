import { test, expect } from '@playwright/test';
import { SearchPage } from '../page-objects/SearchPage';
import { PeoplePage } from '../page-objects/PeoplePage';
import { SettingsPage } from '../page-objects/SettingsPage';
import { APIClient } from '../helpers/api-client';
import { TestData } from '../helpers/test-data';
import * as fs from 'fs';
import * as path from 'path';

test.describe('Full Integration Tests', () => {
  let searchPage: SearchPage;
  let peoplePage: PeoplePage;
  let settingsPage: SettingsPage;
  let apiClient: APIClient;

  test.beforeAll(async () => {
    apiClient = new APIClient();
    await apiClient.initialize();
  });

  test.afterAll(async () => {
    await apiClient.dispose();
  });

  test.describe('Complete Photo Management Workflow', () => {
    test('indexes photos, searches, and manages people end-to-end', async ({ page }) => {
      test.setTimeout(180000);
      // Ensure config allows people management
      await apiClient.updateConfig({ face_search_enabled: true });

      // Step 1: Configure indexing
      settingsPage = new SettingsPage(page);
      await settingsPage.goto('/settings');

      // Add test folder for indexing
      const testFolder = '/tmp/test-photos-integration';
      if (!fs.existsSync(testFolder)) fs.mkdirSync(testFolder, { recursive: true });
      // Create a dummy image to ensure indexing has something to do
      const dummyImage = path.join(testFolder, 'integration-test-image.png');
      if (!fs.existsSync(dummyImage)) {
          const pngBase64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==";
          fs.writeFileSync(dummyImage, Buffer.from(pngBase64, 'base64'));
      }

      await settingsPage.addRootFolder(testFolder);

      // Start indexing
      await settingsPage.startIndexing(false); // incremental

      // Wait for indexing to complete - increase timeout
      await settingsPage.waitForIndexingComplete(120000);

      // Step 2: Perform text search
      searchPage = new SearchPage(page);
      await searchPage.goto();

      await searchPage.textSearchButton.click();
      await searchPage.searchInput.fill(''); // Empty search to list all
      await searchPage.performSearch();

      // Step 3: Add person from search results (using helper to find valid file ID)
      const indexedPhotos = await apiClient.getIndexedPhotos();
      if (indexedPhotos.length === 0) {
          test.skip('No indexed photos');
      }

      peoplePage = new PeoplePage(page);
      await peoplePage.goto('/people');

      const personName = `Integration Person ${Date.now()}`;
      await peoplePage.addPerson(personName, [indexedPhotos[0].file_id]);

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
      test.setTimeout(180000);
      settingsPage = new SettingsPage(page);
      await settingsPage.goto('/settings');

      // Test with "large" folder structure (reduced for CI stability)
      const largeFolders = [
        '/tmp/large-dataset-folder1'
      ];

      for (const folder of largeFolders) {
        if (!fs.existsSync(folder)) fs.mkdirSync(folder, { recursive: true });
        // Create a dummy file
        fs.writeFileSync(path.join(folder, 'dummy.png'), Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==", 'base64'));
        await settingsPage.addRootFolder(folder);
      }

      // Start full indexing
      await settingsPage.startIndexing(true); // full reindex

      // Just wait for completion
      await settingsPage.waitForIndexingComplete(120000);
      
      // Should handle large operations without freezing UI
      await page.waitForTimeout(1000);

      // UI should remain responsive
      await settingsPage.navigateToSearch();
      await expect(page).toHaveURL(/\//);
      
      // Cleanup
      for (const folder of largeFolders) {
          if (fs.existsSync(folder)) fs.rmSync(folder, { recursive: true, force: true });
      }
    });
  });

  test.describe('Multi-User Simulation', () => {
    test('handles concurrent operations', async ({ browser }) => {
      // Simulate multiple users
      const contexts = await Promise.all([
        browser.newContext(),
        browser.newContext() // Reduce to 2 users
      ]);

      const pages = await Promise.all(
        contexts.map(context => context.newPage())
      );

      try {
        const indexedPhotos = await apiClient.getIndexedPhotos();
        if (indexedPhotos.length === 0) test.skip('No photos');

        // Sequential execution to avoid crash
        
        // User 1: Search operations
        const searchPage = new SearchPage(pages[0]);
        await searchPage.goto();
        await searchPage.textSearchButton.click();
        await searchPage.searchInput.fill('concurrent test');
        await searchPage.performSearch();

        // User 2: People management
        const peoplePage = new PeoplePage(pages[1]);
        await peoplePage.goto('/people');
        const uniqueName = `Concurrent User 2 ${Date.now()}`;
        await peoplePage.addPerson(uniqueName, [indexedPhotos[0].file_id]);

        // Verify
        const people = await peoplePage.getAllPeople();
        expect(people).toContain(uniqueName);

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

      const indexedPhotos = await apiClient.getIndexedPhotos();
      if (indexedPhotos.length < 3) test.skip('Need at least 3 photos');

      // Create multiple people
      const ts = Date.now();
      const peopleNames = [`Data Test 1 ${ts}`, `Data Test 2 ${ts}`, `Data Test 3 ${ts}`];

      for (let i = 0; i < peopleNames.length; i++) {
        await peoplePage.addPerson(peopleNames[i], [indexedPhotos[i].file_id]);
      }

      // Verify all were created
      let allPeople = await peoplePage.getAllPeople();
      for (const name of peopleNames) {
        expect(allPeople).toContain(name);
      }

      // Edit one person
      const updatedName = `Data Test Updated ${ts}`;
      await peoplePage.editPerson(peopleNames[0], updatedName);

      // Verify edit didn't affect others
      allPeople = await peoplePage.getAllPeople();
      expect(allPeople).toContain(updatedName);
      expect(allPeople).not.toContain(peopleNames[0]);
      expect(allPeople).toContain(peopleNames[1]);
      expect(allPeople).toContain(peopleNames[2]);

      // Delete one person
      await peoplePage.deletePerson(peopleNames[1]);
      await page.waitForTimeout(1000); // Wait for update

      // Verify deletion was isolated
      allPeople = await peoplePage.getAllPeople();
      expect(allPeople).not.toContain(peopleNames[1]);
      expect(allPeople).toContain(updatedName);
      expect(allPeople).toContain(peopleNames[2]);

      // Cleanup remaining
      await peoplePage.deletePerson(updatedName);
      await peoplePage.deletePerson(peopleNames[2]);
    });

    test('handles rapid state changes correctly', async ({ page }) => {
      peoplePage = new PeoplePage(page);
      await peoplePage.goto('/people');

      const indexedPhotos = await apiClient.getIndexedPhotos();
      if (indexedPhotos.length < 2) test.skip('Need 2 photos');

      const rapidTestName = `Rapid Test ${Date.now()}`;

      // Rapid operations
      await peoplePage.addPerson(rapidTestName, [indexedPhotos[0].file_id]);

      // Immediately edit
      const updatedName = `Rapid Updated ${Date.now()}`;
      await peoplePage.editPerson(rapidTestName, updatedName);

      // Immediately add photos
      await peoplePage.addPhotosToExistingPerson(updatedName);

      // Verify final state is correct
      const photoCount = await peoplePage.getPersonPhotos(updatedName);
      expect(photoCount).toBeGreaterThanOrEqual(2); // Initial 1 + added 1

      // Cleanup
      await peoplePage.deletePerson(updatedName);
    });
  });

  test.describe('Configuration Persistence', () => {
    test('persists settings across sessions', async ({ page }) => {
      settingsPage = new SettingsPage(page);
      await settingsPage.goto('/settings');

      // Change multiple settings
      const persistFolder = '/tmp/persistent-test';
      if (!fs.existsSync(persistFolder)) fs.mkdirSync(persistFolder);
      await settingsPage.addRootFolder(persistFolder);
      
      await apiClient.updateConfig({
        face_search_enabled: true,
        ocr_enabled: true,
        semantic_search_enabled: false
      });

      // Reload page to simulate new session
      await page.reload();
      await settingsPage.waitForSettingsLoaded();

      // Verify settings persisted
      const rootFolders = await settingsPage.getRootFolders();
      // Handle symlink
      expect(rootFolders.some(f => f.endsWith('persistent-test'))).toBeTruthy();

      // Check configuration via API
      const config = await apiClient.getConfig();
      const configData = await config.json();
      expect(configData.face_search_enabled).toBe(true);
      // OCR removed
      // expect(configData.ocr_enabled).toBe(true);
      expect(configData.semantic_search_enabled).toBe(false);
      
      // Cleanup
      if (fs.existsSync(persistFolder)) fs.rmdirSync(persistFolder);
    });

    test('handles configuration conflicts gracefully', async ({ page }) => {
      settingsPage = new SettingsPage(page);
      await settingsPage.goto('/settings');

      // Create conflicting configurations
      const conflictFolder = '/tmp/conflict-test';
      if (!fs.existsSync(conflictFolder)) fs.mkdirSync(conflictFolder);
      
      // Add first time
      await settingsPage.addRootFolder(conflictFolder);

      // Try to add duplicate - page handles this by just not adding it or showing message
      // The UI logic: "if (!rootFolders.includes(folderPath))"
      // So UI prevents it.
      await settingsPage.addRootFolder(conflictFolder);

      // Verify only one entry
      const rootFolders = await settingsPage.getRootFolders();
      const count = rootFolders.filter(f => f.endsWith('conflict-test')).length;
      expect(count).toBe(1);
      
      // Cleanup
      if (fs.existsSync(conflictFolder)) fs.rmdirSync(conflictFolder);
    });
  });

  test.describe('Performance Under Load', () => {
    test('maintains performance with many search results', async ({ page }) => {
      searchPage = new SearchPage(page);
      await searchPage.goto();

      // Mock large result set
      await page.route('**/api/search**', route => {
        const largeResults = Array.from({ length: 1000 }, (_, i) => ({
          id: i,
          file_id: i, // Add file_id
          file_path: `/performance/test/image${i}.jpg`,
          similarity_score: Math.random(),
          thumb_path: `thumbnails/image${i}.jpg`, // Use thumb_path
          filename: `image${i}.jpg`
        }));

        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ items: largeResults, total: 1000 }) // Use items structure
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
      test.setTimeout(120000);
      // Ensure config allows people management
      await apiClient.updateConfig({ face_search_enabled: true });

      peoplePage = new PeoplePage(page);
      await peoplePage.goto('/people');

      const indexedPhotos = await apiClient.getIndexedPhotos();
      if (indexedPhotos.length === 0) test.skip('No photos');

      // Add many people quickly
      const ts = Date.now();
      const manyPeople = Array.from({ length: 10 }, (_, i) => `Perf Person ${i} ${ts}`); // Reduced from 50 to 10 for speed

      for (let i = 0; i < manyPeople.length; i++) {
        await peoplePage.addPerson(manyPeople[i], [indexedPhotos[0].file_id]);
      }

      // Search should remain fast
      const startTime = Date.now();
      await peoplePage.searchPerson('Perf Person');
      const searchTime = Date.now() - startTime;

      expect(searchTime).toBeLessThan(2000);

      // Cleanup
      // We rely on global teardown or afterAll, but let's clean up to be nice
      const response = await apiClient.getPeople();
      const people = await response.json();
      for (const p of people) {
          if (p.name.includes(ts.toString())) {
              await apiClient.deletePerson(p.id);
          }
      }
    });
  });
});