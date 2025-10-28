import { Injectable, inject } from '@angular/core';
import { BehaviorSubject, Observable, Subject, forkJoin, map, catchError, of } from 'rxjs';

import {
  ReviewItem,
  Story,
  EditorSuggestion,
  ChapterComposeState,
  ConversationThread
} from '../models/story.model';
import { GenerationService } from './generation.service';
import { FeedbackService } from './feedback.service';
import { ConversationService } from './conversation.service';
import { LocalStorageService } from './local-storage.service';

export interface ReviewRequestStatus {
  pendingRequests: string[];
  completedRequests: string[];
  failedRequests: string[];
  totalRequests: number;
  completedCount: number;
}

export interface QualityScore {
  overall: number; // 0-100
  categories: {
    grammar: number;
    style: number;
    consistency: number;
    flow: number;
    character: number;
    plot: number;
  };
  readyToSave: boolean;
  improvements: string[];
}

export interface ComprehensiveReviewRequest {
  includeCharacters: boolean;
  includeRaters: boolean;
  includeEditor: boolean;
  targetedAspects?: string[];
}

@Injectable({
  providedIn: 'root'
})
export class ReviewService {
  private generationService = inject(GenerationService);
  private feedbackService = inject(FeedbackService);
  private conversationService = inject(ConversationService);
  private localStorageService = inject(LocalStorageService);

  // Observables for component communication
  private reviewsUpdatedSubject = new Subject<void>();
  private requestStatusSubject = new BehaviorSubject<ReviewRequestStatus>({
    pendingRequests: [],
    completedRequests: [],
    failedRequests: [],
    totalRequests: 0,
    completedCount: 0
  });
  private qualityScoreSubject = new BehaviorSubject<QualityScore | null>(null);

  public reviewsUpdated$ = this.reviewsUpdatedSubject.asObservable();
  public requestStatus$ = this.requestStatusSubject.asObservable();
  public qualityScore$ = this.qualityScoreSubject.asObservable();

  // Internal state
  private reviewCache = new Map<string, ReviewItem[]>();
  private requestStatus: ReviewRequestStatus = {
    pendingRequests: [],
    completedRequests: [],
    failedRequests: [],
    totalRequests: 0,
    completedCount: 0
  };

  /**
   * Add a pending request to track
   */
  private addPendingRequest(requestId: string): void {
    this.requestStatus.pendingRequests.push(requestId);
    this.requestStatus.totalRequests++;
    this.requestStatusSubject.next(this.requestStatus);
  }

  /**
   * Mark a request as completed
   */
  private completeRequest(requestId: string): void {
    const index = this.requestStatus.pendingRequests.indexOf(requestId);
    if (index > -1) {
      this.requestStatus.pendingRequests.splice(index, 1);
      this.requestStatus.completedRequests.push(requestId);
      this.requestStatus.completedCount++;
      this.requestStatusSubject.next(this.requestStatus);
    }
  }

  /**
   * Mark a request as failed
   */
  private failRequest(requestId: string): void {
    const index = this.requestStatus.pendingRequests.indexOf(requestId);
    if (index > -1) {
      this.requestStatus.pendingRequests.splice(index, 1);
      this.requestStatus.failedRequests.push(requestId);
      this.requestStatusSubject.next(this.requestStatus);
    }
  }

  /**
   * Get available reviews for Phase 3 (final-edit)
   */
  getAvailableReviews(storyId: string, chapterNumber: number): ReviewItem[] {
    const cacheKey = `${storyId}_${chapterNumber}_final-edit`;
    
    if (this.reviewCache.has(cacheKey)) {
      return this.reviewCache.get(cacheKey) || [];
    }

    // Load reviews from story data
    const story = this.localStorageService.loadStory(storyId);
    if (!story || !story.chapterCompose) return [];

    const finalEditPhase = story.chapterCompose.phases.finalEdit;
    const reviews = finalEditPhase.reviewSelection.availableReviews;
    
    this.reviewCache.set(cacheKey, reviews);
    return reviews;
  }

