/**
 * Context Builder Models
 * 
 * Defines structured context element types for the ContextBuilderService.
 * These interfaces ensure type safety and clear contracts between frontend
 * components and the backend API.
 */

import { FeedbackItem } from './story.model';

// ============================================================================
// CORE CONTEXT ELEMENT INTERFACES
// ============================================================================

/**
 * System prompts context for AI generation
 */
export interface SystemPromptsContext {
  mainPrefix: string;
  mainSuffix: string;
  assistantPrompt: string;
}

/**
 * Worldbuilding context containing story universe information
 */
export interface WorldbuildingContext {
  content: string;
  isValid: boolean;
  wordCount: number;
  lastUpdated: Date;
}

/**
 * Story summary context
 */
export interface StorySummaryContext {
  summary: string;
  isValid: boolean;
  wordCount: number;
  lastUpdated: Date;
}

/**
 * Character context for story generation
 */
export interface CharacterContext {
  characters: StructuredCharacter[];
  totalCharacters: number;
  visibleCharacters: number;
  lastUpdated: Date;
}

export interface StructuredCharacter {
  name: string;
  basicBio: string;
  sex: string;
  gender: string;
  sexualPreference: string;
  age: number;
  physicalAppearance: string;
  usualClothing: string;
  personality: string;
  motivations: string;
  fears: string;
  relationships: string;
  isHidden: boolean;
}

/**
 * Previous chapters context
 */
export interface ChaptersContext {
  chapters: StructuredChapter[];
  totalChapters: number;
  totalWordCount: number;
  lastUpdated: Date;
}

export interface StructuredChapter {
  number: number;
  title: string;
  content: string;
  wordCount: number;
  created: Date;
}

/**
 * Plot context for current chapter/scene
 */
export interface PlotContext {
  plotPoint: string;
  isValid: boolean;
  wordCount: number;
  lastUpdated: Date;
}

/**
 * Feedback context for incorporation into generation
 */
export interface FeedbackContext {
  incorporatedFeedback: FeedbackItem[];
  selectedFeedback: FeedbackItem[];
  totalFeedbackItems: number;
  lastUpdated: Date;
}

/**
 * Conversation context from chat interactions
 */
export interface ConversationContext {
  messages: StructuredMessage[];
  branchId: string;
  totalMessages: number;
  recentMessages: StructuredMessage[];
  lastUpdated: Date;
}

export interface StructuredMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  messageId?: string;
}

// ============================================================================
// COMPOSITE CONTEXT INTERFACES
// ============================================================================

/**
 * Complete context bundle for chapter generation
 */
export interface ChapterGenerationContext {
  systemPrompts: SystemPromptsContext;
  worldbuilding: WorldbuildingContext;
  storySummary: StorySummaryContext;
  characters: CharacterContext;
  previousChapters: ChaptersContext;
  plotPoint: PlotContext;
  feedback: FeedbackContext;
  conversation?: ConversationContext;
}

/**
 * Context bundle for chapter modification
 */
export interface ChapterModificationContext {
  systemPrompts: SystemPromptsContext;
  worldbuilding: WorldbuildingContext;
  storySummary: StorySummaryContext;
  characters: CharacterContext;
  previousChapters: ChaptersContext;
  currentChapter: string;
  userRequest: string;
  conversation?: ConversationContext;
}

/**
 * Context bundle for feedback requests
 */
export interface FeedbackRequestContext {
  systemPrompts: SystemPromptsContext;
  worldbuilding: WorldbuildingContext;
  storySummary: StorySummaryContext;
  characters: CharacterContext;
  previousChapters: ChaptersContext;
  currentContent: string;
  targetAgent: {
    id: string;
    type: 'character' | 'rater';
    name: string;
  };
}

// ============================================================================
// VALIDATION AND ERROR HANDLING
// ============================================================================

/**
 * Context validation result
 */
export interface ContextValidationResult {
  isValid: boolean;
  errors: ContextValidationError[];
  warnings: ContextValidationWarning[];
}

export interface ContextValidationError {
  field: string;
  message: string;
  severity: 'error' | 'warning';
}

export interface ContextValidationWarning {
  field: string;
  message: string;
  suggestion?: string;
}

/**
 * Context building options
 */
export interface ContextBuildOptions {
  useCache?: boolean;
  validateData?: boolean;
  includeOptionalFields?: boolean;
  maxCacheAge?: number; // in milliseconds
}

/**
 * Context cache entry
 */
export interface ContextCacheEntry<T> {
  data: T;
  timestamp: Date;
  storyVersion: string;
  isValid: boolean;
}

// ============================================================================
// SERVICE RESPONSE TYPES
// ============================================================================

/**
 * Context builder service response
 */
export interface ContextBuilderResponse<T> {
  success: boolean;
  data?: T;
  errors?: ContextValidationError[];
  warnings?: ContextValidationWarning[];
  fromCache?: boolean;
  cacheAge?: number;
}

/**
 * Context element optimization settings
 */
export interface ContextOptimizationSettings {
  maxCharacters?: number;
  maxMessages?: number;
  maxFeedbackItems?: number;
  prioritizeRecent?: boolean;
  includeMetadata?: boolean;
}
