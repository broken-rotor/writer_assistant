import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { Story, StoryListItem } from '../models/story.model';

export interface StorageQuota {
  used: number;
  available: number;
  total: number;
  percentage: number;
}

export interface StoryIndex {
  id: string;
  title: string;
  genre: string;
  size: number;
  lastModified: string;
}

export interface UserPreferences {
  theme?: string;
  language?: string;
  autoSave?: boolean;
  [key: string]: any;
}

export type StoryConfiguration = Record<string, any>;

@Injectable({
  providedIn: 'root'
})
export class LocalStorageService {
  private readonly STORAGE_PREFIX = 'writer_assistant_';
  private readonly STORY_KEY_PREFIX = `${this.STORAGE_PREFIX}story_`;
  private readonly ACTIVE_STORY_KEY = `${this.STORAGE_PREFIX}active_story`;
  private readonly STORY_LIST_KEY = `${this.STORAGE_PREFIX}story_list`;

  private storageQuotaSubject = new BehaviorSubject<StorageQuota>({
    used: 0,
    available: 0,
    total: 0,
    percentage: 0
  });

  private storyListSubject = new BehaviorSubject<StoryListItem[]>([]);

  public storageQuota$ = this.storageQuotaSubject.asObservable();
  public storyList$ = this.storyListSubject.asObservable();

  constructor() {
    this.loadStoryList();
    this.updateStorageQuota();
  }

  // Story CRUD Operations
  saveStory(story: Story): boolean {
    try {
      const key = this.getStoryKey(story.id);

      // Update metadata
      story.metadata.lastModified = new Date();

      // Convert Maps to arrays for JSON serialization
      const serializedStory = {
        ...story,
        characters: Array.from(story.characters.entries()),
        raters: Array.from(story.raters.entries()),
        chapterCreation: {
          ...story.chapterCreation,
          feedbackRequests: Array.from(story.chapterCreation.feedbackRequests.entries())
        },
        // Serialize ChapterComposeState if it exists
        chapterCompose: story.chapterCompose ? this.serializeChapterComposeState(story.chapterCompose) : undefined
      };

      localStorage.setItem(key, JSON.stringify(serializedStory));
      this.updateStoryList(story);
      this.updateStorageQuota();

      return true;
    } catch (error) {
      console.error('Error saving story:', error);
      this.handleStorageError(error);
      return false;
    }
  }

  loadStory(storyId: string): Story | null {
    try {
      const key = this.getStoryKey(storyId);
      const data = localStorage.getItem(key);

      if (!data) return null;

      const parsed = JSON.parse(data);

      // Convert arrays back to Maps
      const story: Story = {
        ...parsed,
        characters: new Map(parsed.characters || []),
        raters: new Map(parsed.raters || []),
        chapterCreation: {
          ...parsed.chapterCreation,
          feedbackRequests: new Map(parsed.chapterCreation?.feedbackRequests || [])
        },
        // Deserialize plotOutline.raterFeedback Map if it exists
        plotOutline: parsed.plotOutline ? {
          ...parsed.plotOutline,
          raterFeedback: new Map(parsed.plotOutline.raterFeedback || []),
          metadata: {
            ...parsed.plotOutline.metadata,
            created: new Date(parsed.plotOutline.metadata.created),
            lastModified: new Date(parsed.plotOutline.metadata.lastModified),
            approvedAt: parsed.plotOutline.metadata.approvedAt ? new Date(parsed.plotOutline.metadata.approvedAt) : undefined,
            lastFeedbackRequest: parsed.plotOutline.metadata.lastFeedbackRequest ? new Date(parsed.plotOutline.metadata.lastFeedbackRequest) : undefined
          }
        } : undefined,
        // Deserialize ChapterComposeState if it exists
        chapterCompose: parsed.chapterCompose ? this.deserializeChapterComposeState(parsed.chapterCompose) : undefined,
        metadata: {
          ...parsed.metadata,
          created: new Date(parsed.metadata.created),
          lastModified: new Date(parsed.metadata.lastModified)
        }
      };

      return story;
    } catch (error) {
      console.error('Error loading story:', error);
      return null;
    }
  }

