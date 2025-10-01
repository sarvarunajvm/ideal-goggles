/**
 * Production-ready logging utility for frontend debugging
 */

/* eslint-disable no-console */
/* eslint-disable @typescript-eslint/no-explicit-any */

interface LogEntry {
  timestamp: string;
  level: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';
  message: string;
  context?: Record<string, any>;
  error?: Error;
  duration?: number;
  requestId?: string;
}

interface PerformanceMetrics {
  operation: string;
  startTime: number;
  endTime?: number;
  duration?: number;
  metadata?: Record<string, any>;
}

class Logger {
  private static instance: Logger;
  private logs: LogEntry[] = [];
  private maxLogs = 1000; // Keep last 1000 logs in memory
  private performanceMetrics: Map<string, PerformanceMetrics> = new Map();
  private isDevelopment: boolean;
  private logLevel: string;
  private requestIdCounter = 0;

  private getEnvValue(): { isDev: boolean; logLevel: string } {
    // Check if we're in a test environment
    if (typeof process !== 'undefined' && process.env.NODE_ENV === 'test') {
      return { isDev: true, logLevel: 'INFO' };
    }

    // Try to access Vite env variables
    try {
      // @ts-ignore - import.meta might not exist in test environment
      const viteEnv = import.meta?.env;
      return {
        isDev: viteEnv?.DEV || false,
        logLevel: viteEnv?.VITE_LOG_LEVEL || 'INFO'
      };
    } catch {
      // Fallback for environments where import.meta doesn't exist
      return { isDev: false, logLevel: 'INFO' };
    }
  }

  private constructor() {
    const env = this.getEnvValue();
    this.isDevelopment = env.isDev;
    this.logLevel = env.logLevel;

    // Set up global error handler
    this.setupGlobalErrorHandler();
    // Set up performance observer
    this.setupPerformanceObserver();
  }

  static getInstance(): Logger {
    if (!Logger.instance) {
      Logger.instance = new Logger();
    }
    return Logger.instance;
  }

  private setupGlobalErrorHandler(): void {
    if (typeof window !== 'undefined') {
      window.addEventListener('error', (event) => {
        this.error('Uncaught error', {
          message: event.message,
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno,
          error: event.error,
        });
      });

      window.addEventListener('unhandledrejection', (event) => {
        this.error('Unhandled promise rejection', {
          reason: event.reason,
        });
      });
    }
  }