  /**
   * Request comprehensive reviews from all agents
   */
  requestComprehensiveReviews(
    story: Story, 
    chapterNumber: number, 
    chapterContent: string,
    options: ComprehensiveReviewRequest = {
      includeCharacters: true,
      includeRaters: true,
      includeEditor: true
    }
  ): Observable<boolean> {
    const requests: Observable<any>[] = [];
    const requestIds: string[] = [];

    // Reset request status
    this.requestStatus = {
      pendingRequests: [],
      completedRequests: [],
      failedRequests: [],
      totalRequests: 0,
      completedCount: 0
    };

    // Request character feedback
    if (options.includeCharacters) {
      const availableCharacters = Array.from(story.characters.values()).filter(char => !char.isHidden);
      availableCharacters.forEach(character => {
        const requestId = `character_${character.id}_${chapterNumber}`;
        requestIds.push(requestId);
        requests.push(
          this.feedbackService.requestCharacterFeedback(story, character, chapterNumber)
        );
      });
    }

    // Request rater feedback
    if (options.includeRaters) {
      const availableRaters = Array.from(story.raters.values()).filter(rater => rater.enabled);
      availableRaters.forEach(rater => {
        const requestId = `rater_${rater.id}_${chapterNumber}`;
        requestIds.push(requestId);
        requests.push(
          this.feedbackService.requestRaterFeedback(story, rater, chapterNumber)
        );
      });
    }

    // Request editor review
    if (options.includeEditor) {
      const requestId = `editor_${chapterNumber}`;
      requestIds.push(requestId);
      requests.push(
        this.generationService.requestEditorReview(story, chapterContent)
      );
    }

    // Update request status
    this.requestStatus.totalRequests = requests.length;
    this.requestStatus.pendingRequests = [...requestIds];
    this.requestStatusSubject.next({ ...this.requestStatus });

    if (requests.length === 0) {
      return of(true);
    }

    // Execute all requests
    return forkJoin(requests).pipe(
      map(responses => {
        // Process responses and convert to ReviewItems
        this.processComprehensiveReviewResponses(
          story.id, 
          chapterNumber, 
          responses, 
          requestIds, 
          options
        );
        
        // Update request status
        this.requestStatus.completedRequests = [...requestIds];
        this.requestStatus.pendingRequests = [];
        this.requestStatus.completedCount = requestIds.length;
        this.requestStatusSubject.next({ ...this.requestStatus });
        
        this.notifyReviewsUpdated();
        return true;
      }),
      catchError(error => {
        console.error('Error requesting comprehensive reviews:', error);
        
        // Mark all as failed
        this.requestStatus.failedRequests = [...requestIds];
        this.requestStatus.pendingRequests = [];
        this.requestStatusSubject.next({ ...this.requestStatus });
        
        return of(false);
      })
    );
  }

  /**
   * Add selected reviews to chat conversation
   */
  addReviewsToChat(
    storyId: string,
    chapterNumber: number,
    selectedReviews: ReviewItem[],
    userComment?: string
  ): Observable<boolean> {
    try {
      // Create chat message content
      const messageContent = this.formatReviewsForChat(selectedReviews, userComment);
      
      // Send message to conversation service
      this.conversationService.sendMessage(
        messageContent,
        'user',
        {
          metadata: {
            reviewItems: selectedReviews.map(item => item.id),
            reviewCount: selectedReviews.length,
            hasUserComment: !!userComment,
            phase: 'final-edit'
          }
        }
      );

      // Mark reviews as applied
      this.markReviewsAsApplied(storyId, selectedReviews.map(item => item.id));

      return of(true);
    } catch (error) {
      console.error('Error adding reviews to chat:', error);
      return of(false);
    }
  }

