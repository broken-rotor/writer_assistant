import { Component, OnInit, OnDestroy, Input, Output, EventEmitter, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subject, takeUntil } from 'rxjs';
import { PhaseStateService, PhaseType, PhaseValidationResult } from '../../services/phase-state.service';
import { ChapterComposeState } from '../../models/story.model';

@Component({
  selector: 'app-phase-navigation',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './phase-navigation.component.html',
  styleUrl: './phase-navigation.component.scss'
})
export class PhaseNavigationComponent implements OnInit, OnDestroy {
  @Input() chapterNumber = 1;
  @Input() chapterTitle = '';
  @Output() phaseChanged = new EventEmitter<PhaseType>();

  currentPhase: PhaseType = 'plot_outline';
  chapterComposeState: ChapterComposeState | null = null;
  validationResult: PhaseValidationResult = {
    canAdvance: false,
    canRevert: false,
    requirements: [],
    validationErrors: []
  };

  private destroy$ = new Subject<void>();

  readonly phases: { key: PhaseType; label: string; description: string }[] = [
    { key: 'plot_outline', label: 'Draft', description: 'Create plot outline' },
    { key: 'chapter_detail', label: 'Refined', description: 'Develop chapter content' },
    { key: 'final_edit', label: 'Approved', description: 'Final review and edit' }
  ];

  private phaseStateService = inject(PhaseStateService);

