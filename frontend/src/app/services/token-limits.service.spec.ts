import { TestBed, fakeAsync, tick, flush } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TokenLimitsService, SystemPromptFieldType } from './token-limits.service';
import { TokenStrategiesResponse } from '../models/token-limits.model';

describe('TokenLimitsService', () => {
  let service: TokenLimitsService;
  let httpMock: HttpTestingController;

  const mockTokenStrategiesResponse: TokenStrategiesResponse = {
    success: true,
    strategies: {
      exact: {
        description: 'Exact token counting',
        overhead: 1.0,
        use_case: 'Precise counting'
      }
    },
    content_types: {
      system_prompt: {
        description: 'System prompt content',
        multiplier: 1.0
      }
    },
    token_limits: {
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
      recommended_limits: {
        system_prompt_prefix: 600,
        system_prompt_suffix: 400,
        writing_assistant_prompt: 1200,
        writing_editor_prompt: 800
      }
    },
    default_strategy: 'exact',
    batch_limits: {
      max_texts_per_request: 10,
      max_text_size_bytes: 1048576
    }
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [TokenLimitsService]
    });
    service = TestBed.inject(TokenLimitsService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
    // Flush the initial HTTP request made in the constructor
    const req = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
    req.flush(mockTokenStrategiesResponse);
  });

  it('should load token limits on initialization', () => {
    const req = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
    expect(req.request.method).toBe('GET');
    req.flush(mockTokenStrategiesResponse);
  });

  describe('getFieldLimit', () => {
    it('should return correct limits for mainPrefix field', (done) => {
      const req = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
      req.flush(mockTokenStrategiesResponse);

      service.getFieldLimit('mainPrefix').subscribe(result => {
        expect(result.fieldType).toBe('mainPrefix');
        expect(result.limit).toBe(600);
        expect(result.warningThreshold).toBe(480); // 80% of 600
        expect(result.criticalThreshold).toBe(540); // 90% of 600
        done();
      });
    });

    it('should return correct limits for mainSuffix field', (done) => {
      const req = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
      req.flush(mockTokenStrategiesResponse);

      service.getFieldLimit('mainSuffix').subscribe(result => {
        expect(result.fieldType).toBe('mainSuffix');
        expect(result.limit).toBe(400);
        expect(result.warningThreshold).toBe(320); // 80% of 400
        expect(result.criticalThreshold).toBe(360); // 90% of 400
        done();
      });
    });

    it('should return correct limits for assistantPrompt field', (done) => {
      const req = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
      req.flush(mockTokenStrategiesResponse);

      service.getFieldLimit('assistantPrompt').subscribe(result => {
        expect(result.fieldType).toBe('assistantPrompt');
        expect(result.limit).toBe(1200);
        expect(result.warningThreshold).toBe(960); // 80% of 1200
        expect(result.criticalThreshold).toBe(1080); // 90% of 1200
        done();
      });
    });

    it('should return correct limits for editorPrompt field', (done) => {
      const req = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
      req.flush(mockTokenStrategiesResponse);

      service.getFieldLimit('editorPrompt').subscribe(result => {
        expect(result.fieldType).toBe('editorPrompt');
        expect(result.limit).toBe(800);
        expect(result.warningThreshold).toBe(640); // 80% of 800
        expect(result.criticalThreshold).toBe(720); // 90% of 800
        done();
      });
    });

    it('should use default limits when backend fails', fakeAsync(() => {
      const req = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');

      let result: any;
      service.getFieldLimit('mainPrefix').subscribe(r => {
        result = r;
      });

      // Trigger error which will cause retries
      req.error(new ErrorEvent('Network error'));

      // Handle retry 1 (after ~1s delay)
      tick(1500);
      let retryReq = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
      retryReq.error(new ErrorEvent('Network error'));

      // Handle retry 2 (after ~2s delay)
      tick(2500);
      retryReq = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
      retryReq.error(new ErrorEvent('Network error'));

      // Handle retry 3 (after ~4s delay)
      tick(5000);
      retryReq = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
      retryReq.error(new ErrorEvent('Network error'));

      // Wait for error handling to complete
      flush();

      expect(result.fieldType).toBe('mainPrefix');
      expect(result.limit).toBe(500); // Default fallback
      expect(result.warningThreshold).toBe(400);
      expect(result.criticalThreshold).toBe(450);
    }));
  });

  describe('getAllFieldLimits', () => {
    it('should return limits for all field types', (done) => {
      const req = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
      req.flush(mockTokenStrategiesResponse);

      service.getAllFieldLimits().subscribe(results => {
        expect(results.length).toBe(5);
        
        const fieldTypes = results.map(r => r.fieldType);
        expect(fieldTypes).toContain('mainPrefix');
        expect(fieldTypes).toContain('mainSuffix');
        expect(fieldTypes).toContain('assistantPrompt');
        expect(fieldTypes).toContain('editorPrompt');
        expect(fieldTypes).toContain('raterSystemPrompt');
        
        const mainPrefixResult = results.find(r => r.fieldType === 'mainPrefix');
        expect(mainPrefixResult?.limit).toBe(600);
        
        done();
      });
    });
  });

  describe('getCurrentLimits', () => {
    it('should return null initially', () => {
      expect(service.getCurrentLimits()).toBeNull();
      // Flush the initial HTTP request made in the constructor
      const req = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
      req.flush(mockTokenStrategiesResponse);
    });

    it('should return loaded limits after successful load', (done) => {
      const req = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
      req.flush(mockTokenStrategiesResponse);

      setTimeout(() => {
        const limits = service.getCurrentLimits();
        expect(limits).toBeTruthy();
        expect(limits?.recommended_limits.system_prompt_prefix).toBe(600);
        done();
      }, 0);
    });
  });

  describe('isLoading', () => {
    it('should emit loading state changes', (done) => {
      const loadingStates: boolean[] = [];
      
      service.isLoading().subscribe(isLoading => {
        loadingStates.push(isLoading);
        
        if (loadingStates.length === 2) {
          expect(loadingStates[0]).toBe(true); // Initially loading
          expect(loadingStates[1]).toBe(false); // After load complete
          done();
        }
      });

      const req = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
      req.flush(mockTokenStrategiesResponse);
    });
  });

  describe('refreshLimits', () => {
    it('should reload limits from backend', (done) => {
      // Initial load
      const initialReq = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
      initialReq.flush(mockTokenStrategiesResponse);

      let emissionCount = 0;
      // Refresh
      service.refreshLimits().subscribe(limits => {
        emissionCount++;
        // Skip the first emission (current cached value)
        if (emissionCount > 1) {
          expect(limits).toBeTruthy();
          expect(limits.recommended_limits.system_prompt_prefix).toBe(600);
          done();
        }
      });

      const refreshReq = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
      refreshReq.flush(mockTokenStrategiesResponse);
    });

    it('should return default limits when refresh fails', fakeAsync(() => {
      // Initial load
      const initialReq = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
      initialReq.flush(mockTokenStrategiesResponse);
      tick();

      let finalLimits: any;
      // Refresh with error
      service.refreshLimits().subscribe(limits => {
        finalLimits = limits;
      });

      const refreshReq = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
      refreshReq.error(new ErrorEvent('Network error'));

      // Handle retry 1
      tick(1500);
      let retryReq = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
      retryReq.error(new ErrorEvent('Network error'));

      // Handle retry 2
      tick(2500);
      retryReq = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
      retryReq.error(new ErrorEvent('Network error'));

      // Handle retry 3
      tick(5000);
      retryReq = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
      retryReq.error(new ErrorEvent('Network error'));

      flush();

      expect(finalLimits).toBeTruthy();
      // Service should use fallback defaults when refresh fails
      expect(finalLimits.recommended_limits.system_prompt_prefix).toBe(500);
    }));
  });

  describe('clearCache', () => {
    it('should clear cached token limits', (done) => {
      // Initial load
      const req = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
      req.flush(mockTokenStrategiesResponse);

      // Verify limits are loaded
      setTimeout(() => {
        expect(service.getCurrentLimits()).toBeTruthy();

        // Clear cache
        service.clearCache();

        // Verify limits are cleared
        expect(service.getCurrentLimits()).toBeNull();
        done();
      }, 0);
    });
  });

  describe('getTokenLimits', () => {
    it('should return token limits state with loading and error information', (done) => {
      const req = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
      req.flush(mockTokenStrategiesResponse);

      service.getTokenLimits().subscribe(state => {
        expect(state.limits).toBeTruthy();
        expect(state.isLoading).toBe(false);
        expect(state.error).toBeNull();
        expect(state.lastUpdated).toBeTruthy();
        done();
      });
    });

    it('should return error state when backend fails', fakeAsync(() => {
      const req = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');

      let state: any;
      service.getTokenLimits().subscribe(s => {
        state = s;
      });

      // Trigger error which will cause retries
      req.error(new ErrorEvent('Network error'));

      // Handle retry 1
      tick(1500);
      let retryReq = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
      retryReq.error(new ErrorEvent('Network error'));

      // Handle retry 2
      tick(2500);
      retryReq = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
      retryReq.error(new ErrorEvent('Network error'));

      // Handle retry 3
      tick(5000);
      retryReq = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
      retryReq.error(new ErrorEvent('Network error'));

      // Wait for error handling to complete
      flush();

      expect(state.limits).toBeTruthy(); // Should have default limits
      expect(state.error).toBeTruthy();
      expect(state.lastUpdated).toBeTruthy();
    }));
  });

  describe('TTL caching', () => {
    beforeEach(() => {
      // Mock Date.now to control time
      jasmine.clock().install();
      jasmine.clock().mockDate(new Date(2023, 0, 1));
    });

    afterEach(() => {
      jasmine.clock().uninstall();
    });

    it('should not reload data within TTL period', (done) => {
      // Initial load
      const initialReq = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
      initialReq.flush(mockTokenStrategiesResponse);

      // Advance time by 2 minutes (less than 5 minute TTL)
      jasmine.clock().tick(2 * 60 * 1000);

      // Request data again - should not trigger new HTTP request
      service.getFieldLimit('mainPrefix').subscribe(result => {
        expect(result.limit).toBe(600);
        httpMock.expectNone('http://localhost:8000/api/v1/tokens/strategies');
        done();
      });
    });

    it('should reload data after TTL expires', (done) => {
      // Initial load
      const initialReq = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
      initialReq.flush(mockTokenStrategiesResponse);

      // Advance time by 6 minutes (more than 5 minute TTL)
      jasmine.clock().tick(6 * 60 * 1000);

      let called = false;
      // Request data again - should trigger new HTTP request
      service.getFieldLimit('mainPrefix').subscribe(result => {
        if (!called) {
          called = true;
          expect(result.limit).toBe(600);
          done();
        }
      });
      const refreshReq = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
      refreshReq.flush(mockTokenStrategiesResponse);
    });
  });

  describe('error handling', () => {
    it('should handle HTTP errors gracefully', fakeAsync(() => {
      const req = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
      req.error(new ErrorEvent('Network error'));

      // Handle retry 1
      tick(1500);
      let retryReq = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
      retryReq.error(new ErrorEvent('Network error'));

      // Handle retry 2
      tick(2500);
      retryReq = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
      retryReq.error(new ErrorEvent('Network error'));

      // Handle retry 3
      tick(5000);
      retryReq = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
      retryReq.error(new ErrorEvent('Network error'));

      flush();

      // Should not throw and should use defaults
      expect(() => service.getCurrentLimits()).not.toThrow();
    }));

    it('should handle malformed response gracefully', () => {
      const req = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
      req.flush({ invalid: 'response' });

      // Should not throw and should use defaults
      expect(() => service.getCurrentLimits()).not.toThrow();
    });
  });

  describe('field type mapping', () => {
    it('should map all field types correctly', (done) => {
      const req = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
      req.flush(mockTokenStrategiesResponse);

      const fieldTypes: SystemPromptFieldType[] = ['mainPrefix', 'mainSuffix', 'assistantPrompt', 'editorPrompt', 'raterSystemPrompt'];
      const expectedLimits = [600, 400, 1200, 800, 1200]; // raterSystemPrompt uses same limit as assistantPrompt

      let completedCount = 0;
      fieldTypes.forEach((fieldType, index) => {
        service.getFieldLimit(fieldType).subscribe(result => {
          expect(result.limit).toBe(expectedLimits[index]);
          completedCount++;
          if (completedCount === fieldTypes.length) {
            done();
          }
        });
      });
    });

    it('should return default limit for unknown field type', (done) => {
      const req = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
      req.flush(mockTokenStrategiesResponse);

      // Cast to bypass TypeScript checking for testing
      service.getFieldLimit('unknownField' as SystemPromptFieldType).subscribe(result => {
        expect(result.limit).toBe(500); // Default fallback
        done();
      });
    });
  });

  describe('threshold calculations', () => {
    it('should calculate thresholds correctly for various limits', (done) => {
      const req = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
      req.flush(mockTokenStrategiesResponse);

      service.getFieldLimit('assistantPrompt').subscribe(result => {
        expect(result.limit).toBe(1200);
        expect(result.warningThreshold).toBe(960); // Math.floor(1200 * 0.8)
        expect(result.criticalThreshold).toBe(1080); // Math.floor(1200 * 0.9)
        done();
      });
    });

    it('should handle edge case of very small limits', (done) => {
      const smallLimitsResponse = {
        ...mockTokenStrategiesResponse,
        token_limits: {
          ...mockTokenStrategiesResponse.token_limits,
          recommended_limits: {
            system_prompt_prefix: 5,
            system_prompt_suffix: 3,
            writing_assistant_prompt: 1,
            writing_editor_prompt: 2
          }
        }
      };

      const req = httpMock.expectOne('http://localhost:8000/api/v1/tokens/strategies');
      req.flush(smallLimitsResponse);

      service.getFieldLimit('mainPrefix').subscribe(result => {
        expect(result.limit).toBe(5);
        expect(result.warningThreshold).toBe(4); // Math.floor(5 * 0.8)
        expect(result.criticalThreshold).toBe(4); // Math.floor(5 * 0.9)
        done();
      });
    });
  });
});
