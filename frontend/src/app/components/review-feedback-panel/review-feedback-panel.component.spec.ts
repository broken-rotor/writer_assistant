import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { of, BehaviorSubject } from 'rxjs';

import { ReviewFeedbackPanelComponent, ReviewFeedbackPanelConfig } from './review-feedback-panel.component';
import { ReviewService, ReviewRequestStatus, QualityScore } from '../../services/review.service';
import { PhaseStateService } from '../../services/phase-state.service';
import { Story, ReviewItem, Character, Rater } from '../../models/story.model';

describe('ReviewFeedbackPanelComponent', () => {
  let component: ReviewFeedbackPanelComponent;
  let fixture: ComponentFixture<ReviewFeedbackPanelComponent>;
  let reviewServiceSpy: jasmine.SpyObj<ReviewService>;
  let phaseStateServiceSpy: jasmine.SpyObj<PhaseStateService>;

  const mockConfig: ReviewFeedbackPanelConfig = {
    storyId: 'test-story-1',
    chapterNumber: 1,
    chapterContent: 'Test chapter content',
    showRequestButtons: true,
    showChatIntegration: true,
    showQualityScore: true,
    maxHeight: '600px'
  };

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
    plotOutline: {
      content: 'Test plot outline',
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
      generatedChapter: undefined,
      incorporatedFeedback: [],
      feedbackRequests: new Map(),
      editorReview: undefined
    },
    metadata: {
      version: '1.0',
      created: new Date(),
      lastModified: new Date()
    }
  } as Story;

  const mockReviewItems: ReviewItem[] = [
    {
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
    },
    {
      id: 'review-2',
      type: 'character',
      title: 'Character Development',
      description: 'Character needs more depth',
      suggestion: 'Add more backstory',
      priority: 'medium',
      status: 'pending',
      metadata: {
        created: new Date(),
        reviewer: 'Test Character'
      }
    },
    {
      id: 'review-3',
      type: 'style',
      title: 'Style Improvement',
      description: 'Improve writing style',
      suggestion: 'Use more varied sentence structure',
      priority: 'low',
      status: 'pending',
      metadata: {
        created: new Date(),
        reviewer: 'Test Rater'
      }
    }
  ];

  const mockQualityScore: QualityScore = {
    overall: 75,
    categories: {
      grammar: 80,
      style: 70,
      consistency: 75,
      flow: 75,
      character: 70,
      plot: 80
    },
    readyToSave: false,
    improvements: ['Fix grammar issues', 'Improve character development']
  };

  beforeEach(async () => {
    const reviewSpy = jasmine.createSpyObj('ReviewService', [
      'getAvailableReviews',
      'requestComprehensiveReviews',
      'addReviewsToChat',
      'calculateQualityScore'
    ], {
      reviewsUpdated$: of(undefined),
      requestStatus$: new BehaviorSubject<ReviewRequestStatus>({
        pendingRequests: [],
        completedRequests: [],
        failedRequests: [],
        totalRequests: 0,
        completedCount: 0
      }),
      qualityScore$: new BehaviorSubject<QualityScore | null>(mockQualityScore)
    });

    const phaseSpy = jasmine.createSpyObj('PhaseStateService', ['getCurrentPhase']);

    await TestBed.configureTestingModule({
      imports: [ReviewFeedbackPanelComponent, FormsModule],
      providers: [
        { provide: ReviewService, useValue: reviewSpy },
        { provide: PhaseStateService, useValue: phaseSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ReviewFeedbackPanelComponent);
    component = fixture.componentInstance;
    reviewServiceSpy = TestBed.inject(ReviewService) as jasmine.SpyObj<ReviewService>;
    phaseStateServiceSpy = TestBed.inject(PhaseStateService) as jasmine.SpyObj<PhaseStateService>;

    // Setup component inputs
    component.config = mockConfig;
    component.story = mockStory;

    // Setup service spy returns
    reviewServiceSpy.getAvailableReviews.and.returnValue(mockReviewItems);
    reviewServiceSpy.requestComprehensiveReviews.and.returnValue(of(true));
    reviewServiceSpy.addReviewsToChat.and.returnValue(of(true));
    reviewServiceSpy.calculateQualityScore.and.returnValue(mockQualityScore);
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize reviews on ngOnInit', () => {
    fixture.detectChanges();

    expect(reviewServiceSpy.getAvailableReviews).toHaveBeenCalledWith('test-story-1', 1);
    expect(component.availableReviews).toEqual(mockReviewItems);
    expect(component.characterReviews.length).toBe(1);
    expect(component.raterReviews.length).toBe(1);
    expect(component.editorReviews.length).toBe(1);
  });

  it('should categorize reviews correctly', () => {
    fixture.detectChanges();

    expect(component.characterReviews[0].metadata.reviewer).toBe('Test Character');
    expect(component.raterReviews[0].metadata.reviewer).toBe('Test Rater');
    expect(component.editorReviews[0].metadata.reviewer).toBe('editor');
  });

  it('should handle review selection', () => {
    fixture.detectChanges();

    spyOn(component.selectionChanged, 'emit');

    component.toggleReviewSelection('review-1');

    expect(component.selectedReviewIds.has('review-1')).toBe(true);
    expect(component.selectionChanged.emit).toHaveBeenCalled();

    component.toggleReviewSelection('review-1');

    expect(component.selectedReviewIds.has('review-1')).toBe(false);
  });

  it('should select all reviews', () => {
    fixture.detectChanges();

    spyOn(component.selectionChanged, 'emit');

    component.selectAllReviews();

    expect(component.selectedReviewIds.size).toBe(3);
    expect(component.selectionChanged.emit).toHaveBeenCalled();
  });

  it('should clear all selections', () => {
    fixture.detectChanges();

    component.selectedReviewIds.add('review-1');
    component.selectedReviewIds.add('review-2');

    spyOn(component.selectionChanged, 'emit');

    component.clearAllSelection();

    expect(component.selectedReviewIds.size).toBe(0);
    expect(component.selectionChanged.emit).toHaveBeenCalled();
  });

  it('should select reviews by category', () => {
    fixture.detectChanges();

    spyOn(component.selectionChanged, 'emit');

    component.selectCategoryReviews('character');

    expect(component.selectedReviewIds.has('review-2')).toBe(true);
    expect(component.selectedReviewIds.size).toBe(1);
    expect(component.selectionChanged.emit).toHaveBeenCalled();
  });

  it('should select reviews by priority', () => {
    fixture.detectChanges();

    spyOn(component.selectionChanged, 'emit');

    component.selectByPriority('high');

    expect(component.selectedReviewIds.has('review-1')).toBe(true);
    expect(component.selectedReviewIds.size).toBe(1);
    expect(component.selectionChanged.emit).toHaveBeenCalled();
  });

  it('should request comprehensive reviews', () => {
    fixture.detectChanges();

    spyOn(component.reviewRequested, 'emit');

    component.requestComprehensiveReviews();

    expect(component.reviewRequested.emit).toHaveBeenCalledWith({
      requestType: 'comprehensive',
      options: component.comprehensiveOptions
    });
    expect(reviewServiceSpy.requestComprehensiveReviews).toHaveBeenCalledWith(
      mockStory,
      1,
      'Test chapter content',
      component.comprehensiveOptions
    );
  });

  it('should add selected reviews to chat', () => {
    fixture.detectChanges();

    component.selectedReviewIds.add('review-1');
    component.selectedReviewIds.add('review-2');
    component.userComment = 'Please apply these reviews';

    spyOn(component.addToChat, 'emit');

    component.addSelectedToChat();

    expect(component.addToChat.emit).toHaveBeenCalled();
    expect(reviewServiceSpy.addReviewsToChat).toHaveBeenCalled();
  });

  it('should not add to chat if no reviews selected', () => {
    fixture.detectChanges();

    spyOn(component.addToChat, 'emit');

    component.addSelectedToChat();

    expect(component.addToChat.emit).not.toHaveBeenCalled();
    expect(reviewServiceSpy.addReviewsToChat).not.toHaveBeenCalled();
  });

  it('should display quality score when enabled', () => {
    fixture.detectChanges();

    expect(component.qualityScore).toEqual(mockQualityScore);

    const compiled = fixture.nativeElement as HTMLElement;
    const qualitySection = compiled.querySelector('.quality-score-section');
    expect(qualitySection).toBeTruthy();
  });

  it('should toggle section visibility', () => {
    fixture.detectChanges();

    expect(component.showCharacterSection).toBe(true);

    component.toggleCharacterSection();

    expect(component.showCharacterSection).toBe(false);
  });

  it('should return correct utility values', () => {
    fixture.detectChanges();

    component.selectedReviewIds.add('review-1');
    component.selectedReviewIds.add('review-2');

    expect(component.selectedCount).toBe(2);
    expect(component.hasSelectedReviews).toBe(true);
    expect(component.availableCharacters.length).toBe(1);
    expect(component.availableRaters.length).toBe(1);
    expect(component.hasHighPriorityIssues).toBe(true);

    const reviewsByPriority = component.reviewsByPriority;
    expect(reviewsByPriority.high.length).toBe(1);
    expect(reviewsByPriority.medium.length).toBe(1);
    expect(reviewsByPriority.low.length).toBe(1);
  });

  it('should return correct icons for review status', () => {
    const pendingIcon = component.getReviewStatusIcon({ status: 'pending' } as ReviewItem);
    const acceptedIcon = component.getReviewStatusIcon({ status: 'accepted' } as ReviewItem);
    const rejectedIcon = component.getReviewStatusIcon({ status: 'rejected' } as ReviewItem);

    expect(pendingIcon).toBe('⏳');
    expect(acceptedIcon).toBe('✅');
    expect(rejectedIcon).toBe('❌');
  });

  it('should return correct icons for priority', () => {
    const highIcon = component.getPriorityIcon('high');
    const mediumIcon = component.getPriorityIcon('medium');
    const lowIcon = component.getPriorityIcon('low');

    expect(highIcon).toBe('🔴');
    expect(mediumIcon).toBe('🟡');
    expect(lowIcon).toBe('🟢');
  });

  it('should return correct icons for review type', () => {
    const grammarIcon = component.getReviewTypeIcon('grammar');
    const styleIcon = component.getReviewTypeIcon('style');
    const characterIcon = component.getReviewTypeIcon('character');

    expect(grammarIcon).toBe('📝');
    expect(styleIcon).toBe('🎨');
    expect(characterIcon).toBe('👤');
  });

  it('should format timestamp correctly', () => {
    const testDate = new Date('2023-12-25T10:30:00');
    const formatted = component.formatTimestamp(testDate);

    expect(formatted).toContain('Dec');
    expect(formatted).toContain('25');
  });

  it('should handle request progress calculation', () => {
    component.requestStatus = {
      pendingRequests: [],
      completedRequests: ['req1', 'req2'],
      failedRequests: [],
      totalRequests: 5,
      completedCount: 2
    };

    expect(component.requestProgress).toBe(40);
  });

  it('should handle zero total requests for progress', () => {
    component.requestStatus = {
      pendingRequests: [],
      completedRequests: [],
      failedRequests: [],
      totalRequests: 0,
      completedCount: 0
    };

    expect(component.requestProgress).toBe(0);
  });

  it('should track reviews by ID', () => {
    const trackResult = component.trackByReviewId(0, mockReviewItems[0]);
    expect(trackResult).toBe('review-1');
  });

  it('should handle comprehensive options toggle', () => {
    expect(component.comprehensiveOptions.includeCharacters).toBe(true);

    component.toggleComprehensiveOption('includeCharacters');

    expect(component.comprehensiveOptions.includeCharacters).toBe(false);
  });

  it('should subscribe to service observables', () => {
    const reviewsUpdatedSpy = spyOn(component as any, 'loadAvailableReviews');
    
    fixture.detectChanges();

    // Trigger the observable
    (reviewServiceSpy.reviewsUpdated$ as any).next();

    expect(reviewsUpdatedSpy).toHaveBeenCalled();
  });

  it('should unsubscribe on destroy', () => {
    fixture.detectChanges();

    const subscriptions = component['subscriptions'];
    spyOn(subscriptions[0], 'unsubscribe');

    component.ngOnDestroy();

    expect(subscriptions[0].unsubscribe).toHaveBeenCalled();
  });
});
