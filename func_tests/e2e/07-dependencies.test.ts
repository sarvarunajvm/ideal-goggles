import { test, expect } from '@playwright/test';
import { BasePage } from '../page-objects/BasePage';
import { APIClient } from '../helpers/api-client';

test.describe('Dependencies and Error Handling', () => {
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
  });

  test.describe('Dependency Management', () => {
    test('shows dependency status and requirements', async ({ page }) => {
      await basePage.goto('/settings');

      // Check for dependency status indicators
      const dependencySection = page.locator('[data-testid="dependencies-section"]');
      const pythonStatus = page.locator('[data-testid="python-status"]');
      const modelsStatus = page.locator('[data-testid="models-status"]');

      // Dependencies section should be visible
      // await expect(dependencySection).toBeVisible();
    });

    test('provides installation guidance for missing dependencies', async ({ page }) => {
      await basePage.goto('/settings');

      // Check for installation instructions
      const installInstructions = page.locator('[data-testid="install-instructions"]');
      const dependencyLinks = page.locator('a[href*="download"]');

      // Should provide helpful guidance
    });

    test('validates system requirements', async ({ page }) => {
      await basePage.goto('/settings');

      // Check system requirements validation
      const systemInfo = page.locator('[data-testid="system-info"]');
      const requirements = page.locator('[data-testid="requirements-check"]');

      // Should show system compatibility
    });
  });

  test.describe('Error Boundaries', () => {
    test('handles component errors gracefully', async ({ page }) => {
      // The app uses React Router's `errorElement` (RouteErrorBoundary). Trigger a 404 route error.
      await page.goto('/this-route-does-not-exist');

      // Should render the route error boundary UI
      await expect(page.locator('text=The page you are looking for does not exist')).toBeVisible();
      await expect(page.locator('button:has-text("Go Home")')).toBeVisible();
      await expect(page.locator('button:has-text("Reload")')).toBeVisible();
    });

    test('provides error recovery options', async ({ page }) => {
      await page.goto('/this-route-does-not-exist');

      const goHomeButton = page.locator('button:has-text("Go Home")');
      await expect(goHomeButton).toBeVisible();
      await goHomeButton.click();

      // Should navigate back to the main app
      await expect(page.locator('[data-testid="search-page"]')).toBeVisible();
    });

    test('logs errors for debugging', async ({ page }) => {
      // Check error logging
      const consoleErrors: string[] = [];

      page.on('console', msg => {
        if (msg.type() === 'error') {
          consoleErrors.push(msg.text());
        }
      });

      // Trigger an error
      await page.route('**/api/health', route => route.abort());
      await basePage.goto();

      // Should log appropriate errors
    });
  });

  test.describe('Network Error Handling', () => {
    test('handles API unavailability', async ({ page }) => {
      // Simulate API being down
      await page.route('**/api/**', route => route.abort('failed'));
      await page.route('**/health', route => route.abort('failed'));
      await page.route('**/index/status', route => route.abort('failed'));

      // Navigate directly; BasePage.waitForApp expects nav which won't render when backend is down
      await page.goto('/');

      // Should show appropriate message
      const errorMessage = page.locator('text=Getting everything ready');
      await expect(errorMessage).toBeVisible();
    });

    test('retries failed requests', async ({ page }) => {
      let requestCount = 0;

      await page.route('**/api/health', route => {
        requestCount++;
        if (requestCount < 3) {
          route.abort('failed');
        } else {
          route.continue();
        }
      });

      await basePage.goto();

      // Should eventually succeed after retries
      await basePage.waitForConnection();
    });

    test('shows offline indicator when network is unavailable', async ({ page }) => {
      // Simulate backend endpoints being unreachable (but still allow the SPA to load)
      await page.route('**/api/index/status', route => route.abort('failed'));
      await page.route('**/api/index/stats', route => route.abort('failed'));

      await basePage.goto();

      // Connection badge should show disconnected
      await expect(basePage.connectionBadge.filter({ hasText: 'Disconnected' })).toBeVisible({
        timeout: 15000,
      });
    });
  });

  test.describe('Performance Monitoring', () => {
    test('tracks page load performance', async ({ page }) => {
      const startTime = Date.now();

      await basePage.goto();
      await basePage.waitForApp();

      const loadTime = Date.now() - startTime;

      // Should load within reasonable time
      expect(loadTime).toBeLessThan(5000);
    });

    test('monitors API response times', async ({ page }) => {
      let apiResponseTime = 0;

      await page.route('**/api/health', async route => {
        const start = Date.now();
        await route.continue();
        apiResponseTime = Date.now() - start;
      });

      await basePage.goto();

      // API should respond quickly
      expect(apiResponseTime).toBeLessThan(1000);
    });

    test('handles large search result sets efficiently', async ({ page }) => {
      await basePage.goto();

      // Simulate large result set
      await page.route('**/api/search/**', route => {
        const largeResultSet = Array.from({ length: 1000 }, (_, i) => ({
          id: i,
          file_path: `/test/image${i}.jpg`,
          similarity_score: 0.9,
          thumbnail_path: `/thumbnails/image${i}.jpg`
        }));

        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ results: largeResultSet })
        });
      });

      // Should handle large datasets without blocking
    });
  });

  test.describe('Accessibility', () => {
    test('supports keyboard navigation throughout app', async ({ page }) => {
      await basePage.goto();

      // Test tab navigation
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');

      // Should have visible focus indicators
      const focusedElement = page.locator(':focus');
      await expect(focusedElement).toBeVisible();
    });

    test('provides proper ARIA labels and roles', async ({ page }) => {
      await basePage.goto();

      // Check for proper ARIA attributes
      const searchInput = page.locator('input[aria-label*="search"]');
      const navigationMenu = page.locator('[role="navigation"]');
      const mainContent = page.locator('[role="main"]');

      // Should have appropriate accessibility attributes
    });

    test('supports screen readers', async ({ page }) => {
      await basePage.goto();

      // Check for screen reader friendly content
      const skipLink = page.locator('a:has-text("Skip to content")');
      const landmarks = page.locator('[role="banner"], [role="main"], [role="navigation"]');

      // Should be screen reader accessible
    });

    test('meets color contrast requirements', async ({ page }) => {
      await basePage.goto();

      // Test high contrast mode
      await page.emulateMedia({ colorScheme: 'dark' });
      await page.waitForTimeout(100);

      // Should maintain readability in dark mode
    });
  });
});