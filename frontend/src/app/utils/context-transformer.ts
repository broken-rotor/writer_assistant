/**
 * Utility functions to transform legacy API format to structured context format.
 * This handles the migration from the old systemPrompts/worldbuilding/storySummary
 * format to the new structured context format required by the backend.
 */

import {
  StructuredContextContainer,
  Character
} from '../models/story.model';

/**
 * Legacy format data structure for transformation
 */
export interface LegacyCharacterGenerationData {
  systemPrompts: {
    mainPrefix: string;
    mainSuffix: string;
  };
  worldbuilding: string;
  storySummary: string;
  basicBio: string;
  existingCharacters: Character[];
}

/**
 * Legacy format data structure for flesh-out transformation
 */
export interface LegacyFleshOutData {
  systemPrompts: {
    mainPrefix: string;
    mainSuffix: string;
  };
  worldbuilding: string;
  storySummary: string;
  textToFleshOut: string;
  context: string;
}

/**
 * Transform legacy character generation data to structured context format
 */
export function transformToStructuredContext(
  legacyData: LegacyCharacterGenerationData
): StructuredContextContainer {
  const structuredContext: StructuredContextContainer = {
    plot_elements: [],
    character_contexts: [],
    user_requests: [],
    system_instructions: []
  };

  // Transform system prompts to system instructions
  if (legacyData.systemPrompts.mainPrefix) {
    structuredContext.system_instructions!.push({
      type: 'behavior',
      content: legacyData.systemPrompts.mainPrefix,
      scope: 'global',
      priority: 'high'
    });
  }

  if (legacyData.systemPrompts.mainSuffix) {
    structuredContext.system_instructions!.push({
      type: 'style',
      content: legacyData.systemPrompts.mainSuffix,
      scope: 'global',
      priority: 'medium'
    });
  }

  // Transform worldbuilding to plot elements
  if (legacyData.worldbuilding) {
    structuredContext.plot_elements!.push({
      type: 'setup',
      content: legacyData.worldbuilding,
      priority: 'high',
      tags: ['worldbuilding', 'setting'],
      metadata: {
        source: 'worldbuilding',
        category: 'background'
      }
    });
  }

  // Transform story summary to plot elements
  if (legacyData.storySummary) {
    structuredContext.plot_elements!.push({
      type: 'scene',
      content: legacyData.storySummary,
      priority: 'high',
      tags: ['story_summary', 'plot'],
      metadata: {
        source: 'story_summary',
        category: 'narrative'
      }
    });
  }

  // Transform existing characters to character contexts
  if (legacyData.existingCharacters && legacyData.existingCharacters.length > 0) {
    legacyData.existingCharacters.forEach((character, index) => {
      structuredContext.character_contexts!.push({
        character_id: character.name.toLowerCase().replace(/\s+/g, '_') || `character_${index}`,
        character_name: character.name || `Character ${index + 1}`,
        current_state: {
          description: character.basicBio || 'No description available'
        },
        relationships: character.relationships ? 
          { general: character.relationships } : {},
        personality_traits: character.personality ? 
          [character.personality] : [],
        goals: character.motivations ? 
          [character.motivations] : [],
        memories: character.fears ? 
          [`Fears: ${character.fears}`] : []
      });
    });
  }

  // Add a user request for character generation
  structuredContext.user_requests!.push({
    type: 'general',
    content: `Generate detailed character information for: ${legacyData.basicBio}`,
    priority: 'high',
    target: 'new_character',
    context: 'character_generation'
  });

  return structuredContext;
}

/**
 * Transform legacy flesh-out data to structured context format
 */
export function transformToFleshOutStructuredContext(
  legacyData: LegacyFleshOutData
): StructuredContextContainer {
  const structuredContext: StructuredContextContainer = {
    plot_elements: [],
    character_contexts: [],
    user_requests: [],
    system_instructions: []
  };

  // Transform system prompts to system instructions
  if (legacyData.systemPrompts.mainPrefix) {
    structuredContext.system_instructions!.push({
      type: 'behavior',
      content: legacyData.systemPrompts.mainPrefix,
      scope: 'global',
      priority: 'high'
    });
  }

  if (legacyData.systemPrompts.mainSuffix) {
    structuredContext.system_instructions!.push({
      type: 'style',
      content: legacyData.systemPrompts.mainSuffix,
      scope: 'global',
      priority: 'medium'
    });
  }

  // Transform worldbuilding to plot elements
  if (legacyData.worldbuilding) {
    structuredContext.plot_elements!.push({
      type: 'setup',
      content: legacyData.worldbuilding,
      priority: 'high',
      tags: ['worldbuilding', 'setting'],
      metadata: {
        source: 'worldbuilding',
        category: 'background'
      }
    });
  }

  // Transform story summary to plot elements
  if (legacyData.storySummary) {
    structuredContext.plot_elements!.push({
      type: 'scene',
      content: legacyData.storySummary,
      priority: 'high',
      tags: ['story_summary', 'plot'],
      metadata: {
        source: 'story_summary',
        category: 'narrative'
      }
    });
  }

  // Add the text to flesh out as a plot element
  if (legacyData.textToFleshOut) {
    structuredContext.plot_elements!.push({
      type: 'scene',
      content: legacyData.textToFleshOut,
      priority: 'high',
      tags: ['current_scene', 'flesh_out_target'],
      metadata: {
        source: 'text_to_flesh_out',
        category: 'target_content'
      }
    });
  }

  // Add user request for flesh-out operation
  structuredContext.user_requests!.push({
    type: 'addition',
    content: `Expand and flesh out the following text with relevant detail: ${legacyData.textToFleshOut}`,
    priority: 'high',
    target: 'flesh_out_target',
    context: legacyData.context || 'general'
  });

  return structuredContext;
}

/**
 * Create a minimal structured context for character generation
 * when legacy data is not available
 */
export function createMinimalStructuredContext(
  basicBio: string,
  existingCharacters: {name: string; basicBio: string; relationships: string}[]
): StructuredContextContainer {
  const structuredContext: StructuredContextContainer = {
    plot_elements: [],
    character_contexts: [],
    user_requests: [],
    system_instructions: []
  };

  // Add basic system instruction for character generation
  structuredContext.system_instructions!.push({
    type: 'behavior',
    content: 'Generate comprehensive character details based on the provided basic biography.',
    scope: 'character',
    priority: 'high'
  });

  // Transform existing characters to character contexts
  if (existingCharacters && existingCharacters.length > 0) {
    existingCharacters.forEach((character, index) => {
      structuredContext.character_contexts!.push({
        character_id: character.name.toLowerCase().replace(/\s+/g, '_') || `character_${index}`,
        character_name: character.name || `Character ${index + 1}`,
        current_state: {
          description: character.basicBio || 'No description available'
        },
        relationships: character.relationships ? 
          { general: character.relationships } : {}
      });
    });
  }

  // Add user request for character generation
  structuredContext.user_requests!.push({
    type: 'general',
    content: `Generate detailed character information for: ${basicBio}`,
    priority: 'high',
    target: 'new_character',
    context: 'character_generation'
  });

  return structuredContext;
}
