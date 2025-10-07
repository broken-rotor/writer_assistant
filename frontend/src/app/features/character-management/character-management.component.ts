import { Component, OnInit, Input } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Character } from '../../shared/models';
import { CharacterService } from '../../core/services/character.service';
import { AiExpansionDialogComponent } from '../ai-expansion-dialog/ai-expansion-dialog.component';

@Component({
  selector: 'app-character-management',
  templateUrl: './character-management.component.html',
  styleUrls: ['./character-management.component.scss']
})
export class CharacterManagementComponent implements OnInit {
  @Input() storyId!: string;

  activeCharacters: Character[] = [];
  hiddenCharacters: Character[] = [];
  selectedCharacter: Character | null = null;

  characterForm: FormGroup;
  isCreatingNew = false;
  isEditMode = false;

  constructor(
    private fb: FormBuilder,
    private characterService: CharacterService,
    private dialog: MatDialog,
    private snackBar: MatSnackBar
  ) {
    this.characterForm = this.fb.group({
      name: ['', [Validators.required, Validators.minLength(2)]],
      role: ['supporting', Validators.required],
      background: ['', Validators.minLength(10)],
      coreTraits: [''],
      emotionalPatterns: [''],
      speechPatterns: [''],
      motivations: ['']
    });
  }

  ngOnInit(): void {
    this.loadCharacters();
  }

  private loadCharacters(): void {
    this.activeCharacters = this.characterService.getActiveCharacters(this.storyId);
    this.hiddenCharacters = this.characterService.getHiddenCharacters(this.storyId);

    if (this.activeCharacters.length > 0 && !this.selectedCharacter) {
      this.selectedCharacter = this.activeCharacters[0];
      this.loadCharacterIntoForm(this.selectedCharacter);
    }
  }

  onSelectCharacter(character: Character): void {
    this.selectedCharacter = character;
    this.loadCharacterIntoForm(character);
    this.isCreatingNew = false;
    this.isEditMode = false;
  }

  private loadCharacterIntoForm(character: Character): void {
    this.characterForm.patchValue({
      name: character.name,
      role: character.role,
      background: character.background,
      coreTraits: character.personality.coreTraits.join(', '),
      emotionalPatterns: character.personality.emotionalPatterns.join(', '),
      speechPatterns: character.personality.speechPatterns.join(', '),
      motivations: character.personality.motivations.join(', ')
    });
  }

  onCreateNew(): void {
    this.isCreatingNew = true;
    this.isEditMode = true;
    this.selectedCharacter = null;
    this.characterForm.reset({
      role: 'supporting'
    });
  }

  onSaveCharacter(): void {
    if (!this.characterForm.valid) {
      this.snackBar.open('Please fill in all required fields', 'Close', { duration: 3000 });
      return;
    }

    const formValue = this.characterForm.value;
    const characterData: Partial<Character> = {
      name: formValue.name,
      role: formValue.role,
      background: formValue.background,
      personality: {
        coreTraits: this.parseCommaSeparated(formValue.coreTraits),
        emotionalPatterns: this.parseCommaSeparated(formValue.emotionalPatterns),
        speechPatterns: this.parseCommaSeparated(formValue.speechPatterns),
        motivations: this.parseCommaSeparated(formValue.motivations)
      }
    };

    if (this.isCreatingNew) {
      const newCharacter = this.characterService.addCharacter(this.storyId, characterData);
      if (newCharacter) {
        this.snackBar.open('Character created successfully', 'Close', { duration: 3000 });
        this.selectedCharacter = newCharacter;
        this.isCreatingNew = false;
        this.isEditMode = false;
        this.loadCharacters();
      } else {
        this.snackBar.open('Failed to create character', 'Close', { duration: 3000 });
      }
    } else if (this.selectedCharacter) {
      const success = this.characterService.updateCharacter(
        this.storyId,
        this.selectedCharacter.id,
        characterData
      );
      if (success) {
        this.snackBar.open('Character updated successfully', 'Close', { duration: 3000 });
        this.isEditMode = false;
        this.loadCharacters();
      } else {
        this.snackBar.open('Failed to update character', 'Close', { duration: 3000 });
      }
    }
  }

  onCancelEdit(): void {
    this.isEditMode = false;
    this.isCreatingNew = false;
    if (this.selectedCharacter) {
      this.loadCharacterIntoForm(this.selectedCharacter);
    }
  }

  onHideCharacter(character: Character): void {
    const confirmMessage = `Are you sure you want to hide ${character.name}? The character data will be preserved but excluded from future interactions.`;
    if (confirm(confirmMessage)) {
      const success = this.characterService.hideCharacter(this.storyId, character.id);
      if (success) {
        this.snackBar.open(`${character.name} has been hidden`, 'Close', { duration: 3000 });
        this.loadCharacters();

        // If the hidden character was selected, select another one
        if (this.selectedCharacter?.id === character.id) {
          this.selectedCharacter = this.activeCharacters.length > 0 ? this.activeCharacters[0] : null;
          if (this.selectedCharacter) {
            this.loadCharacterIntoForm(this.selectedCharacter);
          }
        }
      } else {
        this.snackBar.open('Failed to hide character', 'Close', { duration: 3000 });
      }
    }
  }

  onUnhideCharacter(character: Character): void {
    const success = this.characterService.unhideCharacter(this.storyId, character.id);
    if (success) {
      this.snackBar.open(`${character.name} has been restored`, 'Close', { duration: 3000 });
      this.loadCharacters();
    } else {
      this.snackBar.open('Failed to unhide character', 'Close', { duration: 3000 });
    }
  }

  onExpandWithAI(section: string): void {
    if (!this.selectedCharacter) {
      this.snackBar.open('Please select a character first', 'Close', { duration: 3000 });
      return;
    }

    const dialogRef = this.dialog.open(AiExpansionDialogComponent, {
      width: '600px',
      data: {
        storyId: this.storyId,
        character: this.selectedCharacter,
        section: section
      }
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        // Reload character data after expansion
        this.loadCharacters();
        const updatedCharacter = this.characterService.getCharacter(
          this.storyId,
          this.selectedCharacter!.id
        );
        if (updatedCharacter) {
          this.selectedCharacter = updatedCharacter;
          this.loadCharacterIntoForm(updatedCharacter);
        }
        this.snackBar.open('Character expanded successfully', 'Close', { duration: 3000 });
      }
    });
  }

  onEditMode(): void {
    this.isEditMode = true;
  }

  private parseCommaSeparated(value: string): string[] {
    if (!value) return [];
    return value.split(',').map(s => s.trim()).filter(s => s.length > 0);
  }

  get activeCharacterCount(): number {
    return this.activeCharacters.length;
  }

  get hiddenCharacterCount(): number {
    return this.hiddenCharacters.length;
  }

  get canEdit(): boolean {
    return this.isEditMode || this.isCreatingNew;
  }

  get hasExpansionHistory(): boolean {
    return (this.selectedCharacter?.aiExpansionHistory?.length ?? 0) > 0;
  }
}