  /**
   * Mark reviews as applied
   */
  markReviewsAsApplied(storyId: string, reviewIds: string[]): void {
    // Update cache
    this.reviewCache.forEach((reviews, key) => {
      if (key.startsWith(storyId)) {
        reviews.forEach(item => {
          if (reviewIds.includes(item.id)) {
            item.status = 'accepted';
          }
        });
      }
    });

    // Update story data
    const story = this.localStorageService.loadStory(storyId);
    if (story && story.chapterCompose) {
      const finalEditPhase = story.chapterCompose.phases.finalEdit;
      
      // Move from selectedReviews to appliedReviews
      reviewIds.forEach(reviewId => {
        const selectedIndex = finalEditPhase.reviewSelection.selectedReviews.indexOf(reviewId);
        if (selectedIndex !== -1) {
          finalEditPhase.reviewSelection.selectedReviews.splice(selectedIndex, 1);
        }
        
        if (!finalEditPhase.reviewSelection.appliedReviews.includes(reviewId)) {
          finalEditPhase.reviewSelection.appliedReviews.push(reviewId);
        }
      });

      // Update progress
      finalEditPhase.progress.reviewsApplied = finalEditPhase.reviewSelection.appliedReviews.length;
      finalEditPhase.progress.lastActivity = new Date();

      this.localStorageService.saveStory(story);
    }

    this.notifyReviewsUpdated();
  }

  /**
   * Calculate quality score based on available reviews
   */
  calculateQualityScore(reviews: ReviewItem[]): QualityScore {
    const categoryScores = {
      grammar: 0,
      style: 0,
      consistency: 0,
      flow: 0,
      character: 0,
      plot: 0
    };

    const categoryCounts = {
      grammar: 0,
      style: 0,
      consistency: 0,
      flow: 0,
      character: 0,
      plot: 0
    };

    const improvements: string[] = [];

    // Analyze reviews and calculate scores
    reviews.forEach(review => {
      // Map review types to categories
      const category = this.mapReviewTypeToCategory(review.type);
      if (category && Object.prototype.hasOwnProperty.call(categoryScores, category)) {
        // Score based on priority (high issues = lower score)
        const score = review.priority === 'high' ? 60 : 
                     review.priority === 'medium' ? 80 : 90;
        
        categoryScores[category as keyof typeof categoryScores] += score;
        categoryCounts[category as keyof typeof categoryCounts]++;
        
        if (review.priority === 'high' || review.priority === 'medium') {
          improvements.push(review.suggestion);
        }
      }
    });

    // Calculate averages
    Object.keys(categoryScores).forEach(key => {
      const typedKey = key as keyof typeof categoryScores;
      if (categoryCounts[typedKey] > 0) {
        categoryScores[typedKey] = Math.round(categoryScores[typedKey] / categoryCounts[typedKey]);
      } else {
        categoryScores[typedKey] = 85; // Default score if no reviews in category
      }
    });

    // Calculate overall score
    const overall = Math.round(
      Object.values(categoryScores).reduce((sum, score) => sum + score, 0) / 
      Object.keys(categoryScores).length
    );

    // Determine if ready to save (overall > 80 and no high priority issues)
    const highPriorityIssues = reviews.filter(r => r.priority === 'high').length;
    const readyToSave = overall > 80 && highPriorityIssues === 0;

    const qualityScore: QualityScore = {
      overall,
      categories: categoryScores,
      readyToSave,
      improvements: improvements.slice(0, 5) // Top 5 improvements
    };

    this.qualityScoreSubject.next(qualityScore);
    return qualityScore;
  }

  /**
   * Clear review cache
   */
  clearReviewCache(storyId?: string, chapterNumber?: number): void {
    if (storyId && chapterNumber) {
      const cacheKey = `${storyId}_${chapterNumber}_final-edit`;
      this.reviewCache.delete(cacheKey);
    } else if (storyId) {
      const keysToDelete = Array.from(this.reviewCache.keys()).filter(key => 
        key.startsWith(storyId)
      );
      keysToDelete.forEach(key => this.reviewCache.delete(key));
    } else {
      this.reviewCache.clear();
    }
    
    this.notifyReviewsUpdated();
  }

  // Private helper methods

