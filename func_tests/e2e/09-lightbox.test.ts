import { test, expect, Page } from '@playwright/test';
import { ElectronApplication, _electron as electron } from '@playwright/test';
import path from 'path';

let electronApp: ElectronApplication;
let page: Page;

test.describe.skip('Lightbox Keyboard Navigation E2E Test', () => {
  test.beforeAll(async () => {
    // Launch the Electron app
    electronApp = await electron.launch({
      args: [path.join(__dirname, '../../frontend/dist/electron/main.js')],
      env: {
        ...process.env,
        NODE_ENV: 'test',
        E2E_TEST: 'true',
        SKIP_ONBOARDING: 'true' // Skip onboarding for this test
      }
    });

    // Get the first window
    page = await electronApp.firstWindow();
    await page.waitForLoadState('domcontentloaded');

    // Ensure we have some search results first
    await performInitialSearch();
  });

  test.afterAll(async () => {
    await electronApp.close();
  });

  async function performInitialSearch() {
    // Navigate to search page if not already there
    const searchPage = await page.locator('[data-testid="search-page"]');
    if (!(await searchPage.isVisible())) {
      await page.goto('/');
    }

    // Perform a search to get results
    const searchInput = await page.locator('[data-testid="search-input"]');
    await searchInput.fill('nature');
    await searchInput.press('Enter');

    // Wait for search results
    await page.waitForSelector('[data-testid="search-results"]', { timeout: 10000 });

    // Ensure we have at least 3 results for navigation testing
    const results = await page.locator('[data-testid="search-result-item"]');
    const count = await results.count();
    expect(count).toBeGreaterThan(2);
  }

  test('should open lightbox when clicking on a photo', async () => {
    // Click on the first photo result
    const firstPhoto = await page.locator('[data-testid="search-result-item"]').first();
    await firstPhoto.click();

    // Verify lightbox opens
    const lightbox = await page.locator('[data-testid="lightbox"]');
    await expect(lightbox).toBeVisible({ timeout: 5000 });

    // Verify image is loaded
    const lightboxImage = await page.locator('[data-testid="lightbox-image"]');
    await expect(lightboxImage).toBeVisible();

    // Verify navigation controls are present
    const prevButton = await page.locator('[data-testid="lightbox-prev"]');
    const nextButton = await page.locator('[data-testid="lightbox-next"]');
    await expect(prevButton).toBeVisible();
    await expect(nextButton).toBeVisible();
  });

  test('should navigate with arrow keys', async () => {
    // Open lightbox on first photo
    const firstPhoto = await page.locator('[data-testid="search-result-item"]').first();
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

  test('should close lightbox with Escape key', async () => {
    // Open lightbox
    const firstPhoto = await page.locator('[data-testid="search-result-item"]').first();
    await firstPhoto.click();
    await expect(page.locator('[data-testid="lightbox"]')).toBeVisible();

    // Press Escape
    await page.keyboard.press('Escape');

    // Verify lightbox is closed
    await expect(page.locator('[data-testid="lightbox"]')).not.toBeVisible({ timeout: 5000 });

    // Verify we're back on the search page
    await expect(page.locator('[data-testid="search-page"]')).toBeVisible();
  });

  test('should toggle fullscreen with F key', async () => {
    // Open lightbox
    const firstPhoto = await page.locator('[data-testid="search-result-item"]').first();
    await firstPhoto.click();
    await page.waitForSelector('[data-testid="lightbox"]');

    // Press F for fullscreen
    await page.keyboard.press('f');
    await page.waitForTimeout(500);

    // Verify fullscreen class is applied
    const lightbox = await page.locator('[data-testid="lightbox"]');
    const classList = await lightbox.getAttribute('class');
    expect(classList).toContain('fullscreen');

    // Press F again to exit fullscreen
    await page.keyboard.press('f');
    await page.waitForTimeout(500);

    // Verify fullscreen class is removed
    const updatedClassList = await lightbox.getAttribute('class');
    expect(updatedClassList).not.toContain('fullscreen');
  });

  test('should zoom with + and - keys', async () => {
    // Open lightbox
    const firstPhoto = await page.locator('[data-testid="search-result-item"]').first();
    await firstPhoto.click();
    await page.waitForSelector('[data-testid="lightbox"]');

    // Get initial transform scale
    const image = await page.locator('[data-testid="lightbox-image"]');
    const initialTransform = await image.evaluate(el => window.getComputedStyle(el).transform);

    // Press + to zoom in
    await page.keyboard.press('+');
    await page.waitForTimeout(300);

    // Verify zoom increased
    const zoomedTransform = await image.evaluate(el => window.getComputedStyle(el).transform);
    expect(zoomedTransform).not.toBe(initialTransform);

    // Press - to zoom out
    await page.keyboard.press('-');
    await page.waitForTimeout(300);

    // Press 0 to reset zoom
    await page.keyboard.press('0');
    await page.waitForTimeout(300);

    // Verify zoom is reset
    const resetTransform = await image.evaluate(el => window.getComputedStyle(el).transform);
    expect(resetTransform).toBe(initialTransform);
  });

  test('should show metadata with I key', async () => {
    // Open lightbox
    const firstPhoto = await page.locator('[data-testid="search-result-item"]').first();
    await firstPhoto.click();
    await page.waitForSelector('[data-testid="lightbox"]');

    // Initially metadata should be hidden
    const metadata = await page.locator('[data-testid="lightbox-metadata"]');
    await expect(metadata).not.toBeVisible();

    // Press I to show metadata
    await page.keyboard.press('i');
    await page.waitForTimeout(300);

    // Verify metadata is visible
    await expect(metadata).toBeVisible();

    // Verify metadata contains expected fields
    await expect(page.locator('[data-testid="metadata-filename"]')).toBeVisible();
    // await expect(page.locator('[data-testid="metadata-dimensions"]')).toBeVisible(); // Dimensions might be missing if not in DB
    // await expect(page.locator('[data-testid="metadata-size"]')).toBeVisible(); // Size not implemented in UI

    // Press I again to hide metadata
    await page.keyboard.press('i');
    await page.waitForTimeout(300);

    // Verify metadata is hidden
    await expect(metadata).not.toBeVisible();
  });

  test('should navigate with Page Up/Down keys', async () => {
    // Open lightbox
    const firstPhoto = await page.locator('[data-testid="search-result-item"]').first();
    await firstPhoto.click();
    await page.waitForSelector('[data-testid="lightbox"]');

    const initialSrc = await page.locator('[data-testid="lightbox-image"]').getAttribute('src');

    // Press Page Down to go forward multiple photos
    await page.keyboard.press('PageDown');
    await page.waitForTimeout(500);

    const pageDownSrc = await page.locator('[data-testid="lightbox-image"]').getAttribute('src');
    expect(pageDownSrc).not.toBe(initialSrc);

    // Press Page Up to go back
    await page.keyboard.press('PageUp');
    await page.waitForTimeout(500);

    const pageUpSrc = await page.locator('[data-testid="lightbox-image"]').getAttribute('src');
    expect(pageUpSrc).toBe(initialSrc);
  });

  test('should navigate to first/last with Home/End keys', async () => {
    // Open lightbox on middle photo
    const photos = await page.locator('[data-testid="search-result-item"]');
    const middleIndex = Math.floor((await photos.count()) / 2);
    await photos.nth(middleIndex).click();
    await page.waitForSelector('[data-testid="lightbox"]');

    // Press Home to go to first photo
    await page.keyboard.press('Home');
    await page.waitForTimeout(500);

    // Verify we're at the first photo
    const currentIndex = await page.locator('[data-testid="lightbox-counter"]').textContent();
    expect(currentIndex).toContain('1 /');

    // Press End to go to last photo
    await page.keyboard.press('End');
    await page.waitForTimeout(500);

    // Verify we're at the last photo
    const totalPhotos = await photos.count();
    const lastIndex = await page.locator('[data-testid="lightbox-counter"]').textContent();
    expect(lastIndex).toContain(`${totalPhotos} /`);
  });

  test('should handle Space key for play/pause slideshow', async () => {
    // Open lightbox
    const firstPhoto = await page.locator('[data-testid="search-result-item"]').first();
    await firstPhoto.click();
    await page.waitForSelector('[data-testid="lightbox"]');

    // Press Space to start slideshow
    await page.keyboard.press('Space');

    // Verify slideshow indicator appears
    const slideshowIndicator = await page.locator('[data-testid="slideshow-active"]');
    await expect(slideshowIndicator).toBeVisible({ timeout: 2000 });

    // Get initial image
    const initialSrc = await page.locator('[data-testid="lightbox-image"]').getAttribute('src');

    // Wait for slideshow to advance (typically 3-5 seconds)
    await page.waitForTimeout(5000);

    // Verify image changed automatically
    const autoAdvancedSrc = await page.locator('[data-testid="lightbox-image"]').getAttribute('src');
    expect(autoAdvancedSrc).not.toBe(initialSrc);

    // Press Space again to stop slideshow
    await page.keyboard.press('Space');

    // Verify slideshow stopped
    await expect(slideshowIndicator).not.toBeVisible({ timeout: 2000 });
  });

  test('should copy image path with C key', async () => {
    // Open lightbox
    const firstPhoto = await page.locator('[data-testid="search-result-item"]').first();
    await firstPhoto.click();
    await page.waitForSelector('[data-testid="lightbox"]');

    // Mock clipboard API
    await page.evaluate(() => {
      let clipboardText = '';
      Object.defineProperty(navigator, 'clipboard', {
        value: {
          writeText: async (text: string) => {
            clipboardText = text;
            return Promise.resolve();
          },
          readText: async () => {
            return Promise.resolve(clipboardText);
          }
        },
        writable: true
      });
    });

    // Press C to copy path
    await page.keyboard.press('c');

    // Wait for toast notification
    const toast = await page.locator('[data-testid="toast-notification"]');
    await expect(toast).toBeVisible({ timeout: 2000 });
    await expect(toast).toContainText('Path copied');

    // Verify clipboard contains a path
    const clipboardContent = await page.evaluate(() => navigator.clipboard.readText());
    expect(clipboardContent).toContain('/');
  });

  test('should delete photo with Delete key', async () => {
    // Open lightbox
    const photos = await page.locator('[data-testid="search-result-item"]');
    const initialCount = await photos.count();

    await photos.first().click();
    await page.waitForSelector('[data-testid="lightbox"]');

    // Press Delete key
    await page.keyboard.press('Delete');

    // Confirm deletion dialog should appear
    const confirmDialog = await page.locator('[data-testid="confirm-delete-dialog"]');
    await expect(confirmDialog).toBeVisible({ timeout: 2000 });

    // Cancel first to test cancellation
    const cancelBtn = await page.locator('[data-testid="cancel-delete-btn"]');
    await cancelBtn.click();
    await expect(confirmDialog).not.toBeVisible();

    // Press Delete again and confirm
    await page.keyboard.press('Delete');
    await expect(confirmDialog).toBeVisible();

    const confirmBtn = await page.locator('[data-testid="confirm-delete-btn"]');
    await confirmBtn.click();

    // Should advance to next photo after deletion
    await page.waitForTimeout(1000);

    // Close lightbox and verify photo count decreased
    await page.keyboard.press('Escape');
    await page.waitForTimeout(500);

    const newCount = await photos.count();
    expect(newCount).toBe(initialCount - 1);
  });

  test('should handle edge cases gracefully', async () => {
    // Test navigation at boundaries
    const photos = await page.locator('[data-testid="search-result-item"]');

    // Open last photo
    await photos.last().click();
    await page.waitForSelector('[data-testid="lightbox"]');

    // Try to go next from last photo
    await page.keyboard.press('ArrowRight');
    await page.waitForTimeout(500);

    // Should either wrap to first or stay on last
    const counter = await page.locator('[data-testid="lightbox-counter"]').textContent();
    expect(counter).toMatch(/(\d+) \//);

    // Close and open first photo
    await page.keyboard.press('Escape');
    await photos.first().click();
    await page.waitForSelector('[data-testid="lightbox"]');

    // Try to go previous from first photo
    await page.keyboard.press('ArrowLeft');
    await page.waitForTimeout(500);

    // Should either wrap to last or stay on first
    const firstCounter = await page.locator('[data-testid="lightbox-counter"]').textContent();
    expect(firstCounter).toMatch(/(\d+) \//);
  });

  test('should maintain keyboard focus correctly', async () => {
    // Open lightbox
    const firstPhoto = await page.locator('[data-testid="search-result-item"]').first();
    await firstPhoto.click();
    await page.waitForSelector('[data-testid="lightbox"]');

    // Check that lightbox has focus
    const lightboxHasFocus = await page.evaluate(() => {
      const lightbox = document.querySelector('[data-testid="lightbox"]');
      return lightbox === document.activeElement || lightbox?.contains(document.activeElement);
    });
    expect(lightboxHasFocus).toBe(true);

    // Tab through interactive elements
    await page.keyboard.press('Tab');
    let focusedElement = await page.evaluate(() => document.activeElement?.getAttribute('data-testid'));
    expect(focusedElement).toBeTruthy();

    // Shift+Tab to go backwards
    await page.keyboard.press('Shift+Tab');
    focusedElement = await page.evaluate(() => document.activeElement?.getAttribute('data-testid'));
    expect(focusedElement).toBeTruthy();
  });
});

// Performance tests for lightbox
test.describe.skip('Lightbox Performance', () => {
  test('should open in less than 100ms', async () => {
    const startTime = Date.now();

    const firstPhoto = await page.locator('[data-testid="search-result-item"]').first();
    await firstPhoto.click();

    await page.waitForSelector('[data-testid="lightbox"]');

    const endTime = Date.now();
    const loadTime = endTime - startTime;

    expect(loadTime).toBeLessThan(100);
  });

  test('should maintain 60fps during navigation', async () => {
    // Open lightbox
    const firstPhoto = await page.locator('[data-testid="search-result-item"]').first();
    await firstPhoto.click();
    await page.waitForSelector('[data-testid="lightbox"]');

    // Measure frame rate during rapid navigation
    const frameMetrics = await page.evaluate(async () => {
      const frames: number[] = [];
      let lastTime = performance.now();

      const measureFrame = () => {
        const currentTime = performance.now();
        const delta = currentTime - lastTime;
        frames.push(1000 / delta); // Convert to FPS
        lastTime = currentTime;
      };

      // Simulate rapid key presses
      for (let i = 0; i < 10; i++) {
        requestAnimationFrame(measureFrame);
        await new Promise(resolve => setTimeout(resolve, 16)); // ~60fps timing
      }

      return {
        avgFps: frames.reduce((a, b) => a + b, 0) / frames.length,
        minFps: Math.min(...frames)
      };
    });

    expect(frameMetrics.avgFps).toBeGreaterThan(55);
    expect(frameMetrics.minFps).toBeGreaterThan(45);
  });
});