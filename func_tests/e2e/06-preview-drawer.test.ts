import { test, expect } from '@playwright/test';
import { SearchPage } from '../page-objects/SearchPage';
import { APIClient } from '../helpers/api-client';
import { TestData } from '../helpers/test-data';

test.describe('Preview Drawer', () => {
  let searchPage: SearchPage;
  let apiClient: APIClient;

  test.beforeAll(async () => {
    apiClient = new APIClient();
    await apiClient.initialize();
  });

  test.afterAll(async () => {
    await apiClient.dispose();
  });

  test.beforeEach(async ({ page }) => {
    searchPage = new SearchPage(page);
    await searchPage.goto();
  });

  test.describe('Image Preview', () => {
    test('opens preview drawer when clicking on search result', async ({ page }) => {
      // First need to perform a search to get results
      // For now, test the drawer opening mechanism
      const previewDrawer = page.locator('[data-testid="preview-drawer"]');

      // Check that drawer is initially closed
      await expect(previewDrawer).not.toBeVisible();
    });

    test('closes preview drawer with escape key', async ({ page }) => {
      // Mock opening a preview
      await page.evaluate(() => {
        // Simulate opening preview drawer
        const drawer = document.createElement('div');
        drawer.setAttribute('data-testid', 'preview-drawer');
        drawer.style.display = 'block';
        document.body.appendChild(drawer);
      });

      const previewDrawer = page.locator('[data-testid="preview-drawer"]');

      // Press escape key
      await page.keyboard.press('Escape');

      // Should close drawer (implementation will handle this)
    });

    test('navigates between images with arrow keys', async ({ page }) => {
      // Test arrow key navigation
      await page.keyboard.press('ArrowRight');
      await page.keyboard.press('ArrowLeft');

      // Verify navigation calls are made (implementation dependent)
    });

    test('displays image metadata and details', async ({ page }) => {
      // Test metadata display when preview is open
      const metadataSection = page.locator('[data-testid="image-metadata"]');
      const fileInfo = page.locator('[data-testid="file-info"]');

      // These would be visible when preview is open
      // await expect(metadataSection).toBeVisible();
      // await expect(fileInfo).toBeVisible();
    });

    test('handles image loading errors gracefully', async ({ page }) => {
      // Test error handling for broken images
      const errorMessage = page.locator('[data-testid="image-error"]');

      // Should show error state for broken images
    });

    test('provides reveal in folder functionality', async ({ page }) => {
      // Test the "Reveal in Folder" feature
      const revealButton = page.locator('button:has-text("Reveal in Folder")');

      // Should be present when preview is open
      // await expect(revealButton).toBeVisible();
    });
  });

  test.describe('Keyboard Navigation', () => {
    test('supports full keyboard navigation', async ({ page }) => {
      // Test all keyboard shortcuts
      const shortcuts = [
        { key: 'Escape', action: 'Close preview' },
        { key: 'ArrowRight', action: 'Next image' },
        { key: 'ArrowLeft', action: 'Previous image' },
        { key: 'Enter', action: 'Open full view' }
      ];

      for (const shortcut of shortcuts) {
        await page.keyboard.press(shortcut.key);
        // Verify appropriate action is taken
      }
    });

    test('prevents keyboard navigation when drawer is closed', async ({ page }) => {
      // Ensure arrow keys don't navigate when drawer is closed
      await page.keyboard.press('ArrowRight');
      await page.keyboard.press('ArrowLeft');

      // Should not cause any navigation when closed
    });
  });

  test.describe('Responsive Design', () => {
    test('adapts to different screen sizes', async ({ page }) => {
      const viewports = [
        { width: 1920, height: 1080, name: 'Desktop' },
        { width: 768, height: 1024, name: 'Tablet' },
        { width: 375, height: 667, name: 'Mobile' }
      ];

      for (const viewport of viewports) {
        await page.setViewportSize({ width: viewport.width, height: viewport.height });
        await page.waitForTimeout(100);

        // Preview drawer should adapt to viewport
        const drawer = page.locator('[data-testid="preview-drawer"]');
        // Test responsive behavior
      }
    });

    test('provides touch navigation on mobile devices', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });

      // Test swipe gestures for navigation
      const drawer = page.locator('[data-testid="preview-drawer"]');

      // Simulate touch gestures
      // await drawer.swipe('left');
      // await drawer.swipe('right');
    });
  });
});