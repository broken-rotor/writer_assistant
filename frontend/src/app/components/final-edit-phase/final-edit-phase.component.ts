import { Component, Input, Output, EventEmitter, OnInit, OnDestroy, ChangeDetectorRef, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import {
  Story,
  FinalEditPhase,
  ChatMessage,
  ReviewItem
} from '../../models/story.model';
import { ChatInterfaceComponent, ChatInterfaceConfig, MessageActionEvent } from '../chat-interface/chat-interface.component';
import { ReviewFeedbackPanelComponent, ReviewFeedbackPanelConfig, ReviewSelectionEvent, ReviewRequestEvent, AddToChatEvent } from '../review-feedback-panel/review-feedback-panel.component';
import { GenerationService } from '../../services/generation.service';
import { ConversationService } from '../../services/conversation.service';
import { PhaseStateService } from '../../services/phase-state.service';
import { ReviewService, QualityScore } from '../../services/review.service';
import { StoryService } from '../../services/story.service';
import { ToastService } from '../../services/toast.service';
import { NewlineToBrPipe } from '../../pipes/newline-to-br.pipe';

interface ChapterRevision {
  id: string;
  name: string;
  content: string;
  title: string;
  wordCount: number;
  created: Date;
  appliedReviews: string[]; // IDs of reviews applied in this revision
  changesSummary: string;
  qualityScore?: QualityScore;
  isActive: boolean;
}

interface QualityAssessment {
  overallScore: number;
  categoryScores: {
    characterConsistency: number;
    narrativeFlow: number;
    literaryQuality: number;
    genreSpecific: number;
  };
  readinessLevel: 'needs-work' | 'good' | 'excellent';
  improvementAreas: string[];
  strengths: string[];
}

@Component({
  selector: 'app-final-edit-phase',
  standalone: true,
  imports: [
    CommonModule, 
    FormsModule, 
    ChatInterfaceComponent,
    ReviewFeedbackPanelComponent,
    NewlineToBrPipe
  ],
  templateUrl: './final-edit-phase.component.html',
  styleUrls: ['./final-edit-phase.component.scss']
})
export class FinalEditPhaseComponent implements OnInit, OnDestroy {
  @Input() story!: Story;
  @Input() chapterNumber = 1;
  @Output() phaseCompleted = new EventEmitter<void>();
  @Output() chapterFinalized = new EventEmitter<{ content: string; title: string; }>();

  // Chapter content from Phase 2 (read-only display)
  chapterDraftFromPhase2 = '';
  chapterTitleFromPhase2 = '';
  chapterAnalytics = {
    wordCount: 0,
    readingTime: 0,
    complexity: 'medium' as 'low' | 'medium' | 'high'
  };

  // Final chapter revisions
  revisions: ChapterRevision[] = [];
  currentRevisionId = '';
  nextRevisionNumber = 1;

  // Review integration
  selectedReviews: ReviewItem[] = [];
  appliedReviewIds = new Set<string>();

  // Quality assessment
  qualityAssessment: QualityAssessment | null = null;
  showQualityDetails = false;

  // Chat interface configuration
  chatConfig: ChatInterfaceConfig = {
    phase: 'final_edit',
    storyId: '',
    chapterNumber: 1,
    enableBranching: true,
    placeholder: 'Apply selected reviews or request final edits...',
    showTimestamps: true,
    allowMessageEditing: true
  };

  // Review panel configuration
  reviewConfig: ReviewFeedbackPanelConfig = {
    storyId: '',
    chapterNumber: 1,
    chapterContent: '',
    showRequestButtons: true,
    showChatIntegration: true,
    showQualityScore: true,
    maxHeight: '400px'
  };

  // UI state
  showRevisionHistory = false;
  showChapterPreview = true;
  isProcessingRevision = false;
  isFinalizingChapter = false;
  selectedRevisionForComparison: string | null = null;
  
  // Finalization state
  canFinalize = false;
  finalizationChecks = {
    hasAppliedReviews: false,
    qualityThresholdMet: false,
    userConfirmed: false
  };

  private destroy$ = new Subject<void>();
  private generationService = inject(GenerationService);
  private conversationService = inject(ConversationService);
  private phaseStateService = inject(PhaseStateService);
  private reviewService = inject(ReviewService);
  private storyService = inject(StoryService);
  private toastService = inject(ToastService);
  private cdr = inject(ChangeDetectorRef);

  ngOnInit(): void {
    this.initializeComponent();
    this.loadChapterFromPhase2();
    this.loadExistingRevisions();
    this.setupQualityAssessment();
    this.updateFinalizationStatus();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private initializeComponent(): void {
    // Configure chat interface
    this.chatConfig.storyId = this.story.id;
    this.chatConfig.chapterNumber = this.chapterNumber;

    // Configure review panel
    this.reviewConfig.storyId = this.story.id;
    this.reviewConfig.chapterNumber = this.chapterNumber;
  }

  private loadChapterFromPhase2(): void {
    const chapterDetailerPhase = this.story.chapterCompose?.phases?.chapterDetailer;
    if (chapterDetailerPhase?.chapterDraft) {
      this.chapterDraftFromPhase2 = chapterDetailerPhase.chapterDraft.content || '';
      this.chapterTitleFromPhase2 = chapterDetailerPhase.chapterDraft.title || '';
      
      // Update analytics
      this.chapterAnalytics.wordCount = this.chapterDraftFromPhase2.split(/\s+/).length;
      this.chapterAnalytics.readingTime = Math.ceil(this.chapterAnalytics.wordCount / 200); // ~200 words per minute
      
      // Update review config with chapter content
      this.reviewConfig.chapterContent = this.chapterDraftFromPhase2;
    }
  }

  private loadExistingRevisions(): void {
    const finalEditPhase = this.story.chapterCompose?.phases?.finalEdit;
    if (finalEditPhase?.finalChapter) {
      // Create initial revision from final chapter
      const initialRevision: ChapterRevision = {
        id: 'initial',
        name: 'Initial Draft',
        content: finalEditPhase.finalChapter.content || this.chapterDraftFromPhase2,
        title: finalEditPhase.finalChapter.title || this.chapterTitleFromPhase2,
        wordCount: finalEditPhase.finalChapter.wordCount || this.chapterAnalytics.wordCount,
        created: new Date(),
        appliedReviews: [],
        changesSummary: 'Initial chapter draft from Phase 2',
        isActive: true
      };

      this.revisions = [initialRevision];
      this.currentRevisionId = 'initial';
      this.nextRevisionNumber = 2;

      // Load applied reviews
      if (finalEditPhase.reviewSelection?.appliedReviews) {
        this.appliedReviewIds = new Set(finalEditPhase.reviewSelection.appliedReviews);
      }
    } else {
      // Create initial revision from Phase 2 data
      this.createInitialRevision();
    }
  }

  private createInitialRevision(): void {
    const initialRevision: ChapterRevision = {
      id: 'initial',
      name: 'Initial Draft',
      content: this.chapterDraftFromPhase2,
      title: this.chapterTitleFromPhase2,
      wordCount: this.chapterAnalytics.wordCount,
      created: new Date(),
      appliedReviews: [],
      changesSummary: 'Initial chapter draft from Phase 2',
      isActive: true
    };

    this.revisions = [initialRevision];
    this.currentRevisionId = 'initial';
    this.nextRevisionNumber = 2;
  }

  private setupQualityAssessment(): void {
    // Initialize quality assessment
    this.qualityAssessment = {
      overallScore: 0,
      categoryScores: {
        characterConsistency: 0,
        narrativeFlow: 0,
        literaryQuality: 0,
        genreSpecific: 0
      },
      readinessLevel: 'needs-work',
      improvementAreas: [],
      strengths: []
    };

    // Load quality scores from review service
    this.loadQualityScores();
  }

  private loadQualityScores(): void {
    // This would integrate with the review service to get quality scores
    // For now, we'll set up the structure
    this.reviewService.qualityScore$
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (qualityScore: QualityScore | null) => {
          if (qualityScore && this.qualityAssessment) {
            this.qualityAssessment.overallScore = qualityScore.overall;
            // Map quality score categories to our assessment structure
            this.updateQualityAssessment(qualityScore);
          }
        },
        error: (error: any) => {
          console.warn('Could not load quality scores:', error);
        }
      });
  }

  private updateQualityAssessment(qualityScore: QualityScore): void {
    if (!this.qualityAssessment) return;

    // Update readiness level based on overall score
    if (qualityScore.overall >= 85) {
      this.qualityAssessment.readinessLevel = 'excellent';
    } else if (qualityScore.overall >= 70) {
      this.qualityAssessment.readinessLevel = 'good';
    } else {
      this.qualityAssessment.readinessLevel = 'needs-work';
    }

    this.updateFinalizationStatus();
  }

  public updateFinalizationStatus(): void {
    this.finalizationChecks.hasAppliedReviews = this.appliedReviewIds.size > 0;
    this.finalizationChecks.qualityThresholdMet = 
      this.qualityAssessment?.overallScore ? this.qualityAssessment.overallScore >= 70 : false;

    this.canFinalize = 
      this.finalizationChecks.hasAppliedReviews && 
      this.finalizationChecks.qualityThresholdMet;
  }

  // Event handlers for review panel
  onReviewSelectionChanged(event: ReviewSelectionEvent): void {
    this.selectedReviews = event.selectedItems;
    this.cdr.detectChanges();
  }

  onReviewRequested(event: ReviewRequestEvent): void {
    this.toastService.showInfo(`Requesting ${event.requestType} review...`);
    // The review service will handle the actual request
  }

  onAddToChat(event: AddToChatEvent): void {
    if (event.selectedReviews.length === 0) {
      this.toastService.showWarning('Please select reviews to add to chat');
      return;
    }

    // Create a chat message with selected reviews
    const reviewSummary = event.selectedReviews.map(review => 
      `- ${review.title}: ${review.suggestion}`
    ).join('\n');

    const chatMessage = `Please apply the following reviews to the chapter:\n\n${reviewSummary}`;
    
    if (event.userComment) {
      chatMessage + `\n\nAdditional notes: ${event.userComment}`;
    }

    // Add message to chat (this would be handled by the chat interface)
    this.toastService.showSuccess(`Added ${event.selectedReviews.length} reviews to chat`);
  }

  // Event handlers for chat interface
  onMessageSent(message: ChatMessage): void {
    // Handle new chat messages
    this.processRevisionRequest(message);
  }

  onMessageAction(event: MessageActionEvent): void {
    // Handle chat message actions (edit, delete, branch, reply)
    console.log('Message action:', event);
  }

  private processRevisionRequest(message: ChatMessage): void {
    if (message.type === 'user' && !this.isProcessingRevision) {
      this.isProcessingRevision = true;
      
      // This would integrate with the generation service to process the revision
      // For now, we'll simulate the process
      setTimeout(() => {
        this.createNewRevision('AI-generated revision based on user request');
        this.isProcessingRevision = false;
      }, 2000);
    }
  }

  private createNewRevision(changesSummary: string): void {
    const currentRevision = this.getCurrentRevision();
    if (!currentRevision) return;

    const newRevision: ChapterRevision = {
      id: `revision-${this.nextRevisionNumber}`,
      name: `Revision ${this.nextRevisionNumber}`,
      content: currentRevision.content, // This would be updated with actual changes
      title: currentRevision.title,
      wordCount: currentRevision.wordCount,
      created: new Date(),
      appliedReviews: [...this.selectedReviews.map(r => r.id)],
      changesSummary,
      isActive: true
    };

    // Mark current revision as inactive
    currentRevision.isActive = false;

    // Add new revision
    this.revisions.push(newRevision);
    this.currentRevisionId = newRevision.id;
    this.nextRevisionNumber++;

    // Update applied reviews
    this.selectedReviews.forEach(review => {
      this.appliedReviewIds.add(review.id);
    });

    this.updateFinalizationStatus();
    this.savePhaseState();
    this.toastService.showSuccess('New revision created');
  }

  // Revision history methods
  toggleRevisionHistory(): void {
    this.showRevisionHistory = !this.showRevisionHistory;
  }

  selectRevision(revisionId: string): void {
    const revision = this.revisions.find(r => r.id === revisionId);
    if (revision) {
      // Mark all revisions as inactive
      this.revisions.forEach(r => r.isActive = false);
      
      // Mark selected revision as active
      revision.isActive = true;
      this.currentRevisionId = revisionId;
      
      this.cdr.detectChanges();
    }
  }

  compareRevisions(revisionId: string): void {
    this.selectedRevisionForComparison = revisionId;
    // This would open a comparison view
  }

  rollbackToRevision(revisionId: string): void {
    const revision = this.revisions.find(r => r.id === revisionId);
    if (revision) {
      const confirmRollback = confirm(`Are you sure you want to rollback to "${revision.name}"? This will create a new revision with the content from that version.`);
      
      if (confirmRollback) {
        this.createNewRevision(`Rolled back to ${revision.name}`);
        this.toastService.showInfo(`Rolled back to ${revision.name}`);
      }
    }
  }

  getCurrentRevision(): ChapterRevision | undefined {
    return this.revisions.find(r => r.id === this.currentRevisionId);
  }

  // Quality assessment methods
  toggleQualityDetails(): void {
    this.showQualityDetails = !this.showQualityDetails;
  }

  getReadinessColor(): string {
    if (!this.qualityAssessment) return 'gray';
    
    switch (this.qualityAssessment.readinessLevel) {
      case 'excellent': return 'green';
      case 'good': return 'orange';
      case 'needs-work': return 'red';
      default: return 'gray';
    }
  }

  getReadinessLabel(): string {
    if (!this.qualityAssessment) return 'Unknown';
    
    switch (this.qualityAssessment.readinessLevel) {
      case 'excellent': return 'Ready to Publish';
      case 'good': return 'Good Quality';
      case 'needs-work': return 'Needs Improvement';
      default: return 'Unknown';
    }
  }

  // Chapter finalization methods
  finalizeChapter(): void {
    if (!this.canFinalize) {
      this.toastService.showWarning('Chapter is not ready for finalization');
      return;
    }

    const currentRevision = this.getCurrentRevision();
    if (!currentRevision) {
      this.toastService.showError('No active revision found');
      return;
    }

    const confirmFinalize = confirm('Are you sure you want to finalize this chapter? This will save it to your story and move to the next chapter.');
    
    if (confirmFinalize) {
      this.isFinalizingChapter = true;
      
      // Save the final chapter
      this.saveChapterToStory(currentRevision);
    }
  }

  private saveChapterToStory(revision: ChapterRevision): void {
    // Update the story with the finalized chapter
    const chapterData = {
      content: revision.content,
      title: revision.title,
      wordCount: revision.wordCount,
      appliedReviews: Array.from(this.appliedReviewIds),
      qualityScore: this.qualityAssessment?.overallScore || 0,
      finalizedAt: new Date()
    };

    // Save to story service
    this.storyService.saveChapter(this.story.id, this.chapterNumber, chapterData)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.toastService.showSuccess('Chapter finalized successfully!');
          this.chapterFinalized.emit({
            content: revision.content,
            title: revision.title
          });
          this.phaseCompleted.emit();
          this.isFinalizingChapter = false;
        },
        error: (error: any) => {
          console.error('Error finalizing chapter:', error);
          this.toastService.showError('Error finalizing chapter');
          this.isFinalizingChapter = false;
        }
      });
  }

  private savePhaseState(): void {
    // Save the current phase state
    const finalEditPhase: Partial<FinalEditPhase> = {
      finalChapter: {
        content: this.getCurrentRevision()?.content || '',
        title: this.getCurrentRevision()?.title || '',
        wordCount: this.getCurrentRevision()?.wordCount || 0,
        version: this.nextRevisionNumber - 1
      },
      reviewSelection: {
        availableReviews: [], // This would be populated from the review service
        selectedReviews: this.selectedReviews.map(r => r.id),
        appliedReviews: Array.from(this.appliedReviewIds)
      },
      status: 'active',
      progress: {
        reviewsApplied: this.appliedReviewIds.size,
        totalReviews: this.selectedReviews.length,
        lastActivity: new Date()
      }
    };

    // Save through phase state service
    this.phaseStateService.updatePhaseData(this.story.id, 'final_edit', finalEditPhase);
  }

  // UI helper methods
  toggleChapterPreview(): void {
    this.showChapterPreview = !this.showChapterPreview;
  }

  getProgressPercentage(): number {
    if (!this.qualityAssessment) return 0;
    return Math.round(this.qualityAssessment.overallScore);
  }

  getAppliedReviewsCount(): number {
    return this.appliedReviewIds.size;
  }

  getTotalRevisionsCount(): number {
    return this.revisions.length;
  }
}
