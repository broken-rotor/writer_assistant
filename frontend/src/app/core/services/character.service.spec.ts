import { TestBed } from '@angular/core/testing';
import { CharacterService } from './character.service';
import { LocalStorageService } from './local-storage.service';
import { Character, Story, AIExpansionRecord } from '../../shared/models';

describe('CharacterService', () => {
  let service: CharacterService;
  let localStorageService: jasmine.SpyObj<LocalStorageService>;

  const mockStory: Story = {
    id: 'test-story-1',
    title: 'Test Story',
    genre: 'Mystery',
    length: 'novel',
    style: 'literary',
    focusAreas: ['character', 'plot'],
    createdAt: new Date(),
    lastModified: new Date(),
    currentPhase: 'character_dialog',
    currentDraft: {
      title: 'Test Story',
      outline: [],
      characters: [
        {
          id: 'char-1',
          name: 'Alice',
          role: 'protagonist',
          personality: {
            coreTraits: ['brave', 'curious'],
            emotionalPatterns: ['optimistic'],
            speechPatterns: ['direct'],
            motivations: ['justice']
          },
          background: 'A detective',
          currentState: {
            emotionalState: 'determined',
            activeGoals: [],
            currentKnowledge: [],
            relationships: {}
          },
          memorySize: 0,
          isHidden: false,
          creationSource: 'user_defined',
          aiExpansionHistory: []
        },
        {
          id: 'char-2',
          name: 'Bob',
          role: 'antagonist',
          personality: {
            coreTraits: ['cunning', 'ruthless'],
            emotionalPatterns: ['cold'],
            speechPatterns: ['formal'],
            motivations: ['power']
          },
          background: 'A criminal mastermind',
          currentState: {
            emotionalState: 'calculating',
            activeGoals: [],
            currentKnowledge: [],
            relationships: {}
          },
          memorySize: 0,
          isHidden: true,
          creationSource: 'user_defined',
          aiExpansionHistory: []
        }
      ],
      themes: ['justice'],
      metadata: {
        timestamp: new Date(),
        requestId: 'test-req',
        processingTime: 100,
        model: 'test-model'
      }
    }
  };

  beforeEach(() => {
    const localStorageSpy = jasmine.createSpyObj('LocalStorageService', [
      'getStory',
      'saveStory'
    ]);

    TestBed.configureTestingModule({
      providers: [
        CharacterService,
        { provide: LocalStorageService, useValue: localStorageSpy }
      ]
    });

    service = TestBed.inject(CharacterService);
    localStorageService = TestBed.inject(LocalStorageService) as jasmine.SpyObj<LocalStorageService>;

    // Reset mock story to original state before each test to prevent mutation
    mockStory.currentDraft!.characters = [
      {
        id: 'char-1',
        name: 'Alice',
        role: 'protagonist',
        personality: {
          coreTraits: ['brave', 'curious'],
          emotionalPatterns: ['optimistic'],
          speechPatterns: ['direct'],
          motivations: ['justice']
        },
        background: 'A detective',
        currentState: {
          emotionalState: 'determined',
          activeGoals: [],
          currentKnowledge: [],
          relationships: {}
        },
        memorySize: 0,
        isHidden: false,
        creationSource: 'user_defined',
        aiExpansionHistory: []
      },
      {
        id: 'char-2',
        name: 'Bob',
        role: 'antagonist',
        personality: {
          coreTraits: ['cunning', 'ruthless'],
          emotionalPatterns: ['cold'],
          speechPatterns: ['formal'],
          motivations: ['power']
        },
        background: 'A criminal mastermind',
        currentState: {
          emotionalState: 'calculating',
          activeGoals: [],
          currentKnowledge: [],
          relationships: {}
        },
        memorySize: 0,
        isHidden: true,
        creationSource: 'user_defined',
        aiExpansionHistory: []
      }
    ];
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('getActiveCharacters', () => {
    it('should return only non-hidden characters', () => {
      localStorageService.getStory.and.returnValue(mockStory);

      const activeCharacters = service.getActiveCharacters('test-story-1');

      expect(activeCharacters.length).toBe(1);
      expect(activeCharacters[0].name).toBe('Alice');
      expect(activeCharacters[0].isHidden).toBe(false);
    });

    it('should return empty array when story has no characters', () => {
      const storyWithoutChars = { ...mockStory, currentDraft: null };
      localStorageService.getStory.and.returnValue(storyWithoutChars);

      const activeCharacters = service.getActiveCharacters('test-story-1');

      expect(activeCharacters).toEqual([]);
    });

    it('should return empty array when story not found', () => {
      localStorageService.getStory.and.returnValue(null);

      const activeCharacters = service.getActiveCharacters('nonexistent');

      expect(activeCharacters).toEqual([]);
    });
  });

  describe('getHiddenCharacters', () => {
    it('should return only hidden characters', () => {
      localStorageService.getStory.and.returnValue(mockStory);

      const hiddenCharacters = service.getHiddenCharacters('test-story-1');

      expect(hiddenCharacters.length).toBe(1);
      expect(hiddenCharacters[0].name).toBe('Bob');
      expect(hiddenCharacters[0].isHidden).toBe(true);
    });

    it('should return empty array when no hidden characters exist', () => {
      const storyWithoutHidden = {
        ...mockStory,
        currentDraft: {
          ...mockStory.currentDraft!,
          characters: mockStory.currentDraft!.characters.filter(c => !c.isHidden)
        }
      };
      localStorageService.getStory.and.returnValue(storyWithoutHidden);

      const hiddenCharacters = service.getHiddenCharacters('test-story-1');

      expect(hiddenCharacters).toEqual([]);
    });
  });

  describe('hideCharacter', () => {
    it('should hide an active character', () => {
      localStorageService.getStory.and.returnValue(mockStory);

      const result = service.hideCharacter('test-story-1', 'char-1');

      expect(result).toBe(true);
      expect(localStorageService.saveStory).toHaveBeenCalled();
      const savedStory = localStorageService.saveStory.calls.mostRecent().args[0];
      const hiddenChar = savedStory.currentDraft!.characters.find((c: Character) => c.id === 'char-1');
      expect(hiddenChar!.isHidden).toBe(true);
    });

    it('should return false when character not found', () => {
      localStorageService.getStory.and.returnValue(mockStory);

      const result = service.hideCharacter('test-story-1', 'nonexistent');

      expect(result).toBe(false);
      expect(localStorageService.saveStory).not.toHaveBeenCalled();
    });

    it('should return false when story not found', () => {
      localStorageService.getStory.and.returnValue(null);

      const result = service.hideCharacter('nonexistent', 'char-1');

      expect(result).toBe(false);
      expect(localStorageService.saveStory).not.toHaveBeenCalled();
    });
  });

  describe('unhideCharacter', () => {
    it('should unhide a hidden character', () => {
      localStorageService.getStory.and.returnValue(mockStory);

      const result = service.unhideCharacter('test-story-1', 'char-2');

      expect(result).toBe(true);
      expect(localStorageService.saveStory).toHaveBeenCalled();
      const savedStory = localStorageService.saveStory.calls.mostRecent().args[0];
      const unhiddenChar = savedStory.currentDraft!.characters.find((c: Character) => c.id === 'char-2');
      expect(unhiddenChar!.isHidden).toBe(false);
    });

    it('should return false when character not found', () => {
      localStorageService.getStory.and.returnValue(mockStory);

      const result = service.unhideCharacter('test-story-1', 'nonexistent');

      expect(result).toBe(false);
      expect(localStorageService.saveStory).not.toHaveBeenCalled();
    });
  });

  describe('addCharacter', () => {
    it('should add a new character to the story', () => {
      localStorageService.getStory.and.returnValue(mockStory);

      const newCharData: Partial<Character> = {
        name: 'Charlie',
        role: 'supporting',
        background: 'A helpful friend'
      };

      const result = service.addCharacter('test-story-1', newCharData);

      expect(result).toBeTruthy();
      expect(result!.name).toBe('Charlie');
      expect(result!.isHidden).toBe(false);
      expect(result!.creationSource).toBe('user_defined');
      expect(result!.aiExpansionHistory).toEqual([]);
      expect(localStorageService.saveStory).toHaveBeenCalled();
    });

    it('should initialize currentDraft if not present', () => {
      const storyWithoutDraft = { ...mockStory, currentDraft: null };
      localStorageService.getStory.and.returnValue(storyWithoutDraft);

      const newCharData: Partial<Character> = {
        name: 'Charlie',
        role: 'supporting'
      };

      const result = service.addCharacter('test-story-1', newCharData);

      expect(result).toBeTruthy();
      expect(localStorageService.saveStory).toHaveBeenCalled();
      const savedStory = localStorageService.saveStory.calls.mostRecent().args[0];
      expect(savedStory.currentDraft).toBeTruthy();
      expect(savedStory.currentDraft!.characters.length).toBe(1);
    });

    it('should return null when story not found', () => {
      localStorageService.getStory.and.returnValue(null);

      const result = service.addCharacter('nonexistent', { name: 'Charlie' });

      expect(result).toBeNull();
      expect(localStorageService.saveStory).not.toHaveBeenCalled();
    });
  });

  describe('updateCharacter', () => {
    it('should update an existing character', () => {
      localStorageService.getStory.and.returnValue(mockStory);

      const updates: Partial<Character> = {
        background: 'Updated background'
      };

      const result = service.updateCharacter('test-story-1', 'char-1', updates);

      expect(result).toBe(true);
      expect(localStorageService.saveStory).toHaveBeenCalled();
      const savedStory = localStorageService.saveStory.calls.mostRecent().args[0];
      const updatedChar = savedStory.currentDraft!.characters.find((c: Character) => c.id === 'char-1');
      expect(updatedChar!.background).toBe('Updated background');
    });

    it('should return false when character not found', () => {
      localStorageService.getStory.and.returnValue(mockStory);

      const result = service.updateCharacter('test-story-1', 'nonexistent', { background: 'Test' });

      expect(result).toBe(false);
      expect(localStorageService.saveStory).not.toHaveBeenCalled();
    });
  });

  describe('addExpansionRecord', () => {
    it('should add an AI expansion record to a character', () => {
      localStorageService.getStory.and.returnValue(mockStory);

      const expansionRecord: AIExpansionRecord = {
        date: new Date(),
        expansionType: 'personality_details',
        userPrompt: 'Expand personality',
        aiGeneratedContent: {
          section: 'personality',
          addedDetails: 'More details...'
        }
      };

      const result = service.addExpansionRecord('test-story-1', 'char-1', expansionRecord);

      expect(result).toBe(true);
      expect(localStorageService.saveStory).toHaveBeenCalled();
      const savedStory = localStorageService.saveStory.calls.mostRecent().args[0];
      const updatedChar = savedStory.currentDraft!.characters.find((c: Character) => c.id === 'char-1');
      expect(updatedChar!.aiExpansionHistory.length).toBe(1);
      expect(updatedChar!.aiExpansionHistory[0].userPrompt).toBe('Expand personality');
    });

    it('should return false when character not found', () => {
      localStorageService.getStory.and.returnValue(mockStory);

      const expansionRecord: AIExpansionRecord = {
        date: new Date(),
        expansionType: 'personality_details',
        userPrompt: 'Test',
        aiGeneratedContent: { section: 'test', addedDetails: 'test' }
      };

      const result = service.addExpansionRecord('test-story-1', 'nonexistent', expansionRecord);

      expect(result).toBe(false);
      expect(localStorageService.saveStory).not.toHaveBeenCalled();
    });
  });

  describe('getCharacter', () => {
    it('should return a specific character by ID', () => {
      localStorageService.getStory.and.returnValue(mockStory);

      const character = service.getCharacter('test-story-1', 'char-1');

      expect(character).toBeTruthy();
      expect(character!.name).toBe('Alice');
    });

    it('should return null when character not found', () => {
      localStorageService.getStory.and.returnValue(mockStory);

      const character = service.getCharacter('test-story-1', 'nonexistent');

      expect(character).toBeNull();
    });

    it('should return null when story not found', () => {
      localStorageService.getStory.and.returnValue(null);

      const character = service.getCharacter('nonexistent', 'char-1');

      expect(character).toBeNull();
    });
  });

  describe('isCharacterHidden', () => {
    it('should return true for hidden character', () => {
      localStorageService.getStory.and.returnValue(mockStory);

      const isHidden = service.isCharacterHidden('test-story-1', 'char-2');

      expect(isHidden).toBe(true);
    });

    it('should return false for active character', () => {
      localStorageService.getStory.and.returnValue(mockStory);

      const isHidden = service.isCharacterHidden('test-story-1', 'char-1');

      expect(isHidden).toBe(false);
    });

    it('should return false when character not found', () => {
      localStorageService.getStory.and.returnValue(mockStory);

      const isHidden = service.isCharacterHidden('test-story-1', 'nonexistent');

      expect(isHidden).toBe(false);
    });
  });

  describe('getActiveCharacterCount', () => {
    it('should return count of active characters', () => {
      localStorageService.getStory.and.returnValue(mockStory);

      const count = service.getActiveCharacterCount('test-story-1');

      expect(count).toBe(1);
    });
  });

  describe('getHiddenCharacterCount', () => {
    it('should return count of hidden characters', () => {
      localStorageService.getStory.and.returnValue(mockStory);

      const count = service.getHiddenCharacterCount('test-story-1');

      expect(count).toBe(1);
    });
  });
});
