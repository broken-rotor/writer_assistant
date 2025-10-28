import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
import { of } from 'rxjs';
import {
  ChapterComposeState,
  PhaseTransition,
  ConversationThread,
  PhaseTransitionRequest,
  PhaseTransitionResponse,
  Story
} from '../models/story.model';
import { LocalStorageService } from './local-storage.service';
import { ApiService } from './api.service';

export type PhaseType = 'plot_outline' | 'chapter_detail' | 'final_edit';

export interface PhaseValidationResult {
  canAdvance: boolean;
  canRevert: boolean;
  requirements: string[];
  validationErrors: string[];
  nextPhase?: PhaseType;
  previousPhase?: PhaseType;
}

@Injectable({
  providedIn: 'root'
})
export class PhaseStateService {
  private currentPhaseSubject = new BehaviorSubject<PhaseType>('plot_outline');
  private chapterComposeStateSubject = new BehaviorSubject<ChapterComposeState | null>(null);
  private validationResultSubject = new BehaviorSubject<PhaseValidationResult>({
    canAdvance: false,
    canRevert: false,
    requirements: [],
    validationErrors: []
  });

  public currentPhase$ = this.currentPhaseSubject.asObservable();
  public chapterComposeState$ = this.chapterComposeStateSubject.asObservable();
  public validationResult$ = this.validationResultSubject.asObservable();

  constructor(
    private localStorageService: LocalStorageService,
    private apiService: ApiService
  ) {}

  /**
   * Initialize chapter compose state for a story
   */
  initializeChapterComposeState(storyId: string, chapterNumber: number): ChapterComposeState {
    const now = new Date();
    const conversationId = this.generateId();
    const branchId = this.generateId();

    const initialConversation: ConversationThread = {
      id: conversationId,
      messages: [],
      currentBranchId: branchId,
      branches: new Map([
        [branchId, {
          id: branchId,
          name: 'Main',
          parentMessageId: '',
          messageIds: [],
          isActive: true,
          metadata: { created: now }
        }]
      ]),
      metadata: {
        created: now,
        lastModified: now,
        phase: 'plot_outline'
      }
    };

    const chapterComposeState: ChapterComposeState = {
      currentPhase: 'plot_outline',
      phases: {
        plotOutline: {
          conversation: { ...initialConversation },
          outline: {
            items: new Map(),
            structure: [],
            currentFocus: undefined
          },
          draftSummary: '',
          status: 'active',
          progress: {
            completedItems: 0,
            totalItems: 0,
            lastActivity: now
          }
        },
        chapterDetailer: {
          conversation: { 
            ...initialConversation, 
            id: this.generateId(),
            metadata: { ...initialConversation.metadata, phase: 'chapter_detail' }
          },
          chapterDraft: {
            content: '',
            title: '',
            plotPoint: '',
            wordCount: 0,
            status: 'drafting'
          },
          feedbackIntegration: {
            pendingFeedback: [],
            incorporatedFeedback: [],
            feedbackRequests: new Map()
          },
          status: 'paused',
          progress: {
            feedbackIncorporated: 0,
            totalFeedbackItems: 0,
            lastActivity: now
          }
        },
        finalEdit: {
          conversation: { 
            ...initialConversation, 
            id: this.generateId(),
            metadata: { ...initialConversation.metadata, phase: 'final_edit' }
          },
          finalChapter: {
            content: '',
            title: '',
            wordCount: 0,
            version: 1
          },
          reviewSelection: {
            availableReviews: [],
            selectedReviews: [],
            appliedReviews: []
          },
          status: 'paused',
          progress: {
            reviewsApplied: 0,
            totalReviews: 0,
            lastActivity: now
          }
        }
      },
      sharedContext: {
        chapterNumber: chapterNumber,
        targetWordCount: 2000,
        genre: undefined,
        tone: undefined,
        pov: undefined
      },
      navigation: {
        phaseHistory: ['plot_outline'],
        canGoBack: false,
        canGoForward: false,
        branchNavigation: {
          currentBranchId: branchId,
          availableBranches: [branchId],
          branchHistory: [],
          canNavigateBack: false,
          canNavigateForward: false
        }
      },
      overallProgress: {
        currentStep: 1,
        totalSteps: 3,
        phaseCompletionStatus: {
          'plot_outline': false,
          'chapter_detail': false,
          'final_edit': false
        },
        estimatedTimeRemaining: undefined
      },
      metadata: {
        created: now,
        lastModified: now,
        version: '1.0.0'
      }
    };

    this.chapterComposeStateSubject.next(chapterComposeState);
    this.currentPhaseSubject.next('plot_outline');
    this.updateValidationResult(chapterComposeState);

    return chapterComposeState;
  }

