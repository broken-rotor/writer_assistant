import { Component, Input, Output, EventEmitter, OnInit, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Story, ChatMessage } from '../../models/story.model';
import { GenerationService } from '../../services/generation.service';
import { LoadingService } from '../../services/loading.service';
import { ToastService } from '../../services/toast.service';

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

  constructor(
    private generationService: GenerationService,
    private loadingService: LoadingService,
    private toastService: ToastService
  ) {}

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
      case 'draft': return 'Draft';
      case 'under_review': return 'Under Review';
      case 'approved': return 'Approved';
      case 'needs_revision': return 'Needs Revision';
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
}
