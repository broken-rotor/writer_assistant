import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { GenerationService } from './generation.service';
import { ApiService } from './api.service';
import { ContextBuilderService } from './context-builder.service';
import { TokenCountingService } from './token-counting.service';
import { Story, Character, Rater } from '../models/story.model';
import { of } from 'rxjs';

describe('GenerationService', () => {
  let service: GenerationService;
  let apiServiceSpy: jasmine.SpyObj<ApiService>;

  beforeEach(() => {
    const spy = jasmine.createSpyObj('ApiService', [
      'requestCharacterFeedback',
      'requestRaterFeedback',
      'generateChapter',
      'modifyChapter',
      'requestEditorReview',
      'fleshOut',
      'generateCharacterDetails'
    ]);

    const contextBuilderSpy = jasmine.createSpyObj('ContextBuilderService', [
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

    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        GenerationService,
        { provide: ApiService, useValue: spy },
        { provide: ContextBuilderService, useValue: contextBuilderSpy },
        { provide: TokenCountingService, useValue: tokenCountingSpy }
      ]
    });

    service = TestBed.inject(GenerationService);
    apiServiceSpy = TestBed.inject(ApiService) as jasmine.SpyObj<ApiService>;
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('requestCharacterFeedback', () => {
    it('should build request with complete context and call API', (done) => {
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

      const mockResponse = {
        characterName: 'Test Character',
        feedback: {
          actions: ['Draw sword'],
          dialog: ['I must be brave'],
          physicalSensations: ['Heart pounding'],
          emotions: ['Fear'],
          internalMonologue: ['What awaits?']
        }
      };

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
    it('should build request with complete context and call API', (done) => {
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

      const mockResponse = {
        raterName: 'Pacing Rater',
        feedback: {
          opinion: 'Good pacing',
          suggestions: []
        }
      };

      apiServiceSpy.requestRaterFeedback.and.returnValue(of(mockResponse));

      service.requestRaterFeedback(mockStory, mockRater, 'Enter dungeon').subscribe(response => {
        expect(response).toEqual(mockResponse);
        expect(apiServiceSpy.requestRaterFeedback).toHaveBeenCalledWith(
          jasmine.objectContaining({
            plotContext: jasmine.objectContaining({
              plotPoint: 'Enter dungeon'
            }),
            raterPrompt: 'Evaluate pacing'
          })
        );
        done();
      });
    });
  });

  describe('generateChapter', () => {
    it('should build complete request and call API', (done) => {
      const mockStory = createMockStory();
      mockStory.chapterCreation.plotPoint = 'The hero enters the dungeon';

      const mockResponse = {
        chapterText: 'The hero stepped into the dark dungeon...'
      };

      apiServiceSpy.generateChapter.and.returnValue(of(mockResponse));

      service.generateChapter(mockStory).subscribe(response => {
        expect(response).toEqual(mockResponse);
        expect(apiServiceSpy.generateChapter).toHaveBeenCalledWith(
          jasmine.objectContaining({
            plotContext: jasmine.objectContaining({
              plotPoint: 'The hero enters the dungeon'
            }),
            feedbackContext: jasmine.objectContaining({
              incorporatedFeedback: []
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

      const mockResponse = {
        chapterText: 'Chapter text'
      };

      apiServiceSpy.generateChapter.and.returnValue(of(mockResponse));

      service.generateChapter(mockStory).subscribe(() => {
        const callArgs = apiServiceSpy.generateChapter.calls.mostRecent().args[0];
        expect(callArgs.characters.length).toBe(1);
        expect(callArgs.characters[0].name).toBe('Visible Character');
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
          })
        );
        done();
      });
    });
  });

  describe('requestEditorReview', () => {
    it('should build request with chapter and call API', (done) => {
      const mockStory = createMockStory();
      const mockResponse = {
        overallAssessment: 'Good chapter',
        suggestions: []
      };

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
        name: 'New Character',
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
          })
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
    chapterCreation: {
      plotPoint: '',
      incorporatedFeedback: [],
      feedbackRequests: new Map()
    },
    metadata: {
      version: '1.0',
      created: new Date(),
      lastModified: new Date()
    }
  };
}
