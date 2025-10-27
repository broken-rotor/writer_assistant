import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';

import { ReviewService, ReviewRequestStatus, QualityScore, ComprehensiveReviewRequest } from './review.service';
import { GenerationService } from './generation.service';
import { FeedbackService } from './feedback.service';
import { ConversationService } from './conversation.service';
import { LocalStorageService } from './local-storage.service';
import { Story, ReviewItem, Character, Rater, EditorSuggestion } from '../models/story.model';

describe('ReviewService', () => {
  let service: ReviewService;
  let generationServiceSpy: jasmine.SpyObj<GenerationService>;
  let feedbackServiceSpy: jasmine.SpyObj<FeedbackService>;
  let conversationServiceSpy: jasmine.SpyObj<ConversationService>;
  let localStorageServiceSpy: jasmine.SpyObj<LocalStorageService>;

  const mockStory: Story = {
    id: 'test-story-1',
    general: {
      title: 'Test Story',
      systemPrompts: {
        mainPrefix: 'Test prefix',
        mainSuffix: 'Test suffix',
        assistantPrompt: 'Test assistant',
        editorPrompt: 'Test editor'
      },
      worldbuilding: 'Test world'
    },
    characters: new Map([
      ['char1', {
        id: 'char1',
        name: 'Test Character',
        basicBio: 'Test bio',
        sex: 'female',
        gender: 'female',
        sexualPreference: 'heterosexual',
        age: 25,
        physicalAppearance: 'Test appearance',
        usualClothing: 'Test clothing',
        personality: 'Test personality',
        motivations: 'Test motivations',
        fears: 'Test fears',
        relationships: 'Test relationships',
        isHidden: false,
        metadata: {
          creationSource: 'user',
          lastModified: new Date()
        }
      } as Character]
    ]),
    raters: new Map([
      ['rater1', {
        id: 'rater1',
        name: 'Test Rater',
        systemPrompt: 'Test rater prompt',
        enabled: true,
        metadata: {
          created: new Date(),
          lastModified: new Date()
        }
      } as Rater]
    ]),
    story: {
      summary: 'Test summary',
      chapters: []
    },
    chapterCreation: {
      plotPoint: 'Test plot point',
      generatedChapter: null,
      incorporatedFeedback: [],
      feedbackRequests: new Map(),
      editorReview: undefined
    },
    chapterCompose: {
      currentPhase: 'final-edit',
      phases: {
        plotOutline: {} as any,
        chapterDetailer: {} as any,
        finalEdit: {
          conversation: {} as any,
          finalChapter: {
            content: 'Test chapter content',
            title: 'Test Chapter',
            wordCount: 100,
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
        chapterNumber: 1,
        targetWordCount: 2000
      },
      navigation: {} as any,
      overallProgress: {} as any,
      metadata: {
        created: new Date(),
        lastModified: new Date(),
        version: '1.0.0',
        migrationSource: 'manual'
      }
    }
  } as Story;

  const mockReviewItem: ReviewItem = {
    id: 'review-1',
    type: 'grammar',
    title: 'Grammar Issue',
    description: 'Test grammar issue',
    suggestion: 'Fix grammar',
    priority: 'high',
    status: 'pending',
    metadata: {
      created: new Date(),
      reviewer: 'editor'
    }
  };

  beforeEach(() => {
    const generationSpy = jasmine.createSpyObj('GenerationService', ['requestEditorReview']);
    const feedbackSpy = jasmine.createSpyObj('FeedbackService', ['requestCharacterFeedback', 'requestRaterFeedback']);
    const conversationSpy = jasmine.createSpyObj('ConversationService', ['sendMessage']);
    const localStorageSpy = jasmine.createSpyObj('LocalStorageService', ['loadStory', 'saveStory']);

    TestBed.configureTestingModule({
      providers: [
        ReviewService,
        { provide: GenerationService, useValue: generationSpy },
        { provide: FeedbackService, useValue: feedbackSpy },
        { provide: ConversationService, useValue: conversationSpy },
        { provide: LocalStorageService, useValue: localStorageSpy }
      ]
    });

    service = TestBed.inject(ReviewService);
    generationServiceSpy = TestBed.inject(GenerationService) as jasmine.SpyObj<GenerationService>;
    feedbackServiceSpy = TestBed.inject(FeedbackService) as jasmine.SpyObj<FeedbackService>;
    conversationServiceSpy = TestBed.inject(ConversationService) as jasmine.SpyObj<ConversationService>;
    localStorageServiceSpy = TestBed.inject(LocalStorageService) as jasmine.SpyObj<LocalStorageService>;
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('getAvailableReviews', () => {
    it('should return reviews from cache if available', () => {
      // Setup cache
      const reviews = [mockReviewItem];
      service['reviewCache'].set('test-story-1_1_final-edit', reviews);

      const result = service.getAvailableReviews('test-story-1', 1);

      expect(result).toEqual(reviews);
      expect(localStorageServiceSpy.loadStory).not.toHaveBeenCalled();
    });

    it('should load reviews from story data if not cached', () => {
      localStorageServiceSpy.loadStory.and.returnValue(mockStory);

      const result = service.getAvailableReviews('test-story-1', 1);

      expect(localStorageServiceSpy.loadStory).toHaveBeenCalledWith('test-story-1');
      expect(result).toEqual([]);
    });

    it('should return empty array if story not found', () => {
      localStorageServiceSpy.loadStory.and.returnValue(null);

      const result = service.getAvailableReviews('test-story-1', 1);

      expect(result).toEqual([]);
    });
  });

  describe('requestComprehensiveReviews', () => {
    it('should request reviews from all agents by default', () => {
      const mockCharacterResponse = { feedback: { actions: ['Test action'] } };
      const mockRaterResponse = { feedback: { opinion: 'Test opinion', suggestions: ['Test suggestion'] } };
      const mockEditorResponse = { suggestions: [{ issue: 'Test issue', suggestion: 'Test fix', priority: 'high', selected: false }] };

      feedbackServiceSpy.requestCharacterFeedback.and.returnValue(of(mockCharacterResponse));
      feedbackServiceSpy.requestRaterFeedback.and.returnValue(of(mockRaterResponse));
      generationServiceSpy.requestEditorReview.and.returnValue(of(mockEditorResponse));
      localStorageServiceSpy.loadStory.and.returnValue(mockStory);
      localStorageServiceSpy.saveStory.and.stub();

      service.requestComprehensiveReviews(mockStory, 1, 'Test content').subscribe(result => {
        expect(result).toBe(true);
      });

      expect(feedbackServiceSpy.requestCharacterFeedback).toHaveBeenCalled();
      expect(feedbackServiceSpy.requestRaterFeedback).toHaveBeenCalled();
      expect(generationServiceSpy.requestEditorReview).toHaveBeenCalled();
    });

    it('should handle request failures gracefully', () => {
      feedbackServiceSpy.requestCharacterFeedback.and.returnValue(throwError('Test error'));
      feedbackServiceSpy.requestRaterFeedback.and.returnValue(of({}));
      generationServiceSpy.requestEditorReview.and.returnValue(of({}));

      service.requestComprehensiveReviews(mockStory, 1, 'Test content').subscribe(result => {
        expect(result).toBe(false);
      });
    });

    it('should respect options for selective requests', () => {
      const options: ComprehensiveReviewRequest = {
        includeCharacters: false,
        includeRaters: true,
        includeEditor: false
      };

      feedbackServiceSpy.requestRaterFeedback.and.returnValue(of({}));
      localStorageServiceSpy.loadStory.and.returnValue(mockStory);

      service.requestComprehensiveReviews(mockStory, 1, 'Test content', options).subscribe();

      expect(feedbackServiceSpy.requestCharacterFeedback).not.toHaveBeenCalled();
      expect(feedbackServiceSpy.requestRaterFeedback).toHaveBeenCalled();
      expect(generationServiceSpy.requestEditorReview).not.toHaveBeenCalled();
    });
  });

  describe('addReviewsToChat', () => {
    it('should format and send reviews to chat', () => {
      const reviews = [mockReviewItem];
      const userComment = 'Please apply these reviews';
      
      conversationServiceSpy.sendMessage.and.returnValue({} as any);
      localStorageServiceSpy.loadStory.and.returnValue(mockStory);
      localStorageServiceSpy.saveStory.and.stub();

      service.addReviewsToChat('test-story-1', 1, reviews, userComment).subscribe(result => {
        expect(result).toBe(true);
      });

      expect(conversationServiceSpy.sendMessage).toHaveBeenCalled();
      const messageCall = conversationServiceSpy.sendMessage.calls.mostRecent();
      expect(messageCall.args[0]).toContain(userComment);
      expect(messageCall.args[0]).toContain('Selected Reviews');
    });

    it('should handle chat integration errors', () => {
      const reviews = [mockReviewItem];
      conversationServiceSpy.sendMessage.and.throwError('Chat error');

      service.addReviewsToChat('test-story-1', 1, reviews).subscribe(result => {
        expect(result).toBe(false);
      });
    });
  });

  describe('calculateQualityScore', () => {
    it('should calculate quality score based on review priorities', () => {
      const reviews: ReviewItem[] = [
        { ...mockReviewItem, type: 'grammar', priority: 'high' },
        { ...mockReviewItem, id: 'review-2', type: 'style', priority: 'medium' },
        { ...mockReviewItem, id: 'review-3', type: 'flow', priority: 'low' }
      ];

      const score = service.calculateQualityScore(reviews);

      expect(score.overall).toBeGreaterThan(0);
      expect(score.overall).toBeLessThanOrEqual(100);
      expect(score.categories.grammar).toBe(60); // High priority = 60
      expect(score.categories.style).toBe(80); // Medium priority = 80
      expect(score.categories.flow).toBe(90); // Low priority = 90
      expect(score.readyToSave).toBe(false); // Has high priority issue
      expect(score.improvements.length).toBeGreaterThan(0);
    });

    it('should mark as ready to save when quality is high and no high priority issues', () => {
      const reviews: ReviewItem[] = [
        { ...mockReviewItem, type: 'style', priority: 'low' },
        { ...mockReviewItem, id: 'review-2', type: 'flow', priority: 'low' }
      ];

      const score = service.calculateQualityScore(reviews);

      expect(score.overall).toBeGreaterThan(80);
      expect(score.readyToSave).toBe(true);
    });

    it('should handle empty reviews array', () => {
      const score = service.calculateQualityScore([]);

      expect(score.overall).toBe(85); // Default score
      expect(score.readyToSave).toBe(true);
      expect(score.improvements).toEqual([]);
    });
  });

  describe('markReviewsAsApplied', () => {
    it('should update review status and story data', () => {
      const reviewIds = ['review-1', 'review-2'];
      const reviews = [
        { ...mockReviewItem, id: 'review-1' },
        { ...mockReviewItem, id: 'review-2' }
      ];
      
      service['reviewCache'].set('test-story-1_1_final-edit', reviews);
      localStorageServiceSpy.loadStory.and.returnValue(mockStory);
      localStorageServiceSpy.saveStory.and.stub();

      service.markReviewsAsApplied('test-story-1', reviewIds);

      expect(reviews[0].status).toBe('accepted');
      expect(reviews[1].status).toBe('accepted');
      expect(localStorageServiceSpy.saveStory).toHaveBeenCalled();
    });
  });

  describe('clearReviewCache', () => {
    it('should clear specific cache entry when story and chapter provided', () => {
      service['reviewCache'].set('test-story-1_1_final-edit', [mockReviewItem]);
      service['reviewCache'].set('test-story-1_2_final-edit', [mockReviewItem]);

      service.clearReviewCache('test-story-1', 1);

      expect(service['reviewCache'].has('test-story-1_1_final-edit')).toBe(false);
      expect(service['reviewCache'].has('test-story-1_2_final-edit')).toBe(true);
    });

    it('should clear all story cache entries when only story provided', () => {
      service['reviewCache'].set('test-story-1_1_final-edit', [mockReviewItem]);
      service['reviewCache'].set('test-story-1_2_final-edit', [mockReviewItem]);
      service['reviewCache'].set('test-story-2_1_final-edit', [mockReviewItem]);

      service.clearReviewCache('test-story-1');

      expect(service['reviewCache'].has('test-story-1_1_final-edit')).toBe(false);
      expect(service['reviewCache'].has('test-story-1_2_final-edit')).toBe(false);
      expect(service['reviewCache'].has('test-story-2_1_final-edit')).toBe(true);
    });

    it('should clear entire cache when no parameters provided', () => {
      service['reviewCache'].set('test-story-1_1_final-edit', [mockReviewItem]);
      service['reviewCache'].set('test-story-2_1_final-edit', [mockReviewItem]);

      service.clearReviewCache();

      expect(service['reviewCache'].size).toBe(0);
    });
  });

  describe('observables', () => {
    it('should emit reviews updated events', (done) => {
      service.reviewsUpdated$.subscribe(() => {
        done();
      });

      service['notifyReviewsUpdated']();
    });

    it('should emit request status updates', (done) => {
      const expectedStatus: ReviewRequestStatus = {
        pendingRequests: ['test-request'],
        completedRequests: [],
        failedRequests: [],
        totalRequests: 1,
        completedCount: 0
      };

      service.requestStatus$.subscribe(status => {
        if (status.totalRequests > 0) {
          expect(status).toEqual(expectedStatus);
          done();
        }
      });

      service['requestStatusSubject'].next(expectedStatus);
    });

    it('should emit quality score updates', (done) => {
      const expectedScore: QualityScore = {
        overall: 85,
        categories: {
          grammar: 90,
          style: 80,
          consistency: 85,
          flow: 85,
          character: 85,
          plot: 85
        },
        readyToSave: true,
        improvements: []
      };

      service.qualityScore$.subscribe(score => {
        if (score) {
          expect(score).toEqual(expectedScore);
          done();
        }
      });

      service['qualityScoreSubject'].next(expectedScore);
    });
  });
});
