import { Component, Input, Output, EventEmitter, OnInit, OnDestroy, ChangeDetectorRef, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DragDropModule, CdkDragDrop, moveItemInArray } from '@angular/cdk/drag-drop';
import { Subject } from 'rxjs';

import { 
  Story, 
  OutlineItem, 
  ChatMessage
} from '../../models/story.model';
import { ChatInterfaceComponent, ChatInterfaceConfig, MessageActionEvent } from '../chat-interface/chat-interface.component';
import { GenerationService } from '../../services/generation.service';
import { ArchiveService, RAGResponse } from '../../services/archive.service';
import { ConversationService } from '../../services/conversation.service';
import { PhaseStateService } from '../../services/phase-state.service';
import { StoryService } from '../../services/story.service';
import { ToastService } from '../../services/toast.service';
import { NewlineToBrPipe } from '../../pipes/newline-to-br.pipe';

interface DraftOutlineItem {
  id: string;
  title: string;
  description: string;
  order: number;
  sourceMessageId?: string; // Link to chat message that contributed this item
  isEditing?: boolean;
}

@Component({
  selector: 'app-plot-outline-phase',
  standalone: true,
  imports: [
    CommonModule, 
    FormsModule, 
    DragDropModule, 
    ChatInterfaceComponent,
    NewlineToBrPipe
  ],
  templateUrl: './plot-outline-phase.component.html',
  styleUrls: ['./plot-outline-phase.component.scss']
})
export class PlotOutlinePhaseComponent implements OnInit, OnDestroy {
  @Input() story!: Story;
  @Input() chapterNumber = 1;
  @Output() phaseCompleted = new EventEmitter<void>();
  @Output() outlineUpdated = new EventEmitter<DraftOutlineItem[]>();

  // Basic outline (legacy functionality)
  basicOutline = '';
  
  // Draft outline builder
  draftOutlineItems: DraftOutlineItem[] = [];
  nextItemId = 1;
  
  // Chat interface configuration
  chatConfig: ChatInterfaceConfig = {
    phase: 'plot-outline',
    storyId: '',
    chapterNumber: 1,
    enableBranching: true,
    placeholder: 'Ask for help developing your plot outline...',
    showTimestamps: true,
    allowMessageEditing: true
  };
  
  // UI state
  showChat = false;
  isGeneratingFleshOut = false;
  isResearching = false;
  editingItemId: string | null = null;
  editingTitle = '';
  editingDescription = '';
  
  // Research state
  showResearchSidebar = false;
  researchData: RAGResponse | null = null;
  researchError: string | null = null;
  
  private destroy$ = new Subject<void>();
  private generationService = inject(GenerationService);
  private archiveService = inject(ArchiveService);
  private conversationService = inject(ConversationService);
  private phaseStateService = inject(PhaseStateService);
  private storyService = inject(StoryService);
  private toastService = inject(ToastService);
  private cdr = inject(ChangeDetectorRef);

  ngOnInit(): void {
    this.initializeComponent();
    this.setupChatConfig();
    this.loadExistingOutline();
    this.validatePhaseCompletion();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private initializeComponent(): void {
    // Initialize basic outline from legacy plot point
    if (this.story?.chapterCreation?.plotPoint) {
      this.basicOutline = this.story.chapterCreation.plotPoint;
    }
    
    // Load existing draft outline if available
    if (this.story?.chapterCompose?.phases?.plotOutline?.outline?.items) {
      this.loadDraftOutlineFromStory();
    }
  }

  private setupChatConfig(): void {
    this.chatConfig = {
      ...this.chatConfig,
      storyId: this.story.id,
      chapterNumber: this.chapterNumber
    };
  }

  private loadExistingOutline(): void {
    // Load from chapter compose state if available
    const plotOutlinePhase = this.story?.chapterCompose?.phases?.plotOutline;
    if (plotOutlinePhase?.outline?.items) {
      // Convert from Map to array format
      this.draftOutlineItems = Array.from(plotOutlinePhase.outline.items.values())
        .map(item => ({
          id: item.id,
          title: item.title,
          description: item.description,
          order: item.order,
          sourceMessageId: item.metadata?.sourceMessageId
        }))
        .sort((a, b) => a.order - b.order);
    }
  }

  private loadDraftOutlineFromStory(): void {
    const plotOutlinePhase = this.story?.chapterCompose?.phases?.plotOutline;
    if (plotOutlinePhase?.outline?.items) {
      const items = Array.from(plotOutlinePhase.outline.items.values());
      this.draftOutlineItems = items.map(item => ({
        id: item.id,
        title: item.title,
        description: item.description,
        order: item.order,
        sourceMessageId: item.metadata?.sourceMessageId
      })).sort((a, b) => a.order - b.order);
      
      this.nextItemId = Math.max(...this.draftOutlineItems.map(item => parseInt(item.id.split('-')[1]) || 0)) + 1;
    }
  }

  // Basic outline functionality (preserving existing behavior)
  onBasicOutlineChange(): void {
    // Update the legacy plot point for backward compatibility
    if (this.story?.chapterCreation) {
      this.story.chapterCreation.plotPoint = this.basicOutline;
      this.saveStory();
    }
    this.validatePhaseCompletion();
  }

  async aiFleshOutPlotPoint(): Promise<void> {
    if (!this.basicOutline.trim()) {
      this.toastService.showError('Please enter a plot point to flesh out');
      return;
    }

    this.isGeneratingFleshOut = true;
    
    try {
      const response = await this.generationService.fleshOut(
        this.story,
        this.basicOutline,
        'plot outline development'
      ).toPromise();

      if (response?.fleshedOutText) {
        // Add the AI response to the chat
        this.conversationService.sendMessage(
          `Please help me flesh out this plot point: "${this.basicOutline}"`,
          'user'
        );
        
        this.conversationService.sendMessage(
          response.fleshedOutText,
          'assistant'
        );
        
        // Show the chat interface
        this.showChat = true;
        
        this.toastService.showSuccess('Plot point fleshed out! Check the chat for details.');
      }
    } catch (error) {
      console.error('Error fleshing out plot point:', error);
      this.toastService.showError('Failed to flesh out plot point. Please try again.');
    } finally {
      this.isGeneratingFleshOut = false;
    }
  }

  async researchPlotPoint(): Promise<void> {
    if (!this.basicOutline.trim()) {
      this.toastService.showError('Please enter a plot point to research');
      return;
    }

    this.isResearching = true;
    this.researchError = null;
    
    try {
      const response = await this.archiveService.searchArchive(this.basicOutline).toPromise();
      
      if (response) {
        this.researchData = response;
        this.showResearchSidebar = true;
        
        // Add research results to chat
        this.conversationService.sendMessage(
          `Research archive for: "${this.basicOutline}"`,
          'user'
        );
        
        const researchSummary = this.formatResearchForChat(response);
        this.conversationService.sendMessage(
          researchSummary,
          'assistant'
        );
        
        this.showChat = true;
        this.toastService.showSuccess('Archive research completed! Check the chat and sidebar for results.');
      }
    } catch (error) {
      console.error('Error researching plot point:', error);
      this.researchError = 'Failed to research archive. Please try again.';
      this.toastService.showError('Failed to research archive. Please try again.');
    } finally {
      this.isResearching = false;
    }
  }

  private formatResearchForChat(research: RAGResponse): string {
    let summary = `📚 **Archive Research Results**\n\n${research.response}\n\n`;
    
    if (research.sources && research.sources.length > 0) {
      summary += `**Sources found (${research.sources.length}):**\n`;
      research.sources.forEach((source, index) => {
        const fileName = source.metadata?.file_name || 'Unknown file';
        const similarity = (source.similarity_score * 100).toFixed(1);
        summary += `${index + 1}. ${fileName} (${similarity}% match)\n`;
      });
    }
    
    return summary;
  }

  // Chat interface handlers
  onMessageSent(message: ChatMessage): void {
    // Handle user messages sent through chat
    console.log('Message sent:', message);
  }

  onMessageAction(event: MessageActionEvent): void {
    if (event.action === 'edit') {
      // Handle message editing
      console.log('Edit message:', event.message, event.data);
    }
  }

  onBranchChanged(branchId: string): void {
    console.log('Branch changed:', branchId);
  }

  onConversationCleared(): void {
    console.log('Conversation cleared');
  }

  // Draft outline builder functionality
  addToDraft(content: string, sourceMessageId?: string): void {
    const newItem: DraftOutlineItem = {
      id: `outline-${this.nextItemId++}`,
      title: this.extractTitleFromContent(content),
      description: content,
      order: this.draftOutlineItems.length,
      sourceMessageId
    };
    
    this.draftOutlineItems.push(newItem);
    this.saveDraftOutline();
    this.validatePhaseCompletion();
    this.toastService.showSuccess('Added to draft outline!');
  }

  private extractTitleFromContent(content: string): string {
    // Extract a title from the content (first line or first sentence)
    const firstLine = content.split('\n')[0];
    const firstSentence = content.split('.')[0];
    
    // Use the shorter of the two, up to 50 characters
    const title = firstLine.length <= firstSentence.length ? firstLine : firstSentence;
    return title.length > 50 ? title.substring(0, 47) + '...' : title;
  }

  startEditingItem(item: DraftOutlineItem): void {
    this.editingItemId = item.id;
    this.editingTitle = item.title;
    this.editingDescription = item.description;
    item.isEditing = true;
  }

  saveItemEdit(): void {
    if (!this.editingItemId) return;
    
    const item = this.draftOutlineItems.find(i => i.id === this.editingItemId);
    if (item) {
      item.title = this.editingTitle;
      item.description = this.editingDescription;
      item.isEditing = false;
      
      this.saveDraftOutline();
      this.validatePhaseCompletion();
    }
    
    this.cancelItemEdit();
  }

  cancelItemEdit(): void {
    if (this.editingItemId) {
      const item = this.draftOutlineItems.find(i => i.id === this.editingItemId);
      if (item) {
        item.isEditing = false;
      }
    }
    
    this.editingItemId = null;
    this.editingTitle = '';
    this.editingDescription = '';
  }

  removeItem(itemId: string): void {
    const index = this.draftOutlineItems.findIndex(i => i.id === itemId);
    if (index > -1) {
      this.draftOutlineItems.splice(index, 1);
      
      // Update order for remaining items
      this.draftOutlineItems.forEach((item, idx) => {
        item.order = idx;
      });
      
      this.saveDraftOutline();
      this.validatePhaseCompletion();
      this.toastService.showSuccess('Outline item removed');
    }
  }

  // Drag and drop functionality
  onDrop(event: CdkDragDrop<DraftOutlineItem[]>): void {
    if (event.previousIndex !== event.currentIndex) {
      moveItemInArray(this.draftOutlineItems, event.previousIndex, event.currentIndex);
      
      // Update order values
      this.draftOutlineItems.forEach((item, index) => {
        item.order = index;
      });
      
      this.saveDraftOutline();
      this.toastService.showSuccess('Outline reordered');
    }
  }

  // Phase completion validation
  private validatePhaseCompletion(): void {
    const hasBasicOutline = this.basicOutline.trim().length > 0;
    const hasDraftItems = this.draftOutlineItems.length >= 3; // Minimum 3 items
    const hasDetailedItems = this.draftOutlineItems.every(item => 
      item.title.trim().length > 0 && item.description.trim().length > 20
    );
    
    const isComplete = hasBasicOutline && hasDraftItems && hasDetailedItems;
    
    // Update phase state service
    this.phaseStateService.updatePhaseValidation('plot-outline', {
      canAdvance: isComplete,
      canRevert: false,
      requirements: this.getRequirements(hasBasicOutline, hasDraftItems, hasDetailedItems),
      validationErrors: this.getValidationErrors(hasBasicOutline, hasDraftItems, hasDetailedItems)
    });
    
    if (isComplete) {
      this.phaseCompleted.emit();
    }
  }

  private getRequirements(hasBasicOutline: boolean, hasDraftItems: boolean, hasDetailedItems: boolean): string[] {
    const requirements: string[] = [];
    
    if (!hasBasicOutline) {
      requirements.push('Basic plot outline');
    }
    if (!hasDraftItems) {
      requirements.push('At least 3 draft outline items');
    }
    if (!hasDetailedItems) {
      requirements.push('All outline items must have detailed descriptions (20+ characters)');
    }
    
    return requirements;
  }

  /**
   * Check if all draft outline items have detailed descriptions
   */
  hasDetailedDescriptions(): boolean {
    return this.draftOutlineItems.every(item => 
      item.title.trim().length > 0 && item.description.trim().length >= 20
    );
  }

  private getValidationErrors(hasBasicOutline: boolean, hasDraftItems: boolean, hasDetailedItems: boolean): string[] {
    const errors: string[] = [];
    
    if (!hasBasicOutline) {
      errors.push('Please enter a basic plot outline');
    }
    if (!hasDraftItems) {
      errors.push(`Need ${3 - this.draftOutlineItems.length} more outline items`);
    }
    if (!hasDetailedItems) {
      const shortItems = this.draftOutlineItems.filter(item => 
        item.title.trim().length === 0 || item.description.trim().length < 20
      ).length;
      errors.push(`${shortItems} outline items need more detail`);
    }
    
    return errors;
  }

  // Data persistence
  private saveDraftOutline(): void {
    // Ensure chapter compose state exists
    if (!this.story.chapterCompose) {
      this.initializeChapterComposeState();
    }
    
    // Update the plot outline phase
    const plotOutlinePhase = this.story.chapterCompose!.phases.plotOutline;
    plotOutlinePhase.outline.items = new Map();
    
    this.draftOutlineItems.forEach(item => {
      const outlineItem: OutlineItem = {
        id: item.id,
        type: 'plot-point',
        title: item.title,
        description: item.description,
        order: item.order,
        status: 'draft',
        metadata: {
          created: new Date(),
          lastModified: new Date(),
          sourceMessageId: item.sourceMessageId
        }
      };
      
      plotOutlinePhase.outline.items.set(item.id, outlineItem);
    });
    
    plotOutlinePhase.outline.structure = this.draftOutlineItems.map(item => item.id);
    plotOutlinePhase.progress.totalItems = this.draftOutlineItems.length;
    plotOutlinePhase.progress.completedItems = this.draftOutlineItems.filter(item => 
      item.title.trim().length > 0 && item.description.trim().length > 20
    ).length;
    plotOutlinePhase.progress.lastActivity = new Date();
    
    this.saveStory();
    this.outlineUpdated.emit(this.draftOutlineItems);
  }

  private initializeChapterComposeState(): void {
    const now = new Date();
    
    this.story.chapterCompose = {
      currentPhase: 'plot-outline',
      phases: {
        plotOutline: {
          conversation: {
            id: `plot-outline-${this.story.id}`,
            messages: [],
            currentBranchId: 'main',
            branches: new Map([['main', {
              id: 'main',
              name: 'Main',
              parentMessageId: '',
              messageIds: [],
              isActive: true,
              metadata: { created: now }
            }]]),
            metadata: {
              created: now,
              lastModified: now,
              phase: 'plot-outline'
            }
          },
          outline: {
            items: new Map(),
            structure: [],
            currentFocus: undefined
          },
          draftSummary: '',
          status: 'active',
          progress: {
            completedItems: 0,
            totalItems: 0,
            lastActivity: now
          }
        },
        chapterDetailer: {
          conversation: {
            id: `chapter-detailer-${this.story.id}`,
            messages: [],
            currentBranchId: 'main',
            branches: new Map([['main', {
              id: 'main',
              name: 'Main',
              parentMessageId: '',
              messageIds: [],
              isActive: true,
              metadata: { created: now }
            }]]),
            metadata: {
              created: now,
              lastModified: now,
              phase: 'chapter-detailer'
            }
          },
          chapterDraft: {
            content: '',
            title: '',
            plotPoint: '',
            wordCount: 0,
            status: 'drafting'
          },
          feedbackIntegration: {
            pendingFeedback: [],
            incorporatedFeedback: [],
            feedbackRequests: new Map()
          },
          status: 'active',
          progress: {
            feedbackIncorporated: 0,
            totalFeedbackItems: 0,
            lastActivity: now
          }
        },
        finalEdit: {
          conversation: {
            id: `final-edit-${this.story.id}`,
            messages: [],
            currentBranchId: 'main',
            branches: new Map([['main', {
              id: 'main',
              name: 'Main',
              parentMessageId: '',
              messageIds: [],
              isActive: true,
              metadata: { created: now }
            }]]),
            metadata: {
              created: now,
              lastModified: now,
              phase: 'final-edit'
            }
          },
          finalChapter: {
            content: '',
            title: '',
            wordCount: 0,
            version: 1
          },
          reviewSelection: {
            availableReviews: [],
            selectedReviews: [],
            appliedReviews: []
          },
          status: 'active',
          progress: {
            reviewsApplied: 0,
            totalReviews: 0,
            lastActivity: now
          }
        }
      },
      sharedContext: {
        chapterNumber: this.chapterNumber,
        targetWordCount: undefined,
        genre: undefined,
        tone: undefined,
        pov: undefined
      },
      navigation: {
        phaseHistory: ['plot-outline'],
        canGoBack: false,
        canGoForward: false,
        branchNavigation: {
          currentBranchId: 'main',
          availableBranches: ['main'],
          branchHistory: [],
          canNavigateBack: false,
          canNavigateForward: false
        }
      },
      overallProgress: {
        currentStep: 1,
        totalSteps: 3,
        phaseCompletionStatus: {
          'plot-outline': false,
          'chapter-detailer': false,
          'final-edit': false
        },
        estimatedTimeRemaining: undefined
      },
      metadata: {
        created: now,
        lastModified: now,
        version: '1.0.0',
        migrationSource: 'manual'
      }
    };
  }

  private saveStory(): void {
    if (this.story) {
      this.story.metadata.lastModified = new Date();
      this.storyService.saveStory(this.story);
    }
  }

  // UI helpers
  toggleChat(): void {
    this.showChat = !this.showChat;
  }

  closeResearchSidebar(): void {
    this.showResearchSidebar = false;
    this.researchData = null;
    this.researchError = null;
  }

  getCompletionPercentage(): number {
    if (this.draftOutlineItems.length === 0) return 0;
    
    const completedItems = this.draftOutlineItems.filter(item => 
      item.title.trim().length > 0 && item.description.trim().length > 20
    ).length;
    
    return Math.round((completedItems / Math.max(this.draftOutlineItems.length, 3)) * 100);
  }

  canAdvancePhase(): boolean {
    const hasBasicOutline = this.basicOutline.trim().length > 0;
    const hasDraftItems = this.draftOutlineItems.length >= 3;
    const hasDetailedItems = this.draftOutlineItems.every(item => 
      item.title.trim().length > 0 && item.description.trim().length > 20
    );
    
    return hasBasicOutline && hasDraftItems && hasDetailedItems;
  }

  // Track by function for ngFor
  trackByItemId(index: number, item: DraftOutlineItem): string {
    return item.id;
  }
}
