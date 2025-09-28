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
      const img = screen.getByAlt(photo.name);
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

    const firstPhoto = screen.getByAlt('Beach sunset');
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
    render(<PhotoGrid photos={mockPhotos} showMetadata={true} />);

    const firstPhoto = screen.getByAlt('Beach sunset');
    await user.hover(firstPhoto);

    await waitFor(() => {
      expect(screen.getByText('Beach sunset')).toBeInTheDocument();
      expect(screen.getByText('2024-01-01')).toBeInTheDocument();
      expect(screen.getByText(/1\.0 MB/i)).toBeInTheDocument();
    });
  });

  test('handles lazy loading with intersection observer', async () => {
    const { rerender } = render(
      <PhotoGrid
        photos={mockPhotos}
        lazyLoad={true}
        onLoadMore={mockOnLoadMore}
      />
    );

    // Mock intersection observer
    const observerCallback = jest.fn();
    const mockIntersectionObserver = jest.fn().mockImplementation((callback) => {
      observerCallback.current = callback;
      return {
        observe: jest.fn(),
        unobserve: jest.fn(),
        disconnect: jest.fn(),
      };
    });
    window.IntersectionObserver = mockIntersectionObserver;

    // Simulate scrolling to bottom
    const loadMoreTrigger = screen.getByTestId('load-more-trigger');
    observerCallback.current([{ isIntersecting: true }]);

    await waitFor(() => {
      expect(mockOnLoadMore).toHaveBeenCalled();
    });
  });

  test('displays loading state', () => {
    render(<PhotoGrid photos={[]} isLoading={true} />);

    const loadingSpinner = screen.getByTestId('grid-loading');
    expect(loadingSpinner).toBeInTheDocument();
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

    let gridContainer = container.querySelector('.photo-grid');
    expect(gridContainer).toHaveStyle('grid-template-columns: repeat(3, 1fr)');

    rerender(<PhotoGrid photos={mockPhotos} layout="masonry" />);
    gridContainer = container.querySelector('.photo-masonry');
    expect(gridContainer).toBeInTheDocument();

    rerender(<PhotoGrid photos={mockPhotos} layout="list" />);
    const listContainer = container.querySelector('.photo-list');
    expect(listContainer).toBeInTheDocument();
  });

  test('handles photo zoom on double click', async () => {
    const user = userEvent.setup();
    render(<PhotoGrid photos={mockPhotos} enableZoom={true} />);

    const firstPhoto = screen.getByAlt('Beach sunset');
    await user.dblClick(firstPhoto);

    const zoomedPhoto = screen.getByTestId('zoomed-photo');
    expect(zoomedPhoto).toBeInTheDocument();
    expect(zoomedPhoto).toHaveClass('zoomed');
  });

  test('handles keyboard navigation', async () => {
    const user = userEvent.setup();
    render(
      <PhotoGrid
        photos={mockPhotos}
        onPhotoClick={mockOnPhotoClick}
      />
    );

    const firstPhoto = screen.getByAlt('Beach sunset');
    firstPhoto.focus();

    await user.keyboard('{ArrowRight}');
    expect(document.activeElement).toBe(screen.getByAlt('Mountain view'));

    await user.keyboard('{Enter}');
    expect(mockOnPhotoClick).toHaveBeenCalledWith(mockPhotos[1]);
  });

  test('handles photo download', async () => {
    const user = userEvent.setup();
    const mockDownload = jest.fn();

    render(
      <PhotoGrid
        photos={mockPhotos}
        showDownloadButton={true}
        onDownload={mockDownload}
      />
    );

    const downloadButtons = screen.getAllByLabelText(/download/i);
    await user.click(downloadButtons[0]);

    expect(mockDownload).toHaveBeenCalledWith(mockPhotos[0]);
  });

  test('handles responsive grid columns', () => {
    const { container } = render(
      <PhotoGrid
        photos={mockPhotos}
        responsive={{
          xs: 1,
          sm: 2,
          md: 3,
          lg: 4,
          xl: 5,
        }}
      />
    );

    const gridContainer = container.querySelector('.photo-grid');
    expect(gridContainer).toHaveClass('responsive-grid');
  });

  test('filters photos based on criteria', () => {
    render(
      <PhotoGrid
        photos={mockPhotos}
        filter={{ dateFrom: '2024-01-02', dateTo: '2024-01-03' }}
      />
    );

    expect(screen.queryByAlt('Beach sunset')).not.toBeInTheDocument();
    expect(screen.getByAlt('Mountain view')).toBeInTheDocument();
    expect(screen.getByAlt('City lights')).toBeInTheDocument();
  });

  test('sorts photos by different criteria', () => {
    const { rerender } = render(
      <PhotoGrid photos={mockPhotos} sortBy="name" sortOrder="asc" />
    );

    let images = screen.getAllByRole('img');
    expect(images[0]).toHaveAttribute('alt', 'Beach sunset');

    rerender(
      <PhotoGrid photos={mockPhotos} sortBy="date" sortOrder="desc" />
    );

    images = screen.getAllByRole('img');
    expect(images[0]).toHaveAttribute('alt', 'City lights');
  });
});
