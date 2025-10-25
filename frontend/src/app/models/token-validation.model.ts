/**
 * Token validation status levels
 */
export enum TokenValidationStatus {
  /** Token count is within safe limits */
  VALID = 'valid',
  /** Token count is approaching limits (warning threshold) */
  WARNING = 'warning', 
  /** Token count is near limits (critical threshold) */
  CRITICAL = 'critical',
  /** Token count exceeds limits */
  INVALID = 'invalid',
  /** Validation is in progress */
  LOADING = 'loading',
  /** Validation failed due to error */
  ERROR = 'error'
}

/**
 * Token validation result
 */
export interface TokenValidationResult {
  /** Validation status */
  status: TokenValidationStatus;
  /** Current token count */
  currentTokens: number;
  /** Maximum allowed tokens */
  maxTokens: number;
  /** Warning threshold */
  warningThreshold: number;
  /** Critical threshold */
  criticalThreshold: number;
  /** Percentage of limit used */
  percentage: number;
  /** Validation message for user display */
  message: string;
  /** Whether the field value is valid for form submission */
  isValid: boolean;
  /** Additional metadata */
  metadata?: {
    /** Excess tokens when over limit */
    excessTokens?: number;
    /** Field type being validated */
    fieldType?: string;
    /** Timestamp of validation */
    timestamp?: Date;
  };
}

/**
 * Validation configuration options
 */
export interface TokenValidationConfig {
  /** Warning threshold as percentage (default: 0.8 = 80%) */
  warningThreshold: number;
  /** Critical threshold as percentage (default: 0.9 = 90%) */
  criticalThreshold: number;
  /** Whether to allow submissions when over limit (default: false) */
  allowOverLimit: boolean;
  /** Custom validation messages */
  messages?: {
    valid?: string;
    warning?: string;
    critical?: string;
    invalid?: string;
    loading?: string;
    error?: string;
  };
}

/**
 * Default validation configuration
 */
export const DEFAULT_VALIDATION_CONFIG: TokenValidationConfig = {
  warningThreshold: 0.8,
  criticalThreshold: 0.9,
  allowOverLimit: false,
  messages: {
    valid: 'Token count is within limits',
    warning: 'Approaching token limit',
    critical: 'Near token limit',
    invalid: 'Token limit exceeded',
    loading: 'Counting tokens...',
    error: 'Unable to validate token count'
  }
};

/**
 * Utility functions for token validation
 */
export class TokenValidationUtils {
  /**
   * Calculate validation status based on token count and thresholds
   */
  static calculateStatus(
    currentTokens: number,
    maxTokens: number,
    warningThreshold: number,
    criticalThreshold: number
  ): TokenValidationStatus {
    if (currentTokens > maxTokens) {
      return TokenValidationStatus.INVALID;
    }
    
    if (currentTokens >= criticalThreshold) {
      return TokenValidationStatus.CRITICAL;
    }
    
    if (currentTokens >= warningThreshold) {
      return TokenValidationStatus.WARNING;
    }
    
    return TokenValidationStatus.VALID;
  }

  /**
   * Calculate percentage of limit used
   */
  static calculatePercentage(currentTokens: number, maxTokens: number): number {
    if (maxTokens === 0) return 0;
    return Math.round((currentTokens / maxTokens) * 100);
  }

  /**
   * Get user-friendly message for validation status
   */
  static getStatusMessage(
    status: TokenValidationStatus,
    currentTokens: number,
    maxTokens: number,
    config: TokenValidationConfig = DEFAULT_VALIDATION_CONFIG
  ): string {
    const percentage = this.calculatePercentage(currentTokens, maxTokens);
    const excessTokens = Math.max(0, currentTokens - maxTokens);
    
    switch (status) {
      case TokenValidationStatus.VALID:
        return config.messages?.valid || `${currentTokens}/${maxTokens} tokens (${percentage}%)`;
      case TokenValidationStatus.WARNING:
        return config.messages?.warning || `${currentTokens}/${maxTokens} tokens (${percentage}%) - Approaching limit`;
      case TokenValidationStatus.CRITICAL:
        return config.messages?.critical || `${currentTokens}/${maxTokens} tokens (${percentage}%) - Near limit`;
      case TokenValidationStatus.INVALID:
        return config.messages?.invalid || `${currentTokens}/${maxTokens} tokens (${percentage}%) - ${excessTokens} tokens over limit`;
      case TokenValidationStatus.LOADING:
        return config.messages?.loading || 'Counting tokens...';
      case TokenValidationStatus.ERROR:
        return config.messages?.error || 'Unable to validate token count';
      default:
        return 'Unknown validation status';
    }
  }

  /**
   * Check if validation result allows form submission
   */
  static isValidForSubmission(
    result: TokenValidationResult,
    config: TokenValidationConfig = DEFAULT_VALIDATION_CONFIG
  ): boolean {
    if (result.status === TokenValidationStatus.ERROR || result.status === TokenValidationStatus.LOADING) {
      return false;
    }
    
    if (result.status === TokenValidationStatus.INVALID && !config.allowOverLimit) {
      return false;
    }
    
    return true;
  }

  /**
   * Get CSS class for validation status
   */
  static getStatusClass(status: TokenValidationStatus): string {
    switch (status) {
      case TokenValidationStatus.VALID:
        return 'token-validation--valid';
      case TokenValidationStatus.WARNING:
        return 'token-validation--warning';
      case TokenValidationStatus.CRITICAL:
        return 'token-validation--critical';
      case TokenValidationStatus.INVALID:
        return 'token-validation--invalid';
      case TokenValidationStatus.LOADING:
        return 'token-validation--loading';
      case TokenValidationStatus.ERROR:
        return 'token-validation--error';
      default:
        return 'token-validation--unknown';
    }
  }

  /**
   * Get icon for validation status
   */
  static getStatusIcon(status: TokenValidationStatus): string {
    switch (status) {
      case TokenValidationStatus.VALID:
        return '✅';
      case TokenValidationStatus.WARNING:
        return '⚠️';
      case TokenValidationStatus.CRITICAL:
        return '🟠';
      case TokenValidationStatus.INVALID:
        return '❌';
      case TokenValidationStatus.LOADING:
        return '⏳';
      case TokenValidationStatus.ERROR:
        return '⚠️';
      default:
        return '❓';
    }
  }
}
