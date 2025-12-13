/**
 * Application configuration constants
 * Centralized timeout, retry, and performance values
 */

// API Configuration
export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_URL || 'http://localhost:5555',
  TIMEOUT: 30000, // 30 seconds
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000, // 1 second
} as const;

// Backend Connection
export const BACKEND_CONFIG = {
  PORT: 5555,
  HEALTH_CHECK_INTERVAL: 1000, // 1 second during startup
  HEALTH_CHECK_AFTER_READY: 30000, // 30 seconds after connected
  MAX_RETRIES: 60,
  RETRY_DELAY: 500, // milliseconds
} as const;

// Performance Thresholds
export const PERFORMANCE_CONFIG = {
  VIRTUAL_GRID_OVERSCAN: 5,
  IMAGE_LAZY_LOAD_THRESHOLD: 200, // pixels
  DEBOUNCE_SEARCH: 300, // milliseconds
  THROTTLE_SCROLL: 100, // milliseconds
  SLOW_REQUEST_WARNING: 1000, // milliseconds
} as const;

// UI Configuration
export const UI_CONFIG = {
  TOAST_DURATION: 5000, // milliseconds
  LIGHTBOX_TRANSITION: 200, // milliseconds
  MODAL_ANIMATION: 150, // milliseconds
  TOOLTIP_DELAY: 500, // milliseconds
} as const;

// Pagination
export const PAGINATION_CONFIG = {
  DEFAULT_PAGE_SIZE: 50,
  MAX_PAGE_SIZE: 200,
  MIN_PAGE_SIZE: 10,
} as const;

// Thumbnail Configuration
export const THUMBNAIL_CONFIG = {
  DEFAULT_SIZE: 200,
  SIZES: [100, 200, 400] as const,
  QUALITY: 80,
  FORMAT: 'webp' as const,
} as const;

// Developer Mode
export const DEV_CONFIG = {
  CLICK_COUNT_FOR_DEV_MODE: 6,
  CLICK_TIMEOUT: 2000, // milliseconds
} as const;

// Logging
export const LOGGING_CONFIG = {
  MAX_LOG_ENTRIES: 1000,
  LOG_RETENTION_DAYS: 7,
  ENABLE_PERFORMANCE_LOGGING: import.meta.env.DEV,
  ENABLE_DEBUG_LOGGING: import.meta.env.DEV,
} as const;

// Export all configs as a single object for convenience
export const APP_CONFIG = {
  API: API_CONFIG,
  BACKEND: BACKEND_CONFIG,
  PERFORMANCE: PERFORMANCE_CONFIG,
  UI: UI_CONFIG,
  PAGINATION: PAGINATION_CONFIG,
  THUMBNAIL: THUMBNAIL_CONFIG,
  DEV: DEV_CONFIG,
  LOGGING: LOGGING_CONFIG,
} as const;

export default APP_CONFIG;
