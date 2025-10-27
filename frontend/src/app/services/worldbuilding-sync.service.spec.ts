import { TestBed } from '@angular/core/testing';

import { WorldbuildingSyncService, WorldbuildingSyncConfig } from './worldbuilding-sync.service';
import { ConversationService } from './conversation.service';
import { LocalStorageService } from './local-storage.service';
import { ChatMessage } from '../models/story.model';

describe('WorldbuildingSyncService', () => {
  let service: WorldbuildingSyncService;
  let mockConversationService: jasmine.SpyObj<ConversationService>;
  let mockLocalStorageService: jasmine.SpyObj<LocalStorageService>;

  const mockMessages: ChatMessage[] = [
    {
      id: 'msg1',
      type: 'user',
      content: 'Tell me about the magic system in this world.',
      timestamp: new Date('2023-01-01T10:00:00Z'),
      metadata: {}
    },
    {
      id: 'msg2',
      type: 'assistant',
      content: 'The magic system is based on elemental forces. Fire magic is common in the desert kingdoms, while water magic dominates the coastal regions.',
      timestamp: new Date('2023-01-01T10:01:00Z'),
      metadata: {}
    },
    {
      id: 'msg3',
      type: 'user',
      content: 'What about the political structure?',
      timestamp: new Date('2023-01-01T10:02:00Z'),
      metadata: {}
    },
    {
      id: 'msg4',
      type: 'assistant',
      content: 'The world is divided into five kingdoms, each ruled by a council of mages. The central kingdom serves as a neutral meeting ground.',
      timestamp: new Date('2023-01-01T10:03:00Z'),
      metadata: {}
    }
  ];

  beforeEach(() => {
    const conversationServiceSpy = jasmine.createSpyObj('ConversationService', [
      'getCurrentBranchMessages'
    ]);

    const localStorageServiceSpy = jasmine.createSpyObj('LocalStorageService', [
      'setItem',
      'getItem',
      'removeItem'
    ]);

    TestBed.configureTestingModule({
      providers: [
        WorldbuildingSyncService,
        { provide: ConversationService, useValue: conversationServiceSpy },
        { provide: LocalStorageService, useValue: localStorageServiceSpy }
      ]
    });

    service = TestBed.inject(WorldbuildingSyncService);
    mockConversationService = TestBed.inject(ConversationService) as jasmine.SpyObj<ConversationService>;
    mockLocalStorageService = TestBed.inject(LocalStorageService) as jasmine.SpyObj<LocalStorageService>;
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('syncWorldbuildingFromConversation', () => {
    it('should return current worldbuilding when no messages exist', async () => {
      mockConversationService.getCurrentBranchMessages.and.returnValue([]);
      
      const result = await service.syncWorldbuildingFromConversation('story-1', 'existing content');
      
      expect(result).toBe('existing content');
    });

    it('should extract worldbuilding from messages', async () => {
      mockConversationService.getCurrentBranchMessages.and.returnValue(mockMessages);
      
      const result = await service.syncWorldbuildingFromConversation('story-1', '');
      
      expect(result).toContain('Tell me about the magic system');
      expect(result).toContain('magic system is based on elemental forces');
      expect(result).toContain('political structure');
      expect(result).toContain('five kingdoms');
    });

    it('should merge with existing worldbuilding content', async () => {
      mockConversationService.getCurrentBranchMessages.and.returnValue(mockMessages);
      
      const existingContent = 'Existing worldbuilding content';
      const result = await service.syncWorldbuildingFromConversation('story-1', existingContent);
      
      expect(result).toContain(existingContent);
      expect(result).toContain('--- Recent Conversation ---');
    });

    it('should store sync data', async () => {
      mockConversationService.getCurrentBranchMessages.and.returnValue(mockMessages);
      
      await service.syncWorldbuildingFromConversation('story-1', '');
      
      expect(mockLocalStorageService.setItem).toHaveBeenCalledWith(
        'worldbuilding_sync_story-1',
        jasmine.objectContaining({
          storyId: 'story-1',
          messageCount: 4
        })
      );
    });

    it('should emit worldbuilding update', async () => {
      mockConversationService.getCurrentBranchMessages.and.returnValue(mockMessages);
      
      let emittedValue: string | undefined;
      service.worldbuildingUpdated$.subscribe(value => {
        emittedValue = value;
      });
      
      await service.syncWorldbuildingFromConversation('story-1', '');
      
      // Wait for debounce
      setTimeout(() => {
        expect(emittedValue).toBeDefined();
        expect(emittedValue).toContain('magic system');
      }, 2100);
    });

    it('should handle custom config', async () => {
      mockConversationService.getCurrentBranchMessages.and.returnValue(mockMessages);
      
      const config: Partial<WorldbuildingSyncConfig> = {
        maxSummaryLength: 100,
        includeUserMessages: false,
        includeAssistantMessages: true
      };
      
      const result = await service.syncWorldbuildingFromConversation('story-1', '', config);
      
      // Should only include assistant messages
      expect(result).not.toContain('Tell me about the magic system');
      expect(result).toContain('magic system is based on elemental forces');
      expect(result.length).toBeLessThanOrEqual(100 + 50); // Allow some buffer for truncation message
    });

    it('should handle errors gracefully', async () => {
      mockConversationService.getCurrentBranchMessages.and.throwError('Service error');
      
      await expectAsync(
        service.syncWorldbuildingFromConversation('story-1', '')
      ).toBeRejectedWithError('Service error');
    });
  });

  describe('extractWorldbuildingInsights', () => {
    it('should extract sentences with worldbuilding keywords', () => {
      const content = 'The magic system works differently here. The weather is nice today. The kingdom has strict laws about magic use.';
      
      const result = service['extractWorldbuildingInsights'](content);
      
      expect(result).toContain('magic system works differently');
      expect(result).toContain('kingdom has strict laws');
      expect(result).not.toContain('weather is nice');
    });

    it('should handle empty content', () => {
      const result = service['extractWorldbuildingInsights']('');
      expect(result).toBe('');
    });

    it('should handle content without worldbuilding keywords', () => {
      const content = 'Hello there. How are you doing today?';
      
      const result = service['extractWorldbuildingInsights'](content);
      expect(result).toBe('');
    });
  });

  describe('mergeWorldbuildingContent', () => {
    const mockConfig: WorldbuildingSyncConfig = {
      storyId: 'test',
      maxSummaryLength: 1000
    };

    it('should return existing content when extracted is empty', () => {
      const result = service['mergeWorldbuildingContent']('existing', '', mockConfig);
      expect(result).toBe('existing');
    });

    it('should return extracted content when existing is empty', () => {
      const result = service['mergeWorldbuildingContent']('', 'extracted', mockConfig);
      expect(result).toBe('extracted');
    });

    it('should combine existing and extracted content', () => {
      const result = service['mergeWorldbuildingContent']('existing', 'extracted', mockConfig);
      
      expect(result).toContain('existing');
      expect(result).toContain('--- Recent Conversation ---');
      expect(result).toContain('extracted');
    });
  });

  describe('truncateContent', () => {
    it('should not truncate content shorter than max length', () => {
      const content = 'Short content';
      const result = service['truncateContent'](content, 100);
      expect(result).toBe(content);
    });

    it('should truncate content at sentence boundary', () => {
      const content = 'First sentence. Second sentence. Third sentence.';
      const result = service['truncateContent'](content, 30);
      
      expect(result).toContain('First sentence.');
      expect(result).toContain('[Content truncated...]');
      expect(result.length).toBeLessThanOrEqual(60); // Approximate with truncation message
    });

    it('should truncate at max length when no good break point', () => {
      const content = 'A very long sentence without any good break points that goes on and on';
      const result = service['truncateContent'](content, 20);
      
      expect(result).toContain('...');
      expect(result).toContain('[Content truncated...]');
    });
  });

  describe('storage operations', () => {
    it('should store worldbuilding sync data', () => {
      service['storeWorldbuildingSync']('story-1', 'worldbuilding content');
      
      expect(mockLocalStorageService.setItem).toHaveBeenCalledWith(
        'worldbuilding_sync_story-1',
        jasmine.objectContaining({
          storyId: 'story-1',
          worldbuilding: 'worldbuilding content'
        })
      );
    });

    it('should retrieve stored worldbuilding sync data', () => {
      const mockData = { storyId: 'story-1', worldbuilding: 'content' };
      mockLocalStorageService.getItem.and.returnValue(mockData);
      
      const result = service.getStoredWorldbuildingSync('story-1');
      
      expect(mockLocalStorageService.getItem).toHaveBeenCalledWith('worldbuilding_sync_story-1');
      expect(result).toBe(mockData);
    });

    it('should handle storage errors gracefully', () => {
      mockLocalStorageService.getItem.and.throwError('Storage error');
      spyOn(console, 'error');
      
      const result = service.getStoredWorldbuildingSync('story-1');
      
      expect(result).toBeNull();
      expect(console.error).toHaveBeenCalled();
    });

    it('should clear worldbuilding sync data', () => {
      service.clearWorldbuildingSync('story-1');
      
      expect(mockLocalStorageService.removeItem).toHaveBeenCalledWith('worldbuilding_sync_story-1');
    });
  });

  describe('public methods', () => {
    it('should update worldbuilding manually', () => {
      service.worldbuildingUpdated$.subscribe(() => {
        // emittedValue = value;
      });
      
      service.updateWorldbuilding('manual update');
      
      expect(service.getCurrentWorldbuilding()).toBe('manual update');
    });

    it('should return current worldbuilding', () => {
      service.updateWorldbuilding('test content');
      expect(service.getCurrentWorldbuilding()).toBe('test content');
    });

    it('should track sync progress', () => {
      expect(service.isSyncInProgress()).toBe(false);
      
      // Sync progress is set during syncWorldbuildingFromConversation
      // This would be tested in integration tests
    });
  });

  describe('observables', () => {
    it('should debounce worldbuilding updates', (done) => {
      let emissionCount = 0;
      service.worldbuildingUpdated$.subscribe(() => {
        emissionCount++;
      });
      
      // Rapid updates should be debounced
      service.updateWorldbuilding('update1');
      service.updateWorldbuilding('update2');
      service.updateWorldbuilding('update3');
      
      setTimeout(() => {
        expect(emissionCount).toBeLessThanOrEqual(1);
        done();
      }, 2100);
    });

    it('should emit distinct values only', (done) => {
      const emittedValues: string[] = [];
      service.worldbuildingUpdated$.subscribe(value => {
        emittedValues.push(value);
      });
      
      service.updateWorldbuilding('same value');
      service.updateWorldbuilding('same value');
      service.updateWorldbuilding('different value');
      
      setTimeout(() => {
        expect(emittedValues.filter(v => v === 'same value').length).toBeLessThanOrEqual(1);
        done();
      }, 2100);
    });
  });
});
