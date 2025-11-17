import { Component, Input, Output, EventEmitter, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatTooltipModule } from '@angular/material/tooltip';
import { 
  CharacterFeedbackResponse, 
  RaterFeedbackResponse,
  Story,
  Character
} from '../../models/story.model';

export interface FeedbackAction {
  type: 'apply' | 'dismiss';
  feedbackType: 'character' | 'rater';
  source: string;
  content: string;
}

export interface CharacterFeedbackRequest {
  type: 'character';
  characterId?: string; // If specified, get feedback from specific character
}

export interface RaterFeedbackRequest {
  type: 'rater';
}

export interface AllFeedbackRequest {
  type: 'both';
}

export type FeedbackRequest = CharacterFeedbackRequest | RaterFeedbackRequest | AllFeedbackRequest;

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
    MatProgressSpinnerModule,
    MatSelectModule,
    MatFormFieldModule,
    MatTooltipModule
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
  @Input() story: Story | null = null;

  @Output() getFeedback = new EventEmitter<FeedbackRequest>();
  @Output() applyFeedback = new EventEmitter<FeedbackAction>();
  @Output() clearFeedback = new EventEmitter<void>();

  expandedPanels = new Set<string>();
  selectedCharacterId: string | null = null;
  showCharacterSelection = false;

  ngOnInit(): void {
    // Auto-expand first panel if there's feedback
    if (this.characterFeedback.length > 0) {
      this.expandedPanels.add('character-0');
    } else if (this.raterFeedback.length > 0) {
      this.expandedPanels.add('rater-0');
    }
  }

  onGetCharacterFeedback(): void {
    if (this.selectedCharacterId) {
      this.getFeedback.emit({ type: 'character', characterId: this.selectedCharacterId });
    } else {
      this.getFeedback.emit({ type: 'character' });
    }
  }

  onGetRaterFeedback(): void {
    this.getFeedback.emit({ type: 'rater' });
  }

  onGetAllFeedback(): void {
    this.getFeedback.emit({ type: 'both' });
  }

  onToggleCharacterSelection(): void {
    this.showCharacterSelection = !this.showCharacterSelection;
    if (!this.showCharacterSelection) {
      this.selectedCharacterId = null;
    }
  }

  onSelectCharacter(characterId: string): void {
    this.selectedCharacterId = characterId;
  }

  getAvailableCharacters(): Character[] {
    if (!this.story) return [];
    return Array.from(this.story.characters.values()).filter(char => !char.isHidden);
  }

  getSelectedCharacterName(): string {
    if (!this.selectedCharacterId || !this.story) return '';
    const character = this.story.characters.get(this.selectedCharacterId);
    return character ? character.name : '';
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
