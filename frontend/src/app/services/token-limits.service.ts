import { Injectable, inject } from '@angular/core';
import { Observable, BehaviorSubject, of, timer, throwError } from 'rxjs';
import { map, catchError, retryWhen, mergeMap } from 'rxjs/operators';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { TokenLimitsResponse } from '../models/token-limits.model';
import {
  RETRY_CONFIG,
  ERROR_MESSAGES,
  ErrorType,
  ErrorSeverity,
  RecoveryAction,
  ErrorContext,
  calculateBackoffDelay,
  createErrorContext
} from '../constants/token-limits.constants';

/**
 * Field types for system prompt components
 */
export type SystemPromptFieldType = 'mainPrefix' | 'mainSuffix' | 'assistantPrompt' | 'editorPrompt' | 'raterSystemPrompt';

/**
 * Token limit information for a specific field
 */
export interface FieldTokenLimit {
  /** Field type */
  fieldType: SystemPromptFieldType;
  /** Maximum token limit for this field */
  limit: number;
  /** Warning threshold (typically 80% of limit) */
  warningThreshold: number;
  /** Critical threshold (typically 90% of limit) */
  criticalThreshold: number;
}

/**
 * Token limits state with loading and error information
 */
export interface TokenLimitsState {
  /** Token limits data (null if not loaded) */
  limits: TokenLimitsResponse | null;
  /** Whether limits are currently being loaded */
  isLoading: boolean;
  /** Error message if loading failed */
  error: string | null;
  /** Detailed error context for better error handling */
  errorContext: ErrorContext | null;
  /** Timestamp when limits were last loaded */
  lastUpdated: number | null;
  /** Whether currently operating in fallback mode */
  isFallbackMode: boolean;
  /** Number of retry attempts made */
  retryAttempts: number;
  /** Whether a retry is currently in progress */
  isRetrying: boolean;
}

/**
 * Service for managing token limits for different system prompt field types.
 * 
 * This service provides field-specific token limits based on backend configuration
 * and includes warning thresholds for user feedback.
 */
@Injectable({
  providedIn: 'root'
})
export class TokenLimitsService {
  private readonly baseUrl = 'http://localhost:8000/api/v1/tokens';

  // Cache for token limits with TTL
  private tokenLimits$ = new BehaviorSubject<TokenLimitsResponse | null>(null);
  private isLoading$ = new BehaviorSubject<boolean>(false);
  private error$ = new BehaviorSubject<string | null>(null);
  private errorContext$ = new BehaviorSubject<ErrorContext | null>(null);
  private isFallbackMode$ = new BehaviorSubject<boolean>(false);
  private retryAttempts$ = new BehaviorSubject<number>(0);
  private isRetrying$ = new BehaviorSubject<boolean>(false);
  private cacheTimestamp: number | null = null;
  private readonly cacheTTL: number = 5 * 60 * 1000; // 5 minutes in milliseconds

  // Default fallback limits when API is unavailable
  private readonly defaultLimits: TokenLimitsResponse = {
    system_prompt_prefix: 1000,
    system_prompt_suffix: 1000,
    writing_assistant_prompt: 0,
    writing_editor_prompt: 0,
    worldbuilding: 5000,
    plot_outline: 5000
  };

  private http = inject(HttpClient);

  constructor() {
    this.loadTokenLimits();
  }

  /**
   * Get token limits state with loading and error information
   */
  getTokenLimits(): Observable<TokenLimitsState> {
    this.ensureFreshCache();
    return this.tokenLimits$.pipe(
      map(limits => ({
        limits,
        isLoading: this.isLoading$.value,
        error: this.error$.value,
        errorContext: this.errorContext$.value,
        lastUpdated: this.cacheTimestamp,
        isFallbackMode: this.isFallbackMode$.value,
        retryAttempts: this.retryAttempts$.value,
        isRetrying: this.isRetrying$.value
      }))
    );
  }

  /**
   * Get token limits for a specific field type
   */
  getFieldLimit(fieldType: SystemPromptFieldType): Observable<FieldTokenLimit> {
    this.ensureFreshCache();
    return this.tokenLimits$.pipe(
      map(limits => {
        const limitsToUse = limits || this.defaultLimits;
        const limit = this.mapFieldTypeToLimit(fieldType, limitsToUse);

        return {
          fieldType,
          limit,
          warningThreshold: Math.floor(limit * 0.8), // 80% warning
          criticalThreshold: Math.floor(limit * 0.9)  // 90% critical
        };
      })
    );
  }

