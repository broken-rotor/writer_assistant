import { Injectable, inject } from '@angular/core';
import { BehaviorSubject, Observable, of, throwError } from 'rxjs';
import { Story, StoryListItem, Character, Rater, Chapter } from '../models/story.model';
import { LocalStorageService } from './local-storage.service';

@Injectable({
  providedIn: 'root'
})
export class StoryService {
  private currentStorySubject = new BehaviorSubject<Story | null>(null);
  public currentStory$ = this.currentStorySubject.asObservable();

  private localStorageService = inject(LocalStorageService);

  constructor() {
    // Subscribe to story list changes
    this.localStorageService.getStoryList().subscribe(list => {
      // Handle list updates if needed
    });
  }

  // Story CRUD Operations
  createStory(title: string): Story {
    const newStory: Story = {
      id: this.generateId(),
      general: {
        title: title,
        systemPrompts: {
          mainPrefix: '',
          mainSuffix: '',
          assistantPrompt: 'You are a creative writing assistant helping to generate engaging story chapters based on plot points and character feedback.',
          editorPrompt: 'You are an experienced editor reviewing story chapters for consistency, quality, and narrative flow.'
        },
        worldbuilding: ''
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
        version: '1.0',
        created: new Date(),
        lastModified: new Date()
      }
    };

    this.localStorageService.saveStory(newStory);
    this.localStorageService.setActiveStory(newStory.id);
    this.currentStorySubject.next(newStory);

    return newStory;
  }

  getStory(storyId: string): Story | null {
    const story = this.localStorageService.loadStory(storyId);
    if (story) {
      this.currentStorySubject.next(story);
      this.localStorageService.setActiveStory(storyId);
    }
    return story;
  }

  saveStory(story: Story): boolean {
    const success = this.localStorageService.saveStory(story);
    if (success) {
      // Update current story if it's the one being saved
      const current = this.currentStorySubject.value;
      if (current && current.id === story.id) {
        this.currentStorySubject.next(story);
      }
    }
    return success;
  }

  deleteStory(storyId: string): boolean {
    const success = this.localStorageService.deleteStory(storyId);
    if (success) {
      const current = this.currentStorySubject.value;
      if (current && current.id === storyId) {
        this.currentStorySubject.next(null);
      }
    }
    return success;
  }

  getStoryList(): Observable<StoryListItem[]> {
    return this.localStorageService.getStoryList();
  }

  getCurrentStory(): Story | null {
    return this.currentStorySubject.value;
  }

  setCurrentStory(story: Story | null): void {
    this.currentStorySubject.next(story);
    if (story) {
      this.localStorageService.setActiveStory(story.id);
    }
  }

  // Character Management
  addCharacter(storyId: string, character: Character): boolean {
    const story = this.localStorageService.loadStory(storyId);
    if (!story) return false;

    story.characters.set(character.id, character);
    return this.saveStory(story);
  }

  updateCharacter(storyId: string, characterId: string, updates: Partial<Character>): boolean {
    const story = this.localStorageService.loadStory(storyId);
    if (!story) return false;

    const character = story.characters.get(characterId);
    if (!character) return false;

    const updatedCharacter = { ...character, ...updates };
    updatedCharacter.metadata.lastModified = new Date();

    story.characters.set(characterId, updatedCharacter);
    return this.saveStory(story);
  }

  deleteCharacter(storyId: string, characterId: string): boolean {
    const story = this.localStorageService.loadStory(storyId);
    if (!story) return false;

    story.characters.delete(characterId);
    return this.saveStory(story);
  }

  hideCharacter(storyId: string, characterId: string, hidden: boolean): boolean {
    return this.updateCharacter(storyId, characterId, { isHidden: hidden });
  }

  // Rater Management
  addRater(storyId: string, rater: Rater): boolean {
    const story = this.localStorageService.loadStory(storyId);
    if (!story) return false;

    story.raters.set(rater.id, rater);
    return this.saveStory(story);
  }

  updateRater(storyId: string, raterId: string, updates: Partial<Rater>): boolean {
    const story = this.localStorageService.loadStory(storyId);
    if (!story) return false;

    const rater = story.raters.get(raterId);
    if (!rater) return false;

    const updatedRater = { ...rater, ...updates };
    updatedRater.metadata.lastModified = new Date();

    story.raters.set(raterId, updatedRater);
    return this.saveStory(story);
  }

