import { Component, Input, Output, EventEmitter, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';

import {
  EnhancedFeedbackItem,
  Character,
  Rater,
  Story
} from '../../models/story.model';
import { FeedbackService } from '../../services/feedback.service';

export interface FeedbackSidebarConfig {
  storyId: string;
  chapterNumber: number;
  showRequestButtons?: boolean;
  showChatIntegration?: boolean;
  maxHeight?: string;
}

export interface FeedbackSelectionEvent {
  selectedItems: EnhancedFeedbackItem[];
  totalSelected: number;
}

export interface FeedbackRequestEvent {
  agentId: string;
  agentType: 'character' | 'rater';
  agentName: string;
  progress?: { phase: string; message: string; progress: number };
}

export interface AddToChatEvent {
  selectedFeedback: EnhancedFeedbackItem[];
  userComment?: string;
}

@Component({
  selector: 'app-feedback-sidebar',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './feedback-sidebar.component.html',
  styleUrls: ['./feedback-sidebar.component.scss']
})
export class FeedbackSidebarComponent implements OnInit, OnDestroy {
  @Input() config!: FeedbackSidebarConfig;
  @Input() story!: Story;
  @Input() disabled = false;

  @Output() selectionChanged = new EventEmitter<FeedbackSelectionEvent>();
  @Output() feedbackRequested = new EventEmitter<FeedbackRequestEvent>();
  @Output() addToChat = new EventEmitter<AddToChatEvent>();

  private feedbackService = inject(FeedbackService);
  private subscriptions: Subscription[] = [];

  // Component state
  availableFeedback: EnhancedFeedbackItem[] = [];
  selectedFeedbackIds = new Set<string>();
  isRequestingFeedback = new Set<string>();
  userComment = '';
  
  // Categorized feedback
  characterFeedback: EnhancedFeedbackItem[] = [];
  raterFeedback: EnhancedFeedbackItem[] = [];

  // UI state
  showCharacterSection = true;
  showRaterSection = true;
  isLoading = false;
  error: string | null = null;

  ngOnInit(): void {
    this.initializeFeedback();
    this.subscribeToFeedbackUpdates();
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }

  private initializeFeedback(): void {
    if (!this.story || !this.config) return;
    
    this.loadAvailableFeedback();
    this.categorizeFeedback();
  }

  private subscribeToFeedbackUpdates(): void {
    // Subscribe to feedback service updates
    const feedbackSub = this.feedbackService.feedbackUpdated$.subscribe(() => {
      this.loadAvailableFeedback();
      this.categorizeFeedback();
    });

    const requestStatusSub = this.feedbackService.requestStatus$.subscribe(status => {
      this.isRequestingFeedback = new Set(status.pendingRequests);
    });

    this.subscriptions.push(feedbackSub, requestStatusSub);
  }

  private loadAvailableFeedback(): void {
    this.availableFeedback = this.feedbackService.getAvailableFeedback(
      this.story.id,
      this.config.chapterNumber
    );
  }

  private categorizeFeedback(): void {
    this.characterFeedback = this.availableFeedback.filter(item => 
      this.isCharacterFeedback(item)
    );
    this.raterFeedback = this.availableFeedback.filter(item => 
      this.isRaterFeedback(item)
    );
  }

  // Feedback type checking
  isCharacterFeedback(item: EnhancedFeedbackItem): boolean {
    return item.type === 'action' || item.type === 'dialog' || 
           item.type === 'sensation' || item.type === 'emotion' || 
           item.type === 'thought';
  }

  isRaterFeedback(item: EnhancedFeedbackItem): boolean {
    return item.type === 'suggestion';
  }

  // Selection management
  toggleFeedbackSelection(feedbackId: string): void {
    if (this.selectedFeedbackIds.has(feedbackId)) {
      this.selectedFeedbackIds.delete(feedbackId);
    } else {
      this.selectedFeedbackIds.add(feedbackId);
    }
    this.emitSelectionChange();
  }

  selectAllFeedback(): void {
    this.availableFeedback.forEach(item => {
      this.selectedFeedbackIds.add(item.id);
    });
    this.emitSelectionChange();
  }

  clearAllSelection(): void {
    this.selectedFeedbackIds.clear();
    this.emitSelectionChange();
  }

  selectCategoryFeedback(category: 'character' | 'rater'): void {
    const feedbackItems = category === 'character' ? this.characterFeedback : this.raterFeedback;
    feedbackItems.forEach(item => {
      this.selectedFeedbackIds.add(item.id);
    });
    this.emitSelectionChange();
  }

  clearCategorySelection(category: 'character' | 'rater'): void {
    const feedbackItems = category === 'character' ? this.characterFeedback : this.raterFeedback;
    feedbackItems.forEach(item => {
      this.selectedFeedbackIds.delete(item.id);
    });
    this.emitSelectionChange();
  }

  private emitSelectionChange(): void {
    const selectedItems = this.availableFeedback.filter(item => 
      this.selectedFeedbackIds.has(item.id)
    );
    
    this.selectionChanged.emit({
      selectedItems,
      totalSelected: selectedItems.length
    });
  }

  // Feedback requests
  requestCharacterFeedback(characterId: string): void {
    const character = this.story.characters.get(characterId);
    if (!character) return;

    this.feedbackRequested.emit({
      agentId: characterId,
      agentType: 'character',
      agentName: character.name
    });

    this.feedbackService.requestCharacterFeedback(
      this.story,
      character,
      this.config.chapterNumber
    );
  }

  requestRaterFeedback(raterId: string): void {
    const rater = this.story.raters.get(raterId);
    if (!rater) return;

    this.feedbackRequested.emit({
      agentId: raterId,
      agentType: 'rater',
      agentName: rater.name
    });

    this.feedbackService.requestRaterFeedback(
      this.story,
      rater,
      this.config.chapterNumber,
      (progress) => {
        // Emit progress updates for parent components to handle
        this.feedbackRequested.emit({
          agentId: raterId,
          agentType: 'rater',
          agentName: rater.name,
          progress: progress
        });
      }
    );
  }

  // Chat integration
  addSelectedToChat(): void {
    const selectedItems = this.availableFeedback.filter(item => 
      this.selectedFeedbackIds.has(item.id)
    );

    if (selectedItems.length === 0) return;

    this.addToChat.emit({
      selectedFeedback: selectedItems,
      userComment: this.userComment.trim() || undefined
    });

    // Clear selection and comment after adding to chat
    this.clearAllSelection();
    this.userComment = '';
  }

  // Utility methods
  get selectedCount(): number {
    return this.selectedFeedbackIds.size;
  }

  get hasSelectedFeedback(): boolean {
    return this.selectedFeedbackIds.size > 0;
  }

  get availableCharacters(): Character[] {
    return Array.from(this.story.characters.values()).filter(char => !char.isHidden);
  }

  get availableRaters(): Rater[] {
    return Array.from(this.story.raters.values()).filter(rater => rater.enabled);
  }

  isRequestingForAgent(agentId: string): boolean {
    return this.isRequestingFeedback.has(agentId);
  }

  getFeedbackStatusIcon(item: EnhancedFeedbackItem): string {
    switch (item.status) {
      case 'pending': return '⏳';
      case 'incorporated': return '✅';
      case 'dismissed': return '❌';
      default: return '📝';
    }
  }

  getPriorityIcon(priority: 'high' | 'medium' | 'low'): string {
    switch (priority) {
      case 'high': return '🔴';
      case 'medium': return '🟡';
      case 'low': return '🟢';
      default: return '⚪';
    }
  }

  formatTimestamp(date: Date): string {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  }

  // Section toggle methods
  toggleCharacterSection(): void {
    this.showCharacterSection = !this.showCharacterSection;
  }

  toggleRaterSection(): void {
    this.showRaterSection = !this.showRaterSection;
  }

  // TrackBy function for ngFor performance
  trackByFeedbackId(index: number, item: EnhancedFeedbackItem): string {
    return item.id;
  }
}
