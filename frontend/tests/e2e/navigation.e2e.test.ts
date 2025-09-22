/**
 * End-to-end tests for application navigation
 */

import { test, expect, Page } from '@playwright/test';

test.describe('Application Navigation', () => {
  let page: Page;

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();

    // Mock basic API responses
    await page.route('/api/health', (route) => {
      route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'healthy',
          timestamp: new Date().toISOString()
        })
      });
    });

    await page.route('/api/config', (route) => {
      route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({
          roots: ['/test/photos'],
          ocr_languages: ['eng'],
          face_search_enabled: true,
          index_version: '1.0.0'
        })
      });
    });

    await page.route('/api/index/status', (route) => {
      route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'idle',
          progress: {
            total_files: 0,
            processed_files: 0,
            current_phase: 'idle'
          },
          errors: [],
          started_at: null,
          estimated_completion: null
        })
      });
    });

    await page.goto('http://localhost:5173');
  });

  test('should display main navigation menu', async () => {
    // Verify main navigation elements
    await expect(page.locator('[data-testid="nav-search"]')).toBeVisible();
    await expect(page.locator('[data-testid="nav-settings"]')).toBeVisible();
    await expect(page.locator('[data-testid="nav-people"]')).toBeVisible();
  });

  test('should navigate to search page by default', async () => {
    // Verify we start on search page
    await expect(page.locator('[data-testid="search-page"]')).toBeVisible();
    await expect(page.locator('[data-testid="search-input"]')).toBeVisible();

    // Verify URL
    expect(page.url()).toContain('/');
  });

  test('should navigate to settings page', async () => {
    // Click settings navigation
    await page.click('[data-testid="nav-settings"]');

    // Verify settings page loads
    await expect(page.locator('[data-testid="settings-page"]')).toBeVisible();
    await expect(page.locator('[data-testid="settings-title"]')).toContainText('Settings');

    // Verify URL changed
    expect(page.url()).toContain('/settings');
  });

  test('should navigate to people management page', async () => {
    // Mock people API
    await page.route('/api/people', (route) => {
      route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 1,
            name: 'John Doe',
            sample_count: 5,
            created_at: '2023-01-01T00:00:00Z',
            active: true
          }
        ])
      });
    });

    // Click people navigation
    await page.click('[data-testid="nav-people"]');

    // Verify people page loads
    await expect(page.locator('[data-testid="people-page"]')).toBeVisible();
    await expect(page.locator('[data-testid="people-title"]')).toContainText('People');

    // Verify URL changed
    expect(page.url()).toContain('/people');
  });

  test('should maintain navigation state across page reloads', async () => {
    // Navigate to settings
    await page.click('[data-testid="nav-settings"]');
    await expect(page.locator('[data-testid="settings-page"]')).toBeVisible();

    // Reload page
    await page.reload();

    // Verify we're still on settings page
    await expect(page.locator('[data-testid="settings-page"]')).toBeVisible();
    expect(page.url()).toContain('/settings');
  });

  test('should handle browser back/forward navigation', async () => {
    // Navigate through pages
    await page.click('[data-testid="nav-settings"]');
    await expect(page.locator('[data-testid="settings-page"]')).toBeVisible();

    await page.click('[data-testid="nav-people"]');
    await expect(page.locator('[data-testid="people-page"]')).toBeVisible();

    // Use browser back button
    await page.goBack();
    await expect(page.locator('[data-testid="settings-page"]')).toBeVisible();

    // Use browser forward button
    await page.goForward();
    await expect(page.locator('[data-testid="people-page"]')).toBeVisible();
  });

  test('should highlight active navigation item', async () => {
    // Check default active state (search)
    await expect(page.locator('[data-testid="nav-search"]')).toHaveClass(/active/);

    // Navigate to settings
    await page.click('[data-testid="nav-settings"]');
    await expect(page.locator('[data-testid="nav-settings"]')).toHaveClass(/active/);
    await expect(page.locator('[data-testid="nav-search"]')).not.toHaveClass(/active/);

    // Navigate to people
    await page.click('[data-testid="nav-people"]');
    await expect(page.locator('[data-testid="nav-people"]')).toHaveClass(/active/);
    await expect(page.locator('[data-testid="nav-settings"]')).not.toHaveClass(/active/);
  });

  test('should display status bar with system information', async () => {
    // Verify status bar is visible
    await expect(page.locator('[data-testid="status-bar"]')).toBeVisible();

    // Verify connection status
    await expect(page.locator('[data-testid="connection-status"]')).toBeVisible();
    await expect(page.locator('[data-testid="connection-status"]')).toContainText('Connected to API');

    // Verify indexing status
    await expect(page.locator('[data-testid="indexing-status"]')).toBeVisible();
    await expect(page.locator('[data-testid="indexing-status"]')).toContainText('idle');
  });

  test('should handle disconnected state', async () => {
    // Mock API failure
    await page.route('/api/health', (route) => {
      route.abort('failed');
    });

    // Wait for status update
    await page.waitForTimeout(6000); // Status checks every 5 seconds

    // Verify disconnected state
    await expect(page.locator('[data-testid="connection-status"]')).toContainText('Disconnected from API');
    await expect(page.locator('[data-testid="connection-indicator"]')).toHaveClass(/red/);
  });

  test('should show indexing progress when active', async () => {
    // Mock active indexing
    await page.route('/api/index/status', (route) => {
      route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'indexing',
          progress: {
            total_files: 1000,
            processed_files: 350,
            current_phase: 'embeddings'
          },
          errors: [],
          started_at: new Date().toISOString(),
          estimated_completion: new Date(Date.now() + 600000).toISOString()
        })
      });
    });

    // Wait for status update
    await page.waitForTimeout(1000);

    // Verify indexing progress display
    await expect(page.locator('[data-testid="indexing-status"]')).toContainText('indexing');
    await expect(page.locator('[data-testid="indexing-progress"]')).toContainText('350/1000');
    await expect(page.locator('[data-testid="indexing-phase"]')).toContainText('embeddings');
  });

  test('should provide keyboard navigation support', async () => {
    // Focus first navigation item
    await page.keyboard.press('Tab');
    await expect(page.locator('[data-testid="nav-search"]')).toBeFocused();

    // Navigate with arrow keys
    await page.keyboard.press('ArrowRight');
    await expect(page.locator('[data-testid="nav-settings"]')).toBeFocused();

    await page.keyboard.press('ArrowRight');
    await expect(page.locator('[data-testid="nav-people"]')).toBeFocused();

    // Activate with Enter key
    await page.keyboard.press('Enter');
    await expect(page.locator('[data-testid="people-page"]')).toBeVisible();
  });

  test('should handle rapid navigation clicks', async () => {
    // Rapidly click between navigation items
    const navigationItems = ['nav-settings', 'nav-people', 'nav-search', 'nav-settings'];

    for (const item of navigationItems) {
      await page.click(`[data-testid="${item}"]`);
      await page.waitForTimeout(50); // Small delay to simulate rapid clicking
    }

    // Verify final state
    await expect(page.locator('[data-testid="settings-page"]')).toBeVisible();
    expect(page.url()).toContain('/settings');
  });

  test('should display app version and metadata', async () => {
    // Check if version info is displayed (typically in footer or about section)
    const versionElement = page.locator('[data-testid="app-version"]');
    if (await versionElement.isVisible()) {
      await expect(versionElement).toContainText(/v\d+\.\d+\.\d+/);
    }
  });

  test('should handle navigation during search operations', async () => {
    // Start a search operation
    await page.fill('[data-testid="search-input"]', 'test');

    // Mock slow search response
    await page.route('/api/search*', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 2000));
      route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({
          query: 'test',
          total_matches: 0,
          took_ms: 2000,
          items: []
        })
      });
    });

    // Start search
    const searchPromise = page.click('[data-testid="search-button"]');

    // Try to navigate during search
    await page.click('[data-testid="nav-settings"]');

    // Verify navigation works even during search
    await expect(page.locator('[data-testid="settings-page"]')).toBeVisible();

    // Wait for search to complete (should not affect current page)
    await searchPromise;
  });
});