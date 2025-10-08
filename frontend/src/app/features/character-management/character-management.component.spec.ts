import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { MatDialogModule } from '@angular/material/dialog';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { CharacterManagementComponent } from './character-management.component';
import { CharacterService } from '../../core/services/character.service';
import { Character } from '../../shared/models';

describe('CharacterManagementComponent', () => {
  let component: CharacterManagementComponent;
  let fixture: ComponentFixture<CharacterManagementComponent>;
  let characterService: jasmine.SpyObj<CharacterService>;

  const mockActiveCharacters: Character[] = [
    {
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
    }
  ];

  const mockHiddenCharacters: Character[] = [
    {
      id: 'char-2',
      name: 'Bob',
      role: 'antagonist',
      personality: {
        coreTraits: ['cunning'],
        emotionalPatterns: ['cold'],
        speechPatterns: ['formal'],
        motivations: ['power']
      },
      background: 'A criminal',
      currentState: {
        emotionalState: 'calculating',
        activeGoals: [],
        currentKnowledge: [],
        relationships: {}
      },
      memorySize: 0,
      isHidden: true,
      creationSource: 'user_defined',
      aiExpansionHistory: []
    }
  ];

  beforeEach(async () => {
    const characterServiceSpy = jasmine.createSpyObj('CharacterService', [
      'getActiveCharacters',
      'getHiddenCharacters',
      'hideCharacter',
      'unhideCharacter',
      'addCharacter',
      'updateCharacter',
      'getCharacter'
    ]);

    await TestBed.configureTestingModule({
      declarations: [CharacterManagementComponent],
      imports: [
        ReactiveFormsModule,
        MatDialogModule,
        MatSnackBarModule,
        MatFormFieldModule,
        MatInputModule,
        MatSelectModule,
        MatIconModule,
        MatButtonModule,
        BrowserAnimationsModule
      ],
      providers: [
        { provide: CharacterService, useValue: characterServiceSpy }
      ]
    }).compileComponents();

    characterService = TestBed.inject(CharacterService) as jasmine.SpyObj<CharacterService>;
  });

  beforeEach(() => {
    characterService.getActiveCharacters.and.returnValue(mockActiveCharacters);
    characterService.getHiddenCharacters.and.returnValue(mockHiddenCharacters);

    fixture = TestBed.createComponent(CharacterManagementComponent);
    component = fixture.componentInstance;
    component.storyId = 'test-story-1';
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load active and hidden characters on init', () => {
    expect(component.activeCharacters).toEqual(mockActiveCharacters);
    expect(component.hiddenCharacters).toEqual(mockHiddenCharacters);
    expect(characterService.getActiveCharacters).toHaveBeenCalledWith('test-story-1');
    expect(characterService.getHiddenCharacters).toHaveBeenCalledWith('test-story-1');
  });

  it('should select first active character by default', () => {
    expect(component.selectedCharacter).toEqual(mockActiveCharacters[0]);
  });

  it('should load character into form when selected', () => {
    component.onSelectCharacter(mockActiveCharacters[0]);

    expect(component.selectedCharacter).toEqual(mockActiveCharacters[0]);
    expect(component.characterForm.value.name).toBe('Alice');
    expect(component.characterForm.value.role).toBe('protagonist');
    expect(component.characterForm.value.background).toBe('A detective');
  });

  it('should hide a character', () => {
    spyOn(window, 'confirm').and.returnValue(true);
    characterService.hideCharacter.and.returnValue(true);
    characterService.getActiveCharacters.and.returnValue([]);
    characterService.getHiddenCharacters.and.returnValue([...mockHiddenCharacters, mockActiveCharacters[0]]);

    component.onHideCharacter(mockActiveCharacters[0]);

    expect(characterService.hideCharacter).toHaveBeenCalledWith('test-story-1', 'char-1');
    expect(characterService.getActiveCharacters).toHaveBeenCalled();
  });

  it('should not hide character if user cancels confirmation', () => {
    spyOn(window, 'confirm').and.returnValue(false);

    component.onHideCharacter(mockActiveCharacters[0]);

    expect(characterService.hideCharacter).not.toHaveBeenCalled();
  });

  it('should unhide a character', () => {
    characterService.unhideCharacter.and.returnValue(true);
    characterService.getActiveCharacters.and.returnValue([...mockActiveCharacters, mockHiddenCharacters[0]]);
    characterService.getHiddenCharacters.and.returnValue([]);

    component.onUnhideCharacter(mockHiddenCharacters[0]);

    expect(characterService.unhideCharacter).toHaveBeenCalledWith('test-story-1', 'char-2');
    expect(characterService.getActiveCharacters).toHaveBeenCalled();
  });

  it('should create a new character', () => {
    component.characterForm.patchValue({
      name: 'Charlie',
      role: 'supporting',
      background: 'A helpful friend who assists the protagonist',
      coreTraits: 'friendly, helpful',
      emotionalPatterns: 'cheerful',
      speechPatterns: 'casual',
      motivations: 'help others'
    });

    const newCharacter: Character = {
      id: 'char-3',
      name: 'Charlie',
      role: 'supporting',
      personality: {
        coreTraits: ['friendly', 'helpful'],
        emotionalPatterns: ['cheerful'],
        speechPatterns: ['casual'],
        motivations: ['help others']
      },
      background: 'A helpful friend who assists the protagonist',
      currentState: {
        emotionalState: 'neutral',
        activeGoals: [],
        currentKnowledge: [],
        relationships: {}
      },
      memorySize: 0,
      isHidden: false,
      creationSource: 'user_defined',
      aiExpansionHistory: []
    };

    component.isCreatingNew = true;
    characterService.addCharacter.and.returnValue(newCharacter);
    characterService.getActiveCharacters.and.returnValue([...mockActiveCharacters, newCharacter]);

    component.onSaveCharacter();

    expect(characterService.addCharacter).toHaveBeenCalled();
    expect(component.isCreatingNew).toBe(false);
    expect(component.isEditMode).toBe(false);
  });

  it('should update an existing character', () => {
    component.selectedCharacter = mockActiveCharacters[0];
    component.isEditMode = true;
    component.characterForm.patchValue({
      name: 'Alice Updated',
      background: 'An experienced detective'
    });

    characterService.updateCharacter.and.returnValue(true);

    component.onSaveCharacter();

    expect(characterService.updateCharacter).toHaveBeenCalledWith(
      'test-story-1',
      'char-1',
      jasmine.objectContaining({
        name: 'Alice Updated',
        background: 'An experienced detective'
      })
    );
    expect(component.isEditMode).toBe(false);
  });

  it('should not save if form is invalid', () => {
    component.characterForm.patchValue({
      name: '' // Invalid - required
    });

    component.onSaveCharacter();

    expect(characterService.addCharacter).not.toHaveBeenCalled();
    expect(characterService.updateCharacter).not.toHaveBeenCalled();
  });

  it('should cancel edit mode', () => {
    component.isEditMode = true;
    component.selectedCharacter = mockActiveCharacters[0];
    component.characterForm.patchValue({ name: 'Changed' });

    component.onCancelEdit();

    expect(component.isEditMode).toBe(false);
    expect(component.characterForm.value.name).toBe('Alice'); // Restored original
  });

  it('should enter create new mode', () => {
    component.onCreateNew();

    expect(component.isCreatingNew).toBe(true);
    expect(component.isEditMode).toBe(true);
    expect(component.selectedCharacter).toBeNull();
    expect(component.characterForm.value.role).toBe('supporting'); // Default
  });

  it('should enter edit mode', () => {
    component.isEditMode = false;

    component.onEditMode();

    expect(component.isEditMode).toBe(true);
  });

  it('should parse comma-separated values correctly', () => {
    const result = component['parseCommaSeparated']('brave, curious,  determined');
    expect(result).toEqual(['brave', 'curious', 'determined']);
  });

  it('should handle empty comma-separated values', () => {
    const result = component['parseCommaSeparated']('');
    expect(result).toEqual([]);
  });

  it('should return correct active character count', () => {
    expect(component.activeCharacterCount).toBe(1);
  });

  it('should return correct hidden character count', () => {
    expect(component.hiddenCharacterCount).toBe(1);
  });

  it('should indicate canEdit correctly', () => {
    component.isEditMode = false;
    component.isCreatingNew = false;
    expect(component.canEdit).toBe(false);

    component.isEditMode = true;
    expect(component.canEdit).toBe(true);

    component.isEditMode = false;
    component.isCreatingNew = true;
    expect(component.canEdit).toBe(true);
  });

  it('should check for expansion history', () => {
    const charWithHistory: Character = {
      ...mockActiveCharacters[0],
      aiExpansionHistory: [{
        date: new Date(),
        expansionType: 'personality_details',
        userPrompt: 'Test',
        aiGeneratedContent: { section: 'test', addedDetails: 'test' }
      }]
    };

    component.selectedCharacter = charWithHistory;
    expect(component.hasExpansionHistory).toBe(true);

    component.selectedCharacter = mockActiveCharacters[0];
    expect(component.hasExpansionHistory).toBe(false);
  });
});
