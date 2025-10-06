import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { MatExpansionModule } from '@angular/material/expansion';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { of, throwError } from 'rxjs';
import { CharacterDialogComponent } from './character-dialog.component';
import { ApiService } from '../../core/services/api.service';
import { LocalStorageService } from '../../core/services/local-storage.service';
import { Story, Character } from '../../shared/models';

describe('CharacterDialogComponent', () => {
  let component: CharacterDialogComponent;
  let fixture: ComponentFixture<CharacterDialogComponent>;
  let mockApiService: jasmine.SpyObj<ApiService>;
  let mockLocalStorageService: jasmine.SpyObj<LocalStorageService>;
  let mockRouter: jasmine.SpyObj<Router>;
  let mockActivatedRoute: any;
  let mockSnackBar: jasmine.SpyObj<MatSnackBar>;

  const mockCharacter: Character = {
    id: 'char-1',
    name: 'Detective Smith',
    role: 'protagonist',
    personality: {
      coreTraits: ['analytical'],
      emotionalPatterns: ['stoic'],
      speechPatterns: ['direct'],
      motivations: ['justice']
    },
    background: 'Veteran detective',
    currentState: {
      emotionalState: 'focused',
      activeGoals: ['solve case'],
      currentKnowledge: ['crime scene'],
      relationships: {}
    },
    memorySize: 1024
  };

  const mockStory: Story = {
    id: 'test-story-1',
    title: 'Test Story',
    genre: 'Mystery',
    length: 'short_story',
    style: 'Literary',
    focusAreas: ['character', 'plot'],
    createdAt: new Date(),
    lastModified: new Date(),
    currentPhase: 'character_dialog',
    currentDraft: {
      title: 'Test Story',
      outline: [{
        id: 'ch-1',
        number: 1,
        title: 'The Beginning',
        summary: 'The story begins...',
        keyEvents: ['Investigation starts'],
        charactersPresent: ['char-1']
      }],
      characters: [mockCharacter],
      themes: ['justice', 'truth'],
      metadata: {
        timestamp: new Date(),
        requestId: 'req-123',
        processingTime: 1500,
        model: 'test-model'
      }
    },
    conversationHistory: [],
    selectedResponses: []
  };

  beforeEach(async () => {
    mockApiService = jasmine.createSpyObj('ApiService', ['generateCharacterDialog']);
    mockLocalStorageService = jasmine.createSpyObj('LocalStorageService', ['getStory', 'saveStory']);
    mockRouter = jasmine.createSpyObj('Router', ['navigate']);
    mockSnackBar = jasmine.createSpyObj('MatSnackBar', ['open']);

    mockActivatedRoute = {
      snapshot: {
        paramMap: {
          get: jasmine.createSpy('get').and.returnValue('test-story-1')
        }
      }
    };

    await TestBed.configureTestingModule({
      declarations: [CharacterDialogComponent],
      imports: [
        ReactiveFormsModule,
        FormsModule,
        BrowserAnimationsModule,
        RouterModule.forRoot([]),
        MatFormFieldModule,
        MatInputModule,
        MatButtonModule,
        MatCardModule,
        MatCheckboxModule,
        MatChipsModule,
        MatIconModule,
        MatExpansionModule
      ],
      providers: [
        { provide: ApiService, useValue: mockApiService },
        { provide: LocalStorageService, useValue: mockLocalStorageService },
        { provide: Router, useValue: mockRouter },
        { provide: ActivatedRoute, useValue: mockActivatedRoute },
        { provide: MatSnackBar, useValue: mockSnackBar }
      ]
    }).compileComponents();

    mockLocalStorageService.getStory.and.returnValue(mockStory);
    fixture = TestBed.createComponent(CharacterDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('Initialization', () => {
    it('should load story on init', () => {
      expect(component.story).toBeTruthy();
      expect(component.story?.id).toBe('test-story-1');
      expect(mockLocalStorageService.getStory).toHaveBeenCalledWith('test-story-1');
    });

    it('should initialize selected characters from draft', () => {
      expect(component.selectedCharacters.length).toBe(1);
      expect(component.selectedCharacters[0].name).toBe('Detective Smith');
    });

    it('should navigate to stories if no story ID', () => {
      mockActivatedRoute.snapshot.paramMap.get.and.returnValue(null);
      component.ngOnInit();

      expect(mockRouter.navigate).toHaveBeenCalledWith(['/stories']);
    });

    it('should navigate to stories if story not found', () => {
      mockLocalStorageService.getStory.and.returnValue(null);
      component.ngOnInit();

      expect(mockRouter.navigate).toHaveBeenCalledWith(['/stories']);
      expect(mockSnackBar.open).toHaveBeenCalledWith('Story not found', 'Close', { duration: 3000 });
    });

    it('should navigate away if story not in character_dialog phase', () => {
      const wrongPhaseStory: Story = { ...mockStory, currentPhase: 'draft' };
      mockLocalStorageService.getStory.and.returnValue(wrongPhaseStory);

      component.ngOnInit();

      expect(mockRouter.navigate).toHaveBeenCalled();
    });

    it('should set default context from story outline', () => {
      expect(component.contextForm.get('context')?.value).toContain('Chapter 1');
    });
  });

  describe('Form Validation', () => {
    it('should validate message is required', () => {
      const messageControl = component.messageForm.get('message');
      messageControl?.setValue('');

      expect(messageControl?.hasError('required')).toBeTruthy();
    });

    it('should validate message minimum length', () => {
      const messageControl = component.messageForm.get('message');
      messageControl?.setValue('Hi');

      expect(messageControl?.hasError('minlength')).toBeTruthy();

      messageControl?.setValue('Hello character');
      expect(messageControl?.hasError('minlength')).toBeFalsy();
    });

    it('should validate context is required', () => {
      const contextControl = component.contextForm.get('context');
      contextControl?.setValue('');

      expect(contextControl?.hasError('required')).toBeTruthy();
    });
  });

  describe('Character Selection', () => {
    it('should add character to selection', () => {
      const newCharacter: Character = {
        ...mockCharacter,
        id: 'char-2',
        name: 'Suspect Jones'
      };
      component.selectedCharacters = [];

      component.onCharacterSelectionChange(newCharacter, true);

      expect(component.selectedCharacters.length).toBe(1);
      expect(component.selectedCharacters[0].name).toBe('Suspect Jones');
    });

    it('should remove character from selection', () => {
      component.onCharacterSelectionChange(mockCharacter, false);

      expect(component.selectedCharacters.length).toBe(0);
    });

    it('should check if character is selected', () => {
      expect(component.isCharacterSelected(mockCharacter)).toBeTruthy();

      const otherCharacter: Character = {
        ...mockCharacter,
        id: 'char-2',
        name: 'Other'
      };
      expect(component.isCharacterSelected(otherCharacter)).toBeFalsy();
    });

    it('should check hasSelectedCharacters getter', () => {
      expect(component.hasSelectedCharacters).toBeTruthy();

      component.selectedCharacters = [];
      expect(component.hasSelectedCharacters).toBeFalsy();
    });
  });

  describe('Message Sending', () => {
    beforeEach(() => {
      component.messageForm.patchValue({
        message: 'What do you think about the case?'
      });
      component.contextForm.patchValue({
        context: 'A mysterious murder has occurred'
      });
    });

    it('should generate character responses', async () => {
      const mockResponse = {
        success: true,
        data: {
          response: 'I think we need more evidence',
          emotionalState: 'determined',
          internalThoughts: 'Something is not right here'
        }
      };

      mockApiService.generateCharacterDialog.and.returnValue(of(mockResponse));

      component.onSendMessage();

      // Wait for promises to resolve
      await new Promise(resolve => setTimeout(resolve, 100));

      expect(mockApiService.generateCharacterDialog).toHaveBeenCalled();
      expect(component.conversationHistory.length).toBeGreaterThan(0);
    });

    it('should handle API errors during message generation', async () => {
      mockApiService.generateCharacterDialog.and.returnValue(
        throwError(() => new Error('API Error'))
      );

      component.onSendMessage();

      // Wait for promises to resolve
      await new Promise(resolve => setTimeout(resolve, 100));

      expect(mockSnackBar.open).toHaveBeenCalledWith(
        'Error generating character responses. Please try again.',
        'Close',
        jasmine.objectContaining({ duration: 5000 })
      );
    });

    it('should not send message if form is invalid', () => {
      component.messageForm.patchValue({ message: '' });

      component.onSendMessage();

      expect(mockApiService.generateCharacterDialog).not.toHaveBeenCalled();
    });

    it('should not send message if no characters selected', () => {
      component.selectedCharacters = [];

      component.onSendMessage();

      expect(mockApiService.generateCharacterDialog).not.toHaveBeenCalled();
    });

    it('should not send message if already generating', () => {
      component.isGeneratingResponse = true;

      component.onSendMessage();

      expect(mockApiService.generateCharacterDialog).not.toHaveBeenCalled();
    });
  });

  describe('Prompt Usage', () => {
    it('should use selected prompt', () => {
      const prompt = 'How do you feel about these story events?';

      component.onUsePrompt(prompt);

      expect(component.messageForm.get('message')?.value).toBe(prompt);
    });

    it('should provide reaction prompts', () => {
      expect(component.reactionPrompts.length).toBeGreaterThan(0);
    });
  });

  describe('Response Selection', () => {
    it('should toggle response selection', () => {
      const message = {
        id: 'msg-1',
        characterId: 'char-1',
        content: 'Test response',
        timestamp: new Date(),
        emotionalState: 'neutral',
        selected: false,
        useInStory: false
      };

      component.conversationHistory = [message];
      component.onToggleResponseSelection(message);

      expect(message.selected).toBeTruthy();
      expect(component.selectedResponses.length).toBe(1);
    });

    it('should toggle use in story flag', () => {
      const message = {
        id: 'msg-1',
        characterId: 'char-1',
        content: 'Test response',
        timestamp: new Date(),
        emotionalState: 'neutral',
        selected: false,
        useInStory: false
      };

      component.conversationHistory = [message];
      component.onToggleUseInStory(message);

      expect(message.useInStory).toBeTruthy();
    });

    it('should check hasSelectedResponses getter', () => {
      expect(component.hasSelectedResponses).toBeFalsy();

      component.selectedResponses = [{
        characterId: 'char-1',
        messageId: 'msg-1',
        content: 'Test',
        timestamp: new Date(),
        useInStory: true
      }];

      expect(component.hasSelectedResponses).toBeTruthy();
    });

    it('should get responses to use in story', () => {
      component.selectedResponses = [
        {
          characterId: 'char-1',
          messageId: 'msg-1',
          content: 'Use this',
          timestamp: new Date(),
          useInStory: true
        },
        {
          characterId: 'char-2',
          messageId: 'msg-2',
          content: 'Ignore this',
          timestamp: new Date(),
          useInStory: false
        }
      ];

      const responsesToUse = component.responsesToUseInStory;
      expect(responsesToUse.length).toBe(1);
      expect(responsesToUse[0].content).toBe('Use this');
    });
  });

  describe('Navigation', () => {
    it('should proceed to content generation', () => {
      component.selectedResponses = [{
        characterId: 'char-1',
        messageId: 'msg-1',
        content: 'Test',
        timestamp: new Date(),
        useInStory: true
      }];

      component.onProceedToContentGeneration();

      expect(component.story?.currentPhase).toBe('detailed_content');
      expect(mockLocalStorageService.saveStory).toHaveBeenCalled();
      expect(mockRouter.navigate).toHaveBeenCalledWith(['/content-generation', 'test-story-1']);
    });

    it('should clear conversation history', () => {
      spyOn(window, 'confirm').and.returnValue(true);
      component.conversationHistory = [{
        id: 'msg-1',
        characterId: 'char-1',
        content: 'Test',
        timestamp: new Date(),
        emotionalState: 'neutral',
        selected: false,
        useInStory: false
      }];

      component.onClearConversation();

      expect(component.conversationHistory.length).toBe(0);
      expect(component.selectedResponses.length).toBe(0);
    });
  });

  describe('Helper Methods', () => {
    it('should get character name', () => {
      expect(component.getCharacterName('char-1')).toBe('Detective Smith');
      expect(component.getCharacterName('user')).toBe('You');
      expect(component.getCharacterName('unknown')).toBe('Unknown Character');
    });

    it('should get messages by character', () => {
      component.conversationHistory = [
        {
          id: 'msg-1',
          characterId: 'char-1',
          content: 'Message 1',
          timestamp: new Date(),
          emotionalState: 'neutral',
          selected: false,
          useInStory: false
        },
        {
          id: 'msg-2',
          characterId: 'char-2',
          content: 'Message 2',
          timestamp: new Date(),
          emotionalState: 'neutral',
          selected: false,
          useInStory: false
        }
      ];

      const messages = component.getMessagesByCharacter('char-1');
      expect(messages.length).toBe(1);
      expect(messages[0].content).toBe('Message 1');
    });

    it('should track by message ID', () => {
      const message = {
        id: 'msg-1',
        characterId: 'char-1',
        content: 'Test',
        timestamp: new Date(),
        emotionalState: 'neutral',
        selected: false,
        useInStory: false
      };

      expect(component.trackByMessageId(0, message)).toBe('msg-1');
    });
  });
});