  /**
   * Get all field limits at once
   */
  getAllFieldLimits(): Observable<FieldTokenLimit[]> {
    this.ensureFreshCache();
    return this.tokenLimits$.pipe(
      map(limits => {
        const limitsToUse = limits || this.defaultLimits;
        const fieldTypes: SystemPromptFieldType[] = ['mainPrefix', 'mainSuffix', 'assistantPrompt', 'editorPrompt', 'raterSystemPrompt'];

        return fieldTypes.map(fieldType => {
          const limit = this.mapFieldTypeToLimit(fieldType, limitsToUse);
          return {
            fieldType,
            limit,
            warningThreshold: Math.floor(limit * 0.8),
            criticalThreshold: Math.floor(limit * 0.9)
          };
        });
      })
    );
  }

  /**
   * Get the current token limits (may be null if not loaded)
   */
  getCurrentLimits(): TokenLimitsResponse | null {
    return this.tokenLimits$.value;
  }

  /**
   * Check if limits are currently being loaded
   */
  isLoading(): Observable<boolean> {
    return this.isLoading$.asObservable();
  }

  /**
   * Refresh token limits from the backend
   */
  refreshLimits(): Observable<TokenLimitsResponse> {
    this.loadTokenLimits();
    return this.tokenLimits$.pipe(
      map(limits => limits || this.defaultLimits)
    );
  }

  /**
   * Clear the cached token limits and reset to null
   */
  clearCache(): void {
    this.tokenLimits$.next(null);
    this.cacheTimestamp = null;
    this.resetErrorState();
  }

  /**
   * Manually retry loading token limits
   */
  retryLoadLimits(): Observable<TokenLimitsResponse> {
    this.resetErrorState();
    this.loadTokenLimits();
    return this.tokenLimits$.pipe(
      map(limits => limits || this.defaultLimits)
    );
  }

  /**
   * Get current error context
   */
  getErrorContext(): ErrorContext | null {
    return this.errorContext$.value;
  }

  /**
   * Check if currently in fallback mode
   */
  isInFallbackMode(): boolean {
    return this.isFallbackMode$.value;
  }

  /**
   * Get current retry attempts count
   */
  getRetryAttempts(): number {
    return this.retryAttempts$.value;
  }

  /**
   * Load token limits from the backend with exponential backoff retry
   */
  private loadTokenLimits(): void {
    this.isLoading$.next(true);
    this.error$.next(null);
    this.errorContext$.next(null);

    this.http.get<TokenLimitsResponse>(`${this.baseUrl}/limits`)
      .pipe(
        retryWhen(errors =>
          errors.pipe(
            mergeMap((error, index) => {
              const attempt = index + 1;
              this.retryAttempts$.next(attempt);

              if (attempt > RETRY_CONFIG.maxRetries) {
                return throwError(error);
              }

              this.isRetrying$.next(true);
              const delay = calculateBackoffDelay(attempt);
              console.log(`Retrying token limits request (attempt ${attempt}/${RETRY_CONFIG.maxRetries}) after ${delay}ms`);

              return timer(delay);
            })
          )
        ),
        catchError(error => {
          console.warn('Failed to load token limits from backend after retries, using fallback:', error);

          const errorContext = this.createErrorContextFromHttpError(error);
          this.handleLoadError(errorContext);

          return of(this.defaultLimits);
        })
      )
      .subscribe({
        next: (limits) => {
          this.handleLoadSuccess(limits);
        },
        error: (error) => {
          console.error('Unexpected error loading token limits:', error);
          const errorContext = createErrorContext(
            ErrorType.UNKNOWN,
            ErrorSeverity.MEDIUM,
            ERROR_MESSAGES.LIMITS_UNAVAILABLE,
            [RecoveryAction.RETRY, RecoveryAction.USE_FALLBACK],
            error.message,
            'TokenLimitsService.loadTokenLimits'
          );
          this.handleLoadError(errorContext);
          this.tokenLimits$.next(this.defaultLimits);
        }
      });
  }

