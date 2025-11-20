import { Injectable, inject } from '@angular/core';
import { BehaviorSubject, Observable, Subject, throwError } from 'rxjs';
import { catchError, finalize, map } from 'rxjs/operators';
import { 
  Chapter, 
  CharacterFeedback,
  CharacterFeedbackResponse, 
  RaterFeedbackResponse, 
  GenerateChapterResponse,
  ModifyChapterResponse,
  LLMChatRequest,
  FeedbackItem,
  Story
} from '../models/story.model';
import { FeedbackSelection } from '../components/feedback-selector/feedback-selector.component';
import { GenerationService } from './generation.service';
import { ApiService } from './api.service';
import { ContextBuilderService } from './context-builder.service';

export interface ChapterEditingState {
  currentChapter: Chapter | null;
  isGenerating: boolean;
  isGettingFeedback: boolean;
  isApplyingGuidance: boolean;
  isChatting: boolean;
  chatHistory: { role: 'user' | 'assistant', content: string, timestamp: Date }[];
  characterFeedback: CharacterFeedbackResponse[];
  raterFeedback: RaterFeedbackResponse[];
  userGuidance: string;
  hasUnsavedChanges: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class ChapterEditorService {
  private stateSubject = new BehaviorSubject<ChapterEditingState>({
    currentChapter: null,
    isGenerating: false,
    isGettingFeedback: false,
    isApplyingGuidance: false,
    isChatting: false,
    chatHistory: [],
    characterFeedback: [],
    raterFeedback: [],
    userGuidance: '',
    hasUnsavedChanges: false
  });

  public state$ = this.stateSubject.asObservable();
  private errorSubject = new Subject<string>();
  public error$ = this.errorSubject.asObservable();

  private generationService = inject(GenerationService);
  private apiService = inject(ApiService);
  private contextBuilder = inject(ContextBuilderService);

  /**
   * Initialize chapter editing for a specific chapter
   */
  initializeChapterEditing(chapter: Chapter): void {
    // Load existing feedback from the chapter's incorporatedFeedback
    const existingFeedback = this.loadFeedbackFromChapter(chapter);
    
    this.updateState({
      currentChapter: { ...chapter },
      chatHistory: [],
      characterFeedback: existingFeedback.characterFeedback,
      raterFeedback: existingFeedback.raterFeedback,
      userGuidance: '',
      hasUnsavedChanges: false
    });
  }

  /**
   * Update chapter content
   */
  updateChapterContent(content: string): void {
    const currentState = this.stateSubject.value;
    if (currentState.currentChapter) {
      const updatedChapter = {
        ...currentState.currentChapter,
        content,
        metadata: {
          ...currentState.currentChapter.metadata,
          lastModified: new Date(),
          wordCount: this.countWords(content)
        }
      };
      
      this.updateState({
        currentChapter: updatedChapter,
        hasUnsavedChanges: true
      });
    }
  }

  /**
   * Update chapter title
   */
  updateChapterTitle(title: string): void {
    const currentState = this.stateSubject.value;
    if (currentState.currentChapter) {
      const updatedChapter = {
        ...currentState.currentChapter,
        title,
        metadata: {
          ...currentState.currentChapter.metadata,
          lastModified: new Date()
        }
      };
      
      this.updateState({
        currentChapter: updatedChapter,
        hasUnsavedChanges: true
      });
    }
  }

  /**
   * Update chapter plot point
   */
  updateChapterPlotPoint(plotPoint: string): void {
    const currentState = this.stateSubject.value;
    if (currentState.currentChapter) {
      const updatedChapter = {
        ...currentState.currentChapter,
        plotPoint,
        metadata: {
          ...currentState.currentChapter.metadata,
          lastModified: new Date()
        }
      };
      
      this.updateState({
        currentChapter: updatedChapter,
        hasUnsavedChanges: true
      });
    }
  }

  /**
   * Add key plot item
   */
  addKeyPlotItem(item: string): void {
    const currentState = this.stateSubject.value;
    if (currentState.currentChapter) {
      const keyPlotItems = currentState.currentChapter.keyPlotItems || [];
      const updatedChapter = {
        ...currentState.currentChapter,
        keyPlotItems: [...keyPlotItems, item],
        metadata: {
          ...currentState.currentChapter.metadata,
          lastModified: new Date()
        }
      };
      
      this.updateState({
        currentChapter: updatedChapter,
        hasUnsavedChanges: true
      });
    }
  }

  /**
   * Remove key plot item
   */
  removeKeyPlotItem(index: number): void {
    const currentState = this.stateSubject.value;
    if (currentState.currentChapter && currentState.currentChapter.keyPlotItems) {
      const keyPlotItems = [...currentState.currentChapter.keyPlotItems];
      keyPlotItems.splice(index, 1);
      
      const updatedChapter = {
        ...currentState.currentChapter,
        keyPlotItems,
        metadata: {
          ...currentState.currentChapter.metadata,
          lastModified: new Date()
        }
      };
      
      this.updateState({
        currentChapter: updatedChapter,
        hasUnsavedChanges: true
      });
    }
  }

  /**
   * Generate chapter content from outline
   */
  generateChapterFromOutline(story: Story): Observable<string> {
    const currentState = this.stateSubject.value;
    if (!currentState.currentChapter) {
      return throwError(() => new Error('No chapter selected for generation'));
    }

    this.updateState({ isGenerating: true });

    return this.generationService.generateChapter(story, currentState.currentChapter.number, []).pipe(
      map((response: GenerateChapterResponse) => {
        const updatedChapter = {
          ...currentState.currentChapter!,
          content: response.chapterText,
          metadata: {
            ...currentState.currentChapter!.metadata,
            lastModified: new Date(),
            wordCount: this.countWords(response.chapterText)
          }
        };

        this.updateState({
          currentChapter: updatedChapter,
          hasUnsavedChanges: true
        });

        return response.chapterText;
      }),
      catchError(error => {
        this.errorSubject.next('Failed to generate chapter: ' + error.message);
        return throwError(() => error);
      }),
      finalize(() => {
        this.updateState({ isGenerating: false });
      })
    );
  }

  /**
   * Send chat message for brainstorming
   */
  sendChatMessage(message: string, story: Story): Observable<string> {
    this.updateState({ isChatting: true });

    const currentState = this.stateSubject.value;
    const chatHistory = [...currentState.chatHistory];
    
    // Add user message
    chatHistory.push({
      role: 'user',
      content: message,
      timestamp: new Date()
    });

    // Build chat request
    const chatRequest: LLMChatRequest = {
      messages: chatHistory.map(msg => ({
        role: msg.role,
        content: msg.content
      })),
      agent_type: 'writer',
      compose_context: {
        story_context: this.contextBuilder.buildStorySummaryContext(story).data || {},
        chapter_draft: currentState.currentChapter?.content
      },
      system_prompts: {
        mainPrefix: story.general.systemPrompts.mainPrefix,
        mainSuffix: story.general.systemPrompts.mainSuffix,
        assistantPrompt: story.general.systemPrompts.assistantPrompt
      }
    };

    return this.apiService.llmChat(chatRequest).pipe(
      map(response => {
        // Add assistant response
        chatHistory.push({
          role: 'assistant',
          content: response.message.content,
          timestamp: new Date()
        });

        this.updateState({ chatHistory });
        return response.message.content;
      }),
      catchError(error => {
        this.errorSubject.next('Chat failed: ' + error.message);
        return throwError(() => error);
      }),
      finalize(() => {
        this.updateState({ isChatting: false });
      })
    );
  }

  /**
   * Get character feedback for current chapter from a specific character
   */
  getCharacterFeedback(story: Story, characterId: string, characterName: string): Observable<CharacterFeedbackResponse[]> {
    const currentState = this.stateSubject.value;
    if (!currentState.currentChapter?.content) {
      return throwError(() => new Error('No chapter content to get feedback on'));
    }

    // Find the selected character
    const selectedCharacter = Array.from(story.characters.values()).find(char => char.id === characterId);
    if (!selectedCharacter) {
      return throwError(() => new Error(`Character with ID ${characterId} not found`));
    }

    this.updateState({ isGettingFeedback: true });

    // Request feedback from only the selected character
    return this.generationService.requestCharacterFeedback(
      story,
      selectedCharacter,
      currentState.currentChapter!.content
    ).pipe(
      map(response => {
        // Convert StructuredCharacterFeedbackResponse to CharacterFeedbackResponse
        const characterFeedback = [{
          characterName: response.characterName || characterName,
          feedback: response.feedback || {
            actions: [],
            dialog: [],
            physicalSensations: [],
            emotions: [],
            internalMonologue: [],
            goals: [],
            memories: []
          }
        }];
        
        // Save feedback to chapter's incorporatedFeedback
        this.saveFeedbackToChapter(characterFeedback, 'character');
        
        // Update state with new feedback (merge with existing feedback from other characters)
        const existingFeedback = currentState.characterFeedback.filter(f => f.characterName !== characterName);
        const updatedFeedback = [...existingFeedback, ...characterFeedback];
        this.updateState({ characterFeedback: updatedFeedback });
        
        return characterFeedback;
      }),
      catchError(error => {
        this.errorSubject.next('Failed to get character feedback: ' + error.message);
        return throwError(() => error);
      }),
      finalize(() => {
        this.updateState({ isGettingFeedback: false });
      })
    );
  }

  /**
   * Get rater feedback for current chapter from a specific rater
   */
  getRaterFeedback(story: Story, raterId: string, raterName: string): Observable<RaterFeedbackResponse[]> {
    const currentState = this.stateSubject.value;
    if (!currentState.currentChapter?.content) {
      return throwError(() => new Error('No chapter content to get feedback on'));
    }

    // Find the selected rater
    const selectedRater = Array.from(story.raters.values()).find(rater => rater.id === raterId);
    if (!selectedRater) {
      return throwError(() => new Error(`Rater with ID ${raterId} not found`));
    }

    this.updateState({ isGettingFeedback: true });

    // Request feedback from only the selected rater
    return this.generationService.requestRaterFeedback(
      story,
      selectedRater,
      currentState.currentChapter!.content
    ).pipe(
      map(response => {
        // Convert StructuredRaterFeedbackResponse to RaterFeedbackResponse
        const raterFeedback = [{
          raterName: response.raterName || raterName,
          feedback: response.feedback || 'No feedback provided'
        }];
        
        // Save feedback to chapter's incorporatedFeedback
        this.saveFeedbackToChapter(raterFeedback, 'rater');
        
        // Update state with new feedback (merge with existing feedback from other raters)
        const existingFeedback = currentState.raterFeedback.filter(f => f.raterName !== raterName);
        const updatedFeedback = [...existingFeedback, ...raterFeedback];
        this.updateState({ raterFeedback: updatedFeedback });
        
        return raterFeedback;
      }),
      catchError(error => {
        this.errorSubject.next('Failed to get rater feedback: ' + error.message);
        return throwError(() => error);
      }),
      finalize(() => {
        this.updateState({ isGettingFeedback: false });
      })
    );
  }

  /**
   * Apply user guidance to modify chapter
   */
  applyUserGuidance(guidance: string, story: Story, feedbackSelection?: FeedbackSelection): Observable<string> {
    const currentState = this.stateSubject.value;
    if (!currentState.currentChapter?.content) {
      return throwError(() => new Error('No chapter content to modify'));
    }

    this.updateState({ isApplyingGuidance: true, userGuidance: guidance });

    // Use empty feedback selection if none provided
    const defaultFeedbackSelection: FeedbackSelection = {
      characterFeedback: [],
      raterFeedback: []
    };

    return this.generationService.modifyChapter(
      story,
      currentState.currentChapter.content,
      guidance,
      feedbackSelection || defaultFeedbackSelection
    ).pipe(
      map((response: ModifyChapterResponse) => {
        const updatedChapter = {
          ...currentState.currentChapter!,
          content: response.modifiedChapter,
          metadata: {
            ...currentState.currentChapter!.metadata,
            lastModified: new Date(),
            wordCount: this.countWords(response.modifiedChapter)
          }
        };

        this.updateState({
          currentChapter: updatedChapter,
          hasUnsavedChanges: true
        });

        // Clear feedback after successful chapter modification since it's now incorporated
        this.clearFeedback();

        return response.modifiedChapter;
      }),
      catchError(error => {
        this.errorSubject.next('Failed to apply guidance: ' + error.message);
        return throwError(() => error);
      }),
      finalize(() => {
        this.updateState({ isApplyingGuidance: false });
      })
    );
  }

  /**
   * Apply feedback item to chapter
   */
  applyFeedbackItem(feedbackItem: FeedbackItem, story: Story): Observable<string> {
    const guidance = `Please incorporate this feedback: ${feedbackItem.content}`;
    return this.applyUserGuidance(guidance, story);
  }

  /**
   * Clear chat history
   */
  clearChatHistory(): void {
    this.updateState({ chatHistory: [] });
  }

  /**
   * Clear all feedback
   */
  clearFeedback(): void {
    const currentState = this.stateSubject.value;
    
    // Clear UI feedback arrays and user guidance
    const stateUpdate: Partial<ChapterEditingState> = {
      characterFeedback: [],
      raterFeedback: [],
      userGuidance: ''
    };

    // Also clear incorporated feedback from the chapter itself
    if (currentState.currentChapter) {
      const updatedChapter = {
        ...currentState.currentChapter,
        incorporatedFeedback: [],
        metadata: {
          ...currentState.currentChapter.metadata,
          lastModified: new Date()
        }
      };
      stateUpdate.currentChapter = updatedChapter;
    }

    this.updateState(stateUpdate);
  }

  /**
   * Mark changes as saved
   */
  markAsSaved(): void {
    this.updateState({ hasUnsavedChanges: false });
  }

  /**
   * Get current chapter
   */
  getCurrentChapter(): Chapter | null {
    return this.stateSubject.value.currentChapter;
  }

  /**
   * Reset service state
   */
  reset(): void {
    this.stateSubject.next({
      currentChapter: null,
      isGenerating: false,
      isGettingFeedback: false,
      isApplyingGuidance: false,
      isChatting: false,
      chatHistory: [],
      characterFeedback: [],
      raterFeedback: [],
      userGuidance: '',
      hasUnsavedChanges: false
    });
  }

  /**
   * Load existing feedback from chapter's incorporatedFeedback
   */
  private loadFeedbackFromChapter(chapter: Chapter): { characterFeedback: CharacterFeedbackResponse[], raterFeedback: RaterFeedbackResponse[] } {
    const characterFeedbackMap = new Map<string, CharacterFeedback>();
    const raterFeedbackMap = new Map<string, { opinion: string, suggestions: { issue: string; suggestion: string; priority: 'high' | 'medium' | 'low' }[] }>();

    // Process incorporated feedback items
    chapter.incorporatedFeedback.forEach(item => {
      if (['action', 'dialog', 'sensation', 'emotion', 'thought'].includes(item.type)) {
        // Character feedback
        if (!characterFeedbackMap.has(item.source)) {
          characterFeedbackMap.set(item.source, {
            characterName: item.source,
            actions: [],
            dialog: [],
            physicalSensations: [],
            emotions: [],
            internalMonologue: [],
            goals: [],
            memories: [],
            subtext: []
          });
        }
        
        const feedback = characterFeedbackMap.get(item.source)!;
        switch (item.type) {
          case 'action':
            feedback.actions.push(item.content);
            break;
          case 'dialog':
            feedback.dialog.push(item.content);
            break;
          case 'sensation':
            feedback.physicalSensations.push(item.content);
            break;
          case 'emotion':
            feedback.emotions.push(item.content);
            break;
          case 'thought':
            feedback.internalMonologue.push(item.content);
            break;
        }
      } else if (item.type === 'suggestion') {
        // Rater feedback
        if (!raterFeedbackMap.has(item.source)) {
          raterFeedbackMap.set(item.source, {
            opinion: '',
            suggestions: []
          });
        }
        
        const feedback = raterFeedbackMap.get(item.source)!;
        // Distinguish between opinion and suggestions based on content length or other criteria
        if (item.content.length > 200 && feedback.opinion === '') {
          feedback.opinion = item.content;
        } else {
          feedback.suggestions.push({
            issue: 'General feedback',
            suggestion: item.content,
            priority: 'medium' as const
          });
        }
      }
    });

    // Convert maps to response arrays
    const characterFeedback: CharacterFeedbackResponse[] = Array.from(characterFeedbackMap.entries()).map(([name, feedback]) => ({
      characterName: name,
      feedback
    }));

    const raterFeedback: RaterFeedbackResponse[] = Array.from(raterFeedbackMap.entries()).map(([name, feedback]) => ({
      raterName: name,
      feedback
    }));

    return { characterFeedback, raterFeedback };
  }

  /**
   * Save feedback to chapter's incorporatedFeedback array
   */
  private saveFeedbackToChapter(feedback: CharacterFeedbackResponse[] | RaterFeedbackResponse[], type: 'character' | 'rater'): void {
    const currentState = this.stateSubject.value;
    if (!currentState.currentChapter) return;

    const newFeedbackItems: FeedbackItem[] = [];

    if (type === 'character') {
      (feedback as CharacterFeedbackResponse[]).forEach(charFeedback => {
        const fb = charFeedback.feedback;
        
        // Add each type of character feedback as separate items
        if (fb.actions) {
          fb.actions.forEach(action => {
            newFeedbackItems.push({
              source: charFeedback.characterName,
              type: 'action',
              content: action,
              incorporated: false
            });
          });
        }
        
        if (fb.dialog) {
          fb.dialog.forEach(dialog => {
            newFeedbackItems.push({
              source: charFeedback.characterName,
              type: 'dialog',
              content: dialog,
              incorporated: false
            });
          });
        }
        
        if (fb.physicalSensations) {
          fb.physicalSensations.forEach(sensation => {
            newFeedbackItems.push({
              source: charFeedback.characterName,
              type: 'sensation',
              content: sensation,
              incorporated: false
            });
          });
        }
        
        if (fb.emotions) {
          fb.emotions.forEach(emotion => {
            newFeedbackItems.push({
              source: charFeedback.characterName,
              type: 'emotion',
              content: emotion,
              incorporated: false
            });
          });
        }
        
        if (fb.internalMonologue) {
          fb.internalMonologue.forEach(thought => {
            newFeedbackItems.push({
              source: charFeedback.characterName,
              type: 'thought',
              content: thought,
              incorporated: false
            });
          });
        }
      });
    } else if (type === 'rater') {
      (feedback as RaterFeedbackResponse[]).forEach(raterFeedback => {
        const fb = raterFeedback.feedback;
        
        // Add opinion as a suggestion
        if (fb.opinion) {
          newFeedbackItems.push({
            source: raterFeedback.raterName,
            type: 'suggestion',
            content: fb.opinion,
            incorporated: false
          });
        }
        
        // Add each suggestion
        if (fb.suggestions) {
          fb.suggestions.forEach(suggestion => {
            newFeedbackItems.push({
              source: raterFeedback.raterName,
              type: 'suggestion',
              content: suggestion.suggestion,
              incorporated: false
            });
          });
        }
      });
    }

    // Remove existing feedback from the same sources to avoid duplicates
    const existingSources = new Set(newFeedbackItems.map(item => item.source));
    const filteredExistingFeedback = currentState.currentChapter.incorporatedFeedback.filter(
      item => !existingSources.has(item.source)
    );

    // Update the chapter with new feedback
    const updatedChapter = {
      ...currentState.currentChapter,
      incorporatedFeedback: [...filteredExistingFeedback, ...newFeedbackItems],
      metadata: {
        ...currentState.currentChapter.metadata,
        lastModified: new Date()
      }
    };

    this.updateState({ currentChapter: updatedChapter });
  }

  private updateState(partialState: Partial<ChapterEditingState>): void {
    const currentState = this.stateSubject.value;
    this.stateSubject.next({ ...currentState, ...partialState });
  }

  private countWords(text: string): number {
    return text.trim().split(/\s+/).filter(word => word.length > 0).length;
  }
}
