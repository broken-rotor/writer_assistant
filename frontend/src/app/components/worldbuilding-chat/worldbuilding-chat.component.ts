import { Component, Input, Output, EventEmitter, OnInit, OnDestroy, ViewChild, ElementRef, HostListener, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';

import { ChatInterfaceComponent, ChatInterfaceConfig, MessageActionEvent } from '../chat-interface/chat-interface.component';
import { Story } from '../../models/story.model';
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

  // ViewChild references for focus management
  @ViewChild('summaryPanel', { static: false }) summaryPanel!: ElementRef;
  @ViewChild('chatPanel', { static: false }) chatPanel!: ElementRef;

  // Chat interface configuration
  chatConfig: ChatInterfaceConfig | null = null;
  
  // Component state
  isInitialized = false;
  currentWorldbuilding = '';
  error: string | null = null;
  
  // UI state for accessibility and navigation
  isMobileView = false;
  focusedPanel: 'summary' | 'chat' = 'chat';
  showKeyboardHelpDialog = false;
  private lastFocusedElement: HTMLElement | null = null;
  
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
    this.setupResponsiveDesign();
    this.setupKeyboardListeners();
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }

  // Keyboard event handlers
  @HostListener('document:keydown', ['$event'])
  onKeyDown(event: KeyboardEvent): void {
    // Handle global keyboard shortcuts
    if (event.ctrlKey || event.metaKey) {
      switch (event.key) {
        case '/':
          event.preventDefault();
          this.toggleKeyboardHelp();
          break;
        case 's':
          event.preventDefault();
          this.syncWorldbuilding();
          this.announceToScreenReader('Worldbuilding sync initiated');
          break;
      }
    }

    // Handle Alt + number shortcuts for mobile panel switching
    if (event.altKey && this.isMobileView) {
      switch (event.key) {
        case '1':
          event.preventDefault();
          this.switchToPanel('summary');
          break;
        case '2':
          event.preventDefault();
          this.switchToPanel('chat');
          break;
      }
    }

    // Handle Escape key
    if (event.key === 'Escape') {
      if (this.showKeyboardHelpDialog) {
        this.hideKeyboardHelp();
      } else {
        this.restoreFocus();
      }
    }
  }

  @HostListener('window:resize', ['$event'])
  onResize(): void {
    this.updateMobileView();
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

  onMessageSent(): void {
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

  // Accessibility and Navigation Methods

  /**
   * Setup responsive design detection
   */
  private setupResponsiveDesign(): void {
    this.updateMobileView();
  }

  /**
   * Setup keyboard event listeners
   */
  private setupKeyboardListeners(): void {
    // Additional keyboard listeners can be added here if needed
  }

  /**
   * Update mobile view state based on window size
   */
  private updateMobileView(): void {
    this.isMobileView = window.innerWidth <= 768;
    
    // Reset focus to chat panel on desktop
    if (!this.isMobileView && this.focusedPanel === 'summary') {
      this.focusedPanel = 'chat';
    }
  }

  /**
   * Switch to a specific panel (mobile navigation)
   */
  public switchToPanel(panel: 'summary' | 'chat'): void {
    this.focusedPanel = panel;
    
    // Focus the panel for keyboard users
    setTimeout(() => {
      if (panel === 'summary' && this.summaryPanel) {
        this.summaryPanel.nativeElement.focus();
        this.announceToScreenReader(`Switched to ${panel} panel`);
      } else if (panel === 'chat' && this.chatPanel) {
        this.chatPanel.nativeElement.focus();
        this.announceToScreenReader(`Switched to ${panel} panel`);
      }
    }, 100);
  }

  /**
   * Focus the summary panel (skip link)
   */
  public focusSummaryPanel(event: Event): void {
    event.preventDefault();
    if (this.summaryPanel) {
      this.summaryPanel.nativeElement.focus();
      this.focusedPanel = 'summary';
      this.announceToScreenReader('Focused on worldbuilding summary panel');
    }
  }

  /**
   * Focus the chat panel (skip link)
   */
  public focusChatPanel(event: Event): void {
    event.preventDefault();
    if (this.chatPanel) {
      this.chatPanel.nativeElement.focus();
      this.focusedPanel = 'chat';
      this.announceToScreenReader('Focused on chat panel');
    }
  }

  /**
   * Toggle keyboard shortcuts help
   */
  public toggleKeyboardHelp(): void {
    if (this.showKeyboardHelpDialog) {
      this.hideKeyboardHelp();
    } else {
      this.showKeyboardHelp();
    }
  }

  /**
   * Show keyboard shortcuts help
   */
  public showKeyboardHelp(): void {
    this.lastFocusedElement = document.activeElement as HTMLElement;
    this.showKeyboardHelpDialog = true;
    
    // Focus the help dialog
    setTimeout(() => {
      const helpDialog = document.querySelector('.keyboard-help-overlay') as HTMLElement;
      if (helpDialog) {
        helpDialog.focus();
      }
    }, 100);
    
    this.announceToScreenReader('Keyboard shortcuts help opened');
  }

  /**
   * Hide keyboard shortcuts help
   */
  public hideKeyboardHelp(): void {
    this.showKeyboardHelpDialog = false;
    this.restoreFocus();
    this.announceToScreenReader('Keyboard shortcuts help closed');
  }

  /**
   * Restore focus to the last focused element
   */
  private restoreFocus(): void {
    if (this.lastFocusedElement) {
      this.lastFocusedElement.focus();
      this.lastFocusedElement = null;
    }
  }

  /**
   * Announce message to screen readers
   */
  private announceToScreenReader(message: string): void {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;
    
    document.body.appendChild(announcement);
    
    // Remove the announcement after it's been read
    setTimeout(() => {
      document.body.removeChild(announcement);
    }, 1000);
  }

  /**
   * Enhanced sync with screen reader announcement
   */
  public syncWorldbuilding(): void {
    this.syncWorldbuildingFromConversation();
    this.announceToScreenReader('Worldbuilding content synchronized from conversation');
  }
}
