/**
 * Structured Request Models
 * 
 * Defines interfaces for structured context requests that separate
 * individual context elements for improved context management.
 */

// ============================================================================
// STRUCTURED CONTEXT ELEMENTS
// ============================================================================

/**
 * Structured system prompts context
 */
export interface StructuredSystemPrompts {
  mainPrefix: string;
  mainSuffix: string;
  assistantPrompt?: string;
  editorPrompt?: string;
}

/**
 * Structured worldbuilding context
 */
export interface StructuredWorldbuilding {
  content: string;
  lastModified?: Date;
  wordCount?: number;
}

/**
 * Structured story summary context
 */
export interface StructuredStorySummary {
  summary: string;
  lastModified?: Date;
  wordCount?: number;
}

/**
 * Structured character context
 */
export interface StructuredCharacterContext {
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
  isHidden?: boolean;
}

/**
 * Structured chapter context
 */
export interface StructuredChapterContext {
  number: number;
  title: string;
  content: string;
  plotPoint?: string;
  wordCount?: number;
}

/**
 * Structured plot context
 */
export interface StructuredPlotContext {
  plotPoint: string;
  plotOutline?: string;
  plotOutlineStatus?: 'draft' | 'under_review' | 'approved' | 'needs_revision';
  relatedOutlineItems?: {
    title: string;
    description: string;
    order: number;
  }[];
}

/**
 * Structured feedback context
 */
export interface StructuredFeedbackContext {
  incorporatedFeedback: {
    source: string;
    type: 'action' | 'dialog' | 'sensation' | 'emotion' | 'thought' | 'suggestion';
    content: string;
    incorporated: boolean;
  }[];
  pendingFeedback?: {
    source: string;
    type: string;
    content: string;
  }[];
}

/**
 * Structured user request context
 */
export interface StructuredUserRequest {
  request: string;
  requestType: 'generation' | 'modification' | 'feedback' | 'review' | 'continuation';
  priority?: 'high' | 'medium' | 'low';
  additionalInstructions?: string;
}

/**
 * Structured phase context for three-phase system
 */
export interface StructuredPhaseContext {
  currentPhase: 'plot_outline' | 'chapter_detail' | 'final_edit';
  previousPhaseOutput?: string;
  phaseSpecificInstructions?: string;
  conversationHistory?: {
    role: 'user' | 'assistant';
    content: string;
    timestamp?: string;
  }[];
  conversationBranchId?: string;
}

// ============================================================================
// STRUCTURED REQUEST INTERFACES
// ============================================================================

/**
 * Base structured request interface
 */
export interface BaseStructuredRequest {
  systemPrompts: StructuredSystemPrompts;
  worldbuilding: StructuredWorldbuilding;
  storySummary: StructuredStorySummary;
  previousChapters: StructuredChapterContext[];
  requestMetadata?: {
    requestId?: string;
    timestamp?: Date;
    requestSource?: string;
    optimizationHints?: string[];
  };
}

/**
 * Structured character feedback request
 */
export interface StructuredCharacterFeedbackRequest extends BaseStructuredRequest {
  character: StructuredCharacterContext;
  plotContext: StructuredPlotContext;
  phaseContext?: StructuredPhaseContext;
}

/**
 * Structured rater feedback request
 */
export interface StructuredRaterFeedbackRequest extends BaseStructuredRequest {
  raterPrompt: string;
  raterName?: string;
  plotContext: StructuredPlotContext;
  phaseContext?: StructuredPhaseContext;
}

/**
 * Structured chapter generation request
 */
export interface StructuredGenerateChapterRequest extends BaseStructuredRequest {
  characters: StructuredCharacterContext[];
  plotContext: StructuredPlotContext;
  feedbackContext: StructuredFeedbackContext;
  phaseContext?: StructuredPhaseContext;
}

/**
 * Structured chapter modification request
 */
