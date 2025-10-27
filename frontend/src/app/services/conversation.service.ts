import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
import { of } from 'rxjs';
import { 
  ChatMessage, 
  ConversationThread, 
  ConversationBranch, 
  BranchNavigation,
  ChapterComposeState,
  LLMChatRequest,
  LLMChatResponse,
  LLMChatComposeContext,
  Story
} from '../models/story.model';
import { LocalStorageService } from './local-storage.service';
import { PhaseStateService, PhaseType } from './phase-state.service';
import { ApiService } from './api.service';

export interface ConversationConfig {
  phase: PhaseType;
  storyId: string;
  chapterNumber: number;
  enableBranching: boolean;
  maxBranches?: number;
  autoSave?: boolean;
}

export interface MessageSendOptions {
  createBranch?: boolean;
  branchName?: string;
  parentMessageId?: string;
  metadata?: any;
}

@Injectable({
  providedIn: 'root'
})
export class ConversationService {
  private currentThreadSubject = new BehaviorSubject<ConversationThread | null>(null);
  private branchNavigationSubject = new BehaviorSubject<BranchNavigation>({
    currentBranchId: 'main',
    availableBranches: ['main'],
    branchHistory: [],
    canNavigateBack: false,
    canNavigateForward: false
  });
  private isProcessingSubject = new BehaviorSubject<boolean>(false);

  public currentThread$ = this.currentThreadSubject.asObservable();
  public branchNavigation$ = this.branchNavigationSubject.asObservable();
  public isProcessing$ = this.isProcessingSubject.asObservable();

  private config: ConversationConfig | null = null;
  private storageKey = '';

  constructor(
    private localStorageService: LocalStorageService,
    private phaseStateService: PhaseStateService,
    private apiService: ApiService
  ) {}

  /**
   * Initialize conversation for a specific phase and story
   */
  initializeConversation(config: ConversationConfig): ConversationThread {
    this.config = config;
    
    this.storageKey = `conversation_${config.storyId}_${config.chapterNumber}_${config.phase}`;

    // Try to load existing conversation
    let thread = this.loadConversationFromStorage();
    
    if (!thread) {
      // Create new conversation thread
      thread = this.createNewThread(config);
      this.saveConversationToStorage(thread);
    }

    this.currentThreadSubject.next(thread);
    this.updateBranchNavigation(thread);
    
    return thread;
  }

  /**
   * Send a new message to the current conversation
   */
  sendMessage(content: string, type: 'user' | 'assistant' | 'system' = 'user', options: MessageSendOptions = {}): ChatMessage {
    const currentThread = this.currentThreadSubject.value;
    if (!currentThread || !this.config) {
      throw new Error('Conversation not initialized');
    }

    const messageId = this.generateMessageId();
    const now = new Date();

    const message: ChatMessage = {
      id: messageId,
      type,
      content,
      timestamp: now,
      author: options.metadata?.author,
      parentMessageId: options.parentMessageId,
      metadata: {
        phase: this.config.phase,
        messageIndex: currentThread.messages.length,
        branchId: this.branchNavigationSubject.value.currentBranchId,
        ...options.metadata
      }
    };

    // Handle branch creation if requested
    if (options.createBranch && options.branchName) {
      this.createBranch(options.branchName, options.parentMessageId || this.getLastUserMessageId());
    }

    // Add message to current thread
    currentThread.messages.push(message);
    currentThread.metadata.lastModified = now;

    // Update branch message tracking
    const currentBranch = currentThread.branches.get(this.branchNavigationSubject.value.currentBranchId);
    if (currentBranch) {
      currentBranch.messageIds.push(messageId);
    }

    // Save and notify
    this.saveConversationToStorage(currentThread);
    this.currentThreadSubject.next(currentThread);
    this.updateBranchNavigation(currentThread);

    return message;
  }

  /**
   * Create a new conversation branch
   */
  createBranch(branchName: string, parentMessageId?: string): ConversationBranch {
    const currentThread = this.currentThreadSubject.value;
    if (!currentThread) {
      throw new Error('No active conversation thread');
    }

    const branchId = this.generateBranchId();
    const now = new Date();

    const branch: ConversationBranch = {
      id: branchId,
      name: branchName,
      parentMessageId: parentMessageId || this.getLastUserMessageId(),
      messageIds: [],
      isActive: false,
      metadata: {
        created: now,
        description: `Branch created from message: ${parentMessageId || 'latest'}`
      }
    };

    currentThread.branches.set(branchId, branch);
    currentThread.metadata.lastModified = now;

    this.saveConversationToStorage(currentThread);
    this.currentThreadSubject.next(currentThread);
    this.updateBranchNavigation(currentThread);

    return branch;
  }

