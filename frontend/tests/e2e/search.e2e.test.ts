/**
 * End-to-end tests for search functionality
 */

import { test, expect, Page } from '@playwright/test';

test.describe('Search Functionality', () => {
  let page: Page;

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();

    // Mock API responses for consistent testing
    await page.route('/api/search*', (route) => {
      route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({
          query: 'test',
          total_matches: 5,
          took_ms: 125,
          items: [
            {
              file_id: 1,
              path: '/test/photos/wedding1.jpg',
              folder: '/test/photos',
              filename: 'wedding1.jpg',
              thumb_path: '/thumbnails/1.webp',
              shot_dt: '2023-06-15T14:30:00Z',
              score: 0.95,
              badges: ['filename', 'OCR'],
              snippet: 'wedding ceremony'
            },
            {
              file_id: 2,
              path: '/test/photos/birthday2.jpg',
              folder: '/test/photos',
              filename: 'birthday2.jpg',
              thumb_path: '/thumbnails/2.webp',
              shot_dt: '2023-08-20T16:45:00Z',
              score: 0.87,
              badges: ['filename'],
              snippet: null
            }
          ]
        })
      });
    });

    await page.goto('http://localhost:5173');
  });

  test('should display search interface on load', async () => {
    // Verify main search elements are present
    await expect(page.locator('[data-testid="search-input"]')).toBeVisible();
    await expect(page.locator('[data-testid="search-button"]')).toBeVisible();
    await expect(page.locator('[data-testid="search-filters"]')).toBeVisible();
  });

  test('should perform basic text search', async () => {
    // Enter search query
    await page.fill('[data-testid="search-input"]', 'wedding');
    await page.click('[data-testid="search-button"]');

    // Wait for results to load
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible();

    // Verify results header
    await expect(page.locator('[data-testid="results-count"]')).toContainText('5 photos found');
    await expect(page.locator('[data-testid="search-time"]')).toContainText('125ms');

    // Verify result items
    const resultItems = page.locator('[data-testid="result-item"]');
    await expect(resultItems).toHaveCount(2);

    // Check first result details
    const firstResult = resultItems.first();
    await expect(firstResult.locator('[data-testid="result-filename"]')).toContainText('wedding1.jpg');
    await expect(firstResult.locator('[data-testid="result-score"]')).toContainText('95.0%');
    await expect(firstResult.locator('[data-testid="result-badge"]')).toContainText('filename');
    await expect(firstResult.locator('[data-testid="result-snippet"]')).toContainText('wedding ceremony');
  });

  test('should handle empty search results', async () => {
    // Mock empty results
    await page.route('/api/search*', (route) => {
      route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({
          query: 'nonexistent',
          total_matches: 0,
          took_ms: 45,
          items: []
        })
      });
    });

    await page.fill('[data-testid="search-input"]', 'nonexistent');
    await page.click('[data-testid="search-button"]');

    // Verify empty state message
    await expect(page.locator('[data-testid="empty-results"]')).toBeVisible();
    await expect(page.locator('[data-testid="empty-results"]')).toContainText('No photos found');
  });

  test('should apply date range filters', async () => {
    // Open filters
    await page.click('[data-testid="filters-toggle"]');
    await expect(page.locator('[data-testid="date-filters"]')).toBeVisible();

    // Set date range
    await page.fill('[data-testid="date-from"]', '2023-01-01');
    await page.fill('[data-testid="date-to"]', '2023-12-31');

    // Perform search with filters
    await page.fill('[data-testid="search-input"]', 'photos');
    await page.click('[data-testid="search-button"]');

    // Verify API was called with date parameters
    await page.waitForResponse(response =>
      response.url().includes('/api/search') &&
      response.url().includes('from=2023-01-01') &&
      response.url().includes('to=2023-12-31')
    );
  });

  test('should open photo preview on click', async () => {
    // Perform search first
    await page.fill('[data-testid="search-input"]', 'wedding');
    await page.click('[data-testid="search-button"]');

    // Wait for results and click first item
    await page.waitForSelector('[data-testid="result-item"]');
    await page.click('[data-testid="result-item"]');

    // Verify preview drawer opens
    await expect(page.locator('[data-testid="preview-drawer"]')).toBeVisible();
    await expect(page.locator('[data-testid="preview-image"]')).toBeVisible();
    await expect(page.locator('[data-testid="preview-filename"]')).toContainText('wedding1.jpg');
    await expect(page.locator('[data-testid="preview-path"]')).toContainText('/test/photos/wedding1.jpg');
  });

  test('should navigate between photos in preview', async () => {
    // Perform search and open preview
    await page.fill('[data-testid="search-input"]', 'wedding');
    await page.click('[data-testid="search-button"]');
    await page.waitForSelector('[data-testid="result-item"]');
    await page.click('[data-testid="result-item"]');

    // Verify next/previous buttons are present
    await expect(page.locator('[data-testid="preview-next"]')).toBeVisible();
    await expect(page.locator('[data-testid="preview-previous"]')).toBeVisible();

    // Test navigation
    await page.click('[data-testid="preview-next"]');
    await expect(page.locator('[data-testid="preview-filename"]')).toContainText('birthday2.jpg');

    await page.click('[data-testid="preview-previous"]');
    await expect(page.locator('[data-testid="preview-filename"]')).toContainText('wedding1.jpg');
  });

  test('should close preview with escape key', async () => {
    // Open preview
    await page.fill('[data-testid="search-input"]', 'wedding');
    await page.click('[data-testid="search-button"]');
    await page.waitForSelector('[data-testid="result-item"]');
    await page.click('[data-testid="result-item"]');

    // Verify preview is open
    await expect(page.locator('[data-testid="preview-drawer"]')).toBeVisible();

    // Press Escape key
    await page.keyboard.press('Escape');

    // Verify preview is closed
    await expect(page.locator('[data-testid="preview-drawer"]')).not.toBeVisible();
  });

  test('should handle search loading state', async () => {
    // Mock slow API response
    await page.route('/api/search*', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({
          query: 'test',
          total_matches: 1,
          took_ms: 1000,
          items: []
        })
      });
    });

    // Start search
    await page.fill('[data-testid="search-input"]', 'test');
    const searchPromise = page.click('[data-testid="search-button"]');

    // Verify loading state
    await expect(page.locator('[data-testid="search-loading"]')).toBeVisible();
    await expect(page.locator('[data-testid="search-button"]')).toBeDisabled();

    // Wait for search to complete
    await searchPromise;
    await page.waitForResponse(response => response.url().includes('/api/search'));

    // Verify loading state is gone
    await expect(page.locator('[data-testid="search-loading"]')).not.toBeVisible();
    await expect(page.locator('[data-testid="search-button"]')).toBeEnabled();
  });

  test('should handle API errors gracefully', async () => {
    // Mock API error
    await page.route('/api/search*', (route) => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' })
      });
    });

    await page.fill('[data-testid="search-input"]', 'test');
    await page.click('[data-testid="search-button"]');

    // Verify error message is displayed
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-message"]')).toContainText('search failed');
  });

  test('should perform semantic search', async () => {
    // Mock semantic search API
    await page.route('/api/search/semantic*', (route) => {
      route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({
          query: 'happy family moments',
          total_matches: 3,
          took_ms: 890,
          items: [
            {
              file_id: 10,
              path: '/test/photos/family_vacation.jpg',
              folder: '/test/photos',
              filename: 'family_vacation.jpg',
              thumb_path: '/thumbnails/10.webp',
              shot_dt: '2023-07-15T12:00:00Z',
              score: 0.92,
              badges: ['semantic'],
              snippet: null
            }
          ]
        })
      });
    });

    // Switch to semantic search mode
    await page.click('[data-testid="search-mode-toggle"]');
    await page.selectOption('[data-testid="search-mode"]', 'semantic');

    // Perform semantic search
    await page.fill('[data-testid="search-input"]', 'happy family moments');
    await page.click('[data-testid="search-button"]');

    // Verify semantic search results
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible();
    await expect(page.locator('[data-testid="result-badge"]')).toContainText('semantic');
  });

  test('should perform reverse image search', async () => {
    // Create a test file
    const testFile = new File(['test image data'], 'test.jpg', { type: 'image/jpeg' });

    // Mock image search API
    await page.route('/api/search/image*', (route) => {
      route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({
          query: 'uploaded_image',
          total_matches: 2,
          took_ms: 1250,
          items: [
            {
              file_id: 20,
              path: '/test/photos/similar_photo.jpg',
              folder: '/test/photos',
              filename: 'similar_photo.jpg',
              thumb_path: '/thumbnails/20.webp',
              shot_dt: '2023-05-10T09:15:00Z',
              score: 0.88,
              badges: ['Photo-Match'],
              snippet: null
            }
          ]
        })
      });
    });

    // Switch to image search mode
    await page.click('[data-testid="search-mode-toggle"]');
    await page.selectOption('[data-testid="search-mode"]', 'image');

    // Upload image
    const fileInput = page.locator('[data-testid="image-upload"]');
    await fileInput.setInputFiles({
      name: 'test.jpg',
      mimeType: 'image/jpeg',
      buffer: Buffer.from('test image data')
    });

    // Verify image search results
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible();
    await expect(page.locator('[data-testid="result-badge"]')).toContainText('Photo-Match');
  });

  test('should remember search history', async () => {
    // Perform multiple searches
    const searches = ['wedding', 'birthday', 'vacation'];

    for (const query of searches) {
      await page.fill('[data-testid="search-input"]', query);
      await page.click('[data-testid="search-button"]');
      await page.waitForResponse(response => response.url().includes('/api/search'));
    }

    // Open search history
    await page.click('[data-testid="search-history-toggle"]');
    await expect(page.locator('[data-testid="search-history"]')).toBeVisible();

    // Verify history contains recent searches
    for (const query of searches) {
      await expect(page.locator(`[data-testid="history-item"][data-query="${query}"]`)).toBeVisible();
    }

    // Click on history item should perform search
    await page.click('[data-testid="history-item"][data-query="wedding"]');
    await expect(page.locator('[data-testid="search-input"]')).toHaveValue('wedding');
  });

  test('should respect search result limits', async () => {
    // Mock large result set
    const items = Array.from({ length: 50 }, (_, i) => ({
      file_id: i + 1,
      path: `/test/photos/photo${i + 1}.jpg`,
      folder: '/test/photos',
      filename: `photo${i + 1}.jpg`,
      thumb_path: `/thumbnails/${i + 1}.webp`,
      shot_dt: '2023-01-01T00:00:00Z',
      score: 0.9 - (i * 0.01),
      badges: ['filename'],
      snippet: null
    }));

    await page.route('/api/search*', (route) => {
      const url = new URL(route.request().url());
      const limit = parseInt(url.searchParams.get('limit') || '50');
      const offset = parseInt(url.searchParams.get('offset') || '0');

      route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({
          query: 'photos',
          total_matches: 1000,
          took_ms: 150,
          items: items.slice(offset, offset + limit)
        })
      });
    });

    // Test pagination
    await page.fill('[data-testid="search-input"]', 'photos');
    await page.click('[data-testid="search-button"]');

    // Verify initial results
    await expect(page.locator('[data-testid="result-item"]')).toHaveCount(50);
    await expect(page.locator('[data-testid="results-count"]')).toContainText('1000 photos found');

    // Test load more functionality
    if (await page.locator('[data-testid="load-more"]').isVisible()) {
      await page.click('[data-testid="load-more"]');
      await page.waitForResponse(response =>
        response.url().includes('/api/search') &&
        response.url().includes('offset=50')
      );
    }
  });
});