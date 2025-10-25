import { 
  Component, 
  Input, 
  Output, 
  EventEmitter, 
  OnInit, 
  OnDestroy, 
  forwardRef,
  ChangeDetectionStrategy,
  ChangeDetectorRef
} from '@angular/core';
import { 
  ControlValueAccessor, 
  NG_VALUE_ACCESSOR, 
  NG_VALIDATORS, 
  Validator, 
  AbstractControl, 
  ValidationErrors 
} from '@angular/forms';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject, Subscription, BehaviorSubject } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap, takeUntil } from 'rxjs/operators';

import { TokenCounterComponent } from '../token-counter/token-counter.component';
import { TokenValidationService } from '../../services/token-validation.service';
import { SystemPromptFieldType } from '../../services/token-limits.service';
import { 
  TokenValidationResult, 
  TokenValidationStatus,
  TokenValidationUtils 
} from '../../models/token-validation.model';
import { TokenCounterData, TokenCounterDisplayMode } from '../../models/token-counter.model';

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
  @Input() label: string = '';
  @Input() placeholder: string = '';
  @Input() rows: number = 3;
  @Input() disabled: boolean = false;
  @Input() required: boolean = false;
  @Input() debounceTime: number = 500;

  // Component outputs
  @Output() validationChange = new EventEmitter<TokenValidationResult>();
  @Output() tokenCountChange = new EventEmitter<number>();

  // Internal state
  public value: string = '';
  public validationResult: TokenValidationResult | null = null;
  public tokenCounterData: TokenCounterData | null = null;
  public isLoading: boolean = false;
  public hasError: boolean = false;
  public errorMessage: string = '';

  // Form control integration
  private onChange = (value: string) => {};
  private onTouched = () => {};
  private touched = false;

  // Reactive streams
  private destroy$ = new Subject<void>();
  private valueChange$ = new BehaviorSubject<string>('');
  private validationSubscription?: Subscription;

  // Expose enums and utils to template
  public readonly ValidationStatus = TokenValidationStatus;
  public readonly ValidationUtils = TokenValidationUtils;
  public readonly DisplayMode = TokenCounterDisplayMode;

  constructor(
    private tokenValidationService: TokenValidationService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.setupValidation();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.validationSubscription?.unsubscribe();
  }

  // ControlValueAccessor implementation
  writeValue(value: string): void {
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
  validate(control: AbstractControl): ValidationErrors | null {
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
    this.validationSubscription = this.valueChange$.pipe(
      debounceTime(this.debounceTime),
      distinctUntilChanged(),
      switchMap(value => {
        if (!value.trim()) {
          return [this.createEmptyValidationResult()];
        }
        
        this.isLoading = true;
        this.hasError = false;
        this.cdr.markForCheck();
        
        return this.tokenValidationService.validateField(value, this.fieldType);
      }),
      takeUntil(this.destroy$)
    ).subscribe({
      next: (result) => {
        this.handleValidationResult(result);
      },
      error: (error) => {
        this.handleValidationError(error);
      }
    });
  }

  /**
   * Handle validation result
   */
  private handleValidationResult(result: TokenValidationResult): void {
    this.validationResult = result;
    this.isLoading = false;
    this.hasError = result.status === TokenValidationStatus.ERROR;
    this.errorMessage = this.hasError ? result.message : '';
    
    // Update token counter data
    this.tokenCounterData = {
      current: result.currentTokens,
      limit: result.maxTokens,
      warningThreshold: result.warningThreshold
    };
    
    // Emit events
    this.validationChange.emit(result);
    this.tokenCountChange.emit(result.currentTokens);
    
    this.cdr.markForCheck();
  }

  /**
   * Handle validation error
   */
  private handleValidationError(error: any): void {
    console.error('Validation error:', error);
    
    this.isLoading = false;
    this.hasError = true;
    this.errorMessage = 'Unable to validate token count';
    this.validationResult = this.tokenValidationService.createLoadingResult(this.fieldType);
    this.validationResult.status = TokenValidationStatus.ERROR;
    this.validationResult.message = this.errorMessage;
    
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
    
    if (this.hasError) {
      classes.push('system-prompt-field--error');
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
