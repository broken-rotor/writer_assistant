/**
 * TypeScript interfaces for token limits and strategies API integration.
 * 
 * These interfaces mirror the backend response from /tokens/strategies endpoint
 * to provide type safety and IntelliSense support for token limit management.
 */

/**
 * Token counting strategy information
 */
export interface TokenStrategy {
  /** Description of the strategy */
  description: string;
  /** Overhead multiplier applied */
  overhead: number;
  /** Use case description */
  use_case: string;
}

/**
 * Content type information with multipliers
 */
export interface ContentTypeInfo {
  /** Description of the content type */
  description: string;
  /** Token count multiplier for this content type */
  multiplier: number;
}

/**
 * Context management layer limits
 */
export interface ContextLayerLimits {
  /** System instructions layer token limit */
  system_instructions: number;
  /** Immediate instructions layer token limit */
  immediate_instructions: number;
  /** Recent story layer token limit */
  recent_story: number;
  /** Character and scene data layer token limit */
  character_scene_data: number;
  /** Plot and world summary layer token limit */
  plot_world_summary: number;
}

/**
 * Context management configuration
 */
export interface ContextManagement {
  /** Maximum context tokens */
  max_context_tokens: number;
  /** Buffer tokens for safety */
  buffer_tokens: number;
  /** Layer-specific token limits */
  layer_limits: ContextLayerLimits;
}

/**
 * Recommended token limits for different prompt types
 */
export interface RecommendedLimits {
  /** System prompt prefix limit */
  system_prompt_prefix: number;
  /** System prompt suffix limit */
  system_prompt_suffix: number;
  /** Writing assistant prompt limit */
  writing_assistant_prompt: number;
  /** Writing editor prompt limit */
  writing_editor_prompt: number;
}

/**
 * Token limits configuration
 */
export interface TokenLimits {
  /** LLM context window size */
  llm_context_window: number;
  /** LLM maximum generation tokens */
  llm_max_generation: number;
  /** Context management configuration */
  context_management: ContextManagement;
  /** Recommended limits for different use cases */
  recommended_limits: RecommendedLimits;
}

/**
 * Batch processing limits
 */
export interface BatchLimits {
  /** Maximum texts per request */
  max_texts_per_request: number;
  /** Maximum text size in bytes */
  max_text_size_bytes: number;
}

/**
 * Response from /tokens/strategies endpoint
 */
export interface TokenStrategiesResponse {
  /** Whether the request was successful */
  success: boolean;
  /** Available counting strategies */
  strategies: Record<string, TokenStrategy>;
  /** Available content types */
  content_types: Record<string, ContentTypeInfo>;
  /** Token limits configuration */
  token_limits: TokenLimits;
  /** Default strategy name */
  default_strategy: string;
  /** Batch processing limits */
  batch_limits: BatchLimits;
}
