import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CommonModule } from '@angular/common';
import { of, BehaviorSubject } from 'rxjs';

import { WorldbuildingChatComponent } from './worldbuilding-chat.component';
import { ChatInterfaceComponent } from '../chat-interface/chat-interface.component';
import { ConversationService } from '../../services/conversation.service';
import { WorldbuildingSyncService } from '../../services/worldbuilding-sync.service';
import { Story, ChatMessage, ConversationThread } from '../../models/story.model';

describe('WorldbuildingChatComponent', () => {
  let component: WorldbuildingChatComponent;
  let fixture: ComponentFixture<WorldbuildingChatComponent>;
  let mockConversationService: jasmine.SpyObj<ConversationService>;
  let mockWorldbuildingSyncService: jasmine.SpyObj<WorldbuildingSyncService>;

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
      worldbuilding: 'Initial worldbuilding content'
    },
    characters: new Map(),
    raters: new Map(),
    story: {
      summary: '',
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
      plotPoint: '',
      incorporatedFeedback: [],
      feedbackRequests: new Map()
    },
    metadata: {
      created: new Date(),
      lastModified: new Date(),
      version: '1.0.0'
    }
  };

  const mockThread: ConversationThread = {
    id: 'test-thread',
    messages: [],
    currentBranchId: 'main',
    branches: new Map(),
    metadata: {
      created: new Date(),
      lastModified: new Date(),
      phase: 'plot_outline'
    }
  };

  beforeEach(async () => {
    const conversationServiceSpy = jasmine.createSpyObj('ConversationService', [
      'initializeConversation',
      'sendMessage',
      'getCurrentBranchMessages',
      'createBranch',
      'switchToBranch',
      'clearConversation'
    ], {
      currentThread$: new BehaviorSubject<ConversationThread | null>(mockThread),
      isProcessing$: new BehaviorSubject<boolean>(false)
    });

    const worldbuildingSyncServiceSpy = jasmine.createSpyObj('WorldbuildingSyncService', [
      'syncWorldbuildingFromConversation',
      'updateWorldbuilding',
      'getCurrentWorldbuilding',
      'isSyncInProgress'
    ], {
      worldbuildingUpdated$: new BehaviorSubject<string>(''),
      syncInProgress$: new BehaviorSubject<boolean>(false)
    });

    await TestBed.configureTestingModule({
      imports: [
        CommonModule,
        WorldbuildingChatComponent,
        ChatInterfaceComponent
      ],
      providers: [
        { provide: ConversationService, useValue: conversationServiceSpy },
        { provide: WorldbuildingSyncService, useValue: worldbuildingSyncServiceSpy }
      ]
    }).compileComponents();

    mockConversationService = TestBed.inject(ConversationService) as jasmine.SpyObj<ConversationService>;
    mockWorldbuildingSyncService = TestBed.inject(WorldbuildingSyncService) as jasmine.SpyObj<WorldbuildingSyncService>;

    fixture = TestBed.createComponent(WorldbuildingChatComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    component.story = mockStory;
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  it('should emit error when no story is provided', () => {
    spyOn(component.errorOccurred, 'emit');
    
    component.ngOnInit();
    
    expect(component.errorOccurred.emit).toHaveBeenCalledWith('WorldbuildingChat requires a story input');
  });

  it('should initialize component with story', () => {
    component.story = mockStory;
    
    fixture.detectChanges();
    
    expect(component.isInitialized).toBe(true);
    expect(component.chatConfig).toBeTruthy();
    expect(component.chatConfig?.phase).toBe('plot_outline');
    expect(component.chatConfig?.storyId).toBe('test-story-id');
    expect(component.chatConfig?.chapterNumber).toBe(0);
    expect(component.currentWorldbuilding).toBe('Initial worldbuilding content');
  });

  it('should configure chat interface correctly', () => {
    component.story = mockStory;
    
    fixture.detectChanges();
    
    expect(component.chatConfig).toEqual({
      phase: 'plot_outline',
      storyId: 'test-story-id',
      chapterNumber: 0,
      enableBranching: true,
      enableMessageTypes: ['user', 'assistant'],
      placeholder: 'Describe your world, ask questions, or request worldbuilding assistance...',
      maxHeight: '400px',
      showTimestamps: true,
      showMessageTypes: true,
      allowMessageEditing: true
    });
  });

  it('should handle message sent event', () => {
    component.story = mockStory;
    fixture.detectChanges();

    const mockMessage: ChatMessage = {
      id: 'test-message',
      type: 'user',
      content: 'Test message',
      timestamp: new Date(),
      metadata: {
        phase: 'plot_outline',
        messageIndex: 0
      }
    };

    spyOn(component.conversationStarted, 'emit');
    spyOn(component, 'syncWorldbuildingFromConversation' as any);

    component.onMessageSent(mockMessage);

    expect(component.conversationStarted.emit).toHaveBeenCalled();
    
    // Check that sync is called after delay
    setTimeout(() => {
      expect(component['syncWorldbuildingFromConversation']).toHaveBeenCalled();
    }, 1100);
  });

  it('should handle worldbuilding updates from sync service', () => {
    component.story = mockStory;
    fixture.detectChanges();

    spyOn(component.worldbuildingUpdated, 'emit');

    // Simulate worldbuilding update from sync service
    const updatedWorldbuilding = 'Updated worldbuilding content';
    (mockWorldbuildingSyncService.worldbuildingUpdated$ as BehaviorSubject<string>).next(updatedWorldbuilding);

    expect(component.currentWorldbuilding).toBe(updatedWorldbuilding);
    expect(component.worldbuildingUpdated.emit).toHaveBeenCalledWith(updatedWorldbuilding);
  });

  it('should handle message actions', () => {
    component.story = mockStory;
    fixture.detectChanges();

    const mockMessage: ChatMessage = {
      id: 'test-message',
      type: 'user',
      content: 'Test message',
      timestamp: new Date(),
      metadata: {
        phase: 'plot_outline',
        messageIndex: 0
      }
    };

    spyOn(component, 'syncWorldbuildingFromConversation' as any);

    component.onMessageAction({
      action: 'edit',
      message: mockMessage,
      data: { newContent: 'Edited content' }
    });

    // Check that sync is called after delay for edit actions
    setTimeout(() => {
      expect(component['syncWorldbuildingFromConversation']).toHaveBeenCalled();
    }, 600);
  });

  it('should handle branch changes', () => {
    component.story = mockStory;
    fixture.detectChanges();

    spyOn(component, 'syncWorldbuildingFromConversation' as any);

    component.onBranchChanged('new-branch-id');

    // Check that sync is called after delay
    setTimeout(() => {
      expect(component['syncWorldbuildingFromConversation']).toHaveBeenCalled();
    }, 600);
  });

  it('should handle conversation cleared', () => {
    component.story = mockStory;
    fixture.detectChanges();

    spyOn(component.worldbuildingUpdated, 'emit');

    component.onConversationCleared();

    expect(component.currentWorldbuilding).toBe('');
    expect(component.worldbuildingUpdated.emit).toHaveBeenCalledWith('');
  });

  it('should sync worldbuilding from conversation', () => {
    component.story = mockStory;
    fixture.detectChanges();

    mockWorldbuildingSyncService.syncWorldbuildingFromConversation.and.returnValue(
      Promise.resolve('Synced worldbuilding')
    );

    component.syncWorldbuilding();

    expect(mockWorldbuildingSyncService.syncWorldbuildingFromConversation).toHaveBeenCalledWith(
      'test-story-id',
      'Initial worldbuilding content'
    );
  });

  it('should update worldbuilding content', () => {
    component.story = mockStory;
    fixture.detectChanges();

    spyOn(component.worldbuildingUpdated, 'emit');

    const newWorldbuilding = 'New worldbuilding content';
    component.updateWorldbuilding(newWorldbuilding);

    expect(component.currentWorldbuilding).toBe(newWorldbuilding);
    expect(component.worldbuildingUpdated.emit).toHaveBeenCalledWith(newWorldbuilding);
  });

  it('should return current worldbuilding', () => {
    component.story = mockStory;
    fixture.detectChanges();

    const result = component.getCurrentWorldbuilding();
    expect(result).toBe('Initial worldbuilding content');
  });

  it('should check if component is ready', () => {
    component.story = mockStory;
    fixture.detectChanges();

    expect(component.isReady()).toBe(true);
  });

  it('should handle errors gracefully', () => {
    component.story = mockStory;
    fixture.detectChanges();

    spyOn(component.errorOccurred, 'emit');
    spyOn(console, 'error');

    // Simulate error in sync service
    mockWorldbuildingSyncService.syncWorldbuildingFromConversation.and.returnValue(
      Promise.reject(new Error('Sync failed'))
    );

    component.syncWorldbuilding();

    // Wait for promise to reject
    setTimeout(() => {
      expect(console.error).toHaveBeenCalled();
      expect(component.errorOccurred.emit).toHaveBeenCalledWith('Failed to sync worldbuilding data');
    }, 100);
  });

  it('should handle disabled state', () => {
    component.story = mockStory;
    component.disabled = true;
    fixture.detectChanges();

    expect(component.disabled).toBe(true);
  });

  it('should handle processing state', () => {
    component.story = mockStory;
    component.processing = true;
    fixture.detectChanges();

    expect(component.processing).toBe(true);
  });

  it('should clean up subscriptions on destroy', () => {
    component.story = mockStory;
    fixture.detectChanges();

    const subscriptions = component['subscriptions'];
    spyOn(subscriptions[0], 'unsubscribe');
    spyOn(subscriptions[1], 'unsubscribe');

    component.ngOnDestroy();

    expect(subscriptions[0].unsubscribe).toHaveBeenCalled();
    expect(subscriptions[1].unsubscribe).toHaveBeenCalled();
  });

  it('should render loading state when not initialized', () => {
    component.story = mockStory;
    component.isInitialized = false;
    fixture.detectChanges();

    const loadingElement = fixture.nativeElement.querySelector('.loading-state');
    expect(loadingElement).toBeTruthy();
    expect(loadingElement.textContent).toContain('Initializing worldbuilding chat...');
  });

  it('should render error state when no story provided', () => {
    component.story = null as any;
    fixture.detectChanges();

    const errorElement = fixture.nativeElement.querySelector('.error-state');
    expect(errorElement).toBeTruthy();
    expect(errorElement.textContent).toContain('Unable to initialize worldbuilding chat: No story provided');
  });

  it('should render chat interface when initialized', () => {
    component.story = mockStory;
    fixture.detectChanges();

    const chatInterface = fixture.nativeElement.querySelector('app-chat-interface');
    expect(chatInterface).toBeTruthy();
  });

  it('should render worldbuilding summary panel', () => {
    component.story = mockStory;
    fixture.detectChanges();

    const summaryPanel = fixture.nativeElement.querySelector('.worldbuilding-summary-panel');
    expect(summaryPanel).toBeTruthy();

    const worldbuildingText = fixture.nativeElement.querySelector('.worldbuilding-text pre');
    expect(worldbuildingText.textContent).toBe('Initial worldbuilding content');
  });

  it('should render empty state when no worldbuilding content', () => {
    const storyWithoutWorldbuilding = { ...mockStory };
    storyWithoutWorldbuilding.general.worldbuilding = '';
    component.story = storyWithoutWorldbuilding;
    fixture.detectChanges();

    const emptyState = fixture.nativeElement.querySelector('.empty-state');
    expect(emptyState).toBeTruthy();
    expect(emptyState.textContent).toContain('No worldbuilding content yet.');
  });

  it('should render sync button', () => {
    component.story = mockStory;
    fixture.detectChanges();

    const syncButton = fixture.nativeElement.querySelector('.sync-button');
    expect(syncButton).toBeTruthy();
    expect(syncButton.textContent.trim()).toBe('Sync');
  });

  it('should call syncWorldbuilding when sync button is clicked', () => {
    component.story = mockStory;
    fixture.detectChanges();

    spyOn(component, 'syncWorldbuilding');

    const syncButton = fixture.nativeElement.querySelector('.sync-button');
    syncButton.click();

    expect(component.syncWorldbuilding).toHaveBeenCalled();
  });

  // New accessibility and navigation tests
  describe('Accessibility Features', () => {
    beforeEach(() => {
      component.story = mockStory;
      fixture.detectChanges();
    });

    it('should initialize with proper mobile view detection', () => {
      expect(component.isMobileView).toBeDefined();
      expect(component.focusedPanel).toBe('chat');
    });

    it('should handle keyboard shortcuts', () => {
      spyOn(component, 'toggleKeyboardHelp');
      spyOn(component, 'syncWorldbuilding');

      // Test Ctrl+/ for help
      const helpEvent = new KeyboardEvent('keydown', { key: '/', ctrlKey: true });
      component.onKeyDown(helpEvent);
      expect(component.toggleKeyboardHelp).toHaveBeenCalled();

      // Test Ctrl+S for sync
      const syncEvent = new KeyboardEvent('keydown', { key: 's', ctrlKey: true });
      component.onKeyDown(syncEvent);
      expect(component.syncWorldbuilding).toHaveBeenCalled();
    });

    it('should handle mobile panel switching', () => {
      component.isMobileView = true;
      spyOn(component, 'switchToPanel');

      const event1 = new KeyboardEvent('keydown', { key: '1', altKey: true });
      const event2 = new KeyboardEvent('keydown', { key: '2', altKey: true });

      component.onKeyDown(event1);
      component.onKeyDown(event2);

      expect(component.switchToPanel).toHaveBeenCalledWith('summary');
      expect(component.switchToPanel).toHaveBeenCalledWith('chat');
    });

    it('should handle escape key for help dialog', () => {
      component.showKeyboardHelpDialog = true;
      spyOn(component, 'hideKeyboardHelp');

      const escapeEvent = new KeyboardEvent('keydown', { key: 'Escape' });
      component.onKeyDown(escapeEvent);

      expect(component.hideKeyboardHelp).toHaveBeenCalled();
    });

    it('should update mobile view on window resize', () => {
      spyOn(component, 'updateMobileView' as any);
      component.onResize();
      expect((component as any).updateMobileView).toHaveBeenCalled();
    });

    it('should switch panels correctly', () => {
      component.switchToPanel('summary');
      expect(component.focusedPanel).toBe('summary');

      component.switchToPanel('chat');
      expect(component.focusedPanel).toBe('chat');
    });

    it('should toggle keyboard help visibility', () => {
      expect(component.showKeyboardHelpDialog).toBe(false);
      
      component.toggleKeyboardHelp();
      expect(component.showKeyboardHelpDialog).toBe(true);
      
      component.toggleKeyboardHelp();
      expect(component.showKeyboardHelpDialog).toBe(false);
    });

    it('should handle focus management for skip links', () => {
      const event = new Event('click');
      spyOn(event, 'preventDefault');

      component.focusSummaryPanel(event);
      expect(event.preventDefault).toHaveBeenCalled();
      expect(component.focusedPanel).toBe('summary');

      component.focusChatPanel(event);
      expect(event.preventDefault).toHaveBeenCalled();
      expect(component.focusedPanel).toBe('chat');
    });
  });
});
