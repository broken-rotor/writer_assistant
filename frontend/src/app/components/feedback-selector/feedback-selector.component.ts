import { Component, Input, Output, EventEmitter, OnInit, OnChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatCardModule } from '@angular/material/card';
import { MatTooltipModule } from '@angular/material/tooltip';
import { 
  Story, 
  CharacterFeedbackResponse, 
  RaterFeedbackResponse,
  Character,
  Rater
} from '../../models/story.model';

export interface CharacterFeedbackSelection {
  characterName: string;
  type: 'action' | 'dialog' | 'physicalSensation' | 'emotion' | 'internalMonologue' | 'goals' | 'memories' | 'subtext';
  content: string;
}

export interface RaterFeedbackSelection {
  raterName: string;
  content: string;
}

export interface FeedbackSelection {
  characterFeedback: CharacterFeedbackSelection[];
  raterFeedback: RaterFeedbackSelection[];
}

export interface ChatContext {
  type: 'character' | 'rater';
  id: string;
  name: string;
  messages: { role: 'user' | 'assistant', content: string, timestamp: Date }[];
}

@Component({
  selector: 'app-feedback-selector',
  standalone: true,
  imports: [
    CommonModule, 
    FormsModule, 
    MatIconModule, 
    MatButtonModule, 
    MatChipsModule,
    MatFormFieldModule,
    MatInputModule,
    MatCardModule,
    MatTooltipModule
  ],
  templateUrl: './feedback-selector.component.html',
  styleUrl: './feedback-selector.component.scss'
})
export class FeedbackSelectorComponent implements OnInit, OnChanges {
  @Input() story: Story | null = null;
  @Input() characterFeedback: CharacterFeedbackResponse[] = [];
  @Input() raterFeedback: RaterFeedbackResponse[] = [];
  @Input() isLoading = false;
  @Input() disabled = false;
  @Input() userGuidance = '';
  
  @Output() getFeedback = new EventEmitter<{ type: 'character' | 'rater', entityId: string, entityName: string }>();
  @Output() modifyChapter = new EventEmitter<{ 
    userGuidance: string, 
    selectedFeedback: FeedbackSelection 
  }>();
  @Output() clearFeedback = new EventEmitter<void>();
  @Output() chatMessage = new EventEmitter<{
    type: 'character' | 'rater',
    id: string,
    message: string
  }>();
  @Output() userGuidanceChange = new EventEmitter<string>();

  selectedEntityType: 'character' | 'rater' | null = null;
  selectedEntityId: string | null = null;
  selectedFeedback: FeedbackSelection = {
    characterFeedback: [],
    raterFeedback: []
  };
  
  chatContexts: Record<string, ChatContext> = {};
  currentChatMessage = '';

  ngOnInit() {
    this.initializeFeedbackSelection();
  }

  ngOnChanges() {
    this.initializeFeedbackSelection();
  }

  private initializeFeedbackSelection() {
    // Initialize feedback selection state
    this.selectedFeedback = {
      characterFeedback: [],
      raterFeedback: []
    };
  }

  getAvailableCharacters(): Character[] {
    if (!this.story?.characters) return [];
    return Array.from(this.story.characters.values());
  }

  getAvailableRaters(): Rater[] {
    if (!this.story?.raters) return [];
    return Array.from(this.story.raters.values());
  }

  selectEntity(type: 'character' | 'rater', id: string) {
    this.selectedEntityType = type;
    this.selectedEntityId = id;
    
    // Auto-fetch feedback if none exists for the selected entity
    this.autoFetchFeedbackIfNeeded();
  }

  getSelectedEntityName(): string {
    if (!this.selectedEntityType || !this.selectedEntityId) return '';
    
    if (this.selectedEntityType === 'character') {
      const character = this.getAvailableCharacters().find(c => c.id === this.selectedEntityId);
      return character?.name || '';
    } else {
      const rater = this.getAvailableRaters().find(r => r.id === this.selectedEntityId);
      return rater?.name || '';
    }
  }

  getSelectedEntityFeedback(): CharacterFeedbackResponse | RaterFeedbackResponse | null {
    if (!this.selectedEntityType || !this.selectedEntityId) return null;
    
    if (this.selectedEntityType === 'character') {
      return this.characterFeedback.find(f => f.characterName === this.getSelectedEntityName()) || null;
    } else {
      return this.raterFeedback.find(f => f.raterName === this.getSelectedEntityName()) || null;
    }
  }