  private processComprehensiveReviewResponses(
    storyId: string,
    chapterNumber: number,
    responses: any[],
    requestIds: string[],
    options: ComprehensiveReviewRequest
  ): void {
    const reviews: ReviewItem[] = [];
    let responseIndex = 0;

    // Process character feedback responses
    if (options.includeCharacters) {
      const story = this.localStorageService.loadStory(storyId);
      if (story) {
        const availableCharacters = Array.from(story.characters.values()).filter(char => !char.isHidden);
        availableCharacters.forEach(character => {
          if (responseIndex < responses.length) {
            const characterReviews = this.convertCharacterFeedbackToReviews(
              responses[responseIndex],
              character.name,
              chapterNumber
            );
            reviews.push(...characterReviews);
            responseIndex++;
          }
        });
      }
    }

    // Process rater feedback responses
    if (options.includeRaters) {
      const story = this.localStorageService.loadStory(storyId);
      if (story) {
        const availableRaters = Array.from(story.raters.values()).filter(rater => rater.enabled);
        availableRaters.forEach(rater => {
          if (responseIndex < responses.length) {
            const raterReviews = this.convertRaterFeedbackToReviews(
              responses[responseIndex],
              rater.name,
              chapterNumber
            );
            reviews.push(...raterReviews);
            responseIndex++;
          }
        });
      }
    }

    // Process editor review response
    if (options.includeEditor && responseIndex < responses.length) {
      const editorReviews = this.convertEditorReviewToReviews(
        responses[responseIndex],
        chapterNumber
      );
      reviews.push(...editorReviews);
    }

    // Store reviews
    this.storeReviews(storyId, chapterNumber, reviews);
    
    // Calculate quality score
    this.calculateQualityScore(reviews);
  }

  private convertCharacterFeedbackToReviews(
    response: any,
    characterName: string,
    chapterNumber: number
  ): ReviewItem[] {
    const reviews: ReviewItem[] = [];
    const now = new Date();

    // Convert character feedback to review items
    const feedbackTypes = [
      { key: 'actions', type: 'character' as const },
      { key: 'dialog', type: 'character' as const },
      { key: 'physicalSensations', type: 'character' as const },
      { key: 'emotions', type: 'character' as const },
      { key: 'internalMonologue', type: 'character' as const }
    ];

    feedbackTypes.forEach(({ key, type }) => {
      const items = response.feedback?.[key] || [];
      items.forEach((content: string, index: number) => {
        reviews.push({
          id: `char_${characterName}_${key}_${chapterNumber}_${index}_${Date.now()}`,
          type: type,
          title: `${characterName} - ${key}`,
          description: content,
          suggestion: content,
          priority: 'medium',
          status: 'pending',
          metadata: {
            created: now,
            reviewer: characterName
          }
        });
      });
    });

    return reviews;
  }

  private convertRaterFeedbackToReviews(
    response: any,
    raterName: string,
    chapterNumber: number
  ): ReviewItem[] {
    const reviews: ReviewItem[] = [];
    const now = new Date();

    // Add opinion as a review
    if (response.feedback?.opinion) {
      reviews.push({
        id: `rater_${raterName}_opinion_${chapterNumber}_${Date.now()}`,
        type: 'style',
        title: `${raterName} - Overall Opinion`,
        description: response.feedback.opinion,
        suggestion: response.feedback.opinion,
        priority: 'medium',
        status: 'pending',
        metadata: {
          created: now,
          reviewer: raterName
        }
      });
    }

    // Add suggestions
    const suggestions = response.feedback?.suggestions || [];
    suggestions.forEach((suggestion: any, index: number) => {
      const content = typeof suggestion === 'string' ? suggestion : suggestion.suggestion;
      const priority = suggestion.priority || 'medium';
      
      reviews.push({
        id: `rater_${raterName}_suggestion_${chapterNumber}_${index}_${Date.now()}`,
        type: 'style',
        title: `${raterName} - Suggestion`,
        description: content,
        suggestion: content,
        priority: priority,
        status: 'pending',
        metadata: {
          created: now,
          reviewer: raterName
        }
      });
    });

    return reviews;
  }

