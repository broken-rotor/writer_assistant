/**
 * TypeScript interfaces for token limits API integration.
 *
 * These interfaces mirror the backend response from /tokens/limits endpoint
 * to provide type safety and IntelliSense support for token limit management.
 */

/**
 * Token limits configuration from /tokens/limits endpoint
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
  /** Worldbuilding content limit */
  worldbuilding: number;
  /** Plot outline content limit */
  plot_outline: number;
}