/**
 * Story Model for Writer Assistant - Three-Phase Chapter Compose System
 * 
 * This file contains the complete data model for the new three-phase chapter composition system,
 * which replaces the previous single-phase chapter creation workflow.
 * 
 * SYSTEM OVERVIEW:
 * ================
 * The three-phase system provides a structured approach to chapter creation:
 * 
 * Phase 1 - Plot Outline: 
 *   - Collaborative outline building through chat interface
 *   - AI-assisted plot point development and refinement
 *   - Character involvement planning and scene structuring
 *   - Feedback integration from story context
 * 
 * Phase 2 - Chapter Detailer:
 *   - Detailed chapter content generation based on approved outline
 *   - Real-time feedback from character and rater agents in sidebar
 *   - Multiple draft iterations with feedback integration
 *   - Conversation-driven content refinement
 * 
 * Phase 3 - Final Edit:
 *   - Final review and polishing of chapter content
 *   - Editor agent suggestions and user selection process
 *   - Multiple final draft options with comparison capabilities
 *   - Publication-ready output generation
 * 
 * KEY FEATURES:
 * =============
 * - Chat-Style Interactions: Each phase uses conversational UI for natural interaction
 * - Branching Conversations: Users can explore different approaches by creating conversation branches
 * - Phase-Specific Data Isolation: Each phase maintains its own state while sharing necessary context
 * - Backward Compatibility: Legacy ChapterCreationState is preserved during migration
 * - Progress Tracking: Comprehensive progress and metadata tracking across all phases
 * - Migration Support: Utilities for transitioning from legacy single-phase system
 * 
 * USAGE PATTERNS:
 * ===============
 * 1. Create new ChapterComposeState for new chapters
 * 2. Use migration utilities for existing ChapterCreationState data
 * 3. Navigate between phases using PhaseTransition validation
 * 4. Create conversation branches for exploring alternatives
 * 5. Integrate feedback through phase-specific mechanisms
 * 
 * MIGRATION STRATEGY:
 * ===================
 * - Legacy ChapterCreationState remains available during transition
 * - Migration utilities in migration.model.ts handle data transformation
 * - Story interface supports both old and new systems simultaneously
 * - Gradual migration allows testing and validation before full transition
 */

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

// ============================================================================
// SUPPORTING DATA MODELS
// ============================================================================

/**
 * Represents an item in the plot outline
 * Used in Phase 1 for building chapter structure
 */
export interface OutlineItem {
  id: string;
  order: number;
  title: string;
  description: string;
  type: 'scene' | 'dialogue' | 'action' | 'transition' | 'climax' | 'resolution';
  estimatedWordCount?: number;
  characterInvolvement: string[]; // Character names involved in this outline item
  plotRelevance: 'high' | 'medium' | 'low';
  metadata: {
    created: Date;
    lastModified: Date;
    source: 'user' | 'ai_generated' | 'collaborative';
  };
}

/**
 * Enhanced feedback item for the three-phase system
 * Supports more detailed feedback with phase context
 * Maintains backward compatibility with legacy FeedbackItem usage
 */
export interface FeedbackItem {
  id?: string; // Optional for backward compatibility
  source: string; // Character or rater name
  type: 'action' | 'dialog' | 'sensation' | 'emotion' | 'thought' | 'suggestion' | 'structural' | 'pacing';
  content: string;
  incorporated: boolean;
  phase?: 'plotOutline' | 'chapterDetailer' | 'finalEdit'; // Optional for backward compatibility
  priority?: 'high' | 'medium' | 'low'; // Optional for backward compatibility
  targetSection?: string; // Which part of the content this feedback applies to
  metadata?: { // Optional for backward compatibility
    created: Date;
    incorporatedAt?: Date;
    relatedMessageId?: string; // Link to conversation message that generated this feedback
  };
}

/**
 * Review item for Phase 3 final review process
 * Represents specific review points and user decisions
 */
export interface ReviewItem {
  id: string;
  category: 'character_consistency' | 'plot_coherence' | 'pacing' | 'dialogue' | 'description' | 'overall_quality';
  issue: string;
  suggestion: string;
  severity: 'critical' | 'important' | 'minor' | 'suggestion';
  status: 'pending' | 'addressed' | 'dismissed' | 'deferred';
  userNotes?: string;
  metadata: {
    created: Date;
    reviewedAt?: Date;
    source: 'editor_agent' | 'user' | 'automated_check';
  };
}

/**
 * Manages phase transitions and validation
 * Ensures proper flow between the three phases
 */
