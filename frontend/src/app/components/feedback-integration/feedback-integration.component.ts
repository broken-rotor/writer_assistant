import { Component, Input, Output, EventEmitter, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { 
  CharacterFeedbackResponse, 
  RaterFeedbackResponse
} from '../../models/story.model';

export interface FeedbackAction {
  type: 'apply' | 'dismiss';
  feedbackType: 'character' | 'rater';
  source: string;
  content: string;
}

@Component({
  selector: 'app-feedback-integration',
  standalone: true,
  imports: [
    CommonModule,
    MatButtonModule,
    MatCardModule,
    MatIconModule,
    MatChipsModule,
    MatExpansionModule,
    MatProgressSpinnerModule
  ],
  templateUrl: './feedback-integration.component.html',
  styleUrls: ['./feedback-integration.component.scss']
})
export class FeedbackIntegrationComponent implements OnInit {
  @Input() characterFeedback: CharacterFeedbackResponse[] = [];
  @Input() raterFeedback: RaterFeedbackResponse[] = [];
  @Input() isLoading = false;
  @Input() showGetFeedbackButton = true;
  @Input() disabled = false;

  @Output() getFeedback = new EventEmitter<'character' | 'rater' | 'both'>();
  @Output() applyFeedback = new EventEmitter<FeedbackAction>();
  @Output() clearFeedback = new EventEmitter<void>();

  expandedPanels = new Set<string>();

  ngOnInit(): void {
    // Auto-expand first panel if there's feedback
    if (this.characterFeedback.length > 0) {
      this.expandedPanels.add('character-0');
    } else if (this.raterFeedback.length > 0) {
      this.expandedPanels.add('rater-0');
    }
  }

  onGetCharacterFeedback(): void {
    this.getFeedback.emit('character');
  }

  onGetRaterFeedback(): void {
    this.getFeedback.emit('rater');
  }

  onGetAllFeedback(): void {
    this.getFeedback.emit('both');
  }

  onApplyCharacterFeedback(feedback: CharacterFeedbackResponse, feedbackType: keyof CharacterFeedbackResponse['feedback'], item: string): void {
    this.applyFeedback.emit({
      type: 'apply',
      feedbackType: 'character',
      source: feedback.characterName,
      content: item
    });
  }

  onApplyRaterFeedback(feedback: RaterFeedbackResponse, suggestion: any): void {
    this.applyFeedback.emit({
      type: 'apply',
      feedbackType: 'rater',
      source: feedback.raterName,
      content: suggestion.suggestion
    });
  }

  onDismissFeedback(feedbackType: 'character' | 'rater', source: string, content: string): void {
    this.applyFeedback.emit({
      type: 'dismiss',
      feedbackType,
      source,
      content
    });
  }

  onClearAllFeedback(): void {
    this.clearFeedback.emit();
  }

  togglePanel(panelId: string): void {
    if (this.expandedPanels.has(panelId)) {
      this.expandedPanels.delete(panelId);
    } else {
      this.expandedPanels.add(panelId);
    }
  }

  isPanelExpanded(panelId: string): boolean {
    return this.expandedPanels.has(panelId);
  }

  hasAnyFeedback(): boolean {
    return this.characterFeedback.length > 0 || this.raterFeedback.length > 0;
  }

  getFeedbackTypeIcon(type: string): string {
    const icons: Record<string, string> = {
      'actions': '🎬',
      'dialog': '💬',
      'physicalSensations': '👋',
      'emotions': '❤️',
      'internalMonologue': '💭'
    };
    return icons[type] || '📝';
  }

  getPriorityColor(priority: string): string {
    switch (priority) {
      case 'high': return 'warn';
      case 'medium': return 'accent';
      case 'low': return 'primary';
      default: return 'primary';
    }
  }

  getPriorityIcon(priority: string): string {
    switch (priority) {
      case 'high': return 'priority_high';
      case 'medium': return 'remove';
      case 'low': return 'low_priority';
      default: return 'info';
    }
  }
}
