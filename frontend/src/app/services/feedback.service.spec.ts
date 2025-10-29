import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';

import { FeedbackService } from './feedback.service';
import { GenerationService } from './generation.service';
import { ConversationService } from './conversation.service';
import { LocalStorageService } from './local-storage.service';
import { 
  Story, 
  Character, 
  Rater, 
  EnhancedFeedbackItem,
  CharacterFeedbackResponse,
  RaterFeedbackResponse
} from '../models/story.model';

describe('FeedbackService', () => {
  let service: FeedbackService;
  let mockGenerationService: jasmine.SpyObj<GenerationService>;
  let mockConversationService: jasmine.SpyObj<ConversationService>;
  let mockLocalStorageService: jasmine.SpyObj<LocalStorageService>;

  const mockCharacter: Character = {
    id: 'char1',
    name: 'John Doe',
    basicBio: 'A brave hero',
    sex: 'male',
    gender: 'male',
    sexualPreference: 'heterosexual',
    age: 30,
    physicalAppearance: 'Tall and strong',
    usualClothing: 'Armor',
    personality: 'Brave and kind',
    motivations: 'Save the world',
    fears: 'Losing loved ones',
    relationships: 'Has a sister',
    isHidden: false,
    metadata: {
      creationSource: 'user',
      lastModified: new Date()
    }
  };

  const mockRater: Rater = {
    id: 'rater1',
    name: 'Story Critic',
    systemPrompt: 'You are a story critic',
    enabled: true,
    metadata: {
      created: new Date(),
      lastModified: new Date()
    }
  };

  const mockStory: Story = {
    id: 'test-story-id',
    general: {
      title: 'Test Story',
      systemPrompts: {
        mainPrefix: '',
        mainSuffix: '',
        assistantPrompt: '',
        editorPrompt: ''
      },
      worldbuilding: 'A fantasy world'
    },
    characters: new Map([['char1', mockCharacter]]),
    raters: new Map([['rater1', mockRater]]),
    story: {
      summary: 'A test story',
      chapters: []
    },
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
    chapterCompose: {
      currentPhase: 'plot_outline',
      phases: {
        plotOutline: {
          conversation: {
            id: 'conv-1',
            messages: [],
            currentBranchId: 'main',
            branches: new Map(),
            metadata: {
              created: new Date(),
              lastModified: new Date(),
              phase: 'plot_outline'
            }
          },
          status: 'active',
          outline: {
            items: new Map(),
            structure: []
          },
          draftSummary: '',
          progress: {
            totalItems: 0,
            completedItems: 0,
            lastActivity: new Date()
          }
        },
        chapterDetailer: {
          conversation: {
            id: 'conv-2',
            messages: [],
            currentBranchId: 'main',
            branches: new Map(),
            metadata: {
              created: new Date(),
              lastModified: new Date(),
              phase: 'chapter_detail'
            }
          },
          chapterDraft: {
            content: '',
            title: '',
            plotPoint: '',
            wordCount: 0,
            status: 'drafting'
          },
          feedbackIntegration: {
            pendingFeedback: [],
            incorporatedFeedback: [],
            feedbackRequests: new Map()
          },
          status: 'active',
          progress: {
            feedbackIncorporated: 0,
            totalFeedbackItems: 0,
            lastActivity: new Date()
          }
        },
        finalEdit: {
          conversation: {
            id: 'conv-3',
            messages: [],
            currentBranchId: 'main',
            branches: new Map(),
            metadata: {
              created: new Date(),
              lastModified: new Date(),
              phase: 'final_edit'
            }
          },
          finalChapter: {
            content: '',
            title: '',
            wordCount: 0,
            version: 1
          },
          reviewSelection: {
            availableReviews: [],
            selectedReviews: [],
            appliedReviews: []
          },
          status: 'active',
          progress: {
            reviewsApplied: 0,
            totalReviews: 0,
            lastActivity: new Date()
          }
        }
      },
      sharedContext: {
        chapterNumber: 1
      },
      navigation: {
        phaseHistory: ['plot_outline'],
        canGoBack: false,
        canGoForward: false,
        branchNavigation: {
          currentBranchId: 'main',
          availableBranches: ['main'],
          branchHistory: [],
          canNavigateBack: false,
          canNavigateForward: false
        }
      },
      overallProgress: {
        currentStep: 1,
        totalSteps: 3,
        phaseCompletionStatus: {
          'plot_outline': false,
          'chapter_detail': false,
          'final_edit': false
        }
      },
      metadata: {
        created: new Date(),
        lastModified: new Date(),
        version: '1'
      }
    },
    chapterCreation: {
      plotPoint: 'Test plot point',
      incorporatedFeedback: [
        {
          source: 'John Doe',
          type: 'action',
          content: 'Existing feedback',
          incorporated: true
        }
      ],
      feedbackRequests: new Map()
    },
    metadata: {
      version: '1.0',
      created: new Date(),
      lastModified: new Date()
    }
  };

  const mockCharacterFeedbackResponse: CharacterFeedbackResponse = {
    characterName: 'John Doe',
    feedback: {
      actions: ['Be more decisive'],
      dialog: ['Say something inspiring'],
      physicalSensations: ['Feel the wind'],
      emotions: ['Show determination'],
      internalMonologue: ['Think about the mission']
    }
  };

  const mockRaterFeedbackResponse: RaterFeedbackResponse = {
    raterName: 'Story Critic',
    feedback: {
      opinion: 'The scene needs more tension',
      suggestions: [
        {
          issue: 'Pacing',
          suggestion: 'Add more action',
          priority: 'high'
        }
      ]
    }
  };

  beforeEach(() => {
    const generationServiceSpy = jasmine.createSpyObj('GenerationService', [
      'requestCharacterFeedback',
      'requestRaterFeedback',
      'requestCharacterFeedbackWithPhase',
      'requestRaterFeedbackWithPhase'
    ]);

    const conversationServiceSpy = jasmine.createSpyObj('ConversationService', [
      'sendMessage'
    ]);

    const localStorageServiceSpy = jasmine.createSpyObj('LocalStorageService', [
      'loadStory',
      'saveStory'
    ]);

    TestBed.configureTestingModule({
      providers: [
        FeedbackService,
        { provide: GenerationService, useValue: generationServiceSpy },
        { provide: ConversationService, useValue: conversationServiceSpy },
        { provide: LocalStorageService, useValue: localStorageServiceSpy }
      ]
    });

    service = TestBed.inject(FeedbackService);
    mockGenerationService = TestBed.inject(GenerationService) as jasmine.SpyObj<GenerationService>;
    mockConversationService = TestBed.inject(ConversationService) as jasmine.SpyObj<ConversationService>;
    mockLocalStorageService = TestBed.inject(LocalStorageService) as jasmine.SpyObj<LocalStorageService>;

    // Set up default mocks
    mockLocalStorageService.loadStory.and.returnValue(mockStory);
    mockGenerationService.requestCharacterFeedback.and.returnValue(of(mockCharacterFeedbackResponse));
    mockGenerationService.requestRaterFeedback.and.returnValue(of(mockRaterFeedbackResponse));
    mockConversationService.sendMessage.and.returnValue({
      id: 'msg1',
      type: 'user',
      content: 'test',
      timestamp: new Date()
    });
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('getAvailableFeedback', () => {
    it('should return cached feedback if available', () => {
      const mockFeedback: EnhancedFeedbackItem[] = [
        {
          id: 'feedback1',
          source: 'Test',
          type: 'action',
          content: 'Test feedback',
          incorporated: false,
          phase: 'chapter_detail',
          priority: 'medium',
          status: 'pending',
          metadata: { created: new Date(), lastModified: new Date() }
        }
      ];

      // Set cache
      service['feedbackCache'].set('test-story-id_1_chapter_detail', mockFeedback);

      const result = service.getAvailableFeedback('test-story-id', 1, 'chapter_detail');

      expect(result).toEqual(mockFeedback);
      expect(mockLocalStorageService.loadStory).not.toHaveBeenCalled();
    });

    it('should load feedback from story if not cached', () => {
      const result = service.getAvailableFeedback('test-story-id', 1, 'chapter_detail');

      expect(mockLocalStorageService.loadStory).toHaveBeenCalledWith('test-story-id');
      expect(result.length).toBeGreaterThan(0);
      expect(result[0].source).toBe('John Doe');
    });

    it('should return empty array if story not found', () => {
      mockLocalStorageService.loadStory.and.returnValue(null);

      const result = service.getAvailableFeedback('nonexistent', 1, 'chapter_detail');

      expect(result).toEqual([]);
    });
  });

  describe('requestCharacterFeedback', () => {
    it('should successfully request character feedback', (done) => {
      service.requestCharacterFeedback(mockStory, mockCharacter, 1).subscribe(result => {
        expect(result).toBeTrue();
        expect(mockGenerationService.requestCharacterFeedback).toHaveBeenCalledWith(
          mockStory,
          mockCharacter,
          'Test plot point'
        );
        done();
      });
    });

    it('should handle request errors', (done) => {
      mockGenerationService.requestCharacterFeedback.and.returnValue(
        throwError(() => new Error('Request failed'))
      );

      service.requestCharacterFeedback(mockStory, mockCharacter, 1).subscribe(result => {
        expect(result).toBeFalse();
        done();
      });
    });

    it('should update request status during request', (done) => {
      const statusUpdates: any[] = [];
      
      service.requestStatus$.subscribe(status => {
        statusUpdates.push(status);
      });

      service.requestCharacterFeedback(mockStory, mockCharacter, 1).subscribe(() => {
        expect(statusUpdates.length).toBeGreaterThan(1);
        expect(statusUpdates[1].pendingRequests).toContain('character_char1_1');
        done();
      });
    });
  });

  describe('requestRaterFeedback', () => {
    it('should successfully request rater feedback', (done) => {
      service.requestRaterFeedback(mockStory, mockRater, 1).subscribe(result => {
        expect(result).toBeTrue();
        expect(mockGenerationService.requestRaterFeedback).toHaveBeenCalledWith(
          mockStory,
          mockRater,
          'Test plot point'
        );
        done();
      });
    });

    it('should handle request errors', (done) => {
      mockGenerationService.requestRaterFeedback.and.returnValue(
        throwError(() => new Error('Request failed'))
      );

      service.requestRaterFeedback(mockStory, mockRater, 1).subscribe(result => {
        expect(result).toBeFalse();
        done();
      });
    });
  });

  describe('addFeedbackToChat', () => {
    it('should add feedback to chat successfully', (done) => {
      const mockFeedback: EnhancedFeedbackItem[] = [
        {
          id: 'feedback1',
          source: 'John Doe',
          type: 'action',
          content: 'Test feedback',
          incorporated: false,
          phase: 'chapter_detail',
          priority: 'medium',
          status: 'pending',
          metadata: { created: new Date(), lastModified: new Date() }
        }
      ];

      service.addFeedbackToChat(
        'test-story-id',
        1,
        'chapter_detail',
        mockFeedback,
        'User comment'
      ).subscribe(result => {
        expect(result).toBeTrue();
        expect(mockConversationService.sendMessage).toHaveBeenCalled();
        done();
      });
    });

    it('should format feedback message correctly', (done) => {
      const mockFeedback: EnhancedFeedbackItem[] = [
        {
          id: 'feedback1',
          source: 'John Doe',
          type: 'action',
          content: 'Test feedback',
          incorporated: false,
          phase: 'chapter_detail',
          priority: 'medium',
          status: 'pending',
          metadata: { created: new Date(), lastModified: new Date() }
        }
      ];

      service.addFeedbackToChat(
        'test-story-id',
        1,
        'chapter_detail',
        mockFeedback,
        'User comment'
      ).subscribe(() => {
        const callArgs = mockConversationService.sendMessage.calls.mostRecent().args;
        const messageContent = callArgs[0];
        
        expect(messageContent).toContain('User comment');
        expect(messageContent).toContain('John Doe');
        expect(messageContent).toContain('Test feedback');
        done();
      });
    });

    it('should handle chat integration errors', (done) => {
      mockConversationService.sendMessage.and.throwError('Chat error');

      const mockFeedback: EnhancedFeedbackItem[] = [
        {
          id: 'feedback1',
          source: 'Test',
          type: 'action',
          content: 'Test',
          incorporated: false,
          phase: 'chapter_detail',
          priority: 'medium',
          status: 'pending',
          metadata: { created: new Date(), lastModified: new Date() }
        }
      ];

      service.addFeedbackToChat('test-story-id', 1, 'chapter_detail', mockFeedback).subscribe(result => {
        expect(result).toBeFalse();
        done();
      });
    });
  });

  describe('markFeedbackAsIncorporated', () => {
    it('should mark feedback as incorporated in cache', () => {
      const mockFeedback: EnhancedFeedbackItem[] = [
        {
          id: 'feedback1',
          source: 'Test',
          type: 'action',
          content: 'Test',
          incorporated: false,
          phase: 'chapter_detail',
          priority: 'medium',
          status: 'pending',
          metadata: { created: new Date(), lastModified: new Date() }
        }
      ];

      service['feedbackCache'].set('test-story-id_1_chapter_detail', mockFeedback);

      service.markFeedbackAsIncorporated('test-story-id', ['feedback1']);

      const updatedFeedback = service['feedbackCache'].get('test-story-id_1_chapter_detail');
      expect(updatedFeedback![0].status).toBe('incorporated');
    });

    it('should update story data when marking as incorporated', () => {
      const mockFeedback: EnhancedFeedbackItem[] = [
        {
          id: 'feedback1',
          source: 'John Doe',
          type: 'action',
          content: 'Test feedback',
          incorporated: false,
          phase: 'chapter_detail',
          priority: 'medium',
          status: 'pending',
          metadata: { created: new Date(), lastModified: new Date() }
        }
      ];

      service['feedbackCache'].set('test-story-id_1_chapter_detail', mockFeedback);

      service.markFeedbackAsIncorporated('test-story-id', ['feedback1']);

      expect(mockLocalStorageService.saveStory).toHaveBeenCalled();
    });
  });

  describe('clearFeedbackCache', () => {
    beforeEach(() => {
      service['feedbackCache'].set('story1_1_chapter_detail', []);
      service['feedbackCache'].set('story1_2_chapter_detail', []);
      service['feedbackCache'].set('story2_1_chapter_detail', []);
    });

    it('should clear specific cache entry', () => {
      service.clearFeedbackCache('story1', 1, 'chapter_detail');

      expect(service['feedbackCache'].has('story1_1_chapter_detail')).toBeFalse();
      expect(service['feedbackCache'].has('story1_2_chapter_detail')).toBeTrue();
      expect(service['feedbackCache'].has('story2_1_chapter_detail')).toBeTrue();
    });

    it('should clear all entries for a story', () => {
      service.clearFeedbackCache('story1');

      expect(service['feedbackCache'].has('story1_1_chapter_detail')).toBeFalse();
      expect(service['feedbackCache'].has('story1_2_chapter_detail')).toBeFalse();
      expect(service['feedbackCache'].has('story2_1_chapter_detail')).toBeTrue();
    });

    it('should clear entire cache', () => {
      service.clearFeedbackCache();

      expect(service['feedbackCache'].size).toBe(0);
    });
  });

  describe('feedback conversion', () => {
    it('should convert character feedback response correctly', () => {
      const result = service['convertCharacterFeedbackToEnhanced'](
        mockCharacterFeedbackResponse,
        'John Doe',
        1
      );

      expect(result.length).toBe(5); // actions, dialog, physicalSensations, emotions, internalMonologue
      expect(result[0].source).toBe('John Doe');
      expect(result[0].type).toBe('action');
      expect(result[0].content).toBe('Be more decisive');
    });

    it('should convert rater feedback response correctly', () => {
      const result = service['convertRaterFeedbackToEnhanced'](
        mockRaterFeedbackResponse,
        'Story Critic',
        1
      );

      expect(result.length).toBe(2); // opinion + 1 suggestion
      expect(result[0].source).toBe('Story Critic');
      expect(result[0].type).toBe('suggestion');
      expect(result[0].content).toBe('The scene needs more tension');
      expect(result[1].priority).toBe('high');
    });
  });

  describe('observables', () => {
    it('should emit feedback updated events', (done) => {
      service.feedbackUpdated$.subscribe(() => {
        expect(true).toBeTrue(); // Just verify the observable emits
        done();
      });

      service['notifyFeedbackUpdated']();
    });

    it('should emit request status updates', (done) => {
      service.requestStatus$.subscribe(status => {
        expect(status).toBeDefined();
        expect(status.pendingRequests).toBeDefined();
        expect(status.completedRequests).toBeDefined();
        expect(status.failedRequests).toBeDefined();
        done();
      });
    });
  });

  describe('helper methods', () => {
    it('should get plot point from chapter creation', () => {
      const plotPoint = service['getPlotPointForChapter'](mockStory, 1);
      expect(plotPoint).toBe('Test plot point');
    });

    it('should get plot point from existing chapter', () => {
      const storyWithChapter = {
        ...mockStory,
        chapterCreation: { ...mockStory.chapterCreation, plotPoint: '' },
        story: {
          ...mockStory.story,
          chapters: [
            {
              id: 'ch1',
              number: 1,
              title: 'Chapter 1',
              content: 'Content',
              plotPoint: 'Chapter plot point',
              incorporatedFeedback: [],
              metadata: {
                created: new Date(),
                lastModified: new Date(),
                wordCount: 100
              }
            }
          ]
        }
      };

      const plotPoint = service['getPlotPointForChapter'](storyWithChapter, 1);
      expect(plotPoint).toBe('Chapter plot point');
    });

    it('should return default plot point if none found', () => {
      const storyWithoutPlotPoint = {
        ...mockStory,
        chapterCreation: { ...mockStory.chapterCreation, plotPoint: '' }
      };

      const plotPoint = service['getPlotPointForChapter'](storyWithoutPlotPoint, 1);
      expect(plotPoint).toBe('Chapter 1 development');
    });

    it('should format feedback for chat correctly', () => {
      const mockFeedback: EnhancedFeedbackItem[] = [
        {
          id: 'feedback1',
          source: 'John Doe',
          type: 'action',
          content: 'Be more decisive',
          incorporated: false,
          phase: 'chapter_detail',
          priority: 'medium',
          status: 'pending',
          metadata: { created: new Date(), lastModified: new Date() }
        },
        {
          id: 'feedback2',
          source: 'Story Critic',
          type: 'suggestion',
          content: 'Add tension',
          incorporated: false,
          phase: 'chapter_detail',
          priority: 'high',
          status: 'pending',
          metadata: { created: new Date(), lastModified: new Date() }
        }
      ];

      const formatted = service['formatFeedbackForChat'](mockFeedback, 'User comment');

      expect(formatted).toContain('User comment');
      expect(formatted).toContain('Selected Feedback (2 items)');
      expect(formatted).toContain('John Doe:');
      expect(formatted).toContain('Story Critic:');
      expect(formatted).toContain('action: Be more decisive');
      expect(formatted).toContain('suggestion: Add tension');
    });
  });
});
