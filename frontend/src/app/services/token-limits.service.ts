import { Injectable } from '@angular/core';
import { Observable, BehaviorSubject, of } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
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
  
  // Cache for token limits
  private tokenLimits$ = new BehaviorSubject<TokenLimits | null>(null);
  private isLoading$ = new BehaviorSubject<boolean>(false);
  
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
   * Get token limits for a specific field type
   */
  getFieldLimit(fieldType: SystemPromptFieldType): Observable<FieldTokenLimit> {
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
   * Load token limits from the backend
   */
  private loadTokenLimits(): void {
    this.isLoading$.next(true);
    
    this.http.get<TokenStrategiesResponse>(`${this.baseUrl}/strategies`)
      .pipe(
        map(response => response.token_limits),
        catchError(error => {
          console.warn('Failed to load token limits from backend, using defaults:', error);
          return of(this.createDefaultTokenLimits());
        })
      )
      .subscribe({
        next: (limits) => {
          this.tokenLimits$.next(limits);
          this.isLoading$.next(false);
        },
        error: (error) => {
          console.error('Error loading token limits:', error);
          this.tokenLimits$.next(this.createDefaultTokenLimits());
          this.isLoading$.next(false);
        }
      });
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
