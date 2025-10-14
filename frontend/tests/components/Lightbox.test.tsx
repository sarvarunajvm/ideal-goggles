import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Lightbox } from '@/components/Lightbox/Lightbox';
import { useLightboxStore } from '@/stores/lightboxStore';
import type { Photo } from '@/types';

// Mock child components
jest.mock('@/components/Lightbox/LightboxImage', () => ({
  LightboxImage: ({ photo }: { photo: Photo }) => (
    <div data-testid="lightbox-image">{photo.filename}</div>
  ),
}));

jest.mock('@/components/Lightbox/LightboxNavigation', () => ({
  LightboxNavigation: () => <div data-testid="lightbox-navigation">Navigation</div>,
}));

jest.mock('@/components/Lightbox/LightboxMetadata', () => ({
  LightboxMetadata: ({ photo }: { photo: Photo }) => (
    <div data-testid="lightbox-metadata">{photo.filename} metadata</div>
  ),
}));

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, onClick, className }: any) => (
      <div onClick={onClick} className={className}>
        {children}
      </div>
    ),
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

const mockPhotos: Photo[] = [
  {
    id: '1',
    filename: 'photo1.jpg',
    filepath: '/path/to/photo1.jpg',
    thumbnail: '/thumb/photo1.jpg',
    width: 800,
    height: 600,
    date_taken: '2024-01-01',
    file_size: 1024000,
    tags: [],
    people: [],
    location: null,
    camera_make: 'Canon',
    camera_model: 'EOS R5',
    iso: 100,
    aperture: 2.8,
    shutter_speed: '1/1000',
    focal_length: 50,
  },
  {
    id: '2',
    filename: 'photo2.jpg',
    filepath: '/path/to/photo2.jpg',
    thumbnail: '/thumb/photo2.jpg',
    width: 1920,
    height: 1080,
    date_taken: '2024-01-02',
    file_size: 2048000,
    tags: [],
    people: [],
    location: null,
    camera_make: 'Sony',
    camera_model: 'A7III',
    iso: 200,
    aperture: 1.8,
    shutter_speed: '1/500',
    focal_length: 85,
  },
  {
    id: '3',
    filename: 'photo3.jpg',
    filepath: '/path/to/photo3.jpg',
    thumbnail: '/thumb/photo3.jpg',
    width: 1600,
    height: 1200,
    date_taken: '2024-01-03',
    file_size: 1536000,
    tags: [],
    people: [],
    location: null,
    camera_make: 'Nikon',
    camera_model: 'D850',
    iso: 400,
    aperture: 4.0,
    shutter_speed: '1/250',
    focal_length: 24,
  },
];

