import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import {
  Story,
  LocalStorageInfo,
  ConversationTree,
  StateCheckpoint,
  MemoryState,
  ValidationResult,
  ValidationIssue,
  ValidationWarning
} from '../../shared/models';

@Injectable({
  providedIn: 'root'
})
export class LocalStorageService {
  private storageKeyPrefix = 'writer_assistant_';
  private storageInfo$ = new BehaviorSubject<LocalStorageInfo>(this.getStorageInfo());

  constructor() {
    this.initializeStorage();
  }

  private initializeStorage(): void {
    if (!this.getItem('stories_index')) {
      this.setItem('stories_index', []);
    }
    if (!this.getItem('user_preferences')) {
      this.setItem('user_preferences', {
        theme: 'light',
        autoSave: true,
        backupFrequency: 'daily'
      });
    }
  }

  // Core Storage Operations
  private getKey(key: string): string {
    return `${this.storageKeyPrefix}${key}`;
  }

  private setItem(key: string, value: any): void {
    try {
      localStorage.setItem(this.getKey(key), JSON.stringify(value));
      this.updateStorageInfo();
    } catch (error) {
      console.error('Error saving to localStorage:', error);
      throw new Error('Storage quota exceeded');
    }
  }

  private getItem<T>(key: string): T | null {
    try {
      const item = localStorage.getItem(this.getKey(key));
      return item ? JSON.parse(item) : null;
    } catch (error) {
      console.error('Error reading from localStorage:', error);
      return null;
    }
  }

  private removeItem(key: string): void {
    localStorage.removeItem(this.getKey(key));
    this.updateStorageInfo();
  }

  // Storage Information
  getStorageInfo(): LocalStorageInfo {
    const usedSpace = this.calculateUsedSpace();
    const availableSpace = 5 * 1024 * 1024; // 5MB typical limit
    const storiesIndex = this.getItem<string[]>('stories_index') || [];
    const lastBackup = this.getItem<Date>('last_backup') || new Date();

    return {
      usedSpace,
      availableSpace,
      storiesCount: storiesIndex.length,
      lastBackup: new Date(lastBackup)
    };
  }

