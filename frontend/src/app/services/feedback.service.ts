import { Injectable, inject } from '@angular/core';
import { BehaviorSubject, Observable, Subject, map, catchError, of } from 'rxjs';

import { 
  EnhancedFeedbackItem, 
  CharacterFeedback, 
  RaterFeedback,
  Character,
  Rater,
  Story,
  FeedbackItem,
  ChapterComposeState,
  ConversationThread
} from '../models/story.model';
import { GenerationService } from './generation.service';
import { ConversationService } from './conversation.service';
import { PhaseType } from './phase-state.service';
import { LocalStorageService } from './local-storage.service';

export interface FeedbackRequestStatus {
  pendingRequests: string[];
  completedRequests: string[];
  failedRequests: string[];
}

export interface FeedbackChatMessage {
  selectedFeedback: EnhancedFeedbackItem[];
  userComment?: string;
  timestamp: Date;
}

@Injectable({
  providedIn: 'root'
})
export class FeedbackService {
  private generationService = inject(GenerationService);
  private conversationService = inject(ConversationService);
  private localStorageService = inject(LocalStorageService);

  // Observables for component communication
  private feedbackUpdatedSubject = new Subject<void>();
  private requestStatusSubject = new BehaviorSubject<FeedbackRequestStatus>({
    pendingRequests: [],
    completedRequests: [],
    failedRequests: []
  });

  public feedbackUpdated$ = this.feedbackUpdatedSubject.asObservable();
  public requestStatus$ = this.requestStatusSubject.asObservable();

  // Internal state
  private feedbackCache = new Map<string, EnhancedFeedbackItem[]>();
  private requestStatus: FeedbackRequestStatus = {
    pendingRequests: [],
    completedRequests: [],
    failedRequests: []
  };

  /**
   * Get available feedback for a specific story, chapter, and phase
   */
  getAvailableFeedback(storyId: string, chapterNumber: number, phase: PhaseType): EnhancedFeedbackItem[] {
    const cacheKey = `${storyId}_${chapterNumber}_${phase}`;
    
    if (this.feedbackCache.has(cacheKey)) {
      return this.feedbackCache.get(cacheKey) || [];
    }

    // Load feedback from story data
    const story = this.localStorageService.loadStory(storyId);
    if (!story) return [];

    const feedback = this.extractFeedbackFromStory(story, chapterNumber, phase);
    this.feedbackCache.set(cacheKey, feedback);
    
    return feedback;
  }

  /**
   * Request character feedback
   */
  requestCharacterFeedback(story: Story, character: Character, chapterNumber: number): Observable<boolean> {
    const requestId = `character_${character.id}_${chapterNumber}`;
    
    // Add to pending requests
    this.addPendingRequest(requestId);

    // Get plot point for the chapter
    const plotPoint = this.getPlotPointForChapter(story, chapterNumber);

    return this.generationService.requestCharacterFeedback(story, character, plotPoint).pipe(
      map(response => {
        // Convert response to enhanced feedback items
        const enhancedFeedback = this.convertCharacterFeedbackToEnhanced(
          response, 
          character.name, 
          chapterNumber
        );

        // Store feedback
        this.storeFeedback(story.id, chapterNumber, enhancedFeedback);
        
        // Update request status
        this.completeRequest(requestId);
        this.notifyFeedbackUpdated();
        
        return true;
      }),
      catchError(error => {
        console.error('Error requesting character feedback:', error);
        this.failRequest(requestId);
        return of(false);
      })
    );
  }

  /**
   * Request rater feedback
   */
  requestRaterFeedback(story: Story, rater: Rater, chapterNumber: number): Observable<boolean> {
    const requestId = `rater_${rater.id}_${chapterNumber}`;
    
    // Add to pending requests
    this.addPendingRequest(requestId);

    // Get plot point for the chapter
    const plotPoint = this.getPlotPointForChapter(story, chapterNumber);

    return this.generationService.requestRaterFeedback(story, rater, plotPoint).pipe(
      map(response => {
        // Convert response to enhanced feedback items
        const enhancedFeedback = this.convertRaterFeedbackToEnhanced(
          response, 
          rater.name, 
          chapterNumber
        );

        // Store feedback
        this.storeFeedback(story.id, chapterNumber, enhancedFeedback);
        
        // Update request status
        this.completeRequest(requestId);
        this.notifyFeedbackUpdated();
        
        return true;
      }),
      catchError(error => {
        console.error('Error requesting rater feedback:', error);
        this.failRequest(requestId);
        return of(false);
      })
    );
  }