describe('Lightbox', () => {
  beforeEach(() => {
    // Reset store before each test
    useLightboxStore.setState({
      isOpen: false,
      photos: [],
      currentIndex: 0,
    });
    // Reset body overflow
    document.body.style.overflow = '';
  });

  afterEach(() => {
    // Clean up body overflow
    document.body.style.overflow = '';
  });

  describe('Rendering', () => {
    it('should not render when lightbox is closed', () => {
      render(<Lightbox />);
      expect(screen.queryByRole('button', { name: /close lightbox/i })).not.toBeInTheDocument();
    });

    it('should render when lightbox is open', () => {
      useLightboxStore.getState().openLightbox(mockPhotos, 0);
      render(<Lightbox />);
      expect(screen.getByRole('button', { name: /close lightbox/i })).toBeInTheDocument();
    });

    it('should render the current photo', () => {
      useLightboxStore.getState().openLightbox(mockPhotos, 0);
      render(<Lightbox />);
      expect(screen.getByTestId('lightbox-image')).toHaveTextContent('photo1.jpg');
    });

    it('should render navigation controls', () => {
      useLightboxStore.getState().openLightbox(mockPhotos, 0);
      render(<Lightbox />);
      expect(screen.getByTestId('lightbox-navigation')).toBeInTheDocument();
    });

    it('should render metadata sidebar', () => {
      useLightboxStore.getState().openLightbox(mockPhotos, 0);
      render(<Lightbox />);
      expect(screen.getByTestId('lightbox-metadata')).toBeInTheDocument();
    });

    it('should render photo counter', () => {
      useLightboxStore.getState().openLightbox(mockPhotos, 0);
      render(<Lightbox />);
      expect(screen.getByText('1 / 3')).toBeInTheDocument();
    });

    it('should render correct photo counter for second photo', () => {
      useLightboxStore.getState().openLightbox(mockPhotos, 1);
      render(<Lightbox />);
      expect(screen.getByText('2 / 3')).toBeInTheDocument();
    });

    it('should render close button', () => {
      useLightboxStore.getState().openLightbox(mockPhotos, 0);
      render(<Lightbox />);
      const closeButton = screen.getByRole('button', { name: /close lightbox/i });
      expect(closeButton).toBeInTheDocument();
      expect(closeButton).toHaveClass('lightbox-close-btn');
    });
  });

  describe('Keyboard Navigation', () => {
    it('should close lightbox on Escape key', () => {
      useLightboxStore.getState().openLightbox(mockPhotos, 0);
      render(<Lightbox />);

      fireEvent.keyDown(window, { key: 'Escape' });

      expect(useLightboxStore.getState().isOpen).toBe(false);
    });

    it('should navigate to next photo on ArrowRight key', () => {
      useLightboxStore.getState().openLightbox(mockPhotos, 0);
      render(<Lightbox />);

      fireEvent.keyDown(window, { key: 'ArrowRight' });

      expect(useLightboxStore.getState().currentIndex).toBe(1);
    });

    it('should navigate to previous photo on ArrowLeft key', () => {
      useLightboxStore.getState().openLightbox(mockPhotos, 1);
      render(<Lightbox />);

      fireEvent.keyDown(window, { key: 'ArrowLeft' });

      expect(useLightboxStore.getState().currentIndex).toBe(0);
    });

    it('should not respond to keyboard when lightbox is closed', () => {
      render(<Lightbox />);

      fireEvent.keyDown(window, { key: 'Escape' });
      fireEvent.keyDown(window, { key: 'ArrowRight' });
      fireEvent.keyDown(window, { key: 'ArrowLeft' });

      // Should not throw errors
      expect(useLightboxStore.getState().isOpen).toBe(false);
    });

    it('should ignore other keyboard keys', () => {
      useLightboxStore.getState().openLightbox(mockPhotos, 1);
      render(<Lightbox />);

      const initialState = useLightboxStore.getState();

      fireEvent.keyDown(window, { key: 'a' });
      fireEvent.keyDown(window, { key: 'Enter' });
      fireEvent.keyDown(window, { key: 'Space' });

      expect(useLightboxStore.getState().isOpen).toBe(initialState.isOpen);
      expect(useLightboxStore.getState().currentIndex).toBe(initialState.currentIndex);
    });

    it('should clean up keyboard listeners when component unmounts', () => {
      useLightboxStore.getState().openLightbox(mockPhotos, 0);
      const { unmount } = render(<Lightbox />);

      unmount();

      // Keyboard events should not affect the store after unmount
      const beforeState = useLightboxStore.getState();
      fireEvent.keyDown(window, { key: 'Escape' });

      expect(useLightboxStore.getState()).toEqual(beforeState);
    });

    it('should clean up keyboard listeners when lightbox closes', () => {
      useLightboxStore.getState().openLightbox(mockPhotos, 0);
      const { rerender } = render(<Lightbox />);

      useLightboxStore.getState().closeLightbox();
      rerender(<Lightbox />);

      // Verify listeners are cleaned up by checking no errors occur
      fireEvent.keyDown(window, { key: 'ArrowRight' });
      expect(useLightboxStore.getState().currentIndex).toBe(0);
    });
  });

  describe('Mouse Interactions', () => {
    it('should close lightbox when clicking on backdrop', () => {
      useLightboxStore.getState().openLightbox(mockPhotos, 0);
      const { container } = render(<Lightbox />);

      const backdrop = container.firstChild as HTMLElement;
      fireEvent.click(backdrop);

      expect(useLightboxStore.getState().isOpen).toBe(false);
    });

    it('should not close lightbox when clicking on content area', () => {
      useLightboxStore.getState().openLightbox(mockPhotos, 0);
      render(<Lightbox />);

      const navigation = screen.getByTestId('lightbox-navigation');
      fireEvent.click(navigation);

      expect(useLightboxStore.getState().isOpen).toBe(true);
    });

    it('should close lightbox when clicking close button', () => {
      useLightboxStore.getState().openLightbox(mockPhotos, 0);
      render(<Lightbox />);

      const closeButton = screen.getByRole('button', { name: /close lightbox/i });
      fireEvent.click(closeButton);

      expect(useLightboxStore.getState().isOpen).toBe(false);
    });
  });

  describe('Body Scroll Management', () => {
    it('should prevent body scroll when lightbox opens', () => {
      useLightboxStore.getState().openLightbox(mockPhotos, 0);
      render(<Lightbox />);

      expect(document.body.style.overflow).toBe('hidden');
    });

    it('should restore body scroll when lightbox closes', async () => {
      useLightboxStore.getState().openLightbox(mockPhotos, 0);
      const { rerender } = render(<Lightbox />);

      useLightboxStore.getState().closeLightbox();
      rerender(<Lightbox />);

      await waitFor(() => {
        expect(document.body.style.overflow).toBe('');
      });
    });

    it('should restore body scroll on unmount', () => {
      useLightboxStore.getState().openLightbox(mockPhotos, 0);
      const { unmount } = render(<Lightbox />);

      expect(document.body.style.overflow).toBe('hidden');

      unmount();

      expect(document.body.style.overflow).toBe('');
    });

    it('should handle body scroll when lightbox was never opened', () => {
      const { unmount } = render(<Lightbox />);

      expect(document.body.style.overflow).toBe('');

      unmount();

      expect(document.body.style.overflow).toBe('');
    });
  });

  describe('Photo Navigation', () => {
    it('should display the correct photo when index changes', () => {
      useLightboxStore.getState().openLightbox(mockPhotos, 0);
      const { rerender } = render(<Lightbox />);

      expect(screen.getByTestId('lightbox-image')).toHaveTextContent('photo1.jpg');

      useLightboxStore.getState().nextPhoto();
      rerender(<Lightbox />);

      expect(screen.getByTestId('lightbox-image')).toHaveTextContent('photo2.jpg');
    });

    it('should update metadata when photo changes', () => {
      useLightboxStore.getState().openLightbox(mockPhotos, 0);
      const { rerender } = render(<Lightbox />);

      expect(screen.getByTestId('lightbox-metadata')).toHaveTextContent('photo1.jpg metadata');

      useLightboxStore.getState().nextPhoto();
      rerender(<Lightbox />);

      expect(screen.getByTestId('lightbox-metadata')).toHaveTextContent('photo2.jpg metadata');
    });

    it('should update photo counter when navigating', () => {
      useLightboxStore.getState().openLightbox(mockPhotos, 0);
      const { rerender } = render(<Lightbox />);

      expect(screen.getByText('1 / 3')).toBeInTheDocument();

      useLightboxStore.getState().nextPhoto();
      rerender(<Lightbox />);

      expect(screen.getByText('2 / 3')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty photo array gracefully', () => {
      useLightboxStore.setState({
        isOpen: true,
        photos: [],
        currentIndex: 0,
      });

      render(<Lightbox />);

      expect(screen.queryByTestId('lightbox-image')).not.toBeInTheDocument();
      expect(screen.queryByTestId('lightbox-metadata')).not.toBeInTheDocument();
      expect(screen.getByText('1 / 0')).toBeInTheDocument();
    });

    it('should handle single photo', () => {
      useLightboxStore.getState().openLightbox([mockPhotos[0]], 0);
      render(<Lightbox />);

      expect(screen.getByText('1 / 1')).toBeInTheDocument();
      expect(screen.getByTestId('lightbox-image')).toHaveTextContent('photo1.jpg');
    });

    it('should render correctly with last photo in array', () => {
      useLightboxStore.getState().openLightbox(mockPhotos, 2);
      render(<Lightbox />);

      expect(screen.getByText('3 / 3')).toBeInTheDocument();
      expect(screen.getByTestId('lightbox-image')).toHaveTextContent('photo3.jpg');
    });
  });
});
