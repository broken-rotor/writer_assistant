import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatChipsModule } from '@angular/material/chips';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { of, throwError } from 'rxjs';
import { StoryInputComponent } from './story-input.component';
import { ApiService } from '../../core/services/api.service';
import { LocalStorageService } from '../../core/services/local-storage.service';
import { StoryInput } from '../../shared/models';

describe('StoryInputComponent', () => {
  let component: StoryInputComponent;
  let fixture: ComponentFixture<StoryInputComponent>;
  let mockApiService: jasmine.SpyObj<ApiService>;
  let mockLocalStorageService: jasmine.SpyObj<LocalStorageService>;
  let mockRouter: jasmine.SpyObj<Router>;
  let mockSnackBar: jasmine.SpyObj<MatSnackBar>;

  beforeEach(async () => {
    mockApiService = jasmine.createSpyObj('ApiService', ['generateDraft']);
    mockLocalStorageService = jasmine.createSpyObj('LocalStorageService', ['saveStory']);
    mockRouter = jasmine.createSpyObj('Router', ['navigate']);
    mockSnackBar = jasmine.createSpyObj('MatSnackBar', ['open']);

    await TestBed.configureTestingModule({
      declarations: [StoryInputComponent],
      imports: [
        ReactiveFormsModule,
        FormsModule,
        BrowserAnimationsModule,
        MatFormFieldModule,
        MatInputModule,
        MatSelectModule,
        MatChipsModule,
        MatButtonModule,
        MatCardModule,
        MatProgressSpinnerModule
      ],
      providers: [
        { provide: ApiService, useValue: mockApiService },
        { provide: LocalStorageService, useValue: mockLocalStorageService },
        { provide: Router, useValue: mockRouter },
        { provide: MatSnackBar, useValue: mockSnackBar }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(StoryInputComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('Form Validation', () => {
    it('should initialize with an invalid form', () => {
      expect(component.storyForm.valid).toBeFalsy();
    });

    it('should validate title field is required', () => {
      const titleControl = component.storyForm.get('title');
      expect(titleControl?.valid).toBeFalsy();

      titleControl?.setValue('');
      expect(titleControl?.hasError('required')).toBeTruthy();
    });

    it('should validate title has minimum length of 3', () => {
      const titleControl = component.storyForm.get('title');
      titleControl?.setValue('AB');
      expect(titleControl?.hasError('minlength')).toBeTruthy();

      titleControl?.setValue('ABC');
      expect(titleControl?.hasError('minlength')).toBeFalsy();
    });

    it('should validate theme has minimum length of 10', () => {
      const themeControl = component.storyForm.get('theme');
      themeControl?.setValue('Short');
      expect(themeControl?.hasError('minlength')).toBeTruthy();

      themeControl?.setValue('A detective story set in 1920s Chicago');
      expect(themeControl?.hasError('minlength')).toBeFalsy();
    });

    it('should validate all required fields', () => {
      component.storyForm.patchValue({
        title: 'Test Story',
        genre: 'Mystery',
        length: 'short_story',
        theme: 'A detective investigates a mysterious case',
        style: 'Literary',
        focusAreas: ['Character Development', 'Plot Pacing']
      });

      expect(component.storyForm.valid).toBeTruthy();
    });
  });

  describe('Story Generation', () => {
    const mockFormValue = {
      title: 'Test Mystery',
      genre: 'Mystery',
      length: 'short_story',
      theme: 'A detective solves a complex case',
      style: 'Noir',
      focusAreas: ['Plot Pacing', 'Dialogue']
    };

    const mockApiResponse = {
      success: true,
      data: {
        title: 'Test Mystery',
        outline: [],
        characters: [],
        themes: ['mystery', 'noir'],
        metadata: {
          timestamp: new Date(),
          requestId: 'req-123',
          processingTime: 1500,
          model: 'test-model'
        }
      }
    };

    beforeEach(() => {
      component.storyForm.patchValue(mockFormValue);
    });

    it('should generate story draft on valid form submission', () => {
      mockApiService.generateDraft.and.returnValue(of(mockApiResponse));

      component.onSubmit();

      expect(component.isGenerating).toBeFalsy();
      expect(mockLocalStorageService.saveStory).toHaveBeenCalled();
      expect(mockApiService.generateDraft).toHaveBeenCalled();
    });

    it('should navigate to draft-review after successful generation', () => {
      mockApiService.generateDraft.and.returnValue(of(mockApiResponse));

      component.onSubmit();

      expect(mockRouter.navigate).toHaveBeenCalledWith(jasmine.arrayContaining(['/draft-review']));
    });

    it('should show success message after generation', () => {
      mockApiService.generateDraft.and.returnValue(of(mockApiResponse));

      component.onSubmit();

      expect(mockSnackBar.open).toHaveBeenCalledWith(
        'Story draft generated successfully!',
        'Close',
        { duration: 3000 }
      );
    });

    it('should handle API errors gracefully', () => {
      spyOn(console, 'error');
      const errorResponse = new Error('API Error');
      mockApiService.generateDraft.and.returnValue(throwError(() => errorResponse));

      component.onSubmit();

      expect(console.error).toHaveBeenCalledWith('Error generating draft:', errorResponse);
      expect(mockSnackBar.open).toHaveBeenCalledWith(
        'Error generating story draft. Please try again.',
        'Close',
        jasmine.objectContaining({ duration: 5000 })
      );
    });

    it('should handle unsuccessful API response', () => {
      const unsuccessfulResponse = {
        success: false,
        data: {
          title: '',
          outline: [],
          characters: [],
          themes: [],
          metadata: {
            timestamp: new Date(),
            requestId: '',
            processingTime: 0,
            model: ''
          }
        }
      };
      mockApiService.generateDraft.and.returnValue(of(unsuccessfulResponse));

      component.onSubmit();

      expect(mockSnackBar.open).toHaveBeenCalledWith(
        'Failed to generate story draft',
        'Close',
        jasmine.objectContaining({ duration: 5000 })
      );
    });

    it('should not submit if form is invalid', () => {
      component.storyForm.patchValue({ title: '' });

      component.onSubmit();

      expect(mockApiService.generateDraft).not.toHaveBeenCalled();
    });

    it('should not submit if already generating', () => {
      component.isGenerating = true;

      component.onSubmit();

      expect(mockApiService.generateDraft).not.toHaveBeenCalled();
    });

    it('should set isGenerating flag during generation', () => {
      mockApiService.generateDraft.and.returnValue(of(mockApiResponse));

      component.onSubmit();

      // Flag should be reset after completion
      expect(component.isGenerating).toBeFalsy();
    });
  });

  describe('Form Options', () => {
    it('should provide genre options', () => {
      expect(component.genres.length).toBeGreaterThan(0);
      expect(component.genres).toContain('Mystery');
      expect(component.genres).toContain('Romance');
    });

    it('should provide length options', () => {
      expect(component.lengths.length).toBe(3);
      expect(component.lengths[0].value).toBe('short_story');
    });

    it('should provide style options', () => {
      expect(component.styles.length).toBeGreaterThan(0);
      expect(component.styles).toContain('Literary');
    });

    it('should provide focus area options', () => {
      expect(component.focusAreaOptions.length).toBeGreaterThan(0);
      expect(component.focusAreaOptions).toContain('Character Development');
    });
  });
});
