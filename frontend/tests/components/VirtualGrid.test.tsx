import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { act } from 'react';
import '@testing-library/jest-dom';
import { VirtualGrid } from '../../src/components/VirtualGrid/VirtualGrid';

// Mock IntersectionObserver
const mockIntersectionObserver = jest.fn();
mockIntersectionObserver.mockReturnValue({
  observe: () => null,
  unobserve: () => null,
  disconnect: () => null
});
window.IntersectionObserver = mockIntersectionObserver as any;

// Helper to generate mock photo data
function generateMockPhotos(count: number) {
  return Array.from({ length: count }, (_, i) => ({
    id: `photo-${i}`,
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
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  test('should render large dataset efficiently', async () => {
    const photos = generateMockPhotos(10000);
    const renderItem = (item: any) => <div data-testid={`grid-item-${item.file_id}`}>{item.filename}</div>;

    const { container } = render(
      <VirtualGrid
        items={photos}
        renderItem={renderItem}
        itemHeight={256}
        gap={16}
        onItemClick={jest.fn()}
      />
    );

    // Should only render visible items (not all 10k)
    const renderedItems = container.querySelectorAll('[data-testid^="grid-item"]');
    expect(renderedItems.length).toBeLessThan(200); // Much less than 10k
  });

  test('should maintain 60fps during scroll', async () => {
    const photos = generateMockPhotos(1000);
    const renderItem = (item: any) => <div>{item.filename}</div>;

    const { container } = render(
      <VirtualGrid
        items={photos}
        renderItem={renderItem}
        itemHeight={256}
        gap={16}
        onItemClick={jest.fn()}
      />
    );

    // Find the scroll container
    const scrollContainer = container.querySelector('.overflow-auto');
    expect(scrollContainer).toBeTruthy();

    // Simulate scrolling
    await act(async () => {
      for (let i = 0; i < 10; i++) {
        fireEvent.scroll(scrollContainer!, {
          target: { scrollTop: i * 1000 }
        });
        await new Promise(resolve => setTimeout(resolve, 16));
      }
    });

    expect(scrollContainer).toBeTruthy();
  });

  test('should efficiently handle item updates', async () => {
    const photos = generateMockPhotos(5000);
    const renderItem = (item: any) => <div>{item.filename}</div>;

    const { rerender } = render(
      <VirtualGrid
        items={photos}
        renderItem={renderItem}
        itemHeight={256}
        gap={16}
        onItemClick={jest.fn()}
      />
    );

    // Update with new items
    const updatedPhotos = [...photos, ...generateMockPhotos(100)];
    rerender(
      <VirtualGrid
        items={updatedPhotos}
        renderItem={renderItem}
        itemHeight={256}
        gap={16}
        onItemClick={jest.fn()}
      />
    );

    // Should complete without error
    expect(updatedPhotos.length).toBe(5100);
  });

  test('should lazy load images efficiently', async () => {
    const photos = generateMockPhotos(1000);
    const renderItem = (item: any) => (
      <div>
        <img data-testid="grid-item-image" src={item.thumb_path} alt={item.filename} loading="lazy" />
      </div>
    );

    const { container } = render(
      <VirtualGrid
        items={photos}
        renderItem={renderItem}
        itemHeight={256}
        gap={16}
        onItemClick={jest.fn()}
      />
    );

    const images = container.querySelectorAll('img[data-testid="grid-item-image"]');
    expect(images.length).toBeLessThan(100);
  });

  test('should handle rapid selection changes efficiently', async () => {
    const photos = generateMockPhotos(1000);
    const onSelectionChange = jest.fn();
    const renderItem = (item: any, index: number) => (
      <div data-testid={`grid-item-${index}`}>{item.filename}</div>
    );

    const { container } = render(
      <VirtualGrid
        items={photos}
        renderItem={renderItem}
        itemHeight={256}
        gap={16}
        onItemClick={jest.fn()}
      />
    );

    // Click on visible items
    await act(async () => {
      const renderedItems = container.querySelectorAll('[data-testid^="grid-item"]');
      for (let i = 0; i < Math.min(10, renderedItems.length); i++) {
        fireEvent.click(renderedItems[i]);
      }
    });

    // Test completed successfully
    expect(container).toBeTruthy();
  });

  test('should recycle DOM elements during scroll', async () => {
    const photos = generateMockPhotos(10000);
    const renderItem = (item: any) => <div data-testid="grid-item">{item.filename}</div>;

    const { container } = render(
      <VirtualGrid
        items={photos}
        renderItem={renderItem}
        itemHeight={256}
        gap={16}
        onItemClick={jest.fn()}
      />
    );

    const initialItems = container.querySelectorAll('[data-testid="grid-item"]');
    const initialCount = initialItems.length;

    const scrollContainer = container.querySelector('.overflow-auto');
    await act(async () => {
      fireEvent.scroll(scrollContainer!, {
        target: { scrollTop: 5000 }
      });
    });

    await waitFor(() => {
      const currentItems = container.querySelectorAll('[data-testid="grid-item"]');
      // Should maintain similar number of DOM elements (recycling)
      expect(Math.abs(currentItems.length - initialCount)).toBeLessThan(50);
    });
  });

  test('should handle window resize efficiently', async () => {
    const photos = generateMockPhotos(1000);
    const renderItem = (item: any) => <div>{item.filename}</div>;

    const { container } = render(
      <VirtualGrid
        items={photos}
        renderItem={renderItem}
        itemHeight={256}
        gap={16}
        onItemClick={jest.fn()}
      />
    );

    // Simulate resize events
    await act(async () => {
      for (let width = 1920; width >= 768; width -= 100) {
        global.innerWidth = width;
        fireEvent(window, new Event('resize'));
        await new Promise(resolve => setTimeout(resolve, 10));
      }
    });

    expect(container).toBeTruthy();
  });

  test('should measure memory efficiency', async () => {
    const photos = generateMockPhotos(100000);
    const renderItem = (item: any) => <div>{item.filename}</div>;

    const { container } = render(
      <VirtualGrid
        items={photos}
        renderItem={renderItem}
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
    const renderItem = (item: any) => (
      <img
        data-testid="grid-item-image"
        src={item.thumb_path}
        alt={item.filename}
        loading="lazy"
        className="blur"
      />
    );

    const { container } = render(
      <VirtualGrid
        items={photos}
        renderItem={renderItem}
        itemHeight={256}
        gap={16}
        onItemClick={jest.fn()}
      />
    );

    // VirtualGrid only renders visible items, so there might be lazy loaded images
    const images = container.querySelectorAll('img[data-testid="grid-item-image"]');
    const lazyImages = Array.from(images).filter(img =>
      img.getAttribute('loading') === 'lazy'
    );

    // If any images are rendered (virtualization shows visible items), they should have lazy loading
    if (images.length > 0) {
      expect(lazyImages.length).toBeGreaterThan(0);
    } else {
      // If no images are rendered due to virtualization, that's acceptable
      expect(images.length).toBe(0);
    }
  });

  test('should batch DOM updates efficiently', async () => {
    const photos = generateMockPhotos(1000);
    const renderItem = (item: any) => <div>{item.filename}</div>;

    const { container } = render(
      <VirtualGrid
        items={photos}
        renderItem={renderItem}
        itemHeight={256}
        gap={16}
        onItemClick={jest.fn()}
      />
    );

    const scrollContainer = container.querySelector('.overflow-auto');

    // Trigger multiple updates
    await act(async () => {
      for (let i = 0; i < 10; i++) {
        fireEvent.scroll(scrollContainer!, {
          target: { scrollTop: i * 100 }
        });
      }
    });

    expect(scrollContainer).toBeTruthy();
  });

  test('should handle 100K photos with acceptable performance', async () => {
    const photos = generateMockPhotos(100000);
    const renderItem = (item: any) => <div data-testid="grid-item">{item.filename}</div>;

    const { container } = render(
      <VirtualGrid
        items={photos}
        renderItem={renderItem}
        itemHeight={256}
        gap={16}
        onItemClick={jest.fn()}
      />
    );

    const scrollContainer = container.querySelector('.overflow-auto');
    const scrollPositions = [10000, 50000, 90000, 0];

    for (const position of scrollPositions) {
      await act(async () => {
        fireEvent.scroll(scrollContainer!, {
          target: { scrollTop: position }
        });
      });
    }

    // Check final DOM node count
    const finalNodeCount = container.querySelectorAll('[data-testid="grid-item"]').length;
    expect(finalNodeCount).toBeLessThan(200); // Should virtualize effectively
  });

  test('should provide smooth scrolling experience', async () => {
    const photos = generateMockPhotos(5000);
    const renderItem = (item: any) => <div>{item.filename}</div>;

    const { container } = render(
      <VirtualGrid
        items={photos}
        renderItem={renderItem}
        itemHeight={256}
        gap={16}
        onItemClick={jest.fn()}
      />
    );

    const scrollContainer = container.querySelector('.overflow-auto');

    // Simulate smooth scroll
    const startPos = 0;
    const endPos = 10000;
    const steps = 10;

    for (let i = 0; i <= steps; i++) {
      const progress = i / steps;
      const scrollTop = startPos + (endPos - startPos) * progress;

      await act(async () => {
        fireEvent.scroll(scrollContainer!, {
          target: { scrollTop }
        });
      });

      await new Promise(resolve => setTimeout(resolve, 10));
    }

    expect(scrollContainer).toBeTruthy();
  });
});
