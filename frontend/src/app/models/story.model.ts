// Story Model matching new simplified requirements

import { RequestContext } from '../utils/context-transformer';

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
  worldbuildingChatHistory?: ChatMessage[];
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
  plotPoint?: string; // Overall plot/theme of the chapter
  keyPlotItems?: string[]; // Detailed story beats within the chapter
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
  goals: string[];
  memories: string[];
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

export interface PlotOutlineFeedback {
  raterId: string;
  raterName: string;
  feedback: string;
  status: 'pending' | 'generating' | 'complete' | 'error';
  timestamp: Date;
  userResponse?: 'accepted' | 'revision_requested' | 'discussed';
  conversationId?: string; // For follow-up discussions
}

export interface PlotOutline {
  content: string;
  status: 'draft' | 'under_review' | 'approved' | 'needs_revision';
  chatHistory: ChatMessage[];
  raterFeedback: Map<string, PlotOutlineFeedback>; // Key: raterId
  metadata: {
    created: Date;
    lastModified: Date;
    approvedAt?: Date;
    version: number;
    lastFeedbackRequest?: Date;
  };
}

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
  key_plot_items?: string[]; // Key plot items that occur in this chapter
  order: number;
  parentId?: string; // For hierarchical structure
  children?: string[]; // Child outline item IDs
  status: 'draft' | 'reviewed' | 'approved';
  involved_characters?: string[]; // List of character names involved in this chapter
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
  priority: 'high' | 'medium' | 'low';
  status: 'pending' | 'incorporated' | 'dismissed';
  conversationThreadId?: string; // Link to related conversation
  metadata: {
    created: Date;
    lastModified: Date;
  };
}

/**
 * Review item for review feedback
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
  plotOutline: PlotOutline;
  metadata: {
    version: string;
    created: Date;
    lastModified: Date;
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
  previousChapters: {
    number: number;
    title: string;
    content: string;
  }[];
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
  previousChapters: {
    number: number;
    title: string;
    content: string;
  }[];
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
  previousChapters: {
    number: number;
    title: string;
    content: string;
  }[];
  characters: {
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
  }[];
  plotPoint: string;
  incorporatedFeedback: FeedbackItem[];
}

export interface ModifyChapterRequest {
  chapter_number: number;
  userRequest: string;
  request_context: any; // RequestContext from context-transformer
}

export interface EditorReviewRequest {
  systemPrompts: {
    mainPrefix: string;
    mainSuffix: string;
    editorPrompt: string;
  };
  worldbuilding: string;
  storySummary: string;
  previousChapters: {
    number: number;
    title: string;
    content: string;
  }[];
  characters: {
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
  }[];
  chapterToReview: string;
}

export interface BackendEditorReviewRequest {
  chapter_number: number;
  request_context: RequestContext;
}

export interface BackendEditorSuggestion {
  issue: string;
  suggestion: string;
  priority: string; // "high", "medium", "low"
}

export interface BackendEditorReviewResponse {
  suggestions: BackendEditorSuggestion[];
}

export interface BackendGenerateChapterRequest {
  chapter_number: number;
  request_context: RequestContext;
}

export enum FleshOutType {
  WORLDBUILDING = 'worldbuilding',
  CHAPTER = 'chapter',
  PLOT_OUTLINE = 'plot_outline'
}

export interface FleshOutRequest {
  request_type: FleshOutType;
  text_to_flesh_out: string;
  request_context: RequestContext;
}

// Structured Context Models
export interface PlotElement {
  id?: string;
  type: 'scene' | 'conflict' | 'resolution' | 'twist' | 'setup' | 'payoff' | 'transition' | 'chapter_outline';
  content: string;
  priority?: 'high' | 'medium' | 'low';
  tags?: string[];
  metadata?: Record<string, any>;
}

export interface CharacterContext {
  character_id: string;
  character_name: string;
  current_state?: Record<string, any>;
  recent_actions?: string[];
  relationships?: Record<string, string>;
  goals?: string[];
  memories?: string[];
  personality_traits?: string[];
}

export interface UserRequest {
  id?: string;
  type: 'modification' | 'addition' | 'removal' | 'style_change' | 'tone_adjustment' | 'general';
  content: string;
  priority?: 'high' | 'medium' | 'low';
  target?: string;
  context?: string;
  timestamp?: string | Date;
}

export interface SystemInstruction {
  id?: string;
  type: 'behavior' | 'style' | 'constraint' | 'preference' | 'rule';
  content: string;
  scope?: 'global' | 'character' | 'scene' | 'chapter' | 'story';
  priority?: 'high' | 'medium' | 'low';
  conditions?: Record<string, any>;
  metadata?: Record<string, any>;
}

export interface ContextMetadata {
  total_elements: number;
  processing_applied: boolean;
  processing_mode?: 'legacy' | 'structured' | 'hybrid';
  optimization_level?: 'none' | 'light' | 'moderate' | 'aggressive';
  compression_ratio?: number;
  filtered_elements?: Record<string, number>;
  processing_time_ms?: number;
  created_at?: string;
  version?: string;
}

export interface StructuredContextContainer {
  plot_elements?: PlotElement[];
  character_contexts?: CharacterContext[];
  user_requests?: UserRequest[];
  system_instructions?: SystemInstruction[];
  metadata?: ContextMetadata;
}

export interface GenerateCharacterDetailsRequest {
  character_name: string;
  request_context: RequestContext;
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
    goals: string[];
    memories: string[];
  };
}

export interface RaterFeedbackResponse {
  raterName: string;
  feedback: {
    opinion: string;
    suggestions: {
      issue: string;
      suggestion: string;
      priority: 'high' | 'medium' | 'low';
    }[];
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

export interface CharacterInfo {
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
}

export interface GenerateCharacterDetailsResponse {
  character_info: CharacterInfo;
  context_metadata?: ContextMetadata;
}

export interface RegenerateBioRequest {
  character_name: string;
  request_context: RequestContext;
}

export interface RegenerateBioResponse {
  basicBio: string;
  context_metadata?: ContextMetadata;
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
  story_context: Record<string, any>;
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
  agent_type: 'writer' | 'character' | 'editor' | 'worldbuilding';
  metadata: Record<string, any>;
}

// SSE Streaming interfaces for LLM Chat
export interface LLMChatStreamStatus {
  type: 'status';
  phase: 'context_building' | 'generating' | 'formatting';
  message: string;
  progress: number;
}

export interface LLMChatStreamResult {
  type: 'result';
  data: LLMChatResponse;
  status: 'complete';
}

export interface LLMChatStreamError {
  type: 'error';
  message: string;
}

export type LLMChatStreamMessage = LLMChatStreamStatus | LLMChatStreamResult | LLMChatStreamError;

// ============================================================================
// CHAPTER OUTLINE GENERATION API MODELS (WRI-129)
// ============================================================================

/**
 * Request model for chapter outline generation (Updated to use RequestContext)
 */
export interface ChapterOutlineGenerationRequest {
  request_context: RequestContext;
  context_processing_config?: any; // Optional processing configuration
}

/**
 * Response model for chapter outline generation (Updated to match backend)
 */
export interface ChapterOutlineGenerationResponse {
  outline_items: OutlineItem[];
  context_metadata?: Record<string, any>;
}