  /**
   * Check if the cache is expired
   */
  private isCacheExpired(): boolean {
    if (!this.cacheTimestamp) {
      return true;
    }
    return Date.now() - this.cacheTimestamp > this.cacheTTL;
  }

  /**
   * Ensure cache is fresh, reload if expired
   */
  private ensureFreshCache(): void {
    if (this.isCacheExpired() && !this.isLoading$.value) {
      this.loadTokenLimits();
    }
  }

  /**
   * Map field type to the corresponding limit in TokenLimitsResponse
   */
  private mapFieldTypeToLimit(fieldType: SystemPromptFieldType, limits: TokenLimitsResponse): number {
    switch (fieldType) {
      case 'mainPrefix':
        return limits.system_prompt_prefix;
      case 'mainSuffix':
        return limits.system_prompt_suffix;
      case 'assistantPrompt':
        return limits.writing_assistant_prompt;
      case 'editorPrompt':
        return limits.writing_editor_prompt;
      case 'raterSystemPrompt':
        return limits.writing_assistant_prompt; // Use same limit as assistant prompt for raters
      default:
        return 500; // Default fallback
    }
  }

  /**
   * Handle successful token limits load
   */
  private handleLoadSuccess(limits: TokenLimitsResponse): void {
    this.tokenLimits$.next(limits);
    this.cacheTimestamp = Date.now();
    this.isLoading$.next(false);
    this.isRetrying$.next(false);
    this.isFallbackMode$.next(false);
    this.resetErrorState();
  }

  /**
   * Handle token limits load error
   */
  private handleLoadError(errorContext: ErrorContext): void {
    this.error$.next(errorContext.message);
    this.errorContext$.next(errorContext);
    this.isLoading$.next(false);
    this.isRetrying$.next(false);
    this.isFallbackMode$.next(true);
    this.cacheTimestamp = Date.now(); // Cache the fallback limits
  }

  /**
   * Reset error state
   */
  private resetErrorState(): void {
    this.error$.next(null);
    this.errorContext$.next(null);
    this.retryAttempts$.next(0);
    this.isRetrying$.next(false);
  }

  /**
   * Create error context from HTTP error
   */
  private createErrorContextFromHttpError(error: any): ErrorContext {
    if (error instanceof HttpErrorResponse) {
      switch (error.status) {
        case 0:
          return createErrorContext(
            ErrorType.NETWORK,
            ErrorSeverity.MEDIUM,
            ERROR_MESSAGES.NETWORK_ERROR,
            [RecoveryAction.RETRY, RecoveryAction.USE_FALLBACK],
            `Network error: ${error.message}`,
            'TokenLimitsService'
          );
        case 408:
        case 504:
          return createErrorContext(
            ErrorType.TIMEOUT,
            ErrorSeverity.MEDIUM,
            ERROR_MESSAGES.TIMEOUT_ERROR,
            [RecoveryAction.RETRY, RecoveryAction.USE_FALLBACK],
            `Timeout error: ${error.message}`,
            'TokenLimitsService'
          );
        case 500:
        case 502:
        case 503:
          return createErrorContext(
            ErrorType.SERVER,
            ErrorSeverity.MEDIUM,
            ERROR_MESSAGES.SERVER_ERROR,
            [RecoveryAction.RETRY, RecoveryAction.USE_FALLBACK],
            `Server error: ${error.status} ${error.message}`,
            'TokenLimitsService'
          );
        default:
          return createErrorContext(
            ErrorType.UNAVAILABLE,
            ErrorSeverity.MEDIUM,
            ERROR_MESSAGES.API_UNAVAILABLE,
            [RecoveryAction.RETRY, RecoveryAction.USE_FALLBACK],
            `HTTP ${error.status}: ${error.message}`,
            'TokenLimitsService'
          );
      }
    }

    return createErrorContext(
      ErrorType.UNKNOWN,
      ErrorSeverity.MEDIUM,
      ERROR_MESSAGES.LIMITS_UNAVAILABLE,
      [RecoveryAction.RETRY, RecoveryAction.USE_FALLBACK],
      error?.message || 'Unknown error',
      'TokenLimitsService'
    );
  }
}
