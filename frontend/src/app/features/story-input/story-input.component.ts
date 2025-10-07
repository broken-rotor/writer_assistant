import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatDialog } from '@angular/material/dialog';
import { StoryInput, Story, StoryDraft, Character } from '../../shared/models';
import { ApiService } from '../../core/services/api.service';
import { LocalStorageService } from '../../core/services/local-storage.service';
import { CharacterInputDialogComponent } from './character-input-dialog.component';

@Component({
  selector: 'app-story-input',
  templateUrl: './story-input.component.html',
  styleUrls: ['./story-input.component.scss']
})
export class StoryInputComponent implements OnInit {
  storyForm: FormGroup;
  isGenerating = false;
  initialCharacters: any[] = [];

  genres = [
    'Mystery', 'Romance', 'Thriller', 'Literary Fiction',
    'Science Fiction', 'Fantasy', 'Historical Fiction', 'Crime'
  ];

  lengths = [
    { value: 'short_story', label: 'Short Story (1,000-7,500 words)' },
    { value: 'novella', label: 'Novella (17,500-40,000 words)' },
    { value: 'novel', label: 'Novel (40,000+ words)' }
  ];

  styles = [
    'Minimalist', 'Descriptive', 'Literary', 'Commercial',
    'Experimental', 'Classical', 'Contemporary'
  ];

  focusAreaOptions = [
    'Character Development', 'Plot Pacing', 'Dialogue',
    'Setting/Atmosphere', 'Theme Exploration', 'Emotional Depth',
    'Action Sequences', 'World Building'
  ];

  constructor(
    private fb: FormBuilder,
    private apiService: ApiService,
    private localStorageService: LocalStorageService,
    private router: Router,
    private snackBar: MatSnackBar,
    private dialog: MatDialog
  ) {
    this.storyForm = this.fb.group({
      title: ['', [Validators.required, Validators.minLength(3)]],
      genre: ['', Validators.required],
      length: ['', Validators.required],
      theme: ['', [Validators.required, Validators.minLength(10)]],
      style: ['', Validators.required],
      focusAreas: [[], Validators.required]
    });
  }

  ngOnInit(): void {}

  addCharacter(): void {
    const dialogRef = this.dialog.open(CharacterInputDialogComponent, {
      width: '500px'
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        this.initialCharacters.push(result);
      }
    });
  }

  removeCharacter(index: number): void {
    this.initialCharacters.splice(index, 1);
  }

  onSubmit(): void {
    if (this.storyForm.valid && !this.isGenerating) {
      this.generateStoryDraft();
    }
  }

  private generateStoryDraft(): void {
    this.isGenerating = true;

    const formValue = this.storyForm.value;
    const storyInput: StoryInput = {
      theme: formValue.theme,
      genre: formValue.genre,
      style: formValue.style,
      length: formValue.length,
      focusAreas: formValue.focusAreas
    };

    // Create initial story object
    const story: Story = {
      id: this.generateId(),
      title: formValue.title,
      genre: formValue.genre,
      length: formValue.length,
      theme: formValue.theme,
      style: formValue.style,
      focusAreas: formValue.focusAreas,
      currentPhase: 'draft',
      currentDraft: null,
      finalContent: null,
      characters: [],
      conversationHistory: [],
      refinementHistory: [],
      createdAt: new Date(),
      lastModified: new Date()
    };

    // Save story to local storage
    this.localStorageService.saveStory(story);

    // Generate initial draft
    this.apiService.generateDraft(storyInput).subscribe({
      next: (response) => {
        if (response.success) {
          story.currentDraft = response.data;

          // Add initial characters to the draft
          if (this.initialCharacters.length > 0) {
            const characters: Character[] = this.initialCharacters.map(char => ({
              id: this.generateId(),
              name: char.name,
              role: char.role,
              personality: {
                coreTraits: char.coreTraits || [],
                emotionalPatterns: [],
                speechPatterns: [],
                motivations: []
              },
              background: char.background || '',
              currentState: {
                emotionalState: 'neutral',
                activeGoals: [],
                currentKnowledge: [],
                relationships: {}
              },
              memorySize: 0,
              isHidden: false,
              creationSource: 'user_defined',
              aiExpansionHistory: []
            }));

            if (!story.currentDraft.characters) {
              story.currentDraft.characters = [];
            }
            story.currentDraft.characters.push(...characters);
          }

          story.lastModified = new Date();
          this.localStorageService.saveStory(story);

          this.snackBar.open('Story draft generated successfully!', 'Close', {
            duration: 3000
          });

          this.router.navigate(['/draft-review', story.id]);
        } else {
          this.handleError('Failed to generate story draft');
        }
        this.isGenerating = false;
      },
      error: (error) => {
        console.error('Error generating draft:', error);
        this.handleError('Error generating story draft. Please try again.');
        this.isGenerating = false;
      }
    });
  }

  private handleError(message: string): void {
    this.snackBar.open(message, 'Close', {
      duration: 5000,
      panelClass: ['error-snackbar']
    });
  }

  private generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }
}