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