  deleteRater(storyId: string, raterId: string): boolean {
    const story = this.localStorageService.loadStory(storyId);
    if (!story) return false;

    story.raters.delete(raterId);
    return this.saveStory(story);
  }

  toggleRater(storyId: string, raterId: string): boolean {
    const story = this.localStorageService.loadStory(storyId);
    if (!story) return false;

    const rater = story.raters.get(raterId);
    if (!rater) return false;

    rater.enabled = !rater.enabled;
    story.raters.set(raterId, rater);
    return this.saveStory(story);
  }

  // Chapter Management
  addChapter(storyId: string, chapter: Chapter): boolean {
    const story = this.localStorageService.loadStory(storyId);
    if (!story) return false;

    story.story.chapters.push(chapter);
    return this.saveStory(story);
  }

  updateChapter(storyId: string, chapterId: string, updates: Partial<Chapter>): boolean {
    const story = this.localStorageService.loadStory(storyId);
    if (!story) return false;

    const chapterIndex = story.story.chapters.findIndex(c => c.id === chapterId);
    if (chapterIndex === -1) return false;

    const updatedChapter = {
      ...story.story.chapters[chapterIndex],
      ...updates
    };
    updatedChapter.metadata.lastModified = new Date();

    story.story.chapters[chapterIndex] = updatedChapter;
    return this.saveStory(story);
  }

  deleteChapter(storyId: string, chapterId: string): boolean {
    const story = this.localStorageService.loadStory(storyId);
    if (!story) return false;

    story.story.chapters = story.story.chapters.filter(c => c.id !== chapterId);

    // Renumber remaining chapters
    story.story.chapters.forEach((chapter, index) => {
      chapter.number = index + 1;
    });

    return this.saveStory(story);
  }

  moveChapter(storyId: string, fromIndex: number, toIndex: number): boolean {
    const story = this.localStorageService.loadStory(storyId);
    if (!story) return false;

    const chapters = story.story.chapters;
    if (fromIndex < 0 || fromIndex >= chapters.length || toIndex < 0 || toIndex >= chapters.length) {
      return false;
    }

    const [chapter] = chapters.splice(fromIndex, 1);
    chapters.splice(toIndex, 0, chapter);

    // Renumber chapters
    chapters.forEach((ch, index) => {
      ch.number = index + 1;
    });

    return this.saveStory(story);
  }

  // Story Summary Management
  updateStorySummary(storyId: string, summary: string): boolean {
    const story = this.localStorageService.loadStory(storyId);
    if (!story) return false;

    story.story.summary = summary;
    return this.saveStory(story);
  }

  // Chapter Creation State Management
  updateChapterCreationState(storyId: string, updates: Partial<Story['chapterCreation']>): boolean {
    const story = this.localStorageService.loadStory(storyId);
    if (!story) return false;

    story.chapterCreation = {
      ...story.chapterCreation,
      ...updates
    };

    return this.saveStory(story);
  }

  resetChapterCreationState(storyId: string): boolean {
    return this.updateChapterCreationState(storyId, {
      plotPoint: '',
      incorporatedFeedback: [],
      feedbackRequests: new Map(),
      generatedChapter: undefined,
      editorReview: undefined
    });
  }

  // General Configuration Updates
  updateGeneralConfig(storyId: string, updates: Partial<Story['general']>): boolean {
    const story = this.localStorageService.loadStory(storyId);
    if (!story) return false;

    story.general = {
      ...story.general,
      ...updates
    };

    return this.saveStory(story);
  }

  updateSystemPrompts(storyId: string, updates: Partial<Story['general']['systemPrompts']>): boolean {
    const story = this.localStorageService.loadStory(storyId);
    if (!story) return false;

    story.general.systemPrompts = {
      ...story.general.systemPrompts,
      ...updates
    };

    return this.saveStory(story);
  }

  // Export/Import
  exportStory(storyId: string): Blob | null {
    return this.localStorageService.exportStory(storyId);
  }

