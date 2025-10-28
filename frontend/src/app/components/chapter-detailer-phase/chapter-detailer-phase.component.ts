import { Component, Input, Output, EventEmitter, OnInit, OnDestroy, ChangeDetectorRef, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import {
  Story,
  OutlineItem,
  ChatMessage,
  EnhancedFeedbackItem
} from '../../models/story.model';
import { ChatInterfaceComponent, ChatInterfaceConfig, MessageActionEvent } from '../chat-interface/chat-interface.component';
import { FeedbackSidebarComponent, FeedbackSidebarConfig, FeedbackSelectionEvent, AddToChatEvent } from '../feedback-sidebar/feedback-sidebar.component';
import { GenerationService } from '../../services/generation.service';
import { ConversationService } from '../../services/conversation.service';
import { PhaseStateService } from '../../services/phase-state.service';
import { FeedbackService } from '../../services/feedback.service';
import { StoryService } from '../../services/story.service';
import { ToastService } from '../../services/toast.service';
import { TokenCountingService } from '../../services/token-counting.service';
import { NewlineToBrPipe } from '../../pipes/newline-to-br.pipe';

interface ChapterDraftVersion {
  id: string;
  name: string;
  content: string;
  title: string;
  wordCount: number;
  created: Date;
  sourceType: 'initial' | 'chat' | 'feedback' | 'continuation';
  sourceMessageId?: string;
  incorporatedFeedback: string[]; // IDs of incorporated feedback items
  isActive: boolean;
}

@Component({
  selector: 'app-chapter-detailer-phase',
  standalone: true,
  imports: [
    CommonModule, 
    FormsModule, 
    ChatInterfaceComponent,
    FeedbackSidebarComponent,
    NewlineToBrPipe
  ],
  templateUrl: './chapter-detailer-phase.component.html',
  styleUrls: ['./chapter-detailer-phase.component.scss']
})
export class ChapterDetailerPhaseComponent implements OnInit, OnDestroy {
  @Input() story!: Story;
  @Input() chapterNumber = 1;
  @Output() phaseCompleted = new EventEmitter<void>();
  @Output() chapterUpdated = new EventEmitter<ChapterDraftVersion>();

  // Plot outline data from Phase 1 (read-only)
  plotOutlineItems: OutlineItem[] = [];
  plotOutlineSummary = '';
  showOutlineDetails = false;

  // Chapter draft versions
  draftVersions: ChapterDraftVersion[] = [];
  currentVersionId = '';
  nextVersionNumber = 1;

  // Target and progress tracking
  targetWordCount = 2000;
  showWordCountSettings = false;

  // Chat interface configuration
  chatConfig: ChatInterfaceConfig = {
    phase: 'chapter_detail',
    storyId: '',
    chapterNumber: 1,
    enableBranching: true,
    placeholder: 'Describe how you want to develop this chapter...',
    showTimestamps: true,
    allowMessageEditing: true
  };

  // Feedback sidebar configuration
  feedbackConfig: FeedbackSidebarConfig = {
    phase: 'chapter_detail',
    storyId: '',
    chapterNumber: 1,
    showRequestButtons: true,
    showChatIntegration: true
  };

  // UI state
  showChat = true;
  showFeedbackSidebar = true;
  isGeneratingChapter = false;
  isContinuingChapter = false;
  isIncorporatingFeedback = false;
  selectedFeedbackItems: EnhancedFeedbackItem[] = [];

  // Phase completion tracking
  completionCriteria = {
    hasInitialDraft: false,
    meetsMinWordCount: false,
    hasFeedbackIncorporated: false,
    hasReviewedContent: false
  };

  private destroy$ = new Subject<void>();
  private generationService = inject(GenerationService);
  private conversationService = inject(ConversationService);
  private phaseStateService = inject(PhaseStateService);
  private feedbackService = inject(FeedbackService);
  private storyService = inject(StoryService);
  private toastService = inject(ToastService);
  private tokenCountingService = inject(TokenCountingService);
  private cdr = inject(ChangeDetectorRef);

  ngOnInit(): void {
    this.initializeComponent();
    this.setupConfigurations();
    this.loadPlotOutlineData();
    this.loadExistingDrafts();
    this.validatePhaseCompletion();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private initializeComponent(): void {
    // Initialize with story data
    if (this.story) {
      this.chatConfig.storyId = this.story.id;
      this.chatConfig.chapterNumber = this.chapterNumber;
      this.feedbackConfig.storyId = this.story.id;
      this.feedbackConfig.chapterNumber = this.chapterNumber;
    }
  }

  private setupConfigurations(): void {
    // Set up chat configuration for chapter development
    this.chatConfig = {
      ...this.chatConfig,
      enableMessageTypes: ['user', 'assistant'],
      maxHeight: '400px'
    };

    // Set up feedback sidebar configuration
    this.feedbackConfig = {
      ...this.feedbackConfig,
      maxHeight: '500px'
    };
  }

  private loadPlotOutlineData(): void {
    // Load plot outline data from Phase 1 via PhaseStateService
    this.phaseStateService.chapterComposeState$
      .pipe(takeUntil(this.destroy$))
      .subscribe(state => {
        if (state?.phases.plotOutline) {
          this.plotOutlineItems = Array.from(state.phases.plotOutline.outline.items.values());
          this.plotOutlineSummary = state.phases.plotOutline.draftSummary;
        }
      });
  }

  private loadExistingDrafts(): void {
    // Load existing draft versions from story data
    if (this.story.chapterCompose?.phases.chapterDetailer) {
      const phase = this.story.chapterCompose.phases.chapterDetailer;
      if (phase.chapterDraft.content) {
        // Create initial version from existing draft
        const initialVersion: ChapterDraftVersion = {
          id: 'v1',
          name: 'v1',
          content: phase.chapterDraft.content,
          title: phase.chapterDraft.title,
          wordCount: phase.chapterDraft.wordCount,
          created: new Date(),
          sourceType: 'initial',
          incorporatedFeedback: [],
          isActive: true
        };
        this.draftVersions = [initialVersion];
        this.currentVersionId = 'v1';
        this.nextVersionNumber = 2;
      }
    }

    // If no existing drafts, prepare for initial generation
    if (this.draftVersions.length === 0) {
      this.prepareInitialGeneration();
    }
  }

  private prepareInitialGeneration(): void {
    // Set up for initial chapter generation from plot outline
    this.completionCriteria.hasInitialDraft = false;
  }

  // Plot outline display methods
  toggleOutlineDetails(): void {
    this.showOutlineDetails = !this.showOutlineDetails;
  }

  getOutlineItemsCount(): number {
    return this.plotOutlineItems.length;
  }

  // Draft version management methods
  getCurrentVersion(): ChapterDraftVersion | null {
    return this.draftVersions.find(v => v.id === this.currentVersionId) || null;
  }

  switchToVersion(versionId: string): void {
    const version = this.draftVersions.find(v => v.id === versionId);
    if (version) {
      // Update active status
      this.draftVersions.forEach(v => v.isActive = false);
      version.isActive = true;
      this.currentVersionId = versionId;
      this.chapterUpdated.emit(version);
      this.validatePhaseCompletion();
    }
  }

  createNewVersion(content: string, title: string, sourceType: ChapterDraftVersion['sourceType'], sourceMessageId?: string): string {
    const versionId = `v${this.nextVersionNumber}`;
    const wordCount = this.calculateWordCount(content);
    
    const newVersion: ChapterDraftVersion = {
      id: versionId,
      name: versionId,
      content,
      title,
      wordCount,
      created: new Date(),
      sourceType,
      sourceMessageId,
      incorporatedFeedback: [],
      isActive: false
    };

    this.draftVersions.push(newVersion);
    this.nextVersionNumber++;
    
    return versionId;
  }

  deleteVersion(versionId: string): void {
    if (this.draftVersions.length <= 1) {
      this.toastService.showError('Cannot delete the only remaining version');
      return;
    }

    const index = this.draftVersions.findIndex(v => v.id === versionId);
    if (index !== -1) {
      this.draftVersions.splice(index, 1);
      
      // If we deleted the current version, switch to the first available
      if (versionId === this.currentVersionId && this.draftVersions.length > 0) {
        this.switchToVersion(this.draftVersions[0].id);
      }
    }
  }

  // Word count and target management
  calculateWordCount(text: string): number {
    return this.tokenCountingService.countWords(text);
  }

  getCurrentWordCount(): number {
    const currentVersion = this.getCurrentVersion();
    return currentVersion ? currentVersion.wordCount : 0;
  }

  getWordCountProgress(): number {
    const current = this.getCurrentWordCount();
    return this.targetWordCount > 0 ? Math.min((current / this.targetWordCount) * 100, 100) : 0;
  }

  updateTargetWordCount(target: number): void {
    this.targetWordCount = Math.max(100, target);
    this.validatePhaseCompletion();
  }

  toggleWordCountSettings(): void {
    this.showWordCountSettings = !this.showWordCountSettings;
  }

  // Chapter generation methods
  async generateInitialChapter(): Promise<void> {
    if (this.isGeneratingChapter) return;

    this.isGeneratingChapter = true;
    try {
      // Use plot outline to generate initial chapter
      const outlineItems = this.plotOutlineItems.map(item => ({
        title: item.title,
        description: item.description
      }));
      
      const response = await this.generationService.generateChapterFromOutline(
        this.story,
        outlineItems,
        this.chapterNumber
      ).toPromise();
      
      if (response?.chapterText) {
        const versionId = this.createNewVersion(
          response.chapterText,
          `Chapter ${this.chapterNumber}`,
          'initial'
        );
        this.switchToVersion(versionId);
        this.completionCriteria.hasInitialDraft = true;
        this.toastService.showSuccess('Initial chapter generated successfully');
      }
    } catch (error) {
      console.error('Error generating initial chapter:', error);
      this.toastService.showError('Failed to generate initial chapter');
    } finally {
      this.isGeneratingChapter = false;
    }
  }

  async continueWriting(): Promise<void> {
    if (this.isContinuingChapter) return;

    const currentVersion = this.getCurrentVersion();
    if (!currentVersion) {
      this.toastService.showError('No current chapter version to continue');
      return;
    }

    this.isContinuingChapter = true;
    try {
      const response = await this.generationService.continueChapter(
        this.story,
        currentVersion.content
      ).toPromise();

      if (response?.modifiedChapter) {
        const versionId = this.createNewVersion(
          response.modifiedChapter,
          currentVersion.title,
          'continuation'
        );
        this.switchToVersion(versionId);
        this.toastService.showSuccess('Chapter continued successfully');
      }
    } catch (error) {
      console.error('Error continuing chapter:', error);
      this.toastService.showError('Failed to continue chapter');
    } finally {
      this.isContinuingChapter = false;
    }
  }

  // Chat interface event handlers
  onMessageSent(message: ChatMessage): void {
    // Handle user messages for chapter development
    this.processChapterDevelopmentMessage(message);
  }

  onMessageAction(event: MessageActionEvent): void {
    // Handle message actions like editing, branching, etc.
    console.log('Message action:', event);
  }

  private async processChapterDevelopmentMessage(message: ChatMessage): Promise<void> {
    if (message.type !== 'user') return;

    try {
      const currentVersion = this.getCurrentVersion();
      const currentContent = currentVersion?.content || '';
      
      const response = await this.generationService.modifyChapter(
        this.story,
        currentContent,
        message.content
      ).toPromise();

      if (response?.modifiedChapter) {
        const versionId = this.createNewVersion(
          response.modifiedChapter,
          currentVersion?.title || `Chapter ${this.chapterNumber}`,
          'chat',
          message.id
        );
        this.switchToVersion(versionId);
      }
    } catch (error) {
      console.error('Error processing chapter development message:', error);
      this.toastService.showError('Failed to process chapter development request');
    }
  }

  // Feedback integration methods
  onFeedbackSelectionChanged(event: FeedbackSelectionEvent): void {
    this.selectedFeedbackItems = event.selectedItems;
  }

  onAddFeedbackToChat(event: AddToChatEvent): void {
    // Incorporate selected feedback into chat
    this.incorporateSelectedFeedback(event.selectedFeedback, event.userComment);
  }

  private async incorporateSelectedFeedback(feedbackItems: EnhancedFeedbackItem[], userComment?: string): Promise<void> {
    if (this.isIncorporatingFeedback) return;

    this.isIncorporatingFeedback = true;
    try {
      const currentVersion = this.getCurrentVersion();
      if (!currentVersion) {
        this.toastService.showError('No current chapter version to modify');
        return;
      }

      // Prepare feedback items for the service
      const feedbackForService = feedbackItems.map(item => ({
        source: item.source,
        content: item.content,
        type: item.type
      }));

      const response = await this.generationService.regenerateChapterWithFeedback(
        this.story,
        currentVersion.content,
        feedbackForService,
        userComment
      ).toPromise();

      if (response?.modifiedChapter) {
        const versionId = this.createNewVersion(
          response.modifiedChapter,
          currentVersion.title,
          'feedback'
        );
        
        // Mark feedback as incorporated
        const newVersion = this.draftVersions.find(v => v.id === versionId);
        if (newVersion) {
          newVersion.incorporatedFeedback = feedbackItems.map(item => item.id);
        }
        
        this.switchToVersion(versionId);
        this.completionCriteria.hasFeedbackIncorporated = true;
        this.toastService.showSuccess('Feedback incorporated successfully');
      }
    } catch (error) {
      console.error('Error incorporating feedback:', error);
      this.toastService.showError('Failed to incorporate feedback');
    } finally {
      this.isIncorporatingFeedback = false;
    }
  }

  // Phase completion validation
  private validatePhaseCompletion(): void {
    const currentVersion = this.getCurrentVersion();
    
    this.completionCriteria.hasInitialDraft = this.draftVersions.length > 0;
    this.completionCriteria.meetsMinWordCount = currentVersion ? 
      currentVersion.wordCount >= Math.min(this.targetWordCount * 0.8, 1000) : false;
    this.completionCriteria.hasFeedbackIncorporated = this.draftVersions.some(v => 
      v.incorporatedFeedback.length > 0
    );
    this.completionCriteria.hasReviewedContent = currentVersion ? 
      currentVersion.content.length > 500 : false;

    // Update phase state service
    this.updatePhaseState();
  }

  private updatePhaseState(): void {
    // Update the phase state with current progress
    // Implementation would update PhaseStateService with validation results
  }

  canAdvancePhase(): boolean {
    return Object.values(this.completionCriteria).every(criteria => criteria);
  }

  getCompletionPercentage(): number {
    const completedCriteria = Object.values(this.completionCriteria).filter(c => c).length;
    const totalCriteria = Object.keys(this.completionCriteria).length;
    return Math.round((completedCriteria / totalCriteria) * 100);
  }

  // UI helper methods
  toggleChat(): void {
    this.showChat = !this.showChat;
  }

  toggleFeedbackSidebar(): void {
    this.showFeedbackSidebar = !this.showFeedbackSidebar;
  }

  getVersionDisplayName(version: ChapterDraftVersion): string {
    const sourceIcons = {
      initial: '🌟',
      chat: '💬',
      feedback: '📝',
      continuation: '➕'
    };
    return `${sourceIcons[version.sourceType]} ${version.name}`;
  }

  formatWordCount(count: number): string {
    return count.toLocaleString();
  }

  formatDate(date: Date): string {
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
}
