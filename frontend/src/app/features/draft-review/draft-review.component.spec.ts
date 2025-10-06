import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { of, throwError } from 'rxjs';
import { DraftReviewComponent } from './draft-review.component';
import { ApiService } from '../../core/services/api.service';
import { LocalStorageService } from '../../core/services/local-storage.service';
import { Story } from '../../shared/models';

describe('DraftReviewComponent', () => {
  let component: DraftReviewComponent;
  let fixture: ComponentFixture<DraftReviewComponent>;
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
    currentPhase: 'draft',
    currentDraft: {
      title: 'Test Story',
      outline: [
        {
          id: 'ch-1',
          number: 1,
          title: 'The Beginning',
          summary: 'The investigation begins',
          keyEvents: ['Crime discovered', 'First clue found'],
          charactersPresent: ['char-1']
        },
        {
          id: 'ch-2',
          number: 2,
          title: 'The Middle',
          summary: 'The investigation continues',
          keyEvents: ['Interview suspects', 'New evidence'],
          charactersPresent: ['char-1']
        }
      ],
      characters: [
        {
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
        }
      ],
      themes: ['justice', 'truth'],
      metadata: {
        timestamp: new Date(),
        requestId: 'req-123',
        processingTime: 1500,
        model: 'test-model'
      }
    }
  };

  beforeEach(async () => {
    mockApiService = jasmine.createSpyObj('ApiService', ['reviseDraft']);
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
      declarations: [DraftReviewComponent],
      imports: [
        ReactiveFormsModule,
        FormsModule,
        BrowserAnimationsModule,
        RouterModule.forRoot([]),
        MatFormFieldModule,
        MatInputModule,
        MatSelectModule,
        MatButtonModule,
        MatCardModule,
        MatProgressBarModule,
        MatProgressSpinnerModule,
        MatChipsModule,
        MatIconModule
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
    fixture = TestBed.createComponent(DraftReviewComponent);
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
  });

  describe('Form Validation', () => {
    it('should initialize with valid form', () => {
      expect(component.feedbackForm).toBeTruthy();
    });

    it('should validate feedback is required', () => {
      const feedbackControl = component.feedbackForm.get('feedback');
      feedbackControl?.setValue('');

      expect(feedbackControl?.hasError('required')).toBeTruthy();
    });

    it('should validate feedback minimum length', () => {
      const feedbackControl = component.feedbackForm.get('feedback');
      feedbackControl?.setValue('Short');

      expect(feedbackControl?.hasError('minlength')).toBeTruthy();

      feedbackControl?.setValue('This is a longer feedback message');
      expect(feedbackControl?.hasError('minlength')).toBeFalsy();
    });
  });

  describe('Draft Approval', () => {
    it('should approve draft and navigate to character dialog', () => {
      component.onApprove();

      expect(component.story?.currentPhase).toBe('character_dialog');
      expect(mockLocalStorageService.saveStory).toHaveBeenCalled();
      expect(mockRouter.navigate).toHaveBeenCalledWith(['/character-dialog', 'test-story-1']);
      expect(mockSnackBar.open).toHaveBeenCalled();
    });

    it('should check canApprove getter', () => {
      expect(component.canApprove).toBeTruthy();

      component.story = null;
      expect(component.canApprove).toBeFalsy();
    });
  });

  describe('Draft Revision', () => {
    const mockRevisedDraft = {
      title: 'Revised Story',
      outline: [{
        id: 'ch-1',
        number: 1,
        title: 'Updated Beginning',
        summary: 'A revised opening',
        keyEvents: ['New event'],
        charactersPresent: ['char-1']
      }],
      characters: [],
      themes: ['justice'],
      metadata: {
        timestamp: new Date(),
        requestId: 'req-456',
        processingTime: 2000,
        model: 'test-model'
      }
    };

    beforeEach(() => {
      component.feedbackForm.patchValue({
        feedback: 'Please make the story darker',
        specificChanges: ['Adjust pacing']
      });
    });

    it('should request revision with valid feedback', () => {
      mockApiService.reviseDraft.and.returnValue(of({
        success: true,
        data: mockRevisedDraft
      }));

      component.onRequestRevision();

      expect(mockApiService.reviseDraft).toHaveBeenCalled();
      expect(component.revisionHistory.length).toBe(1);
      expect(component.story?.currentDraft).toEqual(mockRevisedDraft);
    });

    it('should handle API errors during revision', () => {
      mockApiService.reviseDraft.and.returnValue(
        throwError(() => new Error('API Error'))
      );

      component.onRequestRevision();

      expect(mockSnackBar.open).toHaveBeenCalledWith(
        'Error revising draft. Please try again.',
        'Close',
        jasmine.objectContaining({ duration: 5000 })
      );
    });

    it('should not revise if form is invalid', () => {
      component.feedbackForm.patchValue({ feedback: '' });

      component.onRequestRevision();

      expect(mockApiService.reviseDraft).not.toHaveBeenCalled();
    });

    it('should not revise if already revising', () => {
      component.isRevising = true;

      component.onRequestRevision();

      expect(mockApiService.reviseDraft).not.toHaveBeenCalled();
    });

    it('should check canRevise getter', () => {
      expect(component.canRevise).toBeTruthy();

      component.isRevising = true;
      expect(component.canRevise).toBeFalsy();
    });
  });

  describe('Navigation', () => {
    it('should navigate to story input to start over', () => {
      component.onStartOver();

      expect(mockRouter.navigate).toHaveBeenCalledWith(
        ['/story-input'],
        { queryParams: { editStory: 'test-story-1' } }
      );
    });
  });

  describe('Revision History', () => {
    it('should check hasRevisionHistory getter', () => {
      expect(component.hasRevisionHistory).toBeFalsy();

      component.revisionHistory.push({
        version: 1,
        feedback: 'test feedback',
        specificChanges: [],
        previousDraft: mockStory.currentDraft,
        timestamp: new Date()
      });

      expect(component.hasRevisionHistory).toBeTruthy();
    });
  });

  describe('Specific Change Options', () => {
    it('should provide specific change options', () => {
      expect(component.specificChangeOptions.length).toBeGreaterThan(0);
      expect(component.specificChangeOptions).toContain('Adjust pacing');
      expect(component.specificChangeOptions).toContain('Develop characters further');
    });
  });
});
