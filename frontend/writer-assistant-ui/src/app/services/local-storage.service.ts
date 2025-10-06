import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

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
  lastModified: string;
  size: number;
  phase: string;
  status: string;
}

@Injectable({
  providedIn: 'root'
})
export class LocalStorageService {
  private readonly STORAGE_PREFIX = 'writer_assistant_';
  private readonly STORIES_INDEX_KEY = `${this.STORAGE_PREFIX}stories_index`;
  private readonly USER_PREFERENCES_KEY = `${this.STORAGE_PREFIX}user_preferences`;

  private storageQuotaSubject = new BehaviorSubject<StorageQuota>({ used: 0, available: 0, total: 0, percentage: 0 });
  private storiesIndexSubject = new BehaviorSubject<StoryIndex[]>([]);

  public storageQuota$ = this.storageQuotaSubject.asObservable();
  public storiesIndex$ = this.storiesIndexSubject.asObservable();

  constructor() {
    this.loadStoriesIndex();
    this.updateStorageQuota();
  }

  // Story Management
  private getStoryKey(storyId: string, type: 'content' | 'memory' | 'config'): string {
    return `${this.STORAGE_PREFIX}story_${storyId}_${type}`;
  }

  saveStoryContent(storyId: string, story: any): void {
    try {
      const key = this.getStoryKey(storyId, 'content');
      const data = {
        ...story,
        lastModified: new Date().toISOString()
      };
      localStorage.setItem(key, JSON.stringify(data));
      this.updateStoryIndex(storyId, story);
      this.updateStorageQuota();
    } catch (error) {
      console.error('Error saving story content:', error);
      this.handleStorageError(error);
    }
  }

  loadStoryContent(storyId: string): any | null {
    try {
      const key = this.getStoryKey(storyId, 'content');
      const data = localStorage.getItem(key);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error('Error loading story content:', error);
      return null;
    }
  }

  saveStoryMemory(storyId: string, memoryData: any): void {
    try {
      const key = this.getStoryKey(storyId, 'memory');
      const data = {
        ...memoryData,
        lastUpdated: new Date().toISOString(),
        storageSize: JSON.stringify(memoryData).length
      };
      localStorage.setItem(key, JSON.stringify(data));
      this.updateStorageQuota();
    } catch (error) {
      console.error('Error saving story memory:', error);
      this.handleStorageError(error);
    }
  }

  loadStoryMemory(storyId: string): any | null {
    try {
      const key = this.getStoryKey(storyId, 'memory');
      const data = localStorage.getItem(key);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error('Error loading story memory:', error);
      return null;
    }
  }

  saveStoryConfig(storyId: string, configData: any): void {
    try {
      const key = this.getStoryKey(storyId, 'config');
      localStorage.setItem(key, JSON.stringify(configData));
      this.updateStorageQuota();
    } catch (error) {
      console.error('Error saving story config:', error);
      this.handleStorageError(error);
    }
  }

  loadStoryConfig(storyId: string): any | null {
    try {
      const key = this.getStoryKey(storyId, 'config');
      const data = localStorage.getItem(key);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error('Error loading story config:', error);
      return null;
    }
  }

  deleteStory(storyId: string): boolean {
    try {
      // Remove all story data
      localStorage.removeItem(this.getStoryKey(storyId, 'content'));
      localStorage.removeItem(this.getStoryKey(storyId, 'memory'));
      localStorage.removeItem(this.getStoryKey(storyId, 'config'));

      // Update stories index
      const currentIndex = this.storiesIndexSubject.value;
      const updatedIndex = currentIndex.filter(story => story.id !== storyId);
      this.saveStoriesIndex(updatedIndex);
      this.storiesIndexSubject.next(updatedIndex);

      this.updateStorageQuota();
      return true;
    } catch (error) {
      console.error('Error deleting story:', error);
      return false;
    }
  }

  // Stories Index Management
  private loadStoriesIndex(): void {
    try {
      const data = localStorage.getItem(this.STORIES_INDEX_KEY);
      const index = data ? JSON.parse(data) : [];
      this.storiesIndexSubject.next(index);
    } catch (error) {
      console.error('Error loading stories index:', error);
      this.storiesIndexSubject.next([]);
    }
  }

  private saveStoriesIndex(index: StoryIndex[]): void {
    try {
      localStorage.setItem(this.STORIES_INDEX_KEY, JSON.stringify(index));
    } catch (error) {
      console.error('Error saving stories index:', error);
    }
  }

