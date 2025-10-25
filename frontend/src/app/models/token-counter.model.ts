/**
 * TypeScript interfaces for the TokenCounter UI component.
 * 
 * These interfaces define the component's public API and internal state management.
 */

/**
 * Display modes supported by the TokenCounter component
 */
export enum TokenCounterDisplayMode {
  /** Detailed view with progress bars and full information */
  DETAILED = 'detailed',
  /** Compact inline view with minimal information */
  COMPACT = 'compact',
  /** Mobile-optimized responsive view */
  MOBILE = 'mobile'
}

/**
 * Token count status levels with associated colors and meanings
 */
export enum TokenCounterStatus {
  /** Token count is within safe limits (green) */
  GOOD = 'good',
  /** Token count is approaching limits (yellow/orange) */
  WARNING = 'warning',
  /** Token count exceeds limits (red) */
  OVER_LIMIT = 'over_limit',
  /** Loading state */
  LOADING = 'loading',
  /** Error state */
  ERROR = 'error'
}

/**
 * Configuration data for displaying token counts
 */
export interface TokenCounterData {
  /** Current token count */
  current: number;
  /** Maximum allowed tokens */
  limit: number;
  /** Optional warning threshold (defaults to 80% of limit) */
  warningThreshold?: number;
  /** Text content being counted (for caching/debugging) */
  text?: string;
  /** Additional metadata */
  metadata?: Record<string, any>;
}

/**
 * Configuration options for the TokenCounter component
 */
export interface TokenCounterConfig {
  /** Display mode to use */
  displayMode: TokenCounterDisplayMode;
  /** Whether to show the progress bar */
  showProgressBar?: boolean;
  /** Whether to show the token count numbers */
  showCount?: boolean;
  /** Whether to show the status text (Good, Warning, Over) */
  showStatus?: boolean;
  /** Whether to show percentage */
  showPercentage?: boolean;
  /** Custom CSS classes to apply */
  customClasses?: string[];
  /** Whether the component is disabled */
  disabled?: boolean;
  /** Accessibility label override */
  ariaLabel?: string;
}

/**
 * Event data emitted by the TokenCounter component
 */
export interface TokenCounterEvent {
  /** Type of event */
  type: 'click' | 'hover' | 'focus' | 'status_change';
  /** Current token data */
  data: TokenCounterData;
  /** Current status */
  status: TokenCounterStatus;
  /** Additional event data */
  metadata?: Record<string, any>;
}

/**
 * Internal state of the TokenCounter component
 */
export interface TokenCounterState {
  /** Current status */
  status: TokenCounterStatus;
  /** Progress percentage (0-100) */
  percentage: number;
  /** Whether component is in loading state */
  isLoading: boolean;
  /** Error message if in error state */
  errorMessage?: string;
  /** Calculated warning threshold */
  warningThreshold: number;
}

/**
 * Default configuration values
 */
export const DEFAULT_TOKEN_COUNTER_CONFIG: Partial<TokenCounterConfig> = {
  displayMode: TokenCounterDisplayMode.DETAILED,
  showProgressBar: true,
  showCount: true,
  showStatus: true,
  showPercentage: false,
  disabled: false
};

/**
 * Color scheme for different token counter statuses
 */
export const TOKEN_COUNTER_COLORS = {
  [TokenCounterStatus.GOOD]: {
    primary: '#4caf50',
    background: '#e8f5e8',
    text: '#2e7d32'
  },
  [TokenCounterStatus.WARNING]: {
    primary: '#ff9800',
    background: '#fff3e0',
    text: '#f57c00'
  },
  [TokenCounterStatus.OVER_LIMIT]: {
    primary: '#f44336',
    background: '#ffebee',
    text: '#d32f2f'
  },
  [TokenCounterStatus.LOADING]: {
    primary: '#2196f3',
    background: '#e3f2fd',
    text: '#1976d2'
  },
  [TokenCounterStatus.ERROR]: {
    primary: '#9e9e9e',
    background: '#f5f5f5',
    text: '#616161'
  }
};

/**
 * Utility functions for token counter calculations
 */
export class TokenCounterUtils {
  /**
   * Calculate the status based on current count and limits
   */
  static calculateStatus(current: number, limit: number, warningThreshold?: number): TokenCounterStatus {
    if (current < 0 || limit <= 0) {
      return TokenCounterStatus.ERROR;
    }
    
    const threshold = warningThreshold || (limit * 0.8);
    
    if (current > limit) {
      return TokenCounterStatus.OVER_LIMIT;
    } else if (current >= threshold) {
      return TokenCounterStatus.WARNING;
    } else {
      return TokenCounterStatus.GOOD;
    }
  }

  /**
   * Calculate progress percentage
   */
  static calculatePercentage(current: number, limit: number): number {
    if (limit <= 0) return 0;
    return Math.min(Math.round((current / limit) * 100), 100);
  }

  /**
   * Get status display text
   */
  static getStatusText(status: TokenCounterStatus): string {
    switch (status) {
      case TokenCounterStatus.GOOD:
        return 'Good';
      case TokenCounterStatus.WARNING:
        return 'High';
      case TokenCounterStatus.OVER_LIMIT:
        return 'Over!';
      case TokenCounterStatus.LOADING:
        return 'Loading...';
      case TokenCounterStatus.ERROR:
        return 'Error';
      default:
        return '';
    }
  }

  /**
   * Get status icon
   */
  static getStatusIcon(status: TokenCounterStatus): string {
    switch (status) {
      case TokenCounterStatus.GOOD:
        return '🟢';
      case TokenCounterStatus.WARNING:
        return '🟡';
      case TokenCounterStatus.OVER_LIMIT:
        return '🔴';
      case TokenCounterStatus.LOADING:
        return '⏳';
      case TokenCounterStatus.ERROR:
        return '❌';
      default:
        return '';
    }
  }

  /**
   * Format token count for display
   */
  static formatTokenCount(count: number): string {
    if (count >= 1000000) {
      return `${(count / 1000000).toFixed(1)}M`;
    } else if (count >= 1000) {
      return `${(count / 1000).toFixed(1)}K`;
    } else {
      return count.toString();
    }
  }
}
