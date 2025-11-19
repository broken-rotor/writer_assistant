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

export interface FeedbackSelection {
  characterFeedback: Record<string, string[]>;
  raterFeedback: Record<string, string[]>;
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
    characterFeedback: {},
    raterFeedback: {}
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
      characterFeedback: {},
      raterFeedback: {}
    };

    // Initialize character feedback selection
    this.characterFeedback.forEach(feedback => {
      this.selectedFeedback.characterFeedback[feedback.characterName] = [];
    });

    // Initialize rater feedback selection
    this.raterFeedback.forEach(feedback => {
      this.selectedFeedback.raterFeedback[feedback.raterName] = [];
    });
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

  toggleFeedbackSelection(feedbackText: string) {
    if (!this.selectedEntityType || !this.selectedEntityId) return;
    
    const entityName = this.getSelectedEntityName();
    
    if (this.selectedEntityType === 'character') {
      const selections = this.selectedFeedback.characterFeedback[entityName] || [];
      const index = selections.indexOf(feedbackText);
      
      if (index > -1) {
        selections.splice(index, 1);
      } else {
        selections.push(feedbackText);
      }
      
      this.selectedFeedback.characterFeedback[entityName] = selections;
    } else {
      const selections = this.selectedFeedback.raterFeedback[entityName] || [];
      const index = selections.indexOf(feedbackText);
      
      if (index > -1) {
        selections.splice(index, 1);
      } else {
        selections.push(feedbackText);
      }
      
      this.selectedFeedback.raterFeedback[entityName] = selections;
    }
  }

  isFeedbackSelected(feedbackText: string): boolean {
    if (!this.selectedEntityType || !this.selectedEntityId) return false;
    
    const entityName = this.getSelectedEntityName();
    
    if (this.selectedEntityType === 'character') {
      return (this.selectedFeedback.characterFeedback[entityName] || []).includes(feedbackText);
    } else {
      return (this.selectedFeedback.raterFeedback[entityName] || []).includes(feedbackText);
    }
  }

  getTotalSelectedCount(): number {
    let count = 0;
    
    Object.values(this.selectedFeedback.characterFeedback).forEach(selections => {
      count += selections.length;
    });
    
    Object.values(this.selectedFeedback.raterFeedback).forEach(selections => {
      count += selections.length;
    });
    
    return count;
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