  private convertEditorReviewToReviews(
    response: any,
    chapterNumber: number
  ): ReviewItem[] {
    const reviews: ReviewItem[] = [];
    const now = new Date();

    // Convert editor suggestions to review items
    const suggestions = response.suggestions || [];
    suggestions.forEach((suggestion: EditorSuggestion, index: number) => {
      reviews.push({
        id: `editor_${chapterNumber}_${index}_${Date.now()}`,
        type: this.mapEditorIssueToReviewType(suggestion.issue),
        title: `Editor - ${suggestion.issue}`,
        description: suggestion.issue,
        suggestion: suggestion.suggestion,
        priority: suggestion.priority,
        status: 'pending',
        affectedText: suggestion.selected ? {
          startIndex: 0,
          endIndex: 0,
          originalText: '',
          suggestedText: suggestion.suggestion
        } : undefined,
        metadata: {
          created: now,
          reviewer: 'editor'
        }
      });
    });

    return reviews;
  }

  private mapEditorIssueToReviewType(issue: string): ReviewItem['type'] {
    const lowerIssue = issue.toLowerCase();
    if (lowerIssue.includes('grammar') || lowerIssue.includes('spelling')) return 'grammar';
    if (lowerIssue.includes('style') || lowerIssue.includes('tone')) return 'style';
    if (lowerIssue.includes('consistency') || lowerIssue.includes('continuity')) return 'consistency';
    if (lowerIssue.includes('flow') || lowerIssue.includes('pacing')) return 'flow';
    if (lowerIssue.includes('character')) return 'character';
    if (lowerIssue.includes('plot') || lowerIssue.includes('story')) return 'plot';
    return 'style'; // Default
  }

  private mapReviewTypeToCategory(type: ReviewItem['type']): string {
    return type; // Direct mapping for now
  }

  private formatReviewsForChat(selectedReviews: ReviewItem[], userComment?: string): string {
    let message = '';

    if (userComment) {
      message += `${userComment}\n\n`;
    }

    message += `**Selected Reviews (${selectedReviews.length} items):**\n\n`;

    // Group reviews by reviewer
    const reviewsByReviewer = new Map<string, ReviewItem[]>();
    selectedReviews.forEach(item => {
      const reviewer = item.metadata.reviewer;
      if (!reviewsByReviewer.has(reviewer)) {
        reviewsByReviewer.set(reviewer, []);
      }
      reviewsByReviewer.get(reviewer)!.push(item);
    });

    // Format each reviewer's reviews
    reviewsByReviewer.forEach((items, reviewer) => {
      message += `**${reviewer}:**\n`;
      items.forEach(item => {
        message += `- ${item.title}: ${item.suggestion}\n`;
      });
      message += '\n';
    });

    return message.trim();
  }

  private storeReviews(storyId: string, chapterNumber: number, reviews: ReviewItem[]): void {
    // Update cache
    const cacheKey = `${storyId}_${chapterNumber}_final-edit`;
    const existingReviews = this.reviewCache.get(cacheKey) || [];
    this.reviewCache.set(cacheKey, [...existingReviews, ...reviews]);

    // Update story data
    const story = this.localStorageService.loadStory(storyId);
    if (story && story.chapterCompose) {
      const finalEditPhase = story.chapterCompose.phases.finalEdit;
      finalEditPhase.reviewSelection.availableReviews.push(...reviews);
      finalEditPhase.progress.totalReviews = finalEditPhase.reviewSelection.availableReviews.length;
      finalEditPhase.progress.lastActivity = new Date();
      
      this.localStorageService.saveStory(story);
    }
  }

  private notifyReviewsUpdated(): void {
    this.reviewsUpdatedSubject.next();
  }

  // ============================================================================
  // PHASE-AWARE REVIEW METHODS FOR THREE-PHASE CHAPTER COMPOSE SYSTEM (WRI-49)
  // ============================================================================