  toggleFeedbackSelection(feedbackText: string, feedbackType?: string) {
    if (!this.selectedEntityType || !this.selectedEntityId) return;
    
    const entityName = this.getSelectedEntityName();
    
    if (this.selectedEntityType === 'character' && feedbackType) {
      // Find existing selection
      const existingIndex = this.selectedFeedback.characterFeedback.findIndex(
        item => item.characterName === entityName && item.content === feedbackText && item.type === feedbackType
      );
      
      if (existingIndex > -1) {
        // Remove existing selection
        this.selectedFeedback.characterFeedback.splice(existingIndex, 1);
      } else {
        // Add new selection
        this.selectedFeedback.characterFeedback.push({
          characterName: entityName,
          type: feedbackType as any,
          content: feedbackText
        });
      }
    } else if (this.selectedEntityType === 'rater') {
      // Find existing selection
      const existingIndex = this.selectedFeedback.raterFeedback.findIndex(
        item => item.raterName === entityName && item.content === feedbackText
      );
      
      if (existingIndex > -1) {
        // Remove existing selection
        this.selectedFeedback.raterFeedback.splice(existingIndex, 1);
      } else {
        // Add new selection
        this.selectedFeedback.raterFeedback.push({
          raterName: entityName,
          content: feedbackText
        });
      }
    }
  }

  isFeedbackSelected(feedbackText: string): boolean {
    if (!this.selectedEntityType || !this.selectedEntityId) return false;
    
    const entityName = this.getSelectedEntityName();
    
    if (this.selectedEntityType === 'character') {
      return this.selectedFeedback.characterFeedback.some(
        item => item.characterName === entityName && item.content === feedbackText
      );
    } else {
      return this.selectedFeedback.raterFeedback.some(
        item => item.raterName === entityName && item.content === feedbackText
      );
    }
  }

  getTotalSelectedCount(): number {
    return this.selectedFeedback.characterFeedback.length + this.selectedFeedback.raterFeedback.length;
  }

  onGetFeedback(type: 'character' | 'rater') {
    if (!this.selectedEntityId) return;
    
    const entityName = this.getSelectedEntityName();
    if (!entityName) return;
    
    this.getFeedback.emit({ 
      type, 
      entityId: this.selectedEntityId,
      entityName 
    });
  }

  onModifyChapter() {
    this.modifyChapter.emit({
      userGuidance: this.userGuidance,
      selectedFeedback: this.selectedFeedback
    });
  }

  onClearFeedback() {
    this.clearFeedback.emit();
    this.initializeFeedbackSelection();
  }

  onSendChatMessage() {
    if (!this.currentChatMessage.trim() || !this.selectedEntityType || !this.selectedEntityId) return;
    
    this.chatMessage.emit({
      type: this.selectedEntityType,
      id: this.selectedEntityId,
      message: this.currentChatMessage
    });
    
    this.currentChatMessage = '';
  }

  onUserGuidanceChange() {
    this.userGuidanceChange.emit(this.userGuidance);
  }

  hasAnyFeedback(): boolean {
    return this.characterFeedback.length > 0 || this.raterFeedback.length > 0;
  }

  canModifyChapter(): boolean {
    return !this.disabled && !this.isLoading && 
           (this.userGuidance.trim().length > 0 || this.getTotalSelectedCount() > 0);
  }

  private autoFetchFeedbackIfNeeded() {
    if (!this.selectedEntityType || !this.selectedEntityId) return;
    
    const entityName = this.getSelectedEntityName();
    if (!entityName) return;
    
    // Check if feedback already exists for this entity
    let hasFeedback = false;
    
    if (this.selectedEntityType === 'character') {
      hasFeedback = this.characterFeedback.some(f => f.characterName === entityName);
    } else {
      hasFeedback = this.raterFeedback.some(f => f.raterName === entityName);
    }
    
    // If no feedback exists, auto-fetch it
    if (!hasFeedback) {
      this.onGetFeedback(this.selectedEntityType);
    }
  }

  onRefreshFeedback() {
    if (!this.selectedEntityType) return;
    
    // Emit request to refresh feedback for the selected entity
    this.onGetFeedback(this.selectedEntityType);
  }
}
