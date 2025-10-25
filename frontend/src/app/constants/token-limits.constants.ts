/**
 * Constants for token limits error handling and fallback behavior
 */

import { RecommendedLimits } from '../models/token-limits.model';

/**
 * Fallback field limits used when token limits API is unavailable
 * These are conservative defaults that ensure the app remains functional
 */
export const FALLBACK_FIELD_LIMITS: RecommendedLimits = {
  system_prompt_prefix: 500,
  system_prompt_suffix: 500,
  writing_assistant_prompt: 1000,
  writing_editor_prompt: 1000
};

/**
 * Exponential backoff configuration for retry logic
 */
export const RETRY_CONFIG = {
  /** Maximum number of retry attempts */
  maxRetries: 3,
  /** Base delay in milliseconds for first retry */
  baseDelay: 1000,
  /** Maximum delay in milliseconds (caps exponential growth) */
  maxDelay: 8000,
  /** Multiplier for exponential backoff */
  backoffMultiplier: 2,
  /** Jitter factor to randomize delays (0-1) */
  jitterFactor: 0.1
};

/**
 * Error message mappings for user-friendly display
 */
export const ERROR_MESSAGES = {
  // Network and API errors
  NETWORK_ERROR: 'Unable to connect to token validation service. Please check your internet connection.',
  API_UNAVAILABLE: 'Token validation service is temporarily unavailable. Using fallback limits.',
  TIMEOUT_ERROR: 'Request timed out. Please try again.',
  SERVER_ERROR: 'Server error occurred. Please try again in a few moments.',
  
  // Token counting errors
  TOKEN_COUNT_FAILED: 'Unable to count tokens. Please try again.',
  INVALID_CONTENT: 'Content format is invalid for token counting.',
  
  // Validation errors
  VALIDATION_FAILED: 'Token validation failed. Using fallback validation.',
  LIMITS_UNAVAILABLE: 'Token limits are unavailable. Using default limits.',
  TOKEN_LIMITS_FAILED: 'Failed to load token limits. Using fallback limits.',
  
  // Recovery messages
  RETRY_AVAILABLE: 'Click retry to attempt loading token limits again.',
  FALLBACK_MODE: 'Operating in fallback mode with default token limits.',
  SERVICE_RESTORED: 'Token validation service has been restored.',
  
  // Loading states
  LOADING_LIMITS: 'Loading token limits...',
  COUNTING_TOKENS: 'Counting tokens...',
  VALIDATING: 'Validating token count...',
  RETRYING: 'Retrying connection...'
};

/**
 * Toast notification configuration
 */
export const TOAST_CONFIG = {
  /** Default duration for toast messages in milliseconds */
  defaultDuration: 5000,
  /** Duration for error messages */
  errorDuration: 8000,
  /** Duration for success messages */
  successDuration: 3000,
  /** Maximum number of toasts to show simultaneously */
  maxToasts: 3,
  /** Position of toast container */
  position: 'top-right' as const
};

/**
 * Error types for categorization
 */
export enum ErrorType {
  /** Network connectivity issues */
  NETWORK = 'network',
  /** API server errors */
  SERVER = 'server',
  /** Request timeout */
  TIMEOUT = 'timeout',
  /** Invalid request/response format */
  VALIDATION = 'validation',
  /** Service temporarily unavailable */
  UNAVAILABLE = 'unavailable',
  /** Unknown error */
  UNKNOWN = 'unknown'
}

/**
 * Recovery action types
 */
export enum RecoveryAction {
  /** Retry the failed operation */
  RETRY = 'retry',
  /** Refresh/reload data */
  REFRESH = 'refresh',
  /** Use fallback/default values */
  USE_FALLBACK = 'use_fallback',
  /** Continue without the feature */
  CONTINUE = 'continue',
  /** Contact support */
  CONTACT_SUPPORT = 'contact_support'
}

/**
 * Error severity levels
 */
export enum ErrorSeverity {
  /** Low severity - app fully functional */
  LOW = 'low',
  /** Medium severity - some features affected */
  MEDIUM = 'medium',
  /** High severity - major functionality impacted */
  HIGH = 'high',
  /** Critical severity - app may not function properly */
  CRITICAL = 'critical'
}

/**
 * Error context interface for detailed error information
 */
export interface ErrorContext {
  /** Type of error */
  type: ErrorType;
  /** Severity level */
  severity: ErrorSeverity;
  /** User-friendly error message */
  message: string;
  /** Technical error details (for logging) */
  details?: string;
  /** Available recovery actions */
  recoveryActions: RecoveryAction[];
  /** Whether the error is recoverable */
  isRecoverable: boolean;
  /** Timestamp when error occurred */
  timestamp: Date;
  /** Component or service where error occurred */
  source?: string;
}

/**
 * Helper function to calculate exponential backoff delay
 */
export function calculateBackoffDelay(attempt: number, config = RETRY_CONFIG): number {
  const exponentialDelay = config.baseDelay * Math.pow(config.backoffMultiplier, attempt - 1);
  const cappedDelay = Math.min(exponentialDelay, config.maxDelay);
  
  // Add jitter to prevent thundering herd
  const jitter = cappedDelay * config.jitterFactor * Math.random();
  
  return Math.floor(cappedDelay + jitter);
}

/**
 * Helper function to create error context
 */
export function createErrorContext(
  type: ErrorType,
  severity: ErrorSeverity,
  message: string,
  recoveryActions: RecoveryAction[],
  details?: string,
  source?: string
): ErrorContext {
  return {
    type,
    severity,
    message,
    details,
    recoveryActions,
    isRecoverable: recoveryActions.length > 0,
    timestamp: new Date(),
    source
  };
}
