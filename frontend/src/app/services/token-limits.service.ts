import { Injectable } from '@angular/core';
import { Observable, BehaviorSubject, of, timer } from 'rxjs';
import { map, catchError, switchMap, startWith, retry, delay } from 'rxjs/operators';
import { HttpClient } from '@angular/common/http';
import { TokenLimits, RecommendedLimits, TokenStrategiesResponse } from '../models/token-limits.model';

/**
 * Field types for system prompt components
 */
export type SystemPromptFieldType = 'mainPrefix' | 'mainSuffix' | 'assistantPrompt' | 'editorPrompt';

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
  limits: TokenLimits | null;
  /** Whether limits are currently being loaded */
  isLoading: boolean;
  /** Error message if loading failed */
  error: string | null;
  /** Timestamp when limits were last loaded */
  lastUpdated: number | null;
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
  private tokenLimits$ = new BehaviorSubject<TokenLimits | null>(null);
  private isLoading$ = new BehaviorSubject<boolean>(false);
  private error$ = new BehaviorSubject<string | null>(null);
  private cacheTimestamp: number | null = null;
  private readonly cacheTTL: number = 5 * 60 * 1000; // 5 minutes in milliseconds
  
  // Default limits as fallback
  private readonly defaultLimits: RecommendedLimits = {
    system_prompt_prefix: 500,
    system_prompt_suffix: 500,
    writing_assistant_prompt: 1000,
    writing_editor_prompt: 1000
  };

  constructor(private http: HttpClient) {
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
        lastUpdated: this.cacheTimestamp
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
        const recommendedLimits = limits?.recommended_limits || this.defaultLimits;
        const limit = this.mapFieldTypeToLimit(fieldType, recommendedLimits);
        
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
        const recommendedLimits = limits?.recommended_limits || this.defaultLimits;
        const fieldTypes: SystemPromptFieldType[] = ['mainPrefix', 'mainSuffix', 'assistantPrompt', 'editorPrompt'];
        
        return fieldTypes.map(fieldType => {
          const limit = this.mapFieldTypeToLimit(fieldType, recommendedLimits);
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
  getCurrentLimits(): TokenLimits | null {
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
  refreshLimits(): Observable<TokenLimits> {
    this.loadTokenLimits();
    return this.tokenLimits$.pipe(
      map(limits => limits || this.createDefaultTokenLimits())
    );
  }

  /**
   * Clear the cached token limits and reset to null
   */
  clearCache(): void {
    this.tokenLimits$.next(null);
    this.cacheTimestamp = null;
  }

  /**
   * Load token limits from the backend
   */
  private loadTokenLimits(): void {
    this.isLoading$.next(true);
    this.error$.next(null);
    
    this.http.get<TokenStrategiesResponse>(`${this.baseUrl}/strategies`)
      .pipe(
        retry({ count: 3, delay: 1000 }), // Retry up to 3 times with 1 second delay
        map(response => response.token_limits),
        catchError(error => {
          console.warn('Failed to load token limits from backend after retries, using defaults:', error);
          this.error$.next('Failed to load token limits from backend, using defaults');
          return of(this.createDefaultTokenLimits());
        })
      )
      .subscribe({
        next: (limits) => {
          this.tokenLimits$.next(limits);
          this.cacheTimestamp = Date.now();
          this.isLoading$.next(false);
        },
        error: (error) => {
          console.error('Error loading token limits:', error);
          this.error$.next('Error loading token limits');
          this.tokenLimits$.next(this.createDefaultTokenLimits());
          this.cacheTimestamp = Date.now();
          this.isLoading$.next(false);
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
   * Map field type to the corresponding limit in RecommendedLimits
   */
  private mapFieldTypeToLimit(fieldType: SystemPromptFieldType, limits: RecommendedLimits): number {
    switch (fieldType) {
      case 'mainPrefix':
        return limits.system_prompt_prefix;
      case 'mainSuffix':
        return limits.system_prompt_suffix;
      case 'assistantPrompt':
        return limits.writing_assistant_prompt;
      case 'editorPrompt':
        return limits.writing_editor_prompt;
      default:
        return 500; // Default fallback
    }
  }

  /**
   * Create default token limits when backend is unavailable
   */
  private createDefaultTokenLimits(): TokenLimits {
    return {
      llm_context_window: 8192,
      llm_max_generation: 2048,
      context_management: {
        max_context_tokens: 6144,
        buffer_tokens: 512,
        layer_limits: {
          system_instructions: 1024,
          immediate_instructions: 512,
          recent_story: 2048,
          character_scene_data: 1536,
          plot_world_summary: 1024
        }
      },
      recommended_limits: this.defaultLimits
    };
  }
}
