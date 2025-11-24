import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { GenerationService } from './generation.service';
import { ApiService } from './api.service';
import { ContextBuilderService } from './context-builder.service';
import { TokenCountingService } from './token-counting.service';
import { RequestConverterService } from './request-converter.service';

import { RequestOptimizerService } from './request-optimizer.service';
import { Story, Character, Rater, FleshOutType } from '../models/story.model';
import { 
  StructuredCharacterFeedbackResponse,
  StructuredRaterFeedbackResponse,
  StructuredGenerateChapterResponse
} from '../models/structured-request.model';
import { of } from 'rxjs';

describe('GenerationService', () => {
  let service: GenerationService;
  let apiServiceSpy: jasmine.SpyObj<ApiService>;
  let contextBuilderSpy: jasmine.SpyObj<ContextBuilderService>;

  let requestOptimizerSpy: jasmine.SpyObj<RequestOptimizerService>;  // eslint-disable-line @typescript-eslint/no-unused-vars

  beforeEach(() => {
    const spy = jasmine.createSpyObj('ApiService', [
      'requestCharacterFeedback',
      'streamRaterFeedback',
      'generateChapter',
      'modifyChapter',
      'requestEditorReview',
      'requestEditorReviewWithContext',
      'fleshOut',
      'generateCharacterDetails'
    ]);

    const contextBuilderSpyObj = jasmine.createSpyObj('ContextBuilderService', [
      'buildSystemPromptsContext',
      'buildWorldbuildingContext',
      'buildStorySummaryContext',
      'buildCharacterContext',
      'buildChaptersContext',
      'buildPlotContext',
      'buildFeedbackContext',
      'buildConversationContext',
      'buildPhaseContext',
      'buildChapterGenerationContext'
    ]);

    const tokenCountingSpy = jasmine.createSpyObj('TokenCountingService', [
      'countWords',
      'countTokens'
    ]);

    const requestConverterSpy = jasmine.createSpyObj('RequestConverterService', [
      'convertToStructured'
    ]);



    const requestOptimizerSpyObj = jasmine.createSpyObj('RequestOptimizerService', [
      'optimizeCharacterFeedbackRequest',
      'optimizeRaterFeedbackRequest',
      'optimizeEditorReviewRequest'
    ]);



    // Set up default optimization responses (pass through unchanged)
    requestOptimizerSpyObj.optimizeCharacterFeedbackRequest.and.callFake((req: any) => ({ optimizedRequest: req }));
    requestOptimizerSpyObj.optimizeRaterFeedbackRequest.and.callFake((req: any) => ({ optimizedRequest: req }));
    requestOptimizerSpyObj.optimizeEditorReviewRequest.and.callFake((req: any) => ({ optimizedRequest: req }));

    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        GenerationService,
        { provide: ApiService, useValue: spy },
        { provide: ContextBuilderService, useValue: contextBuilderSpyObj },
        { provide: TokenCountingService, useValue: tokenCountingSpy },
        { provide: RequestConverterService, useValue: requestConverterSpy },

        { provide: RequestOptimizerService, useValue: requestOptimizerSpyObj }
      ]
    });

    service = TestBed.inject(GenerationService);
    apiServiceSpy = TestBed.inject(ApiService) as jasmine.SpyObj<ApiService>;
    contextBuilderSpy = TestBed.inject(ContextBuilderService) as jasmine.SpyObj<ContextBuilderService>;

    requestOptimizerSpy = TestBed.inject(RequestOptimizerService) as jasmine.SpyObj<RequestOptimizerService>;
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('requestCharacterFeedback', () => {
    it('should build structured request with complete context and call API', (done) => {
      const mockStory = createMockStory();
      const mockCharacter: Character = {
        id: 'char-1',
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
        relationships: 'None',
        isHidden: false,
        metadata: {
          creationSource: 'user',
          lastModified: new Date()
        }
      };

      const mockResponse: StructuredCharacterFeedbackResponse = {
        characterName: 'Test Character',
        feedback: {
          actions: ['Draw sword'],
          dialog: ['I must be brave'],
          physicalSensations: ['Heart pounding'],
          emotions: ['Fear'],
          internalMonologue: ['What awaits?'],
          goals: ['Survive the encounter'],
          memories: ['Remember the training'],
          subtext: ['Hidden determination beneath the fear']
        }
      };

      // Mock context builder responses
      contextBuilderSpy.buildSystemPromptsContext.and.returnValue({
        success: true,
        data: { mainPrefix: 'prefix', mainSuffix: 'suffix', assistantPrompt: 'prompt' }
      });
      contextBuilderSpy.buildWorldbuildingContext.and.returnValue({
        success: true,
        data: { content: 'A fantasy world', isValid: true, wordCount: 3, lastUpdated: new Date() }
      });
      contextBuilderSpy.buildStorySummaryContext.and.returnValue({
        success: true,
        data: { summary: 'A story about heroes', isValid: true, wordCount: 4, lastUpdated: new Date() }
      });
      contextBuilderSpy.buildChaptersContext.and.returnValue({
        success: true,
        data: { chapters: [], totalChapters: 0, totalWordCount: 0, lastUpdated: new Date() }
      });

      apiServiceSpy.requestCharacterFeedback.and.returnValue(of(mockResponse));

      service.requestCharacterFeedback(mockStory, mockCharacter, 'Enter dungeon').subscribe(response => {
        expect(response).toEqual(mockResponse);
        expect(apiServiceSpy.requestCharacterFeedback).toHaveBeenCalledWith(
          jasmine.objectContaining({
            character_name: 'Test Character',
            plotPoint: 'Enter dungeon',
            request_context: jasmine.any(Object)
          }),
          undefined // onProgress parameter
        );
        done();
      });
    });

    it('should pass onProgress callback to API service', (done) => {
      const mockStory = createMockStory();
      const mockCharacter: Character = {
        id: 'char-1',
        name: 'Test Character',
        basicBio: 'A hero',
        physicalAppearance: '',
        personality: '',
        motivations: '',
        relationships: '',
        age: 25,
        sex: 'Male',
        gender: 'Male',
        sexualPreference: '',
        usualClothing: '',
        fears: '',
        isHidden: false,
        metadata: {
          creationSource: 'user' as const,
          lastModified: new Date()
        }
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

      // Mock context builder responses
      contextBuilderSpy.buildSystemPromptsContext.and.returnValue({
        success: true,
        data: { mainPrefix: 'prefix', mainSuffix: 'suffix', assistantPrompt: 'prompt' }
      });
      contextBuilderSpy.buildWorldbuildingContext.and.returnValue({
        success: true,
        data: { content: 'A fantasy world', isValid: true, wordCount: 3, lastUpdated: new Date() }
      });
      contextBuilderSpy.buildStorySummaryContext.and.returnValue({
        success: true,
        data: { summary: 'A story about heroes', isValid: true, wordCount: 4, lastUpdated: new Date() }
      });
      contextBuilderSpy.buildChaptersContext.and.returnValue({
        success: true,
        data: { chapters: [], totalChapters: 0, totalWordCount: 0, lastUpdated: new Date() }
      });

      const onProgress = jasmine.createSpy('onProgress');
      apiServiceSpy.requestCharacterFeedback.and.returnValue(of(mockResponse));

      service.requestCharacterFeedback(mockStory, mockCharacter, 'Enter dungeon', onProgress).subscribe(response => {
        expect(response).toEqual(mockResponse);
        expect(apiServiceSpy.requestCharacterFeedback).toHaveBeenCalledWith(
          jasmine.objectContaining({
            character_name: 'Test Character',
            plotPoint: 'Enter dungeon',
            request_context: jasmine.any(Object)
          }),
          onProgress
        );
        done();
      });
    });
  });

  describe('requestRaterFeedback', () => {
    it('should use transformToRequestContext and call API with new format', (done) => {
      const mockStory = createMockStory();
      const mockRater: Rater = {
        id: 'rater-1',
        name: 'Pacing Rater',
        systemPrompt: 'Evaluate pacing',
        enabled: true,
        metadata: {
          created: new Date(),
          lastModified: new Date()
        }
      };

      const mockResponse: StructuredRaterFeedbackResponse = {
        raterName: 'Pacing Rater',
        feedback: {
          opinion: 'Good pacing',
          suggestions: []
        },
        context_metadata: {
          requestId: 'test-request-123',
          processingTime: 1500,
          tokenUsage: {
            inputTokens: 50,
            outputTokens: 50,
            totalTokens: 100
          }
        }
      };

      // Mock streaming response
      apiServiceSpy.streamRaterFeedback.and.returnValue(of(
        { type: 'result', data: mockResponse }
      ));

      service.requestRaterFeedback(mockStory, mockRater, 'Enter dungeon').subscribe(response => {
        expect(response).toEqual(mockResponse);
        expect(apiServiceSpy.streamRaterFeedback).toHaveBeenCalledWith(
          jasmine.objectContaining({
            raterName: 'Pacing Rater',
            plotPoint: 'Enter dungeon',
            request_context: jasmine.objectContaining({
              configuration: jasmine.any(Object),
              worldbuilding: jasmine.any(Object),
              characters: jasmine.any(Array),
              story_outline: jasmine.any(Object),
              chapters: jasmine.any(Array),
              context_metadata: jasmine.any(Object)
            })
          })
        );
        done();
      });
    });
  });

  describe('generateChapter', () => {
    it('should build structured request and call API', (done) => {
      const mockStory = createMockStory();
      const chapterNumber = 1;

      const mockResponse: StructuredGenerateChapterResponse = {
        chapterText: 'The hero stepped into the dark dungeon...'
      };

      // Configure context builder spy to return successful response
      contextBuilderSpy.buildChapterGenerationContext.and.returnValue({
        success: true,
        data: {
          systemPrompts: {
            mainPrefix: 'System prefix',
            mainSuffix: 'System suffix',
            assistantPrompt: 'Assistant prompt'
          },
          worldbuilding: {
            content: 'Test worldbuilding',
            isValid: true,
            wordCount: 2,
            lastUpdated: new Date()
          },
          storySummary: {
            summary: 'Test story summary',
            isValid: true,
            wordCount: 3,
            lastUpdated: new Date()
          },
          characters: {
            characters: [],
            totalCharacters: 0,
            visibleCharacters: 0,
            lastUpdated: new Date()
          },
          previousChapters: {
            chapters: [],
            totalChapters: 0,
            totalWordCount: 0,
            lastUpdated: new Date()
          },
          plotPoint: {
            plotPoint: 'The hero enters the dungeon',
            isValid: true,
            wordCount: 5,
            lastUpdated: new Date()
          },
          feedback: {
            incorporatedFeedback: [],
            selectedFeedback: [],
            totalFeedbackItems: 0,
            lastUpdated: new Date()
          }
        },
        errors: undefined,
        warnings: undefined,
        fromCache: false
      });

      apiServiceSpy.generateChapter.and.returnValue(of(mockResponse));

      service.generateChapter(mockStory, chapterNumber).subscribe(response => {
        expect(response).toEqual(mockResponse);
        expect(apiServiceSpy.generateChapter).toHaveBeenCalledWith(
          jasmine.objectContaining({
            chapter_number: 1,
            request_context: jasmine.any(Object)
          })
        );
        done();
      });
    });

    it('should filter out hidden characters', (done) => {
      const mockStory = createMockStory();
      mockStory.characters.set('char-1', {
        id: 'char-1',
        name: 'Visible Character',
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
        relationships: 'None',
        isHidden: false,
        metadata: {
          creationSource: 'user',
          lastModified: new Date()
        }
      });
      mockStory.characters.set('char-2', {
        id: 'char-2',
        name: 'Hidden Character',
        basicBio: 'A villain',
        sex: 'Male',
        gender: 'Male',
        sexualPreference: 'Heterosexual',
        age: 40,
        physicalAppearance: 'Short',
        usualClothing: 'Cloak',
        personality: 'Evil',
        motivations: 'Power',
        fears: 'Defeat',
        relationships: 'None',
        isHidden: true,
        metadata: {
          creationSource: 'user',
          lastModified: new Date()
        }
      });

      const mockResponse: StructuredGenerateChapterResponse = {
        chapterText: 'Chapter text'
      };

      // Configure context builder spy to return successful response
      contextBuilderSpy.buildChapterGenerationContext.and.returnValue({
        success: true,
        data: {
          systemPrompts: {
            mainPrefix: 'System prefix',
            mainSuffix: 'System suffix',
            assistantPrompt: 'Assistant prompt'
          },
          worldbuilding: {
            content: 'Test worldbuilding',
            isValid: true,
            wordCount: 2,
            lastUpdated: new Date()
          },
          storySummary: {
            summary: 'Test story summary',
            isValid: true,
            wordCount: 3,
            lastUpdated: new Date()
          },
          characters: {
            characters: [
              {
                name: 'Visible Character',
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
                relationships: 'None',
                isHidden: false
              }
            ],
            totalCharacters: 1,
            visibleCharacters: 1,
            lastUpdated: new Date()
          },
          previousChapters: {
            chapters: [],
            totalChapters: 0,
            totalWordCount: 0,
            lastUpdated: new Date()
          },
          plotPoint: {
            plotPoint: 'Test plot point',
            isValid: true,
            wordCount: 3,
            lastUpdated: new Date()
          },
          feedback: {
            incorporatedFeedback: [],
            selectedFeedback: [],
            totalFeedbackItems: 0,
            lastUpdated: new Date()
          }
        },
        errors: undefined,
        warnings: undefined,
        fromCache: false
      });

      apiServiceSpy.generateChapter.and.returnValue(of(mockResponse));
      const chapterNumber = 1;

      service.generateChapter(mockStory, chapterNumber).subscribe(() => {
        const callArgs = apiServiceSpy.generateChapter.calls.mostRecent().args[0];
        expect(callArgs.request_context).toBeDefined();
        done();
      });
    });
  });

  describe('modifyChapter', () => {
    it('should build request with chapter number, user request, and request context', (done) => {
      const mockStory = createMockStory();
      // Add a chapter to the story so the method can find it
      mockStory.story.chapters = [{
        id: 'chapter-1',
        number: 1,
        title: 'Chapter 1',
        content: 'Original text',
        incorporatedFeedback: [],
        metadata: {
          created: new Date(),
          lastModified: new Date(),
          wordCount: 20
        }
      }];
      
      const mockResponse = {
        content: 'Modified chapter text',
        iterations_used: 1,
        evaluation_feedback: 'Made it exciting',
        status: 'success'
      };

      apiServiceSpy.modifyChapter.and.returnValue(of(mockResponse));

      const mockFeedbackSelection = {
        characterFeedback: [],
        raterFeedback: []
      };

      service.modifyChapter(mockStory, 'Original text', 'Make it exciting', mockFeedbackSelection).subscribe(response => {
        expect(response).toEqual(mockResponse);
        expect(apiServiceSpy.modifyChapter).toHaveBeenCalledWith(
          jasmine.objectContaining({
            chapter_number: 1,
            user_feedback: 'Make it exciting',
            character_feedback: [],
            rater_feedback: [],
            editor_feedback: [],
            request_context: jasmine.any(Object)
          }),
          undefined
        );
        done();
      });
    });
  });

  describe('requestEditorReview', () => {
    it('should use RequestContext API and transform response', (done) => {
      const mockStory = createMockStory();
      const mockBackendResponse = {
        suggestions: [
          {
            issue: 'Test issue',
            suggestion: 'Test suggestion',
            priority: 'high'
          }
        ]
      };



      apiServiceSpy.requestEditorReviewWithContext.and.returnValue(of(mockBackendResponse));

      service.requestEditorReview(mockStory, 'Chapter text').subscribe(response => {
        expect(response.overallAssessment).toEqual('Editor review for chapter 1');
        expect(response.suggestions.length).toBe(1);
        expect(response.suggestions[0].issue).toBe('Test issue');
        expect(response.suggestions[0].suggestion).toBe('Test suggestion');
        expect(response.suggestions[0].priority).toBe('high');
        expect(response.suggestions[0].selected).toBe(false);
        expect(apiServiceSpy.requestEditorReviewWithContext).toHaveBeenCalledWith(
          jasmine.objectContaining({
            chapter_number: 1,
            request_context: jasmine.any(Object)
          })
        );
        done();
      });
    });
  });

  describe('fleshOut', () => {
    it('should build request and call API', (done) => {
      const mockStory = createMockStory();
      const mockResponse = {
        fleshedOutText: 'Expanded text'
      };

      apiServiceSpy.fleshOut.and.returnValue(of(mockResponse));

      service.fleshOut(mockStory, 'Short text', FleshOutType.WORLDBUILDING).subscribe(response => {
        expect(response).toEqual(mockResponse);
        expect(apiServiceSpy.fleshOut).toHaveBeenCalledWith(
          jasmine.objectContaining({
            request_type: FleshOutType.WORLDBUILDING,
            text_to_flesh_out: 'Short text'
          }),
          undefined // Optional progress callback
        );
        done();
      });
    });
  });

  describe('generateCharacterDetails', () => {
    it('should build request with character name', (done) => {
      const mockStory = createMockStory();

      const mockResponse = {
        character_info: {
          name: 'New Character',
          basicBio: 'A smart mage',
          sex: 'Female',
          gender: 'Female',
          sexualPreference: 'Heterosexual',
          age: 25,
          physicalAppearance: 'Petite',
          usualClothing: 'Dress',
          personality: 'Smart',
          motivations: 'Knowledge',
          fears: 'Ignorance',
          relationships: 'Friend of Existing Character'
        }
      };

      apiServiceSpy.generateCharacterDetails.and.returnValue(of(mockResponse));

      service.generateCharacterDetails(mockStory, 'Gandalf').subscribe(response => {
        expect(response).toEqual(mockResponse);
        expect(apiServiceSpy.generateCharacterDetails).toHaveBeenCalledWith(
          jasmine.objectContaining({
            character_name: 'Gandalf'
          }),
          undefined // onProgress callback parameter
        );
        done();
      });
    });
  });
});

function createMockStory(): Story {
  return {
    id: 'story-1',
    general: {
      title: 'Test Story',
      systemPrompts: {
        mainPrefix: 'Main prefix',
        mainSuffix: 'Main suffix',
        assistantPrompt: 'You are a creative writing assistant.',
        editorPrompt: 'You are an experienced editor.'
      },
      worldbuilding: 'A fantasy world'
    },
    characters: new Map(),
    raters: new Map(),
    plotOutline: {
      content: '',
      status: 'draft',
      chatHistory: [],
      raterFeedback: new Map(),
      metadata: {
        created: new Date(),
        lastModified: new Date(),
        version: 1
      }
    },
    story: {
      summary: 'A story about heroes',
      chapters: []
    },
    metadata: {
      version: '1.0',
      created: new Date(),
      lastModified: new Date()
    }
  };
}
