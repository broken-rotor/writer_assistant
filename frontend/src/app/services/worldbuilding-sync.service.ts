import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { BehaviorSubject, Observable, throwError } from 'rxjs';
import { debounceTime, distinctUntilChanged, catchError, retry, timeout } from 'rxjs/operators';

import { ConversationService } from './conversation.service';
import { LocalStorageService } from './local-storage.service';
import { WorldbuildingValidatorService, ValidationResult } from './worldbuilding-validator.service';
import { ChatMessage } from '../models/story.model';
import { environment } from '../../environments/environment';

export interface WorldbuildingSyncConfig {
  storyId: string;
  syncInterval?: number; // milliseconds
  maxSummaryLength?: number;
  includeAssistantMessages?: boolean;
  includeUserMessages?: boolean;
  enableBackendSync?: boolean;
  retryAttempts?: number;
  timeoutMs?: number;
}

export interface BackendSyncRequest {
  story_id: string;
  messages: ChatMessage[];
  current_worldbuilding: string;
  force_sync?: boolean;
}

export interface BackendSyncResponse {
  success: boolean;
  updated_worldbuilding: string;
  metadata: {
    story_id: string;
    messages_processed: number;
    content_length: number;
    topics_identified: string[];
    sync_timestamp: string;
    quality_score: number;
  };
  errors: string[];
}

