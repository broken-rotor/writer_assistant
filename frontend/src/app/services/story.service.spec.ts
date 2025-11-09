import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { StoryService } from './story.service';
import { LocalStorageService } from './local-storage.service';
import { Story, Character, Rater } from '../models/story.model';

describe('StoryService', () => {
  let service: StoryService;
  let localStorageService: jasmine.SpyObj<LocalStorageService>;

  beforeEach(() => {
    const localStorageSpy = jasmine.createSpyObj('LocalStorageService', [
      'saveStory',
      'loadStory',
      'deleteStory',
      'setActiveStory',
      'getActiveStoryId',
      'getStoryList',
      'exportStory',
      'exportAllStories',
      'importStory',
      'getStorageQuota',
      'getStorageStats',
      'cleanupOldStories',
      'clearAllData'
    ]);

    // Mock getStoryList to return an observable
    localStorageSpy.getStoryList.and.returnValue(of([]));

    TestBed.configureTestingModule({
      providers: [
        StoryService,
        { provide: LocalStorageService, useValue: localStorageSpy }
      ]
    });

    service = TestBed.inject(StoryService);
    localStorageService = TestBed.inject(LocalStorageService) as jasmine.SpyObj<LocalStorageService>;
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('createStory', () => {
    it('should create a new story with default values', () => {
      localStorageService.saveStory.and.returnValue(true);
      localStorageService.setActiveStory.and.returnValue();

      const story = service.createStory('Test Story');

      expect(story).toBeTruthy();
      expect(story.general.title).toBe('Test Story');
      expect(story.characters.size).toBe(0);
      expect(story.raters.size).toBe(0);
      expect(story.story.chapters.length).toBe(0);
      expect(localStorageService.saveStory).toHaveBeenCalledWith(story);
      expect(localStorageService.setActiveStory).toHaveBeenCalledWith(story.id);
    });
  });

  describe('getStory', () => {
    it('should load and set current story', () => {
      const mockStory = createMockStory('test-id', 'Test Story');
      localStorageService.loadStory.and.returnValue(mockStory);

      const story = service.getStory('test-id');

      expect(story).toBe(mockStory);
      expect(localStorageService.loadStory).toHaveBeenCalledWith('test-id');
      expect(localStorageService.setActiveStory).toHaveBeenCalledWith('test-id');
    });

    it('should return null for non-existent story', () => {
      localStorageService.loadStory.and.returnValue(null);

      const story = service.getStory('non-existent');

      expect(story).toBeNull();
    });
  });

  describe('saveStory', () => {
    it('should save story and update current story', () => {
      const mockStory = createMockStory('test-id', 'Test Story');
      localStorageService.saveStory.and.returnValue(true);
      service.setCurrentStory(mockStory);

      const result = service.saveStory(mockStory);

      expect(result).toBe(true);
      expect(localStorageService.saveStory).toHaveBeenCalledWith(mockStory);
    });
  });

  describe('deleteStory', () => {
    it('should delete story and clear current if it matches', () => {
      const mockStory = createMockStory('test-id', 'Test Story');
      localStorageService.deleteStory.and.returnValue(true);
      service.setCurrentStory(mockStory);

      const result = service.deleteStory('test-id');

      expect(result).toBe(true);
      expect(service.getCurrentStory()).toBeNull();
    });
  });

  describe('addCharacter', () => {
    it('should add a character to story', () => {
      const mockStory = createMockStory('story-id', 'Test Story');
      const mockCharacter: Character = {
        id: 'char-1',
        name: 'Test Character',
        basicBio: 'A test character',
        sex: 'Female',
        gender: 'Female',
        sexualPreference: 'Heterosexual',
        age: 25,
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
      };

      localStorageService.loadStory.and.returnValue(mockStory);
      localStorageService.saveStory.and.returnValue(true);

      const result = service.addCharacter('story-id', mockCharacter);

      expect(result).toBe(true);
      expect(mockStory.characters.get('char-1')).toBe(mockCharacter);
    });
  });

  describe('updateCharacter', () => {
    it('should update character properties', () => {
      const mockStory = createMockStory('story-id', 'Test Story');
      const mockCharacter: Character = {
        id: 'char-1',
        name: 'Test Character',
        basicBio: 'A test character',
        sex: 'Female',
        gender: 'Female',
        sexualPreference: 'Heterosexual',
        age: 25,
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
      };
      mockStory.characters.set('char-1', mockCharacter);

      localStorageService.loadStory.and.returnValue(mockStory);
      localStorageService.saveStory.and.returnValue(true);

      const result = service.updateCharacter('story-id', 'char-1', { name: 'Updated Name' });

      expect(result).toBe(true);
      expect(mockStory.characters.get('char-1')?.name).toBe('Updated Name');
    });
  });

  describe('hideCharacter', () => {
    it('should set character isHidden to true', () => {
      const mockStory = createMockStory('story-id', 'Test Story');
      const mockCharacter: Character = {
        id: 'char-1',
        name: 'Test Character',
        basicBio: 'A test character',
        sex: 'Female',
        gender: 'Female',
        sexualPreference: 'Heterosexual',
        age: 25,
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
      };
      mockStory.characters.set('char-1', mockCharacter);

      localStorageService.loadStory.and.returnValue(mockStory);
      localStorageService.saveStory.and.returnValue(true);

      const result = service.hideCharacter('story-id', 'char-1', true);

      expect(result).toBe(true);
    });
  });

  describe('addRater', () => {
    it('should add a rater to story', () => {
      const mockStory = createMockStory('story-id', 'Test Story');
      const mockRater: Rater = {
        id: 'rater-1',
        name: 'Test Rater',
        systemPrompt: 'Test prompt',
        enabled: true,
        metadata: {
          created: new Date(),
          lastModified: new Date()
        }
      };

      localStorageService.loadStory.and.returnValue(mockStory);
      localStorageService.saveStory.and.returnValue(true);

      const result = service.addRater('story-id', mockRater);

      expect(result).toBe(true);
      expect(mockStory.raters.get('rater-1')).toBe(mockRater);
    });
  });

  describe('toggleRater', () => {
    it('should toggle rater enabled state', () => {
      const mockStory = createMockStory('story-id', 'Test Story');
      const mockRater: Rater = {
        id: 'rater-1',
        name: 'Test Rater',
        systemPrompt: 'Test prompt',
        enabled: true,
        metadata: {
          created: new Date(),
          lastModified: new Date()
        }
      };
      mockStory.raters.set('rater-1', mockRater);

      localStorageService.loadStory.and.returnValue(mockStory);
      localStorageService.saveStory.and.returnValue(true);

      const result = service.toggleRater('story-id', 'rater-1');

      expect(result).toBe(true);
      expect(mockStory.raters.get('rater-1')?.enabled).toBe(false);
    });
  });

  describe('addChapter', () => {
    it('should add a chapter to story', () => {
      const mockStory = createMockStory('story-id', 'Test Story');
      const mockChapter = {
        id: 'chapter-1',
        number: 1,
        title: 'Chapter 1',
        content: 'Chapter content',
        plotPoint: 'A plot point',
        incorporatedFeedback: [],
        metadata: {
          created: new Date(),
          lastModified: new Date(),
          wordCount: 2
        }
      };

      localStorageService.loadStory.and.returnValue(mockStory);
      localStorageService.saveStory.and.returnValue(true);

      const result = service.addChapter('story-id', mockChapter);

      expect(result).toBe(true);
      expect(mockStory.story.chapters.length).toBe(1);
    });
  });

  describe('deleteChapter', () => {
    it('should delete chapter and renumber remaining chapters', () => {
      const mockStory = createMockStory('story-id', 'Test Story');
      mockStory.story.chapters = [
        {
          id: 'chapter-1',
          number: 1,
          title: 'Chapter 1',
          content: 'Content 1',
          plotPoint: 'Plot 1',
          incorporatedFeedback: [],
          metadata: {
            created: new Date(),
            lastModified: new Date(),
            wordCount: 2
          }
        },
        {
          id: 'chapter-2',
          number: 2,
          title: 'Chapter 2',
          content: 'Content 2',
          plotPoint: 'Plot 2',
          incorporatedFeedback: [],
          metadata: {
            created: new Date(),
            lastModified: new Date(),
            wordCount: 2
          }
        }
      ];

      localStorageService.loadStory.and.returnValue(mockStory);
      localStorageService.saveStory.and.returnValue(true);

      const result = service.deleteChapter('story-id', 'chapter-1');

      expect(result).toBe(true);
      expect(mockStory.story.chapters.length).toBe(1);
      expect(mockStory.story.chapters[0].number).toBe(1);
      expect(mockStory.story.chapters[0].id).toBe('chapter-2');
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
    metadata: {
      version: '1.0',
      created: new Date(),
      lastModified: new Date()
    }
  };
}
