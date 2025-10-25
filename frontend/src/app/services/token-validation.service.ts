import { Injectable } from '@angular/core';
import { Observable, combineLatest, of } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
import { TokenLimitsService, SystemPromptFieldType, FieldTokenLimit } from './token-limits.service';
import { TokenCountingService } from './token-counting.service';
import { 
  TokenValidationResult, 
  TokenValidationStatus, 
  TokenValidationConfig, 
  DEFAULT_VALIDATION_CONFIG,
  TokenValidationUtils 
} from '../models/token-validation.model';
import { ContentType, CountingStrategy } from '../models/token.model';
import { TokenCounterStatus } from '../models/token-counter.model';

/**
 * Token validation thresholds configuration
 */
export interface TokenValidationThresholds {
  /** Warning threshold as percentage (default: 0.7 = 70%) */
  warningThreshold: number;
  /** Danger threshold as percentage (default: 0.9 = 90%) */
  dangerThreshold: number;
}

/**
 * Field validation state for form-level validation
 */
export interface FieldValidationState {
  [fieldName: string]: TokenValidationResult;
}

/**
 * Default validation thresholds (70%, 90%)
 */
export const DEFAULT_VALIDATION_THRESHOLDS: TokenValidationThresholds = {
  warningThreshold: 0.7,
  dangerThreshold: 0.9
};

/**
 * Service for validating token counts against field-specific limits.
 * 
 * This service combines token counting with limit checking to provide
 * comprehensive validation results for system prompt fields.
 */
@Injectable({
  providedIn: 'root'
})
export class TokenValidationService {
  
  constructor(
    private tokenLimitsService: TokenLimitsService,
    private tokenCountingService: TokenCountingService
  ) {}

  /**
   * Validate token count against limits with configurable thresholds
   */
  validateTokenCount(
    current: number, 
    limit: number, 
    config?: Partial<TokenValidationConfig>
  ): TokenValidationResult {
    const validationConfig = { ...DEFAULT_VALIDATION_CONFIG, ...config };
    const thresholds = {
      warningThreshold: limit * DEFAULT_VALIDATION_THRESHOLDS.warningThreshold,
      dangerThreshold: limit * DEFAULT_VALIDATION_THRESHOLDS.dangerThreshold
    };

    const status = this.calculateStatus(current, limit, DEFAULT_VALIDATION_THRESHOLDS);
    const percentage = TokenValidationUtils.calculatePercentage(current, limit);
    const message = this.getValidationMessage(status, current, limit);
    const isValid = TokenValidationUtils.isValidForSubmission(
      { status } as TokenValidationResult,
      validationConfig
    );
    const excessTokens = Math.max(0, current - limit);

    return {
      status,
      currentTokens: current,
      maxTokens: limit,
      warningThreshold: thresholds.warningThreshold,
      criticalThreshold: thresholds.dangerThreshold,
      percentage,
      message,
      isValid,
      metadata: {
        excessTokens: excessTokens > 0 ? excessTokens : undefined,
        timestamp: new Date()
      }
    };
  }

  /**
   * Calculate validation status based on token counts and limits
   */
  calculateStatus(
    current: number, 
    limit: number, 
    thresholds: TokenValidationThresholds
  ): TokenValidationStatus {
    if (current < 0 || limit <= 0) {
      return TokenValidationStatus.ERROR;
    }

    if (current > limit) {
      return TokenValidationStatus.INVALID;
    }

    const warningThreshold = limit * thresholds.warningThreshold;
    const dangerThreshold = limit * thresholds.dangerThreshold;

    if (current >= dangerThreshold) {
      return TokenValidationStatus.CRITICAL;
    }

    if (current >= warningThreshold) {
      return TokenValidationStatus.WARNING;
    }

    return TokenValidationStatus.VALID;
  }

