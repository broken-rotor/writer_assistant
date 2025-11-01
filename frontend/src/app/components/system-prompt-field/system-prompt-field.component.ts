import {
  Component,
  Input,
  Output,
  EventEmitter,
  OnInit,
  OnDestroy,
  forwardRef,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  inject
} from '@angular/core';
import {
  ControlValueAccessor,
  NG_VALUE_ACCESSOR,
  NG_VALIDATORS,
  Validator,
  ValidationErrors,
  AbstractControl
} from '@angular/forms';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject, Subscription, BehaviorSubject } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap, takeUntil } from 'rxjs/operators';

import { TokenCounterComponent } from '../token-counter/token-counter.component';
import { TokenValidationService } from '../../services/token-validation.service';
import { SystemPromptFieldType } from '../../services/token-limits.service';
import { ToastService } from '../../services/toast.service';
import { 
  TokenValidationResult, 
  TokenValidationStatus,
  TokenValidationUtils 
} from '../../models/token-validation.model';
import { TokenCounterData, TokenCounterDisplayMode } from '../../models/token-counter.model';
import { 
  ERROR_MESSAGES, 
  ErrorContext, 
  RecoveryAction 
} from '../../constants/token-limits.constants';

/**
 * SystemPromptFieldComponent - A reusable component that combines textarea input 
 * with integrated token counting and validation.
 * 
 * Features:
 * - Real-time token counting with debouncing
 * - Field-specific token limits and validation
 * - Angular forms integration via ControlValueAccessor
 * - Loading states and error handling
 * - Responsive design
 * - Accessibility support
 */
@Component({
  selector: 'app-system-prompt-field',
  standalone: true,
  imports: [CommonModule, FormsModule, TokenCounterComponent],
  templateUrl: './system-prompt-field.component.html',
  styleUrl: './system-prompt-field.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => SystemPromptFieldComponent),
      multi: true
    },
    {
      provide: NG_VALIDATORS,
      useExisting: forwardRef(() => SystemPromptFieldComponent),
      multi: true
    }
  ]
})
export class SystemPromptFieldComponent implements OnInit, OnDestroy, ControlValueAccessor, Validator {
  
  // Component inputs
  @Input() fieldType: SystemPromptFieldType = 'mainPrefix';
  @Input() label = '';
  @Input() placeholder = '';
  @Input() rows = 3;
  @Input() disabled = false;
  @Input() required = false;
  @Input() debounceTime = 500;

  // Component outputs
  @Output() validationChange = new EventEmitter<TokenValidationResult>();
  @Output() tokenCountChange = new EventEmitter<number>();

  // Internal state
  public value = '';
  public validationResult: TokenValidationResult | null = null;
  public tokenCounterData: TokenCounterData | null = null;
  public isLoading = false;
  public hasError = false;
  public errorMessage = '';
  public errorContext: ErrorContext | null = null;
  public isFallbackMode = false;
  public isRetrying = false;
  public retryCount = 0;

  // Form control integration (ControlValueAccessor interface)
  private onChange: (value: string) => void = () => { /* Initialized by registerOnChange */ };
  private onTouched = () => { /* Initialized by registerOnTouched */ };
  private touched = false;

  // Reactive streams
  private destroy$ = new Subject<void>();
  private valueChange$ = new BehaviorSubject<string>('');
  private validationSubscription?: Subscription;

  // Expose enums and utils to template
  public readonly ValidationStatus = TokenValidationStatus;
  public readonly ValidationUtils = TokenValidationUtils;
  public readonly DisplayMode = TokenCounterDisplayMode;

  // Dependency injection
  private tokenValidationService = inject(TokenValidationService);
  private toastService = inject(ToastService);
  private cdr = inject(ChangeDetectorRef);

  ngOnInit(): void {
    console.log('🔧 SystemPromptField ngOnInit:', { 
      fieldType: this.fieldType, 
      currentValue: this.value,
      hasValue: !!this.value,
      valueLength: this.value?.length || 0
    });
    this.setupValidation();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.validationSubscription?.unsubscribe();
  }

  // ControlValueAccessor implementation
  writeValue(value: string): void {
    console.log('📝 SystemPromptField writeValue called:', { 
      fieldType: this.fieldType,
      newValue: value,
      hasValue: !!value,
      valueLength: value?.length || 0,
      previousValue: this.value
    });
    this.value = value || '';
    this.valueChange$.next(this.value);
    this.cdr.markForCheck();
  }

  registerOnChange(fn: (value: string) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
    this.cdr.markForCheck();
  }

