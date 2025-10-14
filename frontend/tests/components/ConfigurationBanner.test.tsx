import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import ConfigurationBanner from '@/components/ConfigurationBanner';
import { apiService } from '@/services/apiClient';

// Mock the API service
jest.mock('@/services/apiClient', () => ({
  apiService: {
    getConfig: jest.fn(),
  },
}));

const mockGetConfig = apiService.getConfig as jest.Mock;

describe('ConfigurationBanner', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    // Clear sessionStorage before each test
    sessionStorage.clear();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe('Rendering', () => {
    test('shows banner when no folders are configured', async () => {
      mockGetConfig.mockResolvedValue({
        roots: [],
      });

      render(
        <BrowserRouter>
          <ConfigurationBanner />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('No photo folders configured')).toBeInTheDocument();
        expect(
          screen.getByText('Add your photo folders to start searching and organizing your photos')
        ).toBeInTheDocument();
      });
    });

    test('does not show banner when folders are configured', async () => {
      mockGetConfig.mockResolvedValue({
        roots: ['/path/to/photos'],
      });

      render(
        <BrowserRouter>
          <ConfigurationBanner />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.queryByText('No photo folders configured')).not.toBeInTheDocument();
      });
    });

    test('does not show banner when previously dismissed', async () => {
      sessionStorage.setItem('config-banner-dismissed', 'true');

      mockGetConfig.mockResolvedValue({
        roots: [],
      });

      render(
        <BrowserRouter>
          <ConfigurationBanner />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.queryByText('No photo folders configured')).not.toBeInTheDocument();
      });
    });

    test('renders folder icon', async () => {
      mockGetConfig.mockResolvedValue({
        roots: [],
      });

      render(
        <BrowserRouter>
          <ConfigurationBanner />
        </BrowserRouter>
      );

      await waitFor(() => {
        const folderIcon = document.querySelector('.lucide-folder-open');
        expect(folderIcon).toBeInTheDocument();
      });
    });

    test('renders Go to Settings button with correct link', async () => {
      mockGetConfig.mockResolvedValue({
        roots: [],
      });

      render(
        <BrowserRouter>
          <ConfigurationBanner />
        </BrowserRouter>
      );

      await waitFor(() => {
        const settingsButton = screen.getByRole('button', { name: /go to settings/i });
        expect(settingsButton).toBeInTheDocument();

        // Check that it's wrapped in a Link to /settings
        const link = settingsButton.closest('a');
        expect(link).toHaveAttribute('href', '/settings');
      });
    });

    test('renders dismiss button', async () => {
      mockGetConfig.mockResolvedValue({
        roots: [],
      });

      render(
        <BrowserRouter>
          <ConfigurationBanner />
        </BrowserRouter>
      );

      await waitFor(() => {
        const dismissButton = screen.getByRole('button', { name: /dismiss banner/i });
        expect(dismissButton).toBeInTheDocument();
      });
    });
  });

  describe('Interactions', () => {
    test('dismisses banner when dismiss button is clicked', async () => {
      mockGetConfig.mockResolvedValue({
        roots: [],
      });

      render(
        <BrowserRouter>
          <ConfigurationBanner />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('No photo folders configured')).toBeInTheDocument();
      });

      const dismissButton = screen.getByRole('button', { name: /dismiss banner/i });
      fireEvent.click(dismissButton);

      await waitFor(() => {
        expect(screen.queryByText('No photo folders configured')).not.toBeInTheDocument();
      });

      // Check that dismissal is saved to sessionStorage
      expect(sessionStorage.getItem('config-banner-dismissed')).toBe('true');
    });

    test('banner stays hidden after dismissal even if config is rechecked', async () => {
      mockGetConfig.mockResolvedValue({
        roots: [],
      });

      const { rerender } = render(
        <BrowserRouter>
          <ConfigurationBanner />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('No photo folders configured')).toBeInTheDocument();
      });

      // Dismiss the banner
      const dismissButton = screen.getByRole('button', { name: /dismiss banner/i });
      fireEvent.click(dismissButton);

      await waitFor(() => {
        expect(screen.queryByText('No photo folders configured')).not.toBeInTheDocument();
      });

      // Simulate interval check
      jest.advanceTimersByTime(30000);

      // Rerender to ensure banner stays hidden
      rerender(
        <BrowserRouter>
          <ConfigurationBanner />
        </BrowserRouter>
      );

      expect(screen.queryByText('No photo folders configured')).not.toBeInTheDocument();
    });
  });

  describe('API Integration', () => {
    test('handles API errors gracefully', async () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation();
      mockGetConfig.mockRejectedValue(new Error('API error'));

      render(
        <BrowserRouter>
          <ConfigurationBanner />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(consoleError).toHaveBeenCalledWith(
          'Failed to check configuration:',
          expect.any(Error)
        );
      });

      // Banner should not show on error
      expect(screen.queryByText('No photo folders configured')).not.toBeInTheDocument();

      consoleError.mockRestore();
    });

    test('rechecks configuration every 30 seconds', async () => {
      mockGetConfig
        .mockResolvedValueOnce({ roots: [] })
        .mockResolvedValueOnce({ roots: ['/new/folder'] });

      render(
        <BrowserRouter>
          <ConfigurationBanner />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('No photo folders configured')).toBeInTheDocument();
      });

      expect(apiService.getConfig).toHaveBeenCalledTimes(1);

      // Advance timer by 30 seconds
      jest.advanceTimersByTime(30000);

      await waitFor(() => {
        expect(apiService.getConfig).toHaveBeenCalledTimes(2);
      });

      // Banner should hide after folders are added
      await waitFor(() => {
        expect(screen.queryByText('No photo folders configured')).not.toBeInTheDocument();
      });
    });

    test('cleans up interval on unmount', async () => {
      mockGetConfig.mockResolvedValue({ roots: [] });

      const { unmount } = render(
        <BrowserRouter>
          <ConfigurationBanner />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(apiService.getConfig).toHaveBeenCalledTimes(1);
      });

      unmount();

      // Advance timer and verify no additional calls
      jest.advanceTimersByTime(30000);
      expect(apiService.getConfig).toHaveBeenCalledTimes(1);
    });
  });

  describe('Edge Cases', () => {
    test('handles empty config response', async () => {
      mockGetConfig.mockResolvedValue({});

      render(
        <BrowserRouter>
          <ConfigurationBanner />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('No photo folders configured')).toBeInTheDocument();
      });
    });

    test('handles null roots in config', async () => {
      mockGetConfig.mockResolvedValue({
        roots: null,
      });

      render(
        <BrowserRouter>
          <ConfigurationBanner />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('No photo folders configured')).toBeInTheDocument();
      });
    });

    test('handles undefined roots in config', async () => {
      mockGetConfig.mockResolvedValue({
        roots: undefined,
      });

      render(
        <BrowserRouter>
          <ConfigurationBanner />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('No photo folders configured')).toBeInTheDocument();
      });
    });
  });
});