  /**
   * Get user-friendly validation message for status
   */
  getValidationMessage(
    status: TokenValidationStatus, 
    current: number, 
    limit: number
  ): string {
    const percentage = TokenValidationUtils.calculatePercentage(current, limit);
    const excessTokens = Math.max(0, current - limit);
    const remainingTokens = Math.max(0, limit - current);

    switch (status) {
      case TokenValidationStatus.VALID:
        return `${current}/${limit} tokens (${percentage}%) - ${remainingTokens} tokens remaining`;
      case TokenValidationStatus.WARNING:
        return `${current}/${limit} tokens (${percentage}%) - Approaching limit, ${remainingTokens} tokens remaining`;
      case TokenValidationStatus.CRITICAL:
        return `${current}/${limit} tokens (${percentage}%) - Near limit, ${remainingTokens} tokens remaining`;
      case TokenValidationStatus.INVALID:
        return `${current}/${limit} tokens (${percentage}%) - Exceeded by ${excessTokens} tokens`;
      case TokenValidationStatus.LOADING:
        return 'Counting tokens...';
      case TokenValidationStatus.ERROR:
        return 'Unable to validate token count';
      default:
        return 'Unknown validation status';
    }
  }

  /**
   * Check if form can be saved based on validation results
   */
  canSave(validationResults: FieldValidationState): boolean {
    const results = Object.values(validationResults);
    
    // Cannot save if any field is in error or loading state
    if (results.some(result => 
      result.status === TokenValidationStatus.ERROR || 
      result.status === TokenValidationStatus.LOADING
    )) {
      return false;
    }

    // Cannot save if any field exceeds limits (unless explicitly allowed)
    if (results.some(result => 
      result.status === TokenValidationStatus.INVALID && !result.isValid
    )) {
      return false;
    }

    return true;
  }

  /**
   * Map TokenValidationStatus to TokenCounterStatus
   */
  mapToTokenCounterStatus(status: TokenValidationStatus): TokenCounterStatus {
    switch (status) {
      case TokenValidationStatus.VALID:
        return TokenCounterStatus.GOOD;
      case TokenValidationStatus.WARNING:
        return TokenCounterStatus.WARNING;
      case TokenValidationStatus.CRITICAL:
        return TokenCounterStatus.WARNING;
      case TokenValidationStatus.INVALID:
        return TokenCounterStatus.OVER_LIMIT;
      case TokenValidationStatus.LOADING:
        return TokenCounterStatus.LOADING;
      case TokenValidationStatus.ERROR:
        return TokenCounterStatus.ERROR;
      default:
        return TokenCounterStatus.ERROR;
    }
  }

  /**
   * Validate text against field-specific token limits
   */
  validateField(
    text: string,
    fieldType: SystemPromptFieldType,
    config: Partial<TokenValidationConfig> = {}
  ): Observable<TokenValidationResult> {
    const validationConfig = { ...DEFAULT_VALIDATION_CONFIG, ...config };
    
    // Get field limits and count tokens in parallel
    const fieldLimit$ = this.tokenLimitsService.getFieldLimit(fieldType);
    const tokenCount$ = this.tokenCountingService.countTokensDebounced(
      text,
      ContentType.SYSTEM_PROMPT,
      CountingStrategy.EXACT
    );

    return combineLatest([fieldLimit$, tokenCount$]).pipe(
      map(([fieldLimit, tokenResult]) => {
        return this.createValidationResult(
          tokenResult.token_count,
          fieldLimit,
          validationConfig,
          fieldType,
          text
        );
      }),
      catchError(error => {
        console.error('Token validation error:', error);
        return of(this.createErrorResult(fieldType, validationConfig));
      })
    );
  }

  /**
   * Validate text with immediate token counting (no debouncing)
   */
  validateFieldImmediate(
    text: string,
    fieldType: SystemPromptFieldType,
    config: Partial<TokenValidationConfig> = {}
  ): Observable<TokenValidationResult> {
    const validationConfig = { ...DEFAULT_VALIDATION_CONFIG, ...config };
    
    const fieldLimit$ = this.tokenLimitsService.getFieldLimit(fieldType);
    const tokenCount$ = this.tokenCountingService.countTokens(
      text,
      ContentType.SYSTEM_PROMPT,
      CountingStrategy.EXACT
    );

    return combineLatest([fieldLimit$, tokenCount$]).pipe(
      map(([fieldLimit, tokenResult]) => {
        return this.createValidationResult(
          tokenResult.token_count,
          fieldLimit,
          validationConfig,
          fieldType,
          text
        );
      }),
      catchError(error => {
        console.error('Token validation error:', error);
        return of(this.createErrorResult(fieldType, validationConfig));
      })
    );
  }

