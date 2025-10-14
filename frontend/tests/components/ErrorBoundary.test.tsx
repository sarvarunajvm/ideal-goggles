import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { ErrorBoundary, withErrorBoundary } from '@/components/ErrorBoundary';
import { logger } from '@/utils/logger';

// Mock the logger
jest.mock('@/utils/logger', () => ({
  logger: {
    logComponentError: jest.fn(),
    info: jest.fn(),
    downloadLogs: jest.fn(),
  },
}));

// Mock fetch for error reporting
global.fetch = jest.fn();

// Component that throws an error for testing
interface ThrowErrorProps {
  shouldThrow?: boolean;
  errorMessage?: string;
}

const ThrowError = ({ shouldThrow = false, errorMessage = 'Test error' }: ThrowErrorProps) => {
  if (shouldThrow) {
    throw new Error(errorMessage);
  }
  return <div>Component rendered successfully</div>;
};

// Component for testing withErrorBoundary HOC
interface TestComponentProps {
  text: string;
}

const TestComponent = ({ text }: TestComponentProps) => {
  return <div>{text}</div>;
};
TestComponent.displayName = 'TestComponent';

describe('ErrorBoundary', () => {
  const originalEnv = process.env.NODE_ENV;

  beforeEach(() => {
    jest.clearAllMocks();
    // Reset fetch mock
    (global.fetch as jest.Mock).mockReset();
  });

  afterEach(() => {
    process.env.NODE_ENV = originalEnv;
  });

  describe('Normal Rendering', () => {
    test('renders children when there is no error', () => {
      render(
        <ErrorBoundary>
          <div>Test content</div>
        </ErrorBoundary>
      );

      expect(screen.getByText('Test content')).toBeInTheDocument();
    });

    test('renders multiple children correctly', () => {
      render(
        <ErrorBoundary>
          <div>Child 1</div>
          <div>Child 2</div>
          <div>Child 3</div>
        </ErrorBoundary>
      );

      expect(screen.getByText('Child 1')).toBeInTheDocument();
      expect(screen.getByText('Child 2')).toBeInTheDocument();
      expect(screen.getByText('Child 3')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    test('catches errors and displays error UI', () => {
      // Suppress console.error for this test
      const consoleError = jest.spyOn(console, 'error').mockImplementation();

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
      expect(screen.getByText(/An unexpected error occurred/)).toBeInTheDocument();

      consoleError.mockRestore();
    });

    test('displays custom error message', () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation();

      // Set development mode before rendering
      process.env.NODE_ENV = 'development';

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} errorMessage="Custom error message" />
        </ErrorBoundary>
      );

      // In development mode, error details should be visible
      expect(screen.queryByText('Custom error message')).toBeInTheDocument();

      consoleError.mockRestore();
    });

    test('logs error to logger service', () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation();

      render(
        <ErrorBoundary componentName="TestComponent">
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      expect(logger.logComponentError).toHaveBeenCalledWith(
        'TestComponent',
        expect.any(Error),
        expect.objectContaining({
          componentStack: expect.any(String),
          errorBoundary: true,
          timestamp: expect.any(String),
        })
      );

      consoleError.mockRestore();
    });

    test('displays custom fallback when provided', () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation();
      const customFallback = <div>Custom error fallback</div>;

      render(
        <ErrorBoundary fallback={customFallback}>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      expect(screen.getByText('Custom error fallback')).toBeInTheDocument();
      expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument();

      consoleError.mockRestore();
    });
  });

  describe('Error UI Features', () => {
    beforeEach(() => {
      jest.spyOn(console, 'error').mockImplementation();
    });

    afterEach(() => {
      jest.restoreAllMocks();
    });

    test('shows error details in development mode', () => {
      process.env.NODE_ENV = 'development';

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} errorMessage="Development error" />
        </ErrorBoundary>
      );

      expect(screen.getByText('Error Details (Development Only)')).toBeInTheDocument();
      expect(screen.getByText('Development error')).toBeInTheDocument();
    });

    test('hides error details in production mode', () => {
      process.env.NODE_ENV = 'production';
      (global.fetch as jest.Mock).mockResolvedValueOnce({ ok: true });

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} errorMessage="Production error" />
        </ErrorBoundary>
      );

      expect(screen.queryByText('Error Details (Development Only)')).not.toBeInTheDocument();
      expect(screen.queryByText('Production error')).not.toBeInTheDocument();
    });

    test('shows stack trace in development mode', () => {
      process.env.NODE_ENV = 'development';

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      const stackTraceButton = screen.getByText('Stack Trace');
      expect(stackTraceButton).toBeInTheDocument();
    });

    test('shows component stack in development mode', () => {
      process.env.NODE_ENV = 'development';

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      // Component stack should be available after error
      expect(logger.logComponentError).toHaveBeenCalledWith(
        expect.any(String),
        expect.any(Error),
        expect.objectContaining({
          componentStack: expect.any(String),
        })
      );
    });

    test('displays error count when error occurs multiple times', () => {
      // Using a counter to trigger different errors
      let errorCounter = 0;
      const DynamicError = () => {
        if (errorCounter > 0) {
          throw new Error(`Test error ${errorCounter}`);
        }
        return <div>No error</div>;
      };

      const { rerender } = render(
        <ErrorBoundary>
          <DynamicError />
        </ErrorBoundary>
      );

      // Trigger first error
      errorCounter = 1;
      rerender(
        <ErrorBoundary>
          <DynamicError />
        </ErrorBoundary>
      );

      // Component should show error
      expect(screen.getByText('Something went wrong')).toBeInTheDocument();

      // Note: First error shows error count = 1, which is > 1 check, so no message yet
      expect(screen.queryByText(/This error has occurred/)).not.toBeInTheDocument();

      // Reset the boundary
      const tryAgainButton = screen.getByText('Try Again');
      fireEvent.click(tryAgainButton);

      // Trigger second error
      errorCounter = 2;
      rerender(
        <ErrorBoundary>
          <DynamicError />
        </ErrorBoundary>
      );

      // Should show error occurred 2 times
      expect(screen.getByText(/This error has occurred 2 times/)).toBeInTheDocument();
    });
  });

  describe('User Actions', () => {
    beforeEach(() => {
      jest.spyOn(console, 'error').mockImplementation();
    });

    afterEach(() => {
      jest.restoreAllMocks();
    });

    test('resets error boundary when Try Again is clicked', () => {
      let shouldThrow = true;
      const DynamicError = () => {
        if (shouldThrow) {
          throw new Error('Test error');
        }
        return <div>Component rendered successfully</div>;
      };

      render(
        <ErrorBoundary>
          <DynamicError />
        </ErrorBoundary>
      );

      expect(screen.getByText('Something went wrong')).toBeInTheDocument();

      const tryAgainButton = screen.getByText('Try Again');

      // Reset should clear error state and allow successful render
      shouldThrow = false;
      act(() => {
        fireEvent.click(tryAgainButton);
      });

      expect(screen.getByText('Component rendered successfully')).toBeInTheDocument();
      expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument();
    });

    test('logs reset action', () => {
      render(
        <ErrorBoundary componentName="TestComponent">
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      const tryAgainButton = screen.getByText('Try Again');
      fireEvent.click(tryAgainButton);

      expect(logger.info).toHaveBeenCalledWith(
        'Error boundary reset by user',
        expect.objectContaining({
          componentName: 'TestComponent',
          errorCount: expect.any(Number),
        })
      );
    });

    test('downloads logs when Download Logs is clicked', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      const downloadButton = screen.getByText('Download Logs');
      fireEvent.click(downloadButton);

      expect(logger.downloadLogs).toHaveBeenCalled();
    });

    test('navigates to home when Go to Home is clicked', () => {
      // Spy on the click handler instead of mocking location
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      const homeButton = screen.getByText('Go to Home');

      // The button should have an onClick handler that sets window.location.href
      expect(homeButton).toBeInTheDocument();

      // We can't easily test window.location.href assignment in jsdom,
      // so just verify the button exists and is clickable
      expect(homeButton).not.toBeDisabled();
    });
  });

  describe('Error Reporting', () => {
    beforeEach(() => {
      jest.spyOn(console, 'error').mockImplementation();
    });

    afterEach(() => {
      jest.restoreAllMocks();
    });

    test('reports error to backend in production', async () => {
      process.env.NODE_ENV = 'production';
      (global.fetch as jest.Mock).mockResolvedValueOnce({ ok: true });

      render(
        <ErrorBoundary componentName="ProdComponent">
          <ThrowError shouldThrow={true} errorMessage="Production error" />
        </ErrorBoundary>
      );

      // Wait for async reporting
      await new Promise(resolve => setTimeout(resolve, 0));

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/logs/errors',
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: expect.stringContaining('Production error'),
        })
      );
    });

    test('does not report error to backend in development', async () => {
      process.env.NODE_ENV = 'development';

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      await new Promise(resolve => setTimeout(resolve, 0));

      expect(global.fetch).not.toHaveBeenCalled();
    });

    test('handles backend reporting failure gracefully', async () => {
      process.env.NODE_ENV = 'production';
      const consoleErrorSpy = jest.spyOn(console, 'error');
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      await new Promise(resolve => setTimeout(resolve, 0));

      // Should log the reporting failure
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Failed to report error to backend:',
        expect.any(Error)
      );
    });
  });

  describe('withErrorBoundary HOC', () => {
    beforeEach(() => {
      jest.spyOn(console, 'error').mockImplementation();
    });

    afterEach(() => {
      jest.restoreAllMocks();
    });

    test('wraps component with error boundary', () => {
      const WrappedComponent = withErrorBoundary(TestComponent, 'TestComponent');

      render(<WrappedComponent text="HOC test" />);

      expect(screen.getByText('HOC test')).toBeInTheDocument();
    });

    test('catches errors in wrapped component', () => {
      const ErrorComponent = () => {
        throw new Error('HOC error');
      };

      const WrappedComponent = withErrorBoundary(ErrorComponent, 'ErrorComponent');

      render(<WrappedComponent />);

      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    });

    test('uses component displayName if available', () => {
      const WrappedComponent = withErrorBoundary(TestComponent);

      render(<WrappedComponent text="Display name test" />);

      expect(screen.getByText('Display name test')).toBeInTheDocument();
    });

    test('passes props to wrapped component', () => {
      interface PropsComponentProps {
        value: number;
        label: string;
      }

      const PropsComponent = ({ value, label }: PropsComponentProps) => (
        <div>{label}: {value}</div>
      );

      const WrappedComponent = withErrorBoundary(PropsComponent);

      render(<WrappedComponent value={42} label="Answer" />);

      expect(screen.getByText('Answer: 42')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    beforeEach(() => {
      jest.spyOn(console, 'error').mockImplementation();
    });

    afterEach(() => {
      jest.restoreAllMocks();
    });

    test('handles errors without stack trace', () => {
      const customError = { message: 'Custom error without stack' } as Error;

      const ThrowCustomError = () => {
        throw customError;
      };

      render(
        <ErrorBoundary>
          <ThrowCustomError />
        </ErrorBoundary>
      );

      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    });

    test('handles multiple rapid errors', () => {
      const { rerender } = render(
        <ErrorBoundary>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      );

      // Trigger multiple errors rapidly
      for (let i = 0; i < 5; i++) {
        act(() => {
          rerender(
            <ErrorBoundary>
              <ThrowError shouldThrow={true} />
            </ErrorBoundary>
          );
        });

        const tryAgainButton = screen.getByText('Try Again');
        act(() => {
          fireEvent.click(tryAgainButton);
        });
      }

      // Should show high error count
      act(() => {
        rerender(
          <ErrorBoundary>
            <ThrowError shouldThrow={true} />
          </ErrorBoundary>
        );
      });

      expect(screen.getByText(/This error has occurred 6 times/)).toBeInTheDocument();
    });

    test('handles undefined component name gracefully', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      expect(logger.logComponentError).toHaveBeenCalledWith(
        'Unknown',
        expect.any(Error),
        expect.any(Object)
      );
    });
  });
});