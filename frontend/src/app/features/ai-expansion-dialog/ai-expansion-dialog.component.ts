import { Component, Inject, OnInit } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Character, AIExpansionRecord } from '../../shared/models';
import { ApiService } from '../../core/services/api.service';
import { CharacterService } from '../../core/services/character.service';

export interface AIExpansionDialogData {
  storyId: string;
  character: Character;
  section: string;
}

@Component({
  selector: 'app-ai-expansion-dialog',
  templateUrl: './ai-expansion-dialog.component.html',
  styleUrls: ['./ai-expansion-dialog.component.scss']
})
export class AiExpansionDialogComponent implements OnInit {
  expansionForm: FormGroup;
  isGenerating = false;
  generatedContent: string = '';
  currentContent: string = '';
  showPreview = false;

  sectionLabels: { [key: string]: string } = {
    personality: 'Personality Traits',
    background: 'Background',
    relationships: 'Relationships',
    traits: 'Character Traits',
    other: 'Character Details'
  };

  constructor(
    public dialogRef: MatDialogRef<AiExpansionDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: AIExpansionDialogData,
    private fb: FormBuilder,
    private apiService: ApiService,
    private characterService: CharacterService
  ) {
    this.expansionForm = this.fb.group({
      expansionPrompt: ['', [Validators.required, Validators.minLength(10)]]
    });
  }

  ngOnInit(): void {
    this.loadCurrentContent();
  }

  private loadCurrentContent(): void {
    const { character, section } = this.data;

    switch (section) {
      case 'personality':
        this.currentContent = this.formatPersonalityTraits(character);
        break;
      case 'background':
        this.currentContent = character.background || '';
        break;
      case 'relationships':
        this.currentContent = this.formatRelationships(character);
        break;
      case 'traits':
        this.currentContent = this.formatTraits(character);
        break;
      default:
        this.currentContent = '';
    }
  }

  private formatPersonalityTraits(character: Character): string {
    const traits = [];
    if (character.personality.coreTraits.length > 0) {
      traits.push(`Core Traits: ${character.personality.coreTraits.join(', ')}`);
    }
    if (character.personality.emotionalPatterns.length > 0) {
      traits.push(`Emotional Patterns: ${character.personality.emotionalPatterns.join(', ')}`);
    }
    if (character.personality.speechPatterns.length > 0) {
      traits.push(`Speech Patterns: ${character.personality.speechPatterns.join(', ')}`);
    }
    if (character.personality.motivations.length > 0) {
      traits.push(`Motivations: ${character.personality.motivations.join(', ')}`);
    }
    return traits.join('\n');
  }

  private formatRelationships(character: Character): string {
    const relationships = character.currentState?.relationships || {};
    const entries = Object.entries(relationships);
    if (entries.length === 0) {
      return 'No relationships defined yet.';
    }
    return entries.map(([charId, rel]) =>
      `${charId}: ${rel.perception} (Trust: ${rel.trustLevel})`
    ).join('\n');
  }

  private formatTraits(character: Character): string {
    return character.personality.coreTraits.join(', ');
  }

  onGenerateExpansion(): void {
    if (!this.expansionForm.valid) {
      return;
    }

    this.isGenerating = true;
    const prompt = this.expansionForm.value.expansionPrompt;
    const { character, section } = this.data;

    const expansionRequest = {
      character: {
        name: character.name,
        role: character.role,
        currentContent: this.currentContent,
        personality: character.personality,
        background: character.background
      },
      section: section,
      userPrompt: prompt
    };

    this.apiService.generateCharacterExpansion(expansionRequest).subscribe({
      next: (response) => {
        if (response?.success && response.data?.expandedContent) {
          this.generatedContent = response.data.expandedContent;
          this.showPreview = true;
        } else {
          this.generatedContent = 'Error generating expansion. Please try again.';
          this.showPreview = true;
        }
        this.isGenerating = false;
      },
      error: (error) => {
        console.error('Error generating character expansion:', error);
        this.generatedContent = 'Error generating expansion. Please try again.';
        this.showPreview = true;
        this.isGenerating = false;
      }
    });
  }

  onAccept(): void {
    if (!this.generatedContent) {
      return;
    }

    const expansionRecord: AIExpansionRecord = {
      date: new Date(),
      expansionType: this.mapSectionToExpansionType(this.data.section),
      userPrompt: this.expansionForm.value.expansionPrompt,
      aiGeneratedContent: {
        section: this.data.section,
        addedDetails: this.generatedContent
      }
    };

    // Add expansion record to character
    const success = this.characterService.addExpansionRecord(
      this.data.storyId,
      this.data.character.id,
      expansionRecord
    );

    if (success) {
      // Update character with expanded content
      this.updateCharacterWithExpansion();
      this.dialogRef.close(true);
    } else {
      console.error('Failed to add expansion record');
    }
  }

  private updateCharacterWithExpansion(): void {
    const { character, section } = this.data;
    const updates: Partial<Character> = {};

    switch (section) {
      case 'background':
        updates.background = this.generatedContent;
        break;
      case 'personality':
      case 'traits':
        // Parse the generated content to extract traits
        // This is a simplified version - in production, you'd have more sophisticated parsing
        updates.personality = this.parseExpandedPersonality(this.generatedContent, character);
        break;
      // Add more cases as needed
    }

    if (Object.keys(updates).length > 0) {
      this.characterService.updateCharacter(this.data.storyId, character.id, updates);
    }
  }

  private parseExpandedPersonality(content: string, character: Character): any {
    // This is a placeholder - implement actual parsing logic based on your needs
    // For now, just return existing personality with a note that content was expanded
    return {
      ...character.personality,
      // Could parse content here to extract new traits
    };
  }

  private mapSectionToExpansionType(section: string): AIExpansionRecord['expansionType'] {
    const mapping: { [key: string]: AIExpansionRecord['expansionType'] } = {
      'personality': 'personality_details',
      'background': 'background',
      'relationships': 'relationships',
      'traits': 'traits'
    };
    return mapping[section] || 'other';
  }

  onRegenerate(): void {
    this.showPreview = false;
    this.generatedContent = '';
    this.onGenerateExpansion();
  }

  onRequestAlternative(): void {
    this.onRegenerate();
  }

  onEditBeforeAccepting(): void {
    // This would open an editor - for now, just accept
    this.onAccept();
  }

  onCancel(): void {
    this.dialogRef.close(false);
  }

  get sectionLabel(): string {
    return this.sectionLabels[this.data.section] || 'Character Details';
  }
}