  // Validator implementation
  validate(_control: AbstractControl): ValidationErrors | null {
    if (!this.validationResult) {
      return null;
    }

    const errors: ValidationErrors = {};

    if (this.required && !this.value.trim()) {
      errors['required'] = true;
    }

    if (!this.validationResult.isValid) {
      errors['tokenLimit'] = {
        currentTokens: this.validationResult.currentTokens,
        maxTokens: this.validationResult.maxTokens,
        message: this.validationResult.message
      };
    }

    return Object.keys(errors).length > 0 ? errors : null;
  }

  /**
   * Handle textarea input changes
   */
  onInputChange(event: Event): void {
    const target = event.target as HTMLTextAreaElement;
    this.value = target.value;
    this.valueChange$.next(this.value);
    this.onChange(this.value);
    
    if (!this.touched) {
      this.touched = true;
      this.onTouched();
    }
  }

  /**
   * Handle textarea blur events
   */
  onBlur(): void {
    if (!this.touched) {
      this.touched = true;
      this.onTouched();
    }
  }

  /**
   * Setup debounced validation
   */
  private setupValidation(): void {
    console.log('⚙️ SystemPromptField setupValidation called:', { 
      fieldType: this.fieldType,
      currentValue: this.value,
      hasValue: !!this.value,
      valueLength: this.value?.length || 0
    });

    this.validationSubscription = this.valueChange$.pipe(
      debounceTime(this.debounceTime),
      distinctUntilChanged(),
      switchMap(value => {
        if (!value.trim()) {
          console.log('🔄 SystemPromptField: Empty value, creating empty result', { fieldType: this.fieldType });
          return [this.createEmptyValidationResult()];
        }
        
        console.log('🔄 SystemPromptField: Starting validation', { value: value.substring(0, 50) + '...', fieldType: this.fieldType });
        this.isLoading = true;
        this.hasError = false;
        this.cdr.markForCheck();
        
        return this.tokenValidationService.validateField(value, this.fieldType);
      }),
      takeUntil(this.destroy$)
    ).subscribe({
      next: (result) => {
        console.log('✅ SystemPromptField: Validation subscription received result', { 
          fieldType: this.fieldType, 
          result: result 
        });
        this.handleValidationResult(result);
      },
      error: (error) => {
        console.error('❌ SystemPromptField: Validation subscription error', { 
          fieldType: this.fieldType, 
          error: error 
        });
        this.handleValidationError(error);
      }
    });

    // Trigger validation for initial value if it exists
    // This handles the case where writeValue() was called before ngOnInit()
    if (this.value && this.value.trim()) {
      console.log('🚀 SystemPromptField: Triggering initial validation', { 
        value: this.value.substring(0, 50) + '...', 
        fieldType: this.fieldType 
      });
      this.valueChange$.next(this.value);
    } else {
      console.log('⏭️ SystemPromptField: No initial value to validate', { 
        fieldType: this.fieldType,
        value: this.value,
        hasValue: !!this.value
      });
    }
  }

  /**
   * Handle validation result
   */
  private handleValidationResult(result: TokenValidationResult): void {
    console.log('✅ SystemPromptField: Received validation result', result);
    
    this.validationResult = result;
    this.isLoading = false;
    this.isRetrying = false;
    this.hasError = result.status === TokenValidationStatus.ERROR;
    this.errorMessage = this.hasError ? result.message : '';
    this.errorContext = result.metadata?.errorContext || null;
    this.isFallbackMode = result.metadata?.isFallbackMode || false;
    
    // Update token counter data
    this.tokenCounterData = {
      current: result.currentTokens,
      limit: result.maxTokens,
      warningThreshold: result.warningThreshold
    };
    
    console.log('📊 SystemPromptField: Updated state', {
      isLoading: this.isLoading,
      hasError: this.hasError,
      tokenCounterData: this.tokenCounterData
    });
    
    // Show toast notification for fallback mode
    if (this.isFallbackMode && !this.hasError) {
      this.toastService.showFallbackMode('Token validation');
    }
    
    // Emit events
    this.validationChange.emit(result);
    this.tokenCountChange.emit(result.currentTokens);
    
    console.log('🔄 SystemPromptField: Triggering change detection');
    this.cdr.markForCheck();
  }