export interface PhaseTransition {
  fromPhase: 'plotOutline' | 'chapterDetailer' | 'finalEdit';
  toPhase: 'plotOutline' | 'chapterDetailer' | 'finalEdit';
  canTransition: boolean;
  requirements: Array<{
    requirement: string;
    satisfied: boolean;
    description: string;
  }>;
  transitionData?: {
    // Data to carry forward to the next phase
    outlineItems?: OutlineItem[];
    selectedDraft?: string;
    criticalFeedback?: FeedbackItem[];
  };
  metadata: {
    lastChecked: Date;
    transitionedAt?: Date;
  };
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
 * Supports branching conversations with parent/child relationships
 */
export interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  timestamp: Date;
  parentMessageId?: string; // For branching - which message this branches from
  branchId: string; // Which conversation branch this message belongs to
  metadata: {
    messageType: 'text' | 'feedback' | 'suggestion' | 'outline_item' | 'review';
    source?: string; // Character name, rater name, or 'user'
    isEdited: boolean;
    editHistory?: Array<{
      content: string;
      timestamp: Date;
    }>;
  };
}

/**
 * Represents a branch in a conversation
 * Allows users to explore different conversation paths
 */
export interface ConversationBranch {
  id: string;
  name: string; // User-friendly name for the branch
  parentBranchId?: string; // Which branch this was created from
  branchPointMessageId: string; // The message where this branch started
  isActive: boolean; // Currently selected branch
  created: Date;
  lastModified: Date;
}

/**
 * Manages a complete conversation thread with branching support
 * Contains all messages and branches for a conversation
 */
export interface ConversationThread {
  id: string;
  title: string;
  messages: Map<string, ChatMessage>; // messageId -> ChatMessage
  branches: Map<string, ConversationBranch>; // branchId -> ConversationBranch
  currentBranchId: string; // Currently active branch
  rootMessageId: string; // First message in the conversation
  metadata: {
    created: Date;
    lastModified: Date;
    totalMessages: number;
    totalBranches: number;
  };
}

/**
 * Navigation utilities for managing conversation branches
 */
export interface BranchNavigation {
  currentBranchId: string;
  availableBranches: string[]; // Branch IDs that can be navigated to
  branchHistory: string[]; // Recently visited branches
  canCreateBranch: boolean;
  canMergeBranches: boolean;
}

// ============================================================================
// PHASE-SPECIFIC DATA MODELS
// ============================================================================

/**
 * Phase 1: Plot Outline Phase
 * Focuses on building and refining the chapter outline through conversation
 */
export interface PlotOutlinePhase {
  conversation: ConversationThread;
  draftOutline: OutlineItem[];
  outlineHistory: Array<{
    version: number;
    outline: OutlineItem[];
    timestamp: Date;
    source: 'user' | 'ai_generated';
  }>;
  feedbackIntegration: {
    pendingFeedback: FeedbackItem[];
    integratedFeedback: FeedbackItem[];
    feedbackSources: string[]; // Character/rater names providing feedback
  };
  status: 'draft' | 'refining' | 'ready_for_next_phase';
  metadata: {
    startedAt: Date;
    lastModified: Date;
    iterationCount: number;
  };
}

/**
 * Phase 2: Chapter Detailer Phase  
 * Focuses on developing detailed chapter content with integrated feedback
 */
export interface ChapterDetailerPhase {
  conversation: ConversationThread;
  chapterDrafts: Array<{
    id: string;
    content: string;
    version: number;
    timestamp: Date;
    incorporatedFeedback: FeedbackItem[];
  }>;
  sidebarFeedback: {
    characterFeedback: Map<string, CharacterFeedback>;
    raterFeedback: Map<string, RaterFeedback>;
    feedbackStatus: Map<string, 'pending' | 'generating' | 'ready' | 'integrated'>;
  };
  currentDraftId?: string;
  status: 'drafting' | 'gathering_feedback' | 'integrating_feedback' | 'ready_for_review';
  metadata: {
    startedAt: Date;
    lastModified: Date;
    draftCount: number;
    feedbackRounds: number;
  };
}

/**
 * Phase 3: Final Edit Phase
 * Focuses on final review, selection, and polishing of the chapter
 */
