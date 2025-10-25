import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { BehaviorSubject, Observable, Subject, throwError, timer, EMPTY } from 'rxjs';
import {
  debounceTime,
  distinctUntilChanged,
  switchMap,
  catchError,
  retry,
  retryWhen,
  delay,
  take,
  shareReplay,
  tap,
  map,
  finalize
} from 'rxjs/operators';
// Note: Using simple hash function for browser compatibility
// In production, consider using a more robust hashing library

import {
  TokenCountRequest,
  TokenCountResponse,
  TokenCountRequestItem,
  TokenCountResultItem,
  TokenCountError,
  TokenCountLoadingState,
  TokenCountCacheEntry,
  TokenCountingServiceConfig,
  DEFAULT_TOKEN_COUNTING_CONFIG,
  ContentType,
  CountingStrategy,
  BatchProcessingOptions,
  BatchProgress
} from '../models/token.model';

/**
 * Service for handling token counting API requests with debouncing, caching, and error handling.
 * 
 * Features:
 * - Debounced API calls (configurable delay)
 * - Client-side caching for identical content
 * - Loading state management
 * - Comprehensive error handling with retry logic
 * - Batch processing support
 * - Reactive observables for UI components
 */
@Injectable({
  providedIn: 'root'
})
export class TokenCountingService {
  private readonly baseUrl = 'http://localhost:8000/api/v1/tokens';
  private readonly config: TokenCountingServiceConfig;
  
  // Cache for storing token count results
  private readonly cache = new Map<string, TokenCountCacheEntry>();
  
  // Loading state management
  private readonly loadingState$ = new BehaviorSubject<TokenCountLoadingState>({
    isLoading: false,
    pendingRequests: 0
  });
  
  // Subject for debounced single text counting
  private readonly debouncedCountSubject$ = new Subject<{
    text: string;
    contentType?: ContentType;
    strategy?: CountingStrategy;
    observer: any;
  }>();
  
  // Batch processing queue
  private readonly batchQueue: Array<{
    item: TokenCountRequestItem;
    observer: any;
    timestamp: number;
  }> = [];
  
  private batchTimer?: any;

  constructor(
    private http: HttpClient,
    config?: Partial<TokenCountingServiceConfig>
  ) {
    this.config = { ...DEFAULT_TOKEN_COUNTING_CONFIG, ...config };
    this.setupDebouncedCounting();
  }

  /**
   * Get the current loading state as an observable
   */
  getLoadingState(): Observable<TokenCountLoadingState> {
    return this.loadingState$.asObservable();
  }

  /**
   * Count tokens for a single text with debouncing
   */
  countTokensDebounced(
    text: string,
    contentType?: ContentType,
    strategy: CountingStrategy = CountingStrategy.EXACT
  ): Observable<TokenCountResultItem> {
    return new Observable(observer => {
      this.debouncedCountSubject$.next({
        text,
        contentType,
        strategy,
        observer
      });
    });
  }

  /**
   * Count tokens for a single text immediately (no debouncing)
   */
  countTokens(
    text: string,
    contentType?: ContentType,
    strategy: CountingStrategy = CountingStrategy.EXACT
  ): Observable<TokenCountResultItem> {
    // Check cache first
    const cacheKey = this.generateCacheKey(text, contentType, strategy);
    const cached = this.getCachedResult(cacheKey);
    
    if (cached) {
      return new Observable(observer => {
        observer.next(cached.result);
        observer.complete();
      });
    }

    const request: TokenCountRequest = {
      texts: [{ text, content_type: contentType }],
      strategy,
      include_metadata: true
    };

    return this.makeTokenCountRequest(request).pipe(
      map(response => {
        if (response.results && response.results.length > 0) {
          const result = response.results[0];
          this.cacheResult(cacheKey, result);
          return result;
        }
        throw new Error('No results returned from token counting API');
      })
    );
  }