  /**
   * Switch to a different conversation branch
   */
  switchToBranch(branchId: string): void {
    const currentThread = this.currentThreadSubject.value;
    if (!currentThread || !currentThread.branches.has(branchId)) {
      throw new Error(`Branch ${branchId} not found`);
    }

    // Update branch navigation history
    const currentNavigation = this.branchNavigationSubject.value;
    const newHistory = [...currentNavigation.branchHistory];
    
    if (currentNavigation.currentBranchId !== branchId) {
      newHistory.push(currentNavigation.currentBranchId);
    }

    // Update active branch
    currentThread.branches.forEach(branch => {
      branch.isActive = branch.id === branchId;
    });

    currentThread.currentBranchId = branchId;
    currentThread.metadata.lastModified = new Date();

    this.saveConversationToStorage(currentThread);
    this.currentThreadSubject.next(currentThread);
    this.updateBranchNavigation(currentThread);
  }

  /**
   * Get messages for the current branch
   */
  getCurrentBranchMessages(): ChatMessage[] {
    const currentThread = this.currentThreadSubject.value;
    if (!currentThread) {
      return [];
    }

    const currentBranchId = this.branchNavigationSubject.value.currentBranchId;
    const currentBranch = currentThread.branches.get(currentBranchId);
    
    if (!currentBranch) {
      // Return all messages if no specific branch (main branch)
      return currentThread.messages;
    }

    // Get messages up to the branch point, then branch-specific messages
    const branchPoint = currentThread.messages.find(m => m.id === currentBranch.parentMessageId);
    const branchPointIndex = branchPoint ? currentThread.messages.indexOf(branchPoint) : -1;
    
    const baseMessages = branchPointIndex >= 0 ? 
      currentThread.messages.slice(0, branchPointIndex + 1) : [];
    
    const branchMessages = currentThread.messages.filter(m => 
      currentBranch.messageIds.includes(m.id)
    );

    return [...baseMessages, ...branchMessages];
  }

  /**
   * Get available branches for the current conversation
   */
  getAvailableBranches(): ConversationBranch[] {
    const currentThread = this.currentThreadSubject.value;
    if (!currentThread) {
      return [];
    }

    return Array.from(currentThread.branches.values());
  }

  /**
   * Rename a conversation branch
   */
  renameBranch(branchId: string, newName: string): void {
    const currentThread = this.currentThreadSubject.value;
    if (!currentThread) {
      throw new Error('No active conversation thread');
    }

    const branch = currentThread.branches.get(branchId);
    if (!branch) {
      throw new Error(`Branch ${branchId} not found`);
    }

    branch.name = newName;
    currentThread.metadata.lastModified = new Date();

    this.saveConversationToStorage(currentThread);
    this.currentThreadSubject.next(currentThread);
    this.updateBranchNavigation(currentThread);
  }

  /**
   * Delete a conversation branch
   */
  deleteBranch(branchId: string): void {
    const currentThread = this.currentThreadSubject.value;
    if (!currentThread || branchId === 'main') {
      throw new Error('Cannot delete main branch or no active thread');
    }

    const branch = currentThread.branches.get(branchId);
    if (!branch) {
      throw new Error(`Branch ${branchId} not found`);
    }

    // Remove branch messages from the main messages array
    currentThread.messages = currentThread.messages.filter(m => 
      !branch.messageIds.includes(m.id)
    );

    // Remove the branch
    currentThread.branches.delete(branchId);

    // Switch to main branch if we're deleting the current branch
    if (this.branchNavigationSubject.value.currentBranchId === branchId) {
      this.switchToBranch('main');
    }

    currentThread.metadata.lastModified = new Date();

    this.saveConversationToStorage(currentThread);
    this.currentThreadSubject.next(currentThread);
    this.updateBranchNavigation(currentThread);
  }

  /**
   * Clear the entire conversation
   */
  clearConversation(): void {
    if (!this.config) {
      throw new Error('Conversation not initialized');
    }

    const newThread = this.createNewThread(this.config);
    this.saveConversationToStorage(newThread);
    this.currentThreadSubject.next(newThread);
    this.updateBranchNavigation(newThread);
  }

  /**
   * Get conversation statistics
   */
  getConversationStats(): {
    totalMessages: number;
    branchCount: number;
    userMessages: number;
    assistantMessages: number;
    lastActivity: Date | null;
  } {
    const currentThread = this.currentThreadSubject.value;
    if (!currentThread) {
      return {
        totalMessages: 0,
        branchCount: 0,
        userMessages: 0,
        assistantMessages: 0,
        lastActivity: null
      };
    }

    return {
      totalMessages: currentThread.messages.length,
      branchCount: currentThread.branches.size,
      userMessages: currentThread.messages.filter(m => m.type === 'user').length,
      assistantMessages: currentThread.messages.filter(m => m.type === 'assistant').length,
      lastActivity: currentThread.metadata.lastModified
    };
  }