  /**
   * Load existing chapter compose state
   */
  loadChapterComposeState(state: ChapterComposeState): void {
    this.chapterComposeStateSubject.next(state);
    this.currentPhaseSubject.next(state.currentPhase);
    this.updateValidationResult(state);
  }

  /**
   * Get current phase
   */
  getCurrentPhase(): PhaseType {
    return this.currentPhaseSubject.value;
  }

  /**
   * Get current chapter compose state
   */
  getCurrentState(): ChapterComposeState | null {
    return this.chapterComposeStateSubject.value;
  }

  /**
   * Validate if user can advance to next phase
   */
  canAdvance(): boolean {
    const state = this.getCurrentState();
    if (!state) return false;

    const validation = this.validatePhaseTransition(state, this.getNextPhase(state.currentPhase));
    return validation.canTransition;
  }

  /**
   * Validate if user can revert to previous phase
   */
  canRevert(): boolean {
    const state = this.getCurrentState();
    if (!state) return false;

    const previousPhase = this.getPreviousPhase(state.currentPhase);
    return previousPhase !== undefined && state.navigation.phaseHistory.length > 1;
  }

  /**
   * Advance to next phase
   */
  async advanceToNext(): Promise<boolean> {
    const state = this.getCurrentState();
    if (!state || !this.canAdvance()) return false;

    const nextPhase = this.getNextPhase(state.currentPhase);
    if (!nextPhase) return false;

    return this.transitionToPhase(nextPhase);
  }

  /**
   * Revert to previous phase
   */
  async revertToPrevious(): Promise<boolean> {
    const state = this.getCurrentState();
    if (!state || !this.canRevert()) return false;

    const previousPhase = this.getPreviousPhase(state.currentPhase);
    if (!previousPhase) return false;

    return this.transitionToPhase(previousPhase);
  }

  /**
   * Transition to specific phase
   */
  private async transitionToPhase(targetPhase: PhaseType): Promise<boolean> {
    const state = this.getCurrentState();
    if (!state) return false;

    try {
      // Update phase status
      const currentPhase = state.currentPhase;
      const currentPhaseKey = this.getPhasePropertyKey(currentPhase);
      const targetPhaseKey = this.getPhasePropertyKey(targetPhase);
      state.phases[currentPhaseKey].status = 'completed';
      state.phases[targetPhaseKey].status = 'active';

      // Update navigation
      state.currentPhase = targetPhase;
      if (!state.navigation.phaseHistory.includes(targetPhase)) {
        state.navigation.phaseHistory.push(targetPhase);
      }

      // Update progress
      state.overallProgress.currentStep = this.getPhaseStep(targetPhase);
      state.overallProgress.phaseCompletionStatus[currentPhase] = true;

      // Update metadata
      state.metadata.lastModified = new Date();

      // Emit updates
      this.chapterComposeStateSubject.next(state);
      this.currentPhaseSubject.next(targetPhase);
      this.updateValidationResult(state);

      return true;
    } catch (error) {
      console.error('Error transitioning to phase:', error);
      return false;
    }
  }

  /**
   * Update phase progress
   */
  updatePhaseProgress(phase: PhaseType, progress: Partial<any>): void {
    const state = this.getCurrentState();
    if (!state) return;

    // Update specific phase progress
    switch (phase) {
      case 'plot_outline':
        Object.assign(state.phases.plotOutline.progress, progress);
        break;
      case 'chapter_detail':
        Object.assign(state.phases.chapterDetailer.progress, progress);
        break;
      case 'final_edit':
        Object.assign(state.phases.finalEdit.progress, progress);
        break;
    }

    state.metadata.lastModified = new Date();
    this.chapterComposeStateSubject.next(state);
    this.updateValidationResult(state);
  }

