import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { of, Observable } from 'rxjs';
import { ApiService } from './api.service';
import { SSEStreamingService } from './sse-streaming.service';
import {
  StructuredCharacterFeedbackResponse,
  StructuredRaterFeedbackRequest,
  StructuredRaterFeedbackResponse,
  StructuredGenerateChapterResponse,
  StructuredEditorReviewRequest,
  StructuredEditorReviewResponse
} from '../models/structured-request.model';
import { CharacterFeedbackRequest } from './api.service';
import { transformToRequestContext } from '../utils/context-transformer';
import { BackendGenerateChapterRequest, FleshOutType } from '../models/story.model';
import { TokenStrategiesResponse } from '../models/token-limits.model';

describe('ApiService', () => {
  let service: ApiService;
  let httpMock: HttpTestingController;
  let sseStreamingServiceSpy: jasmine.SpyObj<SSEStreamingService>;
  const baseUrl = 'http://localhost:8000/api/v1';

  beforeEach(() => {
    sseStreamingServiceSpy = jasmine.createSpyObj('SSEStreamingService', ['createSSEObservable']);

    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        ApiService,
        { provide: SSEStreamingService, useValue: sseStreamingServiceSpy }
      ]
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
    it('should use SSE streaming for character-feedback endpoint', () => {
      // Create a minimal mock story for the transformer
      const mockStory = {
        id: 'test-story',
        general: {
          title: 'Test Story',
          systemPrompts: {
            mainPrefix: 'Test prefix',
            mainSuffix: 'Test suffix',
            assistantPrompt: '',
            editorPrompt: ''
          },
          worldbuilding: 'A fantasy world'
        },
        characters: new Map(),
        raters: new Map(),
        story: {
          summary: 'A story',
          chapters: []
        },
        plotOutline: {
          content: '',
          status: 'draft' as const,
          chatHistory: [],
          raterFeedback: new Map(),
          metadata: {
            created: new Date(),
            lastModified: new Date(),
            version: 1
          }
        },
        metadata: {
          version: '1.0',
          created: new Date(),
          lastModified: new Date()
        }
      };

      const request: CharacterFeedbackRequest = {
        character_name: 'Test Character',
        plotPoint: 'The hero enters the dungeon',
        request_context: transformToRequestContext(mockStory)
      };

      const mockResponse: StructuredCharacterFeedbackResponse = {
        characterName: 'Test Character',
        feedback: {
          actions: ['Draw sword'],
          dialog: ['I must be brave'],
          physicalSensations: ['Heart pounding'],
          emotions: ['Fear', 'Determination'],
          internalMonologue: ['What dangers await?'],
          goals: ['Survive the encounter'],
          memories: ['Remember the training'],
          subtext: ['Hidden determination beneath the fear']
        }
      };

      sseStreamingServiceSpy.createSSEObservable.and.returnValue(of(mockResponse));

      service.requestCharacterFeedback(request).subscribe(response => {
        expect(response).toEqual(mockResponse);
      });

      expect(sseStreamingServiceSpy.createSSEObservable).toHaveBeenCalledWith(
        `${baseUrl}/character-feedback`,
        request,
        jasmine.objectContaining({
          onProgress: undefined,
          onError: jasmine.any(Function)
        })
      );
    });

    it('should pass onProgress callback to SSE service', () => {
      const mockStory = {
        id: 'test-story',
        general: {
          title: 'Test Story',
          systemPrompts: {
            mainPrefix: 'Test prefix',
            mainSuffix: 'Test suffix',
            assistantPrompt: '',
            editorPrompt: ''
          },
          worldbuilding: 'A fantasy world'
        },
        characters: new Map(),
        raters: new Map(),
        story: {
          summary: 'A story',
          chapters: []
        },
        plotOutline: {
          content: '',
          status: 'draft' as const,
          chatHistory: [],
          raterFeedback: new Map(),
          metadata: {
            created: new Date(),
            lastModified: new Date(),
            version: 1
          }
        },
        metadata: {
          version: '1.0',
          created: new Date(),
          lastModified: new Date()
        }
      };

      const request: CharacterFeedbackRequest = {
        character_name: 'Test Character',
        plotPoint: 'The hero enters the dungeon',
        request_context: transformToRequestContext(mockStory)
      };

      const mockResponse: StructuredCharacterFeedbackResponse = {
        characterName: 'Test Character',
        feedback: {
          actions: ['Draw sword'],
          dialog: ['I must be brave'],
          physicalSensations: ['Heart pounding'],
          emotions: ['Fear', 'Determination'],
          internalMonologue: ['What dangers await?'],
          goals: ['Survive the encounter'],
          memories: ['Remember the training'],
          subtext: ['Hidden determination beneath the fear']
        }
      };

      const onProgress = jasmine.createSpy('onProgress');
      sseStreamingServiceSpy.createSSEObservable.and.returnValue(of(mockResponse));

      service.requestCharacterFeedback(request, onProgress).subscribe(response => {
        expect(response).toEqual(mockResponse);
      });

      expect(sseStreamingServiceSpy.createSSEObservable).toHaveBeenCalledWith(
        `${baseUrl}/character-feedback`,
        request,
        jasmine.objectContaining({
          onProgress: onProgress,
          onError: jasmine.any(Function)
        })
      );
    });
  });

  describe('requestRaterFeedback', () => {
    it('should use streaming API and return final result', () => {
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
        },
        context_metadata: undefined
      };

      // Mock the streamRaterFeedback method to return streaming events
      spyOn(service, 'streamRaterFeedback').and.returnValue(of(
        { type: 'status', phase: 'PROCESSING', message: 'Processing...', progress: 50 },
        { type: 'result', data: mockResponse }
      ));

      service.requestRaterFeedback(request).subscribe(response => {
        expect(response).toEqual(mockResponse);
      });

      expect(service.streamRaterFeedback).toHaveBeenCalledWith(jasmine.objectContaining({
        raterPrompt: 'Evaluate pacing',
        plotPoint: 'The hero enters the dungeon'
      }));
    });
  });

  describe('generateChapter', () => {
    it('should create an observable for SSE streaming chapter generation', () => {
      const request: BackendGenerateChapterRequest = {
        chapter_number: 1,
        request_context: {
          configuration: {
            system_prompts: {
              main_prefix: 'Test prefix',
              main_suffix: 'Test suffix',
              assistant_prompt: 'Test assistant',
              editor_prompt: 'Test editor'
            },
            raters: [],
            generation_preferences: {}
          },
          worldbuilding: {
            content: 'Test worldbuilding',
            chat_history: [],
            key_elements: []
          },
          characters: [],
          story_outline: {
            summary: 'Test summary',
            status: 'draft' as const,
            content: 'Test Story',
            outline_items: [],
            rater_feedback: [],
            chat_history: []
          },
          chapters: [],
          context_metadata: {
            story_id: 'test-story',
            story_title: 'Test Story',
            version: '1.0',
            created_at: new Date().toISOString(),
            total_characters: 0,
            total_chapters: 0,
            total_word_count: 0,
            context_size_estimate: 0,
            processing_hints: {}
          }
        }
      };

      const mockResponse: StructuredGenerateChapterResponse = {
        chapterText: 'The hero stepped into the dark dungeon...'
      };

      // Mock the SSE streaming service to avoid real fetch calls
      const mockSSEService = jasmine.createSpyObj('SSEStreamingService', ['createSSEObservable']);
      mockSSEService.createSSEObservable.and.returnValue(of(mockResponse));

      // Replace the service's SSE streaming service with our mock
      (service as any).sseStreamingService = mockSSEService;

      service.generateChapter(request).subscribe(response => {
        expect(response).toEqual(mockResponse);
      });

      expect(mockSSEService.createSSEObservable).toHaveBeenCalledWith(
        `${baseUrl}/generate-chapter`,
        request
      );
    });
  });

  describe('modifyChapter', () => {
    it('should create an observable for SSE streaming chapter modification', () => {
      const request = {
        chapter_number: 1,
        user_feedback: 'Make it more exciting',
        character_feedback: [],
        rater_feedback: [],
        editor_feedback: [],
        request_context: {
          configuration: {
            system_prompts: {
              main_prefix: '',
              main_suffix: '',
              assistant_prompt: 'You are a writer',
              editor_prompt: ''
            },
            raters: [],
            generation_preferences: {}
          },
          worldbuilding: {
            content: 'A fantasy world',
            chat_history: [],
            key_elements: []
          },
          characters: [],
          story_outline: {
            summary: 'A story',
            status: 'draft',
            content: '',
            outline_items: [],
            rater_feedback: [],
            chat_history: []
          },
          chapters: [],
          context_metadata: {
            story_id: 'test-story',
            story_title: 'Test Story',
            version: '1.0',
            created_at: new Date().toISOString(),
            total_characters: 0,
            total_chapters: 0,
            total_word_count: 0,
            context_size_estimate: 0,
            processing_hints: {}
          }
        }
      };

      const mockResponse = {
        modifiedChapter: 'The hero burst into the dark dungeon...',
        modifiedChapterText: 'The hero burst into the dark dungeon...',
        wordCount: 50,
        changesSummary: 'Made the chapter more exciting'
      };

      // Configure the SSE streaming service spy
      sseStreamingServiceSpy.createSSEObservable.and.returnValue(
        new Observable(observer => {
          observer.next(mockResponse);
          observer.complete();
        })
      );

      service.modifyChapter(request).subscribe(response => {
        expect(response).toEqual(mockResponse);
      });

      expect(sseStreamingServiceSpy.createSSEObservable).toHaveBeenCalledWith(
        `${baseUrl}/modify-chapter`,
        request,
        jasmine.objectContaining({
          onError: jasmine.any(Function)
        })
      );
    });

    it('should handle progress updates when provided', () => {
      const request = {
        chapter_number: 1,
        user_feedback: 'Make it more exciting',
        character_feedback: [],
        rater_feedback: [],
        editor_feedback: [],
        request_context: {
          configuration: {
            system_prompts: {
              main_prefix: '',
              main_suffix: '',
              assistant_prompt: 'You are a writer',
              editor_prompt: ''
            },
            raters: [],
            generation_preferences: {}
          },
          worldbuilding: {
            content: 'A fantasy world',
            chat_history: [],
            key_elements: []
          },
          characters: [],
          story_outline: {
            summary: 'A story',
            status: 'draft',
            content: '',
            outline_items: [],
            rater_feedback: [],
            chat_history: []
          },
          chapters: [],
          context_metadata: {
            story_id: 'test-story',
            story_title: 'Test Story',
            version: '1.0',
            created_at: new Date().toISOString(),
            total_characters: 0,
            total_chapters: 0,
            total_word_count: 0,
            context_size_estimate: 0,
            processing_hints: {}
          }
        }
      };

      const progressCallback = jasmine.createSpy('onProgress');

      // Configure the SSE streaming service spy
      sseStreamingServiceSpy.createSSEObservable.and.returnValue(
        new Observable(observer => {
          observer.next({});
          observer.complete();
        })
      );

      service.modifyChapter(request, progressCallback).subscribe();

      expect(sseStreamingServiceSpy.createSSEObservable).toHaveBeenCalledWith(
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

      const mockResponse: StructuredEditorReviewResponse = {
        overallAssessment: 'Good chapter',
        suggestions: [
          {
            issue: 'Weak opening',
            suggestion: 'Start with action',
            priority: 'medium',
            selected: false
          }
        ]
      };

      // Mock the SSE streaming service to avoid real fetch calls
      const mockSSEService = jasmine.createSpyObj('SSEStreamingService', ['createSSEObservable']);
      mockSSEService.createSSEObservable.and.returnValue(of(mockResponse));

      // Replace the service's SSE streaming service with our mock
      (service as any).sseStreamingService = mockSSEService;

      service.requestEditorReview(request).subscribe(response => {
        expect(response).toEqual(mockResponse);
      });

      expect(mockSSEService.createSSEObservable).toHaveBeenCalledWith(
        `${baseUrl}/editor-review`,
        request
      );
    });
  });

  describe('fleshOut', () => {
    it('should use SSE streaming service for flesh-out', () => {
      const request = {
        request_type: FleshOutType.WORLDBUILDING,
        text_to_flesh_out: 'The hero is brave',
        request_context: {
          configuration: {
            system_prompts: {
              main_prefix: 'Test prefix',
              main_suffix: 'Test suffix',
              assistant_prompt: 'Test assistant',
              editor_prompt: 'Test editor'
            },
            raters: [],
            generation_preferences: {}
          },
          worldbuilding: {
            content: 'A fantasy world',
            chat_history: [],
            key_elements: []
          },
          characters: [],
          story_outline: {
            summary: 'A story',
            status: 'draft' as const,
            content: 'Test Story',
            outline_items: [],
            rater_feedback: [],
            chat_history: []
          },
          chapters: [],
          context_metadata: {
            story_id: 'test-story',
            story_title: 'Test Story',
            version: '1.0',
            created_at: new Date().toISOString(),
            total_characters: 0,
            total_chapters: 0,
            total_word_count: 0,
            context_size_estimate: 0,
            processing_hints: {}
          }
        }
      };

      const mockResponse = {
        fleshedOutText: 'The hero is brave, standing tall in the face of danger...'
      };

      // Mock the SSE streaming service
      const mockSSEService = jasmine.createSpyObj('SSEStreamingService', ['createSSEObservable']);
      mockSSEService.createSSEObservable.and.returnValue(of(mockResponse));

      // Replace the service's SSE streaming service with our mock
      (service as any).sseStreamingService = mockSSEService;

      const mockOnProgress = jasmine.createSpy('onProgress');

      service.fleshOut(request, mockOnProgress).subscribe(response => {
        expect(response).toEqual(mockResponse);
      });

      expect(mockSSEService.createSSEObservable).toHaveBeenCalledWith(
        `${baseUrl}/flesh-out`,
        request,
        jasmine.objectContaining({
          onProgress: jasmine.any(Function),
          onError: jasmine.any(Function)
        })
      );
    });
  });

  describe('generateCharacterDetails', () => {
    it('should use SSE streaming service for character details generation', () => {
      const request = {
        character_name: 'Sir Galahad',
        request_context: {
          configuration: {
            system_prompts: {
              main_prefix: 'Test prefix',
              main_suffix: 'Test suffix',
              assistant_prompt: 'Test assistant',
              editor_prompt: 'Test editor'
            },
            raters: [],
            generation_preferences: {}
          },
          worldbuilding: {
            content: 'A fantasy world',
            chat_history: [],
            key_elements: []
          },
          characters: [],
          story_outline: {
            summary: 'A story',
            status: 'draft' as const,
            content: 'Test Story',
            outline_items: [],
            rater_feedback: [],
            chat_history: []
          },
          chapters: [],
          context_metadata: {
            story_id: 'test-story',
            story_title: 'Test Story',
            version: '1.0',
            created_at: new Date().toISOString(),
            total_characters: 0,
            total_chapters: 0,
            total_word_count: 0,
            context_size_estimate: 0,
            processing_hints: {}
          }
        }
      };

      const mockResponse = {
        character_info: {
          name: 'Sir Galahad',
          basicBio: 'A noble knight',
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
        }
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
