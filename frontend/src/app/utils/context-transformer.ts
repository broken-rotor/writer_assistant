/**
 * Utility functions to transform Story model to RequestContext format.
 * This builds RequestContext from Story model instead of StructuredContextContainer.
 */

import {
  Story
} from '../models/story.model';

// ============================================================================
// REQUEST CONTEXT INTERFACES
// ============================================================================

export interface SystemPrompts {
  main_prefix: string;
  main_suffix: string;
  assistant_prompt: string;
  editor_prompt: string;
}

export interface RaterConfig {
  id: string;
  name: string;
  system_prompt: string;
  enabled: boolean;
}

export interface StoryConfiguration {
  system_prompts: SystemPrompts;
  raters: RaterConfig[];
  generation_preferences: Record<string, any>;
}

export interface RequestChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  author?: string;
}

export interface WorldElement {
  type: 'location' | 'culture' | 'magic_system' | 'history' | 'politics' | 'technology';
  name: string;
  description: string;
  importance: 'high' | 'medium' | 'low';
}

export interface WorldbuildingInfo {
  content: string;
  chat_history: RequestChatMessage[];
  key_elements: WorldElement[];
}

export interface CharacterDetails {
  id: string;
  name: string;
  basic_bio: string;
  sex: string;
  gender: string;
  sexual_preference: string;
  age: number;
  physical_appearance: string;
  usual_clothing: string;
  personality: string;
  motivations: string;
  fears: string;
  relationships: string;
  current_state: Record<string, any>;
  recent_actions: string[];
  goals: string[];
  memories: string[];
  is_hidden: boolean;
  creation_source: 'user' | 'ai_generated' | 'imported';
  last_modified: string;
}

export interface RequestOutlineItem {
  id: string;
  type: 'chapter' | 'scene' | 'plot-point' | 'character-arc';
  title: string;
  description: string;
  key_plot_items: string[];
  order: number;
  parent_id?: string;
  involved_characters: string[];
  status: 'draft' | 'reviewed' | 'approved';
  word_count_estimate?: number;
}

export interface OutlineFeedback {
  rater_id: string;
  rater_name: string;
  feedback: string;
  status: 'pending' | 'generating' | 'complete' | 'error';
  timestamp: string;
  user_response?: 'accepted' | 'revision_requested' | 'discussed';
}

export interface StoryOutline {
  summary: string;
  status: 'draft' | 'under_review' | 'approved' | 'needs_revision';
  content: string;
  outline_items: RequestOutlineItem[];
  rater_feedback: OutlineFeedback[];
  chat_history: RequestChatMessage[];
}

export interface RequestFeedbackItem {
  id: string;
  source: string;
  type: 'action' | 'dialog' | 'sensation' | 'emotion' | 'thought' | 'suggestion';
  content: string;
  incorporated: boolean;
  priority: 'high' | 'medium' | 'low';
  status: 'pending' | 'incorporated' | 'dismissed';
}

export interface CharacterFeedbackItem {
  character_name: string;
  actions: string[];
  dialog: string[];
  physical_sensations: string[];
  emotions: string[];
  internal_monologue: string[];
}

export interface RaterFeedbackItem {
  rater_name: string;
  opinion: string;
  suggestions: string[];
}

export interface EditorSuggestion {
  issue: string;
  suggestion: string;
  priority: 'high' | 'medium' | 'low';
  selected: boolean;
}

export interface ChapterDetails {
  id: string;
  number: number;
  title: string;
  content: string;
  plot_point?: string;
  key_plot_items: string[];
  incorporated_feedback: RequestFeedbackItem[];
  character_feedback: CharacterFeedbackItem[];
  rater_feedback: RaterFeedbackItem[];
  editor_suggestions: EditorSuggestion[];
  word_count: number;
  created: string;
  last_modified: string;
}

export interface RequestContextMetadata {
  story_id: string;
  story_title: string;
  version: string;
  created_at: string;
  total_characters: number;
  total_chapters: number;
  total_word_count: number;
  context_size_estimate: number;
  processing_hints: Record<string, any>;
}

export interface RequestContext {
  configuration: StoryConfiguration;
  worldbuilding: WorldbuildingInfo;
  characters: CharacterDetails[];
  story_outline: StoryOutline;
  chapters: ChapterDetails[];
  context_metadata: RequestContextMetadata;
}

// ============================================================================
// MAIN TRANSFORM FUNCTION
// ============================================================================