  /**
   * Validate phase transition
   */
  private validatePhaseTransition(state: ChapterComposeState, targetPhase: PhaseType | undefined): PhaseTransition {
    if (!targetPhase) {
      return {
        fromPhase: state.currentPhase,
        toPhase: state.currentPhase,
        canTransition: false,
        requirements: [],
        validationErrors: ['No target phase specified']
      };
    }

    const requirements: string[] = [];
    const validationErrors: string[] = [];

    switch (targetPhase) {
      case 'chapter_detail':
        if (state.currentPhase === 'plot_outline') {
          requirements.push('Complete plot outline');
          requirements.push('Have at least one outline item');
          
          if (state.phases.plotOutline.outline.structure.length === 0) {
            validationErrors.push('Plot outline must contain at least one item');
          }
          if (state.phases.plotOutline.draftSummary.trim().length === 0) {
            validationErrors.push('Plot outline summary is required');
          }
        }
        break;

      case 'final_edit':
        if (state.currentPhase === 'chapter_detail') {
          requirements.push('Complete chapter draft');
          requirements.push('Incorporate minimum feedback');
          
          if (state.phases.chapterDetailer.chapterDraft.content.trim().length === 0) {
            validationErrors.push('Chapter draft content is required');
          }
          if (state.phases.chapterDetailer.chapterDraft.wordCount < 500) {
            validationErrors.push('Chapter draft must be at least 500 words');
          }
        }
        break;
    }

    return {
      fromPhase: state.currentPhase,
      toPhase: targetPhase,
      canTransition: validationErrors.length === 0,
      requirements,
      validationErrors
    };
  }

  /**
   * Update validation result
   */
  private updateValidationResult(state: ChapterComposeState): void {
    const nextPhase = this.getNextPhase(state.currentPhase);
    const previousPhase = this.getPreviousPhase(state.currentPhase);

    const nextValidation = nextPhase ? this.validatePhaseTransition(state, nextPhase) : null;

    const result: PhaseValidationResult = {
      canAdvance: nextValidation?.canTransition || false,
      canRevert: previousPhase !== undefined && state.navigation.phaseHistory.length > 1,
      requirements: nextValidation?.requirements || [],
      validationErrors: nextValidation?.validationErrors || [],
      nextPhase,
      previousPhase
    };

    this.validationResultSubject.next(result);
  }

  /**
   * Convert phase type to property key for phases object
   */
  private getPhasePropertyKey(phase: PhaseType): keyof ChapterComposeState['phases'] {
    switch (phase) {
      case 'plot_outline': return 'plotOutline';
      case 'chapter_detail': return 'chapterDetailer';
      case 'final_edit': return 'finalEdit';
      default: throw new Error(`Unknown phase: ${phase}`);
    }
  }

  /**
   * Get next phase in sequence
   */
  private getNextPhase(currentPhase: PhaseType): PhaseType | undefined {
    switch (currentPhase) {
      case 'plot_outline': return 'chapter_detail';
      case 'chapter_detail': return 'final_edit';
      case 'final_edit': return undefined;
      default: return undefined;
    }
  }

  /**
   * Get previous phase in sequence
   */
  private getPreviousPhase(currentPhase: PhaseType): PhaseType | undefined {
    switch (currentPhase) {
      case 'plot_outline': return undefined;
      case 'chapter_detail': return 'plot_outline';
      case 'final_edit': return 'chapter_detail';
      default: return undefined;
    }
  }

  /**
   * Get phase step number
   */
  private getPhaseStep(phase: PhaseType): number {
    switch (phase) {
      case 'plot_outline': return 1;
      case 'chapter_detail': return 2;
      case 'final_edit': return 3;
      default: return 1;
    }
  }

  /**
   * Generate unique ID
   */
  private generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  /**
   * Get phase display name
   */
  getPhaseDisplayName(phase: PhaseType): string {
    switch (phase) {
      case 'plot_outline': return 'Draft';
      case 'chapter_detail': return 'Refined';
      case 'final_edit': return 'Approved';

      default: return phase;
    }
  }