  private calculateUsedSpace(): number {
    let totalSize = 0;
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(this.storageKeyPrefix)) {
        const value = localStorage.getItem(key);
        totalSize += (key.length + (value?.length || 0)) * 2; // UTF-16 encoding
      }
    }
    return totalSize;
  }

  private updateStorageInfo(): void {
    this.storageInfo$.next(this.getStorageInfo());
  }

  getStorageInfo$(): Observable<LocalStorageInfo> {
    return this.storageInfo$.asObservable();
  }

  // Story Management
  saveStory(story: Story): void {
    const storiesIndex = this.getItem<string[]>('stories_index') || [];

    if (!storiesIndex.includes(story.id)) {
      storiesIndex.push(story.id);
      this.setItem('stories_index', storiesIndex);
    }

    this.setItem(`story_${story.id}`, story);
    this.setItem(`story_${story.id}_last_modified`, new Date());
  }

  getStory(storyId: string): Story | null {
    return this.getItem<Story>(`story_${storyId}`);
  }

  getAllStories(): Story[] {
    const storiesIndex = this.getItem<string[]>('stories_index') || [];
    return storiesIndex
      .map(id => this.getStory(id))
      .filter(story => story !== null) as Story[];
  }

  deleteStory(storyId: string): void {
    const storiesIndex = this.getItem<string[]>('stories_index') || [];
    const updatedIndex = storiesIndex.filter(id => id !== storyId);

    this.setItem('stories_index', updatedIndex);
    this.removeItem(`story_${storyId}`);
    this.removeItem(`story_${storyId}_memory`);
    this.removeItem(`story_${storyId}_conversation_tree`);
    this.removeItem(`story_${storyId}_checkpoints`);
  }

  duplicateStory(storyId: string): Story | null {
    const originalStory = this.getStory(storyId);
    if (!originalStory) return null;

    const newStory: Story = {
      ...originalStory,
      id: this.generateId(),
      title: `${originalStory.title} (Copy)`,
      createdAt: new Date(),
      lastModified: new Date()
    };

    this.saveStory(newStory);

    // Copy associated data
    const memory = this.getStoryMemory(storyId);
    if (memory) {
      this.saveStoryMemory(newStory.id, memory);
    }

    const conversationTree = this.getConversationTree(storyId);
    if (conversationTree) {
      this.saveConversationTree(newStory.id, conversationTree);
    }

    return newStory;
  }

  exportStory(storyId: string): string {
    const story = this.getStory(storyId);
    const memory = this.getStoryMemory(storyId);
    const conversationTree = this.getConversationTree(storyId);
    const checkpoints = this.getCheckpoints(storyId);

    const exportData = {
      story,
      memory,
      conversationTree,
      checkpoints,
      exportedAt: new Date(),
      version: '1.0'
    };

    return JSON.stringify(exportData, null, 2);
  }

  importStory(importData: string): Story | null {
    try {
      const data = JSON.parse(importData);
      const story = data.story;

      if (!story || !story.id) {
        throw new Error('Invalid story data');
      }

      // Generate new ID to avoid conflicts
      story.id = this.generateId();
      story.lastModified = new Date();

      this.saveStory(story);

      if (data.memory) {
        this.saveStoryMemory(story.id, data.memory);
      }

      if (data.conversationTree) {
        this.saveConversationTree(story.id, data.conversationTree);
      }

      if (data.checkpoints) {
        this.saveCheckpoints(story.id, data.checkpoints);
      }

      return story;
    } catch (error) {
      console.error('Error importing story:', error);
      return null;
    }
  }

  // Memory Management
  saveStoryMemory(storyId: string, memoryState: { [agentId: string]: MemoryState }): void {
    this.setItem(`story_${storyId}_memory`, memoryState);
  }

  getStoryMemory(storyId: string): { [agentId: string]: MemoryState } | null {
    return this.getItem(`story_${storyId}_memory`);
  }

  saveAgentMemory(storyId: string, agentId: string, memory: MemoryState): void {
    const allMemory = this.getStoryMemory(storyId) || {};
    allMemory[agentId] = memory;
    this.saveStoryMemory(storyId, allMemory);
  }

  getAgentMemory(storyId: string, agentId: string): MemoryState | null {
    const allMemory = this.getStoryMemory(storyId);
    return allMemory ? allMemory[agentId] || null : null;
  }

  validateMemoryConsistency(storyId: string): ValidationResult {
    const memory = this.getStoryMemory(storyId);
    if (!memory) {
      return { isValid: true, issues: [], warnings: [] };
    }

    const issues: ValidationIssue[] = [];
    const warnings: ValidationWarning[] = [];

    // Add validation logic here
    // For now, return basic validation
    return {
      isValid: issues.length === 0,
      issues,
      warnings
    };
  }

  // Conversation Branching
  saveConversationTree(storyId: string, tree: ConversationTree): void {
    this.setItem(`story_${storyId}_conversation_tree`, tree);
  }

  getConversationTree(storyId: string): ConversationTree | null {
    return this.getItem(`story_${storyId}_conversation_tree`);
  }

  // Checkpoints
  saveCheckpoint(storyId: string, checkpoint: StateCheckpoint): void {
    const checkpoints = this.getCheckpoints(storyId) || [];
    checkpoints.push(checkpoint);
    this.saveCheckpoints(storyId, checkpoints);
  }

  getCheckpoints(storyId: string): StateCheckpoint[] {
    return this.getItem(`story_${storyId}_checkpoints`) || [];
  }

  private saveCheckpoints(storyId: string, checkpoints: StateCheckpoint[]): void {
    this.setItem(`story_${storyId}_checkpoints`, checkpoints);
  }

  restoreCheckpoint(storyId: string, checkpointId: string): boolean {
    const checkpoints = this.getCheckpoints(storyId);
    const checkpoint = checkpoints.find(cp => cp.id === checkpointId);

    if (!checkpoint) return false;

    // Restore state from checkpoint
    if (checkpoint.storyState) {
      this.setItem(`story_${storyId}`, checkpoint.storyState);
    }
    if (checkpoint.memoryState) {
      this.saveStoryMemory(storyId, checkpoint.memoryState);
    }
    if (checkpoint.conversationState) {
      this.saveConversationTree(storyId, checkpoint.conversationState);
    }

    return true;
  }

  // Data Operations
  backupAllData(): string {
    const allData: any = {
      stories: this.getAllStories(),
      storiesIndex: this.getItem('stories_index'),
      userPreferences: this.getItem('user_preferences'),
      backupDate: new Date(),
      version: '1.0',
      storyData: {}
    };

    // Include all story-related data
    const storiesIndex = this.getItem<string[]>('stories_index') || [];

    storiesIndex.forEach(storyId => {
      allData.storyData[storyId] = {
        memory: this.getStoryMemory(storyId),
        conversationTree: this.getConversationTree(storyId),
        checkpoints: this.getCheckpoints(storyId)
      };
    });

    this.setItem('last_backup', new Date());
    return JSON.stringify(allData, null, 2);
  }

  restoreFromBackup(backupData: string): boolean {
    try {
      const data = JSON.parse(backupData);

      // Clear existing data
      this.clearAllData();

      // Restore stories
      if (data.stories && Array.isArray(data.stories)) {
        data.stories.forEach((story: Story) => this.saveStory(story));
      }

      // Restore story data
      if (data.storyData) {
        Object.keys(data.storyData).forEach(storyId => {
          const storyData = data.storyData[storyId];
          if (storyData.memory) {
            this.saveStoryMemory(storyId, storyData.memory);
          }
          if (storyData.conversationTree) {
            this.saveConversationTree(storyId, storyData.conversationTree);
          }
          if (storyData.checkpoints) {
            this.saveCheckpoints(storyId, storyData.checkpoints);
          }
        });
      }

      // Restore preferences
      if (data.userPreferences) {
        this.setItem('user_preferences', data.userPreferences);
      }

      return true;
    } catch (error) {
      console.error('Error restoring backup:', error);
      return false;
    }
  }

  clearAllData(): void {
    const keys = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(this.storageKeyPrefix)) {
        keys.push(key);
      }
    }

    keys.forEach(key => localStorage.removeItem(key));
    this.initializeStorage();
  }

  optimizeStorage(): void {
    // Remove orphaned data
    const storiesIndex = this.getItem<string[]>('stories_index') || [];
    const allKeys = [];

    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(this.storageKeyPrefix)) {
        allKeys.push(key);
      }
    }

    // Find orphaned story data
    allKeys.forEach(key => {
      const match = key.match(/story_([^_]+)_/);
      if (match) {
        const storyId = match[1];
        if (!storiesIndex.includes(storyId)) {
          localStorage.removeItem(key);
        }
      }
    });

    this.updateStorageInfo();
  }

  private generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }
}