  /**
   * Request editor review with phase context
   */
  requestEditorReviewWithPhase(
    story: Story,
    chapterText: string,
    chapterNumber: number,
    chapterComposeState?: ChapterComposeState,
    conversationThread?: ConversationThread,
    additionalInstructions?: string
  ): Observable<ReviewItem[]> {
    const requestId = `editor_${chapterNumber}_${Date.now()}`;
    this.addPendingRequest(requestId);

    return this.generationService.requestEditorReviewWithPhase(
      story,
      chapterText,
      chapterComposeState,
      conversationThread,
      additionalInstructions
    ).pipe(
      map(response => {
        const reviews = this.convertEditorReviewToReviewsWithPhase(
          response,
          chapterNumber,
          chapterComposeState
        );

        // Store reviews with phase context
        this.storeReviewsWithPhase(story.id, chapterNumber, reviews, chapterComposeState);
        this.completeRequest(requestId);
        this.notifyReviewsUpdated();

        return reviews;
      }),
      catchError(error => {
        console.error('Editor review request failed:', error);
        this.failRequest(requestId);
        return of([]);
      })
    );
  }

  /**
   * Request comprehensive review with phase context
   */
  requestComprehensiveReviewWithPhase(
    story: Story,
    chapterText: string,
    chapterNumber: number,
    options: ComprehensiveReviewRequest,
    chapterComposeState?: ChapterComposeState,
    conversationThread?: ConversationThread,
    additionalInstructions?: string
  ): Observable<ReviewItem[]> {
    const requests: Observable<any>[] = [];

    // Character feedback requests
    if (options.includeCharacters) {
      const availableCharacters = Array.from(story.characters.values()).filter(char => !char.isHidden);
      availableCharacters.forEach(character => {
        const plotPoint = this.getPlotPointForChapter(story, chapterNumber);
        requests.push(
          this.generationService.requestCharacterFeedbackWithPhase(
            story,
            character,
            plotPoint,
            chapterComposeState,
            conversationThread,
            additionalInstructions
          )
        );
      });
    }

    // Rater feedback requests
    if (options.includeRaters) {
      const availableRaters = Array.from(story.raters.values()).filter(rater => rater.enabled);
      availableRaters.forEach(rater => {
        const plotPoint = this.getPlotPointForChapter(story, chapterNumber);
        requests.push(
          this.generationService.requestRaterFeedbackWithPhase(
            story,
            rater,
            plotPoint,
            chapterComposeState,
            conversationThread,
            additionalInstructions
          )
        );
      });
    }

    // Editor review request
    if (options.includeEditor) {
      requests.push(
        this.generationService.requestEditorReviewWithPhase(
          story,
          chapterText,
          chapterComposeState,
          conversationThread,
          additionalInstructions
        )
      );
    }

    if (requests.length === 0) {
      return of([]);
    }

    // Execute all requests
    return forkJoin(requests).pipe(
      map(responses => {
        const allReviews: ReviewItem[] = [];
        this.processComprehensiveReviewResponsesWithPhase(
          responses,
          story.id,
          chapterNumber,
          options,
          allReviews,
          chapterComposeState
        );
        return allReviews;
      }),
      catchError(error => {
        console.error('Comprehensive review request failed:', error);
        return of([]);
      })
    );
  }

  /**
   * Convert editor review to review items with phase context
   */
  private convertEditorReviewToReviewsWithPhase(
    response: any,
    chapterNumber: number,
    chapterComposeState?: ChapterComposeState
  ): ReviewItem[] {
    const reviews: ReviewItem[] = [];
    const now = new Date();

    // Convert editor suggestions to review items
    const suggestions = response.suggestions || [];
    suggestions.forEach((suggestion: EditorSuggestion, index: number) => {
      reviews.push({
        id: `editor_${chapterNumber}_${index}_${Date.now()}`,
        type: this.mapEditorIssueToReviewType(suggestion.issue),
        title: `Editor - ${suggestion.issue}`,
        description: suggestion.issue,
        suggestion: suggestion.suggestion,
        priority: suggestion.priority,
        status: 'pending',
        affectedText: suggestion.selected ? {
          startIndex: 0,
          endIndex: 0,
          originalText: '',
          suggestedText: suggestion.suggestion
        } : undefined,
        metadata: {
          created: now,
          reviewer: 'editor',
          phase_context: chapterComposeState ? {
            current_phase: chapterComposeState.currentPhase,
            plot_outline: chapterComposeState.phases.plotOutline.status,
            chapter_detail: chapterComposeState.phases.chapterDetailer.status,
            final_edit: chapterComposeState.phases.finalEdit.status
          } : undefined
        }
      });
    });

    return reviews;
  }

