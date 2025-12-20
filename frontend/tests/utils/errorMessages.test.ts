/**
 * Comprehensive unit tests for Error Messages utility
 * Tests error mapping, user-friendly message generation, and notification formatting
 */

import {
  mapErrorToUserMessage,
  shouldHideError,
  formatErrorForNotification,
} from '../../src/utils/errorMessages'

describe('Error Messages Utility', () => {
  describe('mapErrorToUserMessage', () => {
    describe('Backend Configuration Errors', () => {
      test('maps database manager error to user message', () => {
        const error = 'Failed to retrieve configuration: get_database_manager is not defined'
        const result = mapErrorToUserMessage(error)

        expect(result.message).toBe('Database connection issue. Please restart the application.')
        expect(result.severity).toBe('error')
        expect(result.originalError).toBe(error)
      })

      test('maps HTTP 500 configuration error to warning', () => {
        const error = 'HTTP error! status: 500 - Failed to retrieve configuration'
        const result = mapErrorToUserMessage(error)

        expect(result.message).toBe('Unable to load settings. The application is starting up, please wait a moment.')
        expect(result.severity).toBe('warning')
      })
    })

    describe('API Endpoint Errors', () => {
      test('maps 404 logs error to info', () => {
        const error = 'HTTP error! status: 404 - logs endpoint not found'
        const result = mapErrorToUserMessage(error)

        expect(result.message).toBe('Logging system temporarily unavailable.')
        expect(result.severity).toBe('info')
      })

      test('maps generic 500 error', () => {
        const error = 'HTTP error! status: 500'
        const result = mapErrorToUserMessage(error)

        expect(result.message).toBe('Server error occurred. Please try again in a moment.')
        expect(result.severity).toBe('error')
      })

      test('maps 404 error', () => {
        const error = 'HTTP error! status: 404'
        const result = mapErrorToUserMessage(error)

        expect(result.message).toBe('The requested feature is not available.')
        expect(result.severity).toBe('warning')
      })

      test('maps 403 forbidden error', () => {
        const error = 'HTTP error! status: 403'
        const result = mapErrorToUserMessage(error)

        expect(result.message).toBe('Access denied. Please check your permissions.')
        expect(result.severity).toBe('error')
      })
    })

    describe('Network and Connection Errors', () => {
      test('maps network request failed error', () => {
        const error = 'Network request failed: Connection refused'
        const result = mapErrorToUserMessage(error)

        expect(result.message).toBe('Cannot connect to the server. Please check if the application is running.')
        expect(result.severity).toBe('error')
      })

      test('maps fetch failed error', () => {
        const error = 'fetch operation failed due to network error'
        const result = mapErrorToUserMessage(error)

        expect(result.message).toBe('Cannot connect to the server. Please check if the application is running.')
        expect(result.severity).toBe('error')
      })

      test('maps timeout error', () => {
        const error = 'Request timed out after 30 seconds'
        const result = mapErrorToUserMessage(error)

        expect(result.message).toBe('Request timed out. The server might be busy, please try again.')
        expect(result.severity).toBe('warning')
      })
    })

    describe('Indexing and File System Errors', () => {
      test('maps no root paths configured error', () => {
        const error = 'No root paths configured for indexing'
        const result = mapErrorToUserMessage(error)

        expect(result.message).toBe('No photo folders have been set up yet. Go to Settings to add your photo folders.')
        expect(result.severity).toBe('info')
      })

      test('maps failed to start indexing error', () => {
        const error = 'Failed to start indexing process'
        const result = mapErrorToUserMessage(error)

        expect(result.message).toBe('Unable to start photo indexing. Please check that your photo folders are accessible.')
        expect(result.severity).toBe('error')
      })

      test('maps permission denied folder error', () => {
        const error = 'Permission denied when accessing folder /path/to/photos'
        const result = mapErrorToUserMessage(error)

        expect(result.message).toBe('Cannot access photo folder. Please check folder permissions.')
        expect(result.severity).toBe('error')
      })

      test('maps file not found error', () => {
        const error = 'File not found: /path/to/missing/folder'
        const result = mapErrorToUserMessage(error)

        expect(result.message).toBe('Photo folder no longer exists. Please update your folder settings.')
        expect(result.severity).toBe('warning')
      })

      test('maps path does not exist error', () => {
        const error = 'Path does not exist: /invalid/path'
        const result = mapErrorToUserMessage(error)

        expect(result.message).toBe('Photo folder no longer exists. Please update your folder settings.')
        expect(result.severity).toBe('warning')
      })
    })

    describe('Search and ML Model Errors', () => {
      test('maps CLIP not available error', () => {
        const error = 'CLIP model not available for semantic search'
        const result = mapErrorToUserMessage(error)

        expect(result.message).toBe('Smart search is not available. Some features may be limited.')
        expect(result.severity).toBe('info')
      })

      test('maps semantic search not available error', () => {
        const error = 'semantic search engine not available'
        const result = mapErrorToUserMessage(error)

        expect(result.message).toBe('Smart search is not available. Some features may be limited.')
        expect(result.severity).toBe('info')
      })

      test('maps face detection not available error', () => {
        const error = 'Face detection service not available'
        const result = mapErrorToUserMessage(error)

        expect(result.message).toBe('Face recognition is not available. People search features are disabled.')
        expect(result.severity).toBe('info')
      })

      test('maps OCR not available error', () => {
        const error = 'OCR engine not available for text recognition'
        const result = mapErrorToUserMessage(error)

        expect(result.message).toBe('Text recognition is not available. You cannot search for text in images.')
        expect(result.severity).toBe('info')
      })

      test('maps text recognition not available error', () => {
        const error = 'text recognition service not available'
        const result = mapErrorToUserMessage(error)

        expect(result.message).toBe('Text recognition is not available. You cannot search for text in images.')
        expect(result.severity).toBe('info')
      })
    })

    describe('Database Errors', () => {
      test('maps database locked error', () => {
        const error = 'database is locked - another process is using it'
        const result = mapErrorToUserMessage(error)

        expect(result.message).toBe('Photo database is busy. Please wait a moment and try again.')
        expect(result.severity).toBe('warning')
      })

      test('maps database busy error', () => {
        const error = 'database is busy processing request'
        const result = mapErrorToUserMessage(error)

        expect(result.message).toBe('Photo database is busy. Please wait a moment and try again.')
        expect(result.severity).toBe('warning')
      })

      test('maps database corrupt error', () => {
        const error = 'database file is corrupt and cannot be read'
        const result = mapErrorToUserMessage(error)

        expect(result.message).toBe('Photo database needs repair. Please contact support.')
        expect(result.severity).toBe('error')
      })
    })

    describe('Generic and Edge Cases', () => {
      test('maps generic error', () => {
        const error = 'An unexpected error occurred in the system'
        const result = mapErrorToUserMessage(error)

        expect(result.message).toBe('An unexpected error occurred. Please try again.')
        expect(result.severity).toBe('error')
      })

      test('handles empty string', () => {
        const result = mapErrorToUserMessage('')

        expect(result.message).toBe('An unknown error occurred.')
        expect(result.severity).toBe('error')
      })

      test('handles whitespace only', () => {
        const result = mapErrorToUserMessage('   ')

        expect(result.message).toBe('An unknown error occurred.')
        expect(result.severity).toBe('error')
      })

      test('handles null input', () => {
        const result = mapErrorToUserMessage(null as any)

        expect(result.message).toBe('An unknown error occurred.')
        expect(result.severity).toBe('error')
      })

      test('handles undefined input', () => {
        const result = mapErrorToUserMessage(undefined as any)

        expect(result.message).toBe('An unknown error occurred.')
        expect(result.severity).toBe('error')
      })

      test('cleans up unmatched technical error', () => {
        const error = 'HTTP error! status: 418, message: "I\'m a teapot", detail: "Custom error"'
        const result = mapErrorToUserMessage(error)

        // Should clean up the error message
        expect(result.message).not.toContain('HTTP error! status:')
        expect(result.message).not.toContain('message:')
        expect(result.message).not.toContain('detail:')
        expect(result.severity).toBe('error')
        expect(result.originalError).toBe(error)
      })

      test('handles errors with failed/exception keywords', () => {
        const error = 'Operation failed with exception'
        const result = mapErrorToUserMessage(error)

        expect(result.message).toBe('An unexpected error occurred. Please try again.')
        expect(result.severity).toBe('error')
      })
    })

    describe('Pattern Matching', () => {
      test('uses string pattern matching', () => {
        // Test that string patterns work correctly
        const error = 'Some error containing specific string'
        const result = mapErrorToUserMessage(error)

        expect(result).toBeDefined()
        expect(result.severity).toBeDefined()
      })

      test('uses regex pattern matching', () => {
        // Test case-insensitive regex matching
        const error = 'NETWORK REQUEST FAILED'
        const result = mapErrorToUserMessage(error)

        expect(result.message).toBe('Cannot connect to the server. Please check if the application is running.')
      })

      test('matches first pattern when multiple patterns could match', () => {
        // 404 logs should match more specific pattern first
        const error = 'HTTP error! status: 404 - logs endpoint missing'
        const result = mapErrorToUserMessage(error)

        expect(result.message).toBe('Logging system temporarily unavailable.')
        expect(result.severity).toBe('info')
      })
    })
  })

  describe('shouldHideError', () => {
    test('hides Vite hot update errors', () => {
      const error = 'vite hot module update failed'
      expect(shouldHideError(error)).toBe(true)
    })

    test('hides React DevTools errors', () => {
      const error = 'react-devtools connection error'
      expect(shouldHideError(error)).toBe(true)
    })

    test('hides WebSocket connection errors', () => {
      const error = 'websocket connection failed'
      expect(shouldHideError(error)).toBe(true)
    })

    test('hides favicon 404 errors', () => {
      const error = 'GET /favicon.ico 404 (Not Found)'
      expect(shouldHideError(error)).toBe(true)
    })

    test('hides sourcemap warnings', () => {
      const error = 'sourcemap parsing warning detected'
      expect(shouldHideError(error)).toBe(true)
    })

    test('does not hide user-facing errors', () => {
      const error = 'Failed to load user data'
      expect(shouldHideError(error)).toBe(false)
    })

    test('does not hide API errors', () => {
      const error = 'HTTP error! status: 500'
      expect(shouldHideError(error)).toBe(false)
    })

    test('handles case-insensitive matching', () => {
      const error = 'VITE HOT UPDATE ERROR'
      expect(shouldHideError(error)).toBe(true)
    })

    test('returns false for empty string', () => {
      expect(shouldHideError('')).toBe(false)
    })
  })

  describe('formatErrorForNotification', () => {
    test('formats error severity as destructive for error level', () => {
      const error = 'HTTP error! status: 500'
      const result = formatErrorForNotification(error)

      expect(result.title).toBe('Error')
      expect(result.variant).toBe('destructive')
      expect(result.description).toContain('Server error')
    })

    test('formats warning severity as default for warning level', () => {
      const error = 'Request timed out'
      const result = formatErrorForNotification(error)

      expect(result.title).toBe('Warning')
      expect(result.variant).toBe('default')
      expect(result.description).toContain('timed out')
    })

    test('formats info severity as default for info level', () => {
      const error = 'No root paths configured'
      const result = formatErrorForNotification(error)

      expect(result.title).toBe('Notice')
      expect(result.variant).toBe('default')
      expect(result.description).toContain('photo folders')
    })

    test('handles Error objects', () => {
      const error = new Error('Test error message')
      const result = formatErrorForNotification(error)

      expect(result.title).toBe('Error')
      expect(result.description).toBe('An unexpected error occurred. Please try again.')
      expect(result.variant).toBe('destructive')
    })

    test('handles string errors', () => {
      const error = 'Simple error string'
      const result = formatErrorForNotification(error)

      expect(result.title).toBe('Error')
      expect(result.description).toBe('An unexpected error occurred. Please try again.')
      expect(result.variant).toBe('destructive')
    })

    test('handles null error', () => {
      const result = formatErrorForNotification(null)

      expect(result.title).toBeDefined()
      expect(result.description).toBeDefined()
      expect(result.variant).toBeDefined()
      expect(['destructive', 'default']).toContain(result.variant)
    })

    test('handles undefined error', () => {
      const result = formatErrorForNotification(undefined)

      expect(result.title).toBeDefined()
      expect(result.description).toBeDefined()
      expect(result.variant).toBeDefined()
      expect(['destructive', 'default']).toContain(result.variant)
    })

    test('handles object with message property', () => {
      const error = { message: 'HTTP error! status: 403' }
      const result = formatErrorForNotification(error)

      expect(result.title).toBeDefined()
      expect(result.description).toBeDefined()
      expect(result.variant).toBeDefined()
      // The function converts object to string, so check it doesn't crash
      expect(typeof result.description).toBe('string')
    })

    test('handles number errors', () => {
      const result = formatErrorForNotification(404)

      expect(result).toBeDefined()
      expect(result.title).toBeDefined()
      expect(result.description).toBeDefined()
      expect(result.variant).toBeDefined()
    })
  })

  describe('Edge Cases and Special Scenarios', () => {
    test('handles very long error messages', () => {
      const longError = 'Error: ' + 'x'.repeat(1000)
      const result = mapErrorToUserMessage(longError)

      expect(result.message).toBeDefined()
      expect(result.severity).toBeDefined()
    })

    test('handles error messages with special characters', () => {
      const error = 'Error: <script>alert("xss")</script>'
      const result = mapErrorToUserMessage(error)

      expect(result.message).toBeDefined()
      expect(result.originalError).toBe(error)
    })

    test('handles error messages with newlines', () => {
      const error = 'Error on line 1\nError on line 2\nError on line 3'
      const result = mapErrorToUserMessage(error)

      expect(result.message).toBeDefined()
      expect(result.severity).toBeDefined()
    })

    test('handles error messages with unicode characters', () => {
      const error = 'Error: 文字化けエラー 🚫'
      const result = mapErrorToUserMessage(error)

      expect(result.message).toBeDefined()
    })

    test('handles error messages with JSON', () => {
      const error = '{"error": "Internal server error", "code": 500}'
      const result = mapErrorToUserMessage(error)

      expect(result.message).toBeDefined()
      expect(result.severity).toBe('error')
    })
  })

  describe('Multiple Pattern Matching Priority', () => {
    test('specific database error takes precedence over generic error', () => {
      const error = 'database is locked - error occurred'
      const result = mapErrorToUserMessage(error)

      // Should match specific "database locked" pattern before generic "error" pattern
      expect(result.message).toBe('Photo database is busy. Please wait a moment and try again.')
      expect(result.severity).toBe('warning')
    })

    test('specific HTTP status takes precedence over generic HTTP error', () => {
      const error = 'HTTP error! status: 500 - logs failed'
      const result = mapErrorToUserMessage(error)

      // Should match specific pattern first
      expect(result.message).toBe('Server error occurred. Please try again in a moment.')
      expect(result.severity).toBe('error')
    })
  })
})