/**
 * Helper function to safely convert a date value to ISO string
 * Handles both Date objects and ISO string values (from localStorage)
 */
function toISOString(dateValue: Date | string): string {
  if (!dateValue) {
    return new Date().toISOString();
  }
  if (typeof dateValue === 'string') {
    return dateValue; // Already an ISO string
  }
  if (dateValue instanceof Date) {
    return dateValue.toISOString();
  }
  // Fallback: try to parse and convert
  return new Date(dateValue).toISOString();
}

/**
 * Transform Story model to RequestContext format
 */
export function transformToRequestContext(
  story: Story
): RequestContext {
  return {
    configuration: {
      system_prompts: {
        main_prefix: story.general?.systemPrompts?.mainPrefix || '',
        main_suffix: story.general?.systemPrompts?.mainSuffix || '',
        assistant_prompt: story.general?.systemPrompts?.assistantPrompt || '',
        editor_prompt: story.general?.systemPrompts?.editorPrompt || ''
      },
      raters: Array.from(story.raters?.values() || []).map(rater => ({
        id: rater.id,
        name: rater.name,
        system_prompt: rater.systemPrompt,
        enabled: rater.enabled
      })),
      generation_preferences: {}
    },
    worldbuilding: {
      content: story.general?.worldbuilding || '',
      chat_history: (story.general?.worldbuildingChatHistory || []).map(msg => ({
        id: msg.id,
        type: msg.type,
        content: msg.content,
        timestamp: toISOString(msg.timestamp),
        author: msg.author
      })),
      key_elements: []
    },
    characters: Array.from(story.characters?.values() || []).map(char => ({
      id: char.id,
      name: char.name,
      basic_bio: char.basicBio,
      sex: char.sex,
      gender: char.gender,
      sexual_preference: char.sexualPreference,
      age: char.age,
      physical_appearance: char.physicalAppearance,
      usual_clothing: char.usualClothing,
      personality: char.personality,
      motivations: char.motivations,
      fears: char.fears,
      relationships: char.relationships,
      current_state: {},
      recent_actions: [],
      goals: char.motivations ? [char.motivations] : [],
      memories: char.fears ? [`Fears: ${char.fears}`] : [],
      is_hidden: char.isHidden,
      creation_source: char.metadata.creationSource,
      last_modified: toISOString(char.metadata.lastModified)
    })),
    story_outline: {
      summary: story.story?.summary || '',
      status: story.plotOutline?.status || 'draft',
      content: story.plotOutline?.content || '',
      outline_items: [], // No outline items in current Story model
      rater_feedback: Array.from(story.plotOutline?.raterFeedback?.values() || []).map(feedback => ({
        rater_id: feedback.raterId,
        rater_name: feedback.raterName,
        feedback: feedback.feedback,
        status: feedback.status,
        timestamp: toISOString(feedback.timestamp),
        user_response: feedback.userResponse
      })),
      chat_history: (story.plotOutline?.chatHistory || []).map(msg => ({
        id: msg.id,
        type: msg.type,
        content: msg.content,
        timestamp: toISOString(msg.timestamp),
        author: msg.author
      }))
    },
    chapters: (story.story?.chapters || []).map(chapter => ({
      id: chapter.id,
      number: chapter.number,
      title: chapter.title,
      content: chapter.content,
      plot_point: chapter.plotPoint,
      key_plot_items: chapter.keyPlotItems || [],
      incorporated_feedback: chapter.incorporatedFeedback.map(feedback => ({
        id: `${chapter.id}-${feedback.source}-${Date.now()}`,
        source: feedback.source,
        type: feedback.type,
        content: feedback.content,
        incorporated: feedback.incorporated,
        priority: 'medium' as const,
        status: feedback.incorporated ? 'incorporated' as const : 'pending' as const
      })),
      character_feedback: [],
      rater_feedback: [],
      editor_suggestions: [],
      word_count: chapter.metadata.wordCount,
      created: toISOString(chapter.metadata.created),
      last_modified: toISOString(chapter.metadata.lastModified)
    })),
    context_metadata: {
      story_id: story.id,
      story_title: story.general?.title || '',
      version: '1.0',
      created_at: new Date().toISOString(),
      total_characters: Array.from(story.characters?.values() || []).length,
      total_chapters: story.story?.chapters?.length || 0,
      total_word_count: (story.story?.chapters || []).reduce((total, chapter) => total + chapter.metadata.wordCount, 0),
      context_size_estimate: 0,
      processing_hints: {}
    }
  };
}