export interface FinalEditPhase {
  conversation: ConversationThread;
  finalDrafts: Array<{
    id: string;
    content: string;
    title: string;
    source: 'phase2_output' | 'user_edited' | 'ai_refined';
    timestamp: Date;
  }>;
  reviewItems: ReviewItem[];
  selectedDraftId?: string;
  editorSuggestions: EditorSuggestion[];
  userSelections: Map<string, boolean>; // suggestionId -> selected
  status: 'reviewing' | 'editing' | 'finalizing' | 'completed';
  metadata: {
    startedAt: Date;
    lastModified: Date;
    reviewRounds: number;
    finalWordCount?: number;
  };
}

// ============================================================================
// MAIN CHAPTER COMPOSE STATE CONTAINER
// ============================================================================

/**
 * Main state container for the three-phase chapter compose system
 * Orchestrates all phases and manages overall chapter creation workflow
 */
export interface ChapterComposeState {
  // Phase Management
  currentPhase: 'plotOutline' | 'chapterDetailer' | 'finalEdit';
  phases: {
    plotOutline: PlotOutlinePhase;
    chapterDetailer: ChapterDetailerPhase;
    finalEdit: FinalEditPhase;
  };
  
  // Phase Transitions
  phaseTransitions: {
    toChapterDetailer: PhaseTransition;
    toFinalEdit: PhaseTransition;
    backToPlotOutline?: PhaseTransition; // Optional backward transition
    backToChapterDetailer?: PhaseTransition; // Optional backward transition
  };
  
  // Global Navigation
  branchNavigation: BranchNavigation;
  
  // Shared Data Across Phases
  sharedContext: {
    chapterNumber: number;
    chapterTitle?: string;
    targetWordCount?: number;
    selectedCharacters: string[]; // Character IDs involved in this chapter
    selectedRaters: string[]; // Rater IDs to use for feedback
    globalNotes: string; // User notes that apply across all phases
  };
  
  // Overall Progress Tracking
  progress: {
    overallStatus: 'not_started' | 'in_progress' | 'completed' | 'paused';
    completedPhases: Array<'plotOutline' | 'chapterDetailer' | 'finalEdit'>;
    currentPhaseProgress: number; // 0-100 percentage
    estimatedTimeRemaining?: number; // minutes
  };
  
  // Metadata
  metadata: {
    created: Date;
    lastModified: Date;
    version: string; // For data model versioning
    totalTimeSpent: number; // minutes
    sessionCount: number;
    lastSessionAt?: Date;
  };
}

/**
 * Legacy ChapterCreationState - maintained for backward compatibility
 * @deprecated Use ChapterComposeState instead
 */
export interface ChapterCreationState {
  plotPoint?: string; // Made optional for backward compatibility
  incorporatedFeedback?: FeedbackItem[]; // Made optional for backward compatibility
  feedbackRequests?: Map<string, {
    status: 'pending' | 'generating' | 'ready';
    feedback: CharacterFeedback | RaterFeedback;
  }>; // Made optional for backward compatibility
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

/**
 * Main Story interface - updated to support three-phase chapter compose system
 * 
 * Data Flow Overview:
 * 1. Plot Outline Phase: User and AI collaborate to create detailed chapter outline
 * 2. Chapter Detailer Phase: Generate chapter content with integrated feedback from characters/raters
 * 3. Final Edit Phase: Review, refine, and finalize the chapter for publication
 * 
 * Phase Transitions:
 * - Each phase must meet completion requirements before advancing
 * - Users can navigate backward to previous phases if needed
 * - Conversation threads maintain context across phase transitions
 * 
 * Branching Conversations:
 * - Each phase supports branching conversations for exploring different approaches
 * - Users can create branches at any message to try alternative directions
 * - Branch navigation allows switching between conversation paths
 * - Branches can be merged or kept separate based on user preference
 */
export interface Story {
  id: string;
  general: GeneralConfig;
  characters: Map<string, Character>;
  raters: Map<string, Rater>;
  story: {
    summary: string;
    chapters: Chapter[];
  };
  
  /** 
   * New three-phase chapter compose system
   * Replaces the legacy chapterCreation property
   * Optional during migration period
   */
  chapterCompose?: ChapterComposeState;
  
  /** 
   * Legacy chapter creation state - maintained for backward compatibility
   * @deprecated Use chapterCompose instead
   * Will be removed in future versions after migration is complete
   */
  chapterCreation?: ChapterCreationState;
  
  metadata: {
    version: string;
    created: Date;
    lastModified: Date;
    /** Indicates if this story has been migrated to the new three-phase system */
    migratedToThreePhase?: boolean;
    /** Migration timestamp if applicable */
    migrationDate?: Date;
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
