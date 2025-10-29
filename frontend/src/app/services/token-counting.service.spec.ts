import { TestBed, fakeAsync, tick, flushMicrotasks } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TokenCountingService } from './token-counting.service';
import {
  TokenCountResponse,
  ContentType,
  CountingStrategy,
  TokenCountError,
  DEFAULT_TOKEN_COUNTING_CONFIG
} from '../models/token.model';

describe('TokenCountingService', () => {
  let service: TokenCountingService;
  let httpMock: HttpTestingController;
  const baseUrl = 'http://localhost:8000/api/v1/tokens';

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [TokenCountingService]
    });
    service = TestBed.inject(TokenCountingService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    service.clearCache();
  });

  describe('Service Initialization', () => {
    it('should be created', () => {
      expect(service).toBeTruthy();
    });

    it('should initialize with default configuration', () => {
      const loadingState = service.getLoadingState();
      expect(loadingState).toBeDefined();
    });

    it('should accept custom configuration', () => {
      const customService = new TokenCountingService(
        TestBed.inject(HttpClientTestingModule) as any
      );
      expect(customService).toBeTruthy();
    });
  });

  describe('countTokens', () => {
    const mockResponse: TokenCountResponse = {
      success: true,
      results: [{
        text: 'Hello world',
        token_count: 2,
        content_type: ContentType.UNKNOWN,
        strategy: CountingStrategy.EXACT,
        overhead_applied: 1.0,
        metadata: {}
      }],
      summary: { total_tokens: 2 }
    };

    it('should count tokens for a single text', (done) => {
      service.countTokens('Hello world').subscribe(result => {
        expect(result.text).toBe('Hello world');
        expect(result.token_count).toBe(2);
        expect(result.content_type).toBe(ContentType.UNKNOWN);
        done();
      });

      const req = httpMock.expectOne(`${baseUrl}/count`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body.texts).toEqual([{ text: 'Hello world', content_type: undefined }]);
      req.flush(mockResponse);
    });

    it('should use specified content type and strategy', (done) => {
      service.countTokens('System prompt', ContentType.SYSTEM_PROMPT, CountingStrategy.CONSERVATIVE)
        .subscribe(result => {
          expect(result.content_type).toBe(ContentType.SYSTEM_PROMPT);
          done();
        });

      const req = httpMock.expectOne(`${baseUrl}/count`);
      expect(req.request.body.texts[0].content_type).toBe(ContentType.SYSTEM_PROMPT);
      expect(req.request.body.strategy).toBe(CountingStrategy.CONSERVATIVE);

      // Deep copy to avoid mutating the shared mockResponse
      const response: TokenCountResponse = {
        success: true,
        results: [{
          text: 'System prompt',
          token_count: 2,
          content_type: ContentType.SYSTEM_PROMPT,
          strategy: CountingStrategy.CONSERVATIVE,
          overhead_applied: 1.0,
          metadata: {}
        }],
        summary: { total_tokens: 2 }
      };
      req.flush(response);
    });

    it('should return cached result on subsequent calls', (done) => {
      const text = 'Cached text';

      // First call
      service.countTokens(text).subscribe(result => {
        expect(result.token_count).toBe(2);

        // Second call should use cache (no HTTP request)
        service.countTokens(text).subscribe(cachedResult => {
          expect(cachedResult.token_count).toBe(2);
          expect(cachedResult.text).toBe(text);
          done();
        });
      });

      const req = httpMock.expectOne(`${baseUrl}/count`);
      const cachedResponse: TokenCountResponse = {
        success: true,
        results: [{
          text: text,
          token_count: 2,
          content_type: ContentType.UNKNOWN,
          strategy: CountingStrategy.EXACT,
          overhead_applied: 1.0,
          metadata: {}
        }],
        summary: { total_tokens: 2 }
      };
      req.flush(cachedResponse);

      // No additional HTTP requests should be made
      httpMock.expectNone(`${baseUrl}/count`);
    });

    it('should handle API errors gracefully', fakeAsync(() => {
      let errorReceived = false;

      service.countTokens('Error text').subscribe({
        next: () => fail('Should have thrown an error'),
        error: (error: TokenCountError) => {
          expect(error.message).toContain('Server error occurred');
          expect(error.code).toBe('SERVER_ERROR');
          errorReceived = true;
        }
      });

      // Handle all retry attempts by responding to pending requests then advancing time
      // Service makes 4 total requests (initial + 3 retries)
      const delays = [1000, 2000, 4000]; // delays between retries

      for (let i = 0; i < 4; i++) {
        // Find and respond to the current pending request
        const pending = httpMock.match(`${baseUrl}/count`);
        if (pending.length > 0 && !pending[0].cancelled) {
          pending[0].flush('Server Error', { status: 500, statusText: 'Internal Server Error' });
        }

        // Advance time for the next retry (except after the last one)
        if (i < 3) {
          tick(delays[i]);
          flushMicrotasks();
        }
      }

      flushMicrotasks(); // Allow final error to propagate
      expect(errorReceived).toBe(true);
    }));
  });

  describe('countTokensBatch', () => {
    const mockBatchResponse: TokenCountResponse = {
      success: true,
      results: [
        {
          text: 'First text',
          token_count: 2,
          content_type: ContentType.NARRATIVE,
          strategy: CountingStrategy.EXACT,
          overhead_applied: 1.0,
          metadata: {}
        },
        {
          text: 'Second text',
          token_count: 3,
          content_type: ContentType.DIALOGUE,
          strategy: CountingStrategy.EXACT,
          overhead_applied: 1.0,
          metadata: {}
        }
      ],
      summary: { total_tokens: 5 }
    };

    it('should count tokens for multiple texts', (done) => {
      const items = [
        { text: 'First text', content_type: ContentType.NARRATIVE },
        { text: 'Second text', content_type: ContentType.DIALOGUE }
      ];

      service.countTokensBatch(items).subscribe(results => {
        expect(results.length).toBe(2);
        expect(results[0].text).toBe('First text');
        expect(results[1].text).toBe('Second text');
        expect(results[0].token_count).toBe(2);
        expect(results[1].token_count).toBe(3);
        done();
      });

      const req = httpMock.expectOne(`${baseUrl}/count`);
      expect(req.request.body.texts).toEqual(items);
      req.flush(mockBatchResponse);
    });

    it('should return empty array for empty input', (done) => {
      service.countTokensBatch([]).subscribe(results => {
        expect(results).toEqual([]);
        done();
      });

      httpMock.expectNone(`${baseUrl}/count`);
    });

    it('should use cache for some items and API for others', (done) => {
      const cachedText = 'Cached text';
      const newText = 'New text';
      
      // First, cache one item
      service.countTokens(cachedText).subscribe(() => {
        // Now batch request with cached and new items
        const items = [
          { text: cachedText },
          { text: newText }
        ];

        service.countTokensBatch(items).subscribe(results => {
          expect(results.length).toBe(2);
          // Should have results for both cached and new items
          const cachedResult = results.find(r => r.text === cachedText);
          const newResult = results.find(r => r.text === newText);
          expect(cachedResult).toBeDefined();
          expect(newResult).toBeDefined();
          done();
        });

        // Only the new item should trigger an API call
        const req = httpMock.expectOne(`${baseUrl}/count`);
        expect(req.request.body.texts.length).toBe(1);
        expect(req.request.body.texts[0].text).toBe(newText);
        
        const newItemResponse: TokenCountResponse = {
          success: true,
          results: [{
            text: newText,
            token_count: 3,
            content_type: ContentType.UNKNOWN,
            strategy: CountingStrategy.EXACT,
            overhead_applied: 1.0,
            metadata: {}
          }],
          summary: { total_tokens: 3 }
        };
        req.flush(newItemResponse);
      });

      // Initial request to cache the first item
      const initialReq = httpMock.expectOne(`${baseUrl}/count`);
      const initialResponse: TokenCountResponse = {
        success: true,
        results: [{
          text: cachedText,
          token_count: 2,
          content_type: ContentType.UNKNOWN,
          strategy: CountingStrategy.EXACT,
          overhead_applied: 1.0,
          metadata: {}
        }],
        summary: { total_tokens: 2 }
      };
      initialReq.flush(initialResponse);
    });
  });

  describe('countTokensDebounced', () => {
    it('should debounce rapid successive calls', (done) => {
      const text = 'Debounced text';
      let callCount = 0;

      // Make multiple rapid calls
      for (let i = 0; i < 5; i++) {
        service.countTokensDebounced(text).subscribe(() => {
          callCount++;
          if (callCount === 1) {
            // Only one call should succeed due to debouncing
            expect(callCount).toBe(1);
            done();
          }
        });
      }

      // Fast forward time to trigger debounce
      setTimeout(() => {
        const req = httpMock.expectOne(`${baseUrl}/count`);
        const response: TokenCountResponse = {
          success: true,
          results: [{
            text: text,
            token_count: 2,
            content_type: ContentType.UNKNOWN,
            strategy: CountingStrategy.EXACT,
            overhead_applied: 1.0,
            metadata: {}
          }],
          summary: { total_tokens: 2 }
        };
        req.flush(response);
      }, DEFAULT_TOKEN_COUNTING_CONFIG.debounceMs + 10);
    });
  });

  describe('Loading State Management', () => {
    it('should track loading state during API calls', (done) => {
      const loadingStates: boolean[] = [];

      service.getLoadingState().subscribe(state => {
        loadingStates.push(state.isLoading);
      });

      service.countTokens('Test text').subscribe(() => {
        // Wait for finalize to complete and update loading state
        setTimeout(() => {
          // Should have been loading during the request
          expect(loadingStates).toContain(true);
          expect(loadingStates[loadingStates.length - 1]).toBe(false);
          done();
        }, 0);
      });

      const req = httpMock.expectOne(`${baseUrl}/count`);
      const response: TokenCountResponse = {
        success: true,
        results: [{
          text: 'Test text',
          token_count: 2,
          content_type: ContentType.UNKNOWN,
          strategy: CountingStrategy.EXACT,
          overhead_applied: 1.0,
          metadata: {}
        }],
        summary: { total_tokens: 2 }
      };
      req.flush(response);
    });

    it('should track pending requests count', (done) => {
      let maxPendingRequests = 0;

      service.getLoadingState().subscribe(state => {
        maxPendingRequests = Math.max(maxPendingRequests, state.pendingRequests);
      });

      // Make multiple concurrent requests
      const requests = [
        service.countTokens('Text 1'),
        service.countTokens('Text 2'),
        service.countTokens('Text 3')
      ];

      Promise.all(requests.map(req => req.toPromise())).then(() => {
        expect(maxPendingRequests).toBeGreaterThan(0);
        done();
      });

      // Fulfill all requests
      const httpReqs = httpMock.match(`${baseUrl}/count`);
      httpReqs.forEach(req => {
        const response: TokenCountResponse = {
          success: true,
          results: [{
            text: req.request.body.texts[0].text,
            token_count: 2,
            content_type: ContentType.UNKNOWN,
            strategy: CountingStrategy.EXACT,
            overhead_applied: 1.0,
            metadata: {}
          }],
          summary: { total_tokens: 2 }
        };
        req.flush(response);
      });
    });
  });

  describe('Cache Management', () => {
    it('should clear cache when requested', (done) => {
      const text = 'Cacheable text';

      service.countTokens(text).subscribe(() => {
        // Verify item is cached
        service.countTokens(text).subscribe(() => {
          // Clear cache
          service.clearCache();

          // Next call should hit API again
          service.countTokens(text).subscribe(() => {
            done();
          });

          const req = httpMock.expectOne(`${baseUrl}/count`);
          const response: TokenCountResponse = {
            success: true,
            results: [{
              text: text,
              token_count: 2,
              content_type: ContentType.UNKNOWN,
              strategy: CountingStrategy.EXACT,
              overhead_applied: 1.0,
              metadata: {}
            }],
            summary: { total_tokens: 2 }
          };
          req.flush(response);
        });
      });

      const initialReq = httpMock.expectOne(`${baseUrl}/count`);
      const initialResponse: TokenCountResponse = {
        success: true,
        results: [{
          text: text,
          token_count: 2,
          content_type: ContentType.UNKNOWN,
          strategy: CountingStrategy.EXACT,
          overhead_applied: 1.0,
          metadata: {}
        }],
        summary: { total_tokens: 2 }
      };
      initialReq.flush(initialResponse);
    });

    it('should provide cache statistics', (done) => {
      const text = 'Stats text';

      service.countTokens(text).subscribe(() => {
        // Access cached item multiple times
        service.countTokens(text).subscribe(() => {
          service.countTokens(text).subscribe(() => {
            const stats = service.getCacheStats();
            expect(stats.size).toBe(1);
            expect(stats.totalHits).toBe(2);
            expect(stats.hitRate).toBeGreaterThan(0);
            done();
          });
        });
      });

      const req = httpMock.expectOne(`${baseUrl}/count`);
      const response: TokenCountResponse = {
        success: true,
        results: [{
          text: text,
          token_count: 2,
          content_type: ContentType.UNKNOWN,
          strategy: CountingStrategy.EXACT,
          overhead_applied: 1.0,
          metadata: {}
        }],
        summary: { total_tokens: 2 }
      };
      req.flush(response);
    });
  });

  describe('Error Handling', () => {
    it('should handle network errors', fakeAsync(() => {
      let errorReceived = false;

      service.countTokens('Network error text').subscribe({
        next: () => fail('Should have thrown an error'),
        error: (error: TokenCountError) => {
          expect(error.code).toBe('NETWORK_ERROR');
          expect(error.message).toContain('Network error');
          errorReceived = true;
        }
      });

      // Handle all retry attempts by responding to pending requests then advancing time
      const delays = [1000, 2000, 4000]; // delays between retries

      for (let i = 0; i < 4; i++) {
        const pending = httpMock.match(`${baseUrl}/count`);
        if (pending.length > 0 && !pending[0].cancelled) {
          pending[0].error(new ErrorEvent('Network error'));
        }

        if (i < 3) {
          tick(delays[i]);
          flushMicrotasks();
        }
      }

      flushMicrotasks();
      expect(errorReceived).toBe(true);
    }));

    it('should handle validation errors', fakeAsync(() => {
      let errorReceived = false;

      service.countTokens('Validation error text').subscribe({
        next: () => fail('Should have thrown an error'),
        error: (error: TokenCountError) => {
          expect(error.code).toBe('VALIDATION_ERROR');
          expect(error.message).toContain('Validation error');
          errorReceived = true;
        }
      });

      // Handle all retry attempts by responding to pending requests then advancing time
      const delays = [1000, 2000, 4000]; // delays between retries

      for (let i = 0; i < 4; i++) {
        const pending = httpMock.match(`${baseUrl}/count`);
        if (pending.length > 0 && !pending[0].cancelled) {
          pending[0].flush('Validation Error', { status: 422, statusText: 'Unprocessable Entity' });
        }

        if (i < 3) {
          tick(delays[i]);
          flushMicrotasks();
        }
      }

      flushMicrotasks();
      expect(errorReceived).toBe(true);
    }));

    it('should handle bad request errors', fakeAsync(() => {
      let errorReceived = false;

      service.countTokens('Bad request text').subscribe({
        next: () => fail('Should have thrown an error'),
        error: (error: TokenCountError) => {
          expect(error.code).toBe('BAD_REQUEST');
          expect(error.message).toContain('Invalid request format');
          errorReceived = true;
        }
      });

      // Handle all retry attempts by responding to pending requests then advancing time
      const delays = [1000, 2000, 4000]; // delays between retries

      for (let i = 0; i < 4; i++) {
        const pending = httpMock.match(`${baseUrl}/count`);
        if (pending.length > 0 && !pending[0].cancelled) {
          pending[0].flush('Bad Request', { status: 400, statusText: 'Bad Request' });
        }

        if (i < 3) {
          tick(delays[i]);
          flushMicrotasks();
        }
      }

      flushMicrotasks();
      expect(errorReceived).toBe(true);
    }));
  });

  describe('Batch Processing', () => {
    it('should process batched requests', (done) => {
      const text = 'Batched text';
      
      service.countTokensBatched(text, ContentType.NARRATIVE, {
        strategy: 'immediate'
      }).subscribe(result => {
        expect(result.text).toBe(text);
        expect(result.content_type).toBe(ContentType.NARRATIVE);
        done();
      });

      const req = httpMock.expectOne(`${baseUrl}/count`);
      const response: TokenCountResponse = {
        success: true,
        results: [{
          text: text,
          token_count: 2,
          content_type: ContentType.NARRATIVE,
          strategy: CountingStrategy.EXACT,
          overhead_applied: 1.0,
          metadata: {}
        }],
        summary: { total_tokens: 2 }
      };
      req.flush(response);
    });
  });

  describe('Hash Function', () => {
    it('should generate consistent hash keys', () => {
      const service1 = TestBed.inject(TokenCountingService);
      const service2 = TestBed.inject(TokenCountingService);
      
      // Access private method through any cast for testing
      const hash1 = (service1 as any).generateCacheKey('test', ContentType.NARRATIVE, CountingStrategy.EXACT);
      const hash2 = (service2 as any).generateCacheKey('test', ContentType.NARRATIVE, CountingStrategy.EXACT);
      
      expect(hash1).toBe(hash2);
      expect(hash1).toBeTruthy();
    });

    it('should generate different hashes for different inputs', () => {
      const service1 = TestBed.inject(TokenCountingService);
      
      const hash1 = (service1 as any).generateCacheKey('test1', ContentType.NARRATIVE, CountingStrategy.EXACT);
      const hash2 = (service1 as any).generateCacheKey('test2', ContentType.NARRATIVE, CountingStrategy.EXACT);
      
      expect(hash1).not.toBe(hash2);
    });
  });
});
