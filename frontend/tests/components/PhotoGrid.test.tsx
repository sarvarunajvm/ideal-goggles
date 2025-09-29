/**
 * Unit tests for PhotoGrid component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import PhotoGrid from '../../src/components/PhotoGrid';

describe('PhotoGrid Component', () => {
  const mockPhotos = [
    {
      id: 1,
      path: '/photos/photo1.jpg',
      thumbnail: 'data:image/jpeg;base64,thumbnail1',
      name: 'Beach sunset',
      date: '2024-01-01',
      size: 1024000,
    },
    {
      id: 2,
      path: '/photos/photo2.jpg',
      thumbnail: 'data:image/jpeg;base64,thumbnail2',
      name: 'Mountain view',
      date: '2024-01-02',
      size: 204805555,
    },
    {
      id: 3,
      path: '/photos/photo3.jpg',
      thumbnail: 'data:image/jpeg;base64,thumbnail3',
      name: 'City lights',
      date: '2024-01-03',
      size: 1536000,
    },
  ];

  const mockOnPhotoClick = jest.fn();
  const mockOnPhotoSelect = jest.fn();
  const mockOnLoadMore = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
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
});