  /**
   * Process comprehensive review responses with phase context
   */
  private processComprehensiveReviewResponsesWithPhase(
    responses: any[],
    storyId: string,
    chapterNumber: number,
    options: ComprehensiveReviewRequest,
    reviews: ReviewItem[],
    chapterComposeState?: ChapterComposeState
  ): void {
    let responseIndex = 0;

    // Process character feedback responses
    if (options.includeCharacters) {
      const story = this.localStorageService.loadStory(storyId);
      if (story) {
        const availableCharacters = Array.from(story.characters.values()).filter(char => !char.isHidden);
        availableCharacters.forEach(character => {
          if (responseIndex < responses.length) {
            const characterReviews = this.convertCharacterFeedbackToReviewsWithPhase(
              responses[responseIndex],
              character.name,
              chapterNumber,
              chapterComposeState
            );
            reviews.push(...characterReviews);
            responseIndex++;
          }
        });
      }
    }

    // Process rater feedback responses
    if (options.includeRaters) {
      const story = this.localStorageService.loadStory(storyId);
      if (story) {
        const availableRaters = Array.from(story.raters.values()).filter(rater => rater.enabled);
        availableRaters.forEach(rater => {
          if (responseIndex < responses.length) {
            const raterReviews = this.convertRaterFeedbackToReviewsWithPhase(
              responses[responseIndex],
              rater.name,
              chapterNumber,
              chapterComposeState
            );
            reviews.push(...raterReviews);
            responseIndex++;
          }
        });
      }
    }

    // Process editor review response
    if (options.includeEditor && responseIndex < responses.length) {
      const editorReviews = this.convertEditorReviewToReviewsWithPhase(
        responses[responseIndex],
        chapterNumber,
        chapterComposeState
      );
      reviews.push(...editorReviews);
    }

    // Store reviews with phase context
    this.storeReviewsWithPhase(storyId, chapterNumber, reviews, chapterComposeState);
    
    // Calculate quality score
    this.calculateQualityScore(reviews);
  }

  /**
   * Convert character feedback to reviews with phase context
   */
  private convertCharacterFeedbackToReviewsWithPhase(
    response: any,
    characterName: string,
    chapterNumber: number,
    chapterComposeState?: ChapterComposeState
  ): ReviewItem[] {
    const reviews: ReviewItem[] = [];
    const now = new Date();

    // Convert character feedback to review items
    const feedbackTypes = [
      { key: 'actions', type: 'character' as const },
      { key: 'dialog', type: 'character' as const },
      { key: 'physicalSensations', type: 'character' as const },
      { key: 'emotions', type: 'character' as const },
      { key: 'internalMonologue', type: 'character' as const }
    ];

    feedbackTypes.forEach(({ key, type }) => {
      const items = response.feedback?.[key] || [];
      items.forEach((content: string, index: number) => {
        reviews.push({
          id: `char_${characterName}_${key}_${chapterNumber}_${index}_${Date.now()}`,
          type: type,
          title: `${characterName} - ${key}`,
          description: content,
          suggestion: content,
          priority: 'medium',
          status: 'pending',
          metadata: {
            created: now,
            reviewer: characterName,
            phase_context: chapterComposeState ? {
              current_phase: chapterComposeState.currentPhase,
              plot_outline: chapterComposeState.phases.plotOutline.status,
              chapter_detail: chapterComposeState.phases.chapterDetailer.status,
              final_edit: chapterComposeState.phases.finalEdit.status
            } : undefined
          }
        });
      });
    });

    return reviews;
  }

