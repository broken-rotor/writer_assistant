import { Component, Input, Output, EventEmitter, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatChipsModule } from '@angular/material/chips';
import { Subscription } from 'rxjs';

import { CollapsibleSectionComponent } from '../collapsible-section/collapsible-section.component';
import { FeedbackSelectorComponent, FeedbackSelection } from '../feedback-selector/feedback-selector.component';
import { ChapterEditorService, ChapterEditingState } from '../../services/chapter-editor.service';
import { 
  Story, 
  Chapter
} from '../../models/story.model';

@Component({
  selector: 'app-chapter-editor-tab',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatIconModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatChipsModule,
    CollapsibleSectionComponent,
    FeedbackSelectorComponent
  ],
  templateUrl: './chapter-editor-tab.component.html',
  styleUrl: './chapter-editor-tab.component.scss'
})
export class ChapterEditorTabComponent implements OnInit, OnDestroy {
  @Input() story: Story | null = null;
  @Input() chapter: Chapter | null = null;
  @Input() disabled = false;

  @Output() backToStory = new EventEmitter<void>();
  @Output() saveChapter = new EventEmitter<Chapter>();
  @Output() chapterChange = new EventEmitter<Chapter>();

  state: ChapterEditingState | null = null;
  private stateSubscription?: Subscription;

  // Section expansion states
  basicsExpanded = true;
  feedbackExpanded = false;
  finalReviewExpanded = false;

  // Form data
  chapterTitle = '';
  chapterOutline = '';
  chapterContent = '';
  keyPlotItems: string[] = [];
  newPlotItem = '';
  userGuidance = '';

  private chapterEditorService = inject(ChapterEditorService);

  ngOnInit() {
    this.stateSubscription = this.chapterEditorService.state$.subscribe(state => {
      this.state = state;
      this.updateFormFromState();
      this.updateSectionStates();
    });

    if (this.chapter) {
      this.chapterEditorService.initializeChapterEditing(this.chapter);
      this.initializeFormData();
    }
  }

  ngOnDestroy() {
    this.stateSubscription?.unsubscribe();
  }

  private initializeFormData() {
    if (!this.chapter) return;

    this.chapterTitle = this.chapter.title || '';
    this.chapterOutline = this.chapter.plotPoint || '';
    this.chapterContent = this.chapter.content || '';
    this.keyPlotItems = [...(this.chapter.keyPlotItems || [])];
  }

  private updateFormFromState() {
    if (!this.state?.currentChapter) return;

    this.chapterTitle = this.state.currentChapter.title || '';
    this.chapterOutline = this.state.currentChapter.plotPoint || '';
    this.chapterContent = this.state.currentChapter.content || '';
    this.keyPlotItems = [...(this.state.currentChapter.keyPlotItems || [])];
    this.userGuidance = this.state.userGuidance || '';
  }

  private updateSectionStates() {
    if (!this.state) return;

    // Auto-collapse basics after generation
    if (this.chapterContent.trim().length > 0) {
      this.basicsExpanded = false;
    }

    // Show feedback section when content exists
    if (this.chapterContent.trim().length > 0) {
      this.feedbackExpanded = true;
    } else {
      this.feedbackExpanded = false;
    }

    // Show final review when feedback has been applied
    if (this.state.characterFeedback.length > 0 || this.state.raterFeedback.length > 0) {
      this.finalReviewExpanded = true;
    }
  }

  // Chapter content methods
  onTitleChange() {
    this.chapterEditorService.updateChapterTitle(this.chapterTitle);
    this.emitChapterChange();
  }

  onOutlineChange() {
    this.chapterEditorService.updateChapterPlotPoint(this.chapterOutline);
    this.emitChapterChange();
  }

  onContentChange() {
    this.chapterEditorService.updateChapterContent(this.chapterContent);
    this.emitChapterChange();
  }

  onAddPlotItem() {
    if (!this.newPlotItem.trim()) return;

    this.keyPlotItems.push(this.newPlotItem.trim());
    this.newPlotItem = '';
    this.updateChapterKeyPlotItems();
  }

  onRemovePlotItem(index: number) {
    this.keyPlotItems.splice(index, 1);
    this.updateChapterKeyPlotItems();
  }

  private updateChapterKeyPlotItems() {
    if (this.state?.currentChapter) {
      this.state.currentChapter.keyPlotItems = [...this.keyPlotItems];
      this.emitChapterChange();
    }
  }

  private emitChapterChange() {
    if (this.state?.currentChapter) {
      this.chapterChange.emit(this.state.currentChapter);
    }
  }

  // Generation methods
  onChatAboutOutline() {
    // TODO: Implement chat overlay for outline discussion
    console.log('Chat about outline - to be implemented');
  }

  onGenerateChapter() {
    if (!this.story) return;
    this.chapterEditorService.generateChapterFromOutline(this.story).subscribe({
      next: (_chapterText) => {
        // Chapter content is already updated in the service
        console.log('Chapter generated successfully');
      },
      error: (error) => {
        console.error('Failed to generate chapter:', error);
        // Error handling is already done in the service
      }
    });
  }