  /**
   * Add selected feedback to chat conversation
   */
  addFeedbackToChat(
    storyId: string, 
    chapterNumber: number, 
    phase: PhaseType,
    selectedFeedback: EnhancedFeedbackItem[], 
    userComment?: string
  ): Observable<boolean> {
    try {
      // Create chat message content
      const messageContent = this.formatFeedbackForChat(selectedFeedback, userComment);
      
      // Send message to conversation service
      const message = this.conversationService.sendMessage(
        messageContent, 
        'user',
        {
          metadata: {
            feedbackItems: selectedFeedback.map(item => item.id),
            feedbackCount: selectedFeedback.length,
            hasUserComment: !!userComment
          }
        }
      );

      // Mark feedback as incorporated (optional - depends on business logic)
      this.markFeedbackAsIncorporated(storyId, selectedFeedback.map(item => item.id));

      return of(true);
    } catch (error) {
      console.error('Error adding feedback to chat:', error);
      return of(false);
    }
  }

  /**
   * Mark feedback items as incorporated
   */
  markFeedbackAsIncorporated(storyId: string, feedbackIds: string[]): void {
    // Update feedback status in cache
    this.feedbackCache.forEach((feedback, key) => {
      if (key.startsWith(storyId)) {
        feedback.forEach(item => {
          if (feedbackIds.includes(item.id)) {
            item.status = 'incorporated';
            item.metadata.lastModified = new Date();
          }
        });
      }
    });

    // Update story data
    const story = this.localStorageService.loadStory(storyId);
    if (story) {
      // Update incorporated feedback in legacy structure
      feedbackIds.forEach(feedbackId => {
        const feedbackItem = this.findFeedbackById(feedbackId);
        if (feedbackItem) {
          const legacyItem: FeedbackItem = {
            source: feedbackItem.source,
            type: feedbackItem.type,
            content: feedbackItem.content,
            incorporated: true
          };
          
          // Add to incorporated feedback if not already present
          const existingIndex = story.chapterCreation.incorporatedFeedback.findIndex(
            (item: any) => item.source === legacyItem.source && 
                   item.content === legacyItem.content
          );
          
          if (existingIndex === -1) {
            story.chapterCreation.incorporatedFeedback.push(legacyItem);
          } else {
            story.chapterCreation.incorporatedFeedback[existingIndex].incorporated = true;
          }
        }
      });

      this.localStorageService.saveStory(story);
    }

    this.notifyFeedbackUpdated();
  }

  /**
   * Clear feedback cache for a specific story/chapter/phase
   */
  clearFeedbackCache(storyId?: string, chapterNumber?: number, phase?: PhaseType): void {
    if (storyId && chapterNumber && phase) {
      const cacheKey = `${storyId}_${chapterNumber}_${phase}`;
      this.feedbackCache.delete(cacheKey);
    } else if (storyId) {
      // Clear all cache entries for the story
      const keysToDelete = Array.from(this.feedbackCache.keys()).filter(key => 
        key.startsWith(storyId)
      );
      keysToDelete.forEach(key => this.feedbackCache.delete(key));
    } else {
      // Clear entire cache
      this.feedbackCache.clear();
    }
    
    this.notifyFeedbackUpdated();
  }

  // Private helper methods

  private extractFeedbackFromStory(story: Story, chapterNumber: number, phase: PhaseType): EnhancedFeedbackItem[] {
    const feedback: EnhancedFeedbackItem[] = [];

    // Extract from legacy incorporated feedback
    story.chapterCreation.incorporatedFeedback.forEach((item, index) => {
      feedback.push({
        id: `legacy_${index}_${Date.now()}`,
        source: item.source,
        type: item.type,
        content: item.content,
        incorporated: item.incorporated,
        phase: phase,
        priority: 'medium', // Default priority
        status: item.incorporated ? 'incorporated' : 'pending',
        metadata: {
          created: new Date(),
          lastModified: new Date()
        }
      });
    });

    // Extract from feedback requests
    story.chapterCreation.feedbackRequests.forEach((request, agentId) => {
      if (request.status === 'ready') {
        const agentFeedback = this.convertAgentFeedbackToEnhanced(
          request.feedback, 
          agentId, 
          chapterNumber
        );
        feedback.push(...agentFeedback);
      }
    });

    // Extract from three-phase system if available
    if (story.chapterCompose) {
      const phaseData = story.chapterCompose.phases.chapterDetailer;
      if (phaseData.feedbackIntegration) {
        feedback.push(...phaseData.feedbackIntegration.pendingFeedback);
        feedback.push(...phaseData.feedbackIntegration.incorporatedFeedback);
      }
    }

    return feedback;
  }

