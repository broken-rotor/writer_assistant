import { SelectedResponse } from './dialog.model';

export interface Story {
  id: string;
  title: string;
  genre: string;
  length: 'short_story' | 'novella' | 'novel';
  theme?: string;
  style: string;
  focusAreas: string[];
  createdAt: Date;
  lastModified: Date;
  currentPhase: 'draft' | 'character_dialog' | 'detailed_content' | 'refinement' | 'completed';
  progress?: number;
  storageSize?: number;
  currentDraft?: StoryDraft | null;
  finalContent?: any;
  characters?: Character[];
  conversationHistory?: any[];
  refinementHistory?: any[];
  selectedResponses?: SelectedResponse[];
}

export interface StoryDraft {
  title: string;
  outline: Chapter[];
  characters: Character[];
  themes: string[];
  metadata: GenerationMetadata;
}

export interface Chapter {
  id: string;
  number: number;
  title: string;
  summary: string;
  content?: string;
  keyEvents: string[];
  charactersPresent: string[];
  wordCount?: number;
}

export interface Character {
  id: string;
  name: string;
  role: 'protagonist' | 'antagonist' | 'supporting' | 'minor';
  personality: PersonalityTraits;
  background: string;
  currentState: CharacterState;
  memorySize: number;
  isHidden: boolean;
  creationSource: 'user_defined' | 'ai_generated';
  aiExpansionHistory: AIExpansionRecord[];
}

export interface AIExpansionRecord {
  date: Date;
  expansionType: 'personality_details' | 'background' | 'relationships' | 'traits' | 'other';
  userPrompt: string;
  aiGeneratedContent: {
    section: string;
    addedDetails: string;
  };
}

export interface PersonalityTraits {
  coreTraits: string[];
  emotionalPatterns: string[];
  speechPatterns: string[];
  motivations: string[];
}

export interface CharacterState {
  emotionalState: string;
  activeGoals: string[];
  currentKnowledge: string[];
  relationships: { [characterId: string]: RelationshipStatus };
}

export interface RelationshipStatus {
  perception: string;
  trustLevel: number;
  emotionalResponse: string;
  lastInteraction: string;
}

export interface GenerationMetadata {
  timestamp: Date;
  requestId: string;
  processingTime: number;
  model: string;
}

export interface StoryInput {
  theme: string;
  genre: string;
  length: 'short_story' | 'novella' | 'novel';
  style: string;
  focusAreas: string[];
}