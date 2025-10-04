import { test, expect, Page } from '@playwright/test';
import { ElectronApplication, _electron as electron } from '@playwright/test';
import path from 'path';

/**
 * Performance test for virtual scrolling with 100K photos.
 * Requirement: Maintain 60fps with 100K+ photos loaded.
 */

let electronApp: ElectronApplication;
let page: Page;

// Helper to generate mock photo data
function generateMockPhotos(count: number) {
  const photos = [];
  for (let i = 0; i < count; i++) {
    photos.push({
      file_id: i + 1,
      path: `/photos/batch_${Math.floor(i / 1000)}/photo_${i:06}.jpg`,
      filename: `photo_${i:06}.jpg`,
      folder: `/photos/batch_${Math.floor(i / 1000)}`,
      thumb_path: `/thumbnails/thumb_${i:06}.jpg`,
      shot_dt: new Date(2020 + Math.floor(i / 50000), i % 12, (i % 28) + 1).toISOString(),
      score: Math.random(),
      badges: i % 3 === 0 ? ['OCR'] : i % 5 === 0 ? ['Face'] : ['Photo-Match']
    });
  }
  return photos;
}

test.describe('Virtual Scroll Performance with 100K Photos', () => {
  test.beforeAll(async () => {
    // Launch app with performance monitoring enabled
    electronApp = await electron.launch({
      args: [
        path.join(__dirname, '../../frontend/dist/electron/main.js'),
        '--enable-precise-memory-info',
        '--enable-gpu-benchmarking'
      ],
      env: {
        ...process.env,
        NODE_ENV: 'test',
        E2E_TEST: 'true',
        PERF_TEST: 'true',
        SKIP_ONBOARDING: 'true'
      }
    });

    page = await electronApp.firstWindow();
    await page.waitForLoadState('domcontentloaded');

    // Inject large dataset
    await injectLargeDataset();
  });

  test.afterAll(async () => {
    await electronApp.close();
  });

  async function injectLargeDataset() {
    // Mock the API to return 100K photos
    await page.route('**/search**', async route => {
      const photos = generateMockPhotos(100000);
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          query: 'test',
          total_matches: 100000,
          items: photos,
          took_ms: 50
        })
      });
    });

    // Trigger search to load data
    const searchInput = await page.locator('[data-testid="search-input"]');
    await searchInput.fill('test');
    await searchInput.press('Enter');

    // Wait for results to load
    await page.waitForSelector('[data-testid="search-results"]', { timeout: 30000 });
  }

  test('should render 100K photos efficiently', async () => {
    // Measure initial render time
    const startTime = await page.evaluate(() => performance.now());

    // Wait for grid to be visible
    await page.waitForSelector('[data-testid="virtual-grid-container"]');

    const renderTime = await page.evaluate(() => performance.now()) - startTime;

    // Should render quickly despite large dataset
    expect(renderTime).toBeLessThan(500);

    // Check DOM node count - should be virtualized
    const nodeCount = await page.evaluate(() => {
      const grid = document.querySelector('[data-testid="virtual-grid-container"]');
      return grid?.querySelectorAll('[data-testid^="grid-item"]').length || 0;
    });

    // Should only render visible items (not all 100K)
    expect(nodeCount).toBeLessThan(200);
    expect(nodeCount).toBeGreaterThan(0);

    // Verify total count is shown correctly
    const countDisplay = await page.locator('[data-testid="result-count"]');
    const countText = await countDisplay.textContent();
    expect(countText).toContain('100,000');
  });

  test('should maintain 60fps during scrolling', async () => {
    // Enable performance monitoring
    await page.evaluate(() => {
      (window as any).performanceMetrics = {
        frames: [],
        scrollEvents: [],
        jank: []
      };

      let lastFrameTime = performance.now();
      let frameCount = 0;

      const measureFrame = () => {
        const now = performance.now();
        const delta = now - lastFrameTime;
        const fps = 1000 / delta;

        (window as any).performanceMetrics.frames.push({
          time: now,
          fps: fps,
          delta: delta
        });

        // Detect jank (frame took >16.67ms)
        if (delta > 16.67) {
          (window as any).performanceMetrics.jank.push({
            time: now,
            delta: delta
          });
        }

        lastFrameTime = now;
        frameCount++;

        if (frameCount < 600) { // Measure for ~10 seconds at 60fps
          requestAnimationFrame(measureFrame);
        }
      };

      requestAnimationFrame(measureFrame);
    });

    // Perform aggressive scrolling
    const scrollContainer = await page.locator('[data-testid="virtual-grid-container"]');

    // Rapid scroll to different positions
    const scrollPositions = [
      10000, 25000, 50000, 75000, 90000,
      95000, 85000, 60000, 30000, 5000, 0
    ];

    for (const position of scrollPositions) {
      await scrollContainer.evaluate((el, pos) => {
        el.scrollTop = pos;
      }, position);
      await page.waitForTimeout(100); // Brief pause between scrolls
    }

    // Wait for measurements to complete
    await page.waitForTimeout(1000);

    // Analyze performance metrics
    const metrics = await page.evaluate(() => (window as any).performanceMetrics);

    // Calculate average FPS
    const avgFps = metrics.frames.reduce((sum: number, f: any) => sum + f.fps, 0) / metrics.frames.length;

    // Calculate jank percentage
    const jankPercentage = (metrics.jank.length / metrics.frames.length) * 100;

    // Performance assertions
    expect(avgFps).toBeGreaterThan(55); // Average should be close to 60fps
    expect(jankPercentage).toBeLessThan(5); // Less than 5% janky frames
  });

  test('should handle rapid jumping efficiently', async () => {
    const scrollContainer = await page.locator('[data-testid="virtual-grid-container"]');

    // Test jumping to random positions rapidly
    const jumpTest = await page.evaluate(async () => {
      const container = document.querySelector('[data-testid="virtual-grid-container"]');
      if (!container) return { success: false };

      const measurements: number[] = [];

      for (let i = 0; i < 20; i++) {
        const randomPosition = Math.floor(Math.random() * 100000) * 256; // Random row
        const startTime = performance.now();

        container.scrollTop = randomPosition;

        // Wait for render
        await new Promise(resolve => requestAnimationFrame(resolve));

        const renderTime = performance.now() - startTime;
        measurements.push(renderTime);
      }

      return {
        success: true,
        avgRenderTime: measurements.reduce((a, b) => a + b, 0) / measurements.length,
        maxRenderTime: Math.max(...measurements)
      };
    });

    expect(jumpTest.success).toBe(true);
    expect(jumpTest.avgRenderTime).toBeLessThan(50); // Quick renders
    expect(jumpTest.maxRenderTime).toBeLessThan(100); // No slow renders
  });

  test('should maintain low memory usage', async () => {
    // Get initial memory
    const initialMemory = await page.evaluate(() => {
      if ('memory' in performance) {
        return (performance as any).memory.usedJSHeapSize / 1024 / 1024; // MB
      }
      return 0;
    });

    // Scroll through entire list
    const scrollContainer = await page.locator('[data-testid="virtual-grid-container"]');

    for (let i = 0; i <= 100; i += 10) {
      const position = (i / 100) * 100000 * 256; // Percentage of total height
      await scrollContainer.evaluate((el, pos) => {
        el.scrollTop = pos;
      }, position);
      await page.waitForTimeout(50);
    }

    // Get final memory
    const finalMemory = await page.evaluate(() => {
      if ('memory' in performance) {
        return (performance as any).memory.usedJSHeapSize / 1024 / 1024; // MB
      }
      return 0;
    });

    const memoryIncrease = finalMemory - initialMemory;

    // Memory should stay reasonable despite 100K items
    expect(memoryIncrease).toBeLessThan(200); // Less than 200MB increase
    expect(finalMemory).toBeLessThan(500); // Total under 500MB
  });

  test('should lazy load images efficiently', async () => {
    // Monitor image loading
    const imageLoadMetrics = await page.evaluate(() => {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        (window as any).imageLoadMetrics = (window as any).imageLoadMetrics || [];
        entries.forEach(entry => {
          if (entry.name.includes('thumb')) {
            (window as any).imageLoadMetrics.push({
              name: entry.name,
              duration: entry.duration
            });
          }
        });
      });
      observer.observe({ entryTypes: ['resource'] });

      return new Promise(resolve => {
        setTimeout(() => {
          resolve((window as any).imageLoadMetrics || []);
        }, 2000);
      });
    });

    // Only visible images should be loaded initially
    const loadedImages = await page.evaluate(() => {
      const images = Array.from(document.querySelectorAll('img[data-testid="grid-item-image"]'));
      return images.filter(img => (img as HTMLImageElement).complete).length;
    });

    // Should load a reasonable number of images (visible + buffer)
    expect(loadedImages).toBeLessThan(100);
    expect(loadedImages).toBeGreaterThan(10);
  });

  test('should handle filtering without performance degradation', async () => {
    // Apply filter to reduce dataset
    const filterButton = await page.locator('[data-testid="filter-button"]');
    await filterButton.click();

    const dateFilter = await page.locator('[data-testid="filter-date-range"]');
    await dateFilter.selectOption('last-year');

    const applyFilter = await page.locator('[data-testid="apply-filters"]');

    const startTime = await page.evaluate(() => performance.now());
    await applyFilter.click();

    // Wait for filtered results
    await page.waitForSelector('[data-testid="search-results"]');
    const filterTime = await page.evaluate(() => performance.now()) - startTime;

    // Filtering should be fast
    expect(filterTime).toBeLessThan(500);

    // Grid should still be performant after filtering
    const scrollContainer = await page.locator('[data-testid="virtual-grid-container"]');
    const scrollPerf = await page.evaluate(async (container) => {
      const element = container as HTMLElement;
      const startTime = performance.now();

      // Quick scroll test
      element.scrollTop = 10000;
      await new Promise(resolve => requestAnimationFrame(resolve));
      element.scrollTop = 0;
      await new Promise(resolve => requestAnimationFrame(resolve));

      return performance.now() - startTime;
    }, await scrollContainer.elementHandle());

    expect(scrollPerf).toBeLessThan(100);
  });

  test('should handle selection efficiently', async () => {
    // Enable selection mode
    const selectionModeBtn = await page.locator('[data-testid="enable-selection"]');
    await selectionModeBtn.click();

    // Select all visible items
    await page.keyboard.down('Control');
    await page.keyboard.press('a');
    await page.keyboard.up('Control');

    // Measure selection performance
    const selectionMetrics = await page.evaluate(() => {
      const items = document.querySelectorAll('[data-testid^="grid-item"]');
      const selected = document.querySelectorAll('[data-selected="true"]');

      return {
        totalItems: items.length,
        selectedItems: selected.length
      };
    });

    // Should only select visible items
    expect(selectionMetrics.selectedItems).toBeLessThan(200);
    expect(selectionMetrics.selectedItems).toBeGreaterThan(0);

    // Scrolling with selection should remain smooth
    const scrollContainer = await page.locator('[data-testid="virtual-grid-container"]');
    await scrollContainer.evaluate((el) => {
      el.scrollTop = 50000;
    });

    // Check performance is maintained
    const fps = await page.evaluate(() => {
      return new Promise(resolve => {
        let frames = 0;
        const startTime = performance.now();

        const countFrames = () => {
          frames++;
          if (performance.now() - startTime < 1000) {
            requestAnimationFrame(countFrames);
          } else {
            resolve(frames);
          }
        };

        requestAnimationFrame(countFrames);
      });
    });

    expect(fps).toBeGreaterThan(50); // Should maintain good FPS with selection
  });

  test('should handle rapid resize events', async () => {
    // Test window resizing performance
    const resizeMetrics = await page.evaluate(async () => {
      const metrics: any[] = [];

      for (let width = 1920; width >= 768; width -= 100) {
        const startTime = performance.now();

        // Trigger resize
        window.dispatchEvent(new Event('resize'));

        // Wait for reflow
        await new Promise(resolve => requestAnimationFrame(resolve));

        metrics.push({
          width,
          time: performance.now() - startTime
        });
      }

      return {
        avgTime: metrics.reduce((sum, m) => sum + m.time, 0) / metrics.length,
        maxTime: Math.max(...metrics.map(m => m.time))
      };
    });

    // Resize handling should be efficient
    expect(resizeMetrics.avgTime).toBeLessThan(50);
    expect(resizeMetrics.maxTime).toBeLessThan(100);
  });

  test('should provide smooth scroll-to-top experience', async () => {
    const scrollContainer = await page.locator('[data-testid="virtual-grid-container"]');

    // Scroll to bottom
    await scrollContainer.evaluate((el) => {
      el.scrollTop = el.scrollHeight;
    });

    // Click scroll-to-top button
    const scrollToTopBtn = await page.locator('[data-testid="scroll-to-top"]');
    await scrollToTopBtn.click();

    // Measure smooth scroll performance
    const smoothScrollMetrics = await page.evaluate(() => {
      return new Promise(resolve => {
        const container = document.querySelector('[data-testid="virtual-grid-container"]');
        if (!container) {
          resolve({ success: false });
          return;
        }

        const metrics: any[] = [];
        let lastPosition = container.scrollTop;
        let lastTime = performance.now();

        const measureScroll = () => {
          const currentPosition = container.scrollTop;
          const currentTime = performance.now();
          const velocity = Math.abs(currentPosition - lastPosition) / (currentTime - lastTime);

          metrics.push({
            position: currentPosition,
            time: currentTime,
            velocity
          });

          lastPosition = currentPosition;
          lastTime = currentTime;

          if (currentPosition > 0) {
            requestAnimationFrame(measureScroll);
          } else {
            resolve({
              success: true,
              duration: currentTime - metrics[0].time,
              avgVelocity: metrics.reduce((sum, m) => sum + m.velocity, 0) / metrics.length
            });
          }
        };

        requestAnimationFrame(measureScroll);
      });
    });

    expect(smoothScrollMetrics.success).toBe(true);
    expect(smoothScrollMetrics.duration).toBeLessThan(2000); // Complete within 2 seconds
  });
});