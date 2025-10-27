import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { of, BehaviorSubject } from 'rxjs';

import { ChapterDetailerPhaseComponent } from './chapter-detailer-phase.component';
import { ChatInterfaceComponent } from '../chat-interface/chat-interface.component';
import { FeedbackSidebarComponent } from '../feedback-sidebar/feedback-sidebar.component';
import { GenerationService } from '../../services/generation.service';
import { ConversationService } from '../../services/conversation.service';
import { PhaseStateService } from '../../services/phase-state.service';
import { FeedbackService } from '../../services/feedback.service';
import { StoryService } from '../../services/story.service';
import { ToastService } from '../../services/toast.service';
import { TokenCountingService } from '../../services/token-counting.service';
import { NewlineToBrPipe } from '../../pipes/newline-to-br.pipe';
import { 
  Story, 
  ChapterComposeState, 
  OutlineItem, 
  ChatMessage,
  EnhancedFeedbackItem,
  GenerateChapterResponse,
  ModifyChapterResponse
} from '../../models/story.model';

describe('ChapterDetailerPhaseComponent', () => {
  let component: ChapterDetailerPhaseComponent;
  let fixture: ComponentFixture<ChapterDetailerPhaseComponent>;
  let mockGenerationService: jasmine.SpyObj<GenerationService>;
  let mockConversationService: jasmine.SpyObj<ConversationService>;
  let mockPhaseStateService: jasmine.SpyObj<PhaseStateService>;
  let mockFeedbackService: jasmine.SpyObj<FeedbackService>;
  let mockStoryService: jasmine.SpyObj<StoryService>;
  let mockToastService: jasmine.SpyObj<ToastService>;
  let mockTokenCountingService: jasmine.SpyObj<TokenCountingService>;

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
      worldbuilding: 'Test worldbuilding'
    },
    characters: new Map(),
    raters: new Map(),
    story: {
      summary: 'Test summary',
      chapters: []
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

  const mockOutlineItems: OutlineItem[] = [
    {
      id: 'outline-1',
      type: 'chapter',
      title: 'Opening Scene',
      description: 'Character introduction and setting establishment',
      order: 1,
      status: 'approved',
      metadata: {
        created: new Date(),
        lastModified: new Date(),
        wordCountEstimate: 500
      }
    },
    {
      id: 'outline-2',
      type: 'plot-point',
      title: 'Inciting Incident',
      description: 'The event that sets the story in motion',
      order: 2,
      status: 'approved',
      metadata: {
        created: new Date(),
        lastModified: new Date(),
        wordCountEstimate: 300
      }
    }
  ];

  const mockChapterComposeState: ChapterComposeState = {
    currentPhase: 'chapter_detail',
    phases: {
      plotOutline: {
        conversation: {
          id: 'conv-1',
          messages: [],
          currentBranchId: 'branch-1',
          branches: new Map(),
          metadata: {
            created: new Date(),
            lastModified: new Date(),
            phase: 'plot_outline'
          }
        },
        outline: {
          items: new Map(mockOutlineItems.map(item => [item.id, item])),
          structure: ['outline-1', 'outline-2'],
          currentFocus: undefined
        },
        draftSummary: 'Test outline summary',
        status: 'completed',
        progress: {
          completedItems: 2,
          totalItems: 2,
          lastActivity: new Date()
        }
      },
      chapterDetailer: {
        conversation: {
          id: 'conv-2',
          messages: [],
          currentBranchId: 'branch-2',
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
          currentBranchId: 'branch-3',
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
      chapterNumber: 1,
      targetWordCount: 2000
    },
    navigation: {
      phaseHistory: ['plot-outline'],
      canGoBack: false,
      canGoForward: false,
      branchNavigation: {
        currentBranchId: 'branch-2',
        availableBranches: ['branch-2'],
        branchHistory: [],
        canNavigateBack: false,
        canNavigateForward: false
      }
    },
    overallProgress: {
      currentStep: 2,
      totalSteps: 3,
      phaseCompletionStatus: {
        'plot-outline': true,
        'chapter-detailer': false,
        'final-edit': false
      }
    },
    metadata: {
      created: new Date(),
      lastModified: new Date(),
      version: '1.0.0'
    }
  };

  beforeEach(async () => {
    const generationServiceSpy = jasmine.createSpyObj('GenerationService', [
      'generateChapter',
      'modifyChapter',
      'requestCharacterFeedback',
      'requestRaterFeedback'
    ]);
    const conversationServiceSpy = jasmine.createSpyObj('ConversationService', [
      'getConversation',
      'addMessage',
      'updateConversation'
    ]);
    const phaseStateServiceSpy = jasmine.createSpyObj('PhaseStateService', [
      'initializeChapterComposeState',
      'updatePhaseState',
      'validatePhaseTransition'
    ]);
    const feedbackServiceSpy = jasmine.createSpyObj('FeedbackService', [
      'getFeedbackItems',
      'requestFeedback',
      'markFeedbackIncorporated'
    ]);
    const storyServiceSpy = jasmine.createSpyObj('StoryService', [
      'updateStory',
      'saveStory'
    ]);
    const toastServiceSpy = jasmine.createSpyObj('ToastService', [
      'showSuccess',
      'showError',
      'showWarning'
    ]);
    const tokenCountingServiceSpy = jasmine.createSpyObj('TokenCountingService', [
      'countWords',
      'countTokens'
    ]);

    // Set up spy return values
    phaseStateServiceSpy.chapterComposeState$ = new BehaviorSubject(mockChapterComposeState);
    tokenCountingServiceSpy.countWords.and.returnValue(100);

    await TestBed.configureTestingModule({
      imports: [
        FormsModule,
        ChapterDetailerPhaseComponent,
        ChatInterfaceComponent,
        FeedbackSidebarComponent,
        NewlineToBrPipe
      ],
      providers: [
        { provide: GenerationService, useValue: generationServiceSpy },
        { provide: ConversationService, useValue: conversationServiceSpy },
        { provide: PhaseStateService, useValue: phaseStateServiceSpy },
        { provide: FeedbackService, useValue: feedbackServiceSpy },
        { provide: StoryService, useValue: storyServiceSpy },
        { provide: ToastService, useValue: toastServiceSpy },
        { provide: TokenCountingService, useValue: tokenCountingServiceSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ChapterDetailerPhaseComponent);
    component = fixture.componentInstance;
    
    // Inject spies
    mockGenerationService = TestBed.inject(GenerationService) as jasmine.SpyObj<GenerationService>;
    mockConversationService = TestBed.inject(ConversationService) as jasmine.SpyObj<ConversationService>;
    mockPhaseStateService = TestBed.inject(PhaseStateService) as jasmine.SpyObj<PhaseStateService>;
    mockFeedbackService = TestBed.inject(FeedbackService) as jasmine.SpyObj<FeedbackService>;
    mockStoryService = TestBed.inject(StoryService) as jasmine.SpyObj<StoryService>;
    mockToastService = TestBed.inject(ToastService) as jasmine.SpyObj<ToastService>;
    mockTokenCountingService = TestBed.inject(TokenCountingService) as jasmine.SpyObj<TokenCountingService>;

    // Set component inputs
    component.story = mockStory;
    component.chapterNumber = 1;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('Component Initialization', () => {
    it('should initialize with correct default values', () => {
      expect(component.targetWordCount).toBe(2000);
      expect(component.showChat).toBe(true);
      expect(component.showFeedbackSidebar).toBe(true);
      expect(component.draftVersions).toEqual([]);
      expect(component.currentVersionId).toBe('');
    });

    it('should set up chat and feedback configurations', () => {
      component.ngOnInit();
      
      expect(component.chatConfig.phase).toBe('chapter-detailer');
      expect(component.chatConfig.storyId).toBe('test-story-1');
      expect(component.chatConfig.chapterNumber).toBe(1);
      
      expect(component.feedbackConfig.phase).toBe('chapter-detailer');
      expect(component.feedbackConfig.storyId).toBe('test-story-1');
      expect(component.feedbackConfig.chapterNumber).toBe(1);
    });

    it('should load plot outline data from phase state service', () => {
      component.ngOnInit();
      
      expect(component.plotOutlineItems).toEqual(mockOutlineItems);
      expect(component.plotOutlineSummary).toBe('Test outline summary');
    });
  });

  describe('Plot Outline Display', () => {
    beforeEach(() => {
      component.ngOnInit();
    });

    it('should toggle outline details visibility', () => {
      expect(component.showOutlineDetails).toBe(false);
      
      component.toggleOutlineDetails();
      expect(component.showOutlineDetails).toBe(true);
      
      component.toggleOutlineDetails();
      expect(component.showOutlineDetails).toBe(false);
    });

    it('should return correct outline items count', () => {
      expect(component.getOutlineItemsCount()).toBe(2);
    });
  });

  describe('Draft Version Management', () => {
    beforeEach(() => {
      component.ngOnInit();
    });

    it('should create new version correctly', () => {
      const content = 'Test chapter content';
      const title = 'Test Chapter';
      
      const versionId = component.createNewVersion(content, title, 'initial');
      
      expect(versionId).toBe('v1');
      expect(component.draftVersions).toHaveSize(1);
      expect(component.draftVersions[0].content).toBe(content);
      expect(component.draftVersions[0].title).toBe(title);
      expect(component.draftVersions[0].sourceType).toBe('initial');
      expect(mockTokenCountingService.countWords).toHaveBeenCalledWith(content);
    });

    it('should switch to version correctly', () => {
      // Create two versions
      const version1Id = component.createNewVersion('Content 1', 'Title 1', 'initial');
      const version2Id = component.createNewVersion('Content 2', 'Title 2', 'chat');
      
      component.switchToVersion(version1Id);
      
      expect(component.currentVersionId).toBe(version1Id);
      expect(component.draftVersions.find(v => v.id === version1Id)?.isActive).toBe(true);
      expect(component.draftVersions.find(v => v.id === version2Id)?.isActive).toBe(false);
    });

    it('should get current version correctly', () => {
      const versionId = component.createNewVersion('Test content', 'Test title', 'initial');
      component.switchToVersion(versionId);
      
      const currentVersion = component.getCurrentVersion();
      
      expect(currentVersion).toBeTruthy();
      expect(currentVersion?.id).toBe(versionId);
      expect(currentVersion?.content).toBe('Test content');
    });

    it('should delete version correctly', () => {
      const version1Id = component.createNewVersion('Content 1', 'Title 1', 'initial');
      const version2Id = component.createNewVersion('Content 2', 'Title 2', 'chat');
      
      component.deleteVersion(version1Id);
      
      expect(component.draftVersions).toHaveSize(1);
      expect(component.draftVersions[0].id).toBe(version2Id);
    });

    it('should not delete the only remaining version', () => {
      const versionId = component.createNewVersion('Content', 'Title', 'initial');
      
      component.deleteVersion(versionId);
      
      expect(component.draftVersions).toHaveSize(1);
      expect(mockToastService.showError).toHaveBeenCalledWith('Cannot delete the only remaining version');
    });
  });

  describe('Word Count Management', () => {
    beforeEach(() => {
      component.ngOnInit();
    });

    it('should calculate word count correctly', () => {
      const text = 'This is a test text';
      mockTokenCountingService.countWords.and.returnValue(5);
      
      const count = component.calculateWordCount(text);
      
      expect(count).toBe(5);
      expect(mockTokenCountingService.countWords).toHaveBeenCalledWith(text);
    });

    it('should get current word count correctly', () => {
      const versionId = component.createNewVersion('Test content', 'Test title', 'initial');
      component.switchToVersion(versionId);
      
      const wordCount = component.getCurrentWordCount();
      
      expect(wordCount).toBe(100); // Mocked return value
    });

    it('should calculate word count progress correctly', () => {
      component.targetWordCount = 1000;
      const versionId = component.createNewVersion('Test content', 'Test title', 'initial');
      component.switchToVersion(versionId);
      
      const progress = component.getWordCountProgress();
      
      expect(progress).toBe(10); // 100/1000 * 100
    });

    it('should update target word count correctly', () => {
      component.updateTargetWordCount(1500);
      
      expect(component.targetWordCount).toBe(1500);
    });

    it('should enforce minimum target word count', () => {
      component.updateTargetWordCount(50);
      
      expect(component.targetWordCount).toBe(100);
    });

    it('should toggle word count settings', () => {
      expect(component.showWordCountSettings).toBe(false);
      
      component.toggleWordCountSettings();
      expect(component.showWordCountSettings).toBe(true);
      
      component.toggleWordCountSettings();
      expect(component.showWordCountSettings).toBe(false);
    });
  });

  describe('Chapter Generation', () => {
    beforeEach(() => {
      component.ngOnInit();
    });

    it('should generate initial chapter successfully', async () => {
      const mockResponse: GenerateChapterResponse = {
        chapterText: 'Generated chapter content'
      };
      mockGenerationService.generateChapter.and.returnValue(of(mockResponse));
      
      await component.generateInitialChapter();
      
      expect(mockGenerationService.generateChapter).toHaveBeenCalledWith(mockStory);
      expect(component.draftVersions).toHaveSize(1);
      expect(component.draftVersions[0].content).toBe('Generated chapter content');
      expect(component.draftVersions[0].sourceType).toBe('initial');
      expect(component.completionCriteria.hasInitialDraft).toBe(true);
      expect(mockToastService.showSuccess).toHaveBeenCalledWith('Initial chapter generated successfully');
    });

    it('should handle initial chapter generation error', async () => {
      mockGenerationService.generateChapter.and.returnValue(of(null as any));
      
      await component.generateInitialChapter();
      
      expect(component.draftVersions).toHaveSize(0);
      expect(component.completionCriteria.hasInitialDraft).toBe(false);
    });

    it('should continue writing successfully', async () => {
      // Set up existing version
      const versionId = component.createNewVersion('Existing content', 'Test Chapter', 'initial');
      component.switchToVersion(versionId);
      
      const mockResponse: ModifyChapterResponse = {
        modifiedChapter: 'Existing content\n\nContinued content',
        wordCount: 200,
        changesSummary: 'Added continuation'
      };
      mockGenerationService.modifyChapter.and.returnValue(of(mockResponse));
      
      await component.continueWriting();
      
      expect(mockGenerationService.modifyChapter).toHaveBeenCalled();
      expect(component.draftVersions).toHaveSize(2);
      expect(component.draftVersions[1].sourceType).toBe('continuation');
      expect(mockToastService.showSuccess).toHaveBeenCalledWith('Chapter continued successfully');
    });

    it('should handle continue writing without current version', async () => {
      await component.continueWriting();
      
      expect(mockToastService.showError).toHaveBeenCalledWith('No current chapter version to continue');
      expect(mockGenerationService.modifyChapter).not.toHaveBeenCalled();
    });
  });

  describe('Chat Integration', () => {
    beforeEach(() => {
      component.ngOnInit();
    });

    it('should process chat message for chapter development', async () => {
      // Set up existing version
      const versionId = component.createNewVersion('Existing content', 'Test Chapter', 'initial');
      component.switchToVersion(versionId);
      
      const mockMessage: ChatMessage = {
        id: 'msg-1',
        type: 'user',
        content: 'Add more dialogue',
        timestamp: new Date()
      };
      
      const mockResponse: ModifyChapterResponse = {
        modifiedChapter: 'Modified content with dialogue',
        wordCount: 150,
        changesSummary: 'Added dialogue'
      };
      mockGenerationService.modifyChapter.and.returnValue(of(mockResponse));
      
      component.onMessageSent(mockMessage);
      
      // Wait for async processing
      await fixture.whenStable();
      
      expect(mockGenerationService.modifyChapter).toHaveBeenCalledWith(
        mockStory,
        'Existing content',
        'Add more dialogue'
      );
    });

    it('should ignore non-user messages', async () => {
      const mockMessage: ChatMessage = {
        id: 'msg-1',
        type: 'assistant',
        content: 'Assistant response',
        timestamp: new Date()
      };
      
      component.onMessageSent(mockMessage);
      
      expect(mockGenerationService.modifyChapter).not.toHaveBeenCalled();
    });
  });

  describe('Feedback Integration', () => {
    beforeEach(() => {
      component.ngOnInit();
    });

    it('should handle feedback selection change', () => {
      const mockFeedbackItems: EnhancedFeedbackItem[] = [
        {
          id: 'feedback-1',
          source: 'Character A',
          type: 'dialog',
          content: 'Add more emotion to dialogue',
          incorporated: false,
          phase: 'chapter-detailer',
          priority: 'high',
          status: 'pending',
          metadata: {
            created: new Date(),
            lastModified: new Date()
          }
        }
      ];
      
      const event = {
        selectedItems: mockFeedbackItems,
        totalSelected: 1
      };
      
      component.onFeedbackSelectionChanged(event);
      
      expect(component.selectedFeedbackItems).toEqual(mockFeedbackItems);
    });

    it('should incorporate selected feedback', async () => {
      // Set up existing version
      const versionId = component.createNewVersion('Existing content', 'Test Chapter', 'initial');
      component.switchToVersion(versionId);
      
      const mockFeedbackItems: EnhancedFeedbackItem[] = [
        {
          id: 'feedback-1',
          source: 'Character A',
          type: 'dialog',
          content: 'Add more emotion',
          incorporated: false,
          phase: 'chapter-detailer',
          priority: 'high',
          status: 'pending',
          metadata: {
            created: new Date(),
            lastModified: new Date()
          }
        }
      ];
      
      const mockResponse: ModifyChapterResponse = {
        modifiedChapter: 'Content with incorporated feedback',
        wordCount: 180,
        changesSummary: 'Incorporated feedback'
      };
      mockGenerationService.modifyChapter.and.returnValue(of(mockResponse));
      
      const event = {
        selectedFeedback: mockFeedbackItems,
        userComment: 'Please focus on emotional depth'
      };
      
      component.onAddFeedbackToChat(event);
      
      // Wait for async processing
      await fixture.whenStable();
      
      expect(mockGenerationService.modifyChapter).toHaveBeenCalled();
      expect(component.completionCriteria.hasFeedbackIncorporated).toBe(true);
      expect(mockToastService.showSuccess).toHaveBeenCalledWith('Feedback incorporated successfully');
    });
  });

  describe('Phase Completion Validation', () => {
    beforeEach(() => {
      component.ngOnInit();
    });

    it('should validate completion criteria correctly', () => {
      // Initially no criteria should be met
      expect(component.canAdvancePhase()).toBe(false);
      expect(component.getCompletionPercentage()).toBe(0);
      
      // Create initial draft
      const versionId = component.createNewVersion('A'.repeat(1500), 'Test Chapter', 'initial');
      component.switchToVersion(versionId);
      component.targetWordCount = 1000;
      
      // Mock word count to meet minimum requirement
      mockTokenCountingService.countWords.and.returnValue(1200);
      
      // Manually set criteria for testing
      component.completionCriteria = {
        hasInitialDraft: true,
        meetsMinWordCount: true,
        hasFeedbackIncorporated: true,
        hasReviewedContent: true
      };
      
      expect(component.canAdvancePhase()).toBe(true);
      expect(component.getCompletionPercentage()).toBe(100);
    });

    it('should calculate completion percentage correctly', () => {
      component.completionCriteria = {
        hasInitialDraft: true,
        meetsMinWordCount: true,
        hasFeedbackIncorporated: false,
        hasReviewedContent: false
      };
      
      expect(component.getCompletionPercentage()).toBe(50);
    });
  });

  describe('UI Helper Methods', () => {
    it('should toggle chat visibility', () => {
      expect(component.showChat).toBe(true);
      
      component.toggleChat();
      expect(component.showChat).toBe(false);
      
      component.toggleChat();
      expect(component.showChat).toBe(true);
    });

    it('should toggle feedback sidebar visibility', () => {
      expect(component.showFeedbackSidebar).toBe(true);
      
      component.toggleFeedbackSidebar();
      expect(component.showFeedbackSidebar).toBe(false);
      
      component.toggleFeedbackSidebar();
      expect(component.showFeedbackSidebar).toBe(true);
    });

    it('should format version display name correctly', () => {
      const version = {
        id: 'v1',
        name: 'v1',
        content: 'Test',
        title: 'Test',
        wordCount: 100,
        created: new Date(),
        sourceType: 'initial' as const,
        incorporatedFeedback: [],
        isActive: true
      };
      
      const displayName = component.getVersionDisplayName(version);
      expect(displayName).toBe('🌟 v1');
    });

    it('should format word count correctly', () => {
      expect(component.formatWordCount(1234)).toBe('1,234');
      expect(component.formatWordCount(500)).toBe('500');
    });

    it('should format date correctly', () => {
      const date = new Date('2023-12-25T10:30:00');
      const formatted = component.formatDate(date);
      
      expect(formatted).toContain('12/25/2023');
      expect(formatted).toContain('10:30');
    });
  });

  describe('Component Cleanup', () => {
    it('should clean up subscriptions on destroy', () => {
      spyOn(component['destroy$'], 'next');
      spyOn(component['destroy$'], 'complete');
      
      component.ngOnDestroy();
      
      expect(component['destroy$'].next).toHaveBeenCalled();
      expect(component['destroy$'].complete).toHaveBeenCalled();
    });
  });
});
