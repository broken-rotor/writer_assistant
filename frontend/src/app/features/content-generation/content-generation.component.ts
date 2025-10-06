import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Story, SelectedResponse, Character } from '../../shared/models';
import { ApiService } from '../../core/services/api.service';
import { LocalStorageService } from '../../core/services/local-storage.service';

@Component({
  selector: 'app-content-generation',
  templateUrl: './content-generation.component.html',
  styleUrls: ['./content-generation.component.scss']
})
export class ContentGenerationComponent implements OnInit {
  story: Story | null = null;
  guidanceForm: FormGroup;
  isGenerating = false;
  generatedContent: any = null;

  generationPreferences = {
    targetLength: [
      { value: 1000, label: '1,000 words (Short scene)' },
      { value: 2500, label: '2,500 words (Standard scene)' },
      { value: 5000, label: '5,000 words (Extended scene)' },
      { value: 10000, label: '10,000 words (Full chapter)' }
    ],
    mood: [
      'Investigative tension',
      'Romantic atmosphere',
      'Action-packed',
      'Contemplative',
      'Mysterious',
      'Humorous',
      'Dramatic',
      'Suspenseful'
    ],
    style: [
      'Literary mystery',
      'Commercial fiction',
      'Literary fiction',
      'Genre fiction',
      'Experimental',
      'Classical narrative',
      'Stream of consciousness'
    ]
  };

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private fb: FormBuilder,
    private apiService: ApiService,
    private localStorageService: LocalStorageService,
    private snackBar: MatSnackBar
  ) {
    this.guidanceForm = this.fb.group({
      userGuidance: ['', [Validators.required, Validators.minLength(10)]],
      targetLength: [2500, Validators.required],
      mood: ['investigative_tension', Validators.required],
      style: ['literary_mystery', Validators.required]
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
      return;
    }

    if (this.story.currentPhase !== 'detailed_content') {
      this.snackBar.open('Story is not in content generation phase', 'Close', { duration: 3000 });
      this.router.navigate(['/character-dialog', storyId]);
      return;
    }

    // Set default guidance based on story context
    this.setDefaultGuidance();

    // Load existing content if available
    if (this.story.finalContent) {
      this.generatedContent = this.story.finalContent;
    }
  }

  private setDefaultGuidance(): void {
    if (!this.story?.currentDraft) return;

    let defaultGuidance = 'Generate detailed content incorporating the selected character responses. ';

    if (this.story.selectedResponses && this.story.selectedResponses.length > 0) {
      const charactersWithResponses = this.getSelectedCharacterNames();
      defaultGuidance += `Focus on perspectives from: ${charactersWithResponses.join(', ')}. `;
    }

    if (this.story.currentDraft.themes && this.story.currentDraft.themes.length > 0) {
      defaultGuidance += `Emphasize themes of: ${this.story.currentDraft.themes.join(', ')}. `;
    }

    defaultGuidance += 'Maintain consistency with the established character personalities and story outline.';

    this.guidanceForm.patchValue({
      userGuidance: defaultGuidance
    });
  }

  onGenerateContent(): void {
    if (this.guidanceForm.valid && this.story && !this.isGenerating) {
      this.generateDetailedContent();
    }
  }

  private generateDetailedContent(): void {
    if (!this.story?.currentDraft) return;

    this.isGenerating = true;
    const formValues = this.guidanceForm.value;

    // Prepare selected responses for the API
    const selectedResponses = this.story.selectedResponses?.filter((r: SelectedResponse) => r.useInStory) || [];

    this.apiService.generateDetailedContent(
      this.story.currentDraft,
      selectedResponses,
      formValues.userGuidance
    ).subscribe({
      next: (response) => {
        if (response.success) {
          this.generatedContent = response.data;

          // Save content to story
          if (this.story) {
            this.story.finalContent = this.generatedContent;
            this.story.lastModified = new Date();
            this.localStorageService.saveStory(this.story);
          }

          this.snackBar.open('Content generated successfully!', 'Close', {
            duration: 3000
          });
        } else {
          this.handleError('Failed to generate content');
        }
        this.isGenerating = false;
      },
      error: (error) => {
        console.error('Error generating content:', error);
        this.handleError('Error generating content. Please try again.');
        this.isGenerating = false;
      }
    });
  }

  onModifyContent(): void {
    // Allow user to modify generation parameters and regenerate
    this.generatedContent = null;
    if (this.story) {
      this.story.finalContent = null;
      this.localStorageService.saveStory(this.story);
    }
  }

  onApproveContent(): void {
    if (this.story) {
      this.story.currentPhase = 'refinement';
      this.story.lastModified = new Date();
      this.localStorageService.saveStory(this.story);

      this.snackBar.open('Content approved! Moving to refinement phase.', 'Close', {
        duration: 3000
      });

      this.router.navigate(['/refinement', this.story.id]);
    }
  }

  onRequestFeedback(): void {
    if (this.story && this.generatedContent) {
      this.router.navigate(['/refinement', this.story.id], {
        queryParams: { requestFeedback: 'true' }
      });
    }
  }

  private handleError(message: string): void {
    this.snackBar.open(message, 'Close', {
      duration: 5000,
      panelClass: ['error-snackbar']
    });
  }

  get hasSelectedResponses(): boolean {
    return !!(this.story?.selectedResponses && this.story.selectedResponses.length > 0);
  }

  get responsesToUse(): SelectedResponse[] {
    return this.story?.selectedResponses?.filter((r: SelectedResponse) => r.useInStory) || [];
  }

  get canGenerate(): boolean {
    return this.guidanceForm.valid && !this.isGenerating;
  }

  get hasGeneratedContent(): boolean {
    return this.generatedContent != null;
  }

  getSelectedCharacterNames(): string[] {
    if (!this.story?.selectedResponses || !this.story?.currentDraft?.characters) {
      return [];
    }

    const characterIds = this.story.selectedResponses
      .filter((r: SelectedResponse) => r.useInStory)
      .map((r: SelectedResponse) => r.characterId);

    return this.story.currentDraft.characters
      .filter((c: Character) => characterIds.includes(c.id))
      .map((c: Character) => c.name);
  }

  getWordCount(): number {
    if (!this.generatedContent?.content) return 0;
    return this.generatedContent.content.split(/\s+/).length;
  }

  getCharacterName(characterId: string): string {
    if (!this.story?.currentDraft?.characters) {
      return 'Unknown Character';
    }

    const character = this.story.currentDraft.characters.find((c: Character) => c.id === characterId);
    return character ? character.name : 'Unknown Character';
  }
}