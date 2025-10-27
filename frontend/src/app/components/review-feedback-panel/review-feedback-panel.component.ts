import { Component, Input, Output, EventEmitter, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';

import { 
  ReviewItem, 
  Story,
  Character,
  Rater
} from '../../models/story.model';
import { ReviewService, ReviewRequestStatus, QualityScore, ComprehensiveReviewRequest } from '../../services/review.service';
import { PhaseStateService } from '../../services/phase-state.service';

export interface ReviewFeedbackPanelConfig {
  storyId: string;
  chapterNumber: number;
  chapterContent: string;
  showRequestButtons?: boolean;
  showChatIntegration?: boolean;
  showQualityScore?: boolean;
  maxHeight?: string;
}

export interface ReviewSelectionEvent {
  selectedItems: ReviewItem[];
  totalSelected: number;
}

export interface ReviewRequestEvent {
  requestType: 'comprehensive' | 'character' | 'rater' | 'editor';
  options?: ComprehensiveReviewRequest;
}

export interface AddToChatEvent {
  selectedReviews: ReviewItem[];
  userComment?: string;
}

@Component({
  selector: 'app-review-feedback-panel',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './review-feedback-panel.component.html',
  styleUrls: ['./review-feedback-panel.component.scss']
})
export class ReviewFeedbackPanelComponent implements OnInit, OnDestroy {
  @Input() config!: ReviewFeedbackPanelConfig;
  @Input() story!: Story;
  @Input() disabled = false;

  @Output() selectionChanged = new EventEmitter<ReviewSelectionEvent>();
  @Output() reviewRequested = new EventEmitter<ReviewRequestEvent>();
  @Output() addToChat = new EventEmitter<AddToChatEvent>();

  private reviewService = inject(ReviewService);
  private phaseStateService = inject(PhaseStateService);
  private subscriptions: Subscription[] = [];

  // Component state
  availableReviews: ReviewItem[] = [];
  selectedReviewIds = new Set<string>();
  requestStatus: ReviewRequestStatus = {
    pendingRequests: [],
    completedRequests: [],
    failedRequests: [],
    totalRequests: 0,
    completedCount: 0
  };
  qualityScore: QualityScore | null = null;
  userComment = '';
  
  // Categorized reviews
  characterReviews: ReviewItem[] = [];
  raterReviews: ReviewItem[] = [];
  editorReviews: ReviewItem[] = [];

  // UI state
  showCharacterSection = true;
  showRaterSection = true;
  showEditorSection = true;
  isLoading = false;
  error: string | null = null;
  isRequestingComprehensive = false;

  // Comprehensive review options
  comprehensiveOptions: ComprehensiveReviewRequest = {
    includeCharacters: true,
    includeRaters: true,
    includeEditor: true
  };

  ngOnInit(): void {
    this.initializeReviews();
    this.subscribeToReviewUpdates();
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }

  private initializeReviews(): void {
    if (!this.story || !this.config) return;
    
    this.loadAvailableReviews();
    this.categorizeReviews();
    this.updateQualityScore();
  }

  private subscribeToReviewUpdates(): void {
    // Subscribe to review service updates
    const reviewsSub = this.reviewService.reviewsUpdated$.subscribe(() => {
      this.loadAvailableReviews();
      this.categorizeReviews();
      this.updateQualityScore();
    });

    const requestStatusSub = this.reviewService.requestStatus$.subscribe(status => {
      this.requestStatus = status;
      this.isRequestingComprehensive = status.pendingRequests.length > 0;
    });

    const qualityScoreSub = this.reviewService.qualityScore$.subscribe(score => {
      this.qualityScore = score;
    });

    this.subscriptions.push(reviewsSub, requestStatusSub, qualityScoreSub);
  }

  private loadAvailableReviews(): void {
    this.availableReviews = this.reviewService.getAvailableReviews(
      this.config.storyId,
      this.config.chapterNumber
    );
  }

  private categorizeReviews(): void {
    this.characterReviews = this.availableReviews.filter(item => 
      item.type === 'character' || this.isCharacterReview(item)
    );
    this.raterReviews = this.availableReviews.filter(item => 
      item.type === 'style' && this.isRaterReview(item)
    );
    this.editorReviews = this.availableReviews.filter(item => 
      this.isEditorReview(item)
    );
  }

  private updateQualityScore(): void {
    if (this.config.showQualityScore && this.availableReviews.length > 0) {
      this.qualityScore = this.reviewService.calculateQualityScore(this.availableReviews);
    }
  }

  // Review type checking
  isCharacterReview(item: ReviewItem): boolean {
    return item.metadata.reviewer !== 'editor' && 
           (item.type === 'character' || 
            Array.from(this.story.characters.values()).some(char => char.name === item.metadata.reviewer));
  }

  isRaterReview(item: ReviewItem): boolean {
    return Array.from(this.story.raters.values()).some(rater => rater.name === item.metadata.reviewer);
  }

  isEditorReview(item: ReviewItem): boolean {
    return item.metadata.reviewer === 'editor';
  }

  // Selection management
  toggleReviewSelection(reviewId: string): void {
    if (this.selectedReviewIds.has(reviewId)) {
      this.selectedReviewIds.delete(reviewId);
    } else {
      this.selectedReviewIds.add(reviewId);
    }
    this.emitSelectionChange();
  }

  selectAllReviews(): void {
    this.availableReviews.forEach(item => {
      this.selectedReviewIds.add(item.id);
    });
    this.emitSelectionChange();
  }

  clearAllSelection(): void {
    this.selectedReviewIds.clear();
    this.emitSelectionChange();
  }

  selectCategoryReviews(category: 'character' | 'rater' | 'editor'): void {
    const reviewItems = this.getReviewsByCategory(category);
    reviewItems.forEach(item => {
      this.selectedReviewIds.add(item.id);
    });
    this.emitSelectionChange();
  }

  clearCategorySelection(category: 'character' | 'rater' | 'editor'): void {
    const reviewItems = this.getReviewsByCategory(category);
    reviewItems.forEach(item => {
      this.selectedReviewIds.delete(item.id);
    });
    this.emitSelectionChange();
  }

  selectByPriority(priority: 'high' | 'medium' | 'low'): void {
    this.availableReviews
      .filter(item => item.priority === priority)
      .forEach(item => {
        this.selectedReviewIds.add(item.id);
      });
    this.emitSelectionChange();
  }

  private getReviewsByCategory(category: 'character' | 'rater' | 'editor'): ReviewItem[] {
    switch (category) {
      case 'character': return this.characterReviews;
      case 'rater': return this.raterReviews;
      case 'editor': return this.editorReviews;
      default: return [];
    }
  }

  private emitSelectionChange(): void {
    const selectedItems = this.availableReviews.filter(item => 
      this.selectedReviewIds.has(item.id)
    );
    
    this.selectionChanged.emit({
      selectedItems,
      totalSelected: selectedItems.length
    });
  }

  // Review requests
  requestComprehensiveReviews(): void {
    if (this.isRequestingComprehensive) return;

    this.reviewRequested.emit({
      requestType: 'comprehensive',
      options: this.comprehensiveOptions
    });

    this.reviewService.requestComprehensiveReviews(
      this.story,
      this.config.chapterNumber,
      this.config.chapterContent,
      this.comprehensiveOptions
    ).subscribe({
      next: (success) => {
        if (success) {
          console.log('Comprehensive reviews requested successfully');
        } else {
          this.error = 'Failed to request comprehensive reviews';
        }
      },
      error: (error) => {
        console.error('Error requesting comprehensive reviews:', error);
        this.error = 'Error requesting comprehensive reviews';
      }
    });
  }

  // Chat integration
  addSelectedToChat(): void {
    const selectedItems = this.availableReviews.filter(item => 
      this.selectedReviewIds.has(item.id)
    );

    if (selectedItems.length === 0) return;

    this.addToChat.emit({
      selectedReviews: selectedItems,
      userComment: this.userComment.trim() || undefined
    });

    this.reviewService.addReviewsToChat(
      this.config.storyId,
      this.config.chapterNumber,
      selectedItems,
      this.userComment.trim() || undefined
    ).subscribe({
      next: (success) => {
        if (success) {
          // Clear selection and comment after adding to chat
          this.clearAllSelection();
          this.userComment = '';
        }
      },
      error: (error) => {
        console.error('Error adding reviews to chat:', error);
        this.error = 'Error adding reviews to chat';
      }
    });
  }

  // Utility methods
  get selectedCount(): number {
    return this.selectedReviewIds.size;
  }

  get hasSelectedReviews(): boolean {
    return this.selectedReviewIds.size > 0;
  }

  get availableCharacters(): Character[] {
    return Array.from(this.story.characters.values()).filter(char => !char.isHidden);
  }

  get availableRaters(): Rater[] {
    return Array.from(this.story.raters.values()).filter(rater => rater.enabled);
  }

  get requestProgress(): number {
    if (this.requestStatus.totalRequests === 0) return 0;
    return Math.round((this.requestStatus.completedCount / this.requestStatus.totalRequests) * 100);
  }

  get hasHighPriorityIssues(): boolean {
    return this.availableReviews.some(review => review.priority === 'high');
  }

  get reviewsByPriority(): { high: ReviewItem[], medium: ReviewItem[], low: ReviewItem[] } {
    return {
      high: this.availableReviews.filter(r => r.priority === 'high'),
      medium: this.availableReviews.filter(r => r.priority === 'medium'),
      low: this.availableReviews.filter(r => r.priority === 'low')
    };
  }

  getReviewStatusIcon(item: ReviewItem): string {
    switch (item.status) {
      case 'pending': return '⏳';
      case 'accepted': return '✅';
      case 'rejected': return '❌';
      case 'modified': return '✏️';
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

  getReviewTypeIcon(type: ReviewItem['type']): string {
    switch (type) {
      case 'grammar': return '📝';
      case 'style': return '🎨';
      case 'consistency': return '🔗';
      case 'flow': return '🌊';
      case 'character': return '👤';
      case 'plot': return '📖';
      default: return '💬';
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

  toggleEditorSection(): void {
    this.showEditorSection = !this.showEditorSection;
  }

  // Comprehensive review options
  toggleComprehensiveOption(option: keyof ComprehensiveReviewRequest): void {
    if (option === 'targetedAspects') {
      // Handle targetedAspects separately as it's a string array
      return;
    }
    // Type assertion to handle boolean properties
    (this.comprehensiveOptions as any)[option] = !(this.comprehensiveOptions as any)[option];
  }

  // TrackBy function for ngFor performance
  trackByReviewId(index: number, item: ReviewItem): string {
    return item.id;
  }

  // Helper method to safely get category score
  getCategoryScore(category: string): number {
    if (!this.qualityScore?.categories) return 0;
    const categories = this.qualityScore.categories as any;
    return categories[category] || 0;
  }
}
