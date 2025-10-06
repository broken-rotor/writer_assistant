import { TestBed } from '@angular/core/testing';
import { LocalStorageService } from './local-storage.service';
import { Story, MemoryState, StateCheckpoint, ConversationTree } from '../../shared/models';

describe('LocalStorageService', () => {
  let service: LocalStorageService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(LocalStorageService);
    // Clear localStorage before each test
    localStorage.clear();
  });

  afterEach(() => {
    // Clean up after each test
    localStorage.clear();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('Storage Initialization', () => {
    it('should initialize storage with default values', () => {
      const info = service.getStorageInfo();
      expect(info.storiesCount).toBe(0);
      expect(info.usedSpace).toBeGreaterThanOrEqual(0);
    });
  });

  describe('Story Management', () => {
    let mockStory: Story;

    beforeEach(() => {
      mockStory = {
        id: 'test-story-1',
        title: 'Test Story',
        genre: 'Mystery',
        length: 'short_story',
        style: 'Literary',
        focusAreas: ['character', 'plot'],
        createdAt: new Date(),
        lastModified: new Date(),
        currentPhase: 'draft',
        progress: 0,
        storageSize: 1024
      };
    });

    it('should save a story', () => {
      service.saveStory(mockStory);
      const retrieved = service.getStory(mockStory.id);
      expect(retrieved).toBeTruthy();
      expect(retrieved?.title).toBe('Test Story');
    });

    it('should retrieve all stories', () => {
      service.saveStory(mockStory);
      const story2 = { ...mockStory, id: 'test-story-2', title: 'Second Story' };
      service.saveStory(story2);

      const allStories = service.getAllStories();
      expect(allStories.length).toBe(2);
    });

    it('should delete a story', () => {
      service.saveStory(mockStory);
      service.deleteStory(mockStory.id);
      const retrieved = service.getStory(mockStory.id);
      expect(retrieved).toBeNull();
    });

    it('should duplicate a story', () => {
      service.saveStory(mockStory);
      const duplicated = service.duplicateStory(mockStory.id);

      expect(duplicated).toBeTruthy();
      expect(duplicated?.id).not.toBe(mockStory.id);
      expect(duplicated?.title).toBe('Test Story (Copy)');

      const allStories = service.getAllStories();
      expect(allStories.length).toBe(2);
    });

    it('should return null when duplicating non-existent story', () => {
      const duplicated = service.duplicateStory('non-existent');
      expect(duplicated).toBeNull();
    });
  });

  describe('Export and Import', () => {
    let mockStory: Story;

    beforeEach(() => {
      mockStory = {
        id: 'export-test',
        title: 'Export Test Story',
        genre: 'Thriller',
        length: 'novel',
        style: 'Suspense',
        focusAreas: ['tension'],
        createdAt: new Date(),
        lastModified: new Date(),
        currentPhase: 'draft',
        progress: 50,
        storageSize: 2048
      };
    });

    it('should export story data', () => {
      service.saveStory(mockStory);
      const exportData = service.exportStory(mockStory.id);

      expect(exportData).toBeTruthy();
      const parsed = JSON.parse(exportData);
      expect(parsed.story.id).toBe(mockStory.id);
      expect(parsed.version).toBe('1.0');
    });

    it('should import story data', () => {
      service.saveStory(mockStory);
      const exportData = service.exportStory(mockStory.id);

      // Clear and re-import
      localStorage.clear();
      const imported = service.importStory(exportData);

      expect(imported).toBeTruthy();
      expect(imported?.title).toBe(mockStory.title);
      expect(imported?.genre).toBe(mockStory.genre);
    });

    it('should return null for invalid import data', () => {
      const result = service.importStory('invalid json');
      expect(result).toBeNull();
    });
  });

  describe('Memory Management', () => {
    const storyId = 'memory-test';
    let mockMemory: MemoryState;

    beforeEach(() => {
      mockMemory = {
        agentId: 'agent-1',
        agentName: 'Writer Agent',
        workingMemory: { currentChapter: 1 },
        episodicMemory: { events: [] },
        semanticMemory: { themes: [] },
        lastUpdated: new Date(),
        size: 512
      };
    });

    it('should save agent memory', () => {
      service.saveAgentMemory(storyId, 'agent-1', mockMemory);
      const retrieved = service.getAgentMemory(storyId, 'agent-1');

      expect(retrieved).toBeTruthy();
      expect(retrieved?.agentName).toBe('Writer Agent');
    });

    it('should save and retrieve story memory', () => {
      const memoryMap = { 'agent-1': mockMemory };
      service.saveStoryMemory(storyId, memoryMap);

      const retrieved = service.getStoryMemory(storyId);
      expect(retrieved).toBeTruthy();
      expect(retrieved?.['agent-1'].agentName).toBe('Writer Agent');
    });

    it('should return null for non-existent agent memory', () => {
      const retrieved = service.getAgentMemory('non-existent', 'agent-1');
      expect(retrieved).toBeNull();
    });

    it('should validate memory consistency', () => {
      service.saveAgentMemory(storyId, 'agent-1', mockMemory);
      const result = service.validateMemoryConsistency(storyId);

      expect(result.isValid).toBe(true);
      expect(result.issues.length).toBe(0);
    });
  });

  describe('Conversation Tree', () => {
    const storyId = 'conversation-test';
    let mockTree: ConversationTree;

    beforeEach(() => {
      mockTree = {
        rootPrompt: {
          id: 'prompt-1',
          content: 'Initial prompt',
          timestamp: new Date(),
          modifications: [],
          storyState: {}
        },
        branches: [],
        currentBranch: 'branch-1',
        currentPrompt: 'prompt-1'
      };
    });

    it('should save conversation tree', () => {
      service.saveConversationTree(storyId, mockTree);
      const retrieved = service.getConversationTree(storyId);

      expect(retrieved).toBeTruthy();
      expect(retrieved?.rootPrompt.content).toBe('Initial prompt');
    });

    it('should return null for non-existent conversation tree', () => {
      const retrieved = service.getConversationTree('non-existent');
      expect(retrieved).toBeNull();
    });
  });

  describe('Checkpoints', () => {
    const storyId = 'checkpoint-test';
    let mockCheckpoint: StateCheckpoint;

    beforeEach(() => {
      mockCheckpoint = {
        id: 'cp-1',
        name: 'Chapter 1 Complete',
        description: 'First chapter finished',
        timestamp: new Date(),
        storyState: { currentChapter: 1 },
        memoryState: {},
        conversationState: {}
      };
    });

    it('should save checkpoint', () => {
      service.saveCheckpoint(storyId, mockCheckpoint);
      const checkpoints = service.getCheckpoints(storyId);

      expect(checkpoints.length).toBe(1);
      expect(checkpoints[0].name).toBe('Chapter 1 Complete');
    });

    it('should restore checkpoint', () => {
      const story: Story = {
        id: storyId,
        title: 'Original',
        genre: 'Mystery',
        length: 'novel',
        style: 'Classic',
        focusAreas: [],
        createdAt: new Date(),
        lastModified: new Date(),
        currentPhase: 'draft',
        progress: 0,
        storageSize: 1024
      };

      service.saveStory(story);
      mockCheckpoint.storyState = story;
      service.saveCheckpoint(storyId, mockCheckpoint);

      const result = service.restoreCheckpoint(storyId, 'cp-1');
      expect(result).toBe(true);
    });

    it('should return false when restoring non-existent checkpoint', () => {
      const result = service.restoreCheckpoint(storyId, 'non-existent');
      expect(result).toBe(false);
    });
  });

  describe('Backup and Restore', () => {
    it('should backup all data', () => {
      const story: Story = {
        id: 'backup-test',
        title: 'Backup Story',
        genre: 'Fantasy',
        length: 'novella',
        style: 'Epic',
        focusAreas: ['world-building'],
        createdAt: new Date(),
        lastModified: new Date(),
        currentPhase: 'draft',
        progress: 25,
        storageSize: 1500
      };

      service.saveStory(story);
      const backup = service.backupAllData();

      expect(backup).toBeTruthy();
      const parsed = JSON.parse(backup);
      expect(parsed.stories.length).toBe(1);
      expect(parsed.version).toBe('1.0');
    });

    it('should restore from backup', () => {
      const story: Story = {
        id: 'restore-test',
        title: 'Restore Story',
        genre: 'SciFi',
        length: 'novel',
        style: 'Hard SciFi',
        focusAreas: ['technology'],
        createdAt: new Date(),
        lastModified: new Date(),
        currentPhase: 'draft',
        progress: 75,
        storageSize: 3000
      };

      service.saveStory(story);
      const backup = service.backupAllData();

      localStorage.clear();
      const result = service.restoreFromBackup(backup);

      expect(result).toBe(true);
      const stories = service.getAllStories();
      expect(stories.length).toBe(1);
      expect(stories[0].title).toBe('Restore Story');
    });

    it('should return false for invalid backup data', () => {
      const result = service.restoreFromBackup('invalid data');
      expect(result).toBe(false);
    });
  });

  describe('Storage Optimization', () => {
    it('should optimize storage by removing orphaned data', () => {
      const story: Story = {
        id: 'optimize-test',
        title: 'Optimize Test',
        genre: 'Horror',
        length: 'short_story',
        style: 'Gothic',
        focusAreas: ['atmosphere'],
        createdAt: new Date(),
        lastModified: new Date(),
        currentPhase: 'draft',
        progress: 0,
        storageSize: 800
      };

      service.saveStory(story);

      // Manually add orphaned data
      localStorage.setItem('writer_assistant_story_orphaned_data', 'test');

      service.optimizeStorage();

      // Orphaned data should be removed
      const orphanedData = localStorage.getItem('writer_assistant_story_orphaned_data');
      expect(orphanedData).toBeNull();
    });

    it('should clear all data', () => {
      const story: Story = {
        id: 'clear-test',
        title: 'Clear Test',
        genre: 'Romance',
        length: 'novella',
        style: 'Contemporary',
        focusAreas: ['relationships'],
        createdAt: new Date(),
        lastModified: new Date(),
        currentPhase: 'draft',
        progress: 0,
        storageSize: 1200
      };

      service.saveStory(story);
      service.clearAllData();

      const stories = service.getAllStories();
      expect(stories.length).toBe(0);
    });
  });

  describe('Storage Info Observable', () => {
    it('should provide storage info observable', (done) => {
      service.getStorageInfo$().subscribe(info => {
        expect(info).toBeTruthy();
        expect(info.storiesCount).toBeGreaterThanOrEqual(0);
        done();
      });
    });
  });
});
