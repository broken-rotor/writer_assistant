/**
 * TypeScript interfaces for token limits and strategies API integration.
 * 
 * These interfaces mirror the backend response from /tokens/strategies endpoint
 * to provide type safety and IntelliSense support for token limit management.
 */

/**
 * Token limits configuration
 */
export interface TokenLimitsResponse {
  /** System prompt prefix limit */
  system_prompt_prefix: number;
  /** System prompt suffix limit */
  system_prompt_suffix: number;
  /** Writing assistant prompt limit */
  writing_assistant_prompt: number;
  /** Writing editor prompt limit */
  writing_editor_prompt: number;
  /** Plot and world summary layer token limit */
  plot_world_summary: number;

  /** LLM context window size */
  llm_context_window: number;
  /** LLM maximum generation tokens */
  llm_max_generation: number;
}