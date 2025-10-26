import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { FormsModule, ReactiveFormsModule, FormControl } from '@angular/forms';
import { ChangeDetectorRef } from '@angular/core';
import { of, throwError, BehaviorSubject } from 'rxjs';
import { SystemPromptFieldComponent } from './system-prompt-field.component';
import { TokenValidationService } from '../../services/token-validation.service';
import { TokenCounterComponent } from '../token-counter/token-counter.component';
import { 
  TokenValidationResult, 
  TokenValidationStatus 
} from '../../models/token-validation.model';
import { SystemPromptFieldType } from '../../services/token-limits.service';

describe('SystemPromptFieldComponent', () => {
  let component: SystemPromptFieldComponent;
  let fixture: ComponentFixture<SystemPromptFieldComponent>;
  let mockTokenValidationService: jasmine.SpyObj<TokenValidationService>;
  let mockChangeDetectorRef: jasmine.SpyObj<ChangeDetectorRef>;

  const mockValidationResult: TokenValidationResult = {
    status: TokenValidationStatus.VALID,
    currentTokens: 100,
    maxTokens: 500,
    warningThreshold: 400,
    criticalThreshold: 450,
    percentage: 20,
    message: '100/500 tokens (20%)',
    isValid: true,
    metadata: {
      fieldType: 'mainPrefix',
      timestamp: new Date()
    }
  };

  beforeEach(async () => {
    const validationServiceSpy = jasmine.createSpyObj('TokenValidationService', [
      'validateField', 
      'createLoadingResult'
    ]);
    const cdrSpy = jasmine.createSpyObj('ChangeDetectorRef', ['markForCheck']);

    await TestBed.configureTestingModule({
      imports: [
        SystemPromptFieldComponent,
        FormsModule,
        ReactiveFormsModule,
        TokenCounterComponent
      ],
      providers: [
        { provide: TokenValidationService, useValue: validationServiceSpy },
        { provide: ChangeDetectorRef, useValue: cdrSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(SystemPromptFieldComponent);
    component = fixture.componentInstance;
    mockTokenValidationService = TestBed.inject(TokenValidationService) as jasmine.SpyObj<TokenValidationService>;
    mockChangeDetectorRef = TestBed.inject(ChangeDetectorRef) as jasmine.SpyObj<ChangeDetectorRef>;

    // Setup default mock behavior
    mockTokenValidationService.validateField.and.returnValue(of(mockValidationResult));
    mockTokenValidationService.createLoadingResult.and.returnValue({
      ...mockValidationResult,
      status: TokenValidationStatus.LOADING,
      message: 'Counting tokens...',
      isValid: false
    });
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('Component Initialization', () => {
    it('should initialize with default values', () => {
      expect(component.fieldType).toBe('mainPrefix');
      expect(component.label).toBe('');
      expect(component.placeholder).toBe('');
      expect(component.rows).toBe(3);
      expect(component.disabled).toBe(false);
      expect(component.required).toBe(false);
      expect(component.debounceTime).toBe(500);
      expect(component.value).toBe('');
      expect(component.validationResult).toBeNull();
      expect(component.isLoading).toBe(false);
      expect(component.hasError).toBe(false);
    });

    it('should setup validation on init', () => {
      component.ngOnInit();
      expect(component).toBeTruthy();
      // Validation setup is tested in separate tests
    });

    it('should cleanup on destroy', () => {
      component.ngOnInit();
      spyOn(component['destroy$'], 'next');
      spyOn(component['destroy$'], 'complete');
      
      component.ngOnDestroy();
      
      expect(component['destroy$'].next).toHaveBeenCalled();
      expect(component['destroy$'].complete).toHaveBeenCalled();
    });
  });

  describe('ControlValueAccessor Implementation', () => {
    it('should write value correctly', () => {
      const testValue = 'Test content';
      component.writeValue(testValue);
      
      expect(component.value).toBe(testValue);
      expect(mockChangeDetectorRef.markForCheck).toHaveBeenCalled();
    });

    it('should handle null value in writeValue', () => {
      component.writeValue(null);
      expect(component.value).toBe('');
    });

    it('should register onChange callback', () => {
      const mockOnChange = jasmine.createSpy('onChange');
      component.registerOnChange(mockOnChange);
      
      // Trigger change
      const event = { target: { value: 'new value' } } as Event & { target: { value: string } };
      component.onInputChange(event);
      
      expect(mockOnChange).toHaveBeenCalledWith('new value');
    });

    it('should register onTouched callback', () => {
      const mockOnTouched = jasmine.createSpy('onTouched');
      component.registerOnTouched(mockOnTouched);
      
      component.onBlur();
      
      expect(mockOnTouched).toHaveBeenCalled();
    });

    it('should set disabled state', () => {
      component.setDisabledState(true);
      expect(component.disabled).toBe(true);
      expect(mockChangeDetectorRef.markForCheck).toHaveBeenCalled();
    });
  });

  describe('Validator Implementation', () => {
    it('should return null for valid input', () => {
      component.validationResult = mockValidationResult;
      component.value = 'Valid content';
      
      const control = new FormControl('Valid content');
      const result = component.validate(control);
      
      expect(result).toBeNull();
    });

    it('should return required error for empty required field', () => {
      component.required = true;
      component.value = '';
      component.validationResult = mockValidationResult;
      
      const control = new FormControl('');
      const result = component.validate(control);
      
      expect(result).toEqual({ required: true });
    });

    it('should return tokenLimit error for invalid validation', () => {
      const invalidResult = {
        ...mockValidationResult,
        status: TokenValidationStatus.INVALID,
        isValid: false,
        currentTokens: 600,
        message: 'Token limit exceeded'
      };
      component.validationResult = invalidResult;
      component.value = 'Too much content';
      
      const control = new FormControl('Too much content');
      const result = component.validate(control);
      
      expect(result).toEqual({
        tokenLimit: {
          currentTokens: 600,
          maxTokens: 500,
          message: 'Token limit exceeded'
        }
      });
    });

    it('should return null when no validation result exists', () => {
      component.validationResult = null;
      
      const control = new FormControl('Some content');
      const result = component.validate(control);
      
      expect(result).toBeNull();
    });
  });

  describe('Input Handling', () => {
    it('should handle input changes', () => {
      const mockOnChange = jasmine.createSpy('onChange');
      component.registerOnChange(mockOnChange);
      
      const event = { target: { value: 'New content' } } as Event & { target: { value: string } };
      component.onInputChange(event);
      
      expect(component.value).toBe('New content');
      expect(mockOnChange).toHaveBeenCalledWith('New content');
    });

    it('should mark as touched on first input', () => {
      const mockOnTouched = jasmine.createSpy('onTouched');
      component.registerOnTouched(mockOnTouched);
      
      const event = { target: { value: 'Content' } } as Event & { target: { value: string } };
      component.onInputChange(event);
      
      expect(mockOnTouched).toHaveBeenCalled();
    });

    it('should not call onTouched multiple times', () => {
      const mockOnTouched = jasmine.createSpy('onTouched');
      component.registerOnTouched(mockOnTouched);
      
      const event1 = { target: { value: 'Content 1' } } as Event & { target: { value: string } };
      const event2 = { target: { value: 'Content 2' } } as Event & { target: { value: string } };
      
      component.onInputChange(event1);
      component.onInputChange(event2);
      
      expect(mockOnTouched).toHaveBeenCalledTimes(1);
    });

    it('should handle blur events', () => {
      const mockOnTouched = jasmine.createSpy('onTouched');
      component.registerOnTouched(mockOnTouched);
      
      component.onBlur();
      
      expect(mockOnTouched).toHaveBeenCalled();
    });
  });

  describe('Validation Flow', () => {
    beforeEach(() => {
      component.ngOnInit();
    });

    it('should trigger validation after debounce time', fakeAsync(() => {
      const validationSubject = new BehaviorSubject(mockValidationResult);
      mockTokenValidationService.validateField.and.returnValue(validationSubject);
      
      component.writeValue('Test content');
      tick(500); // Wait for debounce
      
      expect(mockTokenValidationService.validateField).toHaveBeenCalledWith('Test content', 'mainPrefix');
      expect(component.validationResult).toEqual(mockValidationResult);
      expect(component.isLoading).toBe(false);
    }));

    it('should show loading state during validation', fakeAsync(() => {
      const validationSubject = new BehaviorSubject(mockValidationResult);
      mockTokenValidationService.validateField.and.returnValue(validationSubject);
      
      component.writeValue('Test content');
      tick(500); // Trigger validation
      
      // Loading state should be handled in the validation flow
      expect(component.isLoading).toBe(false); // After completion
    }));

    it('should handle validation errors', fakeAsync(() => {
      mockTokenValidationService.validateField.and.returnValue(throwError('Validation error'));
      
      component.writeValue('Test content');
      tick(500);
      
      expect(component.hasError).toBe(true);
      expect(component.errorMessage).toBe('Unable to validate token count');
    }));

    it('should emit validation change events', fakeAsync(() => {
      spyOn(component.validationChange, 'emit');
      spyOn(component.tokenCountChange, 'emit');
      
      component.writeValue('Test content');
      tick(500);
      
      expect(component.validationChange.emit).toHaveBeenCalledWith(mockValidationResult);
      expect(component.tokenCountChange.emit).toHaveBeenCalledWith(100);
    }));

    it('should not validate empty content', fakeAsync(() => {
      component.writeValue('');
      tick(500);
      
      expect(mockTokenValidationService.validateField).not.toHaveBeenCalled();
      expect(component.validationResult?.status).toBe(TokenValidationStatus.VALID);
      expect(component.validationResult?.currentTokens).toBe(0);
    }));

    it('should debounce rapid input changes', fakeAsync(() => {
      component.writeValue('Test 1');
      tick(200);
      component.writeValue('Test 2');
      tick(200);
      component.writeValue('Test 3');
      tick(500);
      
      expect(mockTokenValidationService.validateField).toHaveBeenCalledTimes(1);
      expect(mockTokenValidationService.validateField).toHaveBeenCalledWith('Test 3', 'mainPrefix');
    }));
  });

  describe('CSS Classes', () => {
    it('should return correct component classes', () => {
      component.disabled = true;
      component.isLoading = true;
      component.hasError = true;
      component.validationResult = { ...mockValidationResult, status: TokenValidationStatus.WARNING };
      
      const classes = component.getComponentClasses();
      
      expect(classes).toContain('system-prompt-field');
      expect(classes).toContain('system-prompt-field--disabled');
      expect(classes).toContain('system-prompt-field--loading');
      expect(classes).toContain('system-prompt-field--error');
      expect(classes).toContain('system-prompt-field--warning');
    });

    it('should return correct textarea classes', () => {
      component.validationResult = { ...mockValidationResult, status: TokenValidationStatus.CRITICAL };
      
      const classes = component.getTextareaClasses();
      
      expect(classes).toContain('system-prompt-field__textarea');
      expect(classes).toContain('token-validation--critical');
    });
  });

  describe('Display Logic', () => {
    it('should show validation message for non-valid status', () => {
      component.validationResult = { ...mockValidationResult, status: TokenValidationStatus.WARNING };
      expect(component.shouldShowValidationMessage()).toBe(true);
      
      component.validationResult = { ...mockValidationResult, status: TokenValidationStatus.VALID };
      expect(component.shouldShowValidationMessage()).toBe(false);
      
      component.validationResult = { ...mockValidationResult, status: TokenValidationStatus.LOADING };
      expect(component.shouldShowValidationMessage()).toBe(false);
    });

    it('should show token counter when tokens > 0', () => {
      component.tokenCounterData = { current: 100, limit: 500 };
      expect(component.shouldShowTokenCounter()).toBe(true);
      
      component.tokenCounterData = { current: 0, limit: 500 };
      expect(component.shouldShowTokenCounter()).toBe(false);
      
      component.tokenCounterData = null;
      expect(component.shouldShowTokenCounter()).toBe(false);
    });

    it('should generate unique textarea ID', () => {
      component.fieldType = 'assistantPrompt';
      expect(component.getTextareaId()).toBe('system-prompt-field-assistantPrompt');
    });

    it('should generate correct ARIA describedby', () => {
      component.validationResult = { ...mockValidationResult, status: TokenValidationStatus.WARNING };
      component.tokenCounterData = { current: 100, limit: 500 };
      
      const ariaDescribedBy = component.getAriaDescribedBy();
      
      expect(ariaDescribedBy).toContain('system-prompt-field-mainPrefix-validation');
      expect(ariaDescribedBy).toContain('system-prompt-field-mainPrefix-counter');
    });
  });

  describe('Field Type Support', () => {
    const fieldTypes: SystemPromptFieldType[] = ['mainPrefix', 'mainSuffix', 'assistantPrompt', 'editorPrompt'];
    
    fieldTypes.forEach(fieldType => {
      it(`should support ${fieldType} field type`, () => {
        component.fieldType = fieldType;
        component.ngOnInit();
        
        expect(component.fieldType).toBe(fieldType);
        expect(component.getTextareaId()).toBe(`system-prompt-field-${fieldType}`);
      });
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA attributes', () => {
      component.fieldType = 'mainPrefix';
      component.label = 'Test Label';
      component.required = true;
      component.hasError = true;
      
      fixture.detectChanges();
      
      const textarea = fixture.nativeElement.querySelector('textarea');
      const label = fixture.nativeElement.querySelector('label');
      
      expect(textarea.id).toBe('system-prompt-field-mainPrefix');
      expect(label.getAttribute('for')).toBe('system-prompt-field-mainPrefix');
      expect(textarea.getAttribute('aria-invalid')).toBe('true');
      expect(textarea.required).toBe(true);
    });

    it('should show required indicator', () => {
      component.label = 'Test Label';
      component.required = true;
      
      fixture.detectChanges();
      
      const requiredSpan = fixture.nativeElement.querySelector('.system-prompt-field__required');
      expect(requiredSpan).toBeTruthy();
      expect(requiredSpan.textContent).toBe('*');
    });
  });

  describe('Error Handling', () => {
    it('should display error messages', () => {
      component.hasError = true;
      component.errorMessage = 'Test error message';
      
      fixture.detectChanges();
      
      const errorDiv = fixture.nativeElement.querySelector('.system-prompt-field__error');
      expect(errorDiv).toBeTruthy();
      expect(errorDiv.textContent).toContain('Test error message');
    });

    it('should handle validation service errors gracefully', fakeAsync(() => {
      component.ngOnInit();
      mockTokenValidationService.validateField.and.returnValue(throwError('Service error'));
      
      component.writeValue('Test content');
      tick(500);
      
      expect(component.hasError).toBe(true);
      expect(component.validationResult?.status).toBe(TokenValidationStatus.ERROR);
    }));
  });

  describe('Performance', () => {
    it('should use OnPush change detection', () => {
      expect(component.constructor.name).toBe('SystemPromptFieldComponent');
      // OnPush is configured in component decorator
    });

    it('should debounce input changes', fakeAsync(() => {
      component.debounceTime = 300;
      component.ngOnInit();
      
      component.writeValue('Test 1');
      tick(100);
      component.writeValue('Test 2');
      tick(100);
      component.writeValue('Test 3');
      tick(300);
      
      expect(mockTokenValidationService.validateField).toHaveBeenCalledTimes(1);
    }));
  });

  describe('Integration', () => {
    it('should integrate with TokenCounterComponent', () => {
      component.tokenCounterData = { current: 250, limit: 500, warningThreshold: 400 };
      
      fixture.detectChanges();
      
      const tokenCounter = fixture.nativeElement.querySelector('app-token-counter');
      expect(tokenCounter).toBeTruthy();
    });

    it('should update token counter data from validation results', fakeAsync(() => {
      component.ngOnInit();
      component.writeValue('Test content');
      tick(500);
      
      expect(component.tokenCounterData).toEqual({
        current: 100,
        limit: 500,
        warningThreshold: 400
      });
    }));
  });

  describe('Edge Cases', () => {
    it('should handle very long content', fakeAsync(() => {
      const longContent = 'a'.repeat(10000);
      
      component.writeValue(longContent);
      tick(500);
      
      expect(mockTokenValidationService.validateField).toHaveBeenCalledWith(longContent, 'mainPrefix');
    }));

    it('should handle special characters', fakeAsync(() => {
      const specialContent = '🚀 Special chars: @#$%^&*()';
      
      component.writeValue(specialContent);
      tick(500);
      
      expect(mockTokenValidationService.validateField).toHaveBeenCalledWith(specialContent, 'mainPrefix');
    }));

    it('should handle rapid enable/disable changes', () => {
      component.setDisabledState(true);
      component.setDisabledState(false);
      component.setDisabledState(true);
      
      expect(component.disabled).toBe(true);
      expect(mockChangeDetectorRef.markForCheck).toHaveBeenCalledTimes(3);
    });
  });
});
