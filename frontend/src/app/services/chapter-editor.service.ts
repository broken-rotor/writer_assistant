import { Injectable, inject } from '@angular/core';
import { BehaviorSubject, Observable, Subject, throwError, forkJoin } from 'rxjs';
import { catchError, finalize, map } from 'rxjs/operators';
import { 
  Chapter, 
  CharacterFeedbackResponse, 
  RaterFeedbackResponse, 
  GenerateChapterResponse,
  ModifyChapterResponse,
  LLMChatRequest,
  FeedbackItem,
  Story
} from '../models/story.model';
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
    this.updateState({
      currentChapter: { ...chapter },
      chatHistory: [],
      characterFeedback: [],
      raterFeedback: [],
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
   * Get character feedback for current chapter
   */
  getCharacterFeedback(story: Story): Observable<CharacterFeedbackResponse[]> {
    const currentState = this.stateSubject.value;
    if (!currentState.currentChapter?.content) {
      return throwError(() => new Error('No chapter content to get feedback on'));
    }

    this.updateState({ isGettingFeedback: true });

    const requests = Array.from(story.characters.values())
      .filter(char => !char.isHidden)
      .map(character => {
        return this.generationService.requestCharacterFeedback(
          story,
          character,
          currentState.currentChapter!.content
        );
      });

    if (requests.length === 0) {
      this.updateState({ isGettingFeedback: false });
      return new Observable(observer => {
        observer.next([]);
        observer.complete();
      });
    }

    return forkJoin(requests).pipe(
      map(responses => {
        // Convert StructuredCharacterFeedbackResponse to CharacterFeedbackResponse
        const characterFeedback = responses.map(response => ({
          characterName: response.characterName || 'Unknown',
          feedback: response.feedback || 'No feedback provided'
        }));
        this.updateState({ characterFeedback });
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
   * Get rater feedback for current chapter
   */
  getRaterFeedback(story: Story): Observable<RaterFeedbackResponse[]> {
    const currentState = this.stateSubject.value;
    if (!currentState.currentChapter?.content) {
      return throwError(() => new Error('No chapter content to get feedback on'));
    }

    this.updateState({ isGettingFeedback: true });

    const requests = Array.from(story.raters.values())
      .filter(rater => rater.enabled)
      .map(rater => {
        return this.generationService.requestRaterFeedback(
          story,
          rater,
          currentState.currentChapter!.content
        );
      });

    if (requests.length === 0) {
      this.updateState({ isGettingFeedback: false });
      return new Observable(observer => {
        observer.next([]);
        observer.complete();
      });
    }

    return forkJoin(requests).pipe(
      map(responses => {
        // Convert StructuredRaterFeedbackResponse to RaterFeedbackResponse
        const raterFeedback = responses.map(response => ({
          raterName: response.raterName || 'Unknown',
          feedback: response.feedback || 'No feedback provided'
        }));
        this.updateState({ raterFeedback });
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
  applyUserGuidance(guidance: string, story: Story): Observable<string> {
    const currentState = this.stateSubject.value;
    if (!currentState.currentChapter?.content) {
      return throwError(() => new Error('No chapter content to modify'));
    }

    this.updateState({ isApplyingGuidance: true, userGuidance: guidance });

    return this.generationService.modifyChapter(
      story,
      currentState.currentChapter.content,
      guidance
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
    this.updateState({ 
      characterFeedback: [],
      raterFeedback: []
    });
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

  private updateState(partialState: Partial<ChapterEditingState>): void {
    const currentState = this.stateSubject.value;
    this.stateSubject.next({ ...currentState, ...partialState });
  }

  private countWords(text: string): number {
    return text.trim().split(/\s+/).filter(word => word.length > 0).length;
  }
}