  private convertCharacterFeedbackToEnhanced(
    response: any, 
    characterName: string, 
    chapterNumber: number
  ): EnhancedFeedbackItem[] {
    const feedback: EnhancedFeedbackItem[] = [];
    const now = new Date();

    // Convert each type of character feedback
    const feedbackTypes = [
      { key: 'actions', type: 'action' as const },
      { key: 'dialog', type: 'dialog' as const },
      { key: 'physicalSensations', type: 'sensation' as const },
      { key: 'emotions', type: 'emotion' as const },
      { key: 'internalMonologue', type: 'thought' as const }
    ];

    feedbackTypes.forEach(({ key, type }) => {
      const items = response.feedback[key] || [];
      items.forEach((content: string, index: number) => {
        feedback.push({
          id: `char_${characterName}_${type}_${chapterNumber}_${index}_${Date.now()}`,
          source: characterName,
          type: type,
          content: content,
          incorporated: false,
          phase: 'chapter_detail',
          priority: 'medium',
          status: 'pending',
          metadata: {
            created: now,
            lastModified: now
          }
        });
      });
    });

    return feedback;
  }

  private convertRaterFeedbackToEnhanced(
    response: any, 
    raterName: string, 
    chapterNumber: number
  ): EnhancedFeedbackItem[] {
    const feedback: EnhancedFeedbackItem[] = [];
    const now = new Date();

    // Add opinion as a suggestion
    if (response.feedback.opinion) {
      feedback.push({
        id: `rater_${raterName}_opinion_${chapterNumber}_${Date.now()}`,
        source: raterName,
        type: 'suggestion',
        content: response.feedback.opinion,
        incorporated: false,
        phase: 'chapter_detail',
        priority: 'medium',
        status: 'pending',
        metadata: {
          created: now,
          lastModified: now
        }
      });
    }

    // Add suggestions
    const suggestions = response.feedback.suggestions || [];
    suggestions.forEach((suggestion: any, index: number) => {
      const content = typeof suggestion === 'string' ? suggestion : suggestion.suggestion;
      const priority = suggestion.priority || 'medium';
      
      feedback.push({
        id: `rater_${raterName}_suggestion_${chapterNumber}_${index}_${Date.now()}`,
        source: raterName,
        type: 'suggestion',
        content: content,
        incorporated: false,
        phase: 'chapter_detail',
        priority: priority,
        status: 'pending',
        metadata: {
          created: now,
          lastModified: now
        }
      });
    });

    return feedback;
  }

  private convertAgentFeedbackToEnhanced(
    feedback: CharacterFeedback | RaterFeedback, 
    agentId: string, 
    chapterNumber: number
  ): EnhancedFeedbackItem[] {
    if ('actions' in feedback) {
      // Character feedback
      return this.convertCharacterFeedbackToEnhanced(
        { feedback }, 
        feedback.characterName || agentId, 
        chapterNumber
      );
    } else {
      // Rater feedback
      return this.convertRaterFeedbackToEnhanced(
        { feedback }, 
        feedback.raterName || agentId, 
        chapterNumber
      );
    }
  }

  private formatFeedbackForChat(selectedFeedback: EnhancedFeedbackItem[], userComment?: string): string {
    let message = '';

    if (userComment) {
      message += `${userComment}\n\n`;
    }

    message += `**Selected Feedback (${selectedFeedback.length} items):**\n\n`;

    // Group feedback by source
    const feedbackBySource = new Map<string, EnhancedFeedbackItem[]>();
    selectedFeedback.forEach(item => {
      if (!feedbackBySource.has(item.source)) {
        feedbackBySource.set(item.source, []);
      }
      feedbackBySource.get(item.source)!.push(item);
    });

    // Format each source's feedback
    feedbackBySource.forEach((items, source) => {
      message += `**${source}:**\n`;
      items.forEach(item => {
        message += `- ${item.type}: ${item.content}\n`;
      });
      message += '\n';
    });

    return message.trim();
  }