  deleteStory(storyId: string): boolean {
    try {
      const key = this.getStoryKey(storyId);
      localStorage.removeItem(key);

      // Update story list
      const currentList = this.storyListSubject.value;
      const updatedList = currentList.filter(item => item.id !== storyId);
      this.saveStoryList(updatedList);
      this.storyListSubject.next(updatedList);

      this.updateStorageQuota();
      return true;
    } catch (error) {
      console.error('Error deleting story:', error);
      return false;
    }
  }

  // Active Story Management
  setActiveStory(storyId: string): void {
    try {
      localStorage.setItem(this.ACTIVE_STORY_KEY, storyId);
    } catch (error) {
      console.error('Error setting active story:', error);
    }
  }

  getActiveStoryId(): string | null {
    try {
      return localStorage.getItem(this.ACTIVE_STORY_KEY);
    } catch (error) {
      console.error('Error getting active story:', error);
      return null;
    }
  }

  // Story List Management
  private loadStoryList(): void {
    try {
      const data = localStorage.getItem(this.STORY_LIST_KEY);
      const list = data ? JSON.parse(data) : [];

      // Convert date strings back to Date objects
      const parsedList = list.map((item: any) => ({
        ...item,
        lastModified: new Date(item.lastModified)
      }));

      this.storyListSubject.next(parsedList);
    } catch (error) {
      console.error('Error loading story list:', error);
      this.storyListSubject.next([]);
    }
  }

  private saveStoryList(list: StoryListItem[]): void {
    try {
      localStorage.setItem(this.STORY_LIST_KEY, JSON.stringify(list));
    } catch (error) {
      console.error('Error saving story list:', error);
    }
  }

  private updateStoryList(story: Story): void {
    const currentList = this.storyListSubject.value;
    const existingIndex = currentList.findIndex(item => item.id === story.id);

    const listItem: StoryListItem = {
      id: story.id,
      title: story.general.title,
      lastModified: story.metadata.lastModified,
      chapterCount: story.story.chapters.length
    };

    let updatedList: StoryListItem[];
    if (existingIndex >= 0) {
      updatedList = [...currentList];
      updatedList[existingIndex] = listItem;
    } else {
      updatedList = [...currentList, listItem];
    }

    // Sort by last modified (newest first)
    updatedList.sort((a, b) => b.lastModified.getTime() - a.lastModified.getTime());

    this.saveStoryList(updatedList);
    this.storyListSubject.next(updatedList);
  }

  getStoryList(): Observable<StoryListItem[]> {
    return this.storyList$;
  }

  // Storage Management
  private getStoryKey(storyId: string): string {
    return `${this.STORY_KEY_PREFIX}${storyId}`;
  }

  private updateStorageQuota(): void {
    try {
      let totalSize = 0;
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith(this.STORAGE_PREFIX)) {
          const value = localStorage.getItem(key);
          totalSize += key.length + (value?.length || 0);
        }
      }

      // Estimate available space (localStorage typically has ~5-10MB limit)
      const estimatedLimit = 5 * 1024 * 1024; // 5MB in bytes
      const available = Math.max(0, estimatedLimit - totalSize);
      const percentage = (totalSize / estimatedLimit) * 100;

      const quota: StorageQuota = {
        used: totalSize,
        available: available,
        total: estimatedLimit,
        percentage: Math.min(100, percentage)
      };

