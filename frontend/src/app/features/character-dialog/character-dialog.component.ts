import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Story, Character, DialogMessage, DialogConversation, SelectedResponse } from '../../shared/models';
import { ApiService } from '../../core/services/api.service';
import { LocalStorageService } from '../../core/services/local-storage.service';

@Component({
  selector: 'app-character-dialog',
  templateUrl: './character-dialog.component.html',
  styleUrls: ['./character-dialog.component.scss']
})
export class CharacterDialogComponent implements OnInit {
  story: Story | null = null;
  selectedCharacters: Character[] = [];
  activeConversation: DialogConversation | null = null;
  messageForm: FormGroup;
  contextForm: FormGroup;

  isGeneratingResponse = false;
  selectedResponses: SelectedResponse[] = [];
  conversationHistory: DialogMessage[] = [];

  reactionPrompts = [
    'How do you feel about these story events?',
    'What are your thoughts on the proposed plot?',
    'How would you react to these circumstances?',
    'What concerns or excitement do you have?',
    'What would you do in this situation?'
  ];

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private fb: FormBuilder,
    private apiService: ApiService,
    private localStorageService: LocalStorageService,
    private snackBar: MatSnackBar
  ) {
    this.messageForm = this.fb.group({
      message: ['', [Validators.required, Validators.minLength(3)]],
      selectedPrompt: ['']
    });

    this.contextForm = this.fb.group({
      context: ['', [Validators.required, Validators.minLength(10)]]
    });
  }

  ngOnInit(): void {
    const storyId = this.route.snapshot.paramMap.get('id');
    if (storyId) {
      this.loadStory(storyId);
    } else {
      this.router.navigate(['/stories']);
    }
  }

  private loadStory(storyId: string): void {
    this.story = this.localStorageService.getStory(storyId);
    if (!this.story) {
      this.snackBar.open('Story not found', 'Close', { duration: 3000 });
      this.router.navigate(['/stories']);
      return;
    }

    if (this.story.currentPhase !== 'character_dialog') {
      this.snackBar.open('Story is not in character dialog phase', 'Close', { duration: 3000 });
      this.router.navigate(['/draft-review', storyId]);
      return;
    }

    // Initialize with available characters from the draft
    if (this.story.currentDraft?.characters) {
      this.selectedCharacters = [...this.story.currentDraft.characters];
    }

    // Load existing conversation history
    this.conversationHistory = this.story.conversationHistory || [];
    this.selectedResponses = this.story.selectedResponses || [];

    // Set default context from story outline
    if (this.story.currentDraft?.outline) {
      const contextText = this.story.currentDraft.outline
        .map(chapter => `${chapter.title}: ${chapter.summary}`)
        .join('\n\n');
      this.contextForm.patchValue({
        context: contextText
      });
    }
  }

  onCharacterSelectionChange(character: Character, selected: boolean): void {
    if (selected) {
      if (!this.selectedCharacters.find(c => c.id === character.id)) {
        this.selectedCharacters.push(character);
      }
    } else {
      this.selectedCharacters = this.selectedCharacters.filter(c => c.id !== character.id);
    }
  }

  onUsePrompt(prompt: string): void {
    this.messageForm.patchValue({ message: prompt });
  }

  onSendMessage(): void {
    if (this.messageForm.valid && this.selectedCharacters.length > 0 && !this.isGeneratingResponse) {
      this.generateCharacterResponses();
    }
  }

  private generateCharacterResponses(): void {
    if (!this.story) return;

    this.isGeneratingResponse = true;
    const message = this.messageForm.value.message;
    const context = this.contextForm.value.context;

    const conversationContext = {
      storyOutline: this.story.currentDraft?.outline || [],
      previousMessages: this.conversationHistory.slice(-10), // Last 10 messages for context
      storyContext: context
    };

    // Generate responses for each selected character
    const responsePromises = this.selectedCharacters.map(character =>
      this.apiService.generateCharacterDialog(character, message, conversationContext).toPromise()
    );

    Promise.all(responsePromises).then(responses => {
      responses.forEach((response, index) => {
        if (response?.success) {
          const character = this.selectedCharacters[index];
          const dialogMessage: DialogMessage = {
            id: this.generateId(),
            characterId: character.id,
            content: response.data.response,
            timestamp: new Date(),
            emotionalState: response.data.emotionalState || character.currentState?.emotionalState || 'neutral',
            internalThoughts: response.data.internalThoughts,
            selected: false,
            useInStory: false
          };

          this.conversationHistory.push(dialogMessage);
        }
      });

      // Add user message to history
      const userMessage: DialogMessage = {
        id: this.generateId(),
        characterId: 'user',
        content: message,
        timestamp: new Date(),
        emotionalState: 'neutral',
        selected: false,
        useInStory: false
      };

      this.conversationHistory.unshift(userMessage);

      // Save to story
      if (this.story) {
        this.story.conversationHistory = this.conversationHistory;
        this.story.lastModified = new Date();
        this.localStorageService.saveStory(this.story);
      }

      // Reset form
      this.messageForm.patchValue({ message: '' });
      this.isGeneratingResponse = false;

    }).catch(error => {
      console.error('Error generating character responses:', error);
      this.snackBar.open('Error generating character responses. Please try again.', 'Close', {
        duration: 5000
      });
      this.isGeneratingResponse = false;
    });
  }

  onToggleResponseSelection(message: DialogMessage): void {
    message.selected = !message.selected;

    if (message.selected) {
      const selectedResponse: SelectedResponse = {
        characterId: message.characterId,
        messageId: message.id,
        content: message.content,
        timestamp: message.timestamp,
        useInStory: message.useInStory
      };

      // Replace existing selection for this character
      this.selectedResponses = this.selectedResponses.filter(r => r.characterId !== message.characterId);
      this.selectedResponses.push(selectedResponse);
    } else {
      this.selectedResponses = this.selectedResponses.filter(r => r.messageId !== message.id);
    }

    // Save selections
    if (this.story) {
      this.story.selectedResponses = this.selectedResponses;
      this.localStorageService.saveStory(this.story);
    }
  }

  onToggleUseInStory(message: DialogMessage): void {
    message.useInStory = !message.useInStory;

    // Update in selected responses if it exists
    const selectedResponse = this.selectedResponses.find(r => r.messageId === message.id);
    if (selectedResponse) {
      selectedResponse.useInStory = message.useInStory;
    }

    // Save to story
    if (this.story) {
      this.story.conversationHistory = this.conversationHistory;
      this.story.selectedResponses = this.selectedResponses;
      this.localStorageService.saveStory(this.story);
    }
  }

  onProceedToContentGeneration(): void {
    if (this.story && this.hasSelectedResponses) {
      this.story.currentPhase = 'detailed_content';
      this.story.lastModified = new Date();
      this.localStorageService.saveStory(this.story);

      this.snackBar.open('Proceeding to detailed content generation...', 'Close', {
        duration: 3000
      });

      this.router.navigate(['/content-generation', this.story.id]);
    }
  }

  onClearConversation(): void {
    if (confirm('Are you sure you want to clear the conversation history?')) {
      this.conversationHistory = [];
      this.selectedResponses = [];

      if (this.story) {
        this.story.conversationHistory = [];
        this.story.selectedResponses = [];
        this.localStorageService.saveStory(this.story);
      }

      this.snackBar.open('Conversation cleared', 'Close', { duration: 3000 });
    }
  }

  private generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  get hasSelectedCharacters(): boolean {
    return this.selectedCharacters.length > 0;
  }

  get hasSelectedResponses(): boolean {
    return this.selectedResponses.length > 0;
  }

  get responsesToUseInStory(): SelectedResponse[] {
    return this.selectedResponses.filter(r => r.useInStory);
  }

  isCharacterSelected(character: Character): boolean {
    return this.selectedCharacters.some(c => c.id === character.id);
  }

  getCharacterName(characterId: string): string {
    if (characterId === 'user') return 'You';
    const character = this.story?.currentDraft?.characters?.find(c => c.id === characterId);
    return character?.name || 'Unknown Character';
  }

  getMessagesByCharacter(characterId: string): DialogMessage[] {
    return this.conversationHistory.filter(m => m.characterId === characterId);
  }

  trackByMessageId(index: number, message: DialogMessage): string {
    return message.id;
  }
}