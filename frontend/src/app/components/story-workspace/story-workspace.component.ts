import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';
import { Story } from '../../models/story.model';
import { StoryService } from '../../services/story.service';

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
    private storyService: StoryService
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
    // TODO: Call API to generate character details from basic bio
    console.log('Generate character details from bio');
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
    // TODO: Call API to flesh out plot point
    console.log('AI flesh out plot point');
  }

  requestCharacterFeedback(characterId: string) {
    this.generatingFeedback.add(characterId);
    // TODO: Call API to get character feedback
    setTimeout(() => {
      this.generatingFeedback.delete(characterId);
    }, 2000);
  }

  requestRaterFeedback(raterId: string) {
    this.generatingFeedback.add(raterId);
    // TODO: Call API to get rater feedback
    setTimeout(() => {
      this.generatingFeedback.delete(raterId);
    }, 2000);
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
    this.generatingChapter = true;
    // TODO: Call API to generate chapter
    setTimeout(() => {
      this.generatingChapter = false;
    }, 3000);
  }

  promptAssistantForChanges(request: string) {
    // TODO: Call API to modify chapter based on user request
    console.log('Prompt assistant:', request);
  }

  requestEditorReview() {
    this.generatingReview = true;
    // TODO: Call API to get editor review
    setTimeout(() => {
      this.generatingReview = false;
    }, 2000);
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
