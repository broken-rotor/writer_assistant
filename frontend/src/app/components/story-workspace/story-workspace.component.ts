import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
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
  selectedAgentId: string | null = null; // Track currently selected agent for feedback display
  editingFeedbackIndex: number | null = null; // Track which feedback item is being edited
  editingFeedbackContent: string = ''; // Store the edited content temporarily
  changeRequest: string = ''; // User's request for chapter changes
  editingChapterId: string | null = null; // Track which chapter is being edited (null = creating new)
  chapterTitle: string = ''; // Title for the chapter being created/edited

  private destroy$ = new Subject<void>();

  constructor(
    private route: ActivatedRoute,
    private storyService: StoryService,
    private generationService: GenerationService,
    private cdr: ChangeDetectorRef
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

  // General tab methods
  aiFleshOutWorldbuilding() {
    if (!this.story || !this.story.general.worldbuilding) {
      alert('Please enter worldbuilding text first');
      return;
    }

    this.generationService.fleshOut(
      this.story,
      this.story.general.worldbuilding,
      'worldbuilding expansion'
    ).pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          if (this.story) {
            this.story.general.worldbuilding = response.fleshedOutText;
            this.storyService.saveStory(this.story);
          }
        },
        error: (err) => {
          console.error('Error fleshing out worldbuilding:', err);
          alert('Failed to flesh out worldbuilding');
        }
      });
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

  get feedbackRequestsArray() {
    if (!this.story || !this.selectedAgentId) {
      return [];
    }
    const request = this.story.chapterCreation.feedbackRequests.get(this.selectedAgentId);
    if (!request) {
      return [];
    }
    return [{
      id: this.selectedAgentId,
      ...request
    }];
  }

  // Type-safe helper methods for template
  isCharacterFeedback(feedback: any): boolean {
    return feedback && 'actions' in feedback;
  }

  isRaterFeedback(feedback: any): boolean {
    return feedback && 'opinion' in feedback;
  }

  getFeedbackName(feedback: any): string {
    return feedback.characterName || feedback.raterName || 'Unknown';
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
    if (!this.story || !this.editingCharacter) {
      alert('Please select a character first');
      return;
    }

    if (!this.editingCharacter.basicBio) {
      alert('Character must have a basic bio to regenerate relationships');
      return;
    }

    // Get all other characters (excluding the current one)
    const otherCharacters = this.activeCharacters.filter(c => c.id !== this.editingCharacter.id);

    if (otherCharacters.length === 0) {
      alert('No other characters exist. Add more characters to generate relationships.');
      return;
    }

    this.generationService.regenerateRelationships(
      this.story,
      this.editingCharacter,
      otherCharacters
    ).pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          // Only update the relationships field
          if (this.editingCharacter) {
            this.editingCharacter.relationships = response.relationships;
          }
        },
        error: (err) => {
          console.error('Error regenerating relationships:', err);
          alert('Failed to regenerate relationships');
        }
      });
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
    if (!this.story) return;

    const chapter = this.story.story.chapters.find(c => c.id === chapterId);
    if (!chapter) {
      alert('Chapter not found');
      return;
    }

    // Set the editing chapter ID so we know we're editing, not creating
    this.editingChapterId = chapterId;

    // Load chapter title
    this.chapterTitle = chapter.title;

    // Load chapter data into chapter creation state
    this.story.chapterCreation = {
      plotPoint: chapter.plotPoint || '',
      incorporatedFeedback: chapter.incorporatedFeedback || [],
      feedbackRequests: new Map(),
      generatedChapter: {
        text: chapter.content,
        status: 'ready',
        metadata: {}
      },
      editorReview: undefined
    };

    // Save the story with the updated chapter creation state
    this.storyService.saveStory(this.story);

    // Switch to chapter creation tab
    this.selectTab('chapter-creation');
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

    // Set this as the selected agent
    this.selectedAgentId = characterId;
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
              physicalSensations: response.feedback.physicalSensations,
              emotions: response.feedback.emotions,
              internalMonologue: response.feedback.internalMonologue
            };
            this.story.chapterCreation.feedbackRequests.set(characterId, {
              feedback: characterFeedback,
              status: 'ready'
            });
            // Manually trigger change detection
            this.cdr.detectChanges();
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

    // Set this as the selected agent
    this.selectedAgentId = raterId;
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
              suggestions: response.feedback.suggestions
            };
            this.story.chapterCreation.feedbackRequests.set(raterId, {
              feedback: raterFeedback,
              status: 'ready'
            });
            // Manually trigger change detection
            this.cdr.detectChanges();
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

  incorporateFeedback(source: string, type: string, content: string) {
    if (!this.story) return;

    const feedbackItem = {
      source: source,
      type: type as 'action' | 'dialog' | 'sensation' | 'emotion' | 'thought' | 'suggestion',
      content: content,
      incorporated: false
    };

    this.story.chapterCreation.incorporatedFeedback.push(feedbackItem);
    this.storyService.saveStory(this.story);
  }

  removeFeedbackItem(index: number) {
    if (!this.story) return;
    this.story.chapterCreation.incorporatedFeedback.splice(index, 1);
    this.storyService.saveStory(this.story);
  }

  editFeedbackItem(index: number) {
    if (!this.story) return;
    this.editingFeedbackIndex = index;
    this.editingFeedbackContent = this.story.chapterCreation.incorporatedFeedback[index].content;
  }

  saveFeedbackEdit() {
    if (!this.story || this.editingFeedbackIndex === null) return;
    this.story.chapterCreation.incorporatedFeedback[this.editingFeedbackIndex].content = this.editingFeedbackContent;
    this.editingFeedbackIndex = null;
    this.editingFeedbackContent = '';
    this.storyService.saveStory(this.story);
  }

  cancelFeedbackEdit() {
    this.editingFeedbackIndex = null;
    this.editingFeedbackContent = '';
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

  promptAssistantForChanges() {
    if (!this.story || !this.story.chapterCreation.generatedChapter) {
      alert('Generate a chapter first');
      return;
    }

    if (!this.changeRequest) {
      alert('Please describe the changes you want');
      return;
    }

    this.generatingChapter = true;

    this.generationService.modifyChapter(
      this.story,
      this.story.chapterCreation.generatedChapter.text,
      this.changeRequest
    ).pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response: any) => {
          if (this.story && this.story.chapterCreation.generatedChapter) {
            // The backend returns 'modifiedChapter', not 'modifiedChapterText'
            this.story.chapterCreation.generatedChapter.text = response.modifiedChapter || response.modifiedChapterText;
            this.storyService.saveStory(this.story);
            this.changeRequest = ''; // Clear the request after successful modification
            // Manually trigger change detection
            this.cdr.detectChanges();
          }
          this.generatingChapter = false;
        },
        error: (err) => {
          console.error('Error modifying chapter:', err);
          alert('Failed to modify chapter');
          this.generatingChapter = false;
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

  applyEditorSuggestions(applyAll: boolean) {
    if (!this.story || !this.story.chapterCreation.generatedChapter || !this.story.chapterCreation.editorReview) {
      return;
    }

    // Collect selected suggestions or all suggestions
    const suggestions = applyAll
      ? this.story.chapterCreation.editorReview.suggestions
      : this.story.chapterCreation.editorReview.suggestions.filter(s => s.selected);

    if (suggestions.length === 0) {
      alert('Please select at least one suggestion to apply');
      return;
    }

    // Format suggestions as a string for the writer assistant
    const suggestionsText = suggestions.map((s, i) =>
      `${i + 1}. ${s.issue}: ${s.suggestion}`
    ).join('\n');

    const modificationRequest = `Apply the following editor suggestions:\n\n${suggestionsText}`;

    this.generatingChapter = true;

    this.generationService.modifyChapter(
      this.story,
      this.story.chapterCreation.generatedChapter.text,
      modificationRequest
    ).pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response: any) => {
          if (this.story && this.story.chapterCreation.generatedChapter) {
            // The backend returns 'modifiedChapter', not 'modifiedChapterText'
            this.story.chapterCreation.generatedChapter.text = response.modifiedChapter || response.modifiedChapterText;
            this.story.chapterCreation.editorReview = undefined; // Clear editor review after applying
            this.storyService.saveStory(this.story);
            // Manually trigger change detection
            this.cdr.detectChanges();
          }
          this.generatingChapter = false;
        },
        error: (err) => {
          console.error('Error applying editor suggestions:', err);
          alert('Failed to apply editor suggestions');
          this.generatingChapter = false;
        }
      });
  }

  acceptChapter() {
    if (!this.story || !this.story.chapterCreation.generatedChapter) return;

    // Use custom title if provided, otherwise generate default
    const finalTitle = this.chapterTitle.trim() ||
                       (this.editingChapterId
                         ? (this.story.story.chapters.find(c => c.id === this.editingChapterId)?.title || `Chapter ${this.story.story.chapters.length + 1}`)
                         : `Chapter ${this.story.story.chapters.length + 1}`);

    if (this.editingChapterId) {
      // Update existing chapter
      const chapterIndex = this.story.story.chapters.findIndex(c => c.id === this.editingChapterId);
      if (chapterIndex !== -1) {
        const existingChapter = this.story.story.chapters[chapterIndex];
        this.story.story.chapters[chapterIndex] = {
          ...existingChapter,
          title: finalTitle,
          content: this.story.chapterCreation.generatedChapter.text,
          plotPoint: this.story.chapterCreation.plotPoint,
          incorporatedFeedback: [...this.story.chapterCreation.incorporatedFeedback],
          metadata: {
            ...existingChapter.metadata,
            lastModified: new Date(),
            wordCount: this.story.chapterCreation.generatedChapter.text.split(/\s+/).length
          }
        };
      }
    } else {
      // Create new chapter
      const newChapter: any = {
        id: this.generateId(),
        number: this.story.story.chapters.length + 1,
        title: finalTitle,
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
    }

    // Reset chapter creation state
    this.story.chapterCreation = {
      plotPoint: '',
      incorporatedFeedback: [],
      feedbackRequests: new Map(),
      generatedChapter: undefined,
      editorReview: undefined
    };

    // Clear editing chapter ID and title
    this.editingChapterId = null;
    this.chapterTitle = '';

    this.storyService.saveStory(this.story);

    // Switch to story tab to see chapter
    this.selectTab('story');
  }

  private generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }
}
