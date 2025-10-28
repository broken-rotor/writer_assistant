import { TestBed } from '@angular/core/testing';
import { LocalStorageService } from './local-storage.service';
import { Story } from '../models/story.model';

describe('LocalStorageService', () => {
  let service: LocalStorageService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(LocalStorageService);
    // Clear localStorage before each test
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('saveStory', () => {
    it('should save a story to localStorage', () => {
      const story: Story = createMockStory('test-id', 'Test Story');
      const result = service.saveStory(story);

      expect(result).toBe(true);
      const saved = localStorage.getItem('writer_assistant_story_test-id');
      expect(saved).toBeTruthy();
    });

    it('should serialize Maps to arrays', () => {
      const story: Story = createMockStory('test-id', 'Test Story');
      story.characters.set('char1', {
        id: 'char1',
        name: 'Test Character',
        basicBio: 'A test',
        sex: 'Female',
        gender: 'Female',
        sexualPreference: 'Heterosexual',
        age: 30,
        physicalAppearance: 'Tall',
        usualClothing: 'Casual',
        personality: 'Friendly',
        motivations: 'Success',
        fears: 'Failure',
        relationships: 'None',
        isHidden: false,
        metadata: {
          creationSource: 'user',
          lastModified: new Date()
        }
      });

      service.saveStory(story);
      const saved = localStorage.getItem('writer_assistant_story_test-id');
      const parsed = JSON.parse(saved!);

      expect(Array.isArray(parsed.characters)).toBe(true);
      expect(parsed.characters.length).toBe(1);
    });
  });

  describe('loadStory', () => {
    it('should load a story from localStorage', () => {
      const story: Story = createMockStory('test-id', 'Test Story');
      service.saveStory(story);

      const loaded = service.loadStory('test-id');
      expect(loaded).toBeTruthy();
      expect(loaded?.id).toBe('test-id');
      expect(loaded?.general.title).toBe('Test Story');
    });

    it('should deserialize arrays to Maps', () => {
      const story: Story = createMockStory('test-id', 'Test Story');
      story.characters.set('char1', {
        id: 'char1',
        name: 'Test Character',
        basicBio: 'A test',
        sex: 'Female',
        gender: 'Female',
        sexualPreference: 'Heterosexual',
        age: 30,
        physicalAppearance: 'Tall',
        usualClothing: 'Casual',
        personality: 'Friendly',
        motivations: 'Success',
        fears: 'Failure',
        relationships: 'None',
        isHidden: false,
        metadata: {
          creationSource: 'user',
          lastModified: new Date()
        }
      });
      service.saveStory(story);

      const loaded = service.loadStory('test-id');
      expect(loaded?.characters instanceof Map).toBe(true);
      expect(loaded?.characters.size).toBe(1);
      expect(loaded?.characters.get('char1')?.name).toBe('Test Character');
    });

    it('should return null for non-existent story', () => {
      const loaded = service.loadStory('non-existent');
      expect(loaded).toBeNull();
    });
  });

  describe('deleteStory', () => {
    it('should delete a story from localStorage', () => {
      const story: Story = createMockStory('test-id', 'Test Story');
      service.saveStory(story);

      const result = service.deleteStory('test-id');
      expect(result).toBe(true);

      const loaded = service.loadStory('test-id');
      expect(loaded).toBeNull();
    });
  });

  describe('getActiveStoryId', () => {
    it('should return the active story ID', () => {
      service.setActiveStory('test-id');
      expect(service.getActiveStoryId()).toBe('test-id');
    });

    it('should return null when no active story', () => {
      expect(service.getActiveStoryId()).toBeNull();
    });
  });

  describe('getStoryList', () => {
    it('should return an observable of story list', (done) => {
      const story: Story = createMockStory('test-id', 'Test Story');
      service.saveStory(story);

      service.getStoryList().subscribe(list => {
        expect(list.length).toBe(1);
        expect(list[0].id).toBe('test-id');
        expect(list[0].title).toBe('Test Story');
        done();
      });
    });
  });

  describe('exportStory', () => {
    it('should export a story as Blob', () => {
      const story: Story = createMockStory('test-id', 'Test Story');
      service.saveStory(story);

      const blob = service.exportStory('test-id');
      expect(blob).toBeTruthy();
      expect(blob?.type).toBe('application/json');
    });

    it('should return null for non-existent story', () => {
      const blob = service.exportStory('non-existent');
      expect(blob).toBeNull();
    });
  });

  describe('clearAllData', () => {
    it('should clear all writer assistant data', () => {
      const story: Story = createMockStory('test-id', 'Test Story');
      service.saveStory(story);

      const result = service.clearAllData();
      expect(result).toBe(true);

      const loaded = service.loadStory('test-id');
      expect(loaded).toBeNull();
    });
  });
});

function createMockStory(id: string, title: string): Story {
  return {
    id: id,
    general: {
      title: title,
      systemPrompts: {
        mainPrefix: '',
        mainSuffix: '',
        assistantPrompt: 'You are a creative writing assistant.',
        editorPrompt: 'You are an experienced editor.'
      },
      worldbuilding: ''
    },
    characters: new Map(),
    raters: new Map(),
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
    story: {
      summary: '',
      chapters: []
    },
    chapterCreation: {
      plotPoint: '',
      incorporatedFeedback: [],
      feedbackRequests: new Map()
    },
    metadata: {
      version: '1.0',
      created: new Date(),
      lastModified: new Date()
    }
  };
}