  private storeFeedback(storyId: string, chapterNumber: number, feedback: EnhancedFeedbackItem[]): void {
    // Update cache
    const cacheKey = `${storyId}_${chapterNumber}_chapter-detailer`;
    const existingFeedback = this.feedbackCache.get(cacheKey) || [];
    this.feedbackCache.set(cacheKey, [...existingFeedback, ...feedback]);

    // Update story data
    const story = this.localStorageService.loadStory(storyId);
    if (story && story.chapterCompose) {
      const phaseData = story.chapterCompose.phases.chapterDetailer;
      phaseData.feedbackIntegration.pendingFeedback.push(...feedback);
      this.localStorageService.saveStory(story);
    }
  }

  private getPlotPointForChapter(story: Story, chapterNumber: number): string {
    // Try to get from current chapter creation state
    if (story.chapterCreation.plotPoint) {
      return story.chapterCreation.plotPoint;
    }

    // Try to get from existing chapters
    const chapter = story.story.chapters.find(ch => ch.number === chapterNumber);
    if (chapter) {
      return chapter.plotPoint;
    }

    // Default fallback
    return `Chapter ${chapterNumber} development`;
  }

  private findFeedbackById(feedbackId: string): EnhancedFeedbackItem | null {
    for (const feedback of this.feedbackCache.values()) {
      const item = feedback.find(f => f.id === feedbackId);
      if (item) return item;
    }
    return null;
  }

  private addPendingRequest(requestId: string): void {
    this.requestStatus.pendingRequests.push(requestId);
    this.requestStatusSubject.next({ ...this.requestStatus });
  }

  private completeRequest(requestId: string): void {
    this.requestStatus.pendingRequests = this.requestStatus.pendingRequests.filter(id => id !== requestId);
    this.requestStatus.completedRequests.push(requestId);
    this.requestStatusSubject.next({ ...this.requestStatus });
  }

  private failRequest(requestId: string): void {
    this.requestStatus.pendingRequests = this.requestStatus.pendingRequests.filter(id => id !== requestId);
    this.requestStatus.failedRequests.push(requestId);
    this.requestStatusSubject.next({ ...this.requestStatus });
  }

  private notifyFeedbackUpdated(): void {
    this.feedbackUpdatedSubject.next();
  }

  // ============================================================================
  // PHASE-AWARE FEEDBACK METHODS FOR THREE-PHASE CHAPTER COMPOSE SYSTEM (WRI-49)
  // ============================================================================

  /**
   * Request character feedback with phase context
   */
  requestCharacterFeedbackWithPhase(
    story: Story,
    character: Character,
    chapterNumber: number,
    chapterComposeState?: ChapterComposeState,
    conversationThread?: ConversationThread,
    additionalInstructions?: string
  ): Observable<EnhancedFeedbackItem[]> {
    const requestId = `character_${character.id}_${Date.now()}`;
    this.addPendingRequest(requestId);

    const plotPoint = this.getPlotPointForChapter(story, chapterNumber);

    return this.generationService.requestCharacterFeedbackWithPhase(
      story,
      character,
      plotPoint,
      chapterComposeState,
      conversationThread,
      additionalInstructions
    ).pipe(
      map(response => {
        const enhancedFeedback = this.convertCharacterFeedbackToEnhanced(
          response,
          character.name,
          chapterNumber
        );

        // Store feedback with phase context
        this.storeFeedbackWithPhase(story.id, chapterNumber, enhancedFeedback, chapterComposeState);
        this.completeRequest(requestId);
        this.notifyFeedbackUpdated();

        return enhancedFeedback;
      }),
      catchError(error => {
        console.error('Character feedback request failed:', error);
        this.failRequest(requestId);
        return of([]);
      })
    );
  }

  /**
   * Request rater feedback with phase context
   */
  requestRaterFeedbackWithPhase(
    story: Story,
    rater: Rater,
    chapterNumber: number,
    chapterComposeState?: ChapterComposeState,
    conversationThread?: ConversationThread,
    additionalInstructions?: string
  ): Observable<EnhancedFeedbackItem[]> {
    const requestId = `rater_${rater.id}_${Date.now()}`;
    this.addPendingRequest(requestId);

    const plotPoint = this.getPlotPointForChapter(story, chapterNumber);

    return this.generationService.requestRaterFeedbackWithPhase(
      story,
      rater,
      plotPoint,
      chapterComposeState,
      conversationThread,
      additionalInstructions
    ).pipe(
      map(response => {
        const enhancedFeedback = this.convertRaterFeedbackToEnhanced(
          response,
          rater.name,
          chapterNumber
        );

        // Store feedback with phase context
        this.storeFeedbackWithPhase(story.id, chapterNumber, enhancedFeedback, chapterComposeState);
        this.completeRequest(requestId);
        this.notifyFeedbackUpdated();

        return enhancedFeedback;
      }),
      catchError(error => {
        console.error('Rater feedback request failed:', error);
        this.failRequest(requestId);
        return of([]);
      })
    );
  }

