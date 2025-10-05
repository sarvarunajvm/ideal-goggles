/**
 * Maps technical error messages to user-friendly messages
 */

export interface ErrorMapping {
  pattern: RegExp | string;
  userMessage: string;
  severity: 'error' | 'warning' | 'info';
}

const ERROR_MAPPINGS: ErrorMapping[] = [
  // Backend configuration errors
  {
    pattern: /Failed to retrieve configuration.*get_database_manager.*not defined/i,
    userMessage: "Database connection issue. Please restart the application.",
    severity: 'error'
  },
  {
    pattern: /HTTP error! status: 500.*Failed to retrieve configuration/i,
    userMessage: "Unable to load settings. The application is starting up, please wait a moment.",
    severity: 'warning'
  },

  // API endpoint errors
  {
    pattern: /HTTP error! status: 404.*logs/i,
    userMessage: "Logging system temporarily unavailable.",
    severity: 'info'
  },
  {
    pattern: /HTTP error! status: 500/i,
    userMessage: "Server error occurred. Please try again in a moment.",
    severity: 'error'
  },
  {
    pattern: /HTTP error! status: 404/i,
    userMessage: "The requested feature is not available.",
    severity: 'warning'
  },
  {
    pattern: /HTTP error! status: 403/i,
    userMessage: "Access denied. Please check your permissions.",
    severity: 'error'
  },

  // Network and connection errors
  {
    pattern: /Network request failed|fetch.*failed|Connection refused/i,
    userMessage: "Cannot connect to the server. Please check if the application is running.",
    severity: 'error'
  },
  {
    pattern: /timeout|timed out/i,
    userMessage: "Request timed out. The server might be busy, please try again.",
    severity: 'warning'
  },

  // Indexing and file system errors
  {
    pattern: /No root paths configured/i,
    userMessage: "No photo folders have been set up yet. Go to Settings to add your photo folders.",
    severity: 'info'
  },
  {
    pattern: /Failed to start indexing/i,
    userMessage: "Unable to start photo indexing. Please check that your photo folders are accessible.",
    severity: 'error'
  },
  {
    pattern: /Permission denied.*folder/i,
    userMessage: "Cannot access photo folder. Please check folder permissions.",
    severity: 'error'
  },
  {
    pattern: /File not found|Path does not exist/i,
    userMessage: "Photo folder no longer exists. Please update your folder settings.",
    severity: 'warning'
  },

  // Search and ML model errors
  {
    pattern: /CLIP.*not available|semantic search.*not available/i,
    userMessage: "Smart search is not available. Some features may be limited.",
    severity: 'info'
  },
  {
    pattern: /Face detection.*not available/i,
    userMessage: "Face recognition is not available. People search features are disabled.",
    severity: 'info'
  },
  {
    pattern: /OCR.*not available|text recognition.*not available/i,
    userMessage: "Text recognition is not available. You cannot search for text in images.",
    severity: 'info'
  },

  // Database errors
  {
    pattern: /database.*locked|database.*busy/i,
    userMessage: "Photo database is busy. Please wait a moment and try again.",
    severity: 'warning'
  },
  {
    pattern: /database.*corrupt/i,
    userMessage: "Photo database needs repair. Please contact support.",
    severity: 'error'
  },

  // Generic fallbacks
  {
    pattern: /error|failed|exception/i,
    userMessage: "An unexpected error occurred. Please try again.",
    severity: 'error'
  }
];

/**
 * Maps a technical error message to a user-friendly message
 */
export function mapErrorToUserMessage(technicalError: string): {
  message: string;
  severity: 'error' | 'warning' | 'info';
  originalError?: string;
} {
  // Clean the input
  const error = String(technicalError || '').trim();

  if (!error) {
    return {
      message: "An unknown error occurred.",
      severity: 'error'
    };
  }

  // Find the first matching pattern
  for (const mapping of ERROR_MAPPINGS) {
    const pattern = mapping.pattern;
    const matches = typeof pattern === 'string'
      ? error.includes(pattern)
      : pattern.test(error);

    if (matches) {
      return {
        message: mapping.userMessage,
        severity: mapping.severity,
        originalError: error
      };
    }
  }

  // No pattern matched, return the original error but cleaned up
  const cleanedError = error
    .replace(/HTTP error! status: \d+,?\s*/gi, '')
    .replace(/message:\s*/gi, '')
    .replace(/^[{]?"?detail"?:\s*"?/gi, '')
    .replace(/["}]*$/gi, '')
    .trim();

  return {
    message: cleanedError || "An unexpected error occurred.",
    severity: 'error',
    originalError: error
  };
}

/**
 * Determines if an error should be hidden from the user (too technical/not actionable)
 */
export function shouldHideError(error: string): boolean {
  const hiddenPatterns = [
    /vite.*hot.*update/i,
    /react.*devtools/i,
    /websocket.*connection/i,
    /favicon\.ico.*404/i,
    /sourcemap.*warning/i
  ];

  return hiddenPatterns.some(pattern => pattern.test(error));
}

/**
 * Formats an error for display in notifications
 */
export function formatErrorForNotification(error: any): {
  title: string;
  description: string;
  variant: 'destructive' | 'default';
} {
  const errorString = error instanceof Error ? error.message : String(error);
  const mapped = mapErrorToUserMessage(errorString);

  return {
    title: mapped.severity === 'error' ? 'Error' : mapped.severity === 'warning' ? 'Warning' : 'Notice',
    description: mapped.message,
    variant: mapped.severity === 'error' ? 'destructive' : 'default'
  };
}