import { TestBed } from '@angular/core/testing';
import { ConversationService, ConversationConfig } from './conversation.service';
import { LocalStorageService } from './local-storage.service';
import { PhaseStateService } from './phase-state.service';
import { ChatMessage, ConversationThread } from '../models/story.model';

describe('ConversationService', () => {
  let service: ConversationService;
  let localStorageService: jasmine.SpyObj<LocalStorageService>;
  let phaseStateService: jasmine.SpyObj<PhaseStateService>;

  const mockConfig: ConversationConfig = {
    phase: 'plot-outline',
    storyId: 'test-story-1',
    chapterNumber: 1,
    enableBranching: true,
    autoSave: true
  };

  beforeEach(() => {
    const localStorageSpy = jasmine.createSpyObj('LocalStorageService', ['getItem', 'setItem']);
    const phaseStateSpy = jasmine.createSpyObj('PhaseStateService', ['getCurrentPhase']);

    TestBed.configureTestingModule({
      providers: [
        ConversationService,
        { provide: LocalStorageService, useValue: localStorageSpy },
        { provide: PhaseStateService, useValue: phaseStateSpy }
      ]
    });

    service = TestBed.inject(ConversationService);
    localStorageService = TestBed.inject(LocalStorageService) as jasmine.SpyObj<LocalStorageService>;
    phaseStateService = TestBed.inject(PhaseStateService) as jasmine.SpyObj<PhaseStateService>;
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('initializeConversation', () => {
    it('should create a new conversation thread when none exists in storage', () => {
      localStorageService.getItem.and.returnValue(null);

      const thread = service.initializeConversation(mockConfig);

      expect(thread).toBeTruthy();
      expect(thread.messages).toEqual([]);
      expect(thread.currentBranchId).toBe('main');
      expect(thread.branches.has('main')).toBe(true);
      expect(thread.metadata.phase).toBe('plot-outline');
    });

    it('should load existing conversation thread from storage', () => {
      const existingThread = {
        id: 'existing-thread',
        messages: [
          {
            id: 'msg-1',
            type: 'user',
            content: 'Hello',
            timestamp: new Date(),
            metadata: { phase: 'plot-outline', messageIndex: 0, branchId: 'main' }
          }
        ],
        currentBranchId: 'main',
        branches: [['main', {
          id: 'main',
          name: 'Main',
          parentMessageId: '',
          messageIds: ['msg-1'],
          isActive: true,
          metadata: { created: new Date() }
        }]],
        metadata: {
          created: new Date(),
          lastModified: new Date(),
          phase: 'plot-outline'
        }
      };

      localStorageService.getItem.and.returnValue(existingThread);

      const thread = service.initializeConversation(mockConfig);

      expect(thread.id).toBe('existing-thread');
      expect(thread.messages.length).toBe(1);
      expect(thread.messages[0].content).toBe('Hello');
    });
  });

  describe('sendMessage', () => {
    beforeEach(() => {
      localStorageService.getItem.and.returnValue(null);
      service.initializeConversation(mockConfig);
    });

    it('should add a user message to the conversation', () => {
      const message = service.sendMessage('Hello world', 'user');

      expect(message.type).toBe('user');
      expect(message.content).toBe('Hello world');
      expect(message.id).toBeTruthy();
      expect(message.timestamp).toBeTruthy();
      expect(message.metadata?.phase).toBe('plot-outline');
      expect(message.metadata?.branchId).toBe('main');
    });

    it('should add an assistant message to the conversation', () => {
      const message = service.sendMessage('Hello back!', 'assistant');

      expect(message.type).toBe('assistant');
      expect(message.content).toBe('Hello back!');
    });

    it('should throw error when conversation not initialized', () => {
      const uninitializedService = new ConversationService(localStorageService, phaseStateService);
      
      expect(() => {
        uninitializedService.sendMessage('test', 'user');
      }).toThrowError('Conversation not initialized');
    });

    it('should save conversation to storage after sending message', () => {
      service.sendMessage('Test message', 'user');

      expect(localStorageService.setItem).toHaveBeenCalled();
    });
  });

  describe('createBranch', () => {
    beforeEach(() => {
      localStorageService.getItem.and.returnValue(null);
      service.initializeConversation(mockConfig);
    });

    it('should create a new branch', () => {
      const userMessage = service.sendMessage('User message', 'user');
      const branch = service.createBranch('Test Branch', userMessage.id);

      expect(branch.name).toBe('Test Branch');
      expect(branch.parentMessageId).toBe(userMessage.id);
      expect(branch.id).toBeTruthy();
      expect(branch.isActive).toBe(false);
    });

    it('should throw error when no active conversation thread', () => {
      const uninitializedService = new ConversationService(localStorageService, phaseStateService);
      
      expect(() => {
        uninitializedService.createBranch('Test Branch');
      }).toThrowError('No active conversation thread');
    });
  });

  describe('switchToBranch', () => {
    beforeEach(() => {
      localStorageService.getItem.and.returnValue(null);
      service.initializeConversation(mockConfig);
    });

    it('should switch to an existing branch', () => {
      const userMessage = service.sendMessage('User message', 'user');
      const branch = service.createBranch('Test Branch', userMessage.id);

      service.switchToBranch(branch.id);

      service.branchNavigation$.subscribe(navigation => {
        expect(navigation.currentBranchId).toBe(branch.id);
      });
    });

    it('should throw error when branch does not exist', () => {
      expect(() => {
        service.switchToBranch('non-existent-branch');
      }).toThrowError('Branch non-existent-branch not found');
    });
  });

  describe('getCurrentBranchMessages', () => {
    beforeEach(() => {
      localStorageService.getItem.and.returnValue(null);
      service.initializeConversation(mockConfig);
    });

    it('should return all messages for main branch', () => {
      service.sendMessage('Message 1', 'user');
      service.sendMessage('Message 2', 'assistant');

      const messages = service.getCurrentBranchMessages();

      expect(messages.length).toBe(2);
      expect(messages[0].content).toBe('Message 1');
      expect(messages[1].content).toBe('Message 2');
    });

    it('should return messages up to branch point plus branch messages', () => {
      const msg1 = service.sendMessage('Message 1', 'user');
      const msg2 = service.sendMessage('Message 2', 'assistant');
      const branch = service.createBranch('Test Branch', msg1.id);
      
      service.switchToBranch(branch.id);
      service.sendMessage('Branch message', 'user');

      const messages = service.getCurrentBranchMessages();

      expect(messages.length).toBe(2); // msg1 + branch message
      expect(messages[0].content).toBe('Message 1');
      expect(messages[1].content).toBe('Branch message');
    });
  });

  describe('getConversationStats', () => {
    beforeEach(() => {
      localStorageService.getItem.and.returnValue(null);
      service.initializeConversation(mockConfig);
    });

    it('should return correct statistics', () => {
      service.sendMessage('User message 1', 'user');
      service.sendMessage('Assistant message 1', 'assistant');
      service.sendMessage('User message 2', 'user');

      const stats = service.getConversationStats();

      expect(stats.totalMessages).toBe(3);
      expect(stats.userMessages).toBe(2);
      expect(stats.assistantMessages).toBe(1);
      expect(stats.branchCount).toBe(1); // main branch
      expect(stats.lastActivity).toBeTruthy();
    });

    it('should return zero stats when no conversation', () => {
      const uninitializedService = new ConversationService(localStorageService, phaseStateService);
      const stats = uninitializedService.getConversationStats();

      expect(stats.totalMessages).toBe(0);
      expect(stats.userMessages).toBe(0);
      expect(stats.assistantMessages).toBe(0);
      expect(stats.branchCount).toBe(0);
      expect(stats.lastActivity).toBeNull();
    });
  });

  describe('clearConversation', () => {
    beforeEach(() => {
      localStorageService.getItem.and.returnValue(null);
      service.initializeConversation(mockConfig);
    });

    it('should clear all messages and reset to initial state', () => {
      service.sendMessage('Message 1', 'user');
      service.sendMessage('Message 2', 'assistant');

      service.clearConversation();

      const messages = service.getCurrentBranchMessages();
      expect(messages.length).toBe(0);

      service.branchNavigation$.subscribe(navigation => {
        expect(navigation.currentBranchId).toBe('main');
        expect(navigation.availableBranches).toEqual(['main']);
      });
    });
  });

  describe('renameBranch', () => {
    beforeEach(() => {
      localStorageService.getItem.and.returnValue(null);
      service.initializeConversation(mockConfig);
    });

    it('should rename an existing branch', () => {
      const userMessage = service.sendMessage('User message', 'user');
      const branch = service.createBranch('Original Name', userMessage.id);

      service.renameBranch(branch.id, 'New Name');

      const branches = service.getAvailableBranches();
      const renamedBranch = branches.find(b => b.id === branch.id);
      expect(renamedBranch?.name).toBe('New Name');
    });

    it('should throw error when branch does not exist', () => {
      expect(() => {
        service.renameBranch('non-existent-branch', 'New Name');
      }).toThrowError('Branch non-existent-branch not found');
    });
  });

  describe('deleteBranch', () => {
    beforeEach(() => {
      localStorageService.getItem.and.returnValue(null);
      service.initializeConversation(mockConfig);
    });

    it('should delete a branch and its messages', () => {
      const userMessage = service.sendMessage('User message', 'user');
      const branch = service.createBranch('Test Branch', userMessage.id);
      
      service.switchToBranch(branch.id);
      service.sendMessage('Branch message', 'user');

      const messageCountBefore = service.getCurrentBranchMessages().length;
      service.deleteBranch(branch.id);

      const branches = service.getAvailableBranches();
      expect(branches.find(b => b.id === branch.id)).toBeUndefined();

      // Should switch back to main branch
      service.branchNavigation$.subscribe(navigation => {
        expect(navigation.currentBranchId).toBe('main');
      });
    });

    it('should not allow deleting main branch', () => {
      expect(() => {
        service.deleteBranch('main');
      }).toThrowError('Cannot delete main branch or no active thread');
    });
  });

  describe('exportConversation', () => {
    beforeEach(() => {
      localStorageService.getItem.and.returnValue(null);
      service.initializeConversation(mockConfig);
    });

    it('should export conversation data', () => {
      service.sendMessage('Test message', 'user');
      
      const exportData = service.exportConversation();

      expect(exportData).toBeTruthy();
      expect(exportData.thread).toBeTruthy();
      expect(exportData.navigation).toBeTruthy();
      expect(exportData.config).toBeTruthy();
      expect(exportData.thread.messages.length).toBe(1);
    });

    it('should return null when no conversation', () => {
      const uninitializedService = new ConversationService(localStorageService, phaseStateService);
      const exportData = uninitializedService.exportConversation();

      expect(exportData).toBeNull();
    });
  });

  describe('importConversation', () => {
    it('should import conversation data', () => {
      const importData = {
        thread: {
          id: 'imported-thread',
          messages: [
            {
              id: 'msg-1',
              type: 'user',
              content: 'Imported message',
              timestamp: new Date(),
              metadata: { phase: 'plot-outline', messageIndex: 0, branchId: 'main' }
            }
          ],
          currentBranchId: 'main',
          branches: [['main', {
            id: 'main',
            name: 'Main',
            parentMessageId: '',
            messageIds: ['msg-1'],
            isActive: true,
            metadata: { created: new Date() }
          }]],
          metadata: {
            created: new Date(),
            lastModified: new Date(),
            phase: 'plot-outline'
          }
        },
        navigation: {
          currentBranchId: 'main',
          availableBranches: ['main'],
          branchHistory: [],
          canNavigateBack: false,
          canNavigateForward: false
        },
        config: mockConfig
      };

      service.importConversation(importData);

      const messages = service.getCurrentBranchMessages();
      expect(messages.length).toBe(1);
      expect(messages[0].content).toBe('Imported message');
    });

    it('should throw error for invalid import data', () => {
      expect(() => {
        service.importConversation({ invalid: 'data' });
      }).toThrowError('Invalid conversation data');
    });
  });
});
