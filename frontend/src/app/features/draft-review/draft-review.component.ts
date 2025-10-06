import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Story, StoryDraft } from '../../shared/models';
import { ApiService } from '../../core/services/api.service';
import { LocalStorageService } from '../../core/services/local-storage.service';

@Component({
  selector: 'app-draft-review',
  templateUrl: './draft-review.component.html',
  styleUrls: ['./draft-review.component.scss']
})
export class DraftReviewComponent implements OnInit {
  story: Story | null = null;
  feedbackForm: FormGroup;
  isRevising = false;
  revisionHistory: any[] = [];

  specificChangeOptions = [
    'Adjust pacing',
    'Develop characters further',
    'Enhance setting description',
    'Strengthen dialogue',
    'Clarify plot points',
    'Add emotional depth',
    'Improve transitions',
    'Expand world-building'
  ];

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private fb: FormBuilder,
    private apiService: ApiService,
    private localStorageService: LocalStorageService,
    private snackBar: MatSnackBar
  ) {
    this.feedbackForm = this.fb.group({
      feedback: ['', [Validators.required, Validators.minLength(10)]],
      specificChanges: [[]]
    });
  }

  ngOnInit(): void {
    const storyId = this.route.snapshot.paramMap.get('id');
    if (storyId) {
      this.loadStory(storyId);
    } else {
      this.router.navigate(['/stories']);
    }
  }

  private loadStory(storyId: string): void {
    this.story = this.localStorageService.getStory(storyId);
    if (!this.story) {
      this.snackBar.open('Story not found', 'Close', { duration: 3000 });
      this.router.navigate(['/stories']);
    }
  }

  onApprove(): void {
    if (this.story && this.story.currentDraft) {
      this.story.currentPhase = 'character_dialog';
      this.story.lastModified = new Date();
      this.localStorageService.saveStory(this.story);

      this.snackBar.open('Draft approved! Moving to character dialog phase.', 'Close', {
        duration: 3000
      });

      this.router.navigate(['/character-dialog', this.story.id]);
    }
  }

  onRequestRevision(): void {
    if (this.feedbackForm.valid && this.story && !this.isRevising) {
      this.isRevising = true;

      const feedback = this.feedbackForm.value.feedback;
      const specificChanges = this.feedbackForm.value.specificChanges;

      if (!this.story.currentDraft) {
        this.handleError('No draft available for revision');
        this.isRevising = false;
        return;
      }

      this.apiService.reviseDraft(this.story.currentDraft, feedback, specificChanges).subscribe({
        next: (response) => {
          if (response.success && this.story) {
            // Store revision history
            this.revisionHistory.push({
              version: this.revisionHistory.length + 1,
              feedback,
              specificChanges,
              previousDraft: this.story.currentDraft,
              timestamp: new Date()
            });

            // Update story with new draft
            this.story.currentDraft = response.data;
            this.story.lastModified = new Date();
            this.localStorageService.saveStory(this.story);

            this.snackBar.open('Draft revised successfully!', 'Close', {
              duration: 3000
            });

            // Reset form
            this.feedbackForm.reset();
          } else {
            this.handleError('Failed to revise draft');
          }
          this.isRevising = false;
        },
        error: (error) => {
          console.error('Error revising draft:', error);
          this.handleError('Error revising draft. Please try again.');
          this.isRevising = false;
        }
      });
    }
  }

  onStartOver(): void {
    if (this.story) {
      this.router.navigate(['/story-input'], {
        queryParams: { editStory: this.story.id }
      });
    }
  }

  onViewRevisionHistory(): void {
    // Toggle revision history display
    // Implementation depends on UI design
  }

  private handleError(message: string): void {
    this.snackBar.open(message, 'Close', {
      duration: 5000,
      panelClass: ['error-snackbar']
    });
  }

  get hasRevisionHistory(): boolean {
    return this.revisionHistory.length > 0;
  }

  get canApprove(): boolean {
    return this.story?.currentDraft != null;
  }

  get canRevise(): boolean {
    return this.story?.currentDraft != null && !this.isRevising;
  }
}