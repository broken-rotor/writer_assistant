import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { Subject, takeUntil, finalize } from 'rxjs';
import { Story } from '../../models/story.model';
import { StoryService } from '../../services/story.service';
import { GenerationService } from '../../services/generation.service';
import { LoadingService } from '../../services/loading.service';
import { LoadingSpinnerComponent } from '../loading-spinner/loading-spinner.component';
import { PhaseNavigationComponent } from '../phase-navigation/phase-navigation.component';
import { ArchiveService, RAGResponse } from '../../services/archive.service';
import { NewlineToBrPipe } from '../../pipes/newline-to-br.pipe';
import { SystemPromptFieldComponent } from '../system-prompt-field/system-prompt-field.component';
import { ToastComponent } from '../toast/toast.component';
import { TokenLimitsService, TokenLimitsState } from '../../services/token-limits.service';
import { TokenValidationService, FieldValidationState } from '../../services/token-validation.service';
import { ToastService } from '../../services/toast.service';
import { TokenValidationResult } from '../../models/token-validation.model';
import { 
  ERROR_MESSAGES, 
  ErrorContext, 
  RecoveryAction 
} from '../../constants/token-limits.constants';
import { PhaseStateService, PhaseType } from '../../services/phase-state.service';
import { PlotOutlinePhaseComponent } from '../plot-outline-phase/plot-outline-phase.component';
import { PlotOutlineTabComponent } from '../plot-outline-tab/plot-outline-tab.component';
import { FinalEditPhaseComponent } from '../final-edit-phase/final-edit-phase.component';
import { FeedbackSidebarComponent, FeedbackSidebarConfig, FeedbackSelectionEvent, FeedbackRequestEvent, AddToChatEvent } from '../feedback-sidebar/feedback-sidebar.component';
import { FeedbackService } from '../../services/feedback.service';
import { WorldbuildingChatComponent } from '../worldbuilding-chat/worldbuilding-chat.component';

interface ResearchChatMessage {
  role: string;
  content: string;
  sources?: any[];
  showSources?: boolean;
}

@Component({
  selector: 'app-story-workspace',
  standalone: true,
  imports: [CommonModule, FormsModule, LoadingSpinnerComponent, PhaseNavigationComponent, NewlineToBrPipe, SystemPromptFieldComponent, ToastComponent, PlotOutlinePhaseComponent, PlotOutlineTabComponent, FinalEditPhaseComponent, FeedbackSidebarComponent, WorldbuildingChatComponent],
  templateUrl: './story-workspace.component.html',
  styleUrl: './story-workspace.component.scss'
})
export class StoryWorkspaceComponent implements OnInit, OnDestroy {
  story: Story | null = null;
  activeTab: 'general' | 'characters' | 'raters' | 'plot-outline' | 'story' | 'chapter-creation' = 'general';
  loading = true;
  error: string | null = null;

  // Characters tab state
  selectedCharacterId: string | null = null;
  editingCharacter: any = null;

  // Raters tab state
  selectedRaterId: string | null = null;
  editingRater: any = null;

  // Chapter Creation tab state
  generatingFeedback = new Set<string>();
  generatingChapter = false;
  generatingReview = false;
  selectedAgentId: string | null = null; // Track currently selected agent for feedback display
  editingFeedbackIndex: number | null = null; // Track which feedback item is being edited
  editingFeedbackContent = ''; // Store the edited content temporarily
  changeRequest = ''; // User's request for chapter changes
  editingChapterId: string | null = null; // Track which chapter is being edited (null = creating new)
  chapterTitle = ''; // Title for the chapter being created/edited

  // Research Archive state
  showResearchSidebar = false;
  researchLoading = false;
  researchError: string | null = null;
  researchData: RAGResponse | null = null;
  researchChatHistory: ResearchChatMessage[] = [];
  researchFollowUpInput = '';

  // Token validation state
  tokenLimitsState: TokenLimitsState | null = null;
  fieldValidationResults: FieldValidationState = {};
  tokenLimitsLoading = false;
  tokenLimitsError: string | null = null;
  tokenLimitsErrorContext: ErrorContext | null = null;
  tokenLimitsRetryCount = 0;
  isTokenLimitsRetrying = false;
  isTokenLimitsFallbackMode = false;

