import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { of, throwError } from 'rxjs';
import { AiExpansionDialogComponent } from './ai-expansion-dialog.component';
import { ApiService } from '../../core/services/api.service';
import { CharacterService } from '../../core/services/character.service';
import { Character } from '../../shared/models';

describe('AiExpansionDialogComponent', () => {
  let component: AiExpansionDialogComponent;
  let fixture: ComponentFixture<AiExpansionDialogComponent>;
  let apiService: jasmine.SpyObj<ApiService>;
  let characterService: jasmine.SpyObj<CharacterService>;
  let dialogRef: jasmine.SpyObj<MatDialogRef<AiExpansionDialogComponent>>;

  const mockCharacter: Character = {
    id: 'char-1',
    name: 'Alice',
    role: 'protagonist',
    personality: {
      coreTraits: ['brave', 'curious'],
      emotionalPatterns: ['optimistic'],
      speechPatterns: ['direct'],
      motivations: ['justice']
    },
    background: 'A detective',
    currentState: {
      emotionalState: 'determined',
      activeGoals: [],
      currentKnowledge: [],
      relationships: {}
    },
    memorySize: 0,
    isHidden: false,
    creationSource: 'user_defined',
    aiExpansionHistory: []
  };

  const mockDialogData = {
    storyId: 'test-story-1',
    character: mockCharacter,
    section: 'personality'
  };

  beforeEach(async () => {
    const apiServiceSpy = jasmine.createSpyObj('ApiService', ['generateCharacterExpansion']);
    const characterServiceSpy = jasmine.createSpyObj('CharacterService', ['addExpansionRecord', 'updateCharacter']);
    const dialogRefSpy = jasmine.createSpyObj('MatDialogRef', ['close']);

    await TestBed.configureTestingModule({
      declarations: [AiExpansionDialogComponent],
      imports: [
        ReactiveFormsModule,
        MatDialogModule,
        MatFormFieldModule,
        MatInputModule,
        MatButtonModule,
        MatIconModule,
        MatProgressSpinnerModule,
        BrowserAnimationsModule
      ],
      providers: [
        { provide: ApiService, useValue: apiServiceSpy },
        { provide: CharacterService, useValue: characterServiceSpy },
        { provide: MatDialogRef, useValue: dialogRefSpy },
        { provide: MAT_DIALOG_DATA, useValue: mockDialogData }
      ]
    }).compileComponents();

    apiService = TestBed.inject(ApiService) as jasmine.SpyObj<ApiService>;
    characterService = TestBed.inject(CharacterService) as jasmine.SpyObj<CharacterService>;
    dialogRef = TestBed.inject(MatDialogRef) as jasmine.SpyObj<MatDialogRef<AiExpansionDialogComponent>>;
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(AiExpansionDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with dialog data', () => {
    expect(component.data).toEqual(mockDialogData);
  });

  it('should load current content on init', () => {
    expect(component.currentContent).toContain('Core Traits: brave, curious');
    expect(component.currentContent).toContain('Emotional Patterns: optimistic');
  });

  it('should display section label correctly', () => {
    expect(component.sectionLabel).toBe('Personality Traits');
  });

  it('should generate expansion when form is valid', () => {
    const mockResponse = {
      success: true,
      data: {
        expandedContent: 'Expanded personality details...'
      }
    };

    apiService.generateCharacterExpansion.and.returnValue(of(mockResponse));

    component.expansionForm.patchValue({
      expansionPrompt: 'Expand on bravery and how it manifests'
    });

    component.onGenerateExpansion();

    expect(apiService.generateCharacterExpansion).toHaveBeenCalled();
    expect(component.isGenerating).toBe(false);
    expect(component.generatedContent).toBe('Expanded personality details...');
    expect(component.showPreview).toBe(true);
  });

  it('should not generate expansion when form is invalid', () => {
    component.expansionForm.patchValue({
      expansionPrompt: '' // Invalid - required
    });

    component.onGenerateExpansion();

    expect(apiService.generateCharacterExpansion).not.toHaveBeenCalled();
  });

  it('should handle API error during generation', () => {
    apiService.generateCharacterExpansion.and.returnValue(
      throwError(() => new Error('API Error'))
    );

    component.expansionForm.patchValue({
      expansionPrompt: 'Test prompt that meets minimum length'
    });

    component.onGenerateExpansion();

    expect(component.isGenerating).toBe(false);
    expect(component.generatedContent).toContain('Error generating expansion');
    expect(component.showPreview).toBe(true);
  });

  it('should accept generated content and close dialog', () => {
    component.generatedContent = 'Expanded content';
    component.expansionForm.patchValue({
      expansionPrompt: 'Expand personality'
    });

    characterService.addExpansionRecord.and.returnValue(true);
    characterService.updateCharacter.and.returnValue(true);

    component.onAccept();

    expect(characterService.addExpansionRecord).toHaveBeenCalled();
    expect(dialogRef.close).toHaveBeenCalledWith(true);
  });

  it('should not accept if no generated content', () => {
    component.generatedContent = '';

    component.onAccept();

    expect(characterService.addExpansionRecord).not.toHaveBeenCalled();
    expect(dialogRef.close).not.toHaveBeenCalled();
  });

  it('should regenerate content', fakeAsync(() => {
    const mockResponse = {
      success: true,
      data: {
        expandedContent: 'Regenerated content'
      }
    };

    apiService.generateCharacterExpansion.and.returnValue(of(mockResponse));

    component.showPreview = true;
    component.generatedContent = 'Old content';
    component.expansionForm.patchValue({
      expansionPrompt: 'Test prompt for regeneration'
    });

    component.onRegenerate();

    // Process the async observable - since of() is synchronous, tick immediately processes it
    tick();

    // After completion, verify the API was called and new content was generated
    expect(apiService.generateCharacterExpansion).toHaveBeenCalled();
    expect(component.showPreview).toBe(true);
    expect(component.generatedContent).toBe('Regenerated content');
  }));

  it('should cancel and close dialog', () => {
    component.onCancel();

    expect(dialogRef.close).toHaveBeenCalledWith(false);
  });

  it('should format personality traits correctly', () => {
    const result = component['formatPersonalityTraits'](mockCharacter);

    expect(result).toContain('Core Traits: brave, curious');
    expect(result).toContain('Emotional Patterns: optimistic');
    expect(result).toContain('Speech Patterns: direct');
    expect(result).toContain('Motivations: justice');
  });

  it('should format relationships correctly', () => {
    const charWithRelationships: Character = {
      ...mockCharacter,
      currentState: {
        ...mockCharacter.currentState,
        relationships: {
          'bob': {
            perception: 'ally',
            trustLevel: 0.8,
            emotionalResponse: 'friendly',
            lastInteraction: 'yesterday'
          }
        }
      }
    };

    const result = component['formatRelationships'](charWithRelationships);

    expect(result).toContain('bob: ally');
    expect(result).toContain('Trust: 0.8');
  });

  it('should handle empty relationships', () => {
    const result = component['formatRelationships'](mockCharacter);

    expect(result).toBe('No relationships defined yet.');
  });

  it('should format background section correctly', () => {
    component.data.section = 'background';
    component['loadCurrentContent']();

    expect(component.currentContent).toBe('A detective');
  });

  it('should map section to expansion type correctly', () => {
    expect(component['mapSectionToExpansionType']('personality')).toBe('personality_details');
    expect(component['mapSectionToExpansionType']('background')).toBe('background');
    expect(component['mapSectionToExpansionType']('relationships')).toBe('relationships');
    expect(component['mapSectionToExpansionType']('traits')).toBe('traits');
    expect(component['mapSectionToExpansionType']('unknown')).toBe('other');
  });
});
