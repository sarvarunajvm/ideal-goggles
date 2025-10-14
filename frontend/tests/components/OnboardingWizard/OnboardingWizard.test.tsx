import { render, screen, act } from '@testing-library/react';
import { OnboardingWizard } from '@/components/OnboardingWizard/OnboardingWizard';
import { useOnboardingStore } from '@/stores/onboardingStore';

// Mock the store
jest.mock('@/stores/onboardingStore', () => ({
  useOnboardingStore: jest.fn(),
}));

// Mock child components
jest.mock('@/components/OnboardingWizard/WelcomeStep', () => ({
  WelcomeStep: () => <div data-testid="welcome-step">Welcome Step</div>,
}));

jest.mock('@/components/OnboardingWizard/FolderSelectionStep', () => ({
  FolderSelectionStep: () => <div data-testid="folder-step">Folder Selection Step</div>,
}));

jest.mock('@/components/OnboardingWizard/IndexingStep', () => ({
  IndexingStep: () => <div data-testid="indexing-step">Indexing Step</div>,
}));

jest.mock('@/components/OnboardingWizard/CompleteStep', () => ({
  CompleteStep: () => <div data-testid="complete-step">Complete Step</div>,
}));

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

describe('OnboardingWizard', () => {
  const mockStoreMethods = {
    nextStep: jest.fn(),
    prevStep: jest.fn(),
    setStep: jest.fn(),
    setCompleted: jest.fn(),
    addFolder: jest.fn(),
    removeFolder: jest.fn(),
    setIndexingStarted: jest.fn(),
    reset: jest.fn(),
  };

  const defaultState = {
    currentStep: 0,
    completed: false,
    selectedFolders: [],
    indexingStarted: false,
    ...mockStoreMethods,
  };

  beforeEach(() => {
    jest.clearAllMocks();

    // Mock the store with default state
    (useOnboardingStore as any).mockReturnValue(defaultState);
  });

  afterEach(() => {
    // Clean up body style changes
    document.body.style.overflow = '';
    (document.body.style as any).touchAction = '';
  });

  describe('Rendering', () => {
    test('renders wizard when not completed', () => {
      render(<OnboardingWizard />);

      // Check for progress indicator
      expect(screen.getByText('Step 1 of 4')).toBeInTheDocument();

      // Check that initial step is rendered
      expect(screen.getByTestId('welcome-step')).toBeInTheDocument();
    });

    test('does not render when onboarding is completed', () => {
      (useOnboardingStore as any).mockReturnValue({
        ...defaultState,
        completed: true,
      });

      const { container } = render(<OnboardingWizard />);
      expect(container.firstChild).toBeNull();
    });

    test('renders progress indicator with correct steps', () => {
      render(<OnboardingWizard />);

      // Check for all step numbers
      expect(screen.getByText('1')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();
      expect(screen.getByText('4')).toBeInTheDocument();
    });

    test('highlights current step in progress indicator', () => {
      (useOnboardingStore as any).mockReturnValue({
        ...defaultState,
        currentStep: 2,
      });

      render(<OnboardingWizard />);

      // The step indicator text
      expect(screen.getByText('Step 3 of 4')).toBeInTheDocument();
    });
  });

  describe('Step Navigation', () => {
    test('renders WelcomeStep when currentStep is 0', () => {
      render(<OnboardingWizard />);
      expect(screen.getByTestId('welcome-step')).toBeInTheDocument();
    });

    test('renders FolderSelectionStep when currentStep is 1', () => {
      (useOnboardingStore as any).mockReturnValue({
        ...defaultState,
        currentStep: 1,
      });

      render(<OnboardingWizard />);
      expect(screen.getByTestId('folder-step')).toBeInTheDocument();
    });

    test('renders IndexingStep when currentStep is 2', () => {
      (useOnboardingStore as any).mockReturnValue({
        ...defaultState,
        currentStep: 2,
      });

      render(<OnboardingWizard />);
      expect(screen.getByTestId('indexing-step')).toBeInTheDocument();
    });

    test('renders CompleteStep when currentStep is 3', () => {
      (useOnboardingStore as any).mockReturnValue({
        ...defaultState,
        currentStep: 3,
      });

      render(<OnboardingWizard />);
      expect(screen.getByTestId('complete-step')).toBeInTheDocument();
    });

    test('renders WelcomeStep for invalid step number', () => {
      (useOnboardingStore as any).mockReturnValue({
        ...defaultState,
        currentStep: 99,
      });

      render(<OnboardingWizard />);
      expect(screen.getByTestId('welcome-step')).toBeInTheDocument();
    });
  });

  describe('Body Scroll Management', () => {
    test('disables body scroll when mounted', () => {
      render(<OnboardingWizard />);

      expect(document.body.style.overflow).toBe('hidden');
      expect((document.body.style as any).touchAction).toBe('none');
    });

    test('restores body scroll when unmounted', () => {
      const originalOverflow = 'auto';
      const originalTouchAction = 'pan-y';
      document.body.style.overflow = originalOverflow;
      (document.body.style as any).touchAction = originalTouchAction;

      const { unmount } = render(<OnboardingWizard />);

      // Check it was changed
      expect(document.body.style.overflow).toBe('hidden');

      // Unmount and check restoration
      unmount();
      expect(document.body.style.overflow).toBe(originalOverflow);
      expect((document.body.style as any).touchAction).toBe(originalTouchAction);
    });

    test('handles missing original touchAction', () => {
      document.body.style.overflow = '';
      delete (document.body.style as any).touchAction;

      const { unmount } = render(<OnboardingWizard />);
      unmount();

      expect((document.body.style as any).touchAction).toBe('');
    });
  });

  describe('Visual Layout', () => {
    test('renders with correct container classes', () => {
      const { container } = render(<OnboardingWizard />);

      const wrapper = container.firstChild as HTMLElement;
      expect(wrapper).toHaveClass('fixed', 'inset-0', 'z-50');
    });

    test('renders card container with correct styling', () => {
      const { container } = render(<OnboardingWizard />);

      const card = container.querySelector('.max-w-3xl');
      expect(card).toBeInTheDocument();
      expect(card).toHaveClass('rounded-lg', 'bg-card');
    });

    test('renders progress connectors between steps', () => {
      render(<OnboardingWizard />);

      // There should be 3 connectors for 4 steps
      const connectors = document.querySelectorAll('.h-1.w-16');
      expect(connectors).toHaveLength(3);
    });

    test('applies active styling to completed step indicators', () => {
      (useOnboardingStore as any).mockReturnValue({
        ...defaultState,
        currentStep: 2,
      });

      render(<OnboardingWizard />);

      // Check that steps 1 and 2 have active styling (0-indexed, so steps 0, 1, 2)
      const stepIndicators = document.querySelectorAll('.bg-primary');
      // This includes both the circles and connectors
      expect(stepIndicators.length).toBeGreaterThan(0);
    });
  });

  describe('Edge Cases', () => {
    test('handles negative step number gracefully', () => {
      (useOnboardingStore as any).mockReturnValue({
        ...defaultState,
        currentStep: -1,
      });

      render(<OnboardingWizard />);
      // Should default to WelcomeStep
      expect(screen.getByTestId('welcome-step')).toBeInTheDocument();
    });

    test('updates when store state changes', () => {
      const { rerender } = render(<OnboardingWizard />);
      expect(screen.getByTestId('welcome-step')).toBeInTheDocument();

      // Update the mock to return different state
      (useOnboardingStore as any).mockReturnValue({
        ...defaultState,
        currentStep: 1,
      });

      rerender(<OnboardingWizard />);
      expect(screen.getByTestId('folder-step')).toBeInTheDocument();
    });

    test('handles rapid step changes', () => {
      const { rerender } = render(<OnboardingWizard />);

      // Rapidly change steps
      for (let i = 0; i < 4; i++) {
        act(() => {
          (useOnboardingStore as any).mockReturnValue({
            ...defaultState,
            currentStep: i,
          });
        });
        rerender(<OnboardingWizard />);
      }

      // Should end on the last step
      expect(screen.getByTestId('complete-step')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    test('progress indicators have proper structure', () => {
      render(<OnboardingWizard />);

      // Check that step numbers are present and readable
      const stepNumbers = ['1', '2', '3', '4'];
      stepNumbers.forEach(num => {
        expect(screen.getByText(num)).toBeInTheDocument();
      });
    });

    test('current step is indicated in text', () => {
      (useOnboardingStore as any).mockReturnValue({
        ...defaultState,
        currentStep: 1,
      });

      render(<OnboardingWizard />);
      expect(screen.getByText('Step 2 of 4')).toBeInTheDocument();
    });
  });
});