  /**
   * Count tokens for multiple texts in a batch
   */
  countTokensBatch(
    items: TokenCountRequestItem[],
    strategy: CountingStrategy = CountingStrategy.EXACT
  ): Observable<TokenCountResultItem[]> {
    if (items.length === 0) {
      return new Observable(observer => {
        observer.next([]);
        observer.complete();
      });
    }

    // Check cache for all items
    const results: TokenCountResultItem[] = [];
    const uncachedItems: TokenCountRequestItem[] = [];
    
    for (const item of items) {
      const cacheKey = this.generateCacheKey(item.text, item.content_type, strategy);
      const cached = this.getCachedResult(cacheKey);
      
      if (cached) {
        results.push(cached.result);
      } else {
        uncachedItems.push(item);
      }
    }

    // If all items are cached, return immediately
    if (uncachedItems.length === 0) {
      return new Observable(observer => {
        observer.next(results);
        observer.complete();
      });
    }

    // Make API request for uncached items
    const request: TokenCountRequest = {
      texts: uncachedItems,
      strategy,
      include_metadata: true
    };

    return this.makeTokenCountRequest(request).pipe(
      map(response => {
        // Cache new results
        if (response.results) {
          for (const result of response.results) {
            const cacheKey = this.generateCacheKey(result.text, result.content_type, strategy);
            this.cacheResult(cacheKey, result);
            results.push(result);
          }
        }
        
        return results;
      })
    );
  }

  /**
   * Add item to batch processing queue
   */
  countTokensBatched(
    text: string,
    contentType?: ContentType,
    strategy: CountingStrategy = CountingStrategy.EXACT,
    options?: BatchProcessingOptions
  ): Observable<TokenCountResultItem> {
    return new Observable(observer => {
      const item: TokenCountRequestItem = {
        text,
        content_type: contentType
      };

      this.batchQueue.push({
        item,
        observer,
        timestamp: Date.now()
      });

      this.processBatchQueue(options);
    });
  }

  /**
   * Clear the token count cache
   */
  clearCache(): void {
    this.cache.clear();
  }

  /**
   * Get cache statistics
   */
  getCacheStats(): {
    size: number;
    hitRate: number;
    totalHits: number;
  } {
    let totalHits = 0;
    let totalRequests = 0;

    for (const entry of this.cache.values()) {
      totalHits += entry.hitCount;
      totalRequests += entry.hitCount + 1; // +1 for the initial request
    }

    return {
      size: this.cache.size,
      hitRate: totalRequests > 0 ? totalHits / totalRequests : 0,
      totalHits
    };
  }

  /**
   * Setup debounced counting stream
   */
  private setupDebouncedCounting(): void {
    this.debouncedCountSubject$.pipe(
      debounceTime(this.config.debounceMs),
      distinctUntilChanged((prev, curr) => 
        prev.text === curr.text && 
        prev.contentType === curr.contentType && 
        prev.strategy === curr.strategy
      ),
      switchMap(({ text, contentType, strategy, observer }) => {
        return this.countTokens(text, contentType, strategy).pipe(
          tap(result => {
            observer.next(result);
            observer.complete();
          }),
          catchError(error => {
            observer.error(error);
            return EMPTY;
          })
        );
      })
    ).subscribe();
  }

  /**
   * Make HTTP request to token counting API
   */
  private makeTokenCountRequest(request: TokenCountRequest): Observable<TokenCountResponse> {
    this.updateLoadingState(true);

    return this.http.post<TokenCountResponse>(`${this.baseUrl}/count`, request).pipe(
      retryWhen(errors =>
        errors.pipe(
          take(this.config.maxRetries),
          delay(this.config.retryDelayMs)
        )
      ),
      catchError(this.handleError.bind(this)),
      finalize(() => this.updateLoadingState(false)),
      shareReplay(1)
    );
  }

  /**
   * Handle HTTP errors with appropriate fallbacks
   */
  private handleError(error: HttpErrorResponse): Observable<never> {
    let errorMessage = 'An error occurred while counting tokens';
    let errorCode = 'UNKNOWN_ERROR';

    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `Client error: ${error.error.message}`;
      errorCode = 'CLIENT_ERROR';
    } else {
      // Server-side error
      switch (error.status) {
        case 400:
          errorMessage = 'Invalid request format';
          errorCode = 'BAD_REQUEST';
          break;
        case 422:
          errorMessage = 'Validation error in request data';
          errorCode = 'VALIDATION_ERROR';
          break;
        case 500:
          errorMessage = 'Server error occurred';
          errorCode = 'SERVER_ERROR';
          break;
        case 0:
          errorMessage = 'Network error - please check your connection';
          errorCode = 'NETWORK_ERROR';
          break;
        default:
          errorMessage = `Server returned error code: ${error.status}`;
          errorCode = 'HTTP_ERROR';
      }
    }

