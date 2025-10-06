import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatChipsModule } from '@angular/material/chips';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatIconModule } from '@angular/material/icon';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { of, throwError } from 'rxjs';
import { ContentGenerationComponent } from './content-generation.component';
import { ApiService } from '../../core/services/api.service';
import { LocalStorageService } from '../../core/services/local-storage.service';
import { Story } from '../../shared/models';

describe('ContentGenerationComponent', () => {
  let component: ContentGenerationComponent;
  let fixture: ComponentFixture<ContentGenerationComponent>;
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
    currentPhase: 'detailed_content',
    currentDraft: {
      title: 'Test Story',
      outline: [],
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
    },
    selectedResponses: [
      {
        characterId: 'char-1',
        responseContent: 'I need to find the truth',
        useInStory: true
      }
    ]
  };

  beforeEach(async () => {
    mockApiService = jasmine.createSpyObj('ApiService', ['generateDetailedContent']);
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

    // Set up mock return value BEFORE creating component
    mockLocalStorageService.getStory.and.returnValue(mockStory);

    await TestBed.configureTestingModule({
      declarations: [ContentGenerationComponent],
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
        MatProgressSpinnerModule,
        MatProgressBarModule,
        MatChipsModule,
        MatExpansionModule,
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

    fixture = TestBed.createComponent(ContentGenerationComponent);
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

    it('should navigate away if story not in detailed_content phase', () => {
      const wrongPhaseStory: Story = { ...mockStory, currentPhase: 'draft' };
      mockLocalStorageService.getStory.and.returnValue(wrongPhaseStory);

      component.ngOnInit();

      expect(mockRouter.navigate).toHaveBeenCalled();
    });

    it('should set default guidance based on story context', () => {
      expect(component.guidanceForm.get('userGuidance')?.value).toContain('Generate detailed content');
      expect(component.guidanceForm.get('userGuidance')?.value).toContain('Detective Smith');
    });

    it('should load existing content if available', () => {
      const storyWithContent = {
        ...mockStory,
        finalContent: { content: 'Existing content' }
      };
      mockLocalStorageService.getStory.and.returnValue(storyWithContent);

      component.ngOnInit();

      expect(component.generatedContent).toBeTruthy();
    });
  });

  describe('Form Validation', () => {
    it('should initialize with valid default values', () => {
      expect(component.guidanceForm.valid).toBeTruthy();
    });

    it('should require userGuidance field', () => {
      const guidanceControl = component.guidanceForm.get('userGuidance');
      guidanceControl?.setValue('');

      expect(guidanceControl?.hasError('required')).toBeTruthy();
    });

    it('should validate userGuidance minimum length', () => {
      const guidanceControl = component.guidanceForm.get('userGuidance');
      guidanceControl?.setValue('Short');

      expect(guidanceControl?.hasError('minlength')).toBeTruthy();

      guidanceControl?.setValue('A longer guidance message for content generation');
      expect(guidanceControl?.hasError('minlength')).toBeFalsy();
    });
  });

  describe('Content Generation', () => {
    const mockApiResponse = {
      success: true,
      data: {
        content: 'Generated story content...',
        wordCount: 2500
      }
    };

    it('should generate content on submit', () => {
      mockApiService.generateDetailedContent.and.returnValue(of(mockApiResponse));

      component.onGenerateContent();

      expect(mockApiService.generateDetailedContent).toHaveBeenCalled();
      expect(component.generatedContent).toBeTruthy();
    });

    it('should save generated content to story', () => {
      mockApiService.generateDetailedContent.and.returnValue(of(mockApiResponse));

      component.onGenerateContent();

      expect(mockLocalStorageService.saveStory).toHaveBeenCalled();
      expect(component.story?.finalContent).toBeTruthy();
    });

    it('should show success message after generation', () => {
      mockApiService.generateDetailedContent.and.returnValue(of(mockApiResponse));

      component.onGenerateContent();

      expect(mockSnackBar.open).toHaveBeenCalledWith(
        'Content generated successfully!',
        'Close',
        { duration: 3000 }
      );
    });

    it('should handle API errors', () => {
      mockApiService.generateDetailedContent.and.returnValue(
        throwError(() => new Error('API Error'))
      );

      component.onGenerateContent();

      expect(mockSnackBar.open).toHaveBeenCalledWith(
        'Error generating content. Please try again.',
        'Close',
        jasmine.objectContaining({ duration: 5000 })
      );
    });

    it('should not generate if form is invalid', () => {
      component.guidanceForm.patchValue({ userGuidance: '' });

      component.onGenerateContent();

      expect(mockApiService.generateDetailedContent).not.toHaveBeenCalled();
    });

    it('should not generate if already generating', () => {
      component.isGenerating = true;

      component.onGenerateContent();

      expect(mockApiService.generateDetailedContent).not.toHaveBeenCalled();
    });
  });

  describe('Content Actions', () => {
    it('should clear content on modify', () => {
      component.generatedContent = { content: 'test' };

      component.onModifyContent();

      expect(component.generatedContent).toBeNull();
      expect(mockLocalStorageService.saveStory).toHaveBeenCalled();
    });

    it('should approve content and move to refinement', () => {
      component.generatedContent = { content: 'test' };

      component.onApproveContent();

      expect(component.story?.currentPhase).toBe('refinement');
      expect(mockLocalStorageService.saveStory).toHaveBeenCalled();
      expect(mockRouter.navigate).toHaveBeenCalledWith(['/refinement', 'test-story-1']);
    });

    it('should navigate to refinement with feedback request', () => {
      component.generatedContent = { content: 'test' };

      component.onRequestFeedback();

      expect(mockRouter.navigate).toHaveBeenCalledWith(
        ['/refinement', 'test-story-1'],
        { queryParams: { requestFeedback: 'true' } }
      );
    });
  });

  describe('Getters and Helpers', () => {
    it('should check if has selected responses', () => {
      expect(component.hasSelectedResponses).toBeTruthy();
    });

    it('should filter responses to use', () => {
      const responsesToUse = component.responsesToUse;
      expect(responsesToUse.length).toBe(1);
      expect(responsesToUse[0].useInStory).toBe(true);
    });

    it('should check if can generate', () => {
      // Ensure the form is valid (should be populated by ngOnInit)
      expect(component.guidanceForm.valid).toBeTruthy();

      component.isGenerating = false;
      expect(component.canGenerate).toBeTruthy();

      component.isGenerating = true;
      expect(component.canGenerate).toBeFalsy();
    });

    it('should check if has generated content', () => {
      component.generatedContent = null;
      expect(component.hasGeneratedContent).toBeFalsy();

      component.generatedContent = { content: 'test' };
      expect(component.hasGeneratedContent).toBeTruthy();
    });

    it('should get selected character names', () => {
      const names = component.getSelectedCharacterNames();
      expect(names.length).toBe(1);
      expect(names).toContain('Detective Smith');
    });

    it('should calculate word count', () => {
      component.generatedContent = null;
      expect(component.getWordCount()).toBe(0);

      component.generatedContent = { content: 'This is a test content' };
      expect(component.getWordCount()).toBe(5);
    });
  });

  describe('Generation Preferences', () => {
    it('should provide target length options', () => {
      expect(component.generationPreferences.targetLength.length).toBe(4);
      expect(component.generationPreferences.targetLength[0].value).toBe(1000);
    });

    it('should provide mood options', () => {
      expect(component.generationPreferences.mood.length).toBeGreaterThan(0);
      expect(component.generationPreferences.mood).toContain('Investigative tension');
    });

    it('should provide style options', () => {
      expect(component.generationPreferences.style.length).toBeGreaterThan(0);
      expect(component.generationPreferences.style).toContain('Literary mystery');
    });
  });
});