  /**
   * Export conversation data
   */
  exportConversation(): any {
    const currentThread = this.currentThreadSubject.value;
    if (!currentThread) {
      return null;
    }

    return {
      thread: {
        ...currentThread,
        branches: Array.from(currentThread.branches.entries())
      },
      navigation: this.branchNavigationSubject.value,
      config: this.config
    };
  }

  /**
   * Import conversation data
   */
  importConversation(data: any): void {
    if (!data.thread || !data.config) {
      throw new Error('Invalid conversation data');
    }

    this.config = data.config;
    this.storageKey = `conversation_${data.config.storyId}_${data.config.chapterNumber}_${data.config.phase}`;

    const thread: ConversationThread = {
      ...data.thread,
      branches: new Map(data.thread.branches)
    };

    this.saveConversationToStorage(thread);
    this.currentThreadSubject.next(thread);
    this.updateBranchNavigation(thread);
  }

  // Private helper methods

  private createNewThread(config: ConversationConfig): ConversationThread {
    const now = new Date();
    const threadId = this.generateThreadId();

    const mainBranch: ConversationBranch = {
      id: 'main',
      name: 'Main',
      parentMessageId: '',
      messageIds: [],
      isActive: true,
      metadata: {
        created: now,
        description: 'Main conversation branch'
      }
    };

    return {
      id: threadId,
      messages: [],
      currentBranchId: 'main',
      branches: new Map([['main', mainBranch]]),
      metadata: {
        created: now,
        lastModified: now,
        phase: config.phase
      }
    };
  }

  private updateBranchNavigation(thread: ConversationThread): void {
    const availableBranches = Array.from(thread.branches.keys());
    const currentNavigation = this.branchNavigationSubject.value;

    const newNavigation: BranchNavigation = {
      currentBranchId: thread.currentBranchId,
      availableBranches,
      branchHistory: currentNavigation.branchHistory,
      canNavigateBack: currentNavigation.branchHistory.length > 0,
      canNavigateForward: false // TODO: Implement forward navigation
    };

    this.branchNavigationSubject.next(newNavigation);
  }

  private loadConversationFromStorage(): ConversationThread | null {
    try {
      const data = this.localStorageService.getItem(this.storageKey);
      if (data) {
        // Convert branches array back to Map
        const thread = {
          ...data,
          branches: new Map(data.branches || [])
        };
        return thread;
      }
    } catch (error) {
      console.error('Failed to load conversation from storage:', error);
    }
    return null;
  }

  private saveConversationToStorage(thread: ConversationThread): void {
    try {
      // Convert Map to array for storage
      const dataToStore = {
        ...thread,
        branches: Array.from(thread.branches.entries())
      };
      this.localStorageService.setItem(this.storageKey, dataToStore);
    } catch (error) {
      console.error('Failed to save conversation to storage:', error);
    }
  }

  private getLastUserMessageId(): string {
    const currentThread = this.currentThreadSubject.value;
    if (!currentThread) {
      return '';
    }

    const userMessages = currentThread.messages.filter(m => m.type === 'user');
    return userMessages.length > 0 ? userMessages[userMessages.length - 1].id : '';
  }

