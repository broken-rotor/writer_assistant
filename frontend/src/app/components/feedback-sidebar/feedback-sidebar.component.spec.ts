import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { of, Subject } from 'rxjs';

import { FeedbackSidebarComponent, FeedbackSidebarConfig } from './feedback-sidebar.component';
import { FeedbackService } from '../../services/feedback.service';
import { 
  EnhancedFeedbackItem, 
  Story, 
  Character, 
  Rater 
} from '../../models/story.model';

describe('FeedbackSidebarComponent', () => {
  let component: FeedbackSidebarComponent;
  let fixture: ComponentFixture<FeedbackSidebarComponent>;
  let mockFeedbackService: jasmine.SpyObj<FeedbackService>;
  let feedbackUpdatedSubject: Subject<void>;
  let requestStatusSubject: Subject<any>;

  const mockConfig: FeedbackSidebarConfig = {
    storyId: 'test-story-id',
    chapterNumber: 1,
    showRequestButtons: true,
    showChatIntegration: true,
    maxHeight: '600px'
  };

  const mockCharacter: Character = {
    id: 'char1',
    name: 'John Doe',
    basicBio: 'A brave hero',
    sex: 'male',
    gender: 'male',
    sexualPreference: 'heterosexual',
    age: 30,
    physicalAppearance: 'Tall and strong',
    usualClothing: 'Armor',
    personality: 'Brave and kind',
    motivations: 'Save the world',
    fears: 'Losing loved ones',
    relationships: 'Has a sister',
    isHidden: false,
    metadata: {
      creationSource: 'user',
      lastModified: new Date()
    }
  };

  const mockRater: Rater = {
    id: 'rater1',
    name: 'Story Critic',
    systemPrompt: 'You are a story critic',
    enabled: true,
    metadata: {
      created: new Date(),
      lastModified: new Date()
    }
  };

  const mockStory: Story = {
    id: 'test-story-id',
    general: {
      title: 'Test Story',
      systemPrompts: {
        mainPrefix: '',
        mainSuffix: '',
        assistantPrompt: '',
        editorPrompt: ''
      },
      worldbuilding: 'A fantasy world'
    },
    characters: new Map([['char1', mockCharacter]]),
    raters: new Map([['rater1', mockRater]]),
    story: {
      summary: 'A test story',
      chapters: []
    },
    plotOutline: {
      content: 'Test plot outline content',
      status: 'approved',
      chatHistory: [],
      raterFeedback: new Map(),
      metadata: {
        created: new Date(),
        lastModified: new Date(),
        version: 1
      }
    },
    metadata: {
      version: '1.0',
      created: new Date(),
      lastModified: new Date()
    }
  };

  const mockFeedbackItems: EnhancedFeedbackItem[] = [
    {
      id: 'feedback1',
      source: 'John Doe',
      type: 'action',
      content: 'Character should be more decisive',
      incorporated: false,
      priority: 'high',
      status: 'pending',
      metadata: {
        created: new Date(),
        lastModified: new Date()
      }
    },
    {
      id: 'feedback2',
      source: 'Story Critic',
      type: 'suggestion',
      content: 'Add more tension to the scene',
      incorporated: false,
      priority: 'medium',
      status: 'pending',
      metadata: {
        created: new Date(),
        lastModified: new Date()
      }
    }
  ];

  beforeEach(async () => {
    feedbackUpdatedSubject = new Subject<void>();
    requestStatusSubject = new Subject<any>();

    const feedbackServiceSpy = jasmine.createSpyObj('FeedbackService', [
      'getAvailableFeedback',
      'requestCharacterFeedback',
      'requestRaterFeedback',
      'addFeedbackToChat',
      'markFeedbackAsIncorporated'
    ], {
      feedbackUpdated$: feedbackUpdatedSubject.asObservable(),
      requestStatus$: requestStatusSubject.asObservable()
    });

    await TestBed.configureTestingModule({
      imports: [FeedbackSidebarComponent, FormsModule],
      providers: [
        { provide: FeedbackService, useValue: feedbackServiceSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(FeedbackSidebarComponent);
    component = fixture.componentInstance;
    mockFeedbackService = TestBed.inject(FeedbackService) as jasmine.SpyObj<FeedbackService>;

    // Set up component inputs
    component.config = mockConfig;
    component.story = mockStory;

    // Set up service mocks
    mockFeedbackService.getAvailableFeedback.and.returnValue(mockFeedbackItems);
    mockFeedbackService.requestCharacterFeedback.and.returnValue(of(true));
    mockFeedbackService.requestRaterFeedback.and.returnValue(of(true));
    mockFeedbackService.addFeedbackToChat.and.returnValue(of(true));
  });

  afterEach(() => {
    feedbackUpdatedSubject.complete();
    requestStatusSubject.complete();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize feedback on ngOnInit', () => {
    component.ngOnInit();

    expect(mockFeedbackService.getAvailableFeedback).toHaveBeenCalledWith(
      mockConfig.storyId,
      mockConfig.chapterNumber
    );
    expect(component.availableFeedback).toEqual(mockFeedbackItems);
  });

  it('should categorize feedback correctly', () => {
    component.ngOnInit();

    expect(component.characterFeedback.length).toBe(1);
    expect(component.characterFeedback[0].source).toBe('John Doe');
    expect(component.raterFeedback.length).toBe(1);
    expect(component.raterFeedback[0].source).toBe('Story Critic');
  });

  it('should toggle feedback selection', () => {
    component.ngOnInit();
    const feedbackId = 'feedback1';

    expect(component.selectedFeedbackIds.has(feedbackId)).toBeFalse();

    component.toggleFeedbackSelection(feedbackId);
    expect(component.selectedFeedbackIds.has(feedbackId)).toBeTrue();

    component.toggleFeedbackSelection(feedbackId);
    expect(component.selectedFeedbackIds.has(feedbackId)).toBeFalse();
  });

  it('should select all feedback', () => {
    component.ngOnInit();

    component.selectAllFeedback();

    expect(component.selectedFeedbackIds.size).toBe(mockFeedbackItems.length);
    mockFeedbackItems.forEach(item => {
      expect(component.selectedFeedbackIds.has(item.id)).toBeTrue();
    });
  });

  it('should clear all selection', () => {
    component.ngOnInit();
    component.selectAllFeedback();

    component.clearAllSelection();

    expect(component.selectedFeedbackIds.size).toBe(0);
  });

  it('should select category feedback', () => {
    component.ngOnInit();

    component.selectCategoryFeedback('character');

    expect(component.selectedFeedbackIds.has('feedback1')).toBeTrue();
    expect(component.selectedFeedbackIds.has('feedback2')).toBeFalse();
  });

  it('should clear category selection', () => {
    component.ngOnInit();
    component.selectAllFeedback();

    component.clearCategorySelection('character');

    expect(component.selectedFeedbackIds.has('feedback1')).toBeFalse();
    expect(component.selectedFeedbackIds.has('feedback2')).toBeTrue();
  });

  it('should emit selection change events', () => {
    spyOn(component.selectionChanged, 'emit');
    component.ngOnInit();

    component.toggleFeedbackSelection('feedback1');

    expect(component.selectionChanged.emit).toHaveBeenCalledWith({
      selectedItems: [mockFeedbackItems[0]],
      totalSelected: 1
    });
  });

  it('should request character feedback', () => {
    spyOn(component.feedbackRequested, 'emit');
    component.ngOnInit();

    component.requestCharacterFeedback('char1');

    expect(component.feedbackRequested.emit).toHaveBeenCalledWith({
      agentId: 'char1',
      agentType: 'character',
      agentName: 'John Doe'
    });
    expect(mockFeedbackService.requestCharacterFeedback).toHaveBeenCalledWith(
      mockStory,
      mockCharacter,
      mockConfig.chapterNumber
    );
  });

  it('should request rater feedback', () => {
    spyOn(component.feedbackRequested, 'emit');
    component.ngOnInit();

    component.requestRaterFeedback('rater1');

    expect(component.feedbackRequested.emit).toHaveBeenCalledWith({
      agentId: 'rater1',
      agentType: 'rater',
      agentName: 'Story Critic'
    });
    expect(mockFeedbackService.requestRaterFeedback).toHaveBeenCalledWith(
      mockStory,
      mockRater,
      mockConfig.chapterNumber,
      jasmine.any(Function)  // onProgress callback
    );
  });

  it('should add selected feedback to chat', () => {
    spyOn(component.addToChat, 'emit');
    component.ngOnInit();
    component.toggleFeedbackSelection('feedback1');
    component.userComment = 'Test comment';

    component.addSelectedToChat();

    expect(component.addToChat.emit).toHaveBeenCalledWith({
      selectedFeedback: [mockFeedbackItems[0]],
      userComment: 'Test comment'
    });
    expect(component.selectedFeedbackIds.size).toBe(0);
    expect(component.userComment).toBe('');
  });

  it('should not add to chat if no feedback selected', () => {
    spyOn(component.addToChat, 'emit');
    component.ngOnInit();

    component.addSelectedToChat();

    expect(component.addToChat.emit).not.toHaveBeenCalled();
  });

  it('should identify character feedback correctly', () => {
    const characterFeedback: EnhancedFeedbackItem = {
      id: 'test',
      source: 'Test',
      type: 'action',
      content: 'Test',
      incorporated: false,
      priority: 'medium',
      status: 'pending',
      metadata: { created: new Date(), lastModified: new Date() }
    };

    expect(component.isCharacterFeedback(characterFeedback)).toBeTrue();
  });

  it('should identify rater feedback correctly', () => {
    const raterFeedback: EnhancedFeedbackItem = {
      id: 'test',
      source: 'Test',
      type: 'suggestion',
      content: 'Test',
      incorporated: false,
      priority: 'medium',
      status: 'pending',
      metadata: { created: new Date(), lastModified: new Date() }
    };

    expect(component.isRaterFeedback(raterFeedback)).toBeTrue();
  });

  it('should get correct status icons', () => {
    const pendingItem: EnhancedFeedbackItem = { ...mockFeedbackItems[0], status: 'pending' };
    const incorporatedItem: EnhancedFeedbackItem = { ...mockFeedbackItems[0], status: 'incorporated' };
    const dismissedItem: EnhancedFeedbackItem = { ...mockFeedbackItems[0], status: 'dismissed' };

    expect(component.getFeedbackStatusIcon(pendingItem)).toBe('⏳');
    expect(component.getFeedbackStatusIcon(incorporatedItem)).toBe('✅');
    expect(component.getFeedbackStatusIcon(dismissedItem)).toBe('❌');
  });

  it('should get correct priority icons', () => {
    expect(component.getPriorityIcon('high')).toBe('🔴');
    expect(component.getPriorityIcon('medium')).toBe('🟡');
    expect(component.getPriorityIcon('low')).toBe('🟢');
  });

  it('should format timestamp correctly', () => {
    const date = new Date('2023-12-25T10:30:00');
    const formatted = component.formatTimestamp(date);
    
    expect(formatted).toContain('Dec');
    expect(formatted).toContain('25');
    expect(formatted).toContain('10:30');
  });

  it('should toggle sections', () => {
    component.showCharacterSection = true;
    component.toggleCharacterSection();
    expect(component.showCharacterSection).toBeFalse();

    component.showRaterSection = true;
    component.toggleRaterSection();
    expect(component.showRaterSection).toBeFalse();
  });

  it('should track feedback items by id', () => {
    const item = mockFeedbackItems[0];
    const trackResult = component.trackByFeedbackId(0, item);
    expect(trackResult).toBe(item.id);
  });

  it('should get available characters and raters', () => {
    component.ngOnInit();

    expect(component.availableCharacters.length).toBe(1);
    expect(component.availableCharacters[0].name).toBe('John Doe');
    expect(component.availableRaters.length).toBe(1);
    expect(component.availableRaters[0].name).toBe('Story Critic');
  });

  it('should handle feedback updates from service', () => {
    component.ngOnInit();
    const newFeedbackItems = [...mockFeedbackItems, {
      id: 'feedback3',
      source: 'New Source',
      type: 'emotion' as const,
      content: 'New feedback',
      incorporated: false,
      priority: 'low' as const,
      status: 'pending' as const,
      metadata: { created: new Date(), lastModified: new Date() }
    }];

    mockFeedbackService.getAvailableFeedback.and.returnValue(newFeedbackItems);
    feedbackUpdatedSubject.next();

    expect(component.availableFeedback.length).toBe(3);
  });

  it('should handle request status updates', () => {
    component.ngOnInit();
    const status = {
      pendingRequests: ['character_char1_1'],
      completedRequests: [],
      failedRequests: []
    };

    requestStatusSubject.next(status);

    expect(component.isRequestingFeedback.has('character_char1_1')).toBeTrue();
  });

  it('should handle disabled state', () => {
    component.disabled = true;
    fixture.detectChanges();

    const sidebarElement = fixture.nativeElement.querySelector('.feedback-sidebar');
    expect(sidebarElement.classList.contains('disabled')).toBeTrue();
  });
});
