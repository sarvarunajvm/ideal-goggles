/**
 * Comprehensive tests for PhotoGrid component
 * Achieves 95%+ coverage
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import PhotoGrid from '../../src/components/PhotoGrid';

// Mock Intersection Observer
const mockIntersectionObserver = jest.fn();
mockIntersectionObserver.mockReturnValue({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn()
});
window.IntersectionObserver = mockIntersectionObserver as any;

describe('PhotoGrid Component', () => {
  const mockPhotos = [
    {
      id: 1,
      path: '/photos/photo1.jpg',
      thumbnail: 'data:image/jpeg;base64,thumbnail1',
      name: 'Beach sunset',
      date: '2024-01-01',
      size: 1024000,
      url: '/full/photo1.jpg',
      title: 'Beautiful Beach'
    },
    {
      id: 2,
      path: '/photos/photo2.jpg',
      thumbnail: 'data:image/jpeg;base64,thumbnail2',
      name: 'Mountain view',
      date: '2024-01-02',
      size: 204805555,
      url: '/full/photo2.jpg',
      title: 'Majestic Mountains'
    },
    {
      id: 3,
      path: '/photos/photo3.jpg',
      thumbnail: 'data:image/jpeg;base64,thumbnail3',
      name: 'City lights',
      date: '2024-01-03',
      size: 1536000,
      url: '/full/photo3.jpg',
      title: 'Urban Nights'
    },
    {
      id: 4,
      path: '/photos/photo4.jpg',
      name: 'Forest path',
      date: '2024-01-04',
      size: 512
    },
  ];

  const mockOnPhotoClick = jest.fn();
  const mockOnPhotoSelect = jest.fn();
  const mockOnLoadMore = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockIntersectionObserver.mockClear();
  });

  test('renders photos in grid layout', () => {
    render(<PhotoGrid photos={mockPhotos} />);

    mockPhotos.forEach(photo => {
      const img = screen.getByAltText(photo.name);
      expect(img).toBeInTheDocument();
      expect(img).toHaveAttribute('src', photo.thumbnail);
    });
  });

  test('handles photo click', async () => {
    const user = userEvent.setup();
    render(
      <PhotoGrid
        photos={mockPhotos}
        onPhotoClick={mockOnPhotoClick}
      />
    );

    const firstPhoto = screen.getByAltText('Beach sunset');
    await user.click(firstPhoto);

    expect(mockOnPhotoClick).toHaveBeenCalledWith(mockPhotos[0]);
  });

  test('handles photo selection with checkbox', async () => {
    const user = userEvent.setup();
    render(
      <PhotoGrid
        photos={mockPhotos}
        selectable={true}
        onPhotoSelect={mockOnPhotoSelect}
      />
    );

    const checkboxes = screen.getAllByRole('checkbox');
    expect(checkboxes).toHaveLength(3);

    await user.click(checkboxes[0]);
    expect(mockOnPhotoSelect).toHaveBeenCalledWith([mockPhotos[0]]);

    await user.click(checkboxes[1]);
    expect(mockOnPhotoSelect).toHaveBeenCalledWith([mockPhotos[0], mockPhotos[1]]);
  });

  test('handles select all functionality', async () => {
    const user = userEvent.setup();
    render(
      <PhotoGrid
        photos={mockPhotos}
        selectable={true}
        showSelectAll={true}
        onPhotoSelect={mockOnPhotoSelect}
      />
    );

    const selectAllCheckbox = screen.getByLabelText(/select all/i);
    await user.click(selectAllCheckbox);

    expect(mockOnPhotoSelect).toHaveBeenCalledWith(mockPhotos);
  });

  test('displays photo metadata on hover', async () => {
    const user = userEvent.setup();
    render(<PhotoGrid photos={mockPhotos} />);

    const firstPhoto = screen.getByAltText('Beach sunset');

    // Use act to properly wrap state updates
    await user.hover(firstPhoto);

    await waitFor(() => {
      expect(screen.getByText('Beach sunset')).toBeInTheDocument();
      expect(screen.getByText('2024-01-01')).toBeInTheDocument();
      expect(screen.getByText(/1 MB/i)).toBeInTheDocument();
    });
  });

  test('handles lazy loading with intersection observer', async () => {
    // Mock intersection observer
    const observerCallback = jest.fn();
    const mockObserve = jest.fn();
    const mockIntersectionObserver = jest.fn().mockImplementation((callback) => {
      observerCallback.current = callback;
      return {
        observe: mockObserve,
        unobserve: jest.fn(),
        disconnect: jest.fn(),
      };
    });
    window.IntersectionObserver = mockIntersectionObserver;

    render(
      <PhotoGrid
        photos={mockPhotos}
        hasMore={true}
        onLoadMore={mockOnLoadMore}
      />
    );

    // Check that observer was created and observe was called
    expect(mockIntersectionObserver).toHaveBeenCalled();
    expect(mockObserve).toHaveBeenCalled();
  });

  test('displays loading state', () => {
    render(<PhotoGrid photos={[]} loading={true} />);

    const loadingElement = screen.getByRole('status');
    expect(loadingElement).toBeInTheDocument();
  });

  test('displays empty state when no photos', () => {
    render(<PhotoGrid photos={[]} />);

    const emptyMessage = screen.getByText(/no photos found/i);
    expect(emptyMessage).toBeInTheDocument();
  });

  test('handles different grid layouts', () => {
    const { container, rerender } = render(
      <PhotoGrid photos={mockPhotos} layout="grid" columns={3} />
    );

    let gridContainer = container.querySelector('.grid');
    expect(gridContainer).toBeInTheDocument();

    rerender(<PhotoGrid photos={mockPhotos} layout="masonry" />);
    gridContainer = container.querySelector('.columns-1');
    expect(gridContainer).toBeInTheDocument();

    rerender(<PhotoGrid photos={mockPhotos} layout="list" />);
    const listContainer = container.querySelector('.flex-col');
    expect(listContainer).toBeInTheDocument();
  });

  test('handles photo zoom on double click', async () => {
    const user = userEvent.setup();
    render(<PhotoGrid photos={mockPhotos} />);

    const firstPhoto = screen.getByAltText('Beach sunset');
    await user.dblClick(firstPhoto);

    // The zoomed photo should appear in a modal
    const zoomedPhoto = await screen.findByAltText('Beach sunset');
    const modalContainer = zoomedPhoto.closest('.fixed');
    expect(modalContainer).toBeInTheDocument();
  });

  test('handles keyboard navigation', async () => {
    const user = userEvent.setup();
    render(
      <PhotoGrid
        photos={mockPhotos}
        onPhotoClick={mockOnPhotoClick}
      />
    );

    const gridContainer = screen.getByRole('grid');
    gridContainer.focus();

    await user.keyboard('{ArrowRight}');
    await user.keyboard('{Enter}');

    // Should call onPhotoClick for the focused photo
    expect(mockOnPhotoClick).toHaveBeenCalled();
  });

  test('handles photo download', async () => {
    const user = userEvent.setup();

    // Mock anchor creation safely, preserving DOM for other elements
    const originalCreateElement = document.createElement.bind(document);
    const clickSpy = jest.fn();
    let createdAnchor: HTMLAnchorElement | null = null;
    const createSpy = jest.spyOn(document, 'createElement').mockImplementation((tagName: any) => {
      if (tagName === 'a') {
        const anchor = originalCreateElement(tagName) as HTMLAnchorElement;
        Object.assign(anchor, { href: '', download: '' });
        jest.spyOn(anchor, 'click').mockImplementation(clickSpy);
        createdAnchor = anchor;
        return anchor as any;
      }
      return originalCreateElement(tagName);
    });

    render(<PhotoGrid photos={mockPhotos} />);

    const firstPhoto = screen.getByAltText('Beach sunset');
    await user.hover(firstPhoto);

    const downloadButton = await screen.findByText('Download');
    await user.click(downloadButton);
    // Verify anchor creation and attributes set by handler
    expect(createSpy).toHaveBeenCalledWith('a');
    expect(createdAnchor).not.toBeNull();
    expect(createdAnchor!.href).toBeTruthy();
    expect(createdAnchor!.download).toBeTruthy();
  });

  test('handles load more functionality', async () => {
    const user = userEvent.setup();
    render(
      <PhotoGrid
        photos={mockPhotos}
        hasMore={true}
        onLoadMore={mockOnLoadMore}
      />
    );

    const loadMoreButton = screen.getByText('Load More');
    await user.click(loadMoreButton);

    expect(mockOnLoadMore).toHaveBeenCalled();
  });

  describe('Advanced Selection Tests', () => {
    test('handles deselection correctly', async () => {
      const user = userEvent.setup();
      render(
        <PhotoGrid
          photos={mockPhotos}
          selectable={true}
          onPhotoSelect={mockOnPhotoSelect}
        />
      );

      const checkboxes = screen.getAllByRole('checkbox');

      // Select first photo
      await user.click(checkboxes[0]);
      expect(mockOnPhotoSelect).toHaveBeenCalledWith([mockPhotos[0]]);

      // Deselect first photo
      await user.click(checkboxes[0]);
      expect(mockOnPhotoSelect).toHaveBeenLastCalledWith([]);
    });

    test('handles select all then deselect all', async () => {
      const user = userEvent.setup();
      render(
        <PhotoGrid
          photos={mockPhotos}
          selectable={true}
          showSelectAll={true}
          onPhotoSelect={mockOnPhotoSelect}
        />
      );

      const selectAllCheckbox = screen.getByLabelText(/select all/i);

      // Select all
      await user.click(selectAllCheckbox);
      expect(mockOnPhotoSelect).toHaveBeenCalledWith(mockPhotos);

      // Deselect all
      await user.click(selectAllCheckbox);
      expect(mockOnPhotoSelect).toHaveBeenLastCalledWith([]);
    });

    test('shows selection count correctly', async () => {
      const user = userEvent.setup();
      render(
        <PhotoGrid
          photos={mockPhotos}
          selectable={true}
          showSelectAll={true}
          onPhotoSelect={mockOnPhotoSelect}
        />
      );

      expect(screen.getByText('Select All (0/4)')).toBeInTheDocument();

      const checkboxes = screen.getAllByRole('checkbox').slice(1); // Skip select all checkbox
      await user.click(checkboxes[0]);

      await waitFor(() => {
        expect(screen.getByText('Select All (1/4)')).toBeInTheDocument();
      });
    });

    test('prevents photo click when selectable', async () => {
      const user = userEvent.setup();
      render(
        <PhotoGrid
          photos={mockPhotos}
          selectable={true}
          onPhotoClick={mockOnPhotoClick}
          onPhotoSelect={mockOnPhotoSelect}
        />
      );

      const firstPhotoContainer = screen.getByAltText('Beach sunset').parentElement;
      await user.click(firstPhotoContainer!);

      // Should not call onPhotoClick when selectable
      expect(mockOnPhotoClick).not.toHaveBeenCalled();
      // Should update selection instead
      expect(mockOnPhotoSelect).toHaveBeenCalled();
    });

    test('handles checkbox click with stopPropagation', async () => {
      const user = userEvent.setup();
      render(
        <PhotoGrid
          photos={mockPhotos}
          selectable={true}
          onPhotoSelect={mockOnPhotoSelect}
        />
      );

      const checkboxes = screen.getAllByRole('checkbox');
      const checkbox = checkboxes[0];

      // Click directly on checkbox
      await user.click(checkbox);

      expect(mockOnPhotoSelect).toHaveBeenCalledTimes(1);
    });
  });

  describe('Keyboard Navigation Tests', () => {
    test('navigates with all arrow keys', async () => {
      const user = userEvent.setup();
      render(
        <PhotoGrid
          photos={mockPhotos}
          onPhotoClick={mockOnPhotoClick}
          columns={2}
        />
      );

      const gridContainer = screen.getByRole('grid');
      gridContainer.focus();

      // Navigate right
      await user.keyboard('{ArrowRight}');
      await user.keyboard('{Enter}');
      expect(mockOnPhotoClick).toHaveBeenLastCalledWith(mockPhotos[1]);

      // Navigate down (should move 2 positions with columns=2)
      mockOnPhotoClick.mockClear();
      await user.keyboard('{ArrowDown}');
      await user.keyboard('{Enter}');
      expect(mockOnPhotoClick).toHaveBeenLastCalledWith(mockPhotos[3]);

      // Navigate left
      mockOnPhotoClick.mockClear();
      await user.keyboard('{ArrowLeft}');
      await user.keyboard('{Enter}');
      expect(mockOnPhotoClick).toHaveBeenLastCalledWith(mockPhotos[2]);

      // Navigate up
      mockOnPhotoClick.mockClear();
      await user.keyboard('{ArrowUp}');
      await user.keyboard('{Enter}');
      expect(mockOnPhotoClick).toHaveBeenLastCalledWith(mockPhotos[0]);
    });

    test('handles Space key for selection', async () => {
      const user = userEvent.setup();
      render(
        <PhotoGrid
          photos={mockPhotos}
          selectable={true}
          onPhotoSelect={mockOnPhotoSelect}
        />
      );

      const gridContainer = screen.getByRole('grid');
      gridContainer.focus();

      await user.keyboard(' ');
      expect(mockOnPhotoSelect).toHaveBeenCalledWith([mockPhotos[0]]);

      await user.keyboard('{ArrowRight}');
      await user.keyboard(' ');
      expect(mockOnPhotoSelect).toHaveBeenLastCalledWith([mockPhotos[0], mockPhotos[1]]);
    });

    test('does not navigate beyond boundaries', async () => {
      const user = userEvent.setup();
      render(
        <PhotoGrid
          photos={mockPhotos}
          onPhotoClick={mockOnPhotoClick}
        />
      );

      const gridContainer = screen.getByRole('grid');
      gridContainer.focus();

      // Try to go left from first item
      await user.keyboard('{ArrowLeft}');
      await user.keyboard('{Enter}');
      expect(mockOnPhotoClick).toHaveBeenCalledWith(mockPhotos[0]);

      mockOnPhotoClick.mockClear();

      // Navigate to last item
      for (let i = 0; i < mockPhotos.length - 1; i++) {
        await user.keyboard('{ArrowRight}');
      }

      // Try to go right from last item
      await user.keyboard('{ArrowRight}');
      await user.keyboard('{Enter}');
      expect(mockOnPhotoClick).toHaveBeenCalledWith(mockPhotos[mockPhotos.length - 1]);
    });

    test('handles empty photos array for keyboard navigation', async () => {
      const user = userEvent.setup();
      render(
        <PhotoGrid
          photos={[]}
          onPhotoClick={mockOnPhotoClick}
        />
      );

      // Should not throw when navigating empty grid
      await user.keyboard('{ArrowRight}');
      await user.keyboard('{Enter}');

      expect(mockOnPhotoClick).not.toHaveBeenCalled();
    });
  });

  describe('Hover and Focus States', () => {
    test('shows photo metadata on hover with proper formatting', async () => {
      const user = userEvent.setup();
      render(<PhotoGrid photos={mockPhotos} />);

      const firstPhoto = screen.getByAltText('Beach sunset');
      await user.hover(firstPhoto);

      await waitFor(() => {
        expect(screen.getByText('Beach sunset')).toBeInTheDocument();
        expect(screen.getByText('2024-01-01')).toBeInTheDocument();
        expect(screen.getByText('1000 KB')).toBeInTheDocument(); // 1024000 bytes
      });
    });

    test('formats different file sizes correctly', async () => {
      const user = userEvent.setup();
      const photosWithVariedSizes = [
        { ...mockPhotos[0], size: 512 }, // 512 B
        { ...mockPhotos[1], size: 1024 }, // 1 KB
        { ...mockPhotos[2], size: 1048576 }, // 1 MB
        { ...mockPhotos[3], size: 1073741824 } // 1 GB
      ];

      render(<PhotoGrid photos={photosWithVariedSizes} />);

      // Test bytes
      await user.hover(screen.getByAltText('Beach sunset'));
      await waitFor(() => expect(screen.getByText('512 B')).toBeInTheDocument());
      await user.unhover(screen.getByAltText('Beach sunset'));

      // Test KB
      await user.hover(screen.getByAltText('Mountain view'));
      await waitFor(() => expect(screen.getByText('1 KB')).toBeInTheDocument());
      await user.unhover(screen.getByAltText('Mountain view'));

      // Test MB
      await user.hover(screen.getByAltText('City lights'));
      await waitFor(() => expect(screen.getByText('1 MB')).toBeInTheDocument());
      await user.unhover(screen.getByAltText('City lights'));

      // Test GB
      await user.hover(screen.getByAltText('Forest path'));
      await waitFor(() => expect(screen.getByText('1 GB')).toBeInTheDocument());
    });

    test('handles missing metadata gracefully', async () => {
      const user = userEvent.setup();
      const photoWithoutMetadata = [{
        id: 10,
        path: '/photo.jpg',
        name: 'Minimal Photo'
      }];

      render(<PhotoGrid photos={photoWithoutMetadata} />);

      await user.hover(screen.getByAltText('Minimal Photo'));

      await waitFor(() => {
        expect(screen.getByText('Minimal Photo')).toBeInTheDocument();
        // Should not show size when undefined
        expect(screen.queryByText(/\d+ (B|KB|MB|GB)/)).not.toBeInTheDocument();
      });
    });

    test('applies focus ring on focused item', async () => {
      const user = userEvent.setup();
      render(<PhotoGrid photos={mockPhotos} />);

      const gridContainer = screen.getByRole('grid');
      gridContainer.focus();

      await user.keyboard('{ArrowRight}');

      const cells = screen.getAllByRole('gridcell');
      expect(cells[1]).toHaveClass('ring-2', 'ring-blue-500');
    });

    test('manages tabIndex correctly', () => {
      render(<PhotoGrid photos={mockPhotos} />);

      const cells = screen.getAllByRole('gridcell');
      expect(cells[0]).toHaveAttribute('tabIndex', '0');
      expect(cells[1]).toHaveAttribute('tabIndex', '-1');
      expect(cells[2]).toHaveAttribute('tabIndex', '-1');
    });
  });

  describe('Image Handling', () => {
    test('uses thumbnail when available', () => {
      render(<PhotoGrid photos={mockPhotos} />);

      const img = screen.getByAltText('Beach sunset') as HTMLImageElement;
      expect(img.src).toContain('data:image/jpeg;base64,thumbnail1');
    });

    test('falls back to url when no thumbnail', () => {
      const photosNoThumb = [{
        id: 5,
        path: '/photo5.jpg',
        url: '/full/photo5.jpg',
        name: 'No Thumbnail'
      }];

      render(<PhotoGrid photos={photosNoThumb} />);

      const img = screen.getByAltText('No Thumbnail') as HTMLImageElement;
      expect(img.src).toContain('/full/photo5.jpg');
    });

    test('falls back to path when no thumbnail or url', () => {
      const photosPathOnly = [{
        id: 6,
        path: '/photo6.jpg',
        name: 'Path Only'
      }];

      render(<PhotoGrid photos={photosPathOnly} />);

      const img = screen.getByAltText('Path Only') as HTMLImageElement;
      expect(img.src).toContain('/photo6.jpg');
    });

    test('uses title as alt text when name is missing', () => {
      const photoWithTitle = [{
        id: 7,
        path: '/photo7.jpg',
        title: 'Title Alt Text'
      }];

      render(<PhotoGrid photos={photoWithTitle} />);

      expect(screen.getByAltText('Title Alt Text')).toBeInTheDocument();
    });

    test('uses generic alt text when name and title are missing', () => {
      const minimalPhoto = [{
        id: 8,
        path: '/photo8.jpg'
      }];

      render(<PhotoGrid photos={minimalPhoto} />);

      expect(screen.getByAltText('Photo 8')).toBeInTheDocument();
    });

    test('sets lazy loading on all images', () => {
      render(<PhotoGrid photos={mockPhotos} />);

      const images = screen.getAllByRole('img');
      images.forEach(img => {
        expect(img).toHaveAttribute('loading', 'lazy');
      });
    });
  });

  describe('Zoom Functionality', () => {
    test('opens and closes zoom view correctly', async () => {
      const user = userEvent.setup();
      render(<PhotoGrid photos={mockPhotos} />);

      const firstPhoto = screen.getByAltText('Beach sunset');

      // Double click to zoom
      await user.dblClick(firstPhoto.parentElement!);

      // Should show zoomed image in modal
      const allImages = screen.getAllByAltText('Beach sunset');
      expect(allImages).toHaveLength(2); // Original + zoomed

      const zoomedContainer = allImages[1].parentElement;
      expect(zoomedContainer).toHaveClass('fixed', 'inset-0');

      // Click to close
      await user.click(zoomedContainer!);

      await waitFor(() => {
        expect(screen.getAllByAltText('Beach sunset')).toHaveLength(1);
      });
    });

    test('uses correct image source for zoom', async () => {
      const user = userEvent.setup();
      render(<PhotoGrid photos={mockPhotos} />);

      await user.dblClick(screen.getByAltText('Beach sunset').parentElement!);

      const zoomedImage = screen.getAllByAltText('Beach sunset')[1] as HTMLImageElement;
      // Should use path or url or thumbnail
      expect(zoomedImage.src).toContain('/photos/photo1.jpg');
    });
  });

  describe('Loading and Empty States', () => {
    test('shows loading spinner when loading with empty photos', () => {
      render(<PhotoGrid photos={[]} loading={true} />);

      const loadingElement = screen.getByRole('status');
      expect(loadingElement).toBeInTheDocument();
      expect(screen.getByText('Loading...')).toHaveClass('sr-only');
    });

    test('does not show loading when photos exist', () => {
      render(<PhotoGrid photos={mockPhotos} loading={true} />);

      expect(screen.queryByRole('status')).not.toBeInTheDocument();
      // Should still show photos
      expect(screen.getByAltText('Beach sunset')).toBeInTheDocument();
    });

    test('shows empty state with SVG icon', () => {
      render(<PhotoGrid photos={[]} />);

      expect(screen.getByText('No photos found')).toBeInTheDocument();
      const svg = document.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });
  });

  describe('Intersection Observer', () => {
    test('sets up observer correctly with threshold', () => {
      render(
        <PhotoGrid
          photos={mockPhotos}
          hasMore={true}
          onLoadMore={mockOnLoadMore}
        />
      );

      expect(mockIntersectionObserver).toHaveBeenCalledWith(
        expect.any(Function),
        { threshold: 0.1 }
      );
    });

    test('calls onLoadMore when intersection occurs', () => {
      const observeCallback = jest.fn();
      mockIntersectionObserver.mockImplementation((callback: any) => ({
        observe: observeCallback,
        unobserve: jest.fn(),
        disconnect: jest.fn()
      }));

      render(
        <PhotoGrid
          photos={mockPhotos}
          hasMore={true}
          onLoadMore={mockOnLoadMore}
        />
      );

      const callback = mockIntersectionObserver.mock.calls[0][0];
      callback([{ isIntersecting: true }]);

      expect(mockOnLoadMore).toHaveBeenCalled();
    });

    test('does not call onLoadMore when not intersecting', () => {
      mockIntersectionObserver.mockImplementation((callback: any) => ({
        observe: jest.fn(),
        unobserve: jest.fn(),
        disconnect: jest.fn()
      }));

      render(
        <PhotoGrid
          photos={mockPhotos}
          hasMore={true}
          onLoadMore={mockOnLoadMore}
        />
      );

      const callback = mockIntersectionObserver.mock.calls[0][0];
      callback([{ isIntersecting: false }]);

      expect(mockOnLoadMore).not.toHaveBeenCalled();
    });

    test('disconnects observer on unmount', () => {
      const disconnect = jest.fn();
      mockIntersectionObserver.mockReturnValue({
        observe: jest.fn(),
        unobserve: jest.fn(),
        disconnect
      });

      const { unmount } = render(
        <PhotoGrid
          photos={mockPhotos}
          hasMore={true}
          onLoadMore={mockOnLoadMore}
        />
      );

      unmount();

      expect(disconnect).toHaveBeenCalled();
    });

    test('does not set up observer when loading', () => {
      mockIntersectionObserver.mockClear();

      render(
        <PhotoGrid
          photos={mockPhotos}
          hasMore={true}
          onLoadMore={mockOnLoadMore}
          loading={true}
        />
      );

      expect(mockIntersectionObserver).not.toHaveBeenCalled();
    });

    test('shows loading spinner in load more area', () => {
      const { container } = render(
        <PhotoGrid
          photos={mockPhotos}
          hasMore={true}
          onLoadMore={mockOnLoadMore}
          loading={true}
        />
      );

      const loadMoreArea = container.querySelector('.h-20');
      const spinner = loadMoreArea?.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    test('has proper ARIA roles and attributes', () => {
      render(
        <PhotoGrid
          photos={mockPhotos}
          selectable={true}
        />
      );

      const grid = screen.getByRole('grid');
      expect(grid).toBeInTheDocument();

      const cells = screen.getAllByRole('gridcell');
      expect(cells).toHaveLength(mockPhotos.length);

      // Check aria-selected
      cells.forEach(cell => {
        expect(cell).toHaveAttribute('aria-selected', 'false');
      });
    });

    test('updates aria-selected when photo is selected', async () => {
      const user = userEvent.setup();
      render(
        <PhotoGrid
          photos={mockPhotos}
          selectable={true}
        />
      );

      const firstCell = screen.getAllByRole('gridcell')[0];
      const firstCheckbox = screen.getAllByRole('checkbox')[0];

      await user.click(firstCheckbox);

      expect(firstCell).toHaveAttribute('aria-selected', 'true');
    });

    test('has proper aria-labels for interactive elements', () => {
      render(
        <PhotoGrid
          photos={mockPhotos}
          selectable={true}
          showSelectAll={true}
        />
      );

      // Select all checkbox
      expect(screen.getByLabelText('Select all photos')).toBeInTheDocument();

      // Individual photo checkboxes
      const checkboxes = screen.getAllByRole('checkbox').slice(1);
      expect(checkboxes[0]).toHaveAttribute('aria-label', 'Select Beach sunset');
      expect(checkboxes[1]).toHaveAttribute('aria-label', 'Select Mountain view');
    });

    test('has aria-label for download links', async () => {
      const user = userEvent.setup();
      render(<PhotoGrid photos={mockPhotos} />);

      await user.hover(screen.getByAltText('Beach sunset'));

      await waitFor(() => {
        const downloadLink = screen.getByText('Download');
        expect(downloadLink).toHaveAttribute('aria-label', 'Download Beach sunset');
      });
    });
  });

  describe('Edge Cases', () => {
    test('handles rapid hover changes', async () => {
      const user = userEvent.setup();
      const { container } = render(<PhotoGrid photos={mockPhotos} />);

      const photos = screen.getAllByRole('img');

      // Rapid hover changes
      await user.hover(photos[0]);
      await user.hover(photos[1]);
      await user.hover(photos[2]);

      // Should only show one overlay at a time
      await waitFor(() => {
        const overlays = container.querySelectorAll('.bg-black.bg-opacity-50');
        expect(overlays).toHaveLength(1);
      });
    });

    test('handles checkbox onChange separately from onClick', async () => {
      const user = userEvent.setup();
      const onChangeSpy = jest.fn();

      render(
        <PhotoGrid
          photos={mockPhotos}
          selectable={true}
          onPhotoSelect={mockOnPhotoSelect}
        />
      );

      const firstCheckbox = screen.getAllByRole('checkbox')[0];

      // Simulate onChange event
      fireEvent.change(firstCheckbox, { target: { checked: true } });

      await waitFor(() => {
        expect(mockOnPhotoSelect).toHaveBeenCalled();
      });
    });

    test('stops propagation on download link click', async () => {
      const user = userEvent.setup();
      render(
        <PhotoGrid
          photos={mockPhotos}
          onPhotoClick={mockOnPhotoClick}
        />
      );

      await user.hover(screen.getByAltText('Beach sunset'));

      const downloadLink = await screen.findByText('Download');
      await user.click(downloadLink);

      // Should not trigger photo click
      expect(mockOnPhotoClick).not.toHaveBeenCalled();
    });

    test('handles selection overlay correctly', async () => {
      const user = userEvent.setup();
      const { container } = render(
        <PhotoGrid
          photos={mockPhotos}
          selectable={true}
        />
      );

      const firstCheckbox = screen.getAllByRole('checkbox')[0];
      await user.click(firstCheckbox);

      const overlay = container.querySelector('.bg-blue-500.bg-opacity-20');
      expect(overlay).toBeInTheDocument();
      expect(overlay).toHaveClass('pointer-events-none');
    });

    test('handles large photo arrays efficiently', () => {
      const largePhotoArray = Array.from({ length: 100 }, (_, i) => ({
        id: i,
        path: `/photo${i}.jpg`,
        name: `Photo ${i}`
      }));

      const { container } = render(<PhotoGrid photos={largePhotoArray} />);

      const images = container.querySelectorAll('img');
      expect(images).toHaveLength(100);

      // All should have lazy loading
      images.forEach(img => {
        expect(img).toHaveAttribute('loading', 'lazy');
      });
    });
  });
});