  private setupPerformanceObserver(): void {
    if (typeof window !== 'undefined' && 'PerformanceObserver' in window) {
      try {
        // Monitor navigation timing
        const navObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.entryType === 'navigation') {
              const navEntry = entry as PerformanceNavigationTiming;
              this.info('Page load performance', {
                domContentLoaded: navEntry.domContentLoadedEventEnd - navEntry.domContentLoadedEventStart,
                loadComplete: navEntry.loadEventEnd - navEntry.loadEventStart,
                domInteractive: navEntry.domInteractive,
                duration: navEntry.duration,
              });
            }
          }
        });
        navObserver.observe({ entryTypes: ['navigation'] });

        // Monitor resource timing
        const resourceObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.duration > 1000) { // Log slow resources
              this.warn('Slow resource loading', {
                name: entry.name,
                duration: entry.duration,
                type: (entry as any).initiatorType,
              });
            }
          }
        });
        resourceObserver.observe({ entryTypes: ['resource'] });
      } catch (e) {
        console.warn('Performance observer setup failed:', e);
      }
    }
  }

  private shouldLog(level: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR'): boolean {
    const levels = ['DEBUG', 'INFO', 'WARN', 'ERROR'];
    const currentLevelIndex = levels.indexOf(this.logLevel);
    const messageLevelIndex = levels.indexOf(level);
    return messageLevelIndex >= currentLevelIndex;
  }

  private formatLogEntry(entry: LogEntry): string {
    const parts = [
      `[${entry.timestamp}]`,
      `[${entry.level}]`,
      entry.message,
    ];

    if (entry.requestId) {
      parts.push(`[req:${entry.requestId}]`);
    }

    if (entry.duration !== undefined) {
      parts.push(`[${entry.duration}ms]`);
    }

    if (entry.context) {
      parts.push(JSON.stringify(entry.context));
    }

    if (entry.error) {
      parts.push(`\nError: ${entry.error.message}\nStack: ${entry.error.stack}`);
    }

    return parts.join(' ');
  }

  private addLog(entry: LogEntry): void {
    // Add to memory buffer
    this.logs.push(entry);
    if (this.logs.length > this.maxLogs) {
      this.logs.shift();
    }

    // Console output
    if (this.shouldLog(entry.level)) {
      const formatted = this.formatLogEntry(entry);
      switch (entry.level) {
        case 'DEBUG':
          console.debug(formatted);
          break;
        case 'INFO':
          console.info(formatted);
          break;
        case 'WARN':
          console.warn(formatted);
          break;
        case 'ERROR':
          console.error(formatted);
          break;
      }
    }

    // Send critical errors to backend (in production)
    if (!this.isDevelopment && entry.level === 'ERROR') {
      this.sendToBackend(entry);
    }
  }

  private async sendToBackend(entry: LogEntry): Promise<void> {
    try {
      // Send error logs to backend for monitoring
      await fetch('/api/logs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...entry,
          userAgent: navigator.userAgent,
          url: window.location.href,
          timestamp: new Date().toISOString(),
        }),
      });
    } catch (e) {
      // Silently fail to avoid infinite loop
      console.error('Failed to send log to backend:', e);
    }
  }

  generateRequestId(): string {
    this.requestIdCounter++;
    return `${Date.now()}-${this.requestIdCounter}`;
  }

  debug(message: string, context?: Record<string, any>): void {
    this.addLog({
      timestamp: new Date().toISOString(),
      level: 'DEBUG',
      message,
      context,
    });
  }

  info(message: string, context?: Record<string, any>): void {
    this.addLog({
      timestamp: new Date().toISOString(),
      level: 'INFO',
      message,
      context,
    });
  }

  warn(message: string, context?: Record<string, any>): void {
    this.addLog({
      timestamp: new Date().toISOString(),
      level: 'WARN',
      message,
      context,
    });
  }

  error(message: string, error?: Error | any, context?: Record<string, any>): void {
    const errorObj = error instanceof Error ? error : new Error(String(error));
    this.addLog({
      timestamp: new Date().toISOString(),
      level: 'ERROR',
      message,
      context,
      error: errorObj,
    });
  }

  // Performance tracking
  startPerformance(operation: string, metadata?: Record<string, any>): void {
    this.performanceMetrics.set(operation, {
      operation,
      startTime: performance.now(),
      metadata,
    });
  }

  endPerformance(operation: string): void {
    const metric = this.performanceMetrics.get(operation);
    if (metric) {
      metric.endTime = performance.now();
      metric.duration = metric.endTime - metric.startTime;

      // Log if operation took too long
      if (metric.duration > 1000) {
        this.warn(`Slow operation: ${operation}`, {
          duration: metric.duration,
          metadata: metric.metadata,
        });
      } else {
        this.debug(`Performance: ${operation}`, {
          duration: metric.duration,
          metadata: metric.metadata,
        });
      }

      this.performanceMetrics.delete(operation);
    }
  }

  // API call logging
  logApiCall(
    method: string,
    url: string,
    requestId: string,
    body?: any,
    headers?: Record<string, string>
  ): void {
    this.info(`API Request: ${method} ${url}`, {
      requestId,
      method,
      url,
      body,
      headers: this.isDevelopment ? headers : undefined, // Only log headers in dev
    });
  }

  logApiResponse(
    method: string,
    url: string,
    requestId: string,
    status: number,
    duration: number,
    data?: any
  ): void {
    const level = status >= 400 ? 'ERROR' : 'INFO';
    this.addLog({
      timestamp: new Date().toISOString(),
      level,
      message: `API Response: ${method} ${url} - ${status}`,
      context: {
        requestId,
        method,
        url,
        status,
        duration,
        data: this.isDevelopment ? data : undefined, // Only log data in dev
      },
      duration,
      requestId,
    });
  }

  // Export logs for debugging
  exportLogs(): string {
    return this.logs.map(entry => this.formatLogEntry(entry)).join('\n');
  }

  downloadLogs(): void {
    const logs = this.exportLogs();
    const blob = new Blob([logs], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `app-logs-${new Date().toISOString()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  clearLogs(): void {
    this.logs = [];
    this.performanceMetrics.clear();
  }

  // Get recent logs for display
  getRecentLogs(count: number = 100): LogEntry[] {
    return this.logs.slice(-count);
  }

  // Component lifecycle logging
  logComponentMount(componentName: string, props?: any): void {
    this.debug(`Component mounted: ${componentName}`, { props });
  }

  logComponentUnmount(componentName: string): void {
    this.debug(`Component unmounted: ${componentName}`);
  }

  logComponentError(componentName: string, error: Error, errorInfo?: any): void {
    this.error(`Component error: ${componentName}`, error, { errorInfo });
  }

  // User action logging
  logUserAction(action: string, details?: Record<string, any>): void {
    this.info(`User action: ${action}`, details);
  }
}

// Export singleton instance
export const logger = Logger.getInstance();

// Export types
export type { LogEntry, PerformanceMetrics };