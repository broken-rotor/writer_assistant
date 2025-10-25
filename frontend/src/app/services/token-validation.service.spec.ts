import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { TokenValidationService } from './token-validation.service';
import { TokenLimitsService, SystemPromptFieldType, FieldTokenLimit } from './token-limits.service';
import { TokenCountingService } from './token-counting.service';
import { 
  TokenValidationResult, 
  TokenValidationStatus, 
  TokenValidationConfig,
  DEFAULT_VALIDATION_CONFIG 
} from '../models/token-validation.model';
import { TokenCountResultItem, ContentType, CountingStrategy } from '../models/token.model';

describe('TokenValidationService', () => {
  let service: TokenValidationService;
  let mockTokenLimitsService: jasmine.SpyObj<TokenLimitsService>;
  let mockTokenCountingService: jasmine.SpyObj<TokenCountingService>;

  const mockFieldLimit: FieldTokenLimit = {
    fieldType: 'mainPrefix',
    limit: 1000,
    warningThreshold: 800,
    criticalThreshold: 900
  };

  const mockTokenResult: TokenCountResultItem = {
    text: 'Sample text',
    token_count: 500,
    content_type: ContentType.SYSTEM_PROMPT,
    metadata: {
      strategy: CountingStrategy.EXACT,
      processing_time: 0.1,
      cached: false
    }
  };

  beforeEach(() => {
    const limitsServiceSpy = jasmine.createSpyObj('TokenLimitsService', ['getFieldLimit']);
    const countingServiceSpy = jasmine.createSpyObj('TokenCountingService', ['countTokensDebounced', 'countTokens']);

    TestBed.configureTestingModule({
      providers: [
        TokenValidationService,
        { provide: TokenLimitsService, useValue: limitsServiceSpy },
        { provide: TokenCountingService, useValue: countingServiceSpy }
      ]
    });

    service = TestBed.inject(TokenValidationService);
    mockTokenLimitsService = TestBed.inject(TokenLimitsService) as jasmine.SpyObj<TokenLimitsService>;
    mockTokenCountingService = TestBed.inject(TokenCountingService) as jasmine.SpyObj<TokenCountingService>;
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('validateField', () => {
    it('should return valid result for text within limits', (done) => {
      mockTokenLimitsService.getFieldLimit.and.returnValue(of(mockFieldLimit));
      mockTokenCountingService.countTokensDebounced.and.returnValue(of(mockTokenResult));

      service.validateField('Sample text', 'mainPrefix').subscribe(result => {
        expect(result.status).toBe(TokenValidationStatus.VALID);
        expect(result.currentTokens).toBe(500);
        expect(result.maxTokens).toBe(1000);
        expect(result.isValid).toBe(true);
        expect(result.percentage).toBe(50);
        done();
      });
    });

    it('should return warning result for text approaching limits', (done) => {
      const warningTokenResult = { ...mockTokenResult, token_count: 850 };
      mockTokenLimitsService.getFieldLimit.and.returnValue(of(mockFieldLimit));
      mockTokenCountingService.countTokensDebounced.and.returnValue(of(warningTokenResult));

      service.validateField('Longer text', 'mainPrefix').subscribe(result => {
        expect(result.status).toBe(TokenValidationStatus.WARNING);
        expect(result.currentTokens).toBe(850);
        expect(result.isValid).toBe(true);
        expect(result.percentage).toBe(85);
        done();
      });
    });

    it('should return critical result for text near limits', (done) => {
      const criticalTokenResult = { ...mockTokenResult, token_count: 950 };
      mockTokenLimitsService.getFieldLimit.and.returnValue(of(mockFieldLimit));
      mockTokenCountingService.countTokensDebounced.and.returnValue(of(criticalTokenResult));

      service.validateField('Very long text', 'mainPrefix').subscribe(result => {
        expect(result.status).toBe(TokenValidationStatus.CRITICAL);
        expect(result.currentTokens).toBe(950);
        expect(result.isValid).toBe(true);
        expect(result.percentage).toBe(95);
        done();
      });
    });

    it('should return invalid result for text over limits', (done) => {
      const invalidTokenResult = { ...mockTokenResult, token_count: 1200 };
      mockTokenLimitsService.getFieldLimit.and.returnValue(of(mockFieldLimit));
      mockTokenCountingService.countTokensDebounced.and.returnValue(of(invalidTokenResult));

      service.validateField('Extremely long text', 'mainPrefix').subscribe(result => {
        expect(result.status).toBe(TokenValidationStatus.INVALID);
        expect(result.currentTokens).toBe(1200);
        expect(result.isValid).toBe(false);
        expect(result.percentage).toBe(120);
        expect(result.metadata?.excessTokens).toBe(200);
        done();
      });
    });

    it('should handle validation errors gracefully', (done) => {
      mockTokenLimitsService.getFieldLimit.and.returnValue(of(mockFieldLimit));
      mockTokenCountingService.countTokensDebounced.and.returnValue(throwError('Network error'));

      service.validateField('Sample text', 'mainPrefix').subscribe(result => {
        expect(result.status).toBe(TokenValidationStatus.ERROR);
        expect(result.isValid).toBe(false);
        expect(result.message).toContain('Unable to validate');
        done();
      });
    });

    it('should use custom validation config', (done) => {
      const customConfig: Partial<TokenValidationConfig> = {
        allowOverLimit: true,
        messages: {
          invalid: 'Custom error message'
        }
      };

      const invalidTokenResult = { ...mockTokenResult, token_count: 1200 };
      mockTokenLimitsService.getFieldLimit.and.returnValue(of(mockFieldLimit));
      mockTokenCountingService.countTokensDebounced.and.returnValue(of(invalidTokenResult));

      service.validateField('Over limit text', 'mainPrefix', customConfig).subscribe(result => {
        expect(result.status).toBe(TokenValidationStatus.INVALID);
        expect(result.isValid).toBe(true); // Should be valid due to allowOverLimit
        expect(result.message).toContain('Custom error message');
        done();
      });
    });

    it('should call services with correct parameters', () => {
      mockTokenLimitsService.getFieldLimit.and.returnValue(of(mockFieldLimit));
      mockTokenCountingService.countTokensDebounced.and.returnValue(of(mockTokenResult));

      service.validateField('Test text', 'assistantPrompt').subscribe();

      expect(mockTokenLimitsService.getFieldLimit).toHaveBeenCalledWith('assistantPrompt');
      expect(mockTokenCountingService.countTokensDebounced).toHaveBeenCalledWith(
        'Test text',
        ContentType.SYSTEM_PROMPT,
        CountingStrategy.EXACT
      );
    });
  });

  describe('validateFieldImmediate', () => {
    it('should use immediate token counting', () => {
      mockTokenLimitsService.getFieldLimit.and.returnValue(of(mockFieldLimit));
      mockTokenCountingService.countTokens.and.returnValue(of(mockTokenResult));

      service.validateFieldImmediate('Test text', 'mainPrefix').subscribe();

      expect(mockTokenCountingService.countTokens).toHaveBeenCalledWith(
        'Test text',
        ContentType.SYSTEM_PROMPT,
        CountingStrategy.EXACT
      );
      expect(mockTokenCountingService.countTokensDebounced).not.toHaveBeenCalled();
    });

    it('should return same validation result as regular validate', (done) => {
      mockTokenLimitsService.getFieldLimit.and.returnValue(of(mockFieldLimit));
      mockTokenCountingService.countTokens.and.returnValue(of(mockTokenResult));

      service.validateFieldImmediate('Sample text', 'mainPrefix').subscribe(result => {
        expect(result.status).toBe(TokenValidationStatus.VALID);
        expect(result.currentTokens).toBe(500);
        expect(result.maxTokens).toBe(1000);
        done();
      });
    });
  });

  describe('validateMultipleFields', () => {
    it('should validate multiple fields simultaneously', (done) => {
      const fields = [
        { text: 'Text 1', fieldType: 'mainPrefix' as SystemPromptFieldType },
        { text: 'Text 2', fieldType: 'mainSuffix' as SystemPromptFieldType }
      ];

      const fieldLimit2: FieldTokenLimit = {
        fieldType: 'mainSuffix',
        limit: 500,
        warningThreshold: 400,
        criticalThreshold: 450
      };

      mockTokenLimitsService.getFieldLimit.and.callFake((fieldType) => {
        if (fieldType === 'mainPrefix') return of(mockFieldLimit);
        if (fieldType === 'mainSuffix') return of(fieldLimit2);
        return of(mockFieldLimit);
      });

      mockTokenCountingService.countTokensDebounced.and.returnValue(of(mockTokenResult));

      service.validateMultipleFields(fields).subscribe(results => {
        expect(results).toHaveLength(2);
        expect(results[0].metadata?.fieldType).toBe('mainPrefix');
        expect(results[1].metadata?.fieldType).toBe('mainSuffix');
        done();
      });
    });

    it('should handle empty fields array', (done) => {
      service.validateMultipleFields([]).subscribe(results => {
        expect(results).toHaveLength(0);
        done();
      });
    });
  });

  describe('isValidForSubmission', () => {
    it('should return true for valid text', (done) => {
      mockTokenLimitsService.getFieldLimit.and.returnValue(of(mockFieldLimit));
      mockTokenCountingService.countTokens.and.returnValue(of(mockTokenResult));

      service.isValidForSubmission('Valid text', 'mainPrefix').subscribe(isValid => {
        expect(isValid).toBe(true);
        done();
      });
    });

    it('should return false for invalid text', (done) => {
      const invalidTokenResult = { ...mockTokenResult, token_count: 1200 };
      mockTokenLimitsService.getFieldLimit.and.returnValue(of(mockFieldLimit));
      mockTokenCountingService.countTokens.and.returnValue(of(invalidTokenResult));

      service.isValidForSubmission('Invalid text', 'mainPrefix').subscribe(isValid => {
        expect(isValid).toBe(false);
        done();
      });
    });

    it('should respect allowOverLimit config', (done) => {
      const invalidTokenResult = { ...mockTokenResult, token_count: 1200 };
      const config = { allowOverLimit: true };
      
      mockTokenLimitsService.getFieldLimit.and.returnValue(of(mockFieldLimit));
      mockTokenCountingService.countTokens.and.returnValue(of(invalidTokenResult));

      service.isValidForSubmission('Invalid text', 'mainPrefix', config).subscribe(isValid => {
        expect(isValid).toBe(true);
        done();
      });
    });
  });

  describe('getValidationStatus', () => {
    it('should return only the validation status', (done) => {
      mockTokenLimitsService.getFieldLimit.and.returnValue(of(mockFieldLimit));
      mockTokenCountingService.countTokensDebounced.and.returnValue(of(mockTokenResult));

      service.getValidationStatus('Sample text', 'mainPrefix').subscribe(status => {
        expect(status).toBe(TokenValidationStatus.VALID);
        done();
      });
    });
  });

  describe('createLoadingResult', () => {
    it('should create a loading validation result', () => {
      const result = service.createLoadingResult('mainPrefix');
      
      expect(result.status).toBe(TokenValidationStatus.LOADING);
      expect(result.isValid).toBe(false);
      expect(result.message).toContain('Counting tokens');
      expect(result.metadata?.fieldType).toBe('mainPrefix');
      expect(result.metadata?.timestamp).toBeInstanceOf(Date);
    });
  });

  describe('edge cases', () => {
    it('should handle zero token count', (done) => {
      const zeroTokenResult = { ...mockTokenResult, token_count: 0 };
      mockTokenLimitsService.getFieldLimit.and.returnValue(of(mockFieldLimit));
      mockTokenCountingService.countTokensDebounced.and.returnValue(of(zeroTokenResult));

      service.validateField('', 'mainPrefix').subscribe(result => {
        expect(result.status).toBe(TokenValidationStatus.VALID);
        expect(result.currentTokens).toBe(0);
        expect(result.percentage).toBe(0);
        done();
      });
    });

    it('should handle exact limit boundary', (done) => {
      const exactLimitResult = { ...mockTokenResult, token_count: 1000 };
      mockTokenLimitsService.getFieldLimit.and.returnValue(of(mockFieldLimit));
      mockTokenCountingService.countTokensDebounced.and.returnValue(of(exactLimitResult));

      service.validateField('Exact limit text', 'mainPrefix').subscribe(result => {
        expect(result.status).toBe(TokenValidationStatus.VALID);
        expect(result.currentTokens).toBe(1000);
        expect(result.percentage).toBe(100);
        expect(result.metadata?.excessTokens).toBeUndefined();
        done();
      });
    });

    it('should handle warning threshold boundary', (done) => {
      const warningBoundaryResult = { ...mockTokenResult, token_count: 800 };
      mockTokenLimitsService.getFieldLimit.and.returnValue(of(mockFieldLimit));
      mockTokenCountingService.countTokensDebounced.and.returnValue(of(warningBoundaryResult));

      service.validateField('Warning boundary text', 'mainPrefix').subscribe(result => {
        expect(result.status).toBe(TokenValidationStatus.WARNING);
        expect(result.currentTokens).toBe(800);
        done();
      });
    });

    it('should handle critical threshold boundary', (done) => {
      const criticalBoundaryResult = { ...mockTokenResult, token_count: 900 };
      mockTokenLimitsService.getFieldLimit.and.returnValue(of(mockFieldLimit));
      mockTokenCountingService.countTokensDebounced.and.returnValue(of(criticalBoundaryResult));

      service.validateField('Critical boundary text', 'mainPrefix').subscribe(result => {
        expect(result.status).toBe(TokenValidationStatus.CRITICAL);
        expect(result.currentTokens).toBe(900);
        done();
      });
    });
  });

  describe('field type variations', () => {
    it('should work with all field types', () => {
      const fieldTypes: SystemPromptFieldType[] = ['mainPrefix', 'mainSuffix', 'assistantPrompt', 'editorPrompt'];
      
      fieldTypes.forEach(fieldType => {
        const fieldLimit = { ...mockFieldLimit, fieldType };
        mockTokenLimitsService.getFieldLimit.and.returnValue(of(fieldLimit));
        mockTokenCountingService.countTokensDebounced.and.returnValue(of(mockTokenResult));

        service.validateField('Test', fieldType).subscribe(result => {
          expect(result.metadata?.fieldType).toBe(fieldType);
        });
      });
    });
  });

  describe('metadata handling', () => {
    it('should include correct metadata in results', (done) => {
      mockTokenLimitsService.getFieldLimit.and.returnValue(of(mockFieldLimit));
      mockTokenCountingService.countTokensDebounced.and.returnValue(of(mockTokenResult));

      service.validateField('Sample text', 'assistantPrompt').subscribe(result => {
        expect(result.metadata).toBeDefined();
        expect(result.metadata?.fieldType).toBe('assistantPrompt');
        expect(result.metadata?.timestamp).toBeInstanceOf(Date);
        expect(result.metadata?.excessTokens).toBeUndefined(); // No excess for valid result
        done();
      });
    });

    it('should include excess tokens for invalid results', (done) => {
      const invalidTokenResult = { ...mockTokenResult, token_count: 1500 };
      mockTokenLimitsService.getFieldLimit.and.returnValue(of(mockFieldLimit));
      mockTokenCountingService.countTokensDebounced.and.returnValue(of(invalidTokenResult));

      service.validateField('Over limit text', 'mainPrefix').subscribe(result => {
        expect(result.metadata?.excessTokens).toBe(500); // 1500 - 1000
        done();
      });
    });
  });
});
