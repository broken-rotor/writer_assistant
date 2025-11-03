import { Component, Input, Output, EventEmitter, OnInit, OnDestroy, OnChanges, SimpleChanges, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';

import { ChatInterfaceComponent, ChatInterfaceConfig, MessageActionEvent } from '../chat-interface/chat-interface.component';
import { Story, ChatMessage } from '../../models/story.model';
import { ConversationService } from '../../services/conversation.service';

@Component({
  selector: 'app-worldbuilding-chat',
  standalone: true,
  imports: [CommonModule, ChatInterfaceComponent],
  templateUrl: './worldbuilding-chat.component.html',
  styleUrls: ['./worldbuilding-chat.component.scss']
})
export class WorldbuildingChatComponent implements OnInit, OnDestroy, OnChanges {
  @Input() story!: Story;
  @Input() disabled = false;
  @Input() processing = false;

  @Output() messageSent = new EventEmitter<ChatMessage>();
  @Output() errorOccurred = new EventEmitter<string>();

  // Chat interface configuration
  chatConfig: ChatInterfaceConfig | null = null;
  
  // Component state
  isInitialized = false;
  error: string | null = null;
  
  // Services
  private conversationService = inject(ConversationService);
  private subscriptions: Subscription[] = [];

  ngOnInit(): void {
    if (!this.story) {
      this.error = 'WorldbuildingChat requires a story input';
      this.errorOccurred.emit('WorldbuildingChat requires a story input');
      return;
    }

    this.initializeComponent();
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }

  ngOnChanges(changes: SimpleChanges): void {
    // Re-initialize if story changes
    if (changes['story'] && !changes['story'].firstChange) {
      this.initializeComponent();
    }
  }

  /**
   * Initialize the chat component
   */
  private initializeComponent(): void {
    if (!this.story) {
      return;
    }

    // Configure chat interface for worldbuilding
    this.chatConfig = {
      phase: 'worldbuilding' as any,
      storyId: this.story.id,
      chapterNumber: 0,
      placeholder: 'Ask about worldbuilding, describe your world, or request assistance...',
      enableBranching: true,
      showTimestamps: true,
      allowMessageEditing: true
    };

    this.isInitialized = true;
  }



  /**
   * Handle message sent event
   */
  onMessageSent(message: ChatMessage): void {
    this.messageSent.emit(message);
  }

  /**
   * Handle message action events
   */
  onMessageAction(event: MessageActionEvent): void {
    // Handle any message actions if needed
    console.log('Message action:', event);
  }

  /**
   * Handle branch changed events
   */
  onBranchChanged(branchId: string): void {
    // Handle branch changes if needed
    console.log('Branch changed:', branchId);
  }

  /**
   * Handle conversation cleared events
   */
  onConversationCleared(): void {
    // Handle conversation clearing if needed
    console.log('Conversation cleared');
  }
}
