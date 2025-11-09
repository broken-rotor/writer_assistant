import { Component, Input, Output, EventEmitter, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewChecked, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';

import {
  ChatMessage,
  ConversationThread,
  ConversationBranch,
  BranchNavigation
} from '../../models/story.model';
import {
  ConversationService,
  ConversationConfig
} from '../../services/conversation.service';

export interface ChatInterfaceConfig {
  storyId: string;
  chapterNumber: number;
  enableBranching?: boolean;
  enableMessageTypes?: ('user' | 'assistant' | 'character' | 'rater' | 'editor')[];
  placeholder?: string;
  maxHeight?: string;
  showTimestamps?: boolean;
  showMessageTypes?: boolean;
  allowMessageEditing?: boolean;
}

export interface MessageActionEvent {
  action: 'edit' | 'delete' | 'branch' | 'reply';
  message: ChatMessage;
  data?: unknown;
}

@Component({
  selector: 'app-chat-interface',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat-interface.component.html',
  styleUrls: ['./chat-interface.component.scss']
})
export class ChatInterfaceComponent implements OnInit, OnDestroy, AfterViewChecked {
  @Input() config!: ChatInterfaceConfig;
  @Input() disabled = false;
  @Input() processing = false;

  @Output() messageSent = new EventEmitter<ChatMessage>();
  @Output() messageAction = new EventEmitter<MessageActionEvent>();
  @Output() branchChanged = new EventEmitter<string>();
  @Output() conversationCleared = new EventEmitter<void>();

  @ViewChild('messagesContainer', { static: false }) messagesContainer!: ElementRef;
  @ViewChild('messageInput', { static: false }) messageInput!: ElementRef;

  // Component state
  currentThread: ConversationThread | null = null;
  branchNavigation: BranchNavigation | null = null;
  messages: ChatMessage[] = [];
  messageText = '';
  isProcessing = false;

  // UI state
  showBranchDialog = false;
  newBranchName = '';
  branchParentMessageId = '';
  editingMessageId: string | null = null;
  editingMessageText = '';
  shouldScrollToBottom = false;

  // Subscriptions
  private subscriptions: Subscription[] = [];
  private conversationService = inject(ConversationService);

  ngOnInit(): void {
    if (!this.config) {
      throw new Error('ChatInterfaceComponent requires config input');
    }

    this.initializeConversation();
    this.setupSubscriptions();
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }

  ngAfterViewChecked(): void {
    if (this.shouldScrollToBottom) {
      this.scrollToBottom();
      this.shouldScrollToBottom = false;
    }
  }

  // Initialization methods

  private initializeConversation(): void {
    const conversationConfig: ConversationConfig = {
      storyId: this.config.storyId,
      chapterNumber: this.config.chapterNumber,
      enableBranching: this.config.enableBranching ?? true,
      autoSave: true
    };

    this.conversationService.initializeConversation(conversationConfig);
  }

  private setupSubscriptions(): void {
    // Subscribe to conversation thread changes
    this.subscriptions.push(
      this.conversationService.currentThread$.subscribe(thread => {
        this.currentThread = thread;
        this.updateMessages();
      })
    );

    // Subscribe to branch navigation changes
    this.subscriptions.push(
      this.conversationService.branchNavigation$.subscribe(navigation => {
        this.branchNavigation = navigation;
      })
    );

    // Subscribe to processing state
    this.subscriptions.push(
      this.conversationService.isProcessing$.subscribe(processing => {
        this.isProcessing = processing;
      })
    );
  }

  private updateMessages(): void {
    this.messages = this.conversationService.getCurrentBranchMessages();
    this.shouldScrollToBottom = true;
  }

  // Message handling methods

  sendMessage(): void {
    if (!this.messageText.trim() || this.disabled || this.isProcessing) {
      return;
    }

    const content = this.messageText.trim();
    this.messageText = '';

    try {
      const message = this.conversationService.sendMessage(content, 'user');
      this.messageSent.emit(message);
      this.shouldScrollToBottom = true;
    } catch (error) {
      console.error('Failed to send message:', error);
      // Restore message text on error
      this.messageText = content;
    }
  }

  onKeyPress(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  // Message actions

  startEditMessage(message: ChatMessage): void {
    if (!this.config.allowMessageEditing || message.type !== 'user') {
      return;
    }

    this.editingMessageId = message.id;
    this.editingMessageText = message.content;
  }

  saveEditMessage(): void {
    if (!this.editingMessageId || !this.editingMessageText.trim()) {
      this.cancelEditMessage();
      return;
    }

    // TODO: Implement message editing in service
    this.messageAction.emit({
      action: 'edit',
      message: this.messages.find(m => m.id === this.editingMessageId)!,
      data: { newContent: this.editingMessageText.trim() }
    });

    this.cancelEditMessage();
  }

  cancelEditMessage(): void {
    this.editingMessageId = null;
    this.editingMessageText = '';
  }

  deleteMessage(message: ChatMessage): void {
    if (confirm('Are you sure you want to delete this message?')) {
      this.messageAction.emit({
        action: 'delete',
        message,
        data: null
      });
    }
  }

  // Branch management methods

  showCreateBranchDialog(message: ChatMessage): void {
    if (!this.config.enableBranching || message.type !== 'user') {
      return;
    }

    this.branchParentMessageId = message.id;
    this.newBranchName = `Branch from "${message.content.substring(0, 20)}..."`;
    this.showBranchDialog = true;
  }

  createBranch(): void {
    if (!this.newBranchName.trim()) {
      return;
    }

    try {
      this.conversationService.createBranch(this.newBranchName.trim(), this.branchParentMessageId);
      this.closeBranchDialog();
    } catch (error) {
      console.error('Failed to create branch:', error);
    }
  }

  onBranchChange(event: Event): void {
    const target = event.target as HTMLSelectElement;
    if (target && target.value) {
      this.switchToBranch(target.value);
    }
  }

  onEditKeydown(event: Event): void {
    const keyboardEvent = event as KeyboardEvent;
    if (keyboardEvent.ctrlKey) {
      this.saveEditMessage();
    }
  }

  switchToBranch(branchId: string): void {
    try {
      this.conversationService.switchToBranch(branchId);
      this.branchChanged.emit(branchId);
    } catch (error) {
      console.error('Failed to switch branch:', error);
    }
  }

  renameBranch(branchId: string, currentName: string): void {
    const newName = prompt('Enter new branch name:', currentName);
    if (newName && newName.trim() && newName.trim() !== currentName) {
      try {
        this.conversationService.renameBranch(branchId, newName.trim());
      } catch (error) {
        console.error('Failed to rename branch:', error);
      }
    }
  }

  deleteBranch(branchId: string): void {
    if (branchId === 'main') {
      return;
    }

    if (confirm('Are you sure you want to delete this branch? This action cannot be undone.')) {
      try {
        this.conversationService.deleteBranch(branchId);
      } catch (error) {
        console.error('Failed to delete branch:', error);
      }
    }
  }

  closeBranchDialog(): void {
    this.showBranchDialog = false;
    this.newBranchName = '';
    this.branchParentMessageId = '';
  }

  // Branch navigation methods

  getBranchesForMessage(message: ChatMessage): ConversationBranch[] {
    if (!this.currentThread || message.type !== 'user') {
      return [];
    }

    return Array.from(this.currentThread.branches.values())
      .filter(branch => branch.parentMessageId === message.id);
  }

  getAvailableBranches(): ConversationBranch[] {
    return this.conversationService.getAvailableBranches();
  }

  getCurrentBranchName(): string {
    if (!this.branchNavigation || !this.currentThread) {
      return 'Main';
    }

    const currentBranch = this.currentThread.branches.get(this.branchNavigation.currentBranchId);
    return currentBranch ? currentBranch.name : 'Main';
  }

  // Utility methods

  clearConversation(): void {
    if (confirm('Are you sure you want to clear the entire conversation? This action cannot be undone.')) {
      this.conversationService.clearConversation();
      this.conversationCleared.emit();
    }
  }

  getMessageTypeClass(message: ChatMessage): string {
    const baseClass = 'message';
    const typeClass = `message-${message.type}`;
    const authorClass = message.author ? `message-author-${message.author.toLowerCase().replace(/\s+/g, '-')}` : '';
    
    return [baseClass, typeClass, authorClass].filter(Boolean).join(' ');
  }

  getMessageTypeLabel(message: ChatMessage): string {
    if (message.author) {
      return message.author;
    }

    switch (message.type) {
      case 'user': return 'You';
      case 'assistant': return 'Assistant';
      case 'system': return 'System';
      default: return message.type;
    }
  }

  formatTimestamp(timestamp: Date): string {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  }

  getPlaceholderText(): string {
    return this.config.placeholder || 'Type your message...';
  }

  isCurrentBranch(branchId: string): boolean {
    return this.branchNavigation?.currentBranchId === branchId;
  }

  canCreateBranch(): boolean {
    return this.config.enableBranching !== false && !this.disabled;
  }

  canEditMessage(message: ChatMessage): boolean {
    return this.config.allowMessageEditing !== false && 
           message.type === 'user' && 
           !this.disabled;
  }

  private scrollToBottom(): void {
    if (this.messagesContainer) {
      const element = this.messagesContainer.nativeElement;
      element.scrollTop = element.scrollHeight;
    }
  }

  // Focus management
  focusInput(): void {
    if (this.messageInput) {
      this.messageInput.nativeElement.focus();
    }
  }

  // Track by function for ngFor
  trackByMessageId(index: number, message: ChatMessage): string {
    return message.id;
  }
}
