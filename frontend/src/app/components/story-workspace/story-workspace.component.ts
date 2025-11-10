import { Component, OnInit, OnDestroy, ChangeDetectorRef, inject, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { Subject, takeUntil, finalize } from 'rxjs';
import { Story, Chapter } from '../../models/story.model';
import { StoryService } from '../../services/story.service';
import { GenerationService } from '../../services/generation.service';
import { LoadingService } from '../../services/loading.service';
import { LoadingSpinnerComponent } from '../loading-spinner/loading-spinner.component';
import { ArchiveService, RAGResponse } from '../../services/archive.service';
import { SSEProgressUpdate } from '../../services/sse-streaming.service';
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
import { PlotOutlineTabComponent } from '../plot-outline-tab/plot-outline-tab.component';
import { FeedbackSidebarComponent, FeedbackSidebarConfig } from '../feedback-sidebar/feedback-sidebar.component';
import { FeedbackService } from '../../services/feedback.service';
import { ContextBuilderService } from '../../services/context-builder.service';
import { WorldbuildingTabComponent } from '../worldbuilding-tab/worldbuilding-tab.component';
import { ChapterEditorComponent } from '../chapter-editor/chapter-editor.component';
import { MatIconModule } from '@angular/material/icon';

interface ResearchChatMessage {
  role: string;
  content: string;
  sources?: any[];
  showSources?: boolean;
}

@Component({
  selector: 'app-story-workspace',
  standalone: true,
  imports: [CommonModule, FormsModule, LoadingSpinnerComponent, NewlineToBrPipe, SystemPromptFieldComponent, ToastComponent, PlotOutlineTabComponent, FeedbackSidebarComponent, WorldbuildingTabComponent, ChapterEditorComponent, MatIconModule],
  templateUrl: './story-workspace.component.html',
  styleUrl: './story-workspace.component.scss'
})
export class StoryWorkspaceComponent implements OnInit, OnDestroy {
  story: Story | null = null;
  activeTab: 'general' | 'worldbuilding' | 'characters' | 'raters' | 'plot-outline' | 'story' = 'general';
  loading = true;
  error: string | null = null;
  
  // Chapter editing state
  isEditingChapter = false;
  currentEditingChapter: Chapter | null = null;

  // Characters tab state
  selectedCharacterId: string | null = null;
  editingCharacter: any = null;

  // Raters tab state
  selectedRaterId: string | null = null;
  editingRater: any = null;
  @ViewChild('raterFileInput') raterFileInput!: ElementRef<HTMLInputElement>;

  // Research Archive state
  showResearchSidebar = false;
  researchLoading = false;
  researchError: string | null = null;
  researchData: RAGResponse | null = null;
  researchChatHistory: ResearchChatMessage[] = [];
  researchFollowUpInput = '';
  researchProgress: SSEProgressUpdate | null = null;

  // Token validation state
  tokenLimitsState: TokenLimitsState | null = null;
  fieldValidationResults: FieldValidationState = {};
  tokenLimitsLoading = false;
  tokenLimitsError: string | null = null;
  tokenLimitsErrorContext: ErrorContext | null = null;
  tokenLimitsRetryCount = 0;
  isTokenLimitsRetrying = false;
  isTokenLimitsFallbackMode = false;

  // Feedback sidebar state
  showFeedbackSidebar = false;
  feedbackSidebarConfig: FeedbackSidebarConfig | null = null;

  private destroy$ = new Subject<void>();

  // Dependency injection
  private route = inject(ActivatedRoute);
  private storyService = inject(StoryService);
  private generationService = inject(GenerationService);
  public loadingService = inject(LoadingService);
  private cdr = inject(ChangeDetectorRef);
  private archiveService = inject(ArchiveService);
  private tokenLimitsService = inject(TokenLimitsService);
  private tokenValidationService = inject(TokenValidationService);
  private toastService = inject(ToastService);
  private feedbackService = inject(FeedbackService);
  private contextBuilderService = inject(ContextBuilderService);

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
      }
    } catch (err) {
      this.error = 'Failed to load story';
      console.error('Error loading story:', err);
    } finally {
      this.loading = false;
    }
  }

  selectTab(tab: 'general' | 'worldbuilding' | 'characters' | 'raters' | 'plot-outline' | 'story') {
    this.activeTab = tab;
    
    // Initialize plot outline if selecting plot-outline tab
    if (tab === 'plot-outline') {
      this.initializePlotOutline();
    }
    
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
  loadFileContent(event: Event, target: 'prefix' | 'suffix' | 'rater') {
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
        } else if (target === 'suffix') {
          this.story.general.systemPrompts.mainSuffix = content;
        } else if (target === 'rater' && this.editingRater) {
          this.editingRater.systemPrompt = content;
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

  // Story update handler for worldbuilding tab
  onStoryUpdated(updatedStory: Story): void {
    this.story = updatedStory;
    this.storyService.saveStory(this.story);
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
      this.activeCharacters,
      (update) => {
        // Update loading with progress, phase, and message
        this.loadingService.updateProgress(update.progress, update.message, update.phase);
      }
    ).pipe(
      takeUntil(this.destroy$),
      finalize(() => this.loadingService.hide())
    ).subscribe({
        next: (response) => {
          // Populate the editing character with generated details
          const characterInfo = response.character_info;
          this.editingCharacter.name = characterInfo.name;
          this.editingCharacter.sex = characterInfo.sex;
          this.editingCharacter.gender = characterInfo.gender;
          this.editingCharacter.sexualPreference = characterInfo.sexualPreference;
          this.editingCharacter.age = characterInfo.age;
          this.editingCharacter.physicalAppearance = characterInfo.physicalAppearance;
          this.editingCharacter.usualClothing = characterInfo.usualClothing;
          this.editingCharacter.personality = characterInfo.personality;
          this.editingCharacter.motivations = characterInfo.motivations;
          this.editingCharacter.fears = characterInfo.fears;
          this.editingCharacter.relationships = characterInfo.relationships;
        },
        error: (err) => {
          console.error('Error generating character details:', err);
          alert('Failed to generate character details');
        }
      });
  }

  regenerateBio() {
    if (!this.story || !this.editingCharacter) {
      alert('Please select a character first');
      return;
    }

    // Check if character has sufficient details to regenerate bio
    const hasDetails = this.editingCharacter.name || 
                      this.editingCharacter.personality || 
                      this.editingCharacter.motivations || 
                      this.editingCharacter.physicalAppearance;
    
    if (!hasDetails) {
      alert('Please fill in some character details first (name, personality, motivations, etc.)');
      return;
    }

    this.loadingService.show('Regenerating bio summary...', 'regenerate-bio');

    this.generationService.regenerateBio(
      this.story,
      this.editingCharacter,
      (update) => {
        // Update loading with progress, phase, and message
        this.loadingService.updateProgress(update.progress, update.message, update.phase);
      }
    ).pipe(
      takeUntil(this.destroy$),
      finalize(() => this.loadingService.hide())
    ).subscribe({
        next: (response) => {
          // Update the basic bio with the generated summary
          this.editingCharacter.basicBio = response.basicBio;
        },
        error: (err) => {
          console.error('Error regenerating bio:', err);
          alert('Failed to regenerate bio');
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
            this.editingCharacter.relationships = response.character_info.relationships;
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

  deleteChapter(chapterId: string) {
    if (!this.story || !confirm('Delete this chapter?')) return;

    this.story.story.chapters = this.story.story.chapters.filter(c => c.id !== chapterId);
    this.storyService.saveStory(this.story);
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
          this.handleTokenLimitsInitializationError();
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

  onRaterFieldValidationChange(result: TokenValidationResult) {
    // Store validation result for the current rater's system prompt
    if (this.editingRater) {
      this.fieldValidationResults[`rater-${this.editingRater.id}-systemPrompt`] = result;
    }
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
    if (!this.story) {
      alert('Please enter a plot point first');
      return;
    }

    this.showResearchSidebar = true;
    this.researchLoading = true;
    this.researchError = null;
    this.researchData = null;
    this.researchChatHistory = [];
    this.researchFollowUpInput = '';
    this.researchProgress = null;

    // Create a detailed research query from the current plot outline or story summary
    const plotContext = this.story.plotOutline?.content || this.story.story.summary || 'the story';
    const researchQuery = `Based on my story archive, provide relevant ideas, themes, plot elements, character archetypes, or writing patterns related to: "${plotContext}".

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

    this.archiveService.ragQueryStream(
      researchQuery,
      8, // More context chunks for better coverage
      1500, // Longer response for detailed insights
      0.4, // Slightly higher temperature for creativity
      undefined, // filterFileName
      {
        onProgress: (progress: SSEProgressUpdate) => {
          this.researchProgress = progress;
          this.cdr.detectChanges();
        },
        onError: (error: Error) => {
          console.error('Research streaming error:', error);
          this.researchError = error.message;
          this.cdr.detectChanges();
        }
      }
    ).pipe(
      takeUntil(this.destroy$),
      finalize(() => {
        this.researchLoading = false;
        this.researchProgress = null;
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
      0.5, // Slightly more creative for conversation
      undefined, // No file filter
      undefined // No progress callback for this usage
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

  /**
   * Navigate to chapter editor
   */
  editChapter(chapter: Chapter): void {
    this.currentEditingChapter = chapter;
    this.isEditingChapter = true;
  }

  /**
   * Return from chapter editor to main workspace
   */
  onBackFromChapterEditor(): void {
    this.isEditingChapter = false;
    this.currentEditingChapter = null;
  }
}
