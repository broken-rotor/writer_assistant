import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';
import { Story } from '../../models/story.model';
import { StoryService } from '../../services/story.service';
import { GenerationService } from '../../services/generation.service';

@Component({
  selector: 'app-story-workspace',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './story-workspace.component.html',
  styleUrl: './story-workspace.component.scss'
})
export class StoryWorkspaceComponent implements OnInit, OnDestroy {
  story: Story | null = null;
  activeTab: 'general' | 'characters' | 'raters' | 'story' | 'chapter-creation' = 'general';
  loading = true;
  error: string | null = null;

  // Characters tab state
  selectedCharacterId: string | null = null;
  editingCharacter: any = null;

  // Raters tab state
  selectedRaterId: string | null = null;
  editingRater: any = null;

  // Chapter Creation tab state
  generatingFeedback: Set<string> = new Set();
  generatingChapter = false;
  generatingReview = false;

  private destroy$ = new Subject<void>();

  constructor(
    private route: ActivatedRoute,
    private storyService: StoryService,
    private generationService: GenerationService
  ) {}

  ngOnInit() {
    this.route.params
      .pipe(takeUntil(this.destroy$))
      .subscribe(params => {
        const storyId = params['id'];
        if (storyId) {
          this.loadStory(storyId);
        }
      });
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadStory(storyId: string) {
    this.loading = true;
    this.error = null;

    try {
      this.story = this.storyService.getStory(storyId);
      if (!this.story) {
        this.error = 'Story not found';
      }
    } catch (err) {
      this.error = 'Failed to load story';
      console.error('Error loading story:', err);
    } finally {
      this.loading = false;
    }
  }

  selectTab(tab: 'general' | 'characters' | 'raters' | 'story' | 'chapter-creation') {
    this.activeTab = tab;
    // Auto-save when switching tabs
    if (this.story) {
      this.storyService.saveStory(this.story);
    }
  }

  get lastSaved(): Date | null {
    return this.story?.metadata.lastModified || null;
  }

  // Helper methods
  get charactersArray() {
    return this.story ? Array.from(this.story.characters.values()) : [];
  }

  get activeCharacters() {
    return this.charactersArray.filter(c => !c.isHidden);
  }

  get hiddenCharacters() {
    return this.charactersArray.filter(c => c.isHidden);
  }

  get ratersArray() {
    return this.story ? Array.from(this.story.raters.values()) : [];
  }

  get enabledRaters() {
    return this.ratersArray.filter(r => r.enabled);
  }

  // Characters tab methods
  addCharacter() {
    if (!this.story) return;

    const newCharacter: any = {
      id: this.generateId(),
      basicBio: '',
      name: '',
      sex: '',
      gender: '',
      sexualPreference: '',
      age: 0,
      physicalAppearance: '',
      usualClothing: '',
      personality: '',
      motivations: '',
      fears: '',
      relationships: '',
      isHidden: false,
      metadata: {
        creationSource: 'user',
        lastModified: new Date()
      }
    };

    this.story.characters.set(newCharacter.id, newCharacter);
    this.selectCharacter(newCharacter.id);
  }

  selectCharacter(id: string) {
    this.selectedCharacterId = id;
    const character = this.story?.characters.get(id);
    if (character) {
      this.editingCharacter = { ...character };
    }
  }

  saveCharacter() {
    if (!this.story || !this.editingCharacter) return;

    this.editingCharacter.metadata.lastModified = new Date();
    this.story.characters.set(this.editingCharacter.id, this.editingCharacter);
    this.storyService.saveStory(this.story);
  }

  hideCharacter(id: string) {
    if (!this.story) return;
    const character = this.story.characters.get(id);
    if (character) {
      character.isHidden = true;
      this.storyService.saveStory(this.story);
    }
  }

  unhideCharacter(id: string) {
    if (!this.story) return;
    const character = this.story.characters.get(id);
    if (character) {
      character.isHidden = false;
      this.storyService.saveStory(this.story);
    }
  }

  removeCharacter(id: string) {
    if (!this.story || !confirm('Permanently delete this character?')) return;
    this.story.characters.delete(id);
    if (this.selectedCharacterId === id) {
      this.selectedCharacterId = null;
      this.editingCharacter = null;
    }
    this.storyService.saveStory(this.story);
  }

  generateCharacterDetails() {
    if (!this.story || !this.editingCharacter || !this.editingCharacter.basicBio) {
      alert('Please enter a basic bio first');
      return;
    }

    this.generationService.generateCharacterDetails(
      this.story,
      this.editingCharacter.basicBio,
      this.activeCharacters
    ).pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          // Populate the editing character with generated details
          this.editingCharacter.name = response.name;
          this.editingCharacter.sex = response.sex;
          this.editingCharacter.gender = response.gender;
          this.editingCharacter.sexualPreference = response.sexualPreference;
          this.editingCharacter.age = response.age;
          this.editingCharacter.physicalAppearance = response.physicalAppearance;
          this.editingCharacter.usualClothing = response.usualClothing;
          this.editingCharacter.personality = response.personality;
          this.editingCharacter.motivations = response.motivations;
          this.editingCharacter.fears = response.fears;
          this.editingCharacter.relationships = response.relationships;
        },
        error: (err) => {
          console.error('Error generating character details:', err);
          alert('Failed to generate character details');
        }
      });
  }

  regenerateRelationships() {
    // TODO: Call API to regenerate relationships considering all characters
    console.log('Regenerate relationships');
  }

  // Raters tab methods
  addRater() {
    if (!this.story) return;

    const newRater: any = {
      id: this.generateId(),
      name: '',
      systemPrompt: '',
      enabled: true,
      metadata: {
        created: new Date(),
        lastModified: new Date()
      }
    };

    this.story.raters.set(newRater.id, newRater);
    this.selectRater(newRater.id);
  }

  selectRater(id: string) {
    this.selectedRaterId = id;
    const rater = this.story?.raters.get(id);
    if (rater) {
      this.editingRater = { ...rater };
    }
  }

  saveRater() {
    if (!this.story || !this.editingRater) return;

    this.editingRater.metadata.lastModified = new Date();
    this.story.raters.set(this.editingRater.id, this.editingRater);
    this.storyService.saveStory(this.story);
  }

  toggleRater(id: string) {
    if (!this.story) return;
    const rater = this.story.raters.get(id);
    if (rater) {
      rater.enabled = !rater.enabled;
      this.storyService.saveStory(this.story);
    }
  }

  removeRater(id: string) {
    if (!this.story || !confirm('Permanently delete this rater?')) return;
    this.story.raters.delete(id);
    if (this.selectedRaterId === id) {
      this.selectedRaterId = null;
      this.editingRater = null;
    }
    this.storyService.saveStory(this.story);
  }

  // Story tab methods
  regenerateSummary() {
    // TODO: Call API to regenerate story summary
    console.log('Regenerate summary');
  }

  editChapter(chapterId: string) {
    // TODO: Load chapter into Chapter Creation tab for editing
    console.log('Edit chapter:', chapterId);
  }

  deleteChapter(chapterId: string) {
    if (!this.story || !confirm('Delete this chapter?')) return;

    this.story.story.chapters = this.story.story.chapters.filter(c => c.id !== chapterId);
    this.storyService.saveStory(this.story);
  }

  insertChapterAfter(position: number) {
    // Switch to chapter creation tab
    this.selectTab('chapter-creation');
  }

  addChapterAtEnd() {
    this.selectTab('chapter-creation');
  }

  // Chapter Creation tab methods
  aiFleshOutPlotPoint() {
    if (!this.story || !this.story.chapterCreation.plotPoint) {
      alert('Please enter a plot point first');
      return;
    }

    this.generationService.fleshOut(
      this.story,
      this.story.chapterCreation.plotPoint,
      'plot point expansion'
    ).pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          if (this.story) {
            this.story.chapterCreation.plotPoint = response.fleshedOutText;
            this.storyService.saveStory(this.story);
          }
        },
        error: (err) => {
          console.error('Error fleshing out plot point:', err);
          alert('Failed to flesh out plot point');
        }
      });
  }

  requestCharacterFeedback(characterId: string) {
    if (!this.story) return;

    const character = this.story.characters.get(characterId);
    if (!character) return;

    this.generatingFeedback.add(characterId);

    this.generationService.requestCharacterFeedback(
      this.story,
      character,
      this.story.chapterCreation.plotPoint
    ).pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          if (this.story) {
            const characterFeedback: any = {
              characterName: response.characterName,
              actions: response.feedback.actions,
              dialog: response.feedback.dialog,
              physicalSensations: response.feedback.sensations,
              emotions: response.feedback.emotions,
              internalMonologue: response.feedback.thoughts
            };
            this.story.chapterCreation.feedbackRequests.set(characterId, {
              feedback: characterFeedback,
              status: 'ready'
            });
          }
          this.generatingFeedback.delete(characterId);
        },
        error: (err) => {
          console.error('Error requesting character feedback:', err);
          alert('Failed to get character feedback');
          this.generatingFeedback.delete(characterId);
        }
      });
  }

  requestRaterFeedback(raterId: string) {
    if (!this.story) return;

    const rater = this.story.raters.get(raterId);
    if (!rater) return;

    this.generatingFeedback.add(raterId);

    this.generationService.requestRaterFeedback(
      this.story,
      rater,
      this.story.chapterCreation.plotPoint
    ).pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          if (this.story) {
            const raterFeedback: any = {
              raterName: response.raterName,
              opinion: response.feedback.opinion,
              suggestions: response.feedback.suggestions.map((s: any) => s.suggestion)
            };
            this.story.chapterCreation.feedbackRequests.set(raterId, {
              feedback: raterFeedback,
              status: 'ready'
            });
          }
          this.generatingFeedback.delete(raterId);
        },
        error: (err) => {
          console.error('Error requesting rater feedback:', err);
          alert('Failed to get rater feedback');
          this.generatingFeedback.delete(raterId);
        }
      });
  }

  incorporateFeedback(source: string, items: any[]) {
    // TODO: Add selected feedback items to incorporated feedback list
    console.log('Incorporate feedback from', source, items);
  }

  removeFeedbackItem(index: number) {
    if (!this.story) return;
    this.story.chapterCreation.incorporatedFeedback.splice(index, 1);
  }

  generateChapter() {
    if (!this.story) return;

    this.generatingChapter = true;

    this.generationService.generateChapter(this.story)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          if (this.story) {
            this.story.chapterCreation.generatedChapter = {
              text: response.chapterText,
              status: 'ready',
              metadata: {}
            };
            this.storyService.saveStory(this.story);
          }
          this.generatingChapter = false;
        },
        error: (err) => {
          console.error('Error generating chapter:', err);
          alert('Failed to generate chapter');
          this.generatingChapter = false;
        }
      });
  }

  promptAssistantForChanges(request: string) {
    if (!this.story || !this.story.chapterCreation.generatedChapter) {
      alert('Generate a chapter first');
      return;
    }

    this.generationService.modifyChapter(
      this.story,
      this.story.chapterCreation.generatedChapter.text,
      request
    ).pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          if (this.story && this.story.chapterCreation.generatedChapter) {
            this.story.chapterCreation.generatedChapter.text = response.modifiedChapterText;
            this.storyService.saveStory(this.story);
          }
        },
        error: (err) => {
          console.error('Error modifying chapter:', err);
          alert('Failed to modify chapter');
        }
      });
  }

  requestEditorReview() {
    if (!this.story || !this.story.chapterCreation.generatedChapter) {
      alert('Generate a chapter first');
      return;
    }

    this.generatingReview = true;

    this.generationService.requestEditorReview(
      this.story,
      this.story.chapterCreation.generatedChapter.text
    ).pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          if (this.story) {
            this.story.chapterCreation.editorReview = {
              suggestions: response.suggestions,
              userSelections: response.suggestions.map(() => false)
            };
          }
          this.generatingReview = false;
        },
        error: (err) => {
          console.error('Error requesting editor review:', err);
          alert('Failed to get editor review');
          this.generatingReview = false;
        }
      });
  }

  applyEditorSuggestions(selectedIndices: number[]) {
    // TODO: Apply selected editor suggestions to chapter
    console.log('Apply suggestions:', selectedIndices);
  }

  acceptChapter() {
    if (!this.story || !this.story.chapterCreation.generatedChapter) return;

    const newChapter: any = {
      id: this.generateId(),
      number: this.story.story.chapters.length + 1,
      title: `Chapter ${this.story.story.chapters.length + 1}`,
      content: this.story.chapterCreation.generatedChapter.text,
      plotPoint: this.story.chapterCreation.plotPoint,
      incorporatedFeedback: [...this.story.chapterCreation.incorporatedFeedback],
      metadata: {
        created: new Date(),
        lastModified: new Date(),
        wordCount: this.story.chapterCreation.generatedChapter.text.split(/\s+/).length
      }
    };

    this.story.story.chapters.push(newChapter);

    // Reset chapter creation state
    this.story.chapterCreation = {
      plotPoint: '',
      incorporatedFeedback: [],
      feedbackRequests: new Map(),
      generatedChapter: undefined,
      editorReview: undefined
    };

    this.storyService.saveStory(this.story);

    // Switch to story tab to see new chapter
    this.selectTab('story');
  }

  private generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }
}