    const tokenError: TokenCountError = {
      message: errorMessage,
      code: errorCode,
      details: {
        status: error.status,
        statusText: error.statusText,
        url: error.url
      }
    };

    console.error('Token counting error:', tokenError);
    return throwError(() => tokenError);
  }

  /**
   * Generate cache key for a token count request
   */
  private generateCacheKey(
    text: string,
    contentType?: ContentType,
    strategy?: CountingStrategy
  ): string {
    const key = `${text}|${contentType || 'unknown'}|${strategy || 'exact'}`;
    // Simple hash function for browser compatibility
    return this.simpleHash(key);
  }

  /**
   * Simple hash function for browser compatibility
   */
  private simpleHash(str: string): string {
    let hash = 0;
    if (str.length === 0) return hash.toString();
    
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    
    return Math.abs(hash).toString(36);
  }

  /**
   * Get cached result if available and not expired
   */
  private getCachedResult(cacheKey: string): TokenCountCacheEntry | null {
    const entry = this.cache.get(cacheKey);
    
    if (!entry) {
      return null;
    }

    // Check if cache entry is expired
    if (Date.now() - entry.timestamp > this.config.cacheTtlMs) {
      this.cache.delete(cacheKey);
      return null;
    }

    // Increment hit count
    entry.hitCount++;
    return entry;
  }

  /**
   * Cache a token count result
   */
  private cacheResult(cacheKey: string, result: TokenCountResultItem): void {
    // Implement LRU eviction if cache is full
    if (this.cache.size >= this.config.maxCacheSize) {
      const oldestKey = this.cache.keys().next().value;
      this.cache.delete(oldestKey);
    }

    const entry: TokenCountCacheEntry = {
      result,
      timestamp: Date.now(),
      hitCount: 0
    };

    this.cache.set(cacheKey, entry);
  }

  /**
   * Update loading state
   */
  private updateLoadingState(isLoading: boolean, operation?: string): void {
    const currentState = this.loadingState$.value;
    const pendingRequests = isLoading 
      ? currentState.pendingRequests + 1 
      : Math.max(0, currentState.pendingRequests - 1);

    this.loadingState$.next({
      isLoading: pendingRequests > 0,
      pendingRequests,
      operation
    });
  }

  /**
   * Process batch queue based on strategy
   */
  private processBatchQueue(options?: BatchProcessingOptions): void {
    const strategy = options?.strategy || 'time-based';
    const maxWaitMs = options?.maxWaitMs || 100;
    const maxBatchSize = options?.maxBatchSize || this.config.maxBatchSize;

    if (strategy === 'immediate') {
      this.flushBatchQueue();
    } else if (strategy === 'size-based') {
      if (this.batchQueue.length >= maxBatchSize) {
        this.flushBatchQueue();
      }
    } else { // time-based
      if (!this.batchTimer) {
        this.batchTimer = setTimeout(() => {
          this.flushBatchQueue();
        }, maxWaitMs);
      }
    }
  }

  /**
   * Flush the batch queue and process all items
   */
  private flushBatchQueue(): void {
    if (this.batchTimer) {
      clearTimeout(this.batchTimer);
      this.batchTimer = undefined;
    }

    if (this.batchQueue.length === 0) {
      return;
    }

    const items = this.batchQueue.map(entry => entry.item);
    const observers = this.batchQueue.map(entry => entry.observer);
    
    // Clear the queue
    this.batchQueue.length = 0;

    // Process the batch
    this.countTokensBatch(items).subscribe({
      next: (results) => {
        // Match results to observers
        for (let i = 0; i < Math.min(results.length, observers.length); i++) {
          observers[i].next(results[i]);
          observers[i].complete();
        }
      },
      error: (error) => {
        // Notify all observers of the error
        observers.forEach(observer => observer.error(error));
      }
    });
  }
}
