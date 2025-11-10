import { Component, Input, Output, EventEmitter, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatDividerModule } from '@angular/material/divider';
import { MatChipsModule } from '@angular/material/chips';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Subject, takeUntil } from 'rxjs';

import { 
  Chapter, 
  Story
} from '../../models/story.model';
import { ChapterEditorService, ChapterEditingState } from '../../services/chapter-editor.service';
import { FeedbackIntegrationComponent, FeedbackAction } from '../feedback-integration/feedback-integration.component';
import { ChatInterfaceComponent } from '../chat-interface/chat-interface.component';

@Component({
  selector: 'app-chapter-editor',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatButtonModule,
    MatCardModule,
    MatIconModule,
    MatInputModule,
    MatFormFieldModule,
    MatProgressSpinnerModule,
    MatDividerModule,
    MatChipsModule,
    FeedbackIntegrationComponent,
    ChatInterfaceComponent
  ],
  templateUrl: './chapter-editor.component.html',
  styleUrls: ['./chapter-editor.component.scss']
})
export class ChapterEditorComponent implements OnInit, OnDestroy {
  @Input() chapter!: Chapter;
  @Input() story!: Story;
  @Input() disabled = false;

  @Output() chapterUpdated = new EventEmitter<Chapter>();
  @Output() backToList = new EventEmitter<void>();
  @Output() saveChapter = new EventEmitter<Chapter>();

  state: ChapterEditingState = {
    currentChapter: null,
    isGenerating: false,
    isGettingFeedback: false,
    isApplyingGuidance: false,
    isChatting: false,
    chatHistory: [],
    characterFeedback: [],
    raterFeedback: [],
    userGuidance: '',
    hasUnsavedChanges: false
  };

  userGuidanceText = '';
  private destroy$ = new Subject<void>();
  
  private chapterEditorService = inject(ChapterEditorService);
  private snackBar = inject(MatSnackBar);