  private updateStoryIndex(storyId: string, story: any): void {
    const currentIndex = this.storiesIndexSubject.value;
    const existingIndex = currentIndex.findIndex(item => item.id === storyId);

    const storyIndexItem: StoryIndex = {
      id: storyId,
      title: story.title,
      genre: story.genre,
      lastModified: new Date().toISOString(),
      size: JSON.stringify(story).length,
      phase: story.current_phase || 'outline_development',
      status: story.status || 'draft'
    };

    let updatedIndex: StoryIndex[];
    if (existingIndex >= 0) {
      updatedIndex = [...currentIndex];
      updatedIndex[existingIndex] = storyIndexItem;
    } else {
      updatedIndex = [...currentIndex, storyIndexItem];
    }

    this.saveStoriesIndex(updatedIndex);
    this.storiesIndexSubject.next(updatedIndex);
  }

  // User Preferences
  saveUserPreferences(preferences: any): void {
    try {
      localStorage.setItem(this.USER_PREFERENCES_KEY, JSON.stringify(preferences));
    } catch (error) {
      console.error('Error saving user preferences:', error);
    }
  }

  loadUserPreferences(): any | null {
    try {
      const data = localStorage.getItem(this.USER_PREFERENCES_KEY);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error('Error loading user preferences:', error);
      return null;
    }
  }

  // Storage Management
  private updateStorageQuota(): void {
    try {
      // Calculate storage usage
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
      // Storage quota exceeded
      console.warn('Storage quota exceeded. Consider cleaning up old stories.');
      // Emit a warning or trigger cleanup
    }
  }

  // Storage Cleanup
  getStorageStats(): { [key: string]: number } {
    const stats: { [key: string]: number } = {};

    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(this.STORAGE_PREFIX)) {
        const value = localStorage.getItem(key);
        const size = key.length + (value?.length || 0);

        if (key.includes('_content')) {
          stats['content'] = (stats['content'] || 0) + size;
        } else if (key.includes('_memory')) {
          stats['memory'] = (stats['memory'] || 0) + size;
        } else if (key.includes('_config')) {
          stats['config'] = (stats['config'] || 0) + size;
        } else {
          stats['other'] = (stats['other'] || 0) + size;
        }
      }
    }

    return stats;
  }

  cleanupOldStories(maxAge: number = 30): number {
    const cutoffDate = new Date(Date.now() - maxAge * 24 * 60 * 60 * 1000);
    const currentIndex = this.storiesIndexSubject.value;
    let cleanedCount = 0;

    const toDelete = currentIndex.filter(story => {
      const lastModified = new Date(story.lastModified);
      return lastModified < cutoffDate;
    });

    toDelete.forEach(story => {
      if (this.deleteStory(story.id)) {
        cleanedCount++;
      }
    });

    return cleanedCount;
  }

  // Export/Import
  exportAllStories(): Blob {
    const exportData: any = {
      exportMetadata: {
        timestamp: new Date().toISOString(),
        version: '1.0',
        totalStories: this.storiesIndexSubject.value.length
      },
      stories: []
    };

    this.storiesIndexSubject.value.forEach(storyIndex => {
      const content = this.loadStoryContent(storyIndex.id);
      const memory = this.loadStoryMemory(storyIndex.id);
      const config = this.loadStoryConfig(storyIndex.id);

      if (content) {
        exportData.stories.push({
          content,
          memory,
          config
        });
      }
    });

    const jsonString = JSON.stringify(exportData, null, 2);
    return new Blob([jsonString], { type: 'application/json' });
  }

  async importStories(file: File): Promise<{ success: number; errors: string[] }> {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const importData = JSON.parse(e.target?.result as string);
          let successCount = 0;
          const errors: string[] = [];

          if (importData.stories && Array.isArray(importData.stories)) {
            importData.stories.forEach((storyData: any, index: number) => {
              try {
                if (storyData.content && storyData.content.id) {
                  this.saveStoryContent(storyData.content.id, storyData.content);
                  if (storyData.memory) {
                    this.saveStoryMemory(storyData.content.id, storyData.memory);
                  }
                  if (storyData.config) {
                    this.saveStoryConfig(storyData.content.id, storyData.config);
                  }
                  successCount++;
                } else {
                  errors.push(`Story ${index + 1}: Missing or invalid content`);
                }
              } catch (error) {
                errors.push(`Story ${index + 1}: ${error}`);
              }
            });
          }

          resolve({ success: successCount, errors });
        } catch (error) {
          resolve({ success: 0, errors: [`Invalid file format: ${error}`] });
        }
      };
      reader.readAsText(file);
    });
  }

  getStorageQuota(): Observable<StorageQuota> {
    return this.storageQuota$;
  }

  getStoriesIndex(): Observable<StoryIndex[]> {
    return this.storiesIndex$;
  }
}