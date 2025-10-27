import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { By } from '@angular/platform-browser';
import { BehaviorSubject } from 'rxjs';

import { ChatInterfaceComponent, ChatInterfaceConfig } from './chat-interface.component';
import { ConversationService } from '../../services/conversation.service';
import { ChatMessage, ConversationThread, ConversationBranch, BranchNavigation } from '../../models/story.model';

describe('ChatInterfaceComponent', () => {
  let component: ChatInterfaceComponent;
  let fixture: ComponentFixture<ChatInterfaceComponent>;
  let conversationService: jasmine.SpyObj<ConversationService>;

  const mockConfig: ChatInterfaceConfig = {
    phase: 'plot-outline',
    storyId: 'test-story-1',
    chapterNumber: 1,
    enableBranching: true,
    showTimestamps: true,
    showMessageTypes: true,
    allowMessageEditing: true
  };

  const mockThread: ConversationThread = {
    id: 'test-thread',
    messages: [
      {
        id: 'msg-1',
        type: 'user',
        content: 'Hello',
        timestamp: new Date(),
        metadata: { phase: 'plot-outline', messageIndex: 0, branchId: 'main' }
      },
      {
        id: 'msg-2',
        type: 'assistant',
        content: 'Hello back!',
        timestamp: new Date(),
        metadata: { phase: 'plot-outline', messageIndex: 1, branchId: 'main' }
      }
    ],
    currentBranchId: 'main',
    branches: new Map([
      ['main', {
        id: 'main',
        name: 'Main',
        parentMessageId: '',
        messageIds: ['msg-1', 'msg-2'],
        isActive: true,
        metadata: { created: new Date() }
      }]
    ]),
    metadata: {
      created: new Date(),
      lastModified: new Date(),
      phase: 'plot-outline'
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
      'sendMessage',
      'createBranch',
      'switchToBranch',
      'renameBranch',
      'deleteBranch',
      'clearConversation',
      'getCurrentBranchMessages',
      'getAvailableBranches'
    ], {
      currentThread$: new BehaviorSubject<ConversationThread | null>(mockThread),
      branchNavigation$: new BehaviorSubject<BranchNavigation>(mockBranchNavigation),
      isProcessing$: new BehaviorSubject<boolean>(false)
    });

    await TestBed.configureTestingModule({
      imports: [ChatInterfaceComponent, FormsModule],
      providers: [
        { provide: ConversationService, useValue: conversationSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ChatInterfaceComponent);
    component = fixture.componentInstance;
    conversationService = TestBed.inject(ConversationService) as jasmine.SpyObj<ConversationService>;

    // Setup default return values
    conversationService.getCurrentBranchMessages.and.returnValue(mockThread.messages);
    conversationService.getAvailableBranches.and.returnValue([mockThread.branches.get('main')!]);

    component.config = mockConfig;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize conversation on ngOnInit', () => {
    component.ngOnInit();

    expect(conversationService.initializeConversation).toHaveBeenCalledWith({
      phase: 'plot-outline',
      storyId: 'test-story-1',
      chapterNumber: 1,
      enableBranching: true,
      autoSave: true
    });
  });

  it('should throw error if config is not provided', () => {
    component.config = undefined as unknown as ChatInterfaceConfig;

    expect(() => {
      component.ngOnInit();
    }).toThrowError('ChatInterfaceComponent requires config input');
  });

  it('should display messages correctly', () => {
    component.ngOnInit();
    fixture.detectChanges();

    const messageElements = fixture.debugElement.queryAll(By.css('.message-container'));
    expect(messageElements.length).toBe(2);

    const userMessage = messageElements[0];
    const assistantMessage = messageElements[1];

    expect(userMessage.nativeElement.textContent).toContain('Hello');
    expect(assistantMessage.nativeElement.textContent).toContain('Hello back!');
  });

  it('should show empty state when no messages', () => {
    conversationService.getCurrentBranchMessages.and.returnValue([]);
    component.ngOnInit();
    fixture.detectChanges();

    const emptyState = fixture.debugElement.query(By.css('.empty-state'));
    expect(emptyState).toBeTruthy();
    expect(emptyState.nativeElement.textContent).toContain('Start Your Conversation');
  });

  it('should send message when send button is clicked', () => {
    const mockMessage: ChatMessage = {
      id: 'new-msg',
      type: 'user',
      content: 'New message',
      timestamp: new Date(),
      metadata: { phase: 'plot-outline', messageIndex: 2, branchId: 'main' }
    };

    conversationService.sendMessage.and.returnValue(mockMessage);
    
    component.ngOnInit();
    component.messageText = 'New message';
    fixture.detectChanges();

    const sendButton = fixture.debugElement.query(By.css('.send-button'));
    sendButton.nativeElement.click();

    expect(conversationService.sendMessage).toHaveBeenCalledWith('New message', 'user');
    expect(component.messageText).toBe('');
  });

  it('should send message when Enter key is pressed', () => {
    const mockMessage: ChatMessage = {
      id: 'new-msg',
      type: 'user',
      content: 'New message',
      timestamp: new Date(),
      metadata: { phase: 'plot-outline', messageIndex: 2, branchId: 'main' }
    };

    conversationService.sendMessage.and.returnValue(mockMessage);
    
    component.ngOnInit();
    component.messageText = 'New message';
    fixture.detectChanges();

    const textarea = fixture.debugElement.query(By.css('.message-input'));
    const event = new KeyboardEvent('keydown', { key: 'Enter' });
    spyOn(event, 'preventDefault');

    textarea.nativeElement.dispatchEvent(event);
    component.onKeyPress(event);

    expect(event.preventDefault).toHaveBeenCalled();
    expect(conversationService.sendMessage).toHaveBeenCalledWith('New message', 'user');
  });

  it('should not send message when Shift+Enter is pressed', () => {
    component.ngOnInit();
    component.messageText = 'New message';
    fixture.detectChanges();

    const event = new KeyboardEvent('keydown', { key: 'Enter', shiftKey: true });
    spyOn(event, 'preventDefault');

    component.onKeyPress(event);

    expect(event.preventDefault).not.toHaveBeenCalled();
    expect(conversationService.sendMessage).not.toHaveBeenCalled();
  });

  it('should not send empty messages', () => {
    component.ngOnInit();
    component.messageText = '   ';
    fixture.detectChanges();

    component.sendMessage();

    expect(conversationService.sendMessage).not.toHaveBeenCalled();
  });

  it('should disable send button when processing', () => {
    component.ngOnInit();
    component.messageText = 'Test message';
    component.processing = true;
    fixture.detectChanges();

    const sendButton = fixture.debugElement.query(By.css('.send-button'));
    expect(sendButton.nativeElement.disabled).toBe(true);
  });

  it('should show branch creation dialog', () => {
    const userMessage = mockThread.messages[0];
    component.ngOnInit();
    fixture.detectChanges();

    component.showCreateBranchDialog(userMessage);

    expect(component.showBranchDialog).toBe(true);
    expect(component.branchParentMessageId).toBe(userMessage.id);
    expect(component.newBranchName).toContain('Hello');
  });

  it('should create branch when dialog is confirmed', () => {
    const mockBranch: ConversationBranch = {
      id: 'new-branch',
      name: 'Test Branch',
      parentMessageId: 'msg-1',
      messageIds: [],
      isActive: false,
      metadata: { created: new Date() }
    };

    conversationService.createBranch.and.returnValue(mockBranch);

    component.ngOnInit();
    component.newBranchName = 'Test Branch';
    component.branchParentMessageId = 'msg-1';

    component.createBranch();

    expect(conversationService.createBranch).toHaveBeenCalledWith('Test Branch', 'msg-1');
    expect(component.showBranchDialog).toBe(false);
  });

  it('should switch to branch when branch arrow is clicked', () => {
    component.ngOnInit();
    fixture.detectChanges();

    component.switchToBranch('test-branch');

    expect(conversationService.switchToBranch).toHaveBeenCalledWith('test-branch');
  });

  it('should clear conversation when clear button is clicked', () => {
    spyOn(window, 'confirm').and.returnValue(true);
    
    component.ngOnInit();
    fixture.detectChanges();

    component.clearConversation();

    expect(conversationService.clearConversation).toHaveBeenCalled();
  });

  it('should not clear conversation when user cancels', () => {
    spyOn(window, 'confirm').and.returnValue(false);
    
    component.ngOnInit();
    fixture.detectChanges();

    component.clearConversation();

    expect(conversationService.clearConversation).not.toHaveBeenCalled();
  });

  it('should start editing message', () => {
    const userMessage = mockThread.messages[0];
    component.ngOnInit();
    fixture.detectChanges();

    component.startEditMessage(userMessage);

    expect(component.editingMessageId).toBe(userMessage.id);
    expect(component.editingMessageText).toBe(userMessage.content);
  });

  it('should not allow editing non-user messages', () => {
    const assistantMessage = mockThread.messages[1];
    component.ngOnInit();
    fixture.detectChanges();

    component.startEditMessage(assistantMessage);

    expect(component.editingMessageId).toBeNull();
  });

  it('should cancel editing message', () => {
    component.ngOnInit();
    component.editingMessageId = 'msg-1';
    component.editingMessageText = 'Editing text';

    component.cancelEditMessage();

    expect(component.editingMessageId).toBeNull();
    expect(component.editingMessageText).toBe('');
  });

  it('should emit messageAction when editing is saved', () => {
    spyOn(component.messageAction, 'emit');
    
    component.ngOnInit();
    component.editingMessageId = 'msg-1';
    component.editingMessageText = 'Updated message';

    component.saveEditMessage();

    expect(component.messageAction.emit).toHaveBeenCalledWith({
      action: 'edit',
      message: mockThread.messages[0],
      data: { newContent: 'Updated message' }
    });
    expect(component.editingMessageId).toBeNull();
  });

  it('should get correct message type class', () => {
    const userMessage = mockThread.messages[0];
    const assistantMessage = mockThread.messages[1];

    const userClass = component.getMessageTypeClass(userMessage);
    const assistantClass = component.getMessageTypeClass(assistantMessage);

    expect(userClass).toContain('message-user');
    expect(assistantClass).toContain('message-assistant');
  });

  it('should get correct message type label', () => {
    const userMessage = mockThread.messages[0];
    const assistantMessage = mockThread.messages[1];

    expect(component.getMessageTypeLabel(userMessage)).toBe('You');
    expect(component.getMessageTypeLabel(assistantMessage)).toBe('Assistant');
  });

  it('should format timestamp correctly', () => {
    const date = new Date('2023-01-01T12:30:00');
    const formatted = component.formatTimestamp(date);

    expect(formatted).toMatch(/12:30/);
  });

  it('should get correct placeholder text', () => {
    component.config = { ...mockConfig, placeholder: 'Custom placeholder' };
    expect(component.getPlaceholderText()).toBe('Custom placeholder');

    component.config = { ...mockConfig, placeholder: undefined };
    expect(component.getPlaceholderText()).toContain('plot-outline phase');
  });

  it('should check if branch is current', () => {
    component.ngOnInit();
    
    expect(component.isCurrentBranch('main')).toBe(true);
    expect(component.isCurrentBranch('other-branch')).toBe(false);
  });

  it('should check if branch creation is allowed', () => {
    component.config = { ...mockConfig, enableBranching: true };
    component.disabled = false;
    expect(component.canCreateBranch()).toBe(true);

    component.config = { ...mockConfig, enableBranching: false };
    expect(component.canCreateBranch()).toBe(false);

    component.config = { ...mockConfig, enableBranching: true };
    component.disabled = true;
    expect(component.canCreateBranch()).toBe(false);
  });

  it('should check if message editing is allowed', () => {
    const userMessage = mockThread.messages[0];
    const assistantMessage = mockThread.messages[1];

    component.config = { ...mockConfig, allowMessageEditing: true };
    component.disabled = false;

    expect(component.canEditMessage(userMessage)).toBe(true);
    expect(component.canEditMessage(assistantMessage)).toBe(false);

    component.disabled = true;
    expect(component.canEditMessage(userMessage)).toBe(false);
  });

  it('should emit messageSent when message is sent', () => {
    const mockMessage: ChatMessage = {
      id: 'new-msg',
      type: 'user',
      content: 'New message',
      timestamp: new Date(),
      metadata: { phase: 'plot-outline', messageIndex: 2, branchId: 'main' }
    };

    conversationService.sendMessage.and.returnValue(mockMessage);
    spyOn(component.messageSent, 'emit');
    
    component.ngOnInit();
    component.messageText = 'New message';

    component.sendMessage();

    expect(component.messageSent.emit).toHaveBeenCalledWith(mockMessage);
  });

  it('should emit branchChanged when branch is switched', () => {
    spyOn(component.branchChanged, 'emit');
    
    component.ngOnInit();
    component.switchToBranch('test-branch');

    expect(component.branchChanged.emit).toHaveBeenCalledWith('test-branch');
  });

  it('should emit conversationCleared when conversation is cleared', () => {
    spyOn(window, 'confirm').and.returnValue(true);
    spyOn(component.conversationCleared, 'emit');
    
    component.ngOnInit();
    component.clearConversation();

    expect(component.conversationCleared.emit).toHaveBeenCalled();
  });

  it('should handle service errors gracefully', () => {
    conversationService.sendMessage.and.throwError('Service error');
    spyOn(console, 'error');
    
    component.ngOnInit();
    component.messageText = 'Test message';

    component.sendMessage();

    expect(console.error).toHaveBeenCalledWith('Failed to send message:', jasmine.any(Error));
    expect(component.messageText).toBe('Test message'); // Should restore message text
  });

  it('should track messages by ID', () => {
    const message = mockThread.messages[0];
    const trackResult = component.trackByMessageId(0, message);

    expect(trackResult).toBe(message.id);
  });
});
