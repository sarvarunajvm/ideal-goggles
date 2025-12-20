import { test, expect } from '@playwright/test';
import { BasePage } from '../page-objects/BasePage';
import { SearchPage } from '../page-objects/SearchPage';
import { APIClient } from '../helpers/api-client';
import { TestData } from '../helpers/test-data';

test.describe('Lightbox Keyboard Navigation E2E Test', () => {
  let basePage: BasePage;
  let searchPage: SearchPage;
  let apiClient: APIClient;

  test.beforeAll(async () => {
    apiClient = new APIClient();
    await apiClient.initialize();
    
    // Ensure we have test data
    await TestData.createTestImages(5);
  });

  test.afterAll(async () => {
    await apiClient.dispose();
  });

  test.beforeEach(async ({ page }) => {
    basePage = new BasePage(page);
    searchPage = new SearchPage(page);
    await searchPage.goto();
    
    // Perform search to populate results
    await searchPage.textSearchButton.click();
    await searchPage.searchInput.fill('');
    await searchPage.performSearch();
    await page.waitForTimeout(1000);
  });

  test('should open lightbox when clicking on a photo', async ({ page }) => {
    // Click on the first photo result
    const firstPhoto = page.locator('[data-testid="search-result-item"]').first();
    await firstPhoto.waitFor({ state: 'visible', timeout: 10000 });
    await firstPhoto.click();

    // Verify lightbox opens
    const lightbox = page.locator('[data-testid="lightbox"]');
    await expect(lightbox).toBeVisible({ timeout: 5000 });

    // Verify image is loaded
    const lightboxImage = page.locator('[data-testid="lightbox-image"]');
    await expect(lightboxImage).toBeVisible();

    // Verify navigation controls are present
    const prevButton = page.locator('[data-testid="lightbox-prev"]');
    const nextButton = page.locator('[data-testid="lightbox-next"]');
    await expect(prevButton).toBeVisible();
    await expect(nextButton).toBeVisible();
  });

  test('should navigate with arrow keys', async ({ page }) => {
    const firstPhoto = page.locator('[data-testid="search-result-item"]').first();
    await firstPhoto.click();
    await page.waitForSelector('[data-testid="lightbox"]');

    // Get initial image src
    const initialSrc = await page.locator('[data-testid="lightbox-image"]').getAttribute('src');

    // Press right arrow to go to next photo
    await page.keyboard.press('ArrowRight');
    await page.waitForTimeout(500); // Wait for animation

    // Verify image changed
    const nextSrc = await page.locator('[data-testid="lightbox-image"]').getAttribute('src');
    expect(nextSrc).not.toBe(initialSrc);

    // Press left arrow to go back
    await page.keyboard.press('ArrowLeft');
    await page.waitForTimeout(500);

    // Verify we're back to the first image
    const currentSrc = await page.locator('[data-testid="lightbox-image"]').getAttribute('src');
    expect(currentSrc).toBe(initialSrc);
  });

  test('should close lightbox with Escape key', async ({ page }) => {
    const firstPhoto = page.locator('[data-testid="search-result-item"]').first();
    await firstPhoto.click();
    await expect(page.locator('[data-testid="lightbox"]')).toBeVisible();

    // Press Escape
    await page.keyboard.press('Escape');

    // Verify lightbox is closed
    await expect(page.locator('[data-testid="lightbox"]')).not.toBeVisible({ timeout: 5000 });
  });

  test('should show metadata', async ({ page }) => {
    const firstPhoto = page.locator('[data-testid="search-result-item"]').first();
    await firstPhoto.click();
    await page.waitForSelector('[data-testid="lightbox"]');

    // Metadata should be visible
    const metadata = page.locator('[data-testid="lightbox-metadata"]');
    await expect(metadata).toBeVisible();
  });
});

test.describe('Lightbox Performance', () => {
  test('should open in less than 500ms', async ({ page }) => {
    const searchPage = new SearchPage(page);
    await searchPage.goto();
    await searchPage.textSearchButton.click();
    await searchPage.searchInput.fill('');
    await searchPage.performSearch();
    await page.waitForTimeout(1000);

    const startTime = Date.now();
    const firstPhoto = page.locator('[data-testid="search-result-item"]').first();
    await firstPhoto.click();
    await page.waitForSelector('[data-testid="lightbox"]');
    const endTime = Date.now();
    const loadTime = endTime - startTime;

    expect(loadTime).toBeLessThan(500);
  });
});