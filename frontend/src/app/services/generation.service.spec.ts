import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { GenerationService } from './generation.service';
import { ApiService } from './api.service';
import { ContextBuilderService } from './context-builder.service';
import { TokenCountingService } from './token-counting.service';
import { RequestConverterService } from './request-converter.service';
import { RequestValidatorService } from './request-validator.service';
import { RequestOptimizerService } from './request-optimizer.service';
import { Story, Character, Rater } from '../models/story.model';
import { 
  StructuredCharacterFeedbackResponse,
  StructuredRaterFeedbackResponse,
  StructuredGenerateChapterResponse,
  StructuredEditorReviewResponse
} from '../models/structured-request.model';
import { of } from 'rxjs';

describe('GenerationService', () => {
  let service: GenerationService;
  let apiServiceSpy: jasmine.SpyObj<ApiService>;
  let contextBuilderSpy: jasmine.SpyObj<ContextBuilderService>;
  let requestValidatorSpy: jasmine.SpyObj<RequestValidatorService>;  // eslint-disable-line @typescript-eslint/no-unused-vars
  let requestOptimizerSpy: jasmine.SpyObj<RequestOptimizerService>;  // eslint-disable-line @typescript-eslint/no-unused-vars

  beforeEach(() => {
    const spy = jasmine.createSpyObj('ApiService', [
      'requestCharacterFeedback',
      'streamRaterFeedback',
      'generateChapter',
      'modifyChapter',
      'requestEditorReview',
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

    const requestValidatorSpyObj = jasmine.createSpyObj('RequestValidatorService', [
      'validateCharacterFeedbackRequest',
      'validateRaterFeedbackRequest',
      'validateEditorReviewRequest'
    ]);

    const requestOptimizerSpyObj = jasmine.createSpyObj('RequestOptimizerService', [
      'optimizeCharacterFeedbackRequest',
      'optimizeRaterFeedbackRequest',
      'optimizeEditorReviewRequest'
    ]);

    // Set up default validation responses
    requestValidatorSpyObj.validateCharacterFeedbackRequest.and.returnValue({ isValid: true, errors: [] });
    requestValidatorSpyObj.validateRaterFeedbackRequest.and.returnValue({ isValid: true, errors: [] });
    requestValidatorSpyObj.validateEditorReviewRequest.and.returnValue({ isValid: true, errors: [] });

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
        { provide: RequestValidatorService, useValue: requestValidatorSpyObj },
        { provide: RequestOptimizerService, useValue: requestOptimizerSpyObj }
      ]
    });

    service = TestBed.inject(GenerationService);
    apiServiceSpy = TestBed.inject(ApiService) as jasmine.SpyObj<ApiService>;
    contextBuilderSpy = TestBed.inject(ContextBuilderService) as jasmine.SpyObj<ContextBuilderService>;
    requestValidatorSpy = TestBed.inject(RequestValidatorService) as jasmine.SpyObj<RequestValidatorService>;
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
          internalMonologue: ['What awaits?']
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
            plotContext: jasmine.objectContaining({
              plotPoint: 'Enter dungeon'
            }),
            character: jasmine.objectContaining({
              name: 'Test Character'
            })
          })
        );
        done();
      });
    });
  });

  describe('requestRaterFeedback', () => {
    it('should build structured request with complete context and call API', (done) => {
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

      // Configure context builder spy methods to return successful responses
      contextBuilderSpy.buildSystemPromptsContext.and.returnValue({
        success: true,
        data: {
          mainPrefix: 'System prefix',
          mainSuffix: 'System suffix',
          assistantPrompt: 'Assistant prompt'
        },
        errors: undefined,
        warnings: undefined,
        fromCache: false
      });

      contextBuilderSpy.buildWorldbuildingContext.and.returnValue({
        success: true,
        data: {
          content: 'Test worldbuilding',
          isValid: true,
          wordCount: 2,
          lastUpdated: new Date()
        },
        errors: undefined,
        warnings: undefined,
        fromCache: false
      });

      contextBuilderSpy.buildStorySummaryContext.and.returnValue({
        success: true,
        data: {
          summary: 'Test story summary',
          isValid: true,
          wordCount: 3,
          lastUpdated: new Date()
        },
        errors: undefined,
        warnings: undefined,
        fromCache: false
      });

      contextBuilderSpy.buildChaptersContext.and.returnValue({
        success: true,
        data: {
          chapters: [],
          totalChapters: 0,
          totalWordCount: 0,
          lastUpdated: new Date()
        },
        errors: undefined,
        warnings: undefined,
        fromCache: false
      });

      contextBuilderSpy.buildCharacterContext.and.returnValue({
        success: true,
        data: {
          characters: [],
          totalCharacters: 0,
          visibleCharacters: 0,
          lastUpdated: new Date()
        },
        errors: undefined,
        warnings: undefined,
        fromCache: false
      });

      // Mock streaming response
      apiServiceSpy.streamRaterFeedback.and.returnValue(of(
        { type: 'result', data: mockResponse }
      ));

      service.requestRaterFeedback(mockStory, mockRater, 'Enter dungeon').subscribe(response => {
        expect(response).toEqual(mockResponse);
        expect(apiServiceSpy.streamRaterFeedback).toHaveBeenCalledWith(
          jasmine.objectContaining({
            plotPoint: 'Enter dungeon',
            raterPrompt: 'Evaluate pacing',
            structured_context: jasmine.objectContaining({
              plotContext: jasmine.objectContaining({
                plotPoint: 'Enter dungeon'
              })
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
      const plotPoint = 'The hero enters the dungeon';

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

      service.generateChapter(mockStory, plotPoint).subscribe(response => {
        expect(response).toEqual(mockResponse);
        expect(apiServiceSpy.generateChapter).toHaveBeenCalledWith(
          jasmine.objectContaining({
            plotPoint: 'The hero enters the dungeon',
            structured_context: jasmine.objectContaining({
              plot_elements: jasmine.any(Array),
              character_contexts: jasmine.any(Array),
              user_requests: jasmine.any(Array),
              system_instructions: jasmine.any(Array),
              metadata: jasmine.any(Object)
            })
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
      const plotPoint = "Test plot point";

      service.generateChapter(mockStory, plotPoint).subscribe(() => {
        const callArgs = apiServiceSpy.generateChapter.calls.mostRecent().args[0];
        expect(callArgs.structured_context.character_contexts?.length).toBe(1);
        expect(callArgs.structured_context.character_contexts?.[0].character_name).toBe('Visible Character');
        done();
      });
    });
  });

  describe('modifyChapter', () => {
    it('should build request with chapter text and user request', (done) => {
      const mockStory = createMockStory();
      const mockResponse = {
        modifiedChapter: 'Modified chapter text',
        modifiedChapterText: 'Modified chapter text',
        wordCount: 30,
        changesSummary: 'Made it exciting'
      };

      apiServiceSpy.modifyChapter.and.returnValue(of(mockResponse));

      service.modifyChapter(mockStory, 'Original text', 'Make it exciting').subscribe(response => {
        expect(response).toEqual(mockResponse);
        expect(apiServiceSpy.modifyChapter).toHaveBeenCalledWith(
          jasmine.objectContaining({
            currentChapter: 'Original text',
            userRequest: 'Make it exciting'
          }),
          undefined
        );
        done();
      });
    });
  });

  describe('requestEditorReview', () => {
    it('should build structured request with chapter and call API', (done) => {
      const mockStory = createMockStory();
      const mockResponse: StructuredEditorReviewResponse = {
        overallAssessment: 'Good chapter',
        suggestions: []
      };

      // Configure context builder spy methods to return successful responses
      contextBuilderSpy.buildSystemPromptsContext.and.returnValue({
        success: true,
        data: {
          mainPrefix: 'System prefix',
          mainSuffix: 'System suffix',
          assistantPrompt: 'Assistant prompt'
        },
        errors: undefined,
        warnings: undefined,
        fromCache: false
      });

      contextBuilderSpy.buildWorldbuildingContext.and.returnValue({
        success: true,
        data: {
          content: 'Test worldbuilding',
          isValid: true,
          wordCount: 2,
          lastUpdated: new Date()
        },
        errors: undefined,
        warnings: undefined,
        fromCache: false
      });

      contextBuilderSpy.buildStorySummaryContext.and.returnValue({
        success: true,
        data: {
          summary: 'Test story summary',
          isValid: true,
          wordCount: 3,
          lastUpdated: new Date()
        },
        errors: undefined,
        warnings: undefined,
        fromCache: false
      });

      contextBuilderSpy.buildChaptersContext.and.returnValue({
        success: true,
        data: {
          chapters: [],
          totalChapters: 0,
          totalWordCount: 0,
          lastUpdated: new Date()
        },
        errors: undefined,
        warnings: undefined,
        fromCache: false
      });

      contextBuilderSpy.buildCharacterContext.and.returnValue({
        success: true,
        data: {
          characters: [],
          totalCharacters: 0,
          visibleCharacters: 0,
          lastUpdated: new Date()
        },
        errors: undefined,
        warnings: undefined,
        fromCache: false
      });

      apiServiceSpy.requestEditorReview.and.returnValue(of(mockResponse));

      service.requestEditorReview(mockStory, 'Chapter text').subscribe(response => {
        expect(response).toEqual(mockResponse);
        expect(apiServiceSpy.requestEditorReview).toHaveBeenCalledWith(
          jasmine.objectContaining({
            chapterToReview: 'Chapter text'
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

      service.fleshOut(mockStory, 'Short text', 'plot_outline').subscribe(response => {
        expect(response).toEqual(mockResponse);
        expect(apiServiceSpy.fleshOut).toHaveBeenCalledWith(
          jasmine.objectContaining({
            textToFleshOut: 'Short text',
            context: 'plot_outline'
          })
        );
        done();
      });
    });
  });

  describe('generateCharacterDetails', () => {
    it('should build request with basic bio and existing characters', (done) => {
      const mockStory = createMockStory();
      const existingCharacter: Character = {
        id: 'char-1',
        name: 'Existing Character',
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

      service.generateCharacterDetails(mockStory, 'A smart mage', [existingCharacter]).subscribe(response => {
        expect(response).toEqual(mockResponse);
        expect(apiServiceSpy.generateCharacterDetails).toHaveBeenCalledWith(
          jasmine.objectContaining({
            basicBio: 'A smart mage',
            existingCharacters: jasmine.arrayContaining([
              jasmine.objectContaining({
                name: 'Existing Character'
              })
            ])
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
