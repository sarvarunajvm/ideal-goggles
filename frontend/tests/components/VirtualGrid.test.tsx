import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { act } from 'react';
import '@testing-library/jest-dom';
import { VirtualGrid } from '../../src/components/VirtualGrid/VirtualGrid';
import { VirtualGridItem } from '../../src/components/VirtualGrid/VirtualGridItem';

// Mock IntersectionObserver
const mockIntersectionObserver = jest.fn();
mockIntersectionObserver.mockReturnValue({
  observe: () => null,
  unobserve: () => null,
  disconnect: () => null
});
window.IntersectionObserver = mockIntersectionObserver as any;

// Mock performance.now for consistent timing
const mockPerformanceNow = jest.spyOn(performance, 'now');

// Helper to generate mock photo data
function generateMockPhotos(count: number) {
  return Array.from({ length: count }, (_, i) => ({
    file_id: i + 1,
    path: `/photos/photo_${i + 1}.jpg`,
    filename: `photo_${i + 1}.jpg`,
    folder: '/photos',
    thumb_path: `/thumbnails/thumb_${i + 1}.jpg`,
    shot_dt: new Date(2024, 0, 1 + i).toISOString(),
    score: Math.random(),
    badges: ['Photo-Match']
  }));
}

describe('VirtualGrid Performance Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockPerformanceNow.mockReset();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  test('should render large dataset efficiently', async () => {
    const photos = generateMockPhotos(10000);
    const startTime = performance.now();

    const { container } = render(
      <VirtualGrid
        items={photos}
        itemHeight={256}
        gap={16}
        onItemClick={jest.fn()}
      />
    );

    const renderTime = performance.now() - startTime;

    // Should render in under 100ms even with 10k items
    expect(renderTime).toBeLessThan(100);

    // Should only render visible items (not all 10k)
    const renderedItems = container.querySelectorAll('[data-testid="grid-item"]');
    expect(renderedItems.length).toBeLessThan(100); // Much less than 10k
  });

  test('should maintain 60fps during scroll', async () => {
    const photos = generateMockPhotos(1000);
    let frameCount = 0;
    let lastFrameTime = 0;
    const frameTimes: number[] = [];

    // Mock requestAnimationFrame to measure frame rate
    const originalRaf = window.requestAnimationFrame;
    window.requestAnimationFrame = (callback: FrameRequestCallback) => {
      const currentTime = performance.now();
      if (lastFrameTime > 0) {
        const delta = currentTime - lastFrameTime;
        frameTimes.push(delta);
      }
      lastFrameTime = currentTime;
      frameCount++;
      return originalRaf(callback);
    };

    const { container } = render(
      <VirtualGrid
        items={photos}
        itemHeight={256}
        gap={16}
        onItemClick={jest.fn()}
      />
    );

    const scrollContainer = container.querySelector('[data-testid="virtual-grid-container"]');
    expect(scrollContainer).toBeTruthy();

    // Simulate rapid scrolling
    await act(async () => {
      for (let i = 0; i < 10; i++) {
        fireEvent.scroll(scrollContainer!, {
          target: { scrollTop: i * 1000 }
        });
        await new Promise(resolve => setTimeout(resolve, 16)); // ~60fps timing
      }
    });

    // Calculate average frame time
    const avgFrameTime = frameTimes.reduce((a, b) => a + b, 0) / frameTimes.length;
    const avgFps = 1000 / avgFrameTime;

    // Should maintain close to 60fps
    expect(avgFps).toBeGreaterThan(55);

    // Restore original RAF
    window.requestAnimationFrame = originalRaf;
  });

  test('should efficiently handle item updates', async () => {
    const photos = generateMockPhotos(5000);
    const { rerender } = render(
      <VirtualGrid
        items={photos}
        itemHeight={256}
        gap={16}
        onItemClick={jest.fn()}
      />
    );

    // Measure update performance
    const startTime = performance.now();

    // Update with new items
    const updatedPhotos = [...photos, ...generateMockPhotos(100)];
    rerender(
      <VirtualGrid
        items={updatedPhotos}
        itemHeight={256}
        gap={16}
        onItemClick={jest.fn()}
      />
    );

    const updateTime = performance.now() - startTime;

    // Should update quickly
    expect(updateTime).toBeLessThan(50);
  });

  test('should lazy load images efficiently', async () => {
    const photos = generateMockPhotos(1000);
    const observerCallbacks: Function[] = [];

    // Mock IntersectionObserver to track observations
    window.IntersectionObserver = jest.fn((callback) => ({
      observe: jest.fn(),
      unobserve: jest.fn(),
      disconnect: jest.fn(),
      root: null,
      rootMargin: '',
      thresholds: [],
      takeRecords: () => []
    })) as any;

    const { container } = render(
      <VirtualGrid
        items={photos}
        itemHeight={256}
        gap={16}
        onItemClick={jest.fn()}
      />
    );

    // Check that only visible items have loaded images
    const images = container.querySelectorAll('img[data-testid="grid-item-image"]');
    const loadedImages = Array.from(images).filter(img =>
      (img as HTMLImageElement).src && !(img as HTMLImageElement).src.includes('placeholder')
    );

    // Should only load visible images initially
    expect(loadedImages.length).toBeLessThan(50);
  });

  test('should handle rapid selection changes efficiently', async () => {
    const photos = generateMockPhotos(1000);
    const onSelectionChange = jest.fn();

    const { container } = render(
      <VirtualGrid
        items={photos}
        itemHeight={256}
        gap={16}
        onItemClick={jest.fn()}
        selectionMode={true}
        onSelectionChange={onSelectionChange}
      />
    );

    const startTime = performance.now();

    // Rapidly toggle selection on multiple items
    await act(async () => {
      for (let i = 0; i < 100; i++) {
        const item = container.querySelector(`[data-testid="grid-item-${i}"]`);
        if (item) {
          fireEvent.click(item);
        }
      }
    });

    const selectionTime = performance.now() - startTime;

    // Should handle rapid selections efficiently
    expect(selectionTime).toBeLessThan(500);
    expect(onSelectionChange).toHaveBeenCalled();
  });

  test('should recycle DOM elements during scroll', async () => {
    const photos = generateMockPhotos(10000);
    const { container } = render(
      <VirtualGrid
        items={photos}
        itemHeight={256}
        gap={16}
        onItemClick={jest.fn()}
      />
    );

    const initialItems = container.querySelectorAll('[data-testid^="grid-item"]');
    const initialCount = initialItems.length;

    // Scroll to middle
    const scrollContainer = container.querySelector('[data-testid="virtual-grid-container"]');
    fireEvent.scroll(scrollContainer!, {
      target: { scrollTop: 5000 * 256 }
    });

    await waitFor(() => {
      const currentItems = container.querySelectorAll('[data-testid^="grid-item"]');
      // Should maintain similar number of DOM elements (recycling)
      expect(Math.abs(currentItems.length - initialCount)).toBeLessThan(10);
    });
  });

  test('should handle window resize efficiently', async () => {
    const photos = generateMockPhotos(1000);
    const { container } = render(
      <VirtualGrid
        items={photos}
        itemHeight={256}
        gap={16}
        onItemClick={jest.fn()}
      />
    );

    const startTime = performance.now();

    // Simulate multiple resize events
    await act(async () => {
      for (let width = 1920; width >= 768; width -= 100) {
        global.innerWidth = width;
        fireEvent(window, new Event('resize'));
        await new Promise(resolve => setTimeout(resolve, 10));
      }
    });

    const resizeTime = performance.now() - startTime;

    // Should handle resize efficiently with debouncing
    expect(resizeTime).toBeLessThan(500);
  });

  test('should measure memory efficiency', async () => {
    // Note: Real memory measurement requires browser APIs
    // This is a simplified test that checks DOM node count

    const photos = generateMockPhotos(100000);
    const { container } = render(
      <VirtualGrid
        items={photos}
        itemHeight={256}
        gap={16}
        onItemClick={jest.fn()}
      />
    );

    // Count total DOM nodes
    const nodeCount = container.querySelectorAll('*').length;

    // Should keep DOM node count low despite large dataset
    expect(nodeCount).toBeLessThan(1000); // Much less than 100k items would create
  });

  test('should optimize thumbnail loading with progressive enhancement', async () => {
    const photos = generateMockPhotos(500);

    const { container } = render(
      <VirtualGrid
        items={photos}
        itemHeight={256}
        gap={16}
        onItemClick={jest.fn()}
        progressive={true}
      />
    );

    // Check for blur-up placeholder strategy
    const images = container.querySelectorAll('img[data-testid="grid-item-image"]');
    const placeholders = Array.from(images).filter(img =>
      img.classList.contains('blur') || img.getAttribute('loading') === 'lazy'
    );

    // Should use progressive loading
    expect(placeholders.length).toBeGreaterThan(0);
  });

  test('should batch DOM updates efficiently', async () => {
    const photos = generateMockPhotos(1000);
    let updateCount = 0;

    // Mock React's batching to count updates
    const originalBatch = (React as any).unstable_batchedUpdates;
    (React as any).unstable_batchedUpdates = (fn: Function) => {
      updateCount++;
      return originalBatch ? originalBatch(fn) : fn();
    };

    const { container } = render(
      <VirtualGrid
        items={photos}
        itemHeight={256}
        gap={16}
        onItemClick={jest.fn()}
      />
    );

    // Trigger multiple updates
    const scrollContainer = container.querySelector('[data-testid="virtual-grid-container"]');
    for (let i = 0; i < 10; i++) {
      fireEvent.scroll(scrollContainer!, {
        target: { scrollTop: i * 100 }
      });
    }

    // Should batch updates (not 10 separate updates)
    expect(updateCount).toBeLessThan(5);

    // Restore
    (React as any).unstable_batchedUpdates = originalBatch;
  });

  test('should handle 100K photos with acceptable performance', async () => {
    const photos = generateMockPhotos(100000);

    const startTime = performance.now();

    const { container } = render(
      <VirtualGrid
        items={photos}
        itemHeight={256}
        gap={16}
        onItemClick={jest.fn()}
      />
    );

    const initialRenderTime = performance.now() - startTime;

    // Initial render should be fast
    expect(initialRenderTime).toBeLessThan(200);

    // Scroll to various positions
    const scrollContainer = container.querySelector('[data-testid="virtual-grid-container"]');
    const scrollPositions = [10000, 50000, 90000, 0];

    for (const position of scrollPositions) {
      const scrollStart = performance.now();

      fireEvent.scroll(scrollContainer!, {
        target: { scrollTop: position }
      });

      await waitFor(() => {
        const scrollTime = performance.now() - scrollStart;
        // Each scroll should be fast
        expect(scrollTime).toBeLessThan(50);
      });
    }

    // Check final DOM node count
    const finalNodeCount = container.querySelectorAll('[data-testid^="grid-item"]').length;
    expect(finalNodeCount).toBeLessThan(200); // Should virtualize effectively
  });

  test('should provide smooth scrolling experience', async () => {
    const photos = generateMockPhotos(5000);
    const scrollEvents: number[] = [];

    const { container } = render(
      <VirtualGrid
        items={photos}
        itemHeight={256}
        gap={16}
        onItemClick={jest.fn()}
      />
    );

    const scrollContainer = container.querySelector('[data-testid="virtual-grid-container"]');

    // Track scroll event timing
    scrollContainer?.addEventListener('scroll', () => {
      scrollEvents.push(performance.now());
    });

    // Simulate smooth scroll
    const startPos = 0;
    const endPos = 10000;
    const duration = 1000; // 1 second
    const steps = 60; // 60fps

    for (let i = 0; i <= steps; i++) {
      const progress = i / steps;
      const easeProgress = 1 - Math.pow(1 - progress, 3); // Cubic ease
      const scrollTop = startPos + (endPos - startPos) * easeProgress;

      fireEvent.scroll(scrollContainer!, {
        target: { scrollTop }
      });

      await new Promise(resolve => setTimeout(resolve, duration / steps));
    }

    // Calculate jank (variation in scroll event timing)
    const deltas = [];
    for (let i = 1; i < scrollEvents.length; i++) {
      deltas.push(scrollEvents[i] - scrollEvents[i - 1]);
    }

    const avgDelta = deltas.reduce((a, b) => a + b, 0) / deltas.length;
    const variance = deltas.reduce((sum, delta) => sum + Math.pow(delta - avgDelta, 2), 0) / deltas.length;
    const stdDev = Math.sqrt(variance);

    // Low standard deviation indicates smooth scrolling
    expect(stdDev).toBeLessThan(10);
  });
});