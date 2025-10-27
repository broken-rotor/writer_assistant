// Story Model matching new simplified requirements

export interface SystemPrompts {
  mainPrefix: string;
  mainSuffix: string;
  assistantPrompt: string;
  editorPrompt: string;
}

export interface GeneralConfig {
  title: string;
  systemPrompts: SystemPrompts;
  worldbuilding: string;
}

export interface Character {
  id: string;
  basicBio: string;
  name: string;
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
  metadata: {
    creationSource: 'user' | 'ai_generated' | 'imported';
    lastModified: Date;
  };
}

export interface Rater {
  id: string;
  name: string;
  systemPrompt: string;
  enabled: boolean;
  metadata: {
    created: Date;
    lastModified: Date;
  };
}

export interface Chapter {
  id: string;
  number: number;
  title: string;
  content: string;
  plotPoint: string;
  incorporatedFeedback: FeedbackItem[];
  metadata: {
    created: Date;
    lastModified: Date;
    wordCount: number;
  };
}

export interface FeedbackItem {
  source: string; // Character or rater name
  type: 'action' | 'dialog' | 'sensation' | 'emotion' | 'thought' | 'suggestion';
  content: string;
  incorporated: boolean;
}

export interface CharacterFeedback {
  characterName: string;
  actions: string[];
  dialog: string[];
  physicalSensations: string[];
  emotions: string[];
  internalMonologue: string[];
}

export interface RaterFeedback {
  raterName: string;
  opinion: string;
  suggestions: string[];
}

export interface EditorSuggestion {
  issue: string;
  suggestion: string;
  priority: 'high' | 'medium' | 'low';
  selected: boolean;
}

// ============================================================================
// THREE-PHASE CHAPTER COMPOSE DATA MODELS
// ============================================================================

/**
 * Represents a single message in a conversation thread
 */
export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  author?: string; // For system messages, could be 'character-feedback', 'rater-feedback', etc.
  parentMessageId?: string; // For branching conversations
  metadata?: {
    phase: 'plot_outline' | 'chapter_detail' | 'final_edit';
    messageIndex: number;
    branchId?: string;
    [key: string]: any;
  };
}

/**
 * Represents a conversation thread with branching support
 */
export interface ConversationThread {
  id: string;
  messages: ChatMessage[];
  currentBranchId: string;
  branches: Map<string, ConversationBranch>;
  metadata: {
    created: Date;
    lastModified: Date;
    phase: 'plot_outline' | 'chapter_detail' | 'final_edit';
  };
}

/**
 * Represents a branch in a conversation for alternative conversation paths
 */
export interface ConversationBranch {
  id: string;
  name: string;
  parentMessageId: string;
  messageIds: string[]; // Messages that belong to this branch
  isActive: boolean;
  metadata: {
    created: Date;
    description?: string;
  };
}

/**
 * Navigation state for managing conversation branches
 */
export interface BranchNavigation {
  currentBranchId: string;
  availableBranches: string[];
  branchHistory: string[]; // Stack of previously visited branches
  canNavigateBack: boolean;
  canNavigateForward: boolean;
}

/**
 * Represents an item in the plot outline
 */
export interface OutlineItem {
  id: string;
  type: 'chapter' | 'scene' | 'plot-point' | 'character-arc';
  title: string;
  description: string;
  order: number;
  parentId?: string; // For hierarchical structure
  children?: string[]; // Child outline item IDs
  status: 'draft' | 'reviewed' | 'approved';
  metadata: {
    created: Date;
    lastModified: Date;
    wordCountEstimate?: number;
  };
}

/**
 * Enhanced feedback item for sidebar feedback management
 */
export interface EnhancedFeedbackItem extends FeedbackItem {
  id: string;
  phase: 'plot_outline' | 'chapter_detail' | 'final_edit';
  priority: 'high' | 'medium' | 'low';
  status: 'pending' | 'incorporated' | 'dismissed';
  conversationThreadId?: string; // Link to related conversation
  metadata: {
    created: Date;
    lastModified: Date;
    phase_context?: {
      current_phase: 'plot_outline' | 'chapter_detail' | 'final_edit';
      plot_outline: string;
      chapter_detail: string;
      final_edit: string;
    };
  };
}

/**
 * Review item for final phase review feedback
 */
export interface ReviewItem {
  id: string;
  type: 'grammar' | 'style' | 'consistency' | 'flow' | 'character' | 'plot';
  title: string;
  description: string;
  suggestion: string;
  priority: 'high' | 'medium' | 'low';
  status: 'pending' | 'accepted' | 'rejected' | 'modified';
  affectedText?: {
    startIndex: number;
    endIndex: number;
    originalText: string;
    suggestedText: string;
  };
  metadata: {
    created: Date;
    reviewer: string; // 'editor' | 'user' | character/rater name
    phase_context?: {
      current_phase: 'plot_outline' | 'chapter_detail' | 'final_edit';
      plot_outline: string;
      chapter_detail: string;
      final_edit: string;
    };
  };
}

/**
 * Phase 1: Plot Outline Phase State
 */
export interface PlotOutlinePhase {
  conversation: ConversationThread;
  outline: {
    items: Map<string, OutlineItem>;
    structure: string[]; // Ordered list of outline item IDs
    currentFocus?: string; // Currently focused outline item ID
  };
  draftSummary: string;
  status: 'active' | 'completed' | 'paused';
  progress: {
    completedItems: number;
    totalItems: number;
    lastActivity: Date;
  };
}

/**
 * Phase 2: Chapter Detailer Phase State
 */
export interface ChapterDetailerPhase {
  conversation: ConversationThread;
  chapterDraft: {
    content: string;
    title: string;
    plotPoint: string;
    wordCount: number;
    status: 'drafting' | 'reviewing' | 'completed';
  };
  feedbackIntegration: {
    pendingFeedback: EnhancedFeedbackItem[];
    incorporatedFeedback: EnhancedFeedbackItem[];
    feedbackRequests: Map<string, {
      status: 'pending' | 'generating' | 'ready';
      feedback: CharacterFeedback | RaterFeedback;
    }>;
  };
  status: 'active' | 'completed' | 'paused';
  progress: {
    feedbackIncorporated: number;
    totalFeedbackItems: number;
    lastActivity: Date;
  };
}

/**
 * Phase 3: Final Edit Phase State
 */
export interface FinalEditPhase {
  conversation: ConversationThread;
  finalChapter: {
    content: string;
    title: string;
    wordCount: number;
    version: number;
  };
  reviewSelection: {
    availableReviews: ReviewItem[];
    selectedReviews: string[]; // IDs of selected review items
    appliedReviews: string[]; // IDs of reviews that have been applied
  };
  editorReview?: {
    suggestions: EditorSuggestion[];
    userSelections: boolean[];
    overallAssessment: string;
  };
  status: 'active' | 'completed' | 'paused';
  progress: {
    reviewsApplied: number;
    totalReviews: number;
    lastActivity: Date;
  };
}

/**
 * Phase transition logic and validation
 */
export interface PhaseTransition {
  fromPhase: 'plot_outline' | 'chapter_detail' | 'final_edit';
  toPhase: 'plot_outline' | 'chapter_detail' | 'final_edit';
  canTransition: boolean;
  requirements: string[]; // List of requirements that must be met
  validationErrors: string[]; // Current validation errors preventing transition
  transitionData?: any; // Data to carry forward to next phase
}

/**
 * Main Chapter Compose State Container
 * Replaces ChapterCreationState with three-phase support
 */
export interface ChapterComposeState {
  // Phase Management
  currentPhase: 'plot_outline' | 'chapter_detail' | 'final_edit';
  phases: {
    plotOutline: PlotOutlinePhase;
    chapterDetailer: ChapterDetailerPhase;
    finalEdit: FinalEditPhase;
  };
  
  // Shared Context
  sharedContext: {
    chapterNumber: number;
    targetWordCount?: number;
    genre?: string;
    tone?: string;
    pov?: string;
  };
  
  // Navigation and State
  navigation: {
    phaseHistory: ('plot_outline' | 'chapter_detail' | 'final_edit')[];
    canGoBack: boolean;
    canGoForward: boolean;
    branchNavigation: BranchNavigation;
  };
  
  // Progress Tracking
  overallProgress: {
    currentStep: number;
    totalSteps: number;
    phaseCompletionStatus: {
      'plot_outline': boolean;
      'chapter_detail': boolean;
      'final_edit': boolean;
    };
    estimatedTimeRemaining?: number;
  };
  
  // Metadata
  metadata: {
    created: Date;
    lastModified: Date;
    version: string;
    migrationSource?: 'ChapterCreationState' | 'manual';
  };
}

// Legacy interface maintained for backward compatibility
export interface ChapterCreationState {
  plotPoint: string;
  incorporatedFeedback: FeedbackItem[];
  feedbackRequests: Map<string, {
    status: 'pending' | 'generating' | 'ready';
    feedback: CharacterFeedback | RaterFeedback;
  }>;
  generatedChapter?: {
    text: string;
    status: string;
    metadata: any;
  };
  editorReview?: {
    suggestions: EditorSuggestion[];
    userSelections: boolean[];
  };
}

export interface Story {
  id: string;
  general: GeneralConfig;
  characters: Map<string, Character>;
  raters: Map<string, Rater>;
  story: {
    summary: string;
    chapters: Chapter[];
  };
  // New three-phase chapter compose system (optional for gradual migration)
  chapterCompose?: ChapterComposeState;
  // Legacy chapter creation (required for backward compatibility)
  chapterCreation: ChapterCreationState;
  metadata: {
    version: string;
    created: Date;
    lastModified: Date;
    // Migration tracking
    migrationStatus?: 'pending' | 'in-progress' | 'completed' | 'failed';
    lastMigrationAttempt?: Date;
  };
}

export interface StoryListItem {
  id: string;
  title: string;
  lastModified: Date;
  chapterCount: number;
}

// API Request/Response types - Simplified structure for stateless backend
export interface CharacterFeedbackRequest {
  systemPrompts: {
    mainPrefix: string;
    mainSuffix: string;
  };
  worldbuilding: string;
  storySummary: string;
  previousChapters: Array<{
    number: number;
    title: string;
    content: string;
  }>;
  character: {
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
  };
  plotPoint: string;
}

export interface RaterFeedbackRequest {
  systemPrompts: {
    mainPrefix: string;
    mainSuffix: string;
  };
  raterPrompt: string;
  worldbuilding: string;
  storySummary: string;
  previousChapters: Array<{
    number: number;
    title: string;
    content: string;
  }>;
  plotPoint: string;
}

export interface GenerateChapterRequest {
  systemPrompts: {
    mainPrefix: string;
    mainSuffix: string;
    assistantPrompt: string;
  };
  worldbuilding: string;
  storySummary: string;
  previousChapters: Array<{
    number: number;
    title: string;
    content: string;
  }>;
  characters: Array<{
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
  }>;
  plotPoint: string;
  incorporatedFeedback: FeedbackItem[];
}

export interface ModifyChapterRequest {
  systemPrompts: {
    mainPrefix: string;
    mainSuffix: string;
    assistantPrompt: string;
  };
  worldbuilding: string;
  storySummary: string;
  previousChapters: Array<{
    number: number;
    title: string;
    content: string;
  }>;
  currentChapter: string;
  userRequest: string;
}

export interface EditorReviewRequest {
  systemPrompts: {
    mainPrefix: string;
    mainSuffix: string;
    editorPrompt: string;
  };
  worldbuilding: string;
  storySummary: string;
  previousChapters: Array<{
    number: number;
    title: string;
    content: string;
  }>;
  characters: Array<{
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
  }>;
  chapterToReview: string;
}

export interface FleshOutRequest {
  systemPrompts: {
    mainPrefix: string;
    mainSuffix: string;
  };
  worldbuilding: string;
  storySummary: string;
  textToFleshOut: string;
  context: string;
}

export interface GenerateCharacterDetailsRequest {
  systemPrompts: {
    mainPrefix: string;
    mainSuffix: string;
  };
  worldbuilding: string;
  storySummary: string;
  basicBio: string;
  existingCharacters: Array<{
    name: string;
    basicBio: string;
    relationships: string;
  }>;
}

// API Response types
export interface CharacterFeedbackResponse {
  characterName: string;
  feedback: {
    actions: string[];
    dialog: string[];
    physicalSensations: string[];
    emotions: string[];
    internalMonologue: string[];
  };
}

export interface RaterFeedbackResponse {
  raterName: string;
  feedback: {
    opinion: string;
    suggestions: Array<{
      issue: string;
      suggestion: string;
      priority: 'high' | 'medium' | 'low';
    }>;
  };
}

export interface GenerateChapterResponse {
  chapterText: string;
}

export interface ModifyChapterResponse {
  modifiedChapter: string;
  modifiedChapterText?: string; // For backward compatibility
  wordCount: number;
  changesSummary: string;
}

export interface EditorReviewResponse {
  overallAssessment: string;
  suggestions: EditorSuggestion[];
}

export interface FleshOutResponse {
  fleshedOutText: string;
}

export interface GenerateCharacterDetailsResponse {
  name: string;
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
}

// ============================================================================
// NEW API MODELS FOR THREE-PHASE CHAPTER COMPOSE SYSTEM (WRI-49)
// ============================================================================

/**
 * Phase context for API requests
 */
export interface ApiPhaseContext {
  previous_phase_output?: string;
  phase_specific_instructions?: string;
  conversation_history?: Array<{
    role: 'user' | 'assistant';
    content: string;
    timestamp?: string;
  }>;
  conversation_branch_id?: string;
}

/**
 * Enhanced API request interfaces with phase support
 */
export interface EnhancedCharacterFeedbackRequest extends CharacterFeedbackRequest {
  compose_phase?: 'plot_outline' | 'chapter_detail' | 'final_edit';
  phase_context?: ApiPhaseContext;
}

export interface EnhancedRaterFeedbackRequest extends RaterFeedbackRequest {
  compose_phase?: 'plot_outline' | 'chapter_detail' | 'final_edit';
  phase_context?: ApiPhaseContext;
}

export interface EnhancedGenerateChapterRequest extends GenerateChapterRequest {
  compose_phase?: 'plot_outline' | 'chapter_detail' | 'final_edit';
  phase_context?: ApiPhaseContext;
}

export interface EnhancedEditorReviewRequest extends EditorReviewRequest {
  compose_phase?: 'plot_outline' | 'chapter_detail' | 'final_edit';
  phase_context?: ApiPhaseContext;
}

/**
 * LLM Chat API models (separate from RAG)
 */
export interface LLMChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export interface LLMChatComposeContext {
  current_phase: 'plot_outline' | 'chapter_detail' | 'final_edit';
  story_context: {
    [key: string]: any;
  };
  chapter_draft?: string;
  conversation_branch_id?: string;
}

export interface LLMChatRequest {
  messages: LLMChatMessage[];
  agent_type: 'writer' | 'character' | 'editor';
  compose_context?: LLMChatComposeContext;
  system_prompts?: {
    mainPrefix?: string;
    mainSuffix?: string;
    assistantPrompt?: string;
    editorPrompt?: string;
  };
  max_tokens?: number;
  temperature?: number;
}

export interface LLMChatResponse {
  message: LLMChatMessage;
  agent_type: 'writer' | 'character' | 'editor';
  metadata: {
    [key: string]: any;
  };
}

/**
 * Phase Validation API models
 */
export interface PhaseTransitionRequest {
  from_phase: 'plot_outline' | 'chapter_detail' | 'final_edit';
  to_phase: 'plot_outline' | 'chapter_detail' | 'final_edit';
  phase_output: string;
  story_context: {
    [key: string]: any;
  };
}

export interface ValidationResult {
  criterion: string;
  passed: boolean;
  message: string;
  score?: number;
}

export interface PhaseTransitionResponse {
  valid: boolean;
  overall_score: number;
  validation_results: ValidationResult[];
  recommendations: string[];
  metadata: {
    [key: string]: any;
  };
}
