import { Component, Input, Output, EventEmitter, OnInit, OnChanges, SimpleChanges, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  TokenCounterData,
  TokenCounterConfig,
  TokenCounterEvent,
  TokenCounterState,
  TokenCounterDisplayMode,
  TokenCounterStatus,
  DEFAULT_TOKEN_COUNTER_CONFIG,
  TokenCounterUtils
} from '../../models/token-counter.model';

/**
 * TokenCounter UI Component
 * 
 * A reusable Angular component for displaying token counts with visual indicators,
 * progress bars, and status colors. Supports multiple display modes and accessibility features.
 * 
 * @example
 * ```html
 * <app-token-counter
 *   [data]="{ current: 1247, limit: 2000 }"
 *   [config]="{ displayMode: 'detailed', showProgressBar: true }"
 *   (interaction)="onTokenCounterInteraction($event)">
 * </app-token-counter>
 * ```
 */
@Component({
  selector: 'app-token-counter',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './token-counter.component.html',
  styleUrl: './token-counter.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class TokenCounterComponent implements OnInit, OnChanges {
  
  // Public inputs
  @Input() data: TokenCounterData | null = null;
  @Input() config: Partial<TokenCounterConfig> = {};
  @Input() loading: boolean = false;
  @Input() error: string | null = null;

  // Public outputs
  @Output() interaction = new EventEmitter<TokenCounterEvent>();
  @Output() statusChange = new EventEmitter<TokenCounterStatus>();

  // Internal state
  public state: TokenCounterState = {
    status: TokenCounterStatus.LOADING,
    percentage: 0,
    isLoading: false,
    warningThreshold: 0
  };

  // Computed configuration
  public computedConfig: TokenCounterConfig = { ...DEFAULT_TOKEN_COUNTER_CONFIG } as TokenCounterConfig;

  // Expose enums to template
  public readonly DisplayMode = TokenCounterDisplayMode;
  public readonly Status = TokenCounterStatus;
  public readonly Utils = TokenCounterUtils;

  ngOnInit(): void {
    this.updateConfiguration();
    this.updateState();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['config']) {
      this.updateConfiguration();
    }
    
    if (changes['data'] || changes['loading'] || changes['error']) {
      this.updateState();
    }
  }

  /**
   * Update the computed configuration by merging defaults with provided config
   */
  private updateConfiguration(): void {
    this.computedConfig = {
      ...DEFAULT_TOKEN_COUNTER_CONFIG,
      ...this.config
    } as TokenCounterConfig;
  }

  /**
   * Update the internal state based on current inputs
   */
  private updateState(): void {
    const previousStatus = this.state.status;

    if (this.loading) {
      this.state = {
        ...this.state,
        status: TokenCounterStatus.LOADING,
        isLoading: true,
        errorMessage: undefined
      };
    } else if (this.error) {
      this.state = {
        ...this.state,
        status: TokenCounterStatus.ERROR,
        isLoading: false,
        errorMessage: this.error,
        percentage: 0
      };
    } else if (this.data) {
      const warningThreshold = this.data.warningThreshold || (this.data.limit * 0.8);
      const status = TokenCounterUtils.calculateStatus(
        this.data.current,
        this.data.limit,
        warningThreshold
      );
      const percentage = TokenCounterUtils.calculatePercentage(this.data.current, this.data.limit);

      this.state = {
        status,
        percentage,
        isLoading: false,
        errorMessage: undefined,
        warningThreshold
      };
    } else {
      this.state = {
        status: TokenCounterStatus.ERROR,
        percentage: 0,
        isLoading: false,
        errorMessage: 'No data provided',
        warningThreshold: 0
      };
    }

    // Emit status change if it changed
    if (previousStatus !== this.state.status) {
      this.statusChange.emit(this.state.status);
    }
  }

  /**
   * Handle click events on the component
   */
  onComponentClick(event: Event): void {
    if (this.computedConfig.disabled || !this.data) {
      return;
    }

    this.emitInteractionEvent('click', event);
  }

  /**
   * Handle hover events on the component
   */
  onComponentHover(event: Event): void {
    if (this.computedConfig.disabled || !this.data) {
      return;
    }

    this.emitInteractionEvent('hover', event);
  }

  /**
   * Handle focus events on the component
   */
  onComponentFocus(event: Event): void {
    if (this.computedConfig.disabled || !this.data) {
      return;
    }

    this.emitInteractionEvent('focus', event);
  }

  /**
   * Emit an interaction event with current state
   */
  private emitInteractionEvent(type: TokenCounterEvent['type'], originalEvent?: Event): void {
    if (!this.data) return;

    const event: TokenCounterEvent = {
      type,
      data: this.data,
      status: this.state.status,
      metadata: {
        percentage: this.state.percentage,
        warningThreshold: this.state.warningThreshold,
        originalEvent
      }
    };

    this.interaction.emit(event);
  }

  /**
   * Get CSS classes for the component based on current state
   */
  getComponentClasses(): string[] {
    const classes = ['token-counter'];
    
    // Add display mode class
    classes.push(`token-counter--${this.computedConfig.displayMode}`);
    
    // Add status class
    classes.push(`token-counter--${this.state.status}`);
    
    // Add loading class
    if (this.state.isLoading) {
      classes.push('token-counter--loading');
    }
    
    // Add disabled class
    if (this.computedConfig.disabled) {
      classes.push('token-counter--disabled');
    }
    
    // Add custom classes
    if (this.computedConfig.customClasses) {
      classes.push(...this.computedConfig.customClasses);
    }
    
    return classes;
  }

  /**
   * Get ARIA label for the component
   */
  getAriaLabel(): string {
    if (this.computedConfig.ariaLabel) {
      return this.computedConfig.ariaLabel;
    }

    if (!this.data) {
      return 'Token counter: No data';
    }

    const statusText = TokenCounterUtils.getStatusText(this.state.status);
    const percentage = this.state.percentage;
    
    return `Token counter: ${this.data.current} of ${this.data.limit} tokens used (${percentage}%). Status: ${statusText}`;
  }

  /**
   * Get progress bar width as a percentage
   */
  getProgressBarWidth(): number {
    return Math.min(this.state.percentage, 100);
  }

  /**
   * Get formatted token count display
   */
  getFormattedCount(): string {
    if (!this.data) return '0';
    
    const current = TokenCounterUtils.formatTokenCount(this.data.current);
    const limit = TokenCounterUtils.formatTokenCount(this.data.limit);
    
    return `${current}/${limit}`;
  }

  /**
   * Get excess token count when over limit
   */
  getExcessTokens(): number {
    if (!this.data || this.data.current <= this.data.limit) {
      return 0;
    }
    return this.data.current - this.data.limit;
  }

  /**
   * Check if the component should show detailed information
   */
  shouldShowDetailed(): boolean {
    return this.computedConfig.displayMode === TokenCounterDisplayMode.DETAILED;
  }

  /**
   * Check if the component should show compact information
   */
  shouldShowCompact(): boolean {
    return this.computedConfig.displayMode === TokenCounterDisplayMode.COMPACT;
  }

  /**
   * Check if the component should show mobile-optimized layout
   */
  shouldShowMobile(): boolean {
    return this.computedConfig.displayMode === TokenCounterDisplayMode.MOBILE;
  }
}
