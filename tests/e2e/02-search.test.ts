import { test, expect } from '@playwright/test';
import { SearchPage } from '../page-objects/SearchPage';
import { APIClient } from '../helpers/api-client';
import { TestData } from '../helpers/test-data';

test.describe('Search Functionality', () => {
  let searchPage: SearchPage;
  let apiClient: APIClient;

  test.beforeAll(async () => {
    apiClient = new APIClient();
    await apiClient.initialize();

    // Ensure we have some test data
    const testFolders = JSON.parse(process.env.TEST_FOLDERS || '[]');
    if (testFolders.length > 0) {
      await apiClient.setRootFolders(testFolders);
      await apiClient.startIndexing(true);
      await apiClient.waitForIndexingComplete();
    }
  });

  test.afterAll(async () => {
    await apiClient.dispose();
  });

  test.beforeEach(async ({ page }) => {
    searchPage = new SearchPage(page);
    await searchPage.goto();
  });

  test.describe('Text Search', () => {
    test('performs basic text search', async () => {
      const query = TestData.getRandomSearchQuery('text');
      await searchPage.performTextSearch(query);

      // Verify search mode is active
      const activeMode = await searchPage.getActiveSearchMode();
      expect(activeMode).toContain('Text Search');
    });

    test('shows empty state when no results', async () => {
      await searchPage.performTextSearch('nonexistentfile12345');
      await expect(searchPage.emptyState).toBeVisible();
    });

    test('validates search input', async () => {
      // Empty search should disable button
      await searchPage.clearSearch();
      const isEnabled = await searchPage.isSearchButtonEnabled();
      expect(isEnabled).toBeFalsy();

      // Valid input should enable button
      await searchPage.searchInput.fill('test');
      const isEnabledAfter = await searchPage.isSearchButtonEnabled();
      expect(isEnabledAfter).toBeTruthy();
    });

    test('handles special characters in search', async () => {
      const specialQueries = [
        'test & test',
        'file (1).jpg',
        'photo@2023',
        'image#001',
        'doc$final'
      ];

      for (const query of specialQueries) {
        await searchPage.performTextSearch(query);
        // Should not crash or show error
        await expect(searchPage.navBar).toBeVisible();
      }
    });

    test('supports pagination', async ({ page }) => {
      await searchPage.performTextSearch('test');

      // Check if pagination controls appear (if results > page size)
      const paginationControls = page.locator('[data-testid="pagination"]');
      if (await paginationControls.isVisible()) {
        const nextButton = page.locator('button:has-text("Next")');
        await nextButton.click();
        await searchPage.waitForLoadingComplete();
      }
    });
  });

  test.describe('Semantic Search', () => {
    test('performs semantic search with natural language', async () => {
      const query = TestData.getRandomSearchQuery('semantic');
      await searchPage.performSemanticSearch(query);

      const activeMode = await searchPage.getActiveSearchMode();
      expect(activeMode).toContain('Semantic Search');
    });

    test('shows appropriate placeholder for semantic search', async () => {
      await searchPage.semanticSearchButton.click();
      const placeholder = await searchPage.getSearchPlaceholder();
      expect(placeholder).toContain('Describe what');
    });

    test('handles long descriptions', async () => {
      const longQuery = 'A beautiful sunset over the ocean with orange and pink clouds reflecting on the calm water surface, seagulls flying in the distance, and a sailboat on the horizon';
      await searchPage.performSemanticSearch(longQuery);
      await expect(searchPage.navBar).toBeVisible();
    });
  });

  test.describe('Image Search', () => {
    test('shows upload interface for image search', async () => {
      await searchPage.imageSearchButton.click();
      await expect(searchPage.uploadArea).toBeVisible();
    });

    test('uploads and searches by image', async () => {
      const testImages = JSON.parse(process.env.TEST_IMAGES || '[]');
      if (testImages.length > 0) {
        await searchPage.uploadImageForSearch(testImages[0]);
        // Should complete without error
        await expect(searchPage.navBar).toBeVisible();
      }
    });

    test('handles invalid file types', async ({ page }) => {
      await searchPage.imageSearchButton.click();

      // Create a text file
      const textFile = '/tmp/test.txt';
      require('fs').writeFileSync(textFile, 'This is not an image');

      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles(textFile);

      // Should show error or not accept the file
      const errorMessage = page.locator('[role="alert"]');
      if (await errorMessage.isVisible()) {
        const text = await errorMessage.textContent();
        expect(text).toContain('image');
      }
    });
  });

  test.describe('Search Filters', () => {
    test('toggles filter panel', async () => {
      await searchPage.toggleFilters();
      // Filter panel should be visible (implementation dependent)
      await searchPage.page.waitForTimeout(500);

      await searchPage.toggleFilters();
      // Filter panel should be hidden
      await searchPage.page.waitForTimeout(500);
    });

    test('applies date range filter', async () => {
      const startDate = '2023-01-01';
      const endDate = '2023-12-31';

      await searchPage.setDateFilter(startDate, endDate);
      await searchPage.performTextSearch('test');

      // Results should be filtered (verify through API or UI)
      await expect(searchPage.navBar).toBeVisible();
    });
  });

  test.describe('Search Results', () => {
    test('displays search results with details', async () => {
      await searchPage.performTextSearch('test');

      const resultCount = await searchPage.getSearchResults();
      if (resultCount > 0) {
        const details = await searchPage.getResultDetails(0);
        expect(details.title).toBeTruthy();
        expect(details.path).toBeTruthy();
      }
    });

    test('handles result selection', async () => {
      await searchPage.performTextSearch('test');

      const resultCount = await searchPage.getSearchResults();
      if (resultCount > 0) {
        await searchPage.selectSearchResult(0);
        // Should open detail view or perform action
        await searchPage.page.waitForTimeout(500);
      }
    });

    test('shows loading state during search', async ({ page }) => {
      // Intercept and delay API response
      await page.route('**/api/search*', async route => {
        await new Promise(resolve => setTimeout(resolve, 1000));
        await route.continue();
      });

      const searchPromise = searchPage.performTextSearch('test');

      // Check for loading indicator
      await expect(searchPage.loadingSpinner).toBeVisible();

      await searchPromise;
    });
  });

  test.describe('Search Mode Switching', () => {
    test('switches between all search modes', async () => {
      // Text search
      await searchPage.textSearchButton.click();
      let activeMode = await searchPage.getActiveSearchMode();
      expect(activeMode).toContain('Text Search');

      // Semantic search
      await searchPage.semanticSearchButton.click();
      activeMode = await searchPage.getActiveSearchMode();
      expect(activeMode).toContain('Semantic Search');

      // Image search
      await searchPage.imageSearchButton.click();
      activeMode = await searchPage.getActiveSearchMode();
      expect(activeMode).toContain('Image Search');
    });

    test('preserves search query when switching modes', async () => {
      const query = 'test query';

      // Enter query in text search
      await searchPage.textSearchButton.click();
      await searchPage.searchInput.fill(query);

      // Switch to semantic search
      await searchPage.semanticSearchButton.click();

      // Query should be preserved
      const currentValue = await searchPage.searchInput.inputValue();
      expect(currentValue).toBe(query);
    });
  });
});