import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { of, throwError } from 'rxjs';

import { FinalEditPhaseComponent } from './final-edit-phase.component';
import { ChatInterfaceComponent } from '../chat-interface/chat-interface.component';
import { ReviewFeedbackPanelComponent } from '../review-feedback-panel/review-feedback-panel.component';
import { GenerationService } from '../../services/generation.service';
import { ConversationService } from '../../services/conversation.service';
import { PhaseStateService } from '../../services/phase-state.service';
import { ReviewService } from '../../services/review.service';
import { StoryService } from '../../services/story.service';
import { ToastService } from '../../services/toast.service';
import { NewlineToBrPipe } from '../../pipes/newline-to-br.pipe';
import { Story, ReviewItem, ChatMessage } from '../../models/story.model';

describe('FinalEditPhaseComponent', () => {
  let component: FinalEditPhaseComponent;
  let fixture: ComponentFixture<FinalEditPhaseComponent>;
  let mockPhaseStateService: jasmine.SpyObj<PhaseStateService>;
  let mockReviewService: jasmine.SpyObj<ReviewService>;
  let mockStoryService: jasmine.SpyObj<StoryService>;
  let mockToastService: jasmine.SpyObj<ToastService>;

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
      worldbuilding: 'A fantasy world'
    },
    characters: new Map(),
    raters: new Map(),
    chapterCompose: {
      currentPhase: 'final_edit',
      sharedContext: {
        chapterNumber: 1,
        targetWordCount: 2000,
        genre: 'Fantasy',
        tone: 'Adventure',
        pov: 'Third Person'
      },
      navigation: {
        phaseHistory: ['plot_outline', 'chapter_detail', 'final_edit'],
        canGoBack: true,
        canGoForward: false,
        branchNavigation: {
          currentBranchId: 'main',
          availableBranches: ['main'],
          branchHistory: [],
          canNavigateBack: false,
          canNavigateForward: false
        }
      },
      phases: {
        plotOutline: {
          conversation: {
            id: 'plot-conversation',
            messages: [],
            currentBranchId: 'main',
            branches: new Map(),
            metadata: { created: new Date(), lastModified: new Date(), phase: 'plot_outline' }
          },
          outline: {
            items: new Map(),
            structure: [],
            currentFocus: undefined
          },
          draftSummary: 'Test plot summary',
          status: 'completed',
          progress: { completedItems: 5, totalItems: 5, lastActivity: new Date() }
        },
        chapterDetailer: {
          conversation: {
            id: 'detailer-conversation',
            messages: [],
            currentBranchId: 'main',
            branches: new Map(),
            metadata: { created: new Date(), lastModified: new Date(), phase: 'chapter_detail' }
          },
          chapterDraft: {
            content: 'This is the chapter content from phase 2.',
            title: 'Chapter 1: The Beginning',
            plotPoint: 'The hero begins their journey',
            wordCount: 1500,
            status: 'completed'
          },
          feedbackIntegration: {
            pendingFeedback: [],
            incorporatedFeedback: [],
            feedbackRequests: new Map()
          },
          status: 'completed',
          progress: { feedbackIncorporated: 1, totalFeedbackItems: 0, lastActivity: new Date() }
        },
        finalEdit: {
          conversation: {
            id: 'final_edit-conversation',
            messages: [],
            currentBranchId: 'main',
            branches: new Map(),
            metadata: { created: new Date(), lastModified: new Date(), phase: 'final_edit' }
          },
          finalChapter: {
            content: 'This is the final chapter content.',
            title: 'Chapter 1: The Beginning',
            wordCount: 1500,
            version: 1
          },
          reviewSelection: {
            availableReviews: [],
            selectedReviews: [],
            appliedReviews: []
          },
          status: 'active',
          progress: { reviewsApplied: 0, totalReviews: 0, lastActivity: new Date() }
        }
      },
      overallProgress: {
        currentStep: 2,
        totalSteps: 3,
        phaseCompletionStatus: {
          plot_outline: true,
          chapter_detail: true,
          final_edit: false
        },
        estimatedTimeRemaining: 60
      },
      metadata: {
        created: new Date(),
        lastModified: new Date(),
        version: '1.0.0'
      }
    },
    story: {
      summary: 'Test story summary',
      chapters: []
    },
    plotOutline: {
      content: 'Test plot outline content',
      status: 'approved',
      chatHistory: [],
      raterFeedback: new Map(),
      metadata: {
        created: new Date(),
        lastModified: new Date(),
        version: 1
      }
    },
    chapterCreation: {
      plotPoint: 'Test plot point',
      incorporatedFeedback: [],
      feedbackRequests: new Map()
    },
    metadata: {
      version: '1.0.0',
      created: new Date(),
      lastModified: new Date()
    }
  };

  const mockReviewItems: ReviewItem[] = [
    {
      id: 'review-1',
      type: 'grammar',
      title: 'Grammar Issue',
      description: 'Fix grammar error',
      suggestion: 'Change "was" to "were"',
      priority: 'high',
      status: 'pending',
      metadata: { created: new Date(), reviewer: 'editor' }
    },
    {
      id: 'review-2',
      type: 'style',
      title: 'Style Improvement',
      description: 'Improve writing style',
      suggestion: 'Use more descriptive language',
      priority: 'medium',
      status: 'pending',
      metadata: { created: new Date(), reviewer: 'editor' }
    }
  ];

  beforeEach(async () => {
    const generationServiceSpy = jasmine.createSpyObj('GenerationService', ['generateContent']);
    const conversationServiceSpy = jasmine.createSpyObj('ConversationService', ['addMessage', 'getConversation']);
    const phaseStateServiceSpy = jasmine.createSpyObj('PhaseStateService', ['updatePhaseData', 'getPhaseData']);
    const reviewServiceSpy = jasmine.createSpyObj('ReviewService', ['getReviews'], {
    qualityScore$: of({
      overall: 85,
      categories: {
        plot: 90,
        character: 80,
        pacing: 85,
        dialogue: 88
      },
      feedback: 'Good chapter overall'
    })
  });
    const storyServiceSpy = jasmine.createSpyObj('StoryService', ['saveChapter', 'updateStory']);
    const toastServiceSpy = jasmine.createSpyObj('ToastService', ['show', 'showSuccess', 'showError', 'showInfo', 'showWarning']);

    await TestBed.configureTestingModule({
      imports: [
        FormsModule,
        HttpClientTestingModule,
        FinalEditPhaseComponent,
        ChatInterfaceComponent,
        ReviewFeedbackPanelComponent,
        NewlineToBrPipe
      ],
      providers: [
        { provide: GenerationService, useValue: generationServiceSpy },
        { provide: ConversationService, useValue: conversationServiceSpy },
        { provide: PhaseStateService, useValue: phaseStateServiceSpy },
        { provide: ReviewService, useValue: reviewServiceSpy },
        { provide: StoryService, useValue: storyServiceSpy },
        { provide: ToastService, useValue: toastServiceSpy }
      ]
    }).compileComponents();

    mockPhaseStateService = TestBed.inject(PhaseStateService) as jasmine.SpyObj<PhaseStateService>;
    mockReviewService = TestBed.inject(ReviewService) as jasmine.SpyObj<ReviewService>;
    mockStoryService = TestBed.inject(StoryService) as jasmine.SpyObj<StoryService>;
    mockToastService = TestBed.inject(ToastService) as jasmine.SpyObj<ToastService>;

    fixture = TestBed.createComponent(FinalEditPhaseComponent);
    component = fixture.componentInstance;
    component.story = mockStory;
    component.chapterNumber = 1;

    // Setup default service responses
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize component with story data', () => {
    component.ngOnInit();

    expect(component.chapterDraftFromPhase2).toBe('This is the chapter content from phase 2.');
    expect(component.chapterTitleFromPhase2).toBe('Chapter 1: The Beginning');
    expect(component.chapterAnalytics.wordCount).toBeGreaterThan(0);
  });

  it('should load existing revisions from final edit phase', () => {
    component.ngOnInit();

    expect(component.revisions.length).toBe(1);
    expect(component.revisions[0].id).toBe('initial');
    expect(component.revisions[0].name).toBe('Initial Draft');
    expect(component.currentRevisionId).toBe('initial');
  });

  it('should setup quality assessment', () => {
    component.ngOnInit();

    expect(component.qualityAssessment).toBeTruthy();
    expect(component.qualityAssessment?.overallScore).toBe(75);
    expect(component.qualityAssessment?.readinessLevel).toBe('good');
  });

  it('should handle review selection changes', () => {
    const selectionEvent = {
      selectedItems: mockReviewItems,
      totalSelected: 2
    };

    component.onReviewSelectionChanged(selectionEvent);

    expect(component.selectedReviews).toEqual(mockReviewItems);
  });

  it('should handle review requests', () => {
    const requestEvent = {
      requestType: 'comprehensive' as const,
      options: {
        includeCharacters: true,
        includeRaters: true,
        includeEditor: true
      }
    };

    component.onReviewRequested(requestEvent);

    expect(mockToastService.show).toHaveBeenCalledWith('Requesting comprehensive review...', 'info');
  });

  it('should handle add to chat events', () => {
    const addToChatEvent = {
      selectedReviews: mockReviewItems,
      userComment: 'Please apply these reviews'
    };

    component.onAddToChat(addToChatEvent);

    expect(mockToastService.show).toHaveBeenCalledWith('Added 2 reviews to chat', 'success');
  });

  it('should handle empty review selection for add to chat', () => {
    const addToChatEvent = {
      selectedReviews: [],
      userComment: 'No reviews selected'
    };

    component.onAddToChat(addToChatEvent);

    expect(mockToastService.show).toHaveBeenCalledWith('Please select reviews to add to chat', 'warning');
  });

  it('should handle chat message sent', () => {
    const mockMessage: ChatMessage = {
      id: 'msg-1',
      type: 'user',
      content: 'Apply the selected reviews',
      timestamp: new Date()
    };

    spyOn(component, 'processRevisionRequest' as any);
    component.onMessageSent(mockMessage);

    expect(component['processRevisionRequest']).toHaveBeenCalledWith(mockMessage);
  });

  it('should create new revision', () => {
    component.ngOnInit();
    component.selectedReviews = mockReviewItems;

    const initialRevisionCount = component.revisions.length;
    component['createNewRevision']('Test revision');

    expect(component.revisions.length).toBe(initialRevisionCount + 1);
    expect(component.appliedReviewIds.size).toBe(2);
    expect(mockToastService.show).toHaveBeenCalledWith('New revision created', 'success');
  });

  it('should toggle revision history', () => {
    expect(component.showRevisionHistory).toBeFalse();
    
    component.toggleRevisionHistory();
    expect(component.showRevisionHistory).toBeTrue();
    
    component.toggleRevisionHistory();
    expect(component.showRevisionHistory).toBeFalse();
  });

  it('should select revision', () => {
    component.ngOnInit();
    component['createNewRevision']('Test revision');
    
    const newRevisionId = component.revisions[1].id;
    component.selectRevision(newRevisionId);

    expect(component.currentRevisionId).toBe(newRevisionId);
    expect(component.revisions.find(r => r.id === newRevisionId)?.isActive).toBeTrue();
  });

  it('should handle rollback to revision', () => {
    component.ngOnInit();
    component['createNewRevision']('Test revision');
    
    spyOn(window, 'confirm').and.returnValue(true);
    spyOn(component, 'createNewRevision' as any);

    const revisionId = component.revisions[0].id;
    component.rollbackToRevision(revisionId);

    expect(component['createNewRevision']).toHaveBeenCalledWith('Rolled back to Initial Draft');
    expect(mockToastService.show).toHaveBeenCalledWith('Rolled back to Initial Draft', 'info');
  });

  it('should not rollback if user cancels', () => {
    component.ngOnInit();
    
    spyOn(window, 'confirm').and.returnValue(false);
    spyOn(component, 'createNewRevision' as any);

    const revisionId = component.revisions[0].id;
    component.rollbackToRevision(revisionId);

    expect(component['createNewRevision']).not.toHaveBeenCalled();
  });

  it('should toggle quality details', () => {
    expect(component.showQualityDetails).toBeFalse();
    
    component.toggleQualityDetails();
    expect(component.showQualityDetails).toBeTrue();
    
    component.toggleQualityDetails();
    expect(component.showQualityDetails).toBeFalse();
  });

  it('should get correct readiness color', () => {
    component.qualityAssessment = {
      overallScore: 90,
      categoryScores: { characterConsistency: 90, narrativeFlow: 90, literaryQuality: 90, genreSpecific: 90 },
      readinessLevel: 'excellent',
      improvementAreas: [],
      strengths: []
    };
    expect(component.getReadinessColor()).toBe('green');

    component.qualityAssessment.readinessLevel = 'good';
    expect(component.getReadinessColor()).toBe('orange');

    component.qualityAssessment.readinessLevel = 'needs-work';
    expect(component.getReadinessColor()).toBe('red');
  });

  it('should get correct readiness label', () => {
    component.qualityAssessment = {
      overallScore: 90,
      categoryScores: { characterConsistency: 90, narrativeFlow: 90, literaryQuality: 90, genreSpecific: 90 },
      readinessLevel: 'excellent',
      improvementAreas: [],
      strengths: []
    };
    expect(component.getReadinessLabel()).toBe('Ready to Publish');

    component.qualityAssessment.readinessLevel = 'good';
    expect(component.getReadinessLabel()).toBe('Good Quality');

    component.qualityAssessment.readinessLevel = 'needs-work';
    expect(component.getReadinessLabel()).toBe('Needs Improvement');
  });

  it('should update finalization status correctly', () => {
    component.ngOnInit();
    component.appliedReviewIds.add('review-1');
    component.qualityAssessment = {
      overallScore: 75,
      categoryScores: { characterConsistency: 75, narrativeFlow: 75, literaryQuality: 75, genreSpecific: 75 },
      readinessLevel: 'good',
      improvementAreas: [],
      strengths: []
    };

    component['updateFinalizationStatus']();

    expect(component.finalizationChecks.hasAppliedReviews).toBeTrue();
    expect(component.finalizationChecks.qualityThresholdMet).toBeTrue();
    expect(component.canFinalize).toBeTrue();
  });

  it('should not allow finalization without applied reviews', () => {
    component.ngOnInit();
    component.appliedReviewIds.clear();
    component.qualityAssessment = {
      overallScore: 75,
      categoryScores: { characterConsistency: 75, narrativeFlow: 75, literaryQuality: 75, genreSpecific: 75 },
      readinessLevel: 'good',
      improvementAreas: [],
      strengths: []
    };

    component['updateFinalizationStatus']();

    expect(component.canFinalize).toBeFalse();
  });

  it('should not allow finalization with low quality score', () => {
    component.ngOnInit();
    component.appliedReviewIds.add('review-1');
    component.qualityAssessment = {
      overallScore: 60,
      categoryScores: { characterConsistency: 60, narrativeFlow: 60, literaryQuality: 60, genreSpecific: 60 },
      readinessLevel: 'needs-work',
      improvementAreas: [],
      strengths: []
    };

    component['updateFinalizationStatus']();

    expect(component.canFinalize).toBeFalse();
  });

  it('should finalize chapter successfully', () => {
    component.ngOnInit();
    component.canFinalize = true;
    mockStoryService.saveChapter.and.returnValue(of({}));
    spyOn(window, 'confirm').and.returnValue(true);

    component.finalizeChapter();

    expect(mockStoryService.saveChapter).toHaveBeenCalled();
    expect(mockToastService.show).toHaveBeenCalledWith('Chapter finalized successfully!', 'success');
  });

  it('should not finalize chapter if not ready', () => {
    component.canFinalize = false;

    component.finalizeChapter();

    expect(mockStoryService.saveChapter).not.toHaveBeenCalled();
    expect(mockToastService.show).toHaveBeenCalledWith('Chapter is not ready for finalization', 'warning');
  });

  it('should not finalize chapter if user cancels', () => {
    component.canFinalize = true;
    spyOn(window, 'confirm').and.returnValue(false);

    component.finalizeChapter();

    expect(mockStoryService.saveChapter).not.toHaveBeenCalled();
  });

  it('should handle finalization error', () => {
    component.ngOnInit();
    component.canFinalize = true;
    mockStoryService.saveChapter.and.returnValue(throwError('Save error'));
    spyOn(window, 'confirm').and.returnValue(true);

    component.finalizeChapter();

    expect(mockToastService.show).toHaveBeenCalledWith('Error finalizing chapter', 'error');
  });

  it('should get progress percentage', () => {
    component.qualityAssessment = {
      overallScore: 75,
      categoryScores: { characterConsistency: 75, narrativeFlow: 75, literaryQuality: 75, genreSpecific: 75 },
      readinessLevel: 'good',
      improvementAreas: [],
      strengths: []
    };

    expect(component.getProgressPercentage()).toBe(75);
  });

  it('should get applied reviews count', () => {
    component.appliedReviewIds.add('review-1');
    component.appliedReviewIds.add('review-2');

    expect(component.getAppliedReviewsCount()).toBe(2);
  });

  it('should get total revisions count', () => {
    component.ngOnInit();
    component['createNewRevision']('Test revision 1');
    component['createNewRevision']('Test revision 2');

    expect(component.getTotalRevisionsCount()).toBe(3); // Initial + 2 new revisions
  });

  it('should toggle chapter preview', () => {
    expect(component.showChapterPreview).toBeTrue();
    
    component.toggleChapterPreview();
    expect(component.showChapterPreview).toBeFalse();
    
    component.toggleChapterPreview();
    expect(component.showChapterPreview).toBeTrue();
  });

  it('should handle quality score loading error', () => {
    // Override the qualityScore$ property to return an error
    Object.defineProperty(mockReviewService, 'qualityScore$', {
      value: throwError('Quality score error'),
      writable: true
    });
    spyOn(console, 'warn');

    component.ngOnInit();

    expect(console.warn).toHaveBeenCalledWith('Could not load quality scores:', 'Quality score error');
  });

  it('should save phase state', () => {
    component.ngOnInit();
    component.selectedReviews = mockReviewItems;
    component.appliedReviewIds.add('review-1');

    component['savePhaseState']();

    expect(mockPhaseStateService.updatePhaseData).toHaveBeenCalledWith(
      'test-story-1',
      'final_edit',
      jasmine.objectContaining({
        finalChapter: jasmine.any(Object),
        reviewSelection: jasmine.any(Object),
        status: 'active',
        progress: jasmine.any(Object)
      })
    );
  });

  it('should cleanup on destroy', () => {
    spyOn(component['destroy$'], 'next');
    spyOn(component['destroy$'], 'complete');

    component.ngOnDestroy();

    expect(component['destroy$'].next).toHaveBeenCalled();
    expect(component['destroy$'].complete).toHaveBeenCalled();
  });
});
