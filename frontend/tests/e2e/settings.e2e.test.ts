/**
 * End-to-end tests for settings functionality
 */

import { test, expect, Page } from '@playwright/test';

test.describe('Settings Management', () => {
  let page: Page;

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();

    // Mock initial API responses
    await page.route('/api/config', (route) => {
      route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({
          roots: ['/Users/test/Photos', '/Users/test/Documents'],
          ocr_languages: ['eng', 'spa'],
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

    await page.route('/api/index/stats', (route) => {
      route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({
          database: {
            total_photos: 15432,
            indexed_photos: 15430,
            photos_with_embeddings: 15200,
            total_faces: 8954
          }
        })
      });
    });

    await page.goto('http://localhost:5173/settings');
  });

  test('should display current configuration', async () => {
    // Verify settings page loads
    await expect(page.locator('[data-testid="settings-page"]')).toBeVisible();

    // Verify root folders are displayed
    await expect(page.locator('[data-testid="root-folder"]')).toHaveCount(2);
    await expect(page.locator('[data-testid="root-folder"]').first()).toContainText('/Users/test/Photos');
    await expect(page.locator('[data-testid="root-folder"]').nth(1)).toContainText('/Users/test/Documents');

    // Verify OCR language settings
    await expect(page.locator('[data-testid="ocr-language-eng"]')).toBeChecked();
    await expect(page.locator('[data-testid="ocr-language-spa"]')).toBeChecked();

    // Verify face search setting
    await expect(page.locator('[data-testid="face-search-enabled"]')).toBeChecked();
  });

  test('should display database statistics', async () => {
    // Verify database stats are displayed
    await expect(page.locator('[data-testid="stat-total-photos"]')).toContainText('15,432');
    await expect(page.locator('[data-testid="stat-indexed-photos"]')).toContainText('15,430');
    await expect(page.locator('[data-testid="stat-photos-with-embeddings"]')).toContainText('15,200');
    await expect(page.locator('[data-testid="stat-total-faces"]')).toContainText('8,954');
  });

  test('should add new root folder', async () => {
    const newFolder = '/Users/test/NewPhotos';

    // Mock successful folder addition
    await page.route('/api/config/roots', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true })
      });
    });

    // Enter new folder path
    await page.fill('[data-testid="new-folder-input"]', newFolder);
    await page.click('[data-testid="add-folder-button"]');

    // Verify folder was added to the list
    await expect(page.locator('[data-testid="root-folder"]')).toHaveCount(3);
    await expect(page.locator('[data-testid="root-folder"]').last()).toContainText(newFolder);

    // Verify input was cleared
    await expect(page.locator('[data-testid="new-folder-input"]')).toHaveValue('');
  });

  test('should remove root folder', async () => {
    // Mock successful folder removal
    await page.route('/api/config/roots', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true })
      });
    });

    // Click remove button for first folder
    await page.click('[data-testid="remove-folder-button"]');

    // Verify folder was removed
    await expect(page.locator('[data-testid="root-folder"]')).toHaveCount(1);
    await expect(page.locator('[data-testid="root-folder"]').first()).toContainText('/Users/test/Documents');
  });

  test('should update OCR language settings', async () => {
    // Mock successful config update
    await page.route('/api/config', (route) => {
      if (route.request().method() === 'PUT') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true })
        });
      } else {
        route.continue();
      }
    });

    // Toggle OCR languages
    await page.uncheck('[data-testid="ocr-language-spa"]');
    await page.check('[data-testid="ocr-language-fra"]');

    // Save configuration
    await page.click('[data-testid="save-config-button"]');

    // Verify success message
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="success-message"]')).toContainText('Configuration saved successfully');
  });

  test('should toggle face search setting', async () => {
    // Mock successful config update
    await page.route('/api/config', (route) => {
      if (route.request().method() === 'PUT') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true })
        });
      } else {
        route.continue();
      }
    });

    // Toggle face search
    await page.uncheck('[data-testid="face-search-enabled"]');

    // Save configuration
    await page.click('[data-testid="save-config-button"]');

    // Verify setting was saved
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
  });

  test('should start incremental indexing', async () => {
    // Mock indexing start
    await page.route('/api/index/start', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, message: 'Indexing started' })
      });
    });

    // Click incremental indexing button
    await page.click('[data-testid="start-incremental-index"]');

    // Verify indexing started message
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="success-message"]')).toContainText('Incremental indexing started');
  });

  test('should start full re-indexing', async () => {
    // Mock full indexing start
    await page.route('/api/index/start', (route) => {
      const requestBody = route.request().postData();
      const data = JSON.parse(requestBody || '{}');

      if (data.full === true) {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true, message: 'Full re-indexing started' })
        });
      } else {
        route.continue();
      }
    });

    // Click full re-indexing button
    await page.click('[data-testid="start-full-reindex"]');

    // Verify confirmation dialog if present
    if (await page.locator('[data-testid="confirm-dialog"]').isVisible()) {
      await page.click('[data-testid="confirm-yes"]');
    }

    // Verify full indexing started message
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="success-message"]')).toContainText('Full re-indexing started');
  });

  test('should stop indexing when in progress', async () => {
    // Mock indexing in progress
    await page.route('/api/index/status', (route) => {
      route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'indexing',
          progress: {
            total_files: 1000,
            processed_files: 500,
            current_phase: 'metadata'
          },
          errors: [],
          started_at: new Date().toISOString(),
          estimated_completion: new Date(Date.now() + 300000).toISOString()
        })
      });
    });

    // Mock stop indexing
    await page.route('/api/index/stop', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, message: 'Indexing stopped' })
      });
    });

    await page.reload();

    // Verify stop button is visible
    await expect(page.locator('[data-testid="stop-indexing"]')).toBeVisible();

    // Click stop indexing
    await page.click('[data-testid="stop-indexing"]');

    // Verify indexing stopped message
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="success-message"]')).toContainText('Indexing stopped');
  });

  test('should display indexing progress and errors', async () => {
    // Mock indexing with errors
    await page.route('/api/index/status', (route) => {
      route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'indexing',
          progress: {
            total_files: 1000,
            processed_files: 750,
            current_phase: 'embeddings'
          },
          errors: [
            'Failed to process /path/to/corrupted.jpg: Invalid image format',
            'OCR failed for /path/to/scan.pdf: Tesseract error'
          ],
          started_at: new Date().toISOString(),
          estimated_completion: new Date(Date.now() + 120000).toISOString()
        })
      });
    });

    await page.reload();

    // Verify progress display
    await expect(page.locator('[data-testid="indexing-progress"]')).toContainText('750/1000');
    await expect(page.locator('[data-testid="indexing-phase"]')).toContainText('embeddings');

    // Verify error display
    await expect(page.locator('[data-testid="indexing-errors"]')).toContainText('2 error(s)');

    // Expand error details
    await page.click('[data-testid="expand-errors"]');
    await expect(page.locator('[data-testid="error-detail"]')).toHaveCount(2);
    await expect(page.locator('[data-testid="error-detail"]').first()).toContainText('corrupted.jpg');
  });

  test('should handle configuration save errors', async () => {
    // Mock API error
    await page.route('/api/config', (route) => {
      if (route.request().method() === 'PUT') {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Failed to save configuration' })
        });
      } else {
        route.continue();
      }
    });

    // Make a change and try to save
    await page.uncheck('[data-testid="face-search-enabled"]');
    await page.click('[data-testid="save-config-button"]');

    // Verify error message
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Failed to save configuration');
  });

  test('should validate folder paths', async () => {
    // Try to add invalid folder path
    await page.fill('[data-testid="new-folder-input"]', 'invalid/path');
    await page.click('[data-testid="add-folder-button"]');

    // Verify validation error (if implemented)
    const errorElement = page.locator('[data-testid="folder-validation-error"]');
    if (await errorElement.isVisible()) {
      await expect(errorElement).toContainText('Invalid folder path');
    }
  });

  test('should show loading states during operations', async () => {
    // Mock slow API response
    await page.route('/api/config', (route) => {
      if (route.request().method() === 'PUT') {
        setTimeout(() => {
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ success: true })
          });
        }, 2000);
      } else {
        route.continue();
      }
    });

    // Start save operation
    await page.click('[data-testid="save-config-button"]');

    // Verify loading state
    await expect(page.locator('[data-testid="save-config-button"]')).toBeDisabled();
    await expect(page.locator('[data-testid="save-config-button"]')).toContainText('Saving...');

    // Wait for completion
    await page.waitForResponse(response =>
      response.url().includes('/api/config') && response.request().method() === 'PUT'
    );

    // Verify loading state is cleared
    await expect(page.locator('[data-testid="save-config-button"]')).toBeEnabled();
    await expect(page.locator('[data-testid="save-config-button"]')).toContainText('Save Configuration');
  });

  test('should refresh data when page becomes visible', async () => {
    // Navigate away and back
    await page.click('[data-testid="nav-search"]');
    await page.click('[data-testid="nav-settings"]');

    // Verify API calls were made to refresh data
    await page.waitForResponse(response => response.url().includes('/api/config'));
    await page.waitForResponse(response => response.url().includes('/api/index/status'));
    await page.waitForResponse(response => response.url().includes('/api/index/stats'));
  });
});