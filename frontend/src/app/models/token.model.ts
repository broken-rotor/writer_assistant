/**
 * TypeScript interfaces for token counting API integration.
 * 
 * These interfaces mirror the backend Pydantic models to ensure type safety
 * and provide IntelliSense support throughout the application.
 */

/**
 * Content types supported by the token counting API
 */
export enum ContentType {
  SYSTEM_PROMPT = 'system_prompt',
  NARRATIVE = 'narrative',
  DIALOGUE = 'dialogue',
  CHARACTER_DESCRIPTION = 'character_description',
  SCENE_DESCRIPTION = 'scene_description',
  INTERNAL_MONOLOGUE = 'internal_monologue',
  WORLDBUILDING = 'worldbuilding',
  METADATA = 'metadata',
  UNKNOWN = 'unknown'
}

/**
 * Token counting strategies with different overhead calculations
 */
export enum CountingStrategy {
  EXACT = 'exact',
  ESTIMATED = 'estimated',
  CONSERVATIVE = 'conservative',
  OPTIMISTIC = 'optimistic'
}

/**
 * Individual text item for token counting requests
 */
export interface TokenCountRequestItem {
  /** Text content to count tokens for */
  text: string;
  /** Content type for the text (auto-detected if not provided) */
  content_type?: ContentType;
}

/**
 * Request model for batch token counting
 */
export interface TokenCountRequest {
  /** List of text items to count tokens for */
  texts: TokenCountRequestItem[];
  /** Token counting strategy to use */
  strategy?: CountingStrategy;
  /** Whether to include detailed metadata in response */
  include_metadata?: boolean;
}

/**
 * Individual token count result
 */
export interface TokenCountResultItem {
  /** Original text content */
  text: string;
  /** Number of tokens in the text */
  token_count: number;
  /** Detected or specified content type */
  content_type: ContentType;
  /** Counting strategy used */
  strategy: CountingStrategy;
  /** Overhead multiplier applied */
  overhead_applied: number;
  /** Additional metadata about the token counting */
  metadata?: Record<string, any>;
}

/**
 * Response model for batch token counting
 */
export interface TokenCountResponse {
  /** Whether the request was successful */
  success: boolean;
  /** Token count results for each input text */
  results: TokenCountResultItem[];
  /** Summary statistics for the batch */
  summary: Record<string, any>;
}

/**
 * Error response model
 */
export interface TokenCountError {
  /** Error message */
  message: string;
  /** Error code */
  code?: string;
  /** Additional error details */
  details?: Record<string, any>;
}

/**
 * Loading state for token counting operations
 */
export interface TokenCountLoadingState {
  /** Whether any operation is currently loading */
  isLoading: boolean;
  /** Number of pending requests */
  pendingRequests: number;
  /** Current operation description */
  operation?: string;
}

/**
 * Cache entry for storing token count results
 */
export interface TokenCountCacheEntry {
  /** Cached result */
  result: TokenCountResultItem;
  /** Timestamp when cached */
  timestamp: number;
  /** Cache hit count */
  hitCount: number;
}

/**
 * Configuration options for the TokenCountingService
 */
export interface TokenCountingServiceConfig {
  /** Debounce delay in milliseconds */
  debounceMs: number;
  /** Maximum cache size */
  maxCacheSize: number;
  /** Cache TTL in milliseconds */
  cacheTtlMs: number;
  /** Maximum retry attempts */
  maxRetries: number;
  /** Retry delay in milliseconds */
  retryDelayMs: number;
  /** Maximum batch size */
  maxBatchSize: number;
}

/**
 * Default configuration for the TokenCountingService
 */
export const DEFAULT_TOKEN_COUNTING_CONFIG: TokenCountingServiceConfig = {
  debounceMs: 400,
  maxCacheSize: 1000,
  cacheTtlMs: 5 * 60 * 1000, // 5 minutes
  maxRetries: 3,
  retryDelayMs: 1000,
  maxBatchSize: 50
};

/**
 * Batch processing options
 */
export interface BatchProcessingOptions {
  /** Strategy for batching requests */
  strategy: 'immediate' | 'time-based' | 'size-based';
  /** Maximum wait time for time-based batching */
  maxWaitMs?: number;
  /** Minimum batch size for size-based batching */
  minBatchSize?: number;
  /** Maximum batch size */
  maxBatchSize?: number;
}

/**
 * Progress information for batch operations
 */
export interface BatchProgress {
  /** Total number of items to process */
  total: number;
  /** Number of items completed */
  completed: number;
  /** Number of items failed */
  failed: number;
  /** Progress percentage (0-100) */
  percentage: number;
  /** Current operation status */
  status: 'pending' | 'processing' | 'completed' | 'failed';
}