  /**
   * Validate multiple fields at once
   */
  validateMultipleFields(
    fields: Array<{ text: string; fieldType: SystemPromptFieldType }>,
    config: Partial<TokenValidationConfig> = {}
  ): Observable<TokenValidationResult[]> {
    const validationConfig = { ...DEFAULT_VALIDATION_CONFIG, ...config };
    
    const validations = fields.map(field => 
      this.validateField(field.text, field.fieldType, validationConfig)
    );
    
    return combineLatest(validations);
  }

  /**
   * Check if a field value is valid for form submission
   */
  isValidForSubmission(
    text: string,
    fieldType: SystemPromptFieldType,
    config: Partial<TokenValidationConfig> = {}
  ): Observable<boolean> {
    return this.validateFieldImmediate(text, fieldType, config).pipe(
      map(result => TokenValidationUtils.isValidForSubmission(result, { ...DEFAULT_VALIDATION_CONFIG, ...config }))
    );
  }

  /**
   * Get validation status for text without full validation result
   */
  getValidationStatus(
    text: string,
    fieldType: SystemPromptFieldType
  ): Observable<TokenValidationStatus> {
    return this.validateField(text, fieldType).pipe(
      map(result => result.status)
    );
  }

  /**
   * Create a validation result from token count and field limits
   */
  private createValidationResult(
    tokenCount: number,
    fieldLimit: FieldTokenLimit,
    config: TokenValidationConfig,
    fieldType: SystemPromptFieldType,
    text: string
  ): TokenValidationResult {
    const status = TokenValidationUtils.calculateStatus(
      tokenCount,
      fieldLimit.limit,
      fieldLimit.warningThreshold,
      fieldLimit.criticalThreshold
    );
    
    const percentage = TokenValidationUtils.calculatePercentage(tokenCount, fieldLimit.limit);
    const message = TokenValidationUtils.getStatusMessage(status, tokenCount, fieldLimit.limit, config);
    const isValid = TokenValidationUtils.isValidForSubmission(
      { status } as TokenValidationResult,
      config
    );
    
    const excessTokens = Math.max(0, tokenCount - fieldLimit.limit);
    
    return {
      status,
      currentTokens: tokenCount,
      maxTokens: fieldLimit.limit,
      warningThreshold: fieldLimit.warningThreshold,
      criticalThreshold: fieldLimit.criticalThreshold,
      percentage,
      message,
      isValid,
      metadata: {
        excessTokens: excessTokens > 0 ? excessTokens : undefined,
        fieldType,
        timestamp: new Date()
      }
    };
  }

  /**
   * Create an error validation result
   */
  private createErrorResult(
    fieldType: SystemPromptFieldType,
    config: TokenValidationConfig
  ): TokenValidationResult {
    return {
      status: TokenValidationStatus.ERROR,
      currentTokens: 0,
      maxTokens: 0,
      warningThreshold: 0,
      criticalThreshold: 0,
      percentage: 0,
      message: config.messages?.error || 'Unable to validate token count',
      isValid: false,
      metadata: {
        fieldType,
        timestamp: new Date()
      }
    };
  }

  /**
   * Create a loading validation result
   */
  createLoadingResult(fieldType: SystemPromptFieldType): TokenValidationResult {
    return {
      status: TokenValidationStatus.LOADING,
      currentTokens: 0,
      maxTokens: 0,
      warningThreshold: 0,
      criticalThreshold: 0,
      percentage: 0,
      message: DEFAULT_VALIDATION_CONFIG.messages?.loading || 'Counting tokens...',
      isValid: false,
      metadata: {
        fieldType,
        timestamp: new Date()
      }
    };
  }
}