export interface SyncError {
  type: 'network' | 'validation' | 'server' | 'timeout' | 'unknown';
  message: string;
  details?: any;
  recoverable: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class WorldbuildingSyncService {
  private worldbuildingUpdatedSubject = new BehaviorSubject<string>('');
  private syncInProgressSubject = new BehaviorSubject<boolean>(false);
  private syncErrorSubject = new BehaviorSubject<SyncError | null>(null);
  
  // Services
  private conversationService = inject(ConversationService);
  private localStorageService = inject(LocalStorageService);
  private validatorService = inject(WorldbuildingValidatorService);
  private http = inject(HttpClient);

  // Configuration
  private defaultConfig: Partial<WorldbuildingSyncConfig> = {
    syncInterval: 2000, // 2 seconds debounce
    maxSummaryLength: 5000, // characters
    includeAssistantMessages: true,
    includeUserMessages: true,
    enableBackendSync: true,
    retryAttempts: 3,
    timeoutMs: 10000
  };

  private readonly apiBaseUrl = environment.apiUrl || 'http://localhost:8000/api/v1';

  // Observables
  public worldbuildingUpdated$ = this.worldbuildingUpdatedSubject.asObservable().pipe(
    debounceTime(this.defaultConfig.syncInterval!),
    distinctUntilChanged()
  );
  
  public syncInProgress$ = this.syncInProgressSubject.asObservable();
  public syncError$ = this.syncErrorSubject.asObservable();

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
      this.syncErrorSubject.next(null);

      const syncConfig = { ...this.defaultConfig, ...config, storyId };
      const messages = this.conversationService.getCurrentBranchMessages();
      
      if (messages.length === 0) {
        // No messages, return current worldbuilding
        return currentWorldbuilding;
      }

      let updatedWorldbuilding: string;

      // Try backend sync first if enabled
      if (syncConfig.enableBackendSync) {
        try {
          updatedWorldbuilding = await this.syncWithBackend(storyId, messages, currentWorldbuilding, syncConfig);
        } catch (error) {
          console.warn('Backend sync failed, falling back to local sync:', error);
          
          // Set recoverable error
          this.syncErrorSubject.next({
            type: 'network',
            message: 'Backend sync unavailable, using local processing',
            details: error,
            recoverable: true
          });

          // Fallback to local sync
          updatedWorldbuilding = await this.syncLocally(messages, currentWorldbuilding, syncConfig);
        }
      } else {
        // Use local sync only
        updatedWorldbuilding = await this.syncLocally(messages, currentWorldbuilding, syncConfig);
      }

      // Validate the result
      const validation = this.validatorService.validateContent(updatedWorldbuilding);
      if (!validation.isValid) {
        console.warn('Worldbuilding validation failed:', validation.errors);
        
        // Sanitize content if validation fails
        updatedWorldbuilding = this.validatorService.sanitizeContent(updatedWorldbuilding);
        
        this.syncErrorSubject.next({
          type: 'validation',
          message: 'Content validation issues detected and fixed',
          details: validation.errors,
          recoverable: true
        });
      }

      // Update the subject to notify subscribers
      this.worldbuildingUpdatedSubject.next(updatedWorldbuilding);

      // Store the updated worldbuilding
      this.storeWorldbuildingSync(storyId, updatedWorldbuilding);

      return updatedWorldbuilding;

    } catch (error) {
      console.error('Failed to sync worldbuilding from conversation:', error);
      
      this.syncErrorSubject.next({
        type: 'unknown',
        message: 'Sync failed unexpectedly',
        details: error,
        recoverable: false
      });
      
      throw error;
    } finally {
      this.syncInProgressSubject.next(false);
    }
  }

  /**
   * Sync with backend API
   */
  private async syncWithBackend(
    storyId: string,
    messages: ChatMessage[],
    currentWorldbuilding: string,
    config: WorldbuildingSyncConfig
  ): Promise<string> {
    const request: BackendSyncRequest = {
      story_id: storyId,
      messages: messages,
      current_worldbuilding: currentWorldbuilding,
      force_sync: false
    };

    return this.http.post<BackendSyncResponse>(`${this.apiBaseUrl}/worldbuilding/sync`, request)
      .pipe(
        timeout(config.timeoutMs!),
        retry(config.retryAttempts!),
        catchError(this.handleHttpError.bind(this))
      )
      .toPromise()
      .then(response => {
        if (!response || !response.success) {
          throw new Error(response?.errors?.join(', ') || 'Backend sync failed');
        }
        return response.updated_worldbuilding;
      });
  }

  /**
   * Sync locally using frontend processing
   */
  private async syncLocally(
    messages: ChatMessage[],
    currentWorldbuilding: string,
    config: WorldbuildingSyncConfig
  ): Promise<string> {
    // Extract worldbuilding information from messages
    const extractedWorldbuilding = this.extractWorldbuildingFromMessages(
      messages, 
      config
    );

    // Merge with existing worldbuilding
    return this.mergeWorldbuildingContent(
      currentWorldbuilding,
      extractedWorldbuilding,
      config
    );
  }

  /**
   * Handle HTTP errors with proper error classification
   */
  private handleHttpError(error: HttpErrorResponse): Observable<never> {
    let syncError: SyncError;

    if (error.status === 0) {
      // Network error
      syncError = {
        type: 'network',
        message: 'Network connection failed',
        details: error,
        recoverable: true
      };
    } else if (error.status >= 400 && error.status < 500) {
      // Client error
      syncError = {
        type: 'validation',
        message: error.error?.detail || 'Request validation failed',
        details: error,
        recoverable: false
      };
    } else if (error.status >= 500) {
      // Server error
      syncError = {
        type: 'server',
        message: 'Server error occurred',
        details: error,
        recoverable: true
      };
    } else {
      // Unknown error
      syncError = {
        type: 'unknown',
        message: 'Unknown error occurred',
        details: error,
        recoverable: false
      };
    }

    this.syncErrorSubject.next(syncError);
    return throwError(syncError);
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
      this.localStorageService.removeItem(`worldbuilding_sync_${storyId}`);
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

  /**
   * Get current sync error
   */
  getCurrentSyncError(): SyncError | null {
    return this.syncErrorSubject.value;
  }

  /**
   * Clear current sync error
   */
  clearSyncError(): void {
    this.syncErrorSubject.next(null);
  }

  /**
   * Validate worldbuilding content
   */
  validateWorldbuilding(content: string): ValidationResult {
    return this.validatorService.validateContent(content);
  }

  /**
   * Get content suggestions
   */
  getContentSuggestions(content: string): string[] {
    return this.validatorService.suggestImprovements(content);
  }

  /**
   * Get content statistics
   */
  getContentStatistics(content: string) {
    return this.validatorService.getContentStatistics(content);
  }

  /**
   * Force sync with backend (bypass local fallback)
   */
  async forceSyncWithBackend(
    storyId: string,
    currentWorldbuilding = ''
  ): Promise<string> {
    const messages = this.conversationService.getCurrentBranchMessages();
    const config = { ...this.defaultConfig, storyId, enableBackendSync: true };

    return this.syncWithBackend(storyId, messages, currentWorldbuilding, config as WorldbuildingSyncConfig);
  }

  /**
   * Test backend connectivity
   */
  async testBackendConnection(): Promise<boolean> {
    try {
      await this.http.get(`${this.apiBaseUrl}/worldbuilding/status/test`)
        .pipe(timeout(5000))
        .toPromise();
      return true;
    } catch (error) {
      console.warn('Backend connectivity test failed:', error);
      return false;
    }
  }
}