  /**
   * Convert rater feedback to reviews with phase context
   */
  private convertRaterFeedbackToReviewsWithPhase(
    response: any,
    raterName: string,
    chapterNumber: number,
    chapterComposeState?: ChapterComposeState
  ): ReviewItem[] {
    const reviews: ReviewItem[] = [];
    const now = new Date();

    // Add opinion as a review
    if (response.feedback?.opinion) {
      reviews.push({
        id: `rater_${raterName}_opinion_${chapterNumber}_${Date.now()}`,
        type: 'style',
        title: `${raterName} - Overall Opinion`,
        description: response.feedback.opinion,
        suggestion: response.feedback.opinion,
        priority: 'medium',
        status: 'pending',
        metadata: {
          created: now,
          reviewer: raterName,
          phase_context: chapterComposeState ? {
            current_phase: chapterComposeState.currentPhase,
            plot_outline: chapterComposeState.phases.plotOutline.status,
            chapter_detail: chapterComposeState.phases.chapterDetailer.status,
            final_edit: chapterComposeState.phases.finalEdit.status
          } : undefined
        }
      });
    }

    // Add suggestions
    const suggestions = response.feedback?.suggestions || [];
    suggestions.forEach((suggestion: any, index: number) => {
      const content = typeof suggestion === 'string' ? suggestion : suggestion.suggestion;
      const priority = suggestion.priority || 'medium';
      
      reviews.push({
        id: `rater_${raterName}_suggestion_${chapterNumber}_${index}_${Date.now()}`,
        type: 'style',
        title: `${raterName} - Suggestion`,
        description: content,
        suggestion: content,
        priority: priority,
        status: 'pending',
        metadata: {
          created: now,
          reviewer: raterName,
          phase_context: chapterComposeState ? {
            current_phase: chapterComposeState.currentPhase,
            plot_outline: chapterComposeState.phases.plotOutline.status,
            chapter_detail: chapterComposeState.phases.chapterDetailer.status,
            final_edit: chapterComposeState.phases.finalEdit.status
          } : undefined
        }
      });
    });

    return reviews;
  }

  /**
   * Store reviews with phase context
   */
  private storeReviewsWithPhase(
    storyId: string,
    chapterNumber: number,
    reviews: ReviewItem[],
    chapterComposeState?: ChapterComposeState
  ): void {
    // Use existing storage method - phase context is already in metadata
    this.storeReviews(storyId, chapterNumber, reviews);
  }

  /**
   * Get reviews filtered by phase
   */
  getReviewsByPhase(
    storyId: string,
    chapterNumber: number,
    phase: 'plot_outline' | 'chapter_detail' | 'final_edit'
  ): ReviewItem[] {
    const cacheKey = `${storyId}_${chapterNumber}_final-edit`;
    const allReviews = this.reviewCache.get(cacheKey) || [];

    return allReviews.filter(item => 
      item.metadata?.phase_context?.current_phase === phase
    );
  }

  /**
   * Get review statistics by phase
   */
  getReviewStatsByPhase(
    storyId: string,
    chapterNumber: number
  ): Record<string, { total: number; applied: number; pending: number; dismissed: number }> {
    const cacheKey = `${storyId}_${chapterNumber}_final-edit`;
    const allReviews = this.reviewCache.get(cacheKey) || [];

    const stats: Record<string, { total: number; applied: number; pending: number; dismissed: number }> = {};

    allReviews.forEach(item => {
      const phase = item.metadata?.phase_context?.current_phase || 'unknown';
      
      if (!stats[phase]) {
        stats[phase] = { total: 0, applied: 0, pending: 0, dismissed: 0 };
      }

      stats[phase].total++;
      switch (item.status) {
        case 'accepted':
        case 'modified':
          stats[phase].applied++;
          break;
        case 'rejected':
          stats[phase].dismissed++;
          break;
        default:
          stats[phase].pending++;
          break;
      }
    });

    return stats;
  }

  /**
   * Get plot point for chapter (helper method)
   */
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
}
