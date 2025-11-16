import { Component, Input, Output, EventEmitter, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Story, ChatMessage, FleshOutType } from '../../models/story.model';
import { TokenCounterComponent } from '../token-counter/token-counter.component';
import { TokenCounterData, TokenCounterDisplayMode } from '../../models/token-counter.model';
import { WorldbuildingChatComponent } from '../worldbuilding-chat/worldbuilding-chat.component';
import { TokenCountingService } from '../../services/token-counting.service';
import { ToastService } from '../../services/toast.service';
import { LoadingService } from '../../services/loading.service';
import { GenerationService } from '../../services/generation.service';
import { ConversationService } from '../../services/conversation.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-worldbuilding-tab',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TokenCounterComponent,
    WorldbuildingChatComponent
  ],
  templateUrl: './worldbuilding-tab.component.html',
  styleUrl: './worldbuilding-tab.component.scss'
})
export class WorldbuildingTabComponent implements OnInit, OnDestroy {
  @Input() story: Story | null = null;
  @Input() disabled = false;
  @Output() storyUpdated = new EventEmitter<Story>();

  // Services
  private tokenCountingService = inject(TokenCountingService);
  private toastService = inject(ToastService);
  public loadingService = inject(LoadingService);
  private generationService = inject(GenerationService);
  private conversationService = inject(ConversationService);

  // Token counter state
  worldbuildingTokenCounterData: TokenCounterData | null = null;
  TokenCounterDisplayMode = TokenCounterDisplayMode;

  private subscriptions: Subscription[] = [];

  ngOnInit(): void {
    this.updateWorldbuildingTokenCounter();
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }

  /**
   * Handle file loading for worldbuilding content
   */
  loadFileContent(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    
    if (!file || !this.story) {
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target?.result as string;
      if (content && this.story) {
        this.story.general.worldbuilding = content;
        this.updateWorldbuildingTokenCounter();
        this.emitStoryUpdate();
        this.toastService.showSuccess('File loaded successfully');
      }
    };

    reader.onerror = () => {
      this.toastService.showError('Failed to load file');
    };

    reader.readAsText(file);
    
    // Reset the input so the same file can be loaded again
    input.value = '';
  }

  /**
   * Handle AI Flesh Out functionality
   */
  aiFleshOutWorldbuilding(): void {
    if (!this.story || !this.story.general.worldbuilding) {
      this.toastService.showWarning('Please enter worldbuilding text first');
      return;
    }

    this.loadingService.show('Fleshing out worldbuilding...', 'flesh-worldbuilding');

    const subscription = this.generationService.fleshOut(
      this.story,
      this.story.general.worldbuilding,
      'worldbuilding expansion',
      FleshOutType.WORLDBUILDING
    ).subscribe({
      next: (response: any) => {
        if (this.story) {
          this.story.general.worldbuilding = response.fleshedOutText;
          this.updateWorldbuildingTokenCounter();
          this.emitStoryUpdate();
          this.toastService.showSuccess('Worldbuilding fleshed out successfully! Check the updated content in the worldbuilding panel.');
        }
        this.loadingService.hide();
      },
      error: (err: any) => {
        console.error('Error fleshing out worldbuilding:', err);
        this.toastService.showError('Failed to flesh out worldbuilding. Please try again.');
        this.loadingService.hide();
      }
    });

    this.subscriptions.push(subscription);
  }

  /**
   * Handle direct editing of worldbuilding content
   */
  onWorldbuildingDirectEdit(): void {
    this.updateWorldbuildingTokenCounter();
    this.emitStoryUpdate();
  }

  /**
   * Handle message sent from worldbuilding chat
   */
  onMessageSent(message: ChatMessage): void {
    if (!this.story) {
      return;
    }

    // Initialize chat history if it doesn't exist
    if (!this.story.general.worldbuildingChatHistory) {
      this.story.general.worldbuildingChatHistory = [];
    }

    // Add user message to chat history
    this.story.general.worldbuildingChatHistory.push(message);

    // Generate AI response
    this.loadingService.show('Generating AI response...', 'worldbuilding-chat');

    const subscription = this.generationService.generateWorldbuildingResponse(
      this.story,
      message.content,
      this.story.general.worldbuildingChatHistory
    ).subscribe({
      next: (response: string) => {
        if (this.story) {
          // Add AI response to both the conversation service (for display) and story (for persistence)
          const aiMessage = this.conversationService.sendMessage(response, 'assistant');
          this.story.general.worldbuildingChatHistory!.push(aiMessage);
          this.emitStoryUpdate();
        }
        this.loadingService.hide();
      },
      error: (err: any) => {
        console.error('Error generating worldbuilding response:', err);
        this.toastService.showError('Failed to generate AI response. Please try again.');
        this.loadingService.hide();
      }
    });

    this.subscriptions.push(subscription);
  }

  /**
   * Handle worldbuilding chat errors
   */
  onWorldbuildingError(error: string): void {
    console.error('Worldbuilding chat error:', error);
    this.toastService.showError('Worldbuilding Error', error);
  }

  /**
   * Update the worldbuilding token counter
   */
  private updateWorldbuildingTokenCounter(): void {
    if (!this.story?.general.worldbuilding) {
      this.worldbuildingTokenCounterData = null;
      return;
    }

    const subscription = this.tokenCountingService.countTokens(this.story.general.worldbuilding).subscribe({
      next: (result) => {
        this.worldbuildingTokenCounterData = {
          current: result.token_count,
          limit: 4000, // Set a reasonable limit for worldbuilding
        };
      },
      error: (error) => {
        console.error('Error counting worldbuilding tokens:', error);
        this.worldbuildingTokenCounterData = null;
      }
    });

    this.subscriptions.push(subscription);
  }

  /**
   * Check if worldbuilding token counter should be shown
   */
  shouldShowWorldbuildingTokenCounter(): boolean {
    return !!(this.worldbuildingTokenCounterData && this.worldbuildingTokenCounterData.current > 0);
  }

  /**
   * Emit story update event
   */
  private emitStoryUpdate(): void {
    if (this.story) {
      this.storyUpdated.emit(this.story);
    }
  }
}
