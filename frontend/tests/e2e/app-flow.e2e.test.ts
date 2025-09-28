/**
 * End-to-end tests for complete application flows
 */

import { test, expect } from '@playwright/test';

test.describe('Application End-to-End Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Wait for backend to be ready
    await page.goto('http://localhost:3000');

    // Wait for app to load (backend check completes)
    await page.waitForSelector('nav', { timeout: 30000 });
  });

  test('complete search workflow', async ({ page }) => {
    // Should be on search page by default
    await expect(page).toHaveURL('http://localhost:3000/');

    // Check navigation is visible
    await expect(page.locator('nav')).toBeVisible();
    await expect(page.locator('h1:has-text("Photo Search")')).toBeVisible();

    // Test text search mode (default)
    const searchInput = page.locator('input[placeholder*="Search by filename"]');
    await expect(searchInput).toBeVisible();

    // Enter search query
    await searchInput.fill('vacation photos');
    await searchInput.press('Enter');

    // Wait for search to complete (loading state changes)
    await page.waitForTimeout(500);

    // Switch to semantic search
    const semanticButton = page.locator('button:has-text("Semantic Search")');
    await semanticButton.click();

    // Check placeholder changed
    const semanticInput = page.locator('input[placeholder*="Describe what"]');
    await expect(semanticInput).toBeVisible();

    // Perform semantic search
    await semanticInput.fill('happy family moments at the beach');
    await semanticInput.press('Enter');

    // Wait for results
    await page.waitForTimeout(500);

    // Switch to image search
    const imageButton = page.locator('button:has-text("Image Search")');
    await imageButton.click();

    // Check upload area is visible
    await expect(page.locator('text=Upload an image to search')).toBeVisible();
  });

  test('navigation between pages', async ({ page }) => {
    // Start on search page
    await expect(page.locator('a:has-text("Search")')).toHaveClass(/bg-blue-100/);

    // Navigate to Settings
    await page.click('a:has-text("Settings")');
    await expect(page).toHaveURL('http://localhost:3000/settings');
    await expect(page.locator('a:has-text("Settings")')).toHaveClass(/bg-blue-100/);

    // Navigate to People
    await page.click('a:has-text("People")');
    await expect(page).toHaveURL('http://localhost:3000/people');
    await expect(page.locator('a:has-text("People")')).toHaveClass(/bg-blue-100/);

    // Navigate back to Search
    await page.click('a:has-text("Search")');
    await expect(page).toHaveURL('http://localhost:3000/');
    await expect(page.locator('a:has-text("Search")')).toHaveClass(/bg-blue-100/);
  });

  test('backend connection status', async ({ page }) => {
    // Check connection status indicator
    const statusIndicator = page.locator('.w-2.h-2.rounded-full');

    // Should show connected status (green)
    await expect(statusIndicator.first()).toHaveClass(/bg-green-500/);
    await expect(page.locator('text=Connected')).toBeVisible();
  });

  test('search mode switching', async ({ page }) => {
    // Text search is default
    let activeButton = page.locator('button.bg-blue-600:has-text("Text Search")');
    await expect(activeButton).toBeVisible();

    // Switch to Semantic
    await page.click('button:has-text("Semantic Search")');
    activeButton = page.locator('button.bg-blue-600:has-text("Semantic Search")');
    await expect(activeButton).toBeVisible();

    // Switch to Image
    await page.click('button:has-text("Image Search")');
    activeButton = page.locator('button.bg-blue-600:has-text("Image Search")');
    await expect(activeButton).toBeVisible();

    // Switch back to Text
    await page.click('button:has-text("Text Search")');
    activeButton = page.locator('button.bg-blue-600:has-text("Text Search")');
    await expect(activeButton).toBeVisible();
  });

  test('filter panel toggle', async ({ page }) => {
    const filterButton = page.locator('button:has-text("Filters")');
    await expect(filterButton).toBeVisible();

    // Click to expand filters
    await filterButton.click();

    // Check if filter panel appears (implementation dependent)
    // This would depend on actual filter panel implementation
    await page.waitForTimeout(300);

    // Click again to collapse
    await filterButton.click();
    await page.waitForTimeout(300);
  });

  test('responsive design', async ({ page }) => {
    // Test desktop view
    await page.setViewportSize({ width: 1920, height: 1080 });
    await expect(page.locator('nav')).toBeVisible();

    // Test tablet view
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.locator('nav')).toBeVisible();

    // Test mobile view
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.locator('nav')).toBeVisible();

    // Navigation should still work on mobile
    await page.click('a:has-text("Settings")');
    await expect(page).toHaveURL('http://localhost:3000/settings');
  });

  test('keyboard navigation', async ({ page }) => {
    // Focus search input with Tab
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    // Type in search
    await page.keyboard.type('test search');

    // Submit with Enter
    await page.keyboard.press('Enter');

    // Wait for any search action
    await page.waitForTimeout(500);
  });

  test('loading states', async ({ page }) => {
    // Enter search to trigger loading
    const searchInput = page.locator('input[placeholder*="Search"]');
    await searchInput.fill('test query');

    // Mock slow response by intercepting
    await page.route('**/api/search*', async route => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      await route.continue();
    });

    await searchInput.press('Enter');

    // Check for loading indicator (spinner in button)
    const searchButton = page.locator('button[type="submit"]');
    const spinner = searchButton.locator('.animate-spin');

    // Loading state might be brief, so we check if button is disabled
    await expect(searchButton).toBeDisabled();
  });

  test('error handling', async ({ page }) => {
    // Intercept API calls and return errors
    await page.route('**/api/search*', route => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ error: 'Internal server error' })
      });
    });

    const searchInput = page.locator('input[placeholder*="Search"]');
    await searchInput.fill('error test');
    await searchInput.press('Enter');

    // Wait for error handling
    await page.waitForTimeout(1000);

    // App should remain functional
    await expect(page.locator('nav')).toBeVisible();
  });

  test('empty state display', async ({ page }) => {
    // On initial load, should show empty state
    await expect(page.locator('text=Search Your Photos')).toBeVisible();
    await expect(page.locator('text=Enter a search term')).toBeVisible();

    // Should show search mode descriptions
    await expect(page.locator('text=Text Search').first()).toBeVisible();
    await expect(page.locator('text=Semantic Search').first()).toBeVisible();
    await expect(page.locator('text=Image Search').first()).toBeVisible();
  });

  test('api connection indicator', async ({ page }) => {
    // Check footer for API connection status
    const footer = page.locator('.bg-gray-100.border-t');
    await expect(footer).toBeVisible();

    // Should show API docs link
    const apiDocsButton = page.locator('button:has-text("API Docs")');
    await expect(apiDocsButton).toBeVisible();

    // Click API docs (would open in new window/tab in real app)
    await apiDocsButton.click();
  });

  test('search input validation', async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="Search"]');
    const searchButton = page.locator('button[type="submit"]');

    // Empty search should have disabled button
    await searchInput.clear();
    await expect(searchButton).toBeDisabled();

    // With text, button should be enabled
    await searchInput.fill('valid search');
    await expect(searchButton).not.toBeDisabled();

    // Whitespace only should be treated as empty
    await searchInput.clear();
    await searchInput.fill('   ');
    await expect(searchButton).toBeDisabled();
  });
});