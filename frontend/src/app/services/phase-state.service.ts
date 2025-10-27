import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { 
  ChapterComposeState, 
  PhaseTransition,
  PlotOutlinePhase,
  ChapterDetailerPhase,
  FinalEditPhase,
  ConversationThread,
  ChatMessage,
  OutlineItem,
  EnhancedFeedbackItem
} from '../models/story.model';
import { LocalStorageService } from './local-storage.service';

export type PhaseType = 'plot-outline' | 'chapter-detailer' | 'final-edit';

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
  private currentPhaseSubject = new BehaviorSubject<PhaseType>('plot-outline');
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

  constructor(private localStorageService: LocalStorageService) {}

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
        phase: 'plot-outline'
      }
    };

    const chapterComposeState: ChapterComposeState = {
      currentPhase: 'plot-outline',
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
            metadata: { ...initialConversation.metadata, phase: 'chapter-detailer' }
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
            metadata: { ...initialConversation.metadata, phase: 'final-edit' }
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
        phaseHistory: ['plot-outline'],
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
          'plot-outline': false,
          'chapter-detailer': false,
          'final-edit': false
        },
        estimatedTimeRemaining: undefined
      },
      metadata: {
        created: now,
        lastModified: now,
        version: '1.0.0',
        migrationSource: 'manual'
      }
    };

    this.chapterComposeStateSubject.next(chapterComposeState);
    this.currentPhaseSubject.next('plot-outline');
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
      case 'plot-outline':
        Object.assign(state.phases.plotOutline.progress, progress);
        break;
      case 'chapter-detailer':
        Object.assign(state.phases.chapterDetailer.progress, progress);
        break;
      case 'final-edit':
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
      case 'chapter-detailer':
        if (state.currentPhase === 'plot-outline') {
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

      case 'final-edit':
        if (state.currentPhase === 'chapter-detailer') {
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
      case 'plot-outline': return 'plotOutline';
      case 'chapter-detailer': return 'chapterDetailer';
      case 'final-edit': return 'finalEdit';
      default: throw new Error(`Unknown phase: ${phase}`);
    }
  }

  /**
   * Get next phase in sequence
   */
  private getNextPhase(currentPhase: PhaseType): PhaseType | undefined {
    switch (currentPhase) {
      case 'plot-outline': return 'chapter-detailer';
      case 'chapter-detailer': return 'final-edit';
      case 'final-edit': return undefined;
      default: return undefined;
    }
  }

  /**
   * Get previous phase in sequence
   */
  private getPreviousPhase(currentPhase: PhaseType): PhaseType | undefined {
    switch (currentPhase) {
      case 'plot-outline': return undefined;
      case 'chapter-detailer': return 'plot-outline';
      case 'final-edit': return 'chapter-detailer';
      default: return undefined;
    }
  }

  /**
   * Get phase step number
   */
  private getPhaseStep(phase: PhaseType): number {
    switch (phase) {
      case 'plot-outline': return 1;
      case 'chapter-detailer': return 2;
      case 'final-edit': return 3;
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
      case 'plot-outline': return 'Draft';
      case 'chapter-detailer': return 'Refined';
      case 'final-edit': return 'Approved';
      default: return phase;
    }
  }

  /**
   * Get phase description
   */
  getPhaseDescription(phase: PhaseType): string {
    switch (phase) {
      case 'plot-outline': return 'Create and refine the plot outline for your chapter';
      case 'chapter-detailer': return 'Develop the chapter content with character and rater feedback';
      case 'final-edit': return 'Review and finalize the chapter with editor suggestions';
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
}
