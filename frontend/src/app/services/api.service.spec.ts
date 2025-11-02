import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { of, Observable } from 'rxjs';
import { ApiService } from './api.service';
import {
  StructuredCharacterFeedbackRequest,
  StructuredCharacterFeedbackResponse,
  StructuredRaterFeedbackRequest,
  StructuredRaterFeedbackResponse,
  StructuredGenerateChapterRequest,
  StructuredGenerateChapterResponse,
  StructuredEditorReviewRequest
} from '../models/structured-request.model';
import { TokenStrategiesResponse } from '../models/token-limits.model';

describe('ApiService', () => {
  let service: ApiService;
  let httpMock: HttpTestingController;
  const baseUrl = 'http://localhost:8000/api/v1';

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [ApiService]
    });
    service = TestBed.inject(ApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('requestCharacterFeedback', () => {
    it('should send POST request to character-feedback/structured endpoint', () => {
      const request: StructuredCharacterFeedbackRequest = {
        systemPrompts: {
          mainPrefix: '',
          mainSuffix: ''
        },
        worldbuilding: {
          content: 'A fantasy world'
        },
        storySummary: {
          summary: 'A story'
        },
        previousChapters: [],
        character: {
          name: 'Test Character',
          basicBio: 'A hero',
          sex: 'Male',
          gender: 'Male',
          sexualPreference: 'Heterosexual',
          age: 30,
          physicalAppearance: 'Tall',
          usualClothing: 'Armor',
          personality: 'Brave',
          motivations: 'Justice',
          fears: 'Failure',
          relationships: 'None'
        },
        plotContext: {
          plotPoint: 'The hero enters the dungeon'
        }
      };

      const mockResponse: StructuredCharacterFeedbackResponse = {
        characterName: 'Test Character',
        feedback: {
          actions: ['Draw sword'],
          dialog: ['I must be brave'],
          physicalSensations: ['Heart pounding'],
          emotions: ['Fear', 'Determination'],
          internalMonologue: ['What dangers await?']
        }
      };

      service.requestCharacterFeedback(request).subscribe(response => {
        expect(response).toEqual(mockResponse);
      });

      const req = httpMock.expectOne(`${baseUrl}/character-feedback/structured`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(request);
      req.flush(mockResponse);
    });
  });

  describe('requestRaterFeedback', () => {
    it('should send POST request to rater-feedback/structured endpoint', () => {
      const request: StructuredRaterFeedbackRequest = {
        systemPrompts: {
          mainPrefix: '',
          mainSuffix: ''
        },
        raterPrompt: 'Evaluate pacing',
        worldbuilding: {
          content: 'A fantasy world'
        },
        storySummary: {
          summary: 'A story'
        },
        previousChapters: [],
        plotContext: {
          plotPoint: 'The hero enters the dungeon'
        }
      };

      const mockResponse: StructuredRaterFeedbackResponse = {
        raterName: 'Pacing Rater',
        feedback: {
          opinion: 'The pacing is good',
          suggestions: [
            {
              issue: 'Slow intro',
              suggestion: 'Start with action',
              priority: 'medium'
            }
          ]
        }
      };

      service.requestRaterFeedback(request).subscribe(response => {
        expect(response).toEqual(mockResponse);
      });

      const req = httpMock.expectOne(`${baseUrl}/rater-feedback/structured`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(request);
      req.flush(mockResponse);
    });
  });

  describe('generateChapter', () => {
    it('should send POST request to generate-chapter/structured endpoint', () => {
      const request: StructuredGenerateChapterRequest = {
        systemPrompts: {
          mainPrefix: '',
          mainSuffix: '',
          assistantPrompt: 'You are a writer'
        },
        worldbuilding: {
          content: 'A fantasy world'
        },
        storySummary: {
          summary: 'A story'
        },
        previousChapters: [],
        characters: [],
        plotContext: {
          plotPoint: 'The hero enters the dungeon'
        },
        feedbackContext: {
          incorporatedFeedback: []
        }
      };

      const mockResponse: StructuredGenerateChapterResponse = {
        chapterText: 'The hero stepped into the dark dungeon...'
      };

      service.generateChapter(request).subscribe(response => {
        expect(response).toEqual(mockResponse);
      });

      const req = httpMock.expectOne(`${baseUrl}/generate-chapter/structured`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(request);
      req.flush(mockResponse);
    });
  });

  describe('modifyChapter', () => {
    it('should create an observable for SSE streaming chapter modification', () => {
      const request = {
        systemPrompts: {
          mainPrefix: '',
          mainSuffix: '',
          assistantPrompt: 'You are a writer'
        },
        worldbuilding: 'A fantasy world',
        storySummary: 'A story',
        previousChapters: [],
        currentChapter: 'Original chapter text',
        userRequest: 'Make it more exciting'
      };

      const mockResponse = {
        modifiedChapter: 'The hero burst into the dark dungeon...',
        modifiedChapterText: 'The hero burst into the dark dungeon...',
        wordCount: 50,
        changesSummary: 'Made the chapter more exciting'
      };

      // Mock the SSE streaming service
      const mockSSEObservable = jasmine.createSpy('createSSEObservable').and.returnValue(
        new Observable(observer => {
          observer.next(mockResponse);
          observer.complete();
        })
      );
      
      spyOn(service['sseStreamingService'], 'createSSEObservable').and.callFake(mockSSEObservable);

      service.modifyChapter(request).subscribe(response => {
        expect(response).toEqual(mockResponse);
      });

      expect(mockSSEObservable).toHaveBeenCalledWith(
        `${baseUrl}/modify-chapter`,
        request,
        jasmine.objectContaining({
          onError: jasmine.any(Function)
        })
      );
    });

    it('should handle progress updates when provided', () => {
      const request = {
        systemPrompts: {
          mainPrefix: '',
          mainSuffix: '',
          assistantPrompt: 'You are a writer'
        },
        worldbuilding: 'A fantasy world',
        storySummary: 'A story',
        previousChapters: [],
        currentChapter: 'Original chapter text',
        userRequest: 'Make it more exciting'
      };

      const progressCallback = jasmine.createSpy('onProgress');
      
      // Mock the SSE streaming service
      const mockSSEObservable = jasmine.createSpy('createSSEObservable').and.returnValue(
        new Observable(observer => {
          observer.next({});
          observer.complete();
        })
      );
      
      spyOn(service['sseStreamingService'], 'createSSEObservable').and.callFake(mockSSEObservable);

      service.modifyChapter(request, progressCallback).subscribe();

      expect(mockSSEObservable).toHaveBeenCalledWith(
        `${baseUrl}/modify-chapter`,
        request,
        jasmine.objectContaining({
          onProgress: jasmine.any(Function),
          onError: jasmine.any(Function)
        })
      );
    });
  });

  describe('requestEditorReview', () => {
    it('should create an observable for SSE streaming editor review', () => {
      const request: StructuredEditorReviewRequest = {
        systemPrompts: {
          mainPrefix: '',
          mainSuffix: '',
          editorPrompt: 'You are an editor'
        },
        worldbuilding: {
          content: 'A fantasy world'
        },
        storySummary: {
          summary: 'A story'
        },
        previousChapters: [],
        characters: [],
        chapterToReview: 'Chapter text to review'
      };

      const observable = service.requestEditorReview(request);
      expect(observable).toBeDefined();
      expect(observable.subscribe).toBeDefined();
      
      // Note: Full SSE testing would require mocking fetch API
      // This test verifies the method returns an Observable
    });
  });

  describe('fleshOut', () => {
    it('should send POST request to flesh-out endpoint', () => {
      const request = {
        textToFleshOut: 'The hero is brave',
        context: 'character description',
        structured_context: {
          plot_elements: [
            {
              type: 'setup' as const,
              content: 'A fantasy world',
              priority: 'high' as const,
              tags: ['worldbuilding', 'setting'],
              metadata: {
                source: 'worldbuilding',
                category: 'background'
              }
            },
            {
              type: 'scene' as const,
              content: 'A story',
              priority: 'high' as const,
              tags: ['story_summary', 'plot'],
              metadata: {
                source: 'story_summary',
                category: 'narrative'
              }
            },
            {
              type: 'scene' as const,
              content: 'The hero is brave',
              priority: 'high' as const,
              tags: ['current_scene', 'flesh_out_target'],
              metadata: {
                source: 'text_to_flesh_out',
                category: 'target_content'
              }
            }
          ],
          character_contexts: [],
          user_requests: [
            {
              type: 'addition' as const,
              content: 'Expand and flesh out the following text with relevant detail: The hero is brave',
              priority: 'high' as const,
              target: 'flesh_out_target',
              context: 'character description'
            }
          ],
          system_instructions: []
        }
      };

      const mockResponse = {
        fleshedOutText: 'The hero is brave, standing tall in the face of danger...'
      };

      service.fleshOut(request).subscribe(response => {
        expect(response).toEqual(mockResponse);
      });

      const req = httpMock.expectOne(`${baseUrl}/flesh-out`);
      expect(req.request.method).toBe('POST');
      req.flush(mockResponse);
    });
  });

  describe('generateCharacterDetails', () => {
    it('should use SSE streaming service for character details generation', () => {
      const request = {
        basicBio: 'A brave knight',
        existingCharacters: [],
        structured_context: {
          plot_elements: [
            {
              type: 'setup' as const,
              content: 'A fantasy world',
              priority: 'high' as const,
              tags: ['worldbuilding', 'setting'],
              metadata: {
                source: 'worldbuilding',
                category: 'background'
              }
            },
            {
              type: 'scene' as const,
              content: 'A story',
              priority: 'high' as const,
              tags: ['story_summary', 'plot'],
              metadata: {
                source: 'story_summary',
                category: 'narrative'
              }
            }
          ],
          character_contexts: [],
          user_requests: [
            {
              type: 'general' as const,
              content: 'Generate detailed character information for: A brave knight',
              priority: 'high' as const,
              target: 'new_character',
              context: 'character_generation'
            }
          ],
          system_instructions: []
        }
      };

      const mockResponse = {
        name: 'Sir Galahad',
        sex: 'Male',
        gender: 'Male',
        sexualPreference: 'Heterosexual',
        age: 35,
        physicalAppearance: 'Tall and muscular',
        usualClothing: 'Plate armor',
        personality: 'Brave and honorable',
        motivations: 'Protect the weak',
        fears: 'Dishonor',
        relationships: 'Loyal to the king'
      };

      // Mock the SSE streaming service
      const mockSSEService = jasmine.createSpyObj('SSEStreamingService', ['createSSEObservable']);
      mockSSEService.createSSEObservable.and.returnValue(of(mockResponse));
      
      // Replace the service's SSE streaming service with our mock
      (service as any).sseStreamingService = mockSSEService;

      const mockOnProgress = jasmine.createSpy('onProgress');
      
      service.generateCharacterDetails(request, mockOnProgress).subscribe(response => {
        expect(response).toEqual(mockResponse);
      });

      expect(mockSSEService.createSSEObservable).toHaveBeenCalledWith(
        `${baseUrl}/generate-character-details`,
        request,
        jasmine.objectContaining({
          onProgress: jasmine.any(Function),
          onError: jasmine.any(Function)
        })
      );
    });
  });

  describe('getTokenStrategies', () => {
    it('should send GET request to tokens/strategies endpoint', () => {
      const mockResponse: TokenStrategiesResponse = {
        success: true,
        strategies: {
          exact: {
            description: 'Precise token count using tokenizer',
            overhead: 1.0,
            use_case: 'When you need exact token counts'
          },
          conservative: {
            description: 'Higher overhead for safety',
            overhead: 1.25,
            use_case: 'When you want to ensure you don\'t exceed limits'
          }
        },
        content_types: {
          narrative: {
            description: 'Story narrative content',
            multiplier: 1.0
          },
          system_prompt: {
            description: 'System instructions and prompts',
            multiplier: 1.15
          }
        },
        token_limits: {
          llm_context_window: 4096,
          llm_max_generation: 2048,
          context_management: {
            max_context_tokens: 3500,
            buffer_tokens: 500,
            layer_limits: {
              system_instructions: 2000,
              immediate_instructions: 500,
              recent_story: 800,
              character_scene_data: 600,
              plot_world_summary: 600
            }
          },
          recommended_limits: {
            system_prompt_prefix: 500,
            system_prompt_suffix: 500,
            writing_assistant_prompt: 1000,
            writing_editor_prompt: 1000
          }
        },
        default_strategy: 'exact',
        batch_limits: {
          max_texts_per_request: 50,
          max_text_size_bytes: 100000
        }
      };

      service.getTokenStrategies().subscribe(response => {
        expect(response).toEqual(mockResponse);
      });

      const req = httpMock.expectOne(`${baseUrl}/tokens/strategies`);
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);
    });

    it('should handle error response from tokens/strategies endpoint', () => {
      const errorResponse = {
        success: false,
        error: 'Internal server error'
      };

      service.getTokenStrategies().subscribe({
        next: () => fail('Expected error, but got success'),
        error: (error) => {
          expect(error.status).toBe(500);
        }
      });

      const req = httpMock.expectOne(`${baseUrl}/tokens/strategies`);
      expect(req.request.method).toBe('GET');
      req.flush(errorResponse, { status: 500, statusText: 'Internal Server Error' });
    });
  });
});