  /**
   * Get phase description
   */
  getPhaseDescription(phase: PhaseType): string {
    switch (phase) {
      case 'plot_outline': return 'Create and refine the plot outline for your chapter';
      case 'chapter_detail': return 'Develop the chapter content with character and rater feedback';
      case 'final_edit': return 'Review and finalize the chapter with editor suggestions';

      default: return '';
    }
  }

  /**
   * Update phase validation result
   */
  updatePhaseValidation(phase: PhaseType, validation: Partial<PhaseValidationResult>): void {
    const currentValidation = this.validationResultSubject.value;
    const updatedValidation: PhaseValidationResult = {
      ...currentValidation,
      ...validation,
      nextPhase: this.getNextPhase(phase),
      previousPhase: this.getPreviousPhase(phase)
    };
    
    this.validationResultSubject.next(updatedValidation);
  }

  /**
   * Update phase data
   */
  updatePhaseData(storyId: string, phase: PhaseType, data: any): void {
    const state = this.getCurrentState();
    if (!state) return;

    // Update specific phase data
    switch (phase) {
      case 'plot_outline':
        if (data.outline) {
          Object.assign(state.phases.plotOutline.outline, data.outline);
        }
        if (data.draftSummary !== undefined) {
          state.phases.plotOutline.draftSummary = data.draftSummary;
        }
        if (data.conversation) {
          Object.assign(state.phases.plotOutline.conversation, data.conversation);
        }
        break;

      case 'chapter_detail':
        if (data.chapterDraft) {
          Object.assign(state.phases.chapterDetailer.chapterDraft, data.chapterDraft);
        }
        if (data.feedbackIntegration) {
          Object.assign(state.phases.chapterDetailer.feedbackIntegration, data.feedbackIntegration);
        }
        if (data.conversation) {
          Object.assign(state.phases.chapterDetailer.conversation, data.conversation);
        }
        break;

      case 'final_edit':
        if (data.finalChapter) {
          Object.assign(state.phases.finalEdit.finalChapter, data.finalChapter);
        }
        if (data.reviewSelection) {
          Object.assign(state.phases.finalEdit.reviewSelection, data.reviewSelection);
        }
        if (data.conversation) {
          Object.assign(state.phases.finalEdit.conversation, data.conversation);
        }
        break;
    }

    // Update metadata
    state.metadata.lastModified = new Date();

    // Emit updated state
    this.chapterComposeStateSubject.next(state);
    this.updateValidationResult(state);

    // Save to local storage if story ID is provided
    if (storyId) {
      const story = this.localStorageService.loadStory(storyId);
      if (story) {
        story.chapterCompose = state;
        this.localStorageService.saveStory(story);
      }
    }
  }

  // ============================================================================
  // PHASE VALIDATION INTEGRATION FOR THREE-PHASE CHAPTER COMPOSE SYSTEM (WRI-49)
  // ============================================================================

  /**
   * Validate phase transition using the backend API
   */
  validatePhaseTransitionAPI(
    fromPhase: PhaseType,
    toPhase: PhaseType,
    story: Story,
    chapterComposeState: ChapterComposeState
  ): Observable<PhaseTransitionResponse> {
    const phaseOutput = this.getPhaseOutput(fromPhase, chapterComposeState);
    
    const request: PhaseTransitionRequest = {
      from_phase: this.convertPhaseTypeToAPI(fromPhase),
      to_phase: this.convertPhaseTypeToAPI(toPhase),
      phase_output: phaseOutput,
      story_context: {
        worldbuilding: story.general.worldbuilding,
        story_summary: story.story.summary,
        previous_chapters: story.story.chapters.map(ch => ({
          number: ch.number,
          title: ch.title,
          content: ch.content
        })),
        characters: Array.from(story.characters.values())
          .filter(c => !c.isHidden)
          .map(c => ({
            name: c.name,
            basicBio: c.basicBio,
            personality: c.personality,
            motivations: c.motivations
          })),
        current_phase_status: {
          plot_outline: chapterComposeState.phases.plotOutline.status,
          chapter_detail: chapterComposeState.phases.chapterDetailer.status,
          final_edit: chapterComposeState.phases.finalEdit.status
        }
      }
    };

    return this.apiService.validatePhaseTransition(request).pipe(
      map((response: PhaseTransitionResponse) => {
        // Update local validation result based on API response
        this.updatePhaseValidation(fromPhase, {
          canAdvance: response.valid,
          validationErrors: response.valid ? [] : response.validation_results
            .filter(result => !result.passed)
            .map(result => result.message),
          requirements: response.recommendations
        });

        return response;
      }),
      catchError((error) => {
        console.error('Phase validation API error:', error);
        // Fallback to local validation on API error
        this.updateValidationResult(chapterComposeState);
        return of({
          valid: false,
          overall_score: 0,
          validation_results: [{
            criterion: 'API Error',
            passed: false,
            message: 'Unable to validate phase transition. Please try again.',
            score: 0
          }],
          recommendations: ['Please check your connection and try again.'],
          metadata: { error: error.message || 'Unknown error' }
        } as PhaseTransitionResponse);
      })
    );
  }