  exportAllStories(): Blob {
    return this.localStorageService.exportAllStories();
  }

  async importStory(file: File): Promise<{ success: boolean; storyId?: string; error?: string }> {
    const result = await this.localStorageService.importStory(file);
    if (result.success && result.storyId) {
      const story = this.localStorageService.loadStory(result.storyId);
      if (story) {
        this.currentStorySubject.next(story);
      }
    }
    return result;
  }

  // Storage Management
  getStorageQuota(): Observable<any> {
    return this.localStorageService.getStorageQuota();
  }

  getStorageStats() {
    return this.localStorageService.getStorageStats();
  }

  cleanupOldStories(maxAgeInDays = 30): number {
    return this.localStorageService.cleanupOldStories(maxAgeInDays);
  }

  clearAllData(): boolean {
    this.currentStorySubject.next(null);
    return this.localStorageService.clearAllData();
  }

  // Utility Methods
  private generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  // Auto-save functionality
  private autoSaveInterval: any = null;

  startAutoSave(intervalMs = 30000): void {
    if (this.autoSaveInterval) {
      clearInterval(this.autoSaveInterval);
    }

    this.autoSaveInterval = setInterval(() => {
      const story = this.currentStorySubject.value;
      if (story) {
        this.localStorageService.saveStory(story);
      }
    }, intervalMs);
  }

  stopAutoSave(): void {
    if (this.autoSaveInterval) {
      clearInterval(this.autoSaveInterval);
      this.autoSaveInterval = null;
    }
  }

  /**
   * Save a chapter to the story
   */
  saveChapter(storyId: string, chapterNumber: number, chapterData: any): Observable<any> {
    const story = this.localStorageService.loadStory(storyId);
    if (!story) {
      return throwError(() => new Error('Story not found'));
    }

    try {
      // Ensure chapters array exists
      if (!story.story.chapters) {
        story.story.chapters = [];
      }

      // Find existing chapter or create new one
      const existingIndex = story.story.chapters.findIndex((ch: any) => ch.number === chapterNumber);
      
      const chapter = {
        id: chapterData.id || this.generateId(),
        number: chapterNumber,
        title: chapterData.title || `Chapter ${chapterNumber}`,
        content: chapterData.content || '',
        plotPoint: chapterData.plotPoint || '',
        incorporatedFeedback: chapterData.incorporatedFeedback || [],
        metadata: {
          created: chapterData.metadata?.created || new Date(),
          lastModified: new Date(),
          wordCount: chapterData.wordCount || 0
        }
      };

      if (existingIndex !== -1) {
        // Update existing chapter
        story.story.chapters[existingIndex] = chapter;
      } else {
        // Add new chapter
        story.story.chapters.push(chapter);
        // Sort chapters by number
        story.story.chapters.sort((a: any, b: any) => a.number - b.number);
      }

      // Update story metadata
      story.metadata.lastModified = new Date();

      // Save story
      const success = this.localStorageService.saveStory(story);
      if (success) {
        // Update current story if it's the same one
        if (this.currentStorySubject.value?.id === storyId) {
          this.currentStorySubject.next(story);
        }
        return of(chapter);
      } else {
        return throwError(() => new Error('Failed to save story'));
      }
    } catch (error) {
      return throwError(() => error);
    }
  }

  // ============================================================================
  // PLOT OUTLINE MIGRATION LOGIC (WRI-65)
  // ============================================================================

  /**
   * Migrate story to include plot outline structure if missing
   */
  migrateStoryForPlotOutline(story: Story): void {
    if (!story.plotOutline) {
      story.plotOutline = {
        content: '',
        status: 'draft',
        chatHistory: [],
        raterFeedback: new Map(),
        metadata: {
          created: new Date(),
          lastModified: new Date(),
          version: 1
        }
      };
      
      // If story has existing chapters, suggest creating outline
      if (story.story.chapters.length > 0) {
        story.plotOutline.content = `// TODO: Create plot outline based on existing ${story.story.chapters.length} chapters
// Consider the following chapter titles:
${story.story.chapters.map(c => `// - Chapter ${c.number}: ${c.title}`).join('\n')}`;
      }
      
      this.saveStory(story);
    }
  }

}
