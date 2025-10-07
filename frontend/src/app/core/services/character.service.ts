import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { Character, AIExpansionRecord } from '../../shared/models';
import { LocalStorageService } from './local-storage.service';

@Injectable({
  providedIn: 'root'
})
export class CharacterService {
  private charactersSubject = new BehaviorSubject<Character[]>([]);
  public characters$ = this.charactersSubject.asObservable();

  constructor(private localStorageService: LocalStorageService) {}

  /**
   * Get all active (non-hidden) characters for a story
   */
  getActiveCharacters(storyId: string): Character[] {
    const story = this.localStorageService.getStory(storyId);
    if (!story?.currentDraft?.characters) {
      return [];
    }
    return story.currentDraft.characters.filter(c => !c.isHidden);
  }

  /**
   * Get all hidden characters for a story
   */
  getHiddenCharacters(storyId: string): Character[] {
    const story = this.localStorageService.getStory(storyId);
    if (!story?.currentDraft?.characters) {
      return [];
    }
    return story.currentDraft.characters.filter(c => c.isHidden);
  }

  /**
   * Get all characters (both active and hidden) for a story
   */
  getAllCharacters(storyId: string): Character[] {
    const story = this.localStorageService.getStory(storyId);
    return story?.currentDraft?.characters || [];
  }

  /**
   * Hide a character (soft delete)
   */
  hideCharacter(storyId: string, characterId: string): boolean {
    const story = this.localStorageService.getStory(storyId);
    if (!story?.currentDraft?.characters) {
      return false;
    }

    const character = story.currentDraft.characters.find(c => c.id === characterId);
    if (!character) {
      return false;
    }

    character.isHidden = true;
    story.lastModified = new Date();
    this.localStorageService.saveStory(story);
    this.charactersSubject.next(story.currentDraft.characters);
    return true;
  }

  /**
   * Unhide a character (restore)
   */
  unhideCharacter(storyId: string, characterId: string): boolean {
    const story = this.localStorageService.getStory(storyId);
    if (!story?.currentDraft?.characters) {
      return false;
    }

    const character = story.currentDraft.characters.find(c => c.id === characterId);
    if (!character) {
      return false;
    }

    character.isHidden = false;
    story.lastModified = new Date();
    this.localStorageService.saveStory(story);
    this.charactersSubject.next(story.currentDraft.characters);
    return true;
  }

  /**
   * Add a new character to a story
   */
  addCharacter(storyId: string, character: Partial<Character>): Character | null {
    const story = this.localStorageService.getStory(storyId);
    if (!story) {
      return null;
    }

    if (!story.currentDraft) {
      story.currentDraft = {
        title: story.title,
        outline: [],
        characters: [],
        themes: [],
        metadata: {
          timestamp: new Date(),
          requestId: '',
          processingTime: 0,
          model: ''
        }
      };
    }

    if (!story.currentDraft.characters) {
      story.currentDraft.characters = [];
    }

    const newCharacter: Character = {
      id: this.generateId(),
      name: character.name || 'Unnamed Character',
      role: character.role || 'supporting',
      personality: character.personality || {
        coreTraits: [],
        emotionalPatterns: [],
        speechPatterns: [],
        motivations: []
      },
      background: character.background || '',
      currentState: character.currentState || {
        emotionalState: 'neutral',
        activeGoals: [],
        currentKnowledge: [],
        relationships: {}
      },
      memorySize: 0,
      isHidden: false,
      creationSource: 'user_defined',
      aiExpansionHistory: []
    };

    story.currentDraft.characters.push(newCharacter);
    story.lastModified = new Date();
    this.localStorageService.saveStory(story);
    this.charactersSubject.next(story.currentDraft.characters);

    return newCharacter;
  }

  /**
   * Update an existing character
   */
  updateCharacter(storyId: string, characterId: string, updates: Partial<Character>): boolean {
    const story = this.localStorageService.getStory(storyId);
    if (!story?.currentDraft?.characters) {
      return false;
    }

    const characterIndex = story.currentDraft.characters.findIndex(c => c.id === characterId);
    if (characterIndex === -1) {
      return false;
    }

    story.currentDraft.characters[characterIndex] = {
      ...story.currentDraft.characters[characterIndex],
      ...updates
    };

    story.lastModified = new Date();
    this.localStorageService.saveStory(story);
    this.charactersSubject.next(story.currentDraft.characters);
    return true;
  }

  /**
   * Add an AI expansion record to a character
   */
  addExpansionRecord(
    storyId: string,
    characterId: string,
    expansionRecord: AIExpansionRecord
  ): boolean {
    const story = this.localStorageService.getStory(storyId);
    if (!story?.currentDraft?.characters) {
      return false;
    }

    const character = story.currentDraft.characters.find(c => c.id === characterId);
    if (!character) {
      return false;
    }

    character.aiExpansionHistory.push(expansionRecord);
    story.lastModified = new Date();
    this.localStorageService.saveStory(story);
    this.charactersSubject.next(story.currentDraft.characters);
    return true;
  }

  /**
   * Get a specific character by ID
   */
  getCharacter(storyId: string, characterId: string): Character | null {
    const story = this.localStorageService.getStory(storyId);
    if (!story?.currentDraft?.characters) {
      return null;
    }
    return story.currentDraft.characters.find(c => c.id === characterId) || null;
  }

  /**
   * Check if a character is hidden
   */
  isCharacterHidden(storyId: string, characterId: string): boolean {
    const character = this.getCharacter(storyId, characterId);
    return character?.isHidden || false;
  }

  /**
   * Get count of active characters
   */
  getActiveCharacterCount(storyId: string): number {
    return this.getActiveCharacters(storyId).length;
  }

  /**
   * Get count of hidden characters
   */
  getHiddenCharacterCount(storyId: string): number {
    return this.getHiddenCharacters(storyId).length;
  }

  private generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }
}