  // Phase navigation state
  showPhaseNavigation = false;
  currentPhase: PhaseType = 'plot_outline';

  // Feedback sidebar state
  showFeedbackSidebar = false;
  feedbackSidebarConfig: FeedbackSidebarConfig | null = null;

  private destroy$ = new Subject<void>();

  constructor(
    private route: ActivatedRoute,
    private storyService: StoryService,
    private generationService: GenerationService,
    public loadingService: LoadingService,
    private cdr: ChangeDetectorRef,
    private archiveService: ArchiveService,
    private tokenLimitsService: TokenLimitsService,
    private tokenValidationService: TokenValidationService,
    private toastService: ToastService,
    private phaseStateService: PhaseStateService,
    private feedbackService: FeedbackService
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
    
    // Initialize token limits
    this.initializeTokenLimits();
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
      } else {
        // Migrate story for plot outline integration (WRI-65)
        this.storyService.migrateStoryForPlotOutline(this.story);
        this.initializePhaseNavigation(storyId);
      }
    } catch (err) {
      this.error = 'Failed to load story';
      console.error('Error loading story:', err);
    } finally {
      this.loading = false;
    }
  }

  selectTab(tab: 'general' | 'characters' | 'raters' | 'plot-outline' | 'story' | 'chapter-creation') {
    this.activeTab = tab;
    
    // Initialize plot outline if selecting plot-outline tab
    if (tab === 'plot-outline') {
      this.initializePlotOutline();
    }
    
    // Show phase navigation only for chapter-creation tab
    this.showPhaseNavigation = tab === 'chapter-creation';
    
    // Auto-save when switching tabs (only if validation allows)
    if (this.story && this.canSave()) {
      this.storyService.saveStory(this.story);
    }
  }

  get lastSaved(): Date | null {
    return this.story?.metadata.lastModified || null;
  }

  // Plot outline initialization method
  initializePlotOutline(): void {
    if (!this.story?.plotOutline) {
      if (this.story) {
        this.story.plotOutline = {
          content: '',
          status: 'draft',
          chatHistory: [],
          raterFeedback: new Map(),
          metadata: {
            created: new Date(),
            lastModified: new Date(),
            version: 1
          }
        };
        this.storyService.saveStory(this.story);
      }
    }
  }

  // General tab methods
  loadFileContent(event: Event, target: 'prefix' | 'suffix') {
    const input = event.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) {
      return;
    }

    const file = input.files[0];

    // Validate file type
    const allowedExtensions = ['.txt', '.md'];
    const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (!allowedExtensions.includes(fileExtension)) {
      alert(`Invalid file type. Please upload a ${allowedExtensions.join(' or ')} file.`);
      input.value = ''; // Reset input
      return;
    }

    // Validate file size (1MB = 1048576 bytes)
    const maxSize = 1048576;
    if (file.size > maxSize) {
      alert(`File is too large. Maximum size is 1MB (${(file.size / 1048576).toFixed(2)}MB provided).`);
      input.value = ''; // Reset input
      return;
    }

    // Read file content
    const reader = new FileReader();

    reader.onload = (e: ProgressEvent<FileReader>) => {
      const content = e.target?.result as string;
      if (this.story && content) {
        if (target === 'prefix') {
          this.story.general.systemPrompts.mainPrefix = content;
        } else {
          this.story.general.systemPrompts.mainSuffix = content;
        }
        this.storyService.saveStory(this.story);
      }
    };

    reader.onerror = () => {
      alert('Failed to read file. Please try again.');
      console.error('FileReader error:', reader.error);
    };

    reader.readAsText(file);

    // Reset input so the same file can be loaded again if needed
    input.value = '';
  }

  aiFleshOutWorldbuilding() {
    if (!this.story || !this.story.general.worldbuilding) {
      alert('Please enter worldbuilding text first');
      return;
    }

    this.loadingService.show('Fleshing out worldbuilding...', 'flesh-worldbuilding');

    this.generationService.fleshOut(
      this.story,
      this.story.general.worldbuilding,
      'worldbuilding expansion'
    ).pipe(
      takeUntil(this.destroy$),
      finalize(() => this.loadingService.hide())
    ).subscribe({
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

  // Worldbuilding chat event handlers

  onWorldbuildingUpdated(updatedWorldbuilding: string): void {
    if (this.story) {
      this.story.general.worldbuilding = updatedWorldbuilding;
      this.storyService.saveStory(this.story);
      this.cdr.detectChanges();
    }
  }

  onWorldbuildingConversationStarted(): void {
    console.log('Worldbuilding conversation started');
    // Could show a toast or update UI state here
  }

  onWorldbuildingError(error: string): void {
    console.error('Worldbuilding chat error:', error);
    this.toastService.showError('Worldbuilding Error', error);
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

    this.loadingService.show('Generating character details...', 'generate-character');

    this.generationService.generateCharacterDetails(
      this.story,
      this.editingCharacter.basicBio,
      this.activeCharacters
    ).pipe(
      takeUntil(this.destroy$),
      finalize(() => this.loadingService.hide())
    ).subscribe({
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

    this.loadingService.show('Regenerating character relationships...', 'regenerate-relationships');

    this.generationService.regenerateRelationships(
      this.story,
      this.editingCharacter,
      otherCharacters
    ).pipe(
      takeUntil(this.destroy$),
      finalize(() => this.loadingService.hide())
    ).subscribe({
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

  insertChapterAfter() {
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

    this.loadingService.show('Fleshing out plot point...', 'flesh-plotpoint');

    this.generationService.fleshOut(
      this.story,
      this.story.chapterCreation.plotPoint,
      'plot point expansion'
    ).pipe(
      takeUntil(this.destroy$),
      finalize(() => this.loadingService.hide())
    ).subscribe({
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

    this.loadingService.show(`Getting feedback from ${character.name}...`, 'character-feedback');

    this.generationService.requestCharacterFeedback(
      this.story,
      character,
      this.story.chapterCreation.plotPoint
    ).pipe(
      takeUntil(this.destroy$),
      finalize(() => {
        this.generatingFeedback.delete(characterId);
        this.loadingService.hide();
      })
    ).subscribe({
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
        },
        error: (err) => {
          console.error('Error requesting character feedback:', err);
          alert('Failed to get character feedback');
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

    this.loadingService.show(`Getting feedback from ${rater.name}...`, 'rater-feedback');

    this.generationService.requestRaterFeedback(
      this.story,
      rater,
      this.story.chapterCreation.plotPoint
    ).pipe(
      takeUntil(this.destroy$),
      finalize(() => {
        this.generatingFeedback.delete(raterId);
        this.loadingService.hide();
      })
    ).subscribe({
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
        },
        error: (err) => {
          console.error('Error requesting rater feedback:', err);
          alert('Failed to get rater feedback');
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

    if (!this.story.chapterCreation.plotPoint.trim()) {
      this.toastService.show('Please enter a plot point before generating a chapter', 'warning');
      return;
    }

    // Check plot outline status and warn user if needed
    this.checkPlotOutlineStatus();

    this.generatingChapter = true;
    this.loadingService.show('Generating chapter...', 'generate-chapter');

    this.generationService.generateChapter(this.story)
      .pipe(
        takeUntil(this.destroy$),
        finalize(() => {
          this.generatingChapter = false;
          this.loadingService.hide();
        })
      ).subscribe({
        next: (response) => {
          if (this.story) {
            this.story.chapterCreation.generatedChapter = {
              text: response.chapterText,
              status: 'ready',
              metadata: {
                generatedAt: new Date(),
                plotOutlineStatus: this.story.plotOutline?.status || 'none',
                plotOutlineVersion: this.story.plotOutline?.metadata.version || 0
              }
            };
            this.storyService.saveStory(this.story);
            this.toastService.show('Chapter generated successfully!', 'success');
          }
        },
        error: (err) => {
          console.error('Error generating chapter:', err);
          this.toastService.show('Error generating chapter: ' + err, 'error');
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
    this.loadingService.show('Modifying chapter...', 'modify-chapter');

    this.generationService.modifyChapter(
      this.story,
      this.story.chapterCreation.generatedChapter.text,
      this.changeRequest
    ).pipe(
      takeUntil(this.destroy$),
      finalize(() => {
        this.generatingChapter = false;
        this.loadingService.hide();
      })
    ).subscribe({
        next: (response: any) => {
          if (this.story && this.story.chapterCreation.generatedChapter) {
            // The backend returns 'modifiedChapter', not 'modifiedChapterText'
            this.story.chapterCreation.generatedChapter.text = response.modifiedChapter || response.modifiedChapterText;
            this.storyService.saveStory(this.story);
            this.changeRequest = ''; // Clear the request after successful modification
            // Manually trigger change detection
            this.cdr.detectChanges();
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
    this.loadingService.show('Requesting editor review...', 'editor-review');

    this.generationService.requestEditorReview(
      this.story,
      this.story.chapterCreation.generatedChapter.text
    ).pipe(
      takeUntil(this.destroy$),
      finalize(() => {
        this.generatingReview = false;
        this.loadingService.hide();
      })
    ).subscribe({
        next: (response) => {
          if (this.story) {
            this.story.chapterCreation.editorReview = {
              suggestions: response.suggestions,
              userSelections: response.suggestions.map(() => false)
            };
          }
        },
        error: (err) => {
          console.error('Error requesting editor review:', err);
          alert('Failed to get editor review');
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
    this.loadingService.show('Applying editor suggestions...', 'apply-suggestions');

    this.generationService.modifyChapter(
      this.story,
      this.story.chapterCreation.generatedChapter.text,
      modificationRequest
    ).pipe(
      takeUntil(this.destroy$),
      finalize(() => {
        this.generatingChapter = false;
        this.loadingService.hide();
      })
    ).subscribe({
        next: (response: any) => {
          if (this.story && this.story.chapterCreation.generatedChapter) {
            // The backend returns 'modifiedChapter', not 'modifiedChapterText'
            this.story.chapterCreation.generatedChapter.text = response.modifiedChapter || response.modifiedChapterText;
            this.story.chapterCreation.editorReview = undefined; // Clear editor review after applying
            this.storyService.saveStory(this.story);
            // Manually trigger change detection
            this.cdr.detectChanges();
          }
        },
        error: (err) => {
          console.error('Error applying editor suggestions:', err);
          alert('Failed to apply editor suggestions');
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

  // Token validation methods
  private initializeTokenLimits() {
    this.tokenLimitsLoading = true;
    this.tokenLimitsError = null;
    this.tokenLimitsErrorContext = null;
    this.isTokenLimitsFallbackMode = false;

    this.tokenLimitsService.getTokenLimits()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (state) => {
          this.tokenLimitsState = state;
          this.tokenLimitsLoading = state.isLoading;
          this.tokenLimitsError = state.error;
          this.tokenLimitsErrorContext = state.errorContext || null;
          this.isTokenLimitsFallbackMode = state.isFallbackMode || false;
          
          // Show appropriate notifications
          if (state.error && state.errorContext) {
            this.handleTokenLimitsError(state.errorContext);
          } else if (state.isFallbackMode) {
            this.toastService.showFallbackMode('Token Limits Service');
          } else if (!state.isLoading && !state.error) {
            // Service restored successfully
            if (this.tokenLimitsRetryCount > 0) {
              this.toastService.showServiceRestored('Token Limits Service');
              this.tokenLimitsRetryCount = 0;
            }
          }
          
          this.cdr.markForCheck();
        },
        error: (err) => {
          console.error('Failed to load token limits:', err);
          this.handleTokenLimitsInitializationError(err);
        }
      });
  }

  /**
   * Handle token limits error with recovery actions
   */
  private handleTokenLimitsError(errorContext: ErrorContext) {
    this.toastService.showTokenLimitsError(
      errorContext.message,
      errorContext.recoveryActions,
      () => this.retryTokenLimits(),
      () => this.useTokenLimitsFallback()
    );
  }

  /**
   * Handle token limits initialization error
   */
  private handleTokenLimitsInitializationError() {
    this.tokenLimitsLoading = false;
    this.isTokenLimitsRetrying = false;
    this.tokenLimitsError = ERROR_MESSAGES.TOKEN_LIMITS_FAILED;
    this.tokenLimitsRetryCount++;
    
    // Use fallback mode to keep app functional
    this.isTokenLimitsFallbackMode = true;
    
    this.toastService.showTokenLimitsError(
      this.tokenLimitsError!,
      [RecoveryAction.RETRY, RecoveryAction.USE_FALLBACK],
      () => this.retryTokenLimits(),
      () => this.useTokenLimitsFallback()
    );
    
    this.cdr.markForCheck();
  }

  /**
   * Retry token limits loading
   */
  retryTokenLimits() {
    if (this.tokenLimitsLoading || this.isTokenLimitsRetrying) {
      return;
    }
    
    this.isTokenLimitsRetrying = true;
    this.tokenLimitsError = null;
    this.tokenLimitsErrorContext = null;
    this.cdr.markForCheck();
    
    // Retry initialization
    this.initializeTokenLimits();
  }

  /**
   * Use token limits fallback mode
   */
  useTokenLimitsFallback() {
    this.isTokenLimitsFallbackMode = true;
    this.tokenLimitsError = null;
    this.tokenLimitsErrorContext = null;
    this.tokenLimitsLoading = false;
    this.isTokenLimitsRetrying = false;
    
    this.toastService.showInfo(
      'Using default token limits',
      'The app will continue to work with estimated token counts'
    );
    
    this.cdr.markForCheck();
  }

  /**
   * Check if token limits retry is available
   */
  canRetryTokenLimits(): boolean {
    return !!this.tokenLimitsError && !this.tokenLimitsLoading && !this.isTokenLimitsRetrying;
  }

  onFieldValidationChange(fieldType: string, result: TokenValidationResult) {
    this.fieldValidationResults[fieldType] = result;
  }

  canSave(): boolean {
    // If token limits are still loading or retrying, allow save (graceful degradation)
    if (this.tokenLimitsLoading || this.isTokenLimitsRetrying) {
      return true;
    }

    // If in fallback mode, allow save with warnings
    if (this.isTokenLimitsFallbackMode) {
      return true;
    }

    // If there are no validation results yet, allow save
    if (Object.keys(this.fieldValidationResults).length === 0) {
      return true;
    }

    return this.tokenValidationService.canSave(this.fieldValidationResults);
  }

  getValidationSummary(): string {
    if (this.tokenLimitsLoading) {
      return 'Loading token limits...';
    }

    if (this.isTokenLimitsRetrying) {
      return 'Retrying token limits...';
    }

    if (this.tokenLimitsError && !this.isTokenLimitsFallbackMode) {
      return 'Token validation unavailable';
    }

    if (this.isTokenLimitsFallbackMode) {
      return 'Using default token limits';
    }

    const results = Object.values(this.fieldValidationResults);
    const invalidFields = results.filter(r => !r.isValid);
    
    if (invalidFields.length === 0) {
      return 'All fields within token limits';
    }

    return `${invalidFields.length} field(s) exceed token limits`;
  }

  // Research Archive methods
  researchPlotPoint() {
    if (!this.story || !this.story.chapterCreation.plotPoint) {
      alert('Please enter a plot point first');
      return;
    }

    this.showResearchSidebar = true;
    this.researchLoading = true;
    this.researchError = null;
    this.researchData = null;
    this.researchChatHistory = [];
    this.researchFollowUpInput = '';

    // Create a detailed research query
    const researchQuery = `Based on my story archive, provide relevant ideas, themes, plot elements, character archetypes, or writing patterns related to this plot point: "${this.story.chapterCreation.plotPoint}".

Help me understand:
1. Similar plot developments or scenes from my previous stories
2. Character interactions or dynamics that could inform this scene
3. Thematic elements that might be relevant
4. Writing style or techniques I've used in similar situations

Provide actionable insights and creative suggestions to enhance this plot point.`;

    // Add user message to chat history
    this.researchChatHistory.push({
      role: 'user',
      content: researchQuery,
      showSources: false
    });

    this.archiveService.ragQuery(
      researchQuery,
      8, // More context chunks for better coverage
      1500, // Longer response for detailed insights
      0.4 // Slightly higher temperature for creativity
    ).pipe(
      takeUntil(this.destroy$),
      finalize(() => {
        this.researchLoading = false;
        this.cdr.detectChanges();
      })
    ).subscribe({
      next: (response) => {
        this.researchData = response;

        // Add assistant response to chat history
        this.researchChatHistory.push({
          role: 'assistant',
          content: response.answer,
          sources: response.sources,
          showSources: false
        });

        this.cdr.detectChanges();
        this.scrollChatToBottom();
      },
      error: (err) => {
        console.error('Research query failed:', err);
        if (err.status === 503) {
          const errorMessage = err.error?.detail || '';
          if (errorMessage.includes('loading')) {
            this.researchError = 'The AI model is still loading. Please wait a moment and try again.';
          } else {
            this.researchError = 'RAG feature is not available. Please ensure both archive and LLM are configured. See RAG_FEATURE.md for setup instructions.';
          }
        } else {
          this.researchError = 'Failed to research plot point. Please try again.';
        }
        this.cdr.detectChanges();
      }
    });
  }

  sendResearchFollowUp() {
    if (!this.researchFollowUpInput.trim() || this.researchLoading) {
      return;
    }

    const userQuestion = this.researchFollowUpInput.trim();
    this.researchFollowUpInput = '';
    this.researchLoading = true;
    this.researchError = null;

    // Add user message to chat history
    this.researchChatHistory.push({
      role: 'user',
      content: userQuestion,
      showSources: false
    });

    // Build message array for chat API
    const messages = this.researchChatHistory.map(msg => ({
      role: msg.role,
      content: msg.content
    }));

    this.archiveService.ragChat(
      messages,
      5, // Fewer chunks for follow-ups
      1000, // Shorter responses for follow-ups
      0.5 // Slightly more creative for conversation
    ).pipe(
      takeUntil(this.destroy$),
      finalize(() => {
        this.researchLoading = false;
        this.cdr.detectChanges();
      })
    ).subscribe({
      next: (response) => {
        // Add assistant response to chat history
        this.researchChatHistory.push({
          role: 'assistant',
          content: response.answer,
          sources: response.sources,
          showSources: false
        });

        // Update research data to show latest sources
        this.researchData = response;

        this.cdr.detectChanges();
        this.scrollChatToBottom();
      },
      error: (err) => {
        console.error('Follow-up query failed:', err);
        // Remove the user message that failed
        this.researchChatHistory.pop();
        this.researchFollowUpInput = userQuestion; // Restore input

        if (err.status === 503) {
          const errorMessage = err.error?.detail || '';
          if (errorMessage.includes('loading')) {
            this.researchError = 'The AI model is still loading. Please wait a moment and try again.';
          } else {
            this.researchError = 'RAG feature is not available.';
          }
        } else {
          this.researchError = 'Failed to process follow-up question. Please try again.';
        }
        this.cdr.detectChanges();
      }
    });
  }

  onResearchKeyPress(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendResearchFollowUp();
    }
  }

  clearResearchChat() {
    if (!confirm('Clear the entire research conversation?')) {
      return;
    }
    this.researchChatHistory = [];
    this.researchData = null;
    this.researchError = null;
    this.researchFollowUpInput = '';
  }

  closeResearchSidebar() {
    this.showResearchSidebar = false;
    this.researchData = null;
    this.researchError = null;
    this.researchChatHistory = [];
    this.researchFollowUpInput = '';
  }

  private scrollChatToBottom() {
    setTimeout(() => {
      const chatContainer = document.querySelector('.research-chat-history');
      if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
      }
    }, 100);
  }

  getSourceFileName(source: any): string {
    return source.file_name || 'Unknown';
  }

  getSourceExcerpt(source: any): string {
    const text = source.matching_section || '';
    return text.length > 150 ? text.substring(0, 150) + '...' : text;
  }

  getSimilarityLabel(score: number): string {
    if (score >= 0.8) return 'High';
    if (score >= 0.6) return 'Medium';
    return 'Low';
  }

  getSimilarityClass(score: number): string {
    if (score >= 0.8) return 'high';
    if (score >= 0.6) return 'medium';
    return 'low';
  }

  // Phase Navigation Methods
  private initializePhaseNavigation(storyId: string) {
    if (!this.story) return;

    // Initialize ChapterComposeState if it doesn't exist
    if (!this.story.chapterCompose) {
      const nextChapterNumber = this.story.story.chapters.length + 1;
      this.story.chapterCompose = this.phaseStateService.initializeChapterComposeState(storyId, nextChapterNumber);
      
      // Save the updated story
      this.storyService.saveStory(this.story);
    } else {
      // Load existing state
      this.phaseStateService.loadChapterComposeState(this.story.chapterCompose);
    }

    // Subscribe to phase changes
    this.phaseStateService.currentPhase$
      .pipe(takeUntil(this.destroy$))
      .subscribe(phase => {
        this.currentPhase = phase;
        this.cdr.detectChanges();
      });
  }

  onPhaseChanged(newPhase: PhaseType) {
    this.currentPhase = newPhase;
    
    // Update the story's chapter compose state
    if (this.story && this.story.chapterCompose) {
      this.story.chapterCompose.currentPhase = newPhase;
      this.story.chapterCompose.metadata.lastModified = new Date();
      
      // Save the updated story
      this.storyService.saveStory(this.story);
    }
    
    // Update feedback sidebar config if it's open
    this.updateFeedbackSidebarConfig();
    
    this.cdr.detectChanges();
  }

  getCurrentChapterNumber(): number {
    if (!this.story) return 1;
    return this.story.story.chapters.length + 1;
  }

  getCurrentChapterTitle(): string {
    if (!this.story?.chapterCompose) return '';
    
    const currentPhase = this.story.chapterCompose.currentPhase;
    switch (currentPhase) {
      case 'plot_outline':
        return this.story.chapterCompose.phases.plotOutline.draftSummary || '';
      case 'chapter_detail':
        return this.story.chapterCompose.phases.chapterDetailer.chapterDraft.title || '';
      case 'final_edit':
        return this.story.chapterCompose.phases.finalEdit.finalChapter.title || '';
      default:
        return '';
    }
  }

  // Plot Outline Phase handlers
  onPlotOutlinePhaseCompleted(): void {
    console.log('Plot outline phase completed');
    // The phase navigation component will handle the actual phase advancement
  }

  onOutlineUpdated(outlineItems: any[]): void {
    console.log('Outline updated:', outlineItems);
    // The plot outline component handles saving, we just need to trigger change detection
    this.cdr.detectChanges();
  }

  // Plot Outline Tab handlers
  onPlotOutlineUpdated(content: string): void {
    console.log('Plot outline content updated:', content);
    // Handle outline updates
    if (this.story) {
      this.storyService.saveStory(this.story);
    }
  }

  onPlotOutlineApproved(): void {
    console.log('Plot outline approved');
    // Handle outline approval
    if (this.story?.plotOutline) {
      this.story.plotOutline.status = 'approved';
      this.story.plotOutline.metadata.approvedAt = new Date();
      this.story.plotOutline.metadata.lastModified = new Date();
    }
    if (this.story) {
      this.storyService.saveStory(this.story);
    }
  }

  // Final Edit Phase handlers
  onFinalEditPhaseCompleted(): void {
    console.log('Final edit phase completed');
    // The phase navigation component will handle the actual phase advancement
    this.cdr.detectChanges();
  }

  onChapterFinalized(chapterData: { content: string; title: string; }): void {
    console.log('Chapter finalized:', chapterData);
    // Update the story with the finalized chapter
    if (this.story) {
      // Add the finalized chapter to the story's chapters array
      const newChapter = {
        id: `chapter-${this.getCurrentChapterNumber()}`,
        number: this.getCurrentChapterNumber(),
        title: chapterData.title,
        content: chapterData.content,
        plotPoint: '',
        incorporatedFeedback: [],
        metadata: {
          created: new Date(),
          lastModified: new Date(),
          wordCount: chapterData.content.split(/\s+/).length
        }
      };

      if (!this.story.story.chapters) {
        this.story.story.chapters = [];
      }

      // Replace existing chapter or add new one
      const existingIndex = this.story.story.chapters.findIndex((ch: any) => ch.number === newChapter.number);
      if (existingIndex >= 0) {
        this.story.story.chapters[existingIndex] = newChapter;
      } else {
        this.story.story.chapters.push(newChapter);
      }

      // Save the updated story
      this.storyService.saveStory(this.story);
    }
    this.cdr.detectChanges();
  }

  // Feedback Sidebar Methods
  initializeFeedbackSidebar(): void {
    if (!this.story) return;

    this.feedbackSidebarConfig = {
      phase: this.currentPhase,
      storyId: this.story.id,
      chapterNumber: this.getCurrentChapterNumber(),
      showRequestButtons: true,
      showChatIntegration: true,
      maxHeight: '600px'
    };
  }

  toggleFeedbackSidebar(): void {
    this.showFeedbackSidebar = !this.showFeedbackSidebar;
    
    if (this.showFeedbackSidebar) {
      this.initializeFeedbackSidebar();
    }
  }

  closeFeedbackSidebar(): void {
    this.showFeedbackSidebar = false;
  }

  onFeedbackSelectionChanged(event: FeedbackSelectionEvent): void {
    console.log('Feedback selection changed:', event);
    // Handle feedback selection changes if needed
  }

  onFeedbackRequested(event: FeedbackRequestEvent): void {
    console.log('Feedback requested:', event);
    this.toastService.showInfo(`Requesting feedback from ${event.agentName}...`);
  }

  onAddToChat(event: AddToChatEvent): void {
    console.log('Adding feedback to chat:', event);
    
    if (!this.story || !this.feedbackSidebarConfig) return;

    // Add feedback to chat via the feedback service
    this.feedbackService.addFeedbackToChat(
      this.feedbackSidebarConfig.storyId,
      this.feedbackSidebarConfig.chapterNumber,
      this.feedbackSidebarConfig.phase,
      event.selectedFeedback,
      event.userComment
    ).subscribe(success => {
      if (success) {
        this.toastService.showSuccess(
          `Added ${event.selectedFeedback.length} feedback item(s) to chat`
        );
      } else {
        this.toastService.showError('Failed to add feedback to chat');
      }
    });
  }

  // Update feedback sidebar config when phase changes
  private updateFeedbackSidebarConfig(): void {
    if (this.feedbackSidebarConfig && this.story) {
      this.feedbackSidebarConfig = {
        ...this.feedbackSidebarConfig,
        phase: this.currentPhase,
        chapterNumber: this.getCurrentChapterNumber()
      };
    }
  }

  // ============================================================================
  // PLOT OUTLINE INTEGRATION METHODS (WRI-65)
  // ============================================================================

  /**
   * Check plot outline status and provide user guidance
   */
  private checkPlotOutlineStatus(): void {
    if (!this.story) return;

    if (!this.story.plotOutline) {
      this.toastService.show('No plot outline found. Consider creating one for better chapter consistency.', 'info');
      return;
    }

    switch (this.story.plotOutline.status) {
      case 'draft':
        this.toastService.show('Plot outline is still in draft. Consider getting rater feedback before generating chapters.', 'warning');
        break;
      case 'under_review':
        this.toastService.show('Plot outline is under review. Generated chapter may need revision if outline changes.', 'info');
        break;
      case 'approved':
        // No warning needed
        break;
      default:
        this.toastService.show(`Plot outline status: ${this.story.plotOutline.status}`, 'info');
    }
  }

  /**
   * Get display text for plot outline status
   */
  getPlotOutlineStatusDisplay(): string {
    if (!this.story?.plotOutline) return 'None';
    
    switch (this.story.plotOutline.status) {
      case 'draft': return '⏳ Draft';
      case 'under_review': return '👀 Under Review';
      case 'approved': return '✅ Approved';
      case 'needs_revision': return '🔄 Needs Revision';
      default: return this.story.plotOutline.status;
    }
  }
}
