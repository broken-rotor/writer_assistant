import { Injectable, inject } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';

import { ConversationService } from './conversation.service';
import { LocalStorageService } from './local-storage.service';
import { ChatMessage } from '../models/story.model';

export interface WorldbuildingSyncConfig {
  storyId: string;
  syncInterval?: number; // milliseconds
  maxSummaryLength?: number;
  includeAssistantMessages?: boolean;
  includeUserMessages?: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class WorldbuildingSyncService {
  private worldbuildingUpdatedSubject = new BehaviorSubject<string>('');
  private syncInProgressSubject = new BehaviorSubject<boolean>(false);
  
  // Services
  private conversationService = inject(ConversationService);
  private localStorageService = inject(LocalStorageService);

  // Configuration
  private defaultConfig: Partial<WorldbuildingSyncConfig> = {
    syncInterval: 2000, // 2 seconds debounce
    maxSummaryLength: 5000, // characters
    includeAssistantMessages: true,
    includeUserMessages: true
  };

  // Observables
  public worldbuildingUpdated$ = this.worldbuildingUpdatedSubject.asObservable().pipe(
    debounceTime(this.defaultConfig.syncInterval!),
    distinctUntilChanged()
  );
  
  public syncInProgress$ = this.syncInProgressSubject.asObservable();

  /**
   * Sync worldbuilding content from conversation messages
   */
  async syncWorldbuildingFromConversation(
    storyId: string, 
    currentWorldbuilding = '',
    config?: Partial<WorldbuildingSyncConfig>
  ): Promise<string> {
    try {
      this.syncInProgressSubject.next(true);

      const syncConfig = { ...this.defaultConfig, ...config, storyId };
      const messages = this.conversationService.getCurrentBranchMessages();
      
      if (messages.length === 0) {
        // No messages, return current worldbuilding
        return currentWorldbuilding;
      }

      // Extract worldbuilding information from messages
      const extractedWorldbuilding = this.extractWorldbuildingFromMessages(
        messages, 
        syncConfig
      );

      // Merge with existing worldbuilding
      const updatedWorldbuilding = this.mergeWorldbuildingContent(
        currentWorldbuilding,
        extractedWorldbuilding,
        syncConfig
      );

      // Update the subject to notify subscribers
      this.worldbuildingUpdatedSubject.next(updatedWorldbuilding);

      // Store the updated worldbuilding
      this.storeWorldbuildingSync(storyId, updatedWorldbuilding);

      return updatedWorldbuilding;

    } catch (error) {
      console.error('Failed to sync worldbuilding from conversation:', error);
      throw error;
    } finally {
      this.syncInProgressSubject.next(false);
    }
  }

  /**
   * Extract worldbuilding information from chat messages
   */
  private extractWorldbuildingFromMessages(
    messages: ChatMessage[], 
    config: WorldbuildingSyncConfig
  ): string {
    const relevantMessages = messages.filter(message => {
      if (config.includeUserMessages && message.type === 'user') return true;
      if (config.includeAssistantMessages && message.type === 'assistant') return true;
      return false;
    });

    if (relevantMessages.length === 0) {
      return '';
    }

    // Create a structured summary of worldbuilding elements
    const worldbuildingElements: string[] = [];

    relevantMessages.forEach((message) => {
      const messageContent = message.content.trim();
      if (messageContent.length === 0) return;

      // Add message with context
      const timestamp = new Date(message.timestamp).toLocaleString();
      
      // For user messages, treat as worldbuilding input
      if (message.type === 'user') {
        worldbuildingElements.push(`[${timestamp}] User Input: ${messageContent}`);
      }
      
      // For assistant messages, extract worldbuilding insights
      if (message.type === 'assistant') {
        const insights = this.extractWorldbuildingInsights(messageContent);
        if (insights.length > 0) {
          worldbuildingElements.push(`[${timestamp}] AI Insights: ${insights}`);
        }
      }
    });

    return worldbuildingElements.join('\n\n');
  }

  /**
   * Extract worldbuilding insights from assistant messages
   */
  private extractWorldbuildingInsights(content: string): string {
    // Simple extraction logic - in a real implementation, this could be more sophisticated
    // Look for sentences that describe world elements, settings, rules, etc.
    
    const sentences = content.split(/[.!?]+/).map(s => s.trim()).filter(s => s.length > 0);
    const worldbuildingKeywords = [
      'world', 'setting', 'location', 'place', 'culture', 'society', 'history',
      'magic', 'technology', 'politics', 'religion', 'geography', 'climate',
      'species', 'race', 'kingdom', 'empire', 'city', 'town', 'village',
      'law', 'rule', 'custom', 'tradition', 'language', 'currency'
    ];

    const relevantSentences = sentences.filter(sentence => {
      const lowerSentence = sentence.toLowerCase();
      return worldbuildingKeywords.some(keyword => lowerSentence.includes(keyword));
    });

    return relevantSentences.join('. ');
  }

  /**
   * Merge new worldbuilding content with existing content
   */
  private mergeWorldbuildingContent(
    existing: string,
    extracted: string,
    config: WorldbuildingSyncConfig
  ): string {
    if (!extracted.trim()) {
      return existing;
    }

    if (!existing.trim()) {
      return this.truncateContent(extracted, config.maxSummaryLength!);
    }

    // Combine existing and new content
    const combined = `${existing}\n\n--- Recent Conversation ---\n${extracted}`;
    
    return this.truncateContent(combined, config.maxSummaryLength!);
  }

  /**
   * Truncate content to maximum length while preserving readability
   */
  private truncateContent(content: string, maxLength: number): string {
    if (content.length <= maxLength) {
      return content;
    }

    // Try to truncate at a natural break point
    const truncated = content.substring(0, maxLength);
    const lastNewline = truncated.lastIndexOf('\n');
    const lastSentence = truncated.lastIndexOf('.');
    
    const breakPoint = Math.max(lastNewline, lastSentence);
    
    if (breakPoint > maxLength * 0.8) {
      // Use the break point if it's not too far back
      return truncated.substring(0, breakPoint + 1) + '\n\n[Content truncated...]';
    } else {
      // Just truncate at max length
      return truncated + '...\n\n[Content truncated...]';
    }
  }

  /**
   * Store worldbuilding sync metadata
   */
  private storeWorldbuildingSync(storyId: string, worldbuilding: string): void {
    try {
      const syncData = {
        storyId,
        worldbuilding,
        lastSync: new Date().toISOString(),
        messageCount: this.conversationService.getCurrentBranchMessages().length
      };

      this.localStorageService.setItem(
        `worldbuilding_sync_${storyId}`,
        syncData
      );
    } catch (error) {
      console.error('Failed to store worldbuilding sync data:', error);
    }
  }

  /**
   * Get stored worldbuilding sync data
   */
  getStoredWorldbuildingSync(storyId: string): unknown {
    try {
      return this.localStorageService.getItem(`worldbuilding_sync_${storyId}`);
    } catch (error) {
      console.error('Failed to retrieve worldbuilding sync data:', error);
      return null;
    }
  }

  /**
   * Clear worldbuilding sync data
   */
  clearWorldbuildingSync(storyId: string): void {
    try {
      localStorage.removeItem(`worldbuilding_sync_${storyId}`);
      this.worldbuildingUpdatedSubject.next('');
    } catch (error) {
      console.error('Failed to clear worldbuilding sync data:', error);
    }
  }

  /**
   * Manually trigger worldbuilding update
   */
  updateWorldbuilding(worldbuilding: string): void {
    this.worldbuildingUpdatedSubject.next(worldbuilding);
  }

  /**
   * Get current worldbuilding content
   */
  getCurrentWorldbuilding(): string {
    return this.worldbuildingUpdatedSubject.value;
  }

  /**
   * Check if sync is in progress
   */
  isSyncInProgress(): boolean {
    return this.syncInProgressSubject.value;
  }
}
