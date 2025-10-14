import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { IndexingStep } from '@/components/OnboardingWizard/IndexingStep';
import { useOnboardingStore } from '@/stores/onboardingStore';
import axios from 'axios';

// Mock axios
jest.mock('axios');

// Mock the store
jest.mock('@/stores/onboardingStore', () => ({
  useOnboardingStore: jest.fn(),
}));

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

// Mock react-router-dom navigate
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

describe('IndexingStep', () => {
  const mockSetIndexingStarted = jest.fn();
  const mockNextStep = jest.fn();
  const mockPrevStep = jest.fn();
  const mockSetCompleted = jest.fn();

  const defaultStore = {
    selectedFolders: ['/path/to/photos', '/another/path'],
    indexingStarted: false,
    setIndexingStarted: mockSetIndexingStarted,
    nextStep: mockNextStep,
    prevStep: mockPrevStep,
    setCompleted: mockSetCompleted,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    (useOnboardingStore as any).mockReturnValue(defaultStore);

    // Default axios mocks
    (axios as any).post = jest.fn().mockResolvedValue({});
    (axios as any).get = jest.fn().mockResolvedValue({
      data: {
        status: 'indexing',
        progress: {
          total_files: 0,
          processed_files: 0,
          current_phase: 'discovery',
        },
        errors: [],
        started_at: '2024-01-01T00:00:00',
        estimated_completion: null,
      },
    });
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe('Rendering', () => {
    test('renders heading and description', () => {
      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      expect(screen.getByText('Setting Up Your Photo Library')).toBeInTheDocument();
      expect(screen.getByText("Sit back and relax - we're making your photos searchable!")).toBeInTheDocument();
    });

    test('automatically starts indexing on mount', async () => {
      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(mockSetIndexingStarted).toHaveBeenCalledWith(true);
        expect((axios as any).post).toHaveBeenCalledWith(
          'http://localhost:5555/config/roots',
          { roots: ['/path/to/photos', '/another/path'] }
        );
        expect((axios as any).post).toHaveBeenCalledWith(
          'http://localhost:5555/index/start',
          { full: true }
        );
      });
    });

    test('shows Back button', () => {
      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      const backButton = screen.getByRole('button', { name: /back/i });
      expect(backButton).toBeInTheDocument();
    });

    test('shows progress indicator when indexing starts', async () => {
      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      // Should show a loading spinner
      await waitFor(() => {
        const loader = document.querySelector('.lucide-loader-circle');
        expect(loader).toBeInTheDocument();
      });
    });

    test('shows fun fact during indexing', async () => {
      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      // Should show one of the fun facts
      await waitFor(() => {
        const funFactElement = screen.getByText(/You'll be able to search for photos by describing what's in them/);
        expect(funFactElement).toBeInTheDocument();
      });
    });

    test('shows Waiting button when not complete', () => {
      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      expect(screen.getByRole('button', { name: /waiting/i })).toBeInTheDocument();
    });
  });

  describe('Indexing Process', () => {
    test('configures roots before starting indexing', async () => {
      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect((axios as any).post).toHaveBeenNthCalledWith(
          1,
          'http://localhost:5555/config/roots',
          { roots: ['/path/to/photos', '/another/path'] }
        );
        expect((axios as any).post).toHaveBeenNthCalledWith(
          2,
          'http://localhost:5555/index/start',
          { full: true }
        );
      });
    });

    test('sets indexingStarted flag when component mounts', async () => {
      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(mockSetIndexingStarted).toHaveBeenCalledWith(true);
      });
    });

    test('shows Starting message initially', async () => {
      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getAllByText('Starting...').length).toBeGreaterThan(0);
      });
    });
  });

  describe('Status Polling', () => {
    test('polls for status after component mounts', async () => {
      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      // Advance timers to trigger polling (polling interval is 2000ms)
      await act(async () => {
        jest.advanceTimersByTime(2000);
      });

      await waitFor(() => {
        expect((axios as any).get).toHaveBeenCalledWith(
          'http://localhost:5555/index/status'
        );
      });
    });

    test('updates progress text with polling data', async () => {
      (axios as any).get.mockResolvedValue({
        data: {
          status: 'indexing',
          progress: {
            total_files: 100,
            processed_files: 50,
            current_phase: 'metadata'
          },
          errors: [],
          started_at: '2024-01-01T00:00:00',
          estimated_completion: null
        },
      });

      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      await act(async () => {
        jest.advanceTimersByTime(2000);
      });

      await waitFor(() => {
        expect(screen.getByText(/50 \/ 100/)).toBeInTheDocument();
        expect(screen.getByText(/photos processed/)).toBeInTheDocument();
      });
    });

    test('shows phase label', async () => {
      (axios as any).get.mockResolvedValue({
        data: {
          status: 'indexing',
          progress: {
            total_files: 100,
            processed_files: 25,
            current_phase: 'scanning'
          },
          errors: [],
          started_at: '2024-01-01T00:00:00',
          estimated_completion: null
        },
      });

      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      await act(async () => {
        jest.advanceTimersByTime(2000);
      });

      await waitFor(() => {
        expect(screen.getAllByText(/Looking through your photos/).length).toBeGreaterThan(0);
      });
    });

    test('shows percentage when total files known', async () => {
      (axios as any).get.mockResolvedValue({
        data: {
          status: 'indexing',
          progress: {
            total_files: 200,
            processed_files: 100,
            current_phase: 'metadata'
          },
          errors: [],
          started_at: '2024-01-01T00:00:00',
          estimated_completion: null
        },
      });

      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      await act(async () => {
        jest.advanceTimersByTime(2000);
      });

      await waitFor(() => {
        expect(screen.getByText('50%')).toBeInTheDocument();
      });
    });

    test('continues polling while indexing', async () => {
      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      // First poll
      await act(async () => {
        jest.advanceTimersByTime(2000);
      });

      // Second poll
      await act(async () => {
        jest.advanceTimersByTime(2000);
      });

      // Third poll
      await act(async () => {
        jest.advanceTimersByTime(2000);
      });

      await waitFor(() => {
        expect((axios as any).get).toHaveBeenCalled();
      });
    });

    test('shows discovery message when total_files is 0', async () => {
      (axios as any).get.mockResolvedValue({
        data: {
          status: 'indexing',
          progress: {
            total_files: 0,
            processed_files: 0,
            current_phase: 'discovery'
          },
          errors: [],
          started_at: '2024-01-01T00:00:00',
          estimated_completion: null
        },
      });

      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      await act(async () => {
        jest.advanceTimersByTime(2000);
      });

      await waitFor(() => {
        expect(screen.getByText(/Discovering photos in your folders/)).toBeInTheDocument();
      });
    });
  });

  describe('Completion Handling', () => {
    test('shows completion message when indexing succeeds', async () => {
      (axios as any).get.mockResolvedValue({
        data: {
          status: 'completed',
          progress: {
            total_files: 150,
            processed_files: 150,
            current_phase: 'completed'
          },
          errors: [],
          started_at: '2024-01-01T00:00:00',
          estimated_completion: null
        },
      });

      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      await act(async () => {
        jest.advanceTimersByTime(2000);
      });

      await waitFor(() => {
        expect(screen.getByText('All done!')).toBeInTheDocument();
      });
    });

    test('shows total photos on completion', async () => {
      (axios as any).get.mockResolvedValue({
        data: {
          status: 'completed',
          progress: {
            total_files: 234,
            processed_files: 234,
            current_phase: 'completed'
          },
          errors: [],
          started_at: '2024-01-01T00:00:00',
          estimated_completion: null
        },
      });

      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      await act(async () => {
        jest.advanceTimersByTime(2000);
      });

      await waitFor(() => {
        expect(screen.getByText(/Found 234 photos/)).toBeInTheDocument();
      });
    });

    test('shows Continue button on completion', async () => {
      (axios as any).get.mockResolvedValue({
        data: {
          status: 'completed',
          progress: {
            total_files: 100,
            processed_files: 100,
            current_phase: 'completed'
          },
          errors: [],
          started_at: '2024-01-01T00:00:00',
          estimated_completion: null
        },
      });

      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      await act(async () => {
        jest.advanceTimersByTime(2000);
      });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /continue/i })).toBeInTheDocument();
      });
    });

    test('calls nextStep when Continue is clicked after completion', async () => {
      const user = userEvent.setup({ delay: null });
      (axios as any).get.mockResolvedValue({
        data: {
          status: 'completed',
          progress: {
            total_files: 100,
            processed_files: 100,
            current_phase: 'completed'
          },
          errors: [],
          started_at: '2024-01-01T00:00:00',
          estimated_completion: null
        },
      });

      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      await act(async () => {
        jest.advanceTimersByTime(2000);
      });

      const continueButton = await screen.findByRole('button', { name: /continue/i });
      await user.click(continueButton);

      expect(mockNextStep).toHaveBeenCalled();
    });

    test('handles idle status with processed files as complete', async () => {
      (axios as any).get.mockResolvedValue({
        data: {
          status: 'idle',
          progress: {
            total_files: 50,
            processed_files: 50,
            current_phase: 'completed'
          },
          errors: [],
          started_at: '2024-01-01T00:00:00',
          estimated_completion: null
        },
      });

      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      await act(async () => {
        jest.advanceTimersByTime(2000);
      });

      await waitFor(() => {
        expect(screen.getByText('All done!')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    test('shows error message when starting indexing fails', async () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation();
      (axios as any).post.mockRejectedValueOnce(new Error('Network error'));

      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Setup failed')).toBeInTheDocument();
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });

      consoleError.mockRestore();
    });

    test('shows retry button when error occurs', async () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation();
      (axios as any).post.mockRejectedValueOnce(new Error('Error'));

      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
      });

      consoleError.mockRestore();
    });

    test('retries indexing when retry button is clicked', async () => {
      const user = userEvent.setup({ delay: null });
      const consoleError = jest.spyOn(console, 'error').mockImplementation();

      // First attempt fails
      (axios as any).post.mockRejectedValueOnce(new Error('Error'));

      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
      });

      // Second attempt succeeds
      (axios as any).post.mockResolvedValue({});

      const retryButton = screen.getByRole('button', { name: /try again/i });
      await user.click(retryButton);

      await waitFor(() => {
        // Should call axios.post again (once for initial, twice for retry - roots + start)
        expect((axios as any).post).toHaveBeenCalledTimes(3);
      });

      consoleError.mockRestore();
    });

    test('shows retry attempts count', async () => {
      const user = userEvent.setup({ delay: null });
      const consoleError = jest.spyOn(console, 'error').mockImplementation();

      (axios as any).post.mockRejectedValue(new Error('Error'));

      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
      });

      const retryButton = screen.getByRole('button', { name: /try again/i });
      await user.click(retryButton);

      await waitFor(() => {
        expect(screen.getByText('Retry attempt 1')).toBeInTheDocument();
      });

      consoleError.mockRestore();
    });

    test('disables retry after 3 attempts', async () => {
      const user = userEvent.setup({ delay: null });
      const consoleError = jest.spyOn(console, 'error').mockImplementation();

      (axios as any).post.mockRejectedValue(new Error('Error'));

      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
      });

      // Click retry 3 times
      await user.click(screen.getByRole('button', { name: /try again/i }));
      await waitFor(() => expect(screen.getByText('Retry attempt 1')).toBeInTheDocument());

      // Find the button again after state update
      await user.click(screen.getByRole('button', { name: /try again \(2 left\)/i }));
      await waitFor(() => expect(screen.getByText('Retry attempt 2')).toBeInTheDocument());

      // Find the button again after state update
      await user.click(screen.getByRole('button', { name: /try again \(1 left\)/i }));
      await waitFor(() => expect(screen.getByText('Retry attempt 3')).toBeInTheDocument());

      // After 3 retries, button should show max retries
      await waitFor(() => {
        expect(screen.getByText('Max retries reached')).toBeInTheDocument();
      });

      consoleError.mockRestore();
    });

    test('handles 409 status (already indexing) gracefully', async () => {
      const error = new Error('Already indexing');
      (error as any).response = { status: 409 };
      (axios as any).post.mockRejectedValueOnce(error);

      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      // Should not show error for 409
      await waitFor(() => {
        expect(mockSetIndexingStarted).toHaveBeenCalled();
      });

      expect(screen.queryByText('Setup failed')).not.toBeInTheDocument();
    });

    test('displays errors from status response', async () => {
      (axios as any).get.mockResolvedValue({
        data: {
          status: 'indexing',
          progress: {
            total_files: 100,
            processed_files: 50,
            current_phase: 'metadata'
          },
          errors: ['Failed to process file.jpg'],
          started_at: '2024-01-01T00:00:00',
          estimated_completion: null
        },
      });

      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      await act(async () => {
        jest.advanceTimersByTime(2000);
      });

      await waitFor(() => {
        expect(screen.getByText('Failed to process file.jpg')).toBeInTheDocument();
      });
    });
  });

  describe('Navigation', () => {
    test('calls prevStep when Back button is clicked', async () => {
      const user = userEvent.setup({ delay: null });
      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      const backButton = screen.getByRole('button', { name: /back/i });
      await user.click(backButton);

      expect(mockPrevStep).toHaveBeenCalled();
    });

    test('disables Back button during indexing', async () => {
      (axios as any).get.mockResolvedValue({
        data: {
          status: 'indexing',
          progress: {
            total_files: 100,
            processed_files: 50,
            current_phase: 'metadata'
          },
          errors: [],
          started_at: '2024-01-01T00:00:00',
          estimated_completion: null
        },
      });

      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      await act(async () => {
        jest.advanceTimersByTime(2000);
      });

      await waitFor(() => {
        const backButton = screen.getByRole('button', { name: /back/i });
        expect(backButton).toBeDisabled();
      });
    });

    test('disables Back button when complete', async () => {
      (axios as any).get.mockResolvedValue({
        data: {
          status: 'completed',
          progress: {
            total_files: 100,
            processed_files: 100,
            current_phase: 'completed'
          },
          errors: [],
          started_at: '2024-01-01T00:00:00',
          estimated_completion: null
        },
      });

      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      await act(async () => {
        jest.advanceTimersByTime(2000);
      });

      await waitFor(() => {
        const backButton = screen.getByRole('button', { name: /back/i });
        expect(backButton).toBeDisabled();
      });
    });

    test('enables Back button when error occurs', async () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation();
      (axios as any).post.mockRejectedValueOnce(new Error('Error'));

      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      await waitFor(() => {
        const backButton = screen.getByRole('button', { name: /back/i });
        expect(backButton).not.toBeDisabled();
      });

      consoleError.mockRestore();
    });
  });

  describe('Background Continue Option', () => {
    test('shows skip option after 5 seconds', async () => {
      (axios as any).get.mockResolvedValue({
        data: {
          status: 'indexing',
          progress: {
            total_files: 100,
            processed_files: 25,
            current_phase: 'metadata'
          },
          errors: [],
          started_at: '2024-01-01T00:00:00',
          estimated_completion: null
        },
      });

      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      // First trigger polling to get status as 'indexing'
      await act(async () => {
        jest.advanceTimersByTime(2000);
      });

      // Then advance time to show skip option
      await act(async () => {
        jest.advanceTimersByTime(5000);
      });

      await waitFor(() => {
        expect(screen.getByText('Skip the wait!')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /skip & start/i })).toBeInTheDocument();
      });
    });

    test('calls setCompleted and navigates when skip is clicked', async () => {
      const user = userEvent.setup({ delay: null });
      (axios as any).get.mockResolvedValue({
        data: {
          status: 'indexing',
          progress: {
            total_files: 100,
            processed_files: 25,
            current_phase: 'metadata'
          },
          errors: [],
          started_at: '2024-01-01T00:00:00',
          estimated_completion: null
        },
      });

      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      // First trigger polling to get status as 'indexing'
      await act(async () => {
        jest.advanceTimersByTime(2000);
      });

      // Then advance time to show skip option
      await act(async () => {
        jest.advanceTimersByTime(5000);
      });

      const skipButton = await screen.findByRole('button', { name: /skip & start/i });
      await user.click(skipButton);

      expect(mockSetCompleted).toHaveBeenCalled();
      expect(mockNavigate).toHaveBeenCalledWith('/');
    });

    test('does not show skip option when complete', async () => {
      (axios as any).get.mockResolvedValue({
        data: {
          status: 'completed',
          progress: {
            total_files: 100,
            processed_files: 100,
            current_phase: 'completed'
          },
          errors: [],
          started_at: '2024-01-01T00:00:00',
          estimated_completion: null
        },
      });

      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      await act(async () => {
        jest.advanceTimersByTime(2000);
      });

      await act(async () => {
        jest.advanceTimersByTime(5000);
      });

      expect(screen.queryByText('Skip the wait!')).not.toBeInTheDocument();
    });
  });

  describe('Fun Facts Rotation', () => {
    test('rotates fun facts every 5 seconds', async () => {
      (axios as any).get.mockResolvedValue({
        data: {
          status: 'indexing',
          progress: {
            total_files: 100,
            processed_files: 25,
            current_phase: 'metadata'
          },
          errors: [],
          started_at: '2024-01-01T00:00:00',
          estimated_completion: null
        },
      });

      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      // Initially shows first fact
      const firstFact = screen.getByText(/You'll be able to search for photos by describing what's in them/);
      expect(firstFact).toBeInTheDocument();

      // Trigger polling to get status as 'indexing' (which starts fact rotation)
      await act(async () => {
        jest.advanceTimersByTime(2000);
      });

      // After 5 more seconds, should show different fact
      await act(async () => {
        jest.advanceTimersByTime(5000);
      });

      await waitFor(() => {
        expect(screen.queryByText(/You'll be able to search for photos by describing what's in them/)).not.toBeInTheDocument();
      });
    });

    test('stops rotating facts when complete', async () => {
      (axios as any).get.mockResolvedValue({
        data: {
          status: 'completed',
          progress: {
            total_files: 100,
            processed_files: 100,
            current_phase: 'completed'
          },
          errors: [],
          started_at: '2024-01-01T00:00:00',
          estimated_completion: null
        },
      });

      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      await act(async () => {
        jest.advanceTimersByTime(2000);
      });

      // Facts should not be visible when complete
      expect(screen.queryByText(/You'll be able to search for photos by describing what's in them/)).not.toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    test('cleans up polling on unmount', async () => {
      const { unmount } = render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      await act(async () => {
        jest.advanceTimersByTime(2000);
      });

      // Clear previous calls
      (axios as any).get.mockClear();

      // Unmount component
      unmount();

      // Advance timer - should not poll after unmount
      await act(async () => {
        jest.advanceTimersByTime(5000);
      });

      expect((axios as any).get).not.toHaveBeenCalled();
    });

    test('handles missing progress data gracefully', async () => {
      (axios as any).get.mockResolvedValue({
        data: {
          status: 'indexing',
          progress: null,
          errors: [],
        },
      });

      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      await act(async () => {
        jest.advanceTimersByTime(2000);
      });

      // Should show starting message (appears in multiple places)
      expect(screen.getAllByText('Starting...').length).toBeGreaterThan(0);
    });

    test('handles zero photos gracefully', async () => {
      (axios as any).get.mockResolvedValue({
        data: {
          status: 'completed',
          progress: {
            total_files: 0,
            processed_files: 0,
            current_phase: 'completed'
          },
          errors: [],
          started_at: '2024-01-01T00:00:00',
          estimated_completion: null
        },
      });

      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      await act(async () => {
        jest.advanceTimersByTime(2000);
      });

      await waitFor(() => {
        expect(screen.getByText('Found 0 photos')).toBeInTheDocument();
      });
    });

    test('handles polling error gracefully', async () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation();
      (axios as any).get.mockRejectedValue(new Error('Polling failed'));

      render(
        <BrowserRouter>
          <IndexingStep />
        </BrowserRouter>
      );

      await act(async () => {
        jest.advanceTimersByTime(2000);
      });

      // Should not crash, just log error
      expect(consoleError).toHaveBeenCalledWith(
        'Failed to poll indexing status:',
        expect.any(Error)
      );

      consoleError.mockRestore();
    });
  });
});
