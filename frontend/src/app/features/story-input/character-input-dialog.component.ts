import { Component } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatDialogRef } from '@angular/material/dialog';

@Component({
  selector: 'app-character-input-dialog',
  template: `
    <h2 mat-dialog-title>Add Character</h2>
    <mat-dialog-content>
      <form [formGroup]="characterForm" class="character-form">
        <mat-form-field appearance="outline" class="full-width">
          <mat-label>Name</mat-label>
          <input matInput formControlName="name" placeholder="Character name">
          <mat-error *ngIf="characterForm.get('name')?.hasError('required')">
            Name is required
          </mat-error>
        </mat-form-field>

        <mat-form-field appearance="outline" class="full-width">
          <mat-label>Role</mat-label>
          <mat-select formControlName="role">
            <mat-option value="protagonist">Protagonist</mat-option>
            <mat-option value="antagonist">Antagonist</mat-option>
            <mat-option value="supporting">Supporting</mat-option>
            <mat-option value="minor">Minor</mat-option>
          </mat-select>
        </mat-form-field>

        <mat-form-field appearance="outline" class="full-width">
          <mat-label>Background (Optional)</mat-label>
          <textarea matInput formControlName="background" rows="3"
                    placeholder="Brief character background..."></textarea>
        </mat-form-field>

        <mat-form-field appearance="outline" class="full-width">
          <mat-label>Core Traits (Optional, comma-separated)</mat-label>
          <input matInput formControlName="coreTraits"
                 placeholder="e.g., brave, curious, analytical">
        </mat-form-field>
      </form>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button (click)="onCancel()">Cancel</button>
      <button mat-raised-button color="primary"
              [disabled]="!characterForm.valid"
              (click)="onSave()">
        Add Character
      </button>
    </mat-dialog-actions>
  `,
  styles: [`
    .character-form {
      display: flex;
      flex-direction: column;
      gap: 16px;
      min-width: 400px;
      padding: 16px 0;
    }
    .full-width {
      width: 100%;
    }
  `]
})
export class CharacterInputDialogComponent {
  characterForm: FormGroup;

  constructor(
    private fb: FormBuilder,
    private dialogRef: MatDialogRef<CharacterInputDialogComponent>
  ) {
    this.characterForm = this.fb.group({
      name: ['', [Validators.required, Validators.minLength(2)]],
      role: ['supporting', Validators.required],
      background: [''],
      coreTraits: ['']
    });
  }

  onSave(): void {
    if (this.characterForm.valid) {
      const formValue = this.characterForm.value;
      const traits = formValue.coreTraits
        ? formValue.coreTraits.split(',').map((t: string) => t.trim()).filter((t: string) => t)
        : [];

      this.dialogRef.close({
        name: formValue.name,
        role: formValue.role,
        background: formValue.background,
        coreTraits: traits
      });
    }
  }

  onCancel(): void {
    this.dialogRef.close();
  }
}
