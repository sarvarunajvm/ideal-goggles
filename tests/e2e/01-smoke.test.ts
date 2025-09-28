import { test, expect } from '@playwright/test';
import { BasePage } from '../page-objects/BasePage';
import { APIClient } from '../helpers/api-client';

test.describe('Smoke Tests', () => {
  let basePage: BasePage;
  let apiClient: APIClient;

  test.beforeAll(async () => {
    apiClient = new APIClient();
    await apiClient.initialize();
  });

  test.afterAll(async () => {
    await apiClient.dispose();
  });

  test.beforeEach(async ({ page }) => {
    basePage = new BasePage(page);
    await basePage.goto();
  });

  test('application loads successfully', async ({ page }) => {
    await expect(basePage.navBar).toBeVisible();
    await expect(page).toHaveTitle(/Photo Search/i);
  });

  test('backend API is accessible', async () => {
    const response = await apiClient.checkHealth();
    expect(response.ok).toBeTruthy();

    const health = await response.json();
    expect(health).toHaveProperty('status');
    expect(health.status).toBe('healthy');
  });

  test('navigation links are visible and functional', async ({ page }) => {
    // Check all navigation links are visible
    await expect(basePage.searchLink).toBeVisible();
    await expect(basePage.settingsLink).toBeVisible();
    await expect(basePage.peopleLink).toBeVisible();

    // Test navigation to each page
    await basePage.navigateToSettings();
    await expect(page).toHaveURL(/\/settings/);

    await basePage.navigateToPeople();
    await expect(page).toHaveURL(/\/people/);

    await basePage.navigateToSearch();
    await expect(page).toHaveURL(/\//);
  });

  test('connection status indicator shows connected', async () => {
    await basePage.waitForConnection();
    const isConnected = await basePage.isConnected();
    expect(isConnected).toBeTruthy();
  });

  test('API documentation button is accessible', async ({ page }) => {
    await expect(basePage.apiDocsButton).toBeVisible();

    // Click should open API docs (in new tab/window in real app)
    const [newPage] = await Promise.all([
      page.waitForEvent('popup'),
      basePage.apiDocsButton.click()
    ]).catch(() => [null]);

    // If popup opens, verify it loads
    if (newPage) {
      await newPage.waitForLoadState();
      await newPage.close();
    }
  });

  test('responsive design works on different screen sizes', async ({ page }) => {
    const viewports = [
      { width: 1920, height: 1080, name: 'Desktop' },
      { width: 768, height: 1024, name: 'Tablet' },
      { width: 375, height: 667, name: 'Mobile' }
    ];

    for (const viewport of viewports) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.waitForTimeout(100); // Allow time for responsive adjustments

      // Navigation should still be visible
      await expect(basePage.navBar).toBeVisible();

      // Verify active page indicator works
      const activeNav = await basePage.getActiveNavItem();
      expect(activeNav).toBeTruthy();
    }
  });

  test('error handling when backend is unavailable', async ({ page }) => {
    // Intercept API calls and simulate backend failure
    await page.route('**/health', route => {
      route.abort('failed');
    });
    await page.route('**/api/**', route => {
      route.abort('failed');
    });

    // Reload page
    await page.reload();

    // App should show loading/waiting screen when backend is unavailable
    await expect(page.locator('text=Starting local backend')).toBeVisible();

    // Should show the backend URL it's trying to connect to
    await expect(page.locator('code')).toContainText('/api');

    // Should show helpful message about waiting
    await expect(page.locator('text=/If this persists/')).toBeVisible();
  });
});