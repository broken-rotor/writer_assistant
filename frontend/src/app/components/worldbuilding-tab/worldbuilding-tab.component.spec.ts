import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { WorldbuildingTabComponent } from './worldbuilding-tab.component';
import { TokenCountingService } from '../../services/token-counting.service';
import { ToastService } from '../../services/toast.service';
import { LoadingService } from '../../services/loading.service';
import { GenerationService } from '../../services/generation.service';
import { ConversationService } from '../../services/conversation.service';
import { Story } from '../../models/story.model';
import { of, throwError, BehaviorSubject } from 'rxjs';
import { TokenCountResultItem, ContentType, CountingStrategy } from '../../models/token.model';

describe('WorldbuildingTabComponent', () => {
  let component: WorldbuildingTabComponent;
  let fixture: ComponentFixture<WorldbuildingTabComponent>;
  let mockTokenCountingService: jasmine.SpyObj<TokenCountingService>;
  let mockToastService: jasmine.SpyObj<ToastService>;
  let mockLoadingService: jasmine.SpyObj<LoadingService>;
  let mockGenerationService: jasmine.SpyObj<GenerationService>;
  let mockConversationService: jasmine.SpyObj<ConversationService>;

  const mockStory: Story = {
    id: 'test-story',
    general: {
      title: 'Test Story',
      systemPrompts: {
        mainPrefix: 'Test prefix',
        mainSuffix: 'Test suffix',
        assistantPrompt: 'Test assistant prompt',
        editorPrompt: 'Test editor prompt'
      },
      worldbuilding: 'Test worldbuilding content'
    },
    characters: new Map(),
    raters: new Map(),
    plotOutline: {
      content: 'Test plot outline',
      status: 'draft',
      chatHistory: [],
      raterFeedback: new Map(),
      metadata: {
        created: new Date(),
        lastModified: new Date(),
        version: 1
      }
    },
    story: {
      summary: 'Test summary',
      chapters: []
    },
    chapterCreation: {
      plotPoint: 'Test plot point',
      incorporatedFeedback: [],
      feedbackRequests: new Map()
    },
    metadata: {
      version: '1.0',
      created: new Date(),
      lastModified: new Date()
    }
  };

  const mockTokenResult: TokenCountResultItem = {
    text: 'Test worldbuilding content',
    token_count: 10,
    content_type: ContentType.WORLDBUILDING,
    strategy: CountingStrategy.EXACT,
    overhead_applied: 1.0,
    metadata: {}
  };

  beforeEach(async () => {
    const tokenCountingSpy = jasmine.createSpyObj('TokenCountingService', ['countTokens']);
    const toastSpy = jasmine.createSpyObj('ToastService', ['show', 'showError', 'showSuccess', 'showWarning']);
    const loadingSpy = jasmine.createSpyObj('LoadingService', ['show', 'hide'], { isLoading: false });
    const generationSpy = jasmine.createSpyObj('GenerationService', ['fleshOut', 'generateWorldbuildingResponse']);

    // Create mock observables for ConversationService
    const currentThreadSubject = new BehaviorSubject(null);
    const branchNavigationSubject = new BehaviorSubject({
      currentBranchId: 'main',
      availableBranches: ['main'],
      branchHistory: [],
      canNavigateBack: false,
      canNavigateForward: false
    });
    const isProcessingSubject = new BehaviorSubject(false);

    const conversationSpy = jasmine.createSpyObj('ConversationService',
      ['sendMessage', 'initializeConversation', 'getCurrentBranchMessages', 'getAvailableBranches', 'createBranch', 'switchToBranch'],
      {
        currentThread$: currentThreadSubject.asObservable(),
        branchNavigation$: branchNavigationSubject.asObservable(),
        isProcessing$: isProcessingSubject.asObservable()
      }
    );

    await TestBed.configureTestingModule({
      imports: [
        WorldbuildingTabComponent,
        FormsModule,
        HttpClientTestingModule
      ],
      providers: [
        { provide: TokenCountingService, useValue: tokenCountingSpy },
        { provide: ToastService, useValue: toastSpy },
        { provide: LoadingService, useValue: loadingSpy },
        { provide: GenerationService, useValue: generationSpy },
        { provide: ConversationService, useValue: conversationSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(WorldbuildingTabComponent);
    component = fixture.componentInstance;
    mockTokenCountingService = TestBed.inject(TokenCountingService) as jasmine.SpyObj<TokenCountingService>;
    mockToastService = TestBed.inject(ToastService) as jasmine.SpyObj<ToastService>;
    mockLoadingService = TestBed.inject(LoadingService) as jasmine.SpyObj<LoadingService>;
    mockGenerationService = TestBed.inject(GenerationService) as jasmine.SpyObj<GenerationService>;
    mockConversationService = TestBed.inject(ConversationService) as jasmine.SpyObj<ConversationService>;

    // Setup default mock behavior
    mockTokenCountingService.countTokens.and.returnValue(of(mockTokenResult));
    mockGenerationService.fleshOut.and.returnValue(of({ fleshedOutText: 'Expanded content' }));
    mockGenerationService.generateWorldbuildingResponse.and.returnValue(of('AI generated worldbuilding response'));
    mockConversationService.sendMessage.and.returnValue({
      id: 'ai-msg-1',
      type: 'assistant',
      content: 'AI generated worldbuilding response',
      timestamp: new Date()
    });
    mockConversationService.initializeConversation.and.returnValue({
      id: 'thread-1',
      messages: [],
      branches: new Map(),
      metadata: {
        phase: 'plot_outline' as const,
        created: new Date(),
        lastModified: new Date()
      }
    } as any);
    mockConversationService.getCurrentBranchMessages.and.returnValue([]);
    mockConversationService.getAvailableBranches.and.returnValue([{
      id: 'main',
      name: 'Main',
      parentMessageId: '',
      messageIds: [],
      isActive: true,
      metadata: {
        created: new Date()
      }
    }]);
    mockConversationService.createBranch.and.returnValue({
      id: 'branch-1',
      name: 'Branch 1',
      parentMessageId: '',
      messageIds: [],
      isActive: false,
      metadata: {
        created: new Date()
      }
    });
    mockConversationService.switchToBranch.and.returnValue(undefined);

    // Create a fresh copy of mockStory for each test to ensure test isolation
    const storyCopy = JSON.parse(JSON.stringify(mockStory));
    // Restore Date objects (JSON.parse converts them to strings)
    storyCopy.plotOutline.metadata.created = new Date(storyCopy.plotOutline.metadata.created);
    storyCopy.plotOutline.metadata.lastModified = new Date(storyCopy.plotOutline.metadata.lastModified);
    storyCopy.metadata.created = new Date(storyCopy.metadata.created);
    storyCopy.metadata.lastModified = new Date(storyCopy.metadata.lastModified);
    // Restore Map objects
    storyCopy.characters = new Map();
    storyCopy.raters = new Map();
    storyCopy.plotOutline.raterFeedback = new Map();
    storyCopy.chapterCreation.feedbackRequests = new Map();
    component.story = storyCopy;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with story input', () => {
    fixture.detectChanges();
    expect(component.story).toEqual(mockStory);
  });

  it('should update worldbuilding token counter on init', () => {
    fixture.detectChanges();
    expect(mockTokenCountingService.countTokens).toHaveBeenCalledWith('Test worldbuilding content');
  });

  it('should handle empty worldbuilding content', () => {
    const storyWithEmptyWorldbuilding = {
      ...mockStory,
      general: {
        ...mockStory.general,
        worldbuilding: ''
      }
    };
    component.story = storyWithEmptyWorldbuilding;
    
    fixture.detectChanges();
    
    expect(component.worldbuildingTokenCounterData).toBeNull();
  });

  it('should emit story updated when worldbuilding changes', () => {
    spyOn(component.storyUpdated, 'emit');
    
    component.story!.general.worldbuilding = 'Updated worldbuilding';
    component.onWorldbuildingDirectEdit();
    
    expect(component.storyUpdated.emit).toHaveBeenCalledWith(component.story!);
  });

  it('should handle flesh out functionality', () => {
    component.aiFleshOutWorldbuilding();

    expect(mockLoadingService.show).toHaveBeenCalledWith('Fleshing out worldbuilding...', 'flesh-worldbuilding');
    expect(mockGenerationService.fleshOut).toHaveBeenCalledWith(
      component.story!,
      'Test worldbuilding content',
      'worldbuilding expansion'
    );
  });

  it('should handle errors gracefully', () => {
    mockTokenCountingService.countTokens.and.returnValue(
      throwError(() => new Error('Token counting failed'))
    );
    
    fixture.detectChanges();
    
    // Component should not crash and should handle the error
    expect(component).toBeTruthy();
  });

  it('should handle message sent and generate AI response', () => {
    const mockMessage = {
      id: 'msg-1',
      type: 'user' as const,
      content: 'Tell me about magic systems',
      timestamp: new Date()
    };

    component.onMessageSent(mockMessage);

    expect(mockGenerationService.generateWorldbuildingResponse).toHaveBeenCalledWith(
      component.story!,
      mockMessage.content,
      jasmine.any(Array)
    );
    expect(mockLoadingService.show).toHaveBeenCalledWith('Generating AI response...', 'worldbuilding-chat');
  });

  it('should handle worldbuilding errors', () => {
    spyOn(console, 'error');
    const errorMessage = 'Test error';
    
    component.onWorldbuildingError(errorMessage);
    
    expect(console.error).toHaveBeenCalledWith('Worldbuilding chat error:', errorMessage);
    expect(mockToastService.showError).toHaveBeenCalledWith('Worldbuilding Error', errorMessage);
  });

  it('should show token counter when there are tokens', () => {
    component.worldbuildingTokenCounterData = { current: 10, limit: 4000 };
    
    expect(component.shouldShowWorldbuildingTokenCounter()).toBe(true);
  });

  it('should not show token counter when there are no tokens', () => {
    component.worldbuildingTokenCounterData = { current: 0, limit: 4000 };
    
    expect(component.shouldShowWorldbuildingTokenCounter()).toBe(false);
  });

  it('should not show token counter when data is null', () => {
    component.worldbuildingTokenCounterData = null;
    
    expect(component.shouldShowWorldbuildingTokenCounter()).toBe(false);
  });
});
