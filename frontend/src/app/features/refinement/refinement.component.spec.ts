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
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { of, throwError } from 'rxjs';
import { RefinementComponent } from './refinement.component';
import { ApiService } from '../../core/services/api.service';
import { LocalStorageService } from '../../core/services/local-storage.service';
import { Story, FeedbackData } from '../../shared/models';

describe('RefinementComponent', () => {
  let component: RefinementComponent;
  let fixture: ComponentFixture<RefinementComponent>;
  let mockApiService: jasmine.SpyObj<ApiService>;
  let mockLocalStorageService: jasmine.SpyObj<LocalStorageService>;
  let mockRouter: jasmine.SpyObj<Router>;
  let mockActivatedRoute: any;
  let mockSnackBar: jasmine.SpyObj<MatSnackBar>;

  const mockStory: Story = {
    id: 'test-story-1',
    title: 'Test Story',
    genre: 'Mystery',
    length: 'short_story',
    style: 'Literary',
    focusAreas: ['character', 'plot'],
    createdAt: new Date(),
    lastModified: new Date(),
    currentPhase: 'refinement',
    currentDraft: {
      title: 'Test Story',
      outline: [{
        id: 'ch-1',
        number: 1,
        title: 'The Beginning',
        summary: 'The story begins...',
        keyEvents: ['Opening scene'],
        charactersPresent: []
      }],
      characters: [],
      themes: ['justice', 'truth'],
      metadata: {
        timestamp: new Date(),
        requestId: 'req-123',
        processingTime: 1500,
        model: 'test-model'
      }
    },
    finalContent: {
      content: 'This is the final story content with many words to count',
      wordCount: 10
    }
  };

  const mockFeedbackData: FeedbackData[] = [
    {
      agentId: 'character_consistency',
      agentName: 'Character Consistency Rater',
      score: 8.5,
      feedback: 'Good character development',
      suggestions: ['Add more backstory', 'Develop relationships further'],
      timestamp: new Date()
    },
    {
      agentId: 'narrative_flow',
      agentName: 'Narrative Flow Rater',
      score: 7.8,
      feedback: 'Pacing could be improved',
      suggestions: ['Tighten the opening', 'Add more tension'],
      timestamp: new Date()
    }
  ];

  beforeEach(async () => {
    mockApiService = jasmine.createSpyObj('ApiService', [
      'generateFeedback',
      'applySelectedFeedback'
    ]);
    mockLocalStorageService = jasmine.createSpyObj('LocalStorageService', ['getStory', 'saveStory']);
    mockRouter = jasmine.createSpyObj('Router', ['navigate']);
    mockSnackBar = jasmine.createSpyObj('MatSnackBar', ['open']);

    mockActivatedRoute = {
      snapshot: {
        paramMap: {
          get: jasmine.createSpy('get').and.returnValue('test-story-1')
        },
        queryParamMap: {
          get: jasmine.createSpy('get').and.returnValue(null)
        }
      }
    };

    await TestBed.configureTestingModule({
      declarations: [RefinementComponent],
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
        MatExpansionModule,
        MatProgressSpinnerModule,
        MatProgressBarModule
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
    fixture = TestBed.createComponent(RefinementComponent);
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

    it('should navigate away if no final content available', () => {
      const storyWithoutContent: Story = { ...mockStory, finalContent: undefined };
      mockLocalStorageService.getStory.and.returnValue(storyWithoutContent);

      component.ngOnInit();

      expect(mockRouter.navigate).toHaveBeenCalledWith(['/content-generation', 'test-story-1']);
    });

    it('should auto-select default agents when feedback requested', () => {
      mockActivatedRoute.snapshot.queryParamMap.get.and.returnValue('true');

      component.ngOnInit();

      expect(component.selectedAgents.size).toBeGreaterThan(0);
    });
  });

  describe('Agent Selection', () => {
    it('should add agent to selection', () => {
      component.selectedAgents.clear();

      component.onAgentSelectionChange('character_consistency', true);

      expect(component.selectedAgents.has('character_consistency')).toBeTruthy();
    });

    it('should remove agent from selection', () => {
      component.selectedAgents.add('character_consistency');

      component.onAgentSelectionChange('character_consistency', false);

      expect(component.selectedAgents.has('character_consistency')).toBeFalsy();
    });

    it('should provide available agents', () => {
      expect(component.availableAgents.length).toBeGreaterThan(0);
      expect(component.availableAgents.some(a => a.id === 'character_consistency')).toBeTruthy();
    });

    it('should check hasSelectedAgents getter', () => {
      component.selectedAgents.clear();
      expect(component.hasSelectedAgents).toBeFalsy();

      component.selectedAgents.add('character_consistency');
      expect(component.hasSelectedAgents).toBeTruthy();
    });
  });

  describe('Feedback Generation', () => {
    beforeEach(() => {
      component.selectedAgents.add('character_consistency');
      component.selectedAgents.add('narrative_flow');
    });

    it('should generate feedback from selected agents', () => {
      mockApiService.generateFeedback.and.returnValue(of({
        success: true,
        data: mockFeedbackData
      }));

      component.onGenerateFeedback();

      expect(mockApiService.generateFeedback).toHaveBeenCalled();
      expect(component.feedbackData.length).toBe(2);
      expect(component.showFeedbackResults).toBeTruthy();
    });

    it('should handle API errors during feedback generation', () => {
      mockApiService.generateFeedback.and.returnValue(
        throwError(() => new Error('API Error'))
      );

      component.onGenerateFeedback();

      expect(mockSnackBar.open).toHaveBeenCalledWith(
        'Error generating feedback. Please try again.',
        'Close',
        jasmine.objectContaining({ duration: 5000 })
      );
    });

    it('should not generate feedback if no agents selected', () => {
      component.selectedAgents.clear();

      component.onGenerateFeedback();

      expect(mockApiService.generateFeedback).not.toHaveBeenCalled();
    });

    it('should not generate feedback if already generating', () => {
      component.isGeneratingFeedback = true;

      component.onGenerateFeedback();

      expect(mockApiService.generateFeedback).not.toHaveBeenCalled();
    });

    it('should check canGenerateFeedback getter', () => {
      expect(component.canGenerateFeedback).toBeTruthy();

      component.isGeneratingFeedback = true;
      expect(component.canGenerateFeedback).toBeFalsy();
    });
  });

  describe('Feedback Selection', () => {
    beforeEach(() => {
      component.feedbackData = mockFeedbackData;
    });

    it('should toggle feedback selection', () => {
      const feedbackItem = {
        id: 'feedback-1',
        agentId: 'character_consistency',
        type: 'suggestion' as const,
        content: 'Add more backstory',
        priority: 'medium' as const,
        actionable: true,
        selected: false
      };

      component.onToggleFeedbackSelection(feedbackItem);

      expect(component.selectedFeedback.length).toBe(1);
      expect(component.selectedFeedback[0].id).toBe('feedback-1');
    });

    it('should move feedback from selected to ignored', () => {
      const feedbackItem = {
        id: 'feedback-1',
        agentId: 'character_consistency',
        type: 'suggestion' as const,
        content: 'Add more backstory',
        priority: 'medium' as const,
        actionable: true,
        selected: false
      };

      component.selectedFeedback = [feedbackItem];

      component.onToggleFeedbackSelection(feedbackItem);

      expect(component.selectedFeedback.length).toBe(0);
      expect(component.ignoredFeedback.length).toBe(1);
    });

    it('should check hasSelectedFeedback getter', () => {
      expect(component.hasSelectedFeedback).toBeFalsy();

      component.selectedFeedback = [{
        id: 'feedback-1',
        agentId: 'character_consistency',
        type: 'suggestion',
        content: 'Test',
        priority: 'medium',
        actionable: true,
        selected: false
      }];

      expect(component.hasSelectedFeedback).toBeTruthy();
    });

    it('should get feedback selection state', () => {
      const feedbackItem = {
        id: 'feedback-1',
        agentId: 'character_consistency',
        type: 'suggestion' as const,
        content: 'Test',
        priority: 'medium' as const,
        actionable: true,
        selected: false
      };

      expect(component.getFeedbackSelectionState(feedbackItem)).toBe('unselected');

      component.selectedFeedback = [feedbackItem];
      expect(component.getFeedbackSelectionState(feedbackItem)).toBe('selected');

      component.selectedFeedback = [];
      component.ignoredFeedback = [feedbackItem];
      expect(component.getFeedbackSelectionState(feedbackItem)).toBe('ignored');
    });
  });

  describe('Feedback Application', () => {
    beforeEach(() => {
      component.selectedFeedback = [{
        id: 'feedback-1',
        agentId: 'character_consistency',
        type: 'suggestion',
        content: 'Add more backstory',
        priority: 'medium',
        actionable: true,
        selected: false
      }];
    });

    it('should apply selected feedback', () => {
      const mockRefinedContent = {
        content: 'Refined story content',
        wordCount: 5,
        improvements: ['Added backstory']
      };

      mockApiService.applySelectedFeedback.and.returnValue(of({
        success: true,
        data: mockRefinedContent
      }));

      component.onApplySelectedFeedback();

      expect(mockApiService.applySelectedFeedback).toHaveBeenCalled();
      expect(component.story?.finalContent).toEqual(mockRefinedContent);
      expect(component.story?.refinementHistory?.length).toBe(1);
    });

    it('should handle API errors during feedback application', () => {
      mockApiService.applySelectedFeedback.and.returnValue(
        throwError(() => new Error('API Error'))
      );

      component.onApplySelectedFeedback();

      expect(mockSnackBar.open).toHaveBeenCalledWith(
        'Error applying feedback. Please try again.',
        'Close',
        jasmine.objectContaining({ duration: 5000 })
      );
    });

    it('should not apply feedback if none selected', () => {
      component.selectedFeedback = [];

      component.onApplySelectedFeedback();

      expect(mockApiService.applySelectedFeedback).not.toHaveBeenCalled();
    });

    it('should not apply feedback if already applying', () => {
      component.isApplyingFeedback = true;

      component.onApplySelectedFeedback();

      expect(mockApiService.applySelectedFeedback).not.toHaveBeenCalled();
    });

    it('should check canApplyFeedback getter', () => {
      expect(component.canApplyFeedback).toBeTruthy();

      component.isApplyingFeedback = true;
      expect(component.canApplyFeedback).toBeFalsy();
    });
  });

  describe('Story Completion', () => {
    it('should complete story and navigate to story view', () => {
      component.onCompleteStory();

      expect(component.story?.currentPhase).toBe('completed');
      expect(mockLocalStorageService.saveStory).toHaveBeenCalled();
      expect(mockRouter.navigate).toHaveBeenCalledWith(['/story-view', 'test-story-1']);
    });
  });

  describe('Feedback Management', () => {
    it('should request more feedback', () => {
      component.feedbackData = mockFeedbackData;
      component.selectedFeedback = [/* some items */];
      component.showFeedbackResults = true;

      component.onRequestMoreFeedback();

      expect(component.feedbackData.length).toBe(0);
      expect(component.selectedFeedback.length).toBe(0);
      expect(component.showFeedbackResults).toBeFalsy();
    });

    it('should get feedback by agent', () => {
      component.feedbackData = mockFeedbackData;

      const feedback = component.getFeedbackByAgent('character_consistency');
      expect(feedback).toBeTruthy();
      expect(feedback?.agentName).toBe('Character Consistency Rater');
    });

    it('should get feedback suggestions', () => {
      const feedback = mockFeedbackData[0];
      const suggestions = component.getFeedbackSuggestions(feedback);

      expect(suggestions.length).toBe(2);
      expect(suggestions[0].content).toBe('Add more backstory');
    });

    it('should get total suggestions count', () => {
      component.feedbackData = mockFeedbackData;

      const total = component.getTotalSuggestions();
      expect(total).toBe(4); // 2 suggestions from each agent
    });
  });

  describe('Helper Methods', () => {
    it('should calculate word count', () => {
      const wordCount = component.getWordCount();
      expect(wordCount).toBeGreaterThan(0);
    });

    it('should return 0 for word count if no content', () => {
      component.story = { ...mockStory, finalContent: undefined };
      expect(component.getWordCount()).toBe(0);
    });

    it('should track by feedback ID', () => {
      const feedback = mockFeedbackData[0];
      expect(component.trackByFeedbackId(0, feedback)).toBe('character_consistency');
    });

    it('should track by suggestion ID', () => {
      const suggestion = {
        id: 'suggestion-1',
        agentId: 'test',
        type: 'suggestion' as const,
        content: 'test',
        priority: 'medium' as const,
        actionable: true,
        selected: false
      };
      expect(component.trackBySuggestionId(0, suggestion)).toBe('suggestion-1');
    });
  });
});
