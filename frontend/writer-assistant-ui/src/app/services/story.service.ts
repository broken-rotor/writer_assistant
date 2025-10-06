import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { Story, StoryCreate, StoryUpdate } from '../models/story.model';
import { LocalStorageService, StoryIndex } from './local-storage.service';
import { GenerationService } from './generation.service';

@Injectable({
  providedIn: 'root'
})
export class StoryService {
  private storiesSubject = new BehaviorSubject<Story[]>([]);
  private currentStorySubject = new BehaviorSubject<Story | null>(null);

  public stories$ = this.storiesSubject.asObservable();
  public currentStory$ = this.currentStorySubject.asObservable();

  constructor(
    private localStorageService: LocalStorageService,
    private generationService: GenerationService
  ) {
    this.loadStories();
    // Subscribe to storage index changes
    this.localStorageService.storiesIndex$.subscribe(index => {
      this.loadStoriesFromIndex(index);
    });
  }

  private loadStoriesFromIndex(index: StoryIndex[]): void {
    const stories: Story[] = [];

    index.forEach(storyIndex => {
      const storyContent = this.localStorageService.loadStoryContent(storyIndex.id);
      if (storyContent) {
        stories.push(storyContent);
      }
    });

    this.storiesSubject.next(stories);
  }

  async loadStories(): Promise<void> {
    try {
      // Stories are loaded automatically from local storage via subscription
      console.log('Stories loaded from local storage');
    } catch (error) {
      console.error('Error loading stories:', error);
      this.storiesSubject.next([]);
    }
  }

  async createStory(storyData: StoryCreate): Promise<Story> {
    try {
      const story: Story = {
        id: this.generateStoryId(),
        title: storyData.title,
        genre: storyData.genre,
        description: storyData.description || '',
        current_phase: 'outline_development' as any,
        status: 'draft' as any,
        outline: undefined,
        chapters: [],
        characters: [],
        user_id: 'local_user',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        progress: {
          outline_approved: false,
          chapters_completed: 0,
          total_chapters_planned: 0,
          overall_progress: 0.0
        }
      };

      // Save to local storage
      this.localStorageService.saveStoryContent(story.id, story);

      // Save initial configuration if provided
      if (storyData.configuration) {
        this.localStorageService.saveStoryConfig(story.id, storyData.configuration);
      }

      return story;
    } catch (error) {
      console.error('Error creating story:', error);
      throw error;
    }
  }

  async loadStory(storyId: string): Promise<void> {
    try {
      const story = this.localStorageService.loadStoryContent(storyId);
      if (story) {
        this.currentStorySubject.next(story);
      } else {
        this.currentStorySubject.next(null);
      }
    } catch (error) {
      console.error('Error loading story:', error);
      this.currentStorySubject.next(null);
    }
  }

  async updateStory(storyId: string, storyUpdate: StoryUpdate): Promise<Story | null> {
    try {
      const existingStory = this.localStorageService.loadStoryContent(storyId);
      if (!existingStory) {
        return null;
      }

      const updatedStory: Story = {
        ...existingStory,
        ...storyUpdate,
        updated_at: new Date().toISOString()
      };

      // Save to local storage
      this.localStorageService.saveStoryContent(storyId, updatedStory);

      // Update current story if it's the one being edited
      const currentStory = this.currentStorySubject.value;
      if (currentStory && currentStory.id === storyId) {
        this.currentStorySubject.next(updatedStory);
      }

      return updatedStory;
    } catch (error) {
      console.error('Error updating story:', error);
      throw error;
    }
  }

  async deleteStory(storyId: string): Promise<boolean> {
    try {
      const success = this.localStorageService.deleteStory(storyId);

      // Clear current story if it's the one being deleted
      const currentStory = this.currentStorySubject.value;
      if (currentStory && currentStory.id === storyId) {
        this.currentStorySubject.next(null);
      }

      return success;
    } catch (error) {
      console.error('Error deleting story:', error);
      return false;
    }
  }

  // Generation workflow methods
  async generateOutline(storyId: string, userGuidance: string): Promise<any> {
    const story = this.localStorageService.loadStoryContent(storyId);
    if (!story) {
      throw new Error('Story not found');
    }

    const config = this.localStorageService.loadStoryConfig(storyId) || {};

    const request = {
      title: story.title,
      genre: story.genre,
      description: story.description,
      user_guidance: userGuidance,
      configuration: config
    };

    return this.generationService.generateOutline(request).toPromise();
  }

  async generateChapter(storyId: string, chapterNumber: number, userGuidance: string, sessionId: string): Promise<any> {
    const story = this.localStorageService.loadStoryContent(storyId);
    const memory = this.localStorageService.loadStoryMemory(storyId);
    const config = this.localStorageService.loadStoryConfig(storyId) || {};

    if (!story) {
      throw new Error('Story not found');
    }

    const request = {
      session_id: sessionId,
      chapter_number: chapterNumber,
      user_guidance: userGuidance,
      story_context: {
        outline: story.outline,
        previous_chapters: story.chapters,
        character_states: memory?.character_agents || {},
        story_memory: memory
      },
      configuration: config
    };

    return this.generationService.generateChapter(request).toPromise();
  }

  // Memory management
  saveStoryMemory(storyId: string, memoryData: any): void {
    this.localStorageService.saveStoryMemory(storyId, memoryData);
  }

  loadStoryMemory(storyId: string): any {
    return this.localStorageService.loadStoryMemory(storyId);
  }

  // Configuration management
  saveStoryConfig(storyId: string, configData: any): void {
    this.localStorageService.saveStoryConfig(storyId, configData);
  }

  loadStoryConfig(storyId: string): any {
    return this.localStorageService.loadStoryConfig(storyId);
  }

  setCurrentStory(story: Story | null): void {
    this.currentStorySubject.next(story);
  }

  getCurrentStory(): Story | null {
    return this.currentStorySubject.value;
  }

  private generateStoryId(): string {
    return 'story_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  // Auto-save functionality
  enableAutoSave(storyId: string, interval: number = 30000): void {
    setInterval(() => {
      const currentStory = this.currentStorySubject.value;
      if (currentStory && currentStory.id === storyId) {
        this.localStorageService.saveStoryContent(storyId, currentStory);
      }
    }, interval);
  }
}