import { Component, Input, Output, EventEmitter, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Story } from '../../models/story.model';

@Component({
  selector: 'app-plot-outline-tab',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './plot-outline-tab.component.html',
  styleUrl: './plot-outline-tab.component.scss'
})
export class PlotOutlineTabComponent implements OnInit {
  @Input() story!: Story;
  @Input() disabled = false;
  @Output() outlineUpdated = new EventEmitter<string>();
  @Output() outlineApproved = new EventEmitter<void>();

  // Component state
  showChat = true;
  chatInput = '';
  isGeneratingAI = false;
  isResearching = false;

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

  sendChatMessage(): void {
    console.log('Send chat message - to be implemented');
    if (this.chatInput.trim() && this.story?.plotOutline) {
      // Add user message to chat history
      const userMessage = {
        id: `msg-${Date.now()}`,
        type: 'user' as const,
        content: this.chatInput.trim(),
        timestamp: new Date()
      };
      
      this.story.plotOutline.chatHistory.push(userMessage);
      this.chatInput = '';
      
      // Simulate AI response (placeholder)
      setTimeout(() => {
        const aiMessage = {
          id: `msg-${Date.now()}-ai`,
          type: 'assistant' as const,
          content: 'This is a placeholder AI response. The actual AI chat functionality will be implemented in a future task.',
          timestamp: new Date()
        };
        this.story.plotOutline.chatHistory.push(aiMessage);
      }, 1000);
    }
  }

  clearChat(): void {
    console.log('Clear chat - to be implemented');
    if (this.story?.plotOutline) {
      this.story.plotOutline.chatHistory = [];
    }
  }
}