  onChatAboutContent() {
    // TODO: Implement chat overlay for content discussion
    console.log('Chat about content - to be implemented');
  }

  // Feedback methods
  onGetFeedback(event: { type: 'character' | 'rater', entityId: string, entityName: string, forceRefresh?: boolean }) {
    if (!this.story || !this.state?.currentChapter) return;

    switch (event.type) {
      case 'character':
        this.getCharacterFeedback(event.entityId, event.entityName, event.forceRefresh);
        break;
      case 'rater':
        this.getRaterFeedback(event.entityId, event.entityName, event.forceRefresh);
        break;
    }
  }

  private getCharacterFeedback(characterId: string, characterName: string, forceRefresh?: boolean) {
    if (!this.story) return;

    this.chapterEditorService.getCharacterFeedback(this.story, characterId, characterName, forceRefresh).subscribe({
      next: (feedback) => {
        console.log('Character feedback received:', feedback);
      },
      error: (error) => {
        console.error('Failed to get character feedback:', error);
      }
    });
  }

  private getRaterFeedback(raterId: string, raterName: string, forceRefresh?: boolean) {
    if (!this.story) return;

    this.chapterEditorService.getRaterFeedback(this.story, raterId, raterName, forceRefresh).subscribe({
      next: (feedback) => {
        console.log('Rater feedback received:', feedback);
      },
      error: (error) => {
        console.error('Failed to get rater feedback:', error);
      }
    });
  }



  onModifyChapter(event: { userGuidance: string, selectedFeedback: FeedbackSelection }) {
    if (!this.story || !this.state?.currentChapter) return;

    // Apply user guidance with selected feedback
    this.chapterEditorService.applyUserGuidance(event.userGuidance, this.story, event.selectedFeedback).subscribe({
      next: (_modifiedContent) => {
        console.log('Chapter modified successfully');
      },
      error: (error) => {
        console.error('Failed to modify chapter:', error);
      }
    });
  }

  onClearFeedback() {
    this.chapterEditorService.clearFeedback();
    console.log('Feedback cleared');
  }

  onClearQueuedFeedback() {
    this.chapterEditorService.clearQueuedFeedback();
    console.log('Queued feedback cleared');
  }

  onChatMessage(event: { type: 'character' | 'rater', id: string, message: string }) {
    // TODO: Implement chat with specific character/rater
    console.log('Chat message:', event);
  }

  onUserGuidanceChange(guidance: string) {
    this.userGuidance = guidance;
    // The service tracks userGuidance in state, but we don't need to update it here
    // since it gets updated when applyUserGuidance is called
  }

  // Final review methods
  onRequestFinalReview() {
    // TODO: Implement final editor review request
    console.log('Request final review - to be implemented');
  }

  onMarkChapterComplete() {
    // TODO: Implement chapter completion
    console.log('Mark chapter complete - to be implemented');
  }

  // Section toggle methods
  onToggleBasics(expanded: boolean) {
    this.basicsExpanded = expanded;
  }

  onToggleFeedback(expanded: boolean) {
    this.feedbackExpanded = expanded;
  }

  onToggleFinalReview(expanded: boolean) {
    this.finalReviewExpanded = expanded;
  }

  // Utility methods
  getWordCount(): number {
    return this.chapterContent.trim().split(/\s+/).filter(word => word.length > 0).length;
  }

  getBasicsCollapsedSummary(): string {
    const items = this.keyPlotItems.slice(0, 3);
    return items.length > 0 ? `[${items.join('] [')}]${this.keyPlotItems.length > 3 ? '...' : ''}` : '';
  }

  getFeedbackCollapsedSummary(): string {
    if (!this.state) return '';
    
    const charCount = this.state.characterFeedback.length;
    const raterCount = this.state.raterFeedback.length;
    
    if (charCount === 0 && raterCount === 0) return 'No feedback yet';
    
    const parts = [];
    if (charCount > 0) parts.push(`${charCount} character${charCount !== 1 ? 's' : ''}`);
    if (raterCount > 0) parts.push(`${raterCount} rater${raterCount !== 1 ? 's' : ''}`);
    
    return `Applied feedback from ${parts.join(', ')}`;
  }

  canGenerate(): boolean {
    return !this.disabled && 
           !this.isAnyOperationInProgress() && 
           this.chapterOutline.trim().length > 0;
  }

  canSave(): boolean {
    return !this.disabled && 
           this.state?.hasUnsavedChanges === true;
  }

  isAnyOperationInProgress(): boolean {
    return this.state?.isGenerating === true ||
           this.state?.isGettingFeedback === true ||
           this.state?.isApplyingGuidance === true ||
           this.state?.isChatting === true;
  }

  onSaveChapter() {
    if (this.state?.currentChapter) {
      this.saveChapter.emit(this.state.currentChapter);
    }
  }

  onBackToStory() {
    this.backToStory.emit();
  }
}
