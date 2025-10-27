import { Component, Input, Output, EventEmitter, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';

import { ChatInterfaceComponent, ChatInterfaceConfig, MessageActionEvent } from '../chat-interface/chat-interface.component';
import { ChatMessage, Story } from '../../models/story.model';
import { ConversationService } from '../../services/conversation.service';
import { WorldbuildingSyncService } from '../../services/worldbuilding-sync.service';

@Component({
  selector: 'app-worldbuilding-chat',
  standalone: true,
  imports: [CommonModule, ChatInterfaceComponent],
  templateUrl: './worldbuilding-chat.component.html',
  styleUrls: ['./worldbuilding-chat.component.scss']
})
export class WorldbuildingChatComponent implements OnInit, OnDestroy {
  @Input() story!: Story;
  @Input() disabled = false;
  @Input() processing = false;

  @Output() worldbuildingUpdated = new EventEmitter<string>();
  @Output() conversationStarted = new EventEmitter<void>();
  @Output() errorOccurred = new EventEmitter<string>();

  // Chat interface configuration
  chatConfig: ChatInterfaceConfig | null = null;
  
  // Component state
  isInitialized = false;
  currentWorldbuilding = '';
  error: string | null = null;
  
  // Services
  private conversationService = inject(ConversationService);
  private worldbuildingSyncService = inject(WorldbuildingSyncService);
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

  private initializeComponent(): void {
    try {
      // Initialize current worldbuilding content
      this.currentWorldbuilding = this.story.general.worldbuilding || '';

      // Configure chat interface for worldbuilding
      this.chatConfig = {
        phase: 'plot_outline',
        storyId: this.story.id,
        chapterNumber: 0, // Worldbuilding is not chapter-specific
        enableBranching: true,
        enableMessageTypes: ['user', 'assistant'],
        placeholder: 'Describe your world, ask questions, or request worldbuilding assistance...',
        maxHeight: '400px',
        showTimestamps: true,
        showMessageTypes: true,
        allowMessageEditing: true
      };

      this.setupSubscriptions();
      this.isInitialized = true;

    } catch (error) {
      console.error('Failed to initialize WorldbuildingChat:', error);
      this.error = 'Failed to initialize worldbuilding chat';
      this.errorOccurred.emit('Failed to initialize worldbuilding chat');
    }
  }

  private setupSubscriptions(): void {
    // Subscribe to worldbuilding sync updates
    this.subscriptions.push(
      this.worldbuildingSyncService.worldbuildingUpdated$.subscribe(updatedWorldbuilding => {
        if (updatedWorldbuilding !== this.currentWorldbuilding) {
          this.currentWorldbuilding = updatedWorldbuilding;
          this.worldbuildingUpdated.emit(updatedWorldbuilding);
        }
      })
    );

    // Subscribe to conversation changes to trigger sync
    this.subscriptions.push(
      this.conversationService.currentThread$.subscribe(thread => {
        if (thread && this.isInitialized) {
          this.syncWorldbuildingFromConversation();
        }
      })
    );
  }

  // Event handlers

  onMessageSent(message: ChatMessage): void {
    try {
      // Emit conversation started event on first message
      if (!this.conversationStarted.observers.length) {
        this.conversationStarted.emit();
      }

      // Trigger worldbuilding sync after a short delay to allow for assistant response
      setTimeout(() => {
        this.syncWorldbuildingFromConversation();
      }, 1000);

    } catch (error) {
      console.error('Error handling message sent:', error);
      this.errorOccurred.emit('Failed to process message');
    }
  }

  onMessageAction(event: MessageActionEvent): void {
    try {
      // Handle message actions (edit, delete, branch, reply)
      console.log('Message action:', event.action, event.message);
      
      // Trigger sync after message actions that might affect worldbuilding
      if (event.action === 'edit' || event.action === 'delete') {
        setTimeout(() => {
          this.syncWorldbuildingFromConversation();
        }, 500);
      }

    } catch (error) {
      console.error('Error handling message action:', error);
      this.errorOccurred.emit('Failed to process message action');
    }
  }

  onBranchChanged(branchId: string): void {
    try {
      console.log('Branch changed to:', branchId);
      
      // Sync worldbuilding when switching branches
      setTimeout(() => {
        this.syncWorldbuildingFromConversation();
      }, 500);

    } catch (error) {
      console.error('Error handling branch change:', error);
      this.errorOccurred.emit('Failed to process branch change');
    }
  }

  onConversationCleared(): void {
    try {
      // Reset worldbuilding when conversation is cleared
      this.currentWorldbuilding = '';
      this.worldbuildingUpdated.emit('');

    } catch (error) {
      console.error('Error handling conversation clear:', error);
      this.errorOccurred.emit('Failed to clear conversation');
    }
  }

  // Worldbuilding sync methods

  private syncWorldbuildingFromConversation(): void {
    if (!this.story || !this.isInitialized) {
      return;
    }

    try {
      this.worldbuildingSyncService.syncWorldbuildingFromConversation(
        this.story.id,
        this.currentWorldbuilding
      );
    } catch (error) {
      console.error('Failed to sync worldbuilding from conversation:', error);
      this.errorOccurred.emit('Failed to sync worldbuilding data');
    }
  }

  // Public methods for external integration

  /**
   * Manually trigger worldbuilding sync
   */
  public syncWorldbuilding(): void {
    this.syncWorldbuildingFromConversation();
  }

  /**
   * Update the current worldbuilding content
   */
  public updateWorldbuilding(worldbuilding: string): void {
    this.currentWorldbuilding = worldbuilding;
    this.worldbuildingUpdated.emit(worldbuilding);
  }

  /**
   * Get the current worldbuilding summary
   */
  public getCurrentWorldbuilding(): string {
    return this.currentWorldbuilding;
  }

  /**
   * Check if the chat interface is ready
   */
  public isReady(): boolean {
    return this.isInitialized && this.chatConfig !== null;
  }

  /**
   * Focus the chat input
   */
  public focusInput(): void {
    // This will be handled by the ChatInterfaceComponent
  }
}