  ngOnInit(): void {
    // Initialize the chapter editor service
    this.chapterEditorService.initializeChapterEditing(this.chapter);

    // Subscribe to state changes
    this.chapterEditorService.state$
      .pipe(takeUntil(this.destroy$))
      .subscribe(state => {
        this.state = state;
        if (state.currentChapter) {
          this.chapterUpdated.emit(state.currentChapter);
        }
      });

    // Subscribe to errors
    this.chapterEditorService.error$
      .pipe(takeUntil(this.destroy$))
      .subscribe(error => {
        this.snackBar.open(error, 'Close', {
          duration: 5000,
          panelClass: ['error-snackbar']
        });
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  onBackToList(): void {
    if (this.state.hasUnsavedChanges) {
      const confirmed = confirm('You have unsaved changes. Are you sure you want to go back?');
      if (!confirmed) return;
    }
    this.backToList.emit();
  }

  onTitleChange(title: string): void {
    this.chapterEditorService.updateChapterTitle(title);
  }

  onContentChange(content: string): void {
    this.chapterEditorService.updateChapterContent(content);
  }

  onPlotPointChange(plotPoint: string): void {
    this.chapterEditorService.updateChapterPlotPoint(plotPoint);
  }

  onAddPlotItem(item: string): void {
    if (!item.trim()) return;
    this.chapterEditorService.addKeyPlotItem(item.trim());
  }

  onRemovePlotItem(index: number): void {
    this.chapterEditorService.removeKeyPlotItem(index);
  }

  onGenerateChapter(): void {
    if (!this.story) return;

    this.chapterEditorService.generateChapterFromOutline(this.story)
      .subscribe({
        next: (_content) => {
          this.snackBar.open('Chapter generated successfully!', 'Close', {
            duration: 3000,
            panelClass: ['success-snackbar']
          });
        },
        error: (error) => {
          console.error('Failed to generate chapter:', error);
        }
      });
  }

  onChatMessage(message: string): void {
    if (!this.story || !message.trim()) return;

    this.chapterEditorService.sendChatMessage(message, this.story)
      .subscribe({
        next: (_response) => {
          // Chat history is automatically updated in the service
        },
        error: (error) => {
          console.error('Chat failed:', error);
        }
      });
  }

  onGetFeedback(feedbackType: 'character' | 'rater' | 'both'): void {
    if (!this.story) return;

    if (feedbackType === 'character' || feedbackType === 'both') {
      this.chapterEditorService.getCharacterFeedback(this.story)
        .subscribe({
          next: (feedback) => {
            this.snackBar.open(`Got feedback from ${feedback.length} characters`, 'Close', {
              duration: 3000,
              panelClass: ['success-snackbar']
            });
          },
          error: (error) => {
            console.error('Failed to get character feedback:', error);
          }
        });
    }

    if (feedbackType === 'rater' || feedbackType === 'both') {
      this.chapterEditorService.getRaterFeedback(this.story)
        .subscribe({
          next: (feedback) => {
            this.snackBar.open(`Got feedback from ${feedback.length} raters`, 'Close', {
              duration: 3000,
              panelClass: ['success-snackbar']
            });
          },
          error: (error) => {
            console.error('Failed to get rater feedback:', error);
          }
        });
    }
  }

  onApplyFeedback(action: FeedbackAction): void {
    if (!this.story || action.type !== 'apply') return;

    this.chapterEditorService.applyUserGuidance(
      `Please incorporate this ${action.feedbackType} feedback from ${action.source}: ${action.content}`,
      this.story
    ).subscribe({
      next: (_modifiedContent) => {
        this.snackBar.open('Feedback applied successfully!', 'Close', {
          duration: 3000,
          panelClass: ['success-snackbar']
        });
      },
      error: (error) => {
        console.error('Failed to apply feedback:', error);
      }
    });
  }

  onClearFeedback(): void {
    this.chapterEditorService.clearFeedback();
    this.snackBar.open('Feedback cleared', 'Close', {
      duration: 2000
    });
  }

  onChatKeydown(event: KeyboardEvent, chatInput: HTMLTextAreaElement): void {
    if (event.ctrlKey && chatInput.value.trim()) {
      this.onChatMessage(chatInput.value);
      chatInput.value = '';
    }
  }

  onApplyUserGuidance(): void {
    if (!this.story || !this.userGuidanceText.trim()) return;

    this.chapterEditorService.applyUserGuidance(this.userGuidanceText, this.story)
      .subscribe({
        next: (_modifiedContent) => {
          this.userGuidanceText = '';
          this.snackBar.open('Guidance applied successfully!', 'Close', {
            duration: 3000,
            panelClass: ['success-snackbar']
          });
        },
        error: (error) => {
          console.error('Failed to apply guidance:', error);
        }
      });
  }

  onSaveChapter(): void {
    if (this.state.currentChapter) {
      this.saveChapter.emit(this.state.currentChapter);
      this.chapterEditorService.markAsSaved();
      this.snackBar.open('Chapter saved!', 'Close', {
        duration: 2000,
        panelClass: ['success-snackbar']
      });
    }
  }

  onClearChat(): void {
    this.chapterEditorService.clearChatHistory();
    this.snackBar.open('Chat history cleared', 'Close', {
      duration: 2000
    });
  }

  getWordCount(): number {
    return this.state.currentChapter?.metadata.wordCount || 0;
  }

  hasContent(): boolean {
    return !!(this.state.currentChapter?.content?.trim());
  }

  canGenerate(): boolean {
    return !this.state.isGenerating && !this.disabled;
  }

  canGetFeedback(): boolean {
    return this.hasContent() && !this.state.isGettingFeedback && !this.disabled;
  }

  canApplyGuidance(): boolean {
    return this.hasContent() && 
           this.userGuidanceText.trim().length > 0 && 
           !this.state.isApplyingGuidance && 
           !this.disabled;
  }

  canChat(): boolean {
    return !this.state.isChatting && !this.disabled;
  }

  isAnyOperationInProgress(): boolean {
    return this.state.isGenerating || 
           this.state.isGettingFeedback || 
           this.state.isApplyingGuidance || 
           this.state.isChatting;
  }
}