  /**
   * Handle validation error
   */
  private handleValidationError(error: any): void {
    console.error('❌ SystemPromptField: Validation error:', error);
    
    this.isLoading = false;
    this.isRetrying = false;
    this.hasError = true;
    this.retryCount++;
    
    // Create fallback result for better user experience
    const fallbackResult = this.tokenValidationService.createFallbackResult(
      this.value,
      this.fieldType
    );
    
    this.validationResult = fallbackResult;
    this.errorMessage = ERROR_MESSAGES.VALIDATION_FAILED;
    this.isFallbackMode = true;
    
    console.log('📊 SystemPromptField: Updated error state', {
      isLoading: this.isLoading,
      hasError: this.hasError,
      retryCount: this.retryCount
    });
    
    // Show error toast with recovery actions
    this.toastService.showTokenLimitsError(
      this.errorMessage,
      [RecoveryAction.RETRY, RecoveryAction.USE_FALLBACK],
      () => this.retryValidation(),
      () => this.useFallbackMode()
    );
    
    console.log('🔄 SystemPromptField: Triggering change detection after error');
    this.cdr.markForCheck();
  }

  /**
   * Create empty validation result for empty input
   */
  private createEmptyValidationResult(): TokenValidationResult {
    return {
      status: TokenValidationStatus.VALID,
      currentTokens: 0,
      maxTokens: 0,
      warningThreshold: 0,
      criticalThreshold: 0,
      percentage: 0,
      message: 'No content to validate',
      isValid: true,
      metadata: {
        fieldType: this.fieldType,
        timestamp: new Date()
      }
    };
  }

  /**
   * Retry validation manually
   */
  retryValidation(): void {
    if (this.isLoading || this.isRetrying) {
      return;
    }
    
    this.isRetrying = true;
    this.hasError = false;
    this.errorMessage = '';
    this.errorContext = null;
    this.isFallbackMode = false;
    this.cdr.markForCheck();
    
    // Trigger validation again
    this.valueChange$.next(this.value);
  }

  /**
   * Use fallback mode explicitly
   */
  useFallbackMode(): void {
    const fallbackResult = this.tokenValidationService.createFallbackResult(
      this.value,
      this.fieldType
    );
    
    this.handleValidationResult(fallbackResult);
    this.toastService.showInfo('Using default token limits', 'Validation will continue with estimated token counts');
  }

  /**
   * Check if retry is available
   */
  canRetry(): boolean {
    return this.hasError && !this.isLoading && !this.isRetrying;
  }

  /**
   * Get current status message
   */
  getStatusMessage(): string {
    if (this.isLoading) {
      return ERROR_MESSAGES.COUNTING_TOKENS;
    }
    
    if (this.isRetrying) {
      return ERROR_MESSAGES.RETRYING;
    }
    
    if (this.isFallbackMode) {
      return ERROR_MESSAGES.FALLBACK_MODE;
    }
    
    if (this.hasError) {
      return this.errorMessage;
    }
    
    if (this.validationResult) {
      return this.validationResult.message;
    }
    
    return '';
  }

  /**
   * Get CSS classes for the component
   */
  getComponentClasses(): string[] {
    const classes = ['system-prompt-field'];
    
    if (this.disabled) {
      classes.push('system-prompt-field--disabled');
    }
    
    if (this.isLoading) {
      classes.push('system-prompt-field--loading');
    }
    
    if (this.isRetrying) {
      classes.push('system-prompt-field--retrying');
    }
    
    if (this.hasError) {
      classes.push('system-prompt-field--error');
    }
    
    if (this.isFallbackMode) {
      classes.push('system-prompt-field--fallback');
    }
    
    if (this.validationResult) {
      classes.push(`system-prompt-field--${this.validationResult.status}`);
    }
    
    return classes;
  }

  /**
   * Get CSS classes for the textarea
   */
  getTextareaClasses(): string[] {
    const classes = ['system-prompt-field__textarea'];
    
    if (this.validationResult) {
      classes.push(TokenValidationUtils.getStatusClass(this.validationResult.status));
    }
    
    return classes;
  }

  /**
   * Check if validation message should be shown
   */
  shouldShowValidationMessage(): boolean {
    return !!(this.validationResult && 
             this.validationResult.status !== TokenValidationStatus.VALID &&
             this.validationResult.status !== TokenValidationStatus.LOADING);
  }

  /**
   * Check if token counter should be shown
   */
  shouldShowTokenCounter(): boolean {
    return !!(this.tokenCounterData && this.tokenCounterData.current > 0);
  }

  /**
   * Get unique ID for the textarea
   */
  getTextareaId(): string {
    return `system-prompt-field-${this.fieldType}`;
  }

  /**
   * Get ARIA describedby attribute value
   */
  getAriaDescribedBy(): string {
    const ids = [];
    
    if (this.shouldShowValidationMessage()) {
      ids.push(`${this.getTextareaId()}-validation`);
    }
    
    if (this.shouldShowTokenCounter()) {
      ids.push(`${this.getTextareaId()}-counter`);
    }
    
    return ids.join(' ');
  }
}