export interface StructuredModifyChapterRequest extends BaseStructuredRequest {
  currentChapter: string;
  userRequest: StructuredUserRequest;
  characters?: StructuredCharacterContext[];
  phaseContext?: StructuredPhaseContext;
}

/**
 * Structured editor review request
 */
export interface StructuredEditorReviewRequest extends BaseStructuredRequest {
  characters: StructuredCharacterContext[];
  chapterToReview: string;
  reviewFocus?: string[];
  phaseContext?: StructuredPhaseContext;
}

// ============================================================================
// REQUEST VALIDATION INTERFACES
// ============================================================================

/**
 * Validation error for structured requests
 */
export interface StructuredRequestValidationError {
  field: string;
  message: string;
  severity: 'error' | 'warning' | 'info';
  code?: string;
}

/**
 * Validation result for structured requests
 */
export interface StructuredRequestValidationResult {
  isValid: boolean;
  errors: StructuredRequestValidationError[];
  warnings: StructuredRequestValidationError[];
  optimizationSuggestions?: string[];
}

// ============================================================================
// REQUEST CONVERSION INTERFACES
// ============================================================================

/**
 * Request format detection result
 */
export interface RequestFormatDetectionResult {
  format: 'traditional' | 'structured' | 'enhanced' | 'unknown';
  confidence: number;
  detectedFeatures: string[];
}

/**
 * Request conversion options
 */
export interface RequestConversionOptions {
  preserveMetadata?: boolean;
  addOptimizationHints?: boolean;
  validateAfterConversion?: boolean;
  includePhaseContext?: boolean;
}

/**
 * Request conversion result
 */
export interface RequestConversionResult<T> {
  success: boolean;
  convertedRequest?: T;
  originalFormat: string;
  targetFormat: string;
  errors?: StructuredRequestValidationError[];
  warnings?: StructuredRequestValidationError[];
  metadata?: {
    conversionTime: number;
    dataLoss?: string[];
    optimizationsApplied?: string[];
  };
}

// ============================================================================
// RESPONSE ENHANCEMENT INTERFACES
// ============================================================================

/**
 * Enhanced response metadata for structured requests
 */
export interface StructuredResponseMetadata {
  requestId?: string;
  processingTime?: number;
  contextValidation?: {
    systemPrompts: boolean;
    worldbuilding: boolean;
    characters: boolean;
    plotContext: boolean;
  };
  optimizationsApplied?: string[];
  tokenUsage?: {
    inputTokens: number;
    outputTokens: number;
    totalTokens: number;
  };
  cacheHits?: string[];
}

/**
 * Enhanced character feedback response
 */
export interface StructuredCharacterFeedbackResponse {
  characterName: string;
  feedback: {
    actions: string[];
    dialog: string[];
    physicalSensations: string[];
    emotions: string[];
    internalMonologue: string[];
    goals: string[];
    memories: string[];
    subtext: string[];
  };
  metadata?: StructuredResponseMetadata;
}

/**
 * Enhanced rater feedback response
 */
export interface StructuredRaterFeedbackResponse {
  raterName: string;
  feedback: {
    opinion: string;
    suggestions: {
      issue: string;
      suggestion: string;
      priority: 'high' | 'medium' | 'low';
    }[];
  };
  context_metadata?: StructuredResponseMetadata;
}

/**
 * Enhanced chapter generation response
 */
export interface StructuredGenerateChapterResponse {
  chapterText: string;
  metadata?: StructuredResponseMetadata;
}

/**
 * Enhanced chapter modification response
 */
export interface StructuredModifyChapterResponse {
  modifiedChapter: string;
  wordCount: number;
  changesSummary: string;
  metadata?: StructuredResponseMetadata;
}

/**
 * Enhanced editor review response
 */
export interface StructuredEditorReviewResponse {
  overallAssessment: string;
  suggestions: {
    issue: string;
    suggestion: string;
    priority: 'high' | 'medium' | 'low';
    selected: boolean;
  }[];
  metadata?: StructuredResponseMetadata;
}
