import { ComponentFixture, TestBed } from '@angular/core/testing';
import { SimpleChanges } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

import { WorldbuildingChatComponent } from './worldbuilding-chat.component';
import { Story, ConversationThread, ConversationBranch, BranchNavigation } from '../../models/story.model';
import { ConversationService } from '../../services/conversation.service';
import { ChatInterfaceComponent } from '../chat-interface/chat-interface.component';

describe('WorldbuildingChatComponent', () => {
  let component: WorldbuildingChatComponent;
  let fixture: ComponentFixture<WorldbuildingChatComponent>;
  let _conversationService: jasmine.SpyObj<ConversationService>;

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
    chapterCreation: {
      plotPoint: '',
      incorporatedFeedback: [],
      feedbackRequests: new Map()
    },
    metadata: {
      version: '1.0.0',
      created: new Date(),
      lastModified: new Date()
    }
  };

  const mockThread: ConversationThread = {
    id: 'thread-1',
    messages: [],
    currentBranchId: 'main',
    branches: new Map([
      ['main', {
        id: 'main',
        name: 'Main',
        parentMessageId: '',
        messageIds: [],
        isActive: true,
        metadata: { created: new Date() }
      }]
    ]),
    metadata: {
      created: new Date(),
      lastModified: new Date(),
      phase: 'worldbuilding' as any
    }
  };

  const mockBranchNavigation: BranchNavigation = {
    currentBranchId: 'main',
    availableBranches: ['main'],
    branchHistory: [],
    canNavigateBack: false,
    canNavigateForward: false
  };

  beforeEach(async () => {
    const conversationSpy = jasmine.createSpyObj('ConversationService', [
      'initializeConversation',
      'getConversation',
      'sendMessage',
      'clearConversation',
      'createBranch',
      'switchBranch',
      'deleteBranch',
      'getCurrentBranchMessages',
      'getAvailableBranches'
    ], {
      currentThread$: new BehaviorSubject<ConversationThread | null>(mockThread),
      branchNavigation$: new BehaviorSubject<BranchNavigation>(mockBranchNavigation),
      isProcessing$: new BehaviorSubject<boolean>(false)
    });

    await TestBed.configureTestingModule({
      imports: [WorldbuildingChatComponent, ChatInterfaceComponent],
      providers: [
        { provide: ConversationService, useValue: conversationSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(WorldbuildingChatComponent);
    component = fixture.componentInstance;
    _conversationService = TestBed.inject(ConversationService) as jasmine.SpyObj<ConversationService>;

    // Setup default return values
    _conversationService.getCurrentBranchMessages.and.returnValue(mockThread.messages);
    _conversationService.getAvailableBranches.and.returnValue([mockThread.branches.get('main')!]);

    // Set required inputs
    component.story = mockStory;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with story input', () => {
    fixture.detectChanges();
    expect(component.story).toEqual(mockStory);
    expect(component.isInitialized).toBe(true);
  });

  it('should handle missing story input', () => {
    component.story = null as any;
    spyOn(component.errorOccurred, 'emit');
    
    fixture.detectChanges();
    
    expect(component.error).toBe('WorldbuildingChat requires a story input');
    expect(component.errorOccurred.emit).toHaveBeenCalledWith('WorldbuildingChat requires a story input');
  });

  it('should initialize chat configuration', () => {
    fixture.detectChanges();
    
    expect(component.chatConfig).toBeDefined();
    expect(component.chatConfig?.phase).toBe('worldbuilding' as any);
    expect(component.chatConfig?.storyId).toBe('test-story-id');
    expect(component.chatConfig?.chapterNumber).toBe(0);
    expect(component.chatConfig?.enableBranching).toBe(true);
    expect(component.chatConfig?.placeholder).toBe('Ask about worldbuilding, describe your world, or request assistance...');
  });

  it('should re-initialize when story changes', () => {
    fixture.detectChanges();
    expect(component.isInitialized).toBe(true);
    
    const newStory = { ...mockStory, id: 'new-story-id' };
    const changes: SimpleChanges = {
      story: {
        currentValue: newStory,
        previousValue: mockStory,
        firstChange: false,
        isFirstChange: () => false
      }
    };
    
    // Update the component's story property
    component.story = newStory;
    component.ngOnChanges(changes);
    
    expect(component.chatConfig?.storyId).toBe('new-story-id');
  });

  it('should not re-initialize on first change', () => {
    const changes: SimpleChanges = {
      story: {
        currentValue: mockStory,
        previousValue: undefined,
        firstChange: true,
        isFirstChange: () => true
      }
    };
    
    spyOn(component as any, 'initializeComponent');
    component.ngOnChanges(changes);
    
    expect((component as any).initializeComponent).not.toHaveBeenCalled();
  });

  it('should emit conversationStarted when message is sent', () => {
    spyOn(component.conversationStarted, 'emit');
    
    component.onMessageSent();
    
    expect(component.conversationStarted.emit).toHaveBeenCalled();
  });

  it('should handle message action events', () => {
    const mockMessage = {
      id: 'msg-1',
      type: 'user' as const,
      content: 'test message',
      timestamp: new Date(),
      metadata: {
        phase: 'plot_outline' as const,
        messageIndex: 0
      }
    };
    const mockEvent = { action: 'edit' as const, message: mockMessage };
    spyOn(console, 'log');
    
    component.onMessageAction(mockEvent);
    
    expect(console.log).toHaveBeenCalledWith('Message action:', mockEvent);
  });

  it('should handle branch changed events', () => {
    spyOn(console, 'log');
    
    component.onBranchChanged('branch-1');
    
    expect(console.log).toHaveBeenCalledWith('Branch changed:', 'branch-1');
  });

  it('should handle conversation cleared events', () => {
    spyOn(console, 'log');
    
    component.onConversationCleared();
    
    expect(console.log).toHaveBeenCalledWith('Conversation cleared');
  });

  it('should handle disabled state', () => {
    component.disabled = true;
    fixture.detectChanges();
    
    expect(component.disabled).toBe(true);
  });

  it('should handle processing state', () => {
    component.processing = true;
    fixture.detectChanges();
    
    expect(component.processing).toBe(true);
  });

  it('should clean up subscriptions on destroy', () => {
    const mockSubscription = jasmine.createSpyObj('Subscription', ['unsubscribe']);
    (component as any).subscriptions = [mockSubscription];
    
    component.ngOnDestroy();
    
    expect(mockSubscription.unsubscribe).toHaveBeenCalled();
  });

  it('should not initialize without story', () => {
    component.story = null as any;
    (component as any).initializeComponent();
    
    expect(component.chatConfig).toBeNull();
    expect(component.isInitialized).toBe(false);
  });
});