  ngOnInit(): void {
    // Subscribe to phase state changes
    this.phaseStateService.currentPhase$
      .pipe(takeUntil(this.destroy$))
      .subscribe(phase => {
        this.currentPhase = phase;
      });

    // Subscribe to chapter compose state changes
    this.phaseStateService.chapterComposeState$
      .pipe(takeUntil(this.destroy$))
      .subscribe(state => {
        this.chapterComposeState = state;
      });

    // Subscribe to validation result changes
    this.phaseStateService.validationResult$
      .pipe(takeUntil(this.destroy$))
      .subscribe(result => {
        this.validationResult = result;
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Get phase display name
   */
  getPhaseDisplayName(phase: PhaseType): string {
    return this.phaseStateService.getPhaseDisplayName(phase);
  }

  /**
   * Get phase description
   */
  getPhaseDescription(phase: PhaseType): string {
    return this.phaseStateService.getPhaseDescription(phase);
  }

  /**
   * Check if phase is completed
   */
  isPhaseCompleted(phase: PhaseType): boolean {
    if (!this.chapterComposeState) return false;
    return this.chapterComposeState.overallProgress.phaseCompletionStatus[phase];
  }

  /**
   * Check if phase is current
   */
  isCurrentPhase(phase: PhaseType): boolean {
    return this.currentPhase === phase;
  }

  /**
   * Check if phase is accessible (current or completed)
   */
  isPhaseAccessible(phase: PhaseType): boolean {
    if (!this.chapterComposeState) return phase === 'plot_outline';
    
    const phaseOrder: PhaseType[] = ['plot_outline', 'chapter_detail', 'final_edit'];
    const currentIndex = phaseOrder.indexOf(this.currentPhase);
    const targetIndex = phaseOrder.indexOf(phase);
    
    // Can access current phase or any completed phase
    return targetIndex <= currentIndex || this.isPhaseCompleted(phase);
  }

  /**
   * Get phase progress percentage
   */
  getPhaseProgress(phase: PhaseType): number {
    if (!this.chapterComposeState) return 0;

    switch (phase) {
      case 'plot_outline': {
        const plotProgress = this.chapterComposeState.phases.plotOutline.progress;
        if (plotProgress.totalItems === 0) return 0;
        return Math.round((plotProgress.completedItems / plotProgress.totalItems) * 100);
      }

      case 'chapter_detail': {
        const detailerProgress = this.chapterComposeState.phases.chapterDetailer.progress;
        if (detailerProgress.totalFeedbackItems === 0) return 0;
        return Math.round((detailerProgress.feedbackIncorporated / detailerProgress.totalFeedbackItems) * 100);
      }

      case 'final_edit': {
        const editProgress = this.chapterComposeState.phases.finalEdit.progress;
        if (editProgress.totalReviews === 0) return 0;
        return Math.round((editProgress.reviewsApplied / editProgress.totalReviews) * 100);
      }

      default:
        return 0;
    }
  }

  /**
   * Get overall progress percentage
   */
  getOverallProgress(): number {
    if (!this.chapterComposeState) return 0;
    
    const progress = this.chapterComposeState.overallProgress;
    return Math.round((progress.currentStep / progress.totalSteps) * 100);
  }

  /**
   * Navigate to specific phase
   */
  async navigateToPhase(targetPhase: PhaseType): Promise<void> {
    if (!this.isPhaseAccessible(targetPhase) || targetPhase === this.currentPhase) {
      return;
    }

    try {
      let success = false;
      
      if (this.isPhaseAfter(targetPhase, this.currentPhase)) {
        // Moving forward - need to advance through phases
        success = await this.advanceToPhase(targetPhase);
      } else {
        // Moving backward - can jump directly to completed phases
        success = await this.revertToPhase();
      }

      if (success) {
        this.phaseChanged.emit(targetPhase);
      }
    } catch (error) {
      console.error('Error navigating to phase:', error);
    }
  }

  /**
   * Advance to next phase
   */
  async advanceToNext(): Promise<void> {
    try {
      const success = await this.phaseStateService.advanceToNext();
      if (success) {
        this.phaseChanged.emit(this.phaseStateService.getCurrentPhase());
      }
    } catch (error) {
      console.error('Error advancing to next phase:', error);
    }
  }

  /**
   * Revert to previous phase
   */
  async revertToPrevious(): Promise<void> {
    try {
      const success = await this.phaseStateService.revertToPrevious();
      if (success) {
        this.phaseChanged.emit(this.phaseStateService.getCurrentPhase());
      }
    } catch (error) {
      console.error('Error reverting to previous phase:', error);
    }
  }

  /**
   * Check if target phase is after current phase
   */
  private isPhaseAfter(targetPhase: PhaseType, currentPhase: PhaseType): boolean {
    const phaseOrder: PhaseType[] = ['plot_outline', 'chapter_detail', 'final_edit'];
    return phaseOrder.indexOf(targetPhase) > phaseOrder.indexOf(currentPhase);
  }

  /**
   * Advance through phases to reach target
   */
  private async advanceToPhase(targetPhase: PhaseType): Promise<boolean> {
    let currentPhase = this.currentPhase;
    
    while (currentPhase !== targetPhase) {
      const success = await this.phaseStateService.advanceToNext();
      if (!success) return false;
      
      currentPhase = this.phaseStateService.getCurrentPhase();
    }
    
    return true;
  }

  /**
   * Revert to target phase
   */
  private async revertToPhase(): Promise<boolean> {
    // For now, we'll implement simple reversion
    // In a more complex implementation, we might need to handle multiple steps
    return await this.phaseStateService.revertToPrevious();
  }

  /**
   * Get validation error message for display
   */
  getValidationErrorMessage(): string {
    if (!this.validationResult || !this.validationResult.validationErrors?.length) return '';
    return this.validationResult.validationErrors[0];
  }

  /**
   * Get requirements message for display
   */
  getRequirementsMessage(): string {
    if (!this.validationResult || !this.validationResult.requirements?.length) return '';
    return `Requirements: ${this.validationResult.requirements.join(', ')}`;
  }

  /**
   * Check if advance button should be shown
   */
  showAdvanceButton(): boolean {
    return this.validationResult?.nextPhase !== undefined;
  }

  /**
   * Check if revert button should be shown
   */
  showRevertButton(): boolean {
    return this.validationResult?.previousPhase !== undefined;
  }

  /**
   * TrackBy function for requirements list to improve performance
   */
  trackByRequirement(index: number, requirement: string): string {
    return requirement;
  }

  /**
   * TrackBy function for validation errors list to improve performance
   */
  trackByError(index: number, error: string): string {
    return error;
  }
}
