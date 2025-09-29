import React, { Component, ErrorInfo, ReactNode } from 'react';
import { logger } from '../utils/logger';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { AlertCircle } from 'lucide-react';

interface Props {
  children: ReactNode;
  componentName?: string;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
  errorCount: number;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      errorCount: 0,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error,
      errorCount: 0,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    const { componentName = 'Unknown' } = this.props;

    // Log the error to our logging service
    logger.logComponentError(componentName, error, {
      componentStack: errorInfo.componentStack,
      errorBoundary: true,
      timestamp: new Date().toISOString(),
    });

    // Update state with error details
    this.setState(prevState => ({
      error,
      errorInfo,
      errorCount: prevState.errorCount + 1,
    }));

    // Send error to backend for monitoring (in production)
    if (process.env.NODE_ENV === 'production') {
      this.reportErrorToBackend(error, errorInfo);
    }
  }

  private reportErrorToBackend(error: Error, errorInfo: ErrorInfo): void {
    // Send error details to backend
    fetch('/api/logs/errors', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        componentName: this.props.componentName,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href,
      }),
    }).catch(err => {
      // Silently fail to avoid infinite loop
      console.error('Failed to report error to backend:', err);
    });
  }

  handleReset = (): void => {
    logger.info('Error boundary reset by user', {
      componentName: this.props.componentName,
      errorCount: this.state.errorCount,
    });

    this.setState({
      hasError: false,
      error: undefined,
      errorInfo: undefined,
      errorCount: 0,
    });
  };

  handleDownloadLogs = (): void => {
    logger.downloadLogs();
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-gray-50">
          <Card className="max-w-2xl w-full">
            <CardHeader>
              <div className="flex items-center gap-2">
                <AlertCircle className="h-6 w-6 text-red-500" />
                <CardTitle>Something went wrong</CardTitle>
              </div>
              <CardDescription>
                An unexpected error occurred in the application. The error has been logged and reported.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <div className="p-4 bg-red-50 rounded-lg">
                  <h3 className="font-semibold text-red-800 mb-2">Error Details (Development Only)</h3>
                  <p className="text-sm text-red-700 font-mono mb-2">
                    {this.state.error.message}
                  </p>
                  {this.state.error.stack && (
                    <details className="text-xs text-red-600">
                      <summary className="cursor-pointer hover:underline">Stack Trace</summary>
                      <pre className="mt-2 p-2 bg-white rounded overflow-x-auto">
                        {this.state.error.stack}
                      </pre>
                    </details>
                  )}
                  {this.state.errorInfo?.componentStack && (
                    <details className="text-xs text-red-600 mt-2">
                      <summary className="cursor-pointer hover:underline">Component Stack</summary>
                      <pre className="mt-2 p-2 bg-white rounded overflow-x-auto">
                        {this.state.errorInfo.componentStack}
                      </pre>
                    </details>
                  )}
                </div>
              )}

              <div className="flex gap-2">
                <Button onClick={this.handleReset}>
                  Try Again
                </Button>
                <Button variant="outline" onClick={this.handleDownloadLogs}>
                  Download Logs
                </Button>
                <Button variant="outline" onClick={() => window.location.href = '/'}>
                  Go to Home
                </Button>
              </div>

              {this.state.errorCount > 1 && (
                <p className="text-sm text-amber-600">
                  This error has occurred {this.state.errorCount} times. If it persists, please contact support.
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

// Higher-order component for wrapping components with error boundary
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  componentName?: string
): React.ComponentType<P> {
  return (props: P) => (
    <ErrorBoundary componentName={componentName || Component.displayName || Component.name}>
      <Component {...props} />
    </ErrorBoundary>
  );
}