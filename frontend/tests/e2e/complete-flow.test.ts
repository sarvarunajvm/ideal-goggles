/**
 * End-to-end test for complete application flow
 */

import { test, expect } from '@playwright/test';

test.describe('Complete Application Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Start from the home page
    await page.goto('http://localhost:3000');
  });

  test('complete user journey from indexing to search', async ({ page }) => {
    // Step 1: Navigate to settings
    await page.click('[data-testid="settings-button"]');
    await expect(page).toHaveURL(/.*settings/);

    // Step 2: Configure photo directories
    await page.click('[data-testid="add-directory-button"]');
    await page.fill('[data-testid="directory-input"]', '/Users/photos');
    await page.click('[data-testid="save-directory-button"]');

    // Verify directory was added
    await expect(page.locator('[data-testid="directory-list"]')).toContainText('/Users/photos');

    // Step 3: Start indexing
    await page.click('[data-testid="indexing-tab"]');
    await page.click('[data-testid="start-indexing-button"]');

    // Wait for indexing to start
    await expect(page.locator('[data-testid="indexing-status"]')).toContainText('Indexing in progress');

    // Mock quick indexing completion for testing
    await page.waitForTimeout(2000);

    // Step 4: Navigate to search
    await page.click('[data-testid="search-nav-button"]');
    await expect(page).toHaveURL(/.*search/);

    // Step 5: Perform text search
    await page.fill('[data-testid="search-input"]', 'vacation photos');
    await page.press('[data-testid="search-input"]', 'Enter');

    // Wait for results
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible();
    await expect(page.locator('[data-testid="photo-grid"] img')).toHaveCount.greaterThan(0);

    // Step 6: Open photo viewer
    await page.click('[data-testid="photo-grid"] img:first-child');
    await expect(page.locator('[data-testid="photo-viewer"]')).toBeVisible();

    // Navigate through photos
    await page.click('[data-testid="next-photo-button"]');
    await page.click('[data-testid="previous-photo-button"]');

    // Close viewer
    await page.press('body', 'Escape');
    await expect(page.locator('[data-testid="photo-viewer"]')).not.toBeVisible();

    // Step 7: Switch to semantic search
    await page.click('[data-testid="search-mode-dropdown"]');
    await page.click('[data-testid="semantic-search-option"]');

    await page.fill('[data-testid="search-input"]', 'happy family moments');
    await page.press('[data-testid="search-input"]', 'Enter');

    // Verify semantic results
    await expect(page.locator('[data-testid="search-type-indicator"]')).toContainText('Semantic');

    // Step 8: Apply filters
    await page.click('[data-testid="filter-button"]');
    await page.fill('[data-testid="date-from-input"]', '2024-01-01');
    await page.fill('[data-testid="date-to-input"]', '2024-12-31');
    await page.click('[data-testid="apply-filters-button"]');

    // Verify filtered results
    await expect(page.locator('[data-testid="active-filters"]')).toContainText('2024');

    // Step 9: Select multiple photos
    await page.click('[data-testid="select-mode-button"]');
    await page.click('[data-testid="photo-checkbox-1"]');
    await page.click('[data-testid="photo-checkbox-2"]');
    await page.click('[data-testid="photo-checkbox-3"]');

    // Perform batch action
    await page.click('[data-testid="batch-actions-button"]');
    await page.click('[data-testid="export-selected-button"]');

    // Verify export dialog
    await expect(page.locator('[data-testid="export-dialog"]')).toBeVisible();
  });

  test('face recognition flow', async ({ page }) => {
    // Navigate to people section
    await page.click('[data-testid="people-nav-button"]');
    await expect(page).toHaveURL(/.*people/);

    // View detected faces
    await expect(page.locator('[data-testid="face-clusters"]')).toBeVisible();

    // Click on a face cluster
    await page.click('[data-testid="face-cluster-1"]');

    // View all photos with this person
    await expect(page.locator('[data-testid="person-photos"]')).toBeVisible();
    await expect(page.locator('[data-testid="photo-grid"] img')).toHaveCount.greaterThan(0);

    // Name the person
    await page.click('[data-testid="name-person-button"]');
    await page.fill('[data-testid="person-name-input"]', 'John Doe');
    await page.click('[data-testid="save-person-name-button"]');

    // Verify name was saved
    await expect(page.locator('[data-testid="person-name"]')).toContainText('John Doe');

    // Search by person
    await page.click('[data-testid="search-nav-button"]');
    await page.click('[data-testid="search-mode-dropdown"]');
    await page.click('[data-testid="face-search-option"]');

    await page.click('[data-testid="select-person-button"]');
    await page.click('[data-testid="person-john-doe"]');

    // Verify face search results
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible();
  });

  test('keyboard shortcuts', async ({ page }) => {
    // Test search shortcut
    await page.keyboard.press('Control+K');
    await expect(page.locator('[data-testid="search-input"]')).toBeFocused();

    // Test navigation shortcuts
    await page.keyboard.press('G H'); // Go to home
    await expect(page).toHaveURL('http://localhost:3000');

    await page.keyboard.press('G S'); // Go to settings
    await expect(page).toHaveURL(/.*settings/);

    await page.keyboard.press('G P'); // Go to people
    await expect(page).toHaveURL(/.*people/);

    // Test photo viewer shortcuts
    await page.goto('http://localhost:3000/search');
    await page.fill('[data-testid="search-input"]', 'test');
    await page.press('[data-testid="search-input"]', 'Enter');

    await page.waitForSelector('[data-testid="photo-grid"] img');
    await page.click('[data-testid="photo-grid"] img:first-child');

    await page.keyboard.press('ArrowRight'); // Next photo
    await page.keyboard.press('ArrowLeft'); // Previous photo
    await page.keyboard.press('F'); // Fullscreen
    await page.keyboard.press('Escape'); // Exit fullscreen
  });

  test('responsive mobile view', async ({ page, viewport }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Check mobile menu
    await expect(page.locator('[data-testid="mobile-menu-button"]')).toBeVisible();
    await page.click('[data-testid="mobile-menu-button"]');
    await expect(page.locator('[data-testid="mobile-menu"]')).toBeVisible();

    // Navigate using mobile menu
    await page.click('[data-testid="mobile-search-link"]');
    await expect(page).toHaveURL(/.*search/);

    // Check responsive grid
    const gridItems = await page.locator('[data-testid="photo-grid"] > *').count();
    expect(gridItems).toBeGreaterThan(0);

    // Verify single column layout on mobile
    const firstItem = await page.locator('[data-testid="photo-grid"] > *:first-child').boundingBox();
    const secondItem = await page.locator('[data-testid="photo-grid"] > *:nth-child(2)').boundingBox();

    if (firstItem && secondItem) {
      expect(firstItem.x).toBe(secondItem.x); // Same x position = single column
    }
  });

  test('error handling and recovery', async ({ page }) => {
    // Simulate network error
    await page.route('**/api/search/**', route => route.abort());

    await page.fill('[data-testid="search-input"]', 'test');
    await page.press('[data-testid="search-input"]', 'Enter');

    // Should show error message
    await expect(page.locator('[data-testid="error-message"]')).toContainText(/error|failed/i);

    // Should have retry button
    await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();

    // Re-enable network and retry
    await page.unroute('**/api/search/**');
    await page.click('[data-testid="retry-button"]');

    // Should work now
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible();
  });

  test('accessibility', async ({ page }) => {
    // Check ARIA labels
    const searchInput = page.locator('[data-testid="search-input"]');
    await expect(searchInput).toHaveAttribute('aria-label', /search/i);

    // Check keyboard navigation
    await page.keyboard.press('Tab');
    const activeElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(activeElement).toBeTruthy();

    // Check contrast ratios (would need axe-playwright for comprehensive testing)
    const backgroundColor = await page.locator('body').evaluate(el =>
      window.getComputedStyle(el).backgroundColor
    );
    expect(backgroundColor).toBeTruthy();

    // Check alt texts for images
    const images = page.locator('img');
    const imageCount = await images.count();

    for (let i = 0; i < Math.min(imageCount, 5); i++) {
      const altText = await images.nth(i).getAttribute('alt');
      expect(altText).toBeTruthy();
    }
  });

  test('performance monitoring', async ({ page }) => {
    // Measure initial load time
    const startTime = Date.now();
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    const loadTime = Date.now() - startTime;

    expect(loadTime).toBeLessThan(3000); // Should load within 3 seconds

    // Measure search response time
    const searchStartTime = Date.now();
    await page.fill('[data-testid="search-input"]', 'test');
    await page.press('[data-testid="search-input"]', 'Enter');
    await page.waitForSelector('[data-testid="search-results"]');
    const searchTime = Date.now() - searchStartTime;

    expect(searchTime).toBeLessThan(2000); // Search should complete within 2 seconds

    // Check for memory leaks (basic check)
    const initialMemory = await page.evaluate(() => {
      if (performance.memory) {
        return performance.memory.usedJSHeapSize;
      }
      return 0;
    });

    // Perform multiple searches
    for (let i = 0; i < 10; i++) {
      await page.fill('[data-testid="search-input"]', `test ${i}`);
      await page.press('[data-testid="search-input"]', 'Enter');
      await page.waitForTimeout(100);
    }

    const finalMemory = await page.evaluate(() => {
      if (performance.memory) {
        return performance.memory.usedJSHeapSize;
      }
      return 0;
    });

    // Memory shouldn't increase dramatically
    if (initialMemory > 0 && finalMemory > 0) {
      const memoryIncrease = finalMemory - initialMemory;
      expect(memoryIncrease).toBeLessThan(50 * 1024 * 1024); // Less than 50MB increase
    }
  });
});