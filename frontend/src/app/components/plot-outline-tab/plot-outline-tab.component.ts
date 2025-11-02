import { Component, Input, Output, EventEmitter, OnInit, ViewChild, ElementRef, AfterViewChecked, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { firstValueFrom } from 'rxjs';
import { Story, ChatMessage, Rater, PlotOutlineFeedback } from '../../models/story.model';
import { GenerationService } from '../../services/generation.service';
import { LoadingService } from '../../services/loading.service';
import { ToastService } from '../../services/toast.service';
import { PlotOutlineService } from '../../services/plot-outline.service';

@Component({
  selector: 'app-plot-outline-tab',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './plot-outline-tab.component.html',
  styleUrl: './plot-outline-tab.component.scss'
})
export class PlotOutlineTabComponent implements OnInit, AfterViewChecked {
  @Input() story!: Story;
  @Input() disabled = false;
  @Output() outlineUpdated = new EventEmitter<string>();
  @Output() outlineApproved = new EventEmitter<void>();

  @ViewChild('chatMessages') private chatMessagesContainer!: ElementRef;

  // Component state
  showChat = true;
  chatInput = '';
  isGeneratingAI = false;
  isResearching = false;

  // Chat state
  isChatGenerating = false;
  chatError: string | null = null;
  private shouldScrollToBottom = false;

  // Rater feedback state
  generatingFeedback = new Set<string>();
  feedbackError: string | null = null;

  // Dependency injection
  private generationService = inject(GenerationService);
  private loadingService = inject(LoadingService);
  private toastService = inject(ToastService);
  private plotOutlineService = inject(PlotOutlineService);

  ngOnInit(): void {
    // Initialize component
    if (!this.story?.plotOutline) {
      console.warn('Plot outline not initialized');
    }
  }

  onOutlineChange(): void {
    if (this.story.plotOutline) {
      this.story.plotOutline.metadata.lastModified = new Date();
      this.outlineUpdated.emit(this.story.plotOutline.content);
    }
  }

  getStatusDisplay(): string {
    if (!this.story?.plotOutline) return 'Not initialized';
    
    switch (this.story.plotOutline.status) {
      case 'draft': return '⏳ Draft';
      case 'under_review': return '👀 Under Review';
      case 'approved': return '✅ Approved';
      case 'needs_revision': return '🔄 Needs Revision';
      default: return 'Unknown';
    }
  }

  // Placeholder methods for future implementation
  aiExpandOutline(): void {
    console.log('AI expand outline - to be implemented');
    this.isGeneratingAI = true;
    // Simulate AI processing
    setTimeout(() => {
      this.isGeneratingAI = false;
    }, 2000);
  }

  researchOutline(): void {
    console.log('Research outline - to be implemented');
    this.isResearching = true;
    // Simulate research processing
    setTimeout(() => {
      this.isResearching = false;
    }, 1500);
  }

  saveOutline(): void {
    console.log('Save outline - to be implemented');
    if (this.story?.plotOutline) {
      this.story.plotOutline.metadata.lastModified = new Date();
      this.outlineUpdated.emit(this.story.plotOutline.content);
    }
  }

  resetOutline(): void {
    console.log('Reset outline - to be implemented');
    if (this.story?.plotOutline) {
      this.story.plotOutline.content = '';
      this.story.plotOutline.status = 'draft';
      this.story.plotOutline.metadata.lastModified = new Date();
      this.outlineUpdated.emit(this.story.plotOutline.content);
    }
  }

  async sendChatMessage(): Promise<void> {
    if (!this.chatInput.trim() || this.isChatGenerating) return;

    const userMessage: ChatMessage = {
      id: this.generateMessageId(),
      type: 'user',
      content: this.chatInput.trim(),
      timestamp: new Date()
    };

    // Add user message to chat history
    this.story.plotOutline.chatHistory.push(userMessage);
    
    const userInput = this.chatInput;
    this.chatInput = '';
    this.isChatGenerating = true;
    this.chatError = null;
    this.shouldScrollToBottom = true;

    try {
      // Generate AI response
      const aiResponse = await this.generateAIResponse(userInput);
      
      const aiMessage: ChatMessage = {
        id: this.generateMessageId(),
        type: 'assistant',
        content: aiResponse,
        timestamp: new Date()
      };

      this.story.plotOutline.chatHistory.push(aiMessage);
      this.outlineUpdated.emit(this.story.plotOutline.content);
      this.shouldScrollToBottom = true;
      
    } catch (error) {
      this.chatError = 'Failed to generate AI response. Please try again.';
      this.toastService.showError('Chat error: ' + error);
    } finally {
      this.isChatGenerating = false;
    }
  }

  private async generateAIResponse(userInput: string): Promise<string> {
    return new Promise((resolve, reject) => {
      this.generationService.generatePlotOutlineResponse(
        this.story,
        userInput,
        this.story.plotOutline.chatHistory
      ).subscribe({
        next: (response) => resolve(response),
        error: (error) => reject(error)
      });
    });
  }

  private generateMessageId(): string {
    return Date.now().toString() + Math.random().toString(36).substr(2, 9);
  }

  clearChat(): void {
    if (confirm('Are you sure you want to clear the chat history?')) {
      this.story.plotOutline.chatHistory = [];
      this.outlineUpdated.emit(this.story.plotOutline.content);
      this.toastService.showInfo('Chat history cleared');
    }
  }

  ngAfterViewChecked(): void {
    if (this.shouldScrollToBottom) {
      this.scrollToBottom();
      this.shouldScrollToBottom = false;
    }
  }

  private scrollToBottom(): void {
    try {
      if (this.chatMessagesContainer) {
        const element = this.chatMessagesContainer.nativeElement;
        element.scrollTop = element.scrollHeight;
      }
    } catch (err) {
      console.warn('Could not scroll chat to bottom:', err);
    }
  }

  // Quick action methods
  async suggestPlotStructure(): Promise<void> {
    this.chatInput = 'Can you suggest a plot structure for my story based on the current outline and characters?';
    await this.sendChatMessage();
  }

  async identifyPlotHoles(): Promise<void> {
    this.chatInput = 'Please analyze my plot outline and identify any potential plot holes or inconsistencies.';
    await this.sendChatMessage();
  }

  async generateCharacterArcs(): Promise<void> {
    this.chatInput = 'Based on my characters and plot outline, can you suggest character development arcs for each main character?';
    await this.sendChatMessage();
  }

  async checkPacing(): Promise<void> {
    this.chatInput = 'Please review the pacing of my plot outline. Are there any areas that might feel rushed or too slow?';
    await this.sendChatMessage();
  }

  // Rater feedback methods
  async requestAllRaterFeedback(): Promise<void> {
    if (!this.story.plotOutline.content.trim()) {
      this.toastService.showWarning('Please write a plot outline before requesting feedback');
      return;
    }

    const enabledRaters = this.getEnabledRaters();
    if (enabledRaters.length === 0) {
      this.toastService.showWarning('No enabled raters found. Please enable raters in the Raters tab.');
      return;
    }

    // Set all raters to generating state
    const raterFeedbackMap = this.ensureRaterFeedbackMap();
    enabledRaters.forEach(rater => {
      this.generatingFeedback.add(rater.id);
      raterFeedbackMap.set(rater.id, {
        raterId: rater.id,
        raterName: rater.name,
        feedback: '',
        status: 'generating',
        timestamp: new Date()
      });
    });

    this.story.plotOutline.metadata.lastFeedbackRequest = new Date();
    this.outlineUpdated.emit(this.story.plotOutline.content);

    try {
      const feedbackResults = await firstValueFrom(this.plotOutlineService.requestAllRaterFeedback(this.story.id));
      
      if (feedbackResults) {
        const raterFeedbackMap = this.ensureRaterFeedbackMap();
        feedbackResults.forEach(feedback => {
          raterFeedbackMap.set(feedback.raterId, feedback);
          this.generatingFeedback.delete(feedback.raterId);
        });
      }

      this.updateOutlineStatus();
      this.outlineUpdated.emit(this.story.plotOutline.content);
      this.toastService.showSuccess('Rater feedback received!');

    } catch (error) {
      this.feedbackError = 'Failed to get feedback from some raters';
      this.toastService.showError('Error getting rater feedback: ' + error);
      
      // Clear generating state for all raters
      this.generatingFeedback.clear();
    }
  }

  async requestRaterFeedback(raterId: string): Promise<void> {
    if (!this.story.plotOutline.content.trim()) {
      this.toastService.showWarning('Please write a plot outline before requesting feedback');
      return;
    }

    this.generatingFeedback.add(raterId);
    const rater = this.story.raters.get(raterId);
    
    if (!rater) {
      this.toastService.showError('Rater not found');
      return;
    }

    // Set generating state
    const raterFeedbackMap = this.ensureRaterFeedbackMap();
    raterFeedbackMap.set(raterId, {
      raterId: raterId,
      raterName: rater.name,
      feedback: '',
      status: 'generating',
      timestamp: new Date()
    });

    this.outlineUpdated.emit(this.story.plotOutline.content);

    try {
      const feedback = await firstValueFrom(this.plotOutlineService.requestPlotOutlineFeedback(
        this.story.id, 
        raterId, 
        this.story.plotOutline.content
      ));

      if (feedback) {
        const raterFeedbackMap = this.ensureRaterFeedbackMap();
        raterFeedbackMap.set(raterId, feedback);
      }
      this.generatingFeedback.delete(raterId);
      this.updateOutlineStatus();
      this.outlineUpdated.emit(this.story.plotOutline.content);
      this.toastService.showSuccess(`Feedback received from ${rater.name}!`);

    } catch {
      this.generatingFeedback.delete(raterId);
      const raterFeedbackMap = this.ensureRaterFeedbackMap();
      raterFeedbackMap.set(raterId, {
        raterId: raterId,
        raterName: rater.name,
        feedback: '',
        status: 'error',
        timestamp: new Date()
      });
      this.toastService.showError(`Error getting feedback from ${rater.name}`);
    }
  }

  regenerateAllFeedback(): void {
    if (confirm('Are you sure you want to regenerate all rater feedback? This will replace existing feedback.')) {
      this.clearAllFeedback();
      this.requestAllRaterFeedback();
    }
  }

  clearAllFeedback(): void {
    if (confirm('Are you sure you want to clear all rater feedback?')) {
      const raterFeedbackMap = this.ensureRaterFeedbackMap();
      raterFeedbackMap.clear();
      this.generatingFeedback.clear();
      this.story.plotOutline.status = 'draft';
      this.outlineUpdated.emit(this.story.plotOutline.content);
      this.toastService.showInfo('All rater feedback cleared');
    }
  }

  acceptFeedback(raterId: string): void {
    const raterFeedbackMap = this.ensureRaterFeedbackMap();
    const feedback = raterFeedbackMap.get(raterId);
    if (feedback) {
      feedback.userResponse = 'accepted';
      this.updateOutlineStatus();
      this.outlineUpdated.emit(this.story.plotOutline.content);
    }
  }

  requestRevision(raterId: string): void {
    const raterFeedbackMap = this.ensureRaterFeedbackMap();
    const feedback = raterFeedbackMap.get(raterId);
    if (feedback) {
      feedback.userResponse = 'revision_requested';
      this.requestRaterFeedback(raterId); // Request new feedback
    }
  }

  discussFeedback(raterId: string): void {
    const raterFeedbackMap = this.ensureRaterFeedbackMap();
    const feedback = raterFeedbackMap.get(raterId);
    if (feedback) {
      feedback.userResponse = 'discussed';
      // Add to chat with context about the specific feedback
      this.chatInput = `I'd like to discuss the feedback from ${feedback.raterName}: "${feedback.feedback.substring(0, 100)}..."`;
    }
  }

  canApproveOutline(): boolean {
    const enabledRaters = this.getEnabledRaters();
    if (enabledRaters.length === 0) return true; // Can approve if no raters

    const raterFeedbackMap = this.ensureRaterFeedbackMap();
    const completedFeedback = Array.from(raterFeedbackMap.values())
      .filter(f => f.status === 'complete');

    return this.story.plotOutline.content.trim().length > 0 &&
           completedFeedback.length >= enabledRaters.length;
  }

  approveOutline(): void {
    if (this.canApproveOutline()) {
      this.story.plotOutline.status = 'approved';
      this.story.plotOutline.metadata.approvedAt = new Date();
      this.outlineUpdated.emit(this.story.plotOutline.content);
      this.outlineApproved.emit();
      this.toastService.showSuccess('Plot outline approved! It will now be included in chapter generation.');
    }
  }

  getEnabledRaters(): Rater[] {
    return Array.from(this.story.raters.values()).filter(r => r.enabled);
  }

  // Template helper methods for safe raterFeedback access
  hasRaterFeedback(raterId: string): boolean {
    const raterFeedbackMap = this.ensureRaterFeedbackMap();
    return raterFeedbackMap.has(raterId);
  }

  getRaterFeedback(raterId: string): PlotOutlineFeedback | undefined {
    const raterFeedbackMap = this.ensureRaterFeedbackMap();
    return raterFeedbackMap.get(raterId);
  }

  deleteRaterFeedback(raterId: string): void {
    const raterFeedbackMap = this.ensureRaterFeedbackMap();
    raterFeedbackMap.delete(raterId);
  }

  private updateOutlineStatus(): void {
    const enabledRaters = this.getEnabledRaters();
    const completedFeedback = this.getRaterFeedbackValues()
      .filter(f => f.status === 'complete');

    if (enabledRaters.length === 0) {
      this.story.plotOutline.status = 'draft';
    } else if (completedFeedback.length >= enabledRaters.length) {
      this.story.plotOutline.status = 'under_review';
    } else {
      this.story.plotOutline.status = 'draft';
    }
  }

  getFeedbackProgress(): { completed: number; total: number } {
    const enabledRaters = this.getEnabledRaters();
    const completedFeedback = this.getRaterFeedbackValues()
      .filter(f => f.status === 'complete');

    return {
      completed: completedFeedback.length,
      total: enabledRaters.length
    };
  }

  /**
   * Ensure raterFeedback is a Map and return it, handling cases where it might be a plain object
   */
  private ensureRaterFeedbackMap(): Map<string, PlotOutlineFeedback> {
    if (!this.story.plotOutline) {
      // Initialize plotOutline if it doesn't exist
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
      return this.story.plotOutline.raterFeedback;
    }

    if (!this.story.plotOutline.raterFeedback) {
      this.story.plotOutline.raterFeedback = new Map();
      return this.story.plotOutline.raterFeedback;
    }

    // Check if it's actually a Map
    if (this.story.plotOutline.raterFeedback instanceof Map) {
      return this.story.plotOutline.raterFeedback;
    }

    // If it's a plain object (due to JSON deserialization), convert it
    if (typeof this.story.plotOutline.raterFeedback === 'object') {
      const feedbackMap = new Map(Object.entries(this.story.plotOutline.raterFeedback as Record<string, PlotOutlineFeedback>));
      this.story.plotOutline.raterFeedback = feedbackMap;
      return feedbackMap;
    }

    // Fallback: create new Map
    this.story.plotOutline.raterFeedback = new Map();
    return this.story.plotOutline.raterFeedback;
  }

  /**
   * Safely get rater feedback values, handling cases where raterFeedback might not be a Map
   */
  private getRaterFeedbackValues(): PlotOutlineFeedback[] {
    const feedbackMap = this.ensureRaterFeedbackMap();
    return Array.from(feedbackMap.values());
  }

  // ============================================================================
  // CHAPTER GENERATION INTEGRATION METHODS (WRI-65)
  // ============================================================================

  /**
   * Sync current content with main plot outline
   */
  syncWithMainPlotOutline(): void {
    if (this.story.plotOutline && this.story.plotOutline.content) {
      // This component already works directly with story.plotOutline
      this.toastService.showSuccess('Plot outline is already synced');
    } else {
      this.toastService.showWarning('No main plot outline found to sync with');
    }
  }

  /**
   * Update main plot outline with current content
   */
  updateMainPlotOutline(): void {
    if (!this.story.plotOutline) {
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
    } else {
      this.story.plotOutline.metadata.lastModified = new Date();
      this.story.plotOutline.metadata.version += 1;
      // Reset status to draft if content changed significantly
      if (this.story.plotOutline.status === 'approved') {
        this.story.plotOutline.status = 'draft';
        this.toastService.showInfo('Plot outline updated. Status reset to draft - consider re-approval.');
      }
    }
    
    this.toastService.showSuccess('Main plot outline updated');
    this.outlineUpdated.emit(this.story.plotOutline.content);
  }


}