      this.storageQuotaSubject.next(quota);
    } catch (error) {
      console.error('Error calculating storage quota:', error);
    }
  }

  private handleStorageError(error: any): void {
    if (error.name === 'QuotaExceededError' || error.code === 22) {
      console.warn('Storage quota exceeded. Consider exporting and deleting old stories.');
    }
  }

  getStorageQuota(): Observable<StorageQuota> {
    return this.storageQuota$;
  }

  // Storage Stats
  getStorageStats(): { totalStories: number; totalSize: number; averageSize: number } {
    const list = this.storyListSubject.value;
    let totalSize = 0;

    list.forEach(item => {
      const story = this.loadStory(item.id);
      if (story) {
        const serialized = JSON.stringify({
          ...story,
          characters: Array.from(story.characters.entries()),
          raters: Array.from(story.raters.entries())
        });
        totalSize += serialized.length;
      }
    });

    return {
      totalStories: list.length,
      totalSize: totalSize,
      averageSize: list.length > 0 ? totalSize / list.length : 0
    };
  }

  // Export/Import
  exportStory(storyId: string): Blob | null {
    try {
      const story = this.loadStory(storyId);
      if (!story) return null;

      const exportData = {
        exportMetadata: {
          timestamp: new Date().toISOString(),
          version: '1.0',
          storyId: storyId
        },
        story: {
          ...story,
          characters: Array.from(story.characters.entries()),
          raters: Array.from(story.raters.entries()),
          chapterCreation: {
            ...story.chapterCreation,
            feedbackRequests: Array.from(story.chapterCreation.feedbackRequests.entries())
          }
        }
      };

      const jsonString = JSON.stringify(exportData, null, 2);
      return new Blob([jsonString], { type: 'application/json' });
    } catch (error) {
      console.error('Error exporting story:', error);
      return null;
    }
  }

  exportAllStories(): Blob {
    const list = this.storyListSubject.value;
    const stories: any[] = [];

    list.forEach(item => {
      const story = this.loadStory(item.id);
      if (story) {
        stories.push({
          ...story,
          characters: Array.from(story.characters.entries()),
          raters: Array.from(story.raters.entries()),
          chapterCreation: {
            ...story.chapterCreation,
            feedbackRequests: Array.from(story.chapterCreation.feedbackRequests.entries())
          }
        });
      }
    });

    const exportData = {
      exportMetadata: {
        timestamp: new Date().toISOString(),
        version: '1.0',
        totalStories: stories.length
      },
      stories: stories
    };

    const jsonString = JSON.stringify(exportData, null, 2);
    return new Blob([jsonString], { type: 'application/json' });
  }

  async importStory(file: File): Promise<{ success: boolean; storyId?: string; error?: string }> {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const importData = JSON.parse(e.target?.result as string);

          if (!importData.story) {
            resolve({ success: false, error: 'Invalid import file: missing story data' });
            return;
          }

          const storyData = importData.story;

          // Reconstruct Story object with Maps
          const story: Story = {
            ...storyData,
            characters: new Map(storyData.characters || []),
            raters: new Map(storyData.raters || []),
            chapterCreation: {
              ...storyData.chapterCreation,
              feedbackRequests: new Map(storyData.chapterCreation?.feedbackRequests || [])
            },
            metadata: {
              ...storyData.metadata,
              created: new Date(storyData.metadata.created),
              lastModified: new Date()
            }
          };

          const success = this.saveStory(story);

          if (success) {
            resolve({ success: true, storyId: story.id });
          } else {
            resolve({ success: false, error: 'Failed to save imported story' });
          }
        } catch (error) {
          resolve({ success: false, error: `Import failed: ${error}` });
        }
      };
      reader.readAsText(file);
    });
  }

  // Generic storage methods for other services
  getItem(key: string): any {
    try {
      const data = localStorage.getItem(key);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error('Error getting item from storage:', error);
      return null;
    }
  }

  setItem(key: string, value: any): boolean {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (error) {
      console.error('Error setting item in storage:', error);
      this.handleStorageError(error);
      return false;
    }
  }

  // Cleanup
  cleanupOldStories(maxAgeInDays = 30): number {
    const cutoffDate = new Date(Date.now() - maxAgeInDays * 24 * 60 * 60 * 1000);
    const currentList = this.storyListSubject.value;
    let cleanedCount = 0;

    const toDelete = currentList.filter(item =>
      item.lastModified < cutoffDate
    );

    toDelete.forEach(item => {
      if (this.deleteStory(item.id)) {
        cleanedCount++;
      }
    });

    return cleanedCount;
  }

  clearAllData(): boolean {
    try {
      const keys: string[] = [];
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith(this.STORAGE_PREFIX)) {
          keys.push(key);
        }
      }

      keys.forEach(key => localStorage.removeItem(key));

      this.storyListSubject.next([]);
      this.updateStorageQuota();

      return true;
    } catch (error) {
      console.error('Error clearing all data:', error);
      return false;
    }
  }

  // ChapterComposeState serialization methods
  private serializeChapterComposeState(state: any): any {
    return {
      ...state,
      phases: {
        plotOutline: {
          ...state.phases.plotOutline,
          conversation: this.serializeConversationThread(state.phases.plotOutline.conversation),
          outline: {
            ...state.phases.plotOutline.outline,
            items: Array.from(state.phases.plotOutline.outline.items.entries())
          }
        },
        chapterDetailer: {
          ...state.phases.chapterDetailer,
          conversation: this.serializeConversationThread(state.phases.chapterDetailer.conversation),
          feedbackIntegration: {
            ...state.phases.chapterDetailer.feedbackIntegration,
            feedbackRequests: Array.from(state.phases.chapterDetailer.feedbackIntegration.feedbackRequests.entries())
          }
        },
        finalEdit: {
          ...state.phases.finalEdit,
          conversation: this.serializeConversationThread(state.phases.finalEdit.conversation)
        }
      }
    };
  }

  private deserializeChapterComposeState(serialized: any): any {
    return {
      ...serialized,
      phases: {
        plotOutline: {
          ...serialized.phases.plotOutline,
          conversation: this.deserializeConversationThread(serialized.phases.plotOutline.conversation),
          outline: {
            ...serialized.phases.plotOutline.outline,
            items: new Map(serialized.phases.plotOutline.outline.items || [])
          }
        },
        chapterDetailer: {
          ...serialized.phases.chapterDetailer,
          conversation: this.deserializeConversationThread(serialized.phases.chapterDetailer.conversation),
          feedbackIntegration: {
            ...serialized.phases.chapterDetailer.feedbackIntegration,
            feedbackRequests: new Map(serialized.phases.chapterDetailer.feedbackIntegration.feedbackRequests || [])
          }
        },
        finalEdit: {
          ...serialized.phases.finalEdit,
          conversation: this.deserializeConversationThread(serialized.phases.finalEdit.conversation)
        }
      },
      metadata: {
        ...serialized.metadata,
        created: new Date(serialized.metadata.created),
        lastModified: new Date(serialized.metadata.lastModified)
      }
    };
  }

  private serializeConversationThread(conversation: any): any {
    return {
      ...conversation,
      branches: Array.from(conversation.branches.entries()),
      messages: conversation.messages.map((msg: any) => ({
        ...msg,
        timestamp: msg.timestamp.toISOString()
      }))
    };
  }

  private deserializeConversationThread(serialized: any): any {
    return {
      ...serialized,
      branches: new Map(serialized.branches || []),
      messages: serialized.messages.map((msg: any) => ({
        ...msg,
        timestamp: new Date(msg.timestamp)
      })),
      metadata: {
        ...serialized.metadata,
        created: new Date(serialized.metadata.created),
        lastModified: new Date(serialized.metadata.lastModified)
      }
    };
  }

  /**
   * Remove an item from localStorage by key
   */
  removeItem(key: string): void {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.error('Error removing item from localStorage:', error);
    }
  }

  // Missing methods needed by components
  getStoriesIndex(): Observable<StoryIndex[]> {
    return new Observable(observer => {
      const list = this.storyListSubject.value;
      const storiesIndex: StoryIndex[] = list.map(item => {
        const story = this.loadStory(item.id);
        const serialized = story ? JSON.stringify({
          ...story,
          characters: Array.from(story.characters.entries()),
          raters: Array.from(story.raters.entries())
        }) : '';
        
        return {
          id: item.id,
          title: item.title,
          genre: 'Unknown', // Genre not available in GeneralConfig
          size: serialized.length,
          lastModified: item.lastModified.toISOString()
        };
      });
      
      observer.next(storiesIndex);
      observer.complete();
    });
  }

  async importStories(file: File): Promise<{ success: boolean; storyId?: string; error?: string }> {
    // For now, delegate to importStory since the component seems to expect the same interface
    return this.importStory(file);
  }

  loadUserPreferences(): UserPreferences | null {
    const key = `${this.STORAGE_PREFIX}user_preferences`;
    return this.getItem(key);
  }

  saveUserPreferences(preferences: UserPreferences): boolean {
    const key = `${this.STORAGE_PREFIX}user_preferences`;
    return this.setItem(key, preferences);
  }

  loadStoryConfig(storyId: string): StoryConfiguration | null {
    const key = `${this.STORAGE_PREFIX}story_config_${storyId}`;
    return this.getItem(key);
  }

  saveStoryConfig(storyId: string, config: StoryConfiguration): boolean {
    const key = `${this.STORAGE_PREFIX}story_config_${storyId}`;
    return this.setItem(key, config);
  }
}