  /**
   * Request feedback from multiple agents with phase context
   */
  requestMultipleAgentFeedbackWithPhase(
    story: Story,
    agents: { type: 'character' | 'rater'; agent: Character | Rater }[],
    chapterNumber: number,
    chapterComposeState?: ChapterComposeState,
    conversationThread?: ConversationThread,
    additionalInstructions?: string
  ): Observable<EnhancedFeedbackItem[]> {
    const feedbackRequests = agents.map(({ type, agent }) => {
      if (type === 'character') {
        return this.requestCharacterFeedbackWithPhase(
          story,
          agent as Character,
          chapterNumber,
          chapterComposeState,
          conversationThread,
          additionalInstructions
        );
      } else {
        return this.requestRaterFeedbackWithPhase(
          story,
          agent as Rater,
          chapterNumber,
          chapterComposeState,
          conversationThread,
          additionalInstructions
        );
      }
    });

    // Combine all feedback requests
    return new Observable<EnhancedFeedbackItem[]>(observer => {
      const allFeedback: EnhancedFeedbackItem[] = [];
      let completedRequests = 0;

      feedbackRequests.forEach(request => {
        request.subscribe({
          next: (feedback) => {
            allFeedback.push(...feedback);
            completedRequests++;

            if (completedRequests === feedbackRequests.length) {
              observer.next(allFeedback);
              observer.complete();
            }
          },
          error: (error) => {
            console.error('Agent feedback request failed:', error);
            completedRequests++;

            if (completedRequests === feedbackRequests.length) {
              observer.next(allFeedback);
              observer.complete();
            }
          }
        });
      });
    });
  }

  /**
   * Store feedback with phase context
   */
  private storeFeedbackWithPhase(
    storyId: string,
    chapterNumber: number,
    feedback: EnhancedFeedbackItem[],
    chapterComposeState?: ChapterComposeState
  ): void {
    // Add phase context to feedback metadata
    const enhancedFeedback = feedback.map(item => ({
      ...item,
      metadata: {
        ...item.metadata,
        phase_context: chapterComposeState ? {
          current_phase: chapterComposeState.currentPhase,
          plot_outline: chapterComposeState.phases.plotOutline.status,
          chapter_detail: chapterComposeState.phases.chapterDetailer.status,
          final_edit: chapterComposeState.phases.finalEdit.status
        } : undefined
      }
    }));

    // Use existing storage method with enhanced feedback
    this.storeFeedback(storyId, chapterNumber, enhancedFeedback);
  }

  /**
   * Get feedback filtered by phase
   */
  getFeedbackByPhase(
    storyId: string,
    chapterNumber: number,
    phase: 'plot_outline' | 'chapter_detail' | 'final_edit'
  ): EnhancedFeedbackItem[] {
    const cacheKey = `${storyId}_${chapterNumber}_chapter-detailer`;
    const allFeedback = this.feedbackCache.get(cacheKey) || [];

    return allFeedback.filter(item => 
      item.metadata?.phase_context?.current_phase === phase
    );
  }

  /**
   * Get feedback statistics by phase
   */
  getFeedbackStatsByPhase(
    storyId: string,
    chapterNumber: number
  ): Record<string, { total: number; incorporated: number; pending: number }> {
    const cacheKey = `${storyId}_${chapterNumber}_chapter-detailer`;
    const allFeedback = this.feedbackCache.get(cacheKey) || [];

    const stats: Record<string, { total: number; incorporated: number; pending: number }> = {};

    allFeedback.forEach(item => {
      const phase = item.metadata?.phase_context?.current_phase || 'unknown';
      
      if (!stats[phase]) {
        stats[phase] = { total: 0, incorporated: 0, pending: 0 };
      }

      stats[phase].total++;
      if (item.incorporated) {
        stats[phase].incorporated++;
      } else {
        stats[phase].pending++;
      }
    });

    return stats;
  }
}