  /**
   * Attempt phase transition with API validation
   */
  attemptPhaseTransitionWithValidation(
    toPhase: PhaseType,
    story: Story,
    chapterComposeState: ChapterComposeState
  ): Observable<{ success: boolean; message: string; validationResponse?: PhaseTransitionResponse }> {
    const currentPhase = this.currentPhaseSubject.value;
    
    return this.validatePhaseTransitionAPI(currentPhase, toPhase, story, chapterComposeState).pipe(
      map((validationResponse: PhaseTransitionResponse) => {
        if (validationResponse.valid) {
          // Proceed with phase transition
          this.transitionToPhase(toPhase);
          return {
            success: true,
            message: `Successfully transitioned to ${this.getPhaseDisplayName(toPhase)} phase.`,
            validationResponse
          };
        } else {
          // Phase transition not allowed
          const failedCriteria = validationResponse.validation_results
            .filter(result => !result.passed)
            .map(result => result.message)
            .join(', ');
          
          return {
            success: false,
            message: `Cannot transition to ${this.getPhaseDisplayName(toPhase)} phase. Issues: ${failedCriteria}`,
            validationResponse
          };
        }
      })
    );
  }

  /**
   * Get phase output for validation
   */
  private getPhaseOutput(phase: PhaseType, chapterComposeState: ChapterComposeState): string {
    switch (phase) {
      case 'plot_outline': {
        const outlineItems = Array.from(chapterComposeState.phases.plotOutline.outline.items.values());
        return outlineItems
          .sort((a, b) => a.order - b.order)
          .map(item => `${item.title}: ${item.description}`)
          .join('\n\n');
      }

      case 'chapter_detail':
        return chapterComposeState.phases.chapterDetailer.chapterDraft.content || '';

      case 'final_edit':
        return chapterComposeState.phases.finalEdit.finalChapter.content || 
               chapterComposeState.phases.chapterDetailer.chapterDraft.content || '';

      default:
        return '';
    }
  }

  /**
   * Convert internal phase type to API phase type
   */
  private convertPhaseTypeToAPI(phase: PhaseType): 'plot_outline' | 'chapter_detail' | 'final_edit' {
    switch (phase) {
      case 'plot_outline': return 'plot_outline';
      case 'chapter_detail': return 'chapter_detail';
      case 'final_edit': return 'final_edit';
      default: return 'plot_outline';
    }
  }

  /**
   * Get validation score for a phase
   */
  getPhaseValidationScore(phase: PhaseType, chapterComposeState: ChapterComposeState): number {
    // This could be enhanced to call the API for real-time scoring
    // For now, return a basic score based on completion status
    const phaseKey = this.getPhasePropertyKey(phase);
    const phaseData = chapterComposeState.phases[phaseKey];
    
    switch (phaseData.status) {
      case 'completed': return 100;
      case 'active': return 50;
      case 'paused': return 25;
      default: return 0;
    }
  }

  /**
   * Check if phase can be advanced based on API validation
   */
  canAdvancePhaseWithAPI(
    story: Story,
    chapterComposeState: ChapterComposeState
  ): Observable<boolean> {
    const currentPhase = this.currentPhaseSubject.value;
    const nextPhase = this.getNextPhase(currentPhase);
    
    if (!nextPhase) {
      return of(false);
    }

    return this.validatePhaseTransitionAPI(currentPhase, nextPhase, story, chapterComposeState).pipe(
      map(response => response.valid),
      catchError(() => of(false))
    );
  }
}