  private generateMessageId(): string {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private generateBranchId(): string {
    return `branch_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private generateThreadId(): string {
    return `thread_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // ============================================================================
  // LLM CHAT INTEGRATION FOR THREE-PHASE CHAPTER COMPOSE SYSTEM (WRI-49)
  // ============================================================================

  /**
   * Send a message to the LLM chat endpoint and add the response to the conversation
   */
  sendLLMChatMessage(
    content: string,
    story: Story,
    chapterComposeState: ChapterComposeState,
    agentType: 'writer' | 'character' | 'editor' = 'writer',
    options?: MessageSendOptions
  ): Observable<ChatMessage> {
    const currentThread = this.currentThreadSubject.value;
    if (!currentThread) {
      return of({
        id: this.generateMessageId(),
        type: 'assistant',
        content: 'Error: No active conversation thread',
        timestamp: new Date(),
        metadata: { 
          error: 'No active thread',
          phase: chapterComposeState.currentPhase,
          messageIndex: 0
        }
      });
    }

    this.isProcessingSubject.next(true);

    // Add user message to thread
    const userMessage: ChatMessage = {
      id: this.generateMessageId(),
      type: 'user',
      content,
      timestamp: new Date(),
      metadata: options?.metadata || {}
    };

    this.sendMessage(userMessage.content, userMessage.type, options);

    // Prepare LLM chat request
    const chatRequest: LLMChatRequest = {
      messages: currentThread.messages.map(msg => ({
        role: msg.type === 'user' ? 'user' : 'assistant',
        content: msg.content,
        timestamp: msg.timestamp.toISOString()
      })),
      agent_type: agentType,
      compose_context: this.buildLLMChatContext(chapterComposeState, currentThread),
      system_prompts: {
        mainPrefix: story.general.systemPrompts.mainPrefix,
        mainSuffix: story.general.systemPrompts.mainSuffix,
        assistantPrompt: story.general.systemPrompts.assistantPrompt,
        editorPrompt: story.general.systemPrompts.editorPrompt
      },
      max_tokens: 1000,
      temperature: 0.8
    };

    return this.apiService.llmChat(chatRequest).pipe(
      map((response: LLMChatResponse) => {
        const assistantMessage: ChatMessage = {
          id: this.generateMessageId(),
          type: 'assistant',
          content: response.message.content,
          timestamp: new Date(),
          metadata: {
            agent_type: response.agent_type,
            phase: chapterComposeState.currentPhase,
            messageIndex: currentThread.messages.length,
            ...response.metadata
          }
        };

        this.sendMessage(assistantMessage.content, assistantMessage.type);
        this.isProcessingSubject.next(false);
        return assistantMessage;
      }),
      catchError((error) => {
        console.error('LLM Chat error:', error);
        const errorMessage: ChatMessage = {
          id: this.generateMessageId(),
          type: 'assistant',
          content: 'Sorry, I encountered an error while processing your message. Please try again.',
          timestamp: new Date(),
          metadata: { 
            error: error.message || 'Unknown error',
            phase: chapterComposeState.currentPhase,
            messageIndex: currentThread?.messages.length || 0
          }
        };

        this.sendMessage(errorMessage.content, errorMessage.type);
        this.isProcessingSubject.next(false);
        return of(errorMessage);
      })
    );
  }

  /**
   * Build LLM chat context from chapter compose state
   */
  private buildLLMChatContext(
    chapterComposeState: ChapterComposeState,
    conversationThread: ConversationThread
  ): LLMChatComposeContext {
    const context: LLMChatComposeContext = {
      current_phase: chapterComposeState.currentPhase,
      story_context: {
        phase_status: {
          plot_outline: chapterComposeState.phases.plotOutline.status,
          chapter_detail: chapterComposeState.phases.chapterDetailer.status,
          final_edit: chapterComposeState.phases.finalEdit.status
        }
      },
      conversation_branch_id: conversationThread.currentBranchId
    };

    // Add phase-specific context
    switch (chapterComposeState.currentPhase) {
      case 'plot_outline':
        if (chapterComposeState.phases.plotOutline.outline.items.size > 0) {
          const outlineItems = Array.from(chapterComposeState.phases.plotOutline.outline.items.values());
          context.story_context['plot_outline'] = outlineItems
            .sort((a, b) => a.order - b.order)
            .map(item => ({ title: item.title, description: item.description }));
        }
        break;

      case 'chapter_detail':
        if (chapterComposeState.phases.plotOutline.status === 'completed') {
          const outlineItems = Array.from(chapterComposeState.phases.plotOutline.outline.items.values());
          context.story_context['completed_outline'] = outlineItems
            .sort((a, b) => a.order - b.order)
            .map(item => ({ title: item.title, description: item.description }));
        }
        if (chapterComposeState.phases.chapterDetailer.chapterDraft.content) {
          context.chapter_draft = chapterComposeState.phases.chapterDetailer.chapterDraft.content;
        }
        break;

      case 'final_edit':
        if (chapterComposeState.phases.chapterDetailer.status === 'completed') {
          context.chapter_draft = chapterComposeState.phases.chapterDetailer.chapterDraft.content;
        }
        if (chapterComposeState.phases.finalEdit.finalChapter.content) {
          context.story_context['final_chapter'] = chapterComposeState.phases.finalEdit.finalChapter.content;
        }
        break;
    }

    return context;
  }

  /**
   * Get conversation history for API requests
   */
  getConversationHistoryForAPI(maxMessages = 10): { role: 'user' | 'assistant'; content: string; timestamp?: string }[] {
    const currentThread = this.currentThreadSubject.value;
    if (!currentThread) {
      return [];
    }

    return currentThread.messages
      .slice(-maxMessages)
      .map(msg => ({
        role: msg.type === 'user' ? 'user' : 'assistant',
        content: msg.content,
        timestamp: msg.timestamp.toISOString()
      }));
  }
}
