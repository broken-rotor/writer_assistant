import { Injectable, inject } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { LocalStorageService } from './local-storage.service';

export interface WriterConfig {
  style_profile: string;
  tone: string;
  perspective: string;
  narrative_voice: string;
  pacing_preference: string;
}

export interface CharacterConfig {
  id: string;
  name: string;
  role: string;
  personality_profile: {
    core_traits: string[];
    secondary_traits: string[];
    psychology_profile: {
      motivation: string;
      fears: string[];
      desires: string[];
      internal_conflicts: string[];
    };
  };
  memory_settings: {
    reliability_factor: number;
    bias_patterns: string[];
    attention_focus: string[];
    memory_retention: string;
  };
  background: {
    age?: number;
    occupation?: string;
    education?: string;
    family_status?: string;
    key_relationships: Record<string, any>;
    personal_history: string[];
  };
}

export interface RaterConfig {
  id: string;
  name: string;
  type: 'consistency' | 'flow' | 'quality' | 'genre_specific';
  evaluation_criteria: {
    primary_focus: string[];
    secondary_focus: string[];
    quality_thresholds: {
      minimum_acceptable: number;
      target_score: number;
      exceptional_threshold: number;
    };
  };
  feedback_style: {
    tone: 'constructive' | 'detailed' | 'concise';
    suggestion_level: 'specific' | 'general' | 'minimal';
    encouragement_factor: number;
  };
  genre_specialization?: string;
}

export interface SystemConfig {
  generation_settings: {
    default_chapter_length: number;
    max_context_window: number;
    memory_compression_threshold: number;
    auto_save_interval: number;
  };
  ui_preferences: {
    theme: 'light' | 'dark' | 'auto';
    font_size: 'small' | 'medium' | 'large';
    editor_mode: 'simple' | 'advanced';
    show_agent_status: boolean;
    real_time_updates: boolean;
  };
  privacy_settings: {
    analytics_enabled: boolean;
    crash_reporting: boolean;
    usage_statistics: boolean;
  };
}

export interface StoryConfiguration {
  writer_config: WriterConfig;
  characters: CharacterConfig[];
  raters: RaterConfig[];
  system_config: SystemConfig;
  custom_settings: Record<string, any>;
}

@Injectable({
  providedIn: 'root'
})
export class ConfigurationService {
  private readonly DEFAULT_CONFIG_KEY = 'writer_assistant_default_config';

  private defaultConfigSubject = new BehaviorSubject<StoryConfiguration>(this.getDefaultConfiguration());
  public defaultConfig$ = this.defaultConfigSubject.asObservable();

  private localStorageService = inject(LocalStorageService);

  constructor() {
    this.loadDefaultConfiguration();
  }

  // Default Configuration Management
  getDefaultConfiguration(): StoryConfiguration {
    return {
      writer_config: {
        style_profile: 'balanced',
        tone: 'neutral',
        perspective: 'third_person',
        narrative_voice: 'omniscient',
        pacing_preference: 'moderate'
      },
      characters: [],
      raters: [
        {
          id: 'consistency_rater',
          name: 'Character Consistency Rater',
          type: 'consistency',
          evaluation_criteria: {
            primary_focus: ['character_voice', 'behavior_consistency', 'motivation_alignment'],
            secondary_focus: ['dialogue_authenticity', 'emotional_consistency'],
            quality_thresholds: {
              minimum_acceptable: 6.0,
              target_score: 8.0,
              exceptional_threshold: 9.0
            }
          },
          feedback_style: {
            tone: 'constructive',
            suggestion_level: 'specific',
            encouragement_factor: 0.7
          }
        },
        {
          id: 'flow_rater',
          name: 'Narrative Flow Rater',
          type: 'flow',
          evaluation_criteria: {
            primary_focus: ['pacing', 'scene_transitions', 'tension_management'],
            secondary_focus: ['dialogue_flow', 'action_sequences'],
            quality_thresholds: {
              minimum_acceptable: 6.5,
              target_score: 8.0,
              exceptional_threshold: 9.0
            }
          },
          feedback_style: {
            tone: 'detailed',
            suggestion_level: 'specific',
            encouragement_factor: 0.6
          }
        },
        {
          id: 'quality_rater',
          name: 'Literary Quality Rater',
          type: 'quality',
          evaluation_criteria: {
            primary_focus: ['prose_quality', 'literary_devices', 'thematic_depth'],
            secondary_focus: ['vocabulary_variety', 'sentence_structure'],
            quality_thresholds: {
              minimum_acceptable: 7.0,
              target_score: 8.5,
              exceptional_threshold: 9.5
            }
          },
          feedback_style: {
            tone: 'constructive',
            suggestion_level: 'general',
            encouragement_factor: 0.8
          }
        }
      ],
      system_config: {
        generation_settings: {
          default_chapter_length: 2500,
          max_context_window: 4000,
          memory_compression_threshold: 8000,
          auto_save_interval: 30000
        },
        ui_preferences: {
          theme: 'auto',
          font_size: 'medium',
          editor_mode: 'simple',
          show_agent_status: true,
          real_time_updates: true
        },
        privacy_settings: {
          analytics_enabled: false,
          crash_reporting: false,
          usage_statistics: false
        }
      },
      custom_settings: {}
    };
  }

  loadDefaultConfiguration(): void {
    try {
      const saved = this.localStorageService.loadUserPreferences();
      if (saved && saved['default_config']) {
        this.defaultConfigSubject.next(saved['default_config']);
      }
    } catch (error) {
      console.error('Error loading default configuration:', error);
    }
  }

  saveDefaultConfiguration(config: StoryConfiguration): void {
    try {
      const preferences = this.localStorageService.loadUserPreferences() || {};
      preferences['default_config'] = config;
      this.localStorageService.saveUserPreferences(preferences);
      this.defaultConfigSubject.next(config);
    } catch (error) {
      console.error('Error saving default configuration:', error);
    }
  }

  // Story-Specific Configuration
  getStoryConfiguration(storyId: string): StoryConfiguration | null {
    const config = this.localStorageService.loadStoryConfig(storyId);
    return (config as StoryConfiguration) || this.defaultConfigSubject.value || null;
  }

  saveStoryConfiguration(storyId: string, config: StoryConfiguration): void {
    this.localStorageService.saveStoryConfig(storyId, config);
  }

  // Configuration Templates
  getCharacterTemplate(archetype: string): CharacterConfig {
    const templates: Record<string, Partial<CharacterConfig>> = {
      detective: {
        role: 'protagonist',
        personality_profile: {
          core_traits: ['analytical', 'determined', 'observant'],
          secondary_traits: ['methodical', 'intuitive', 'protective'],
          psychology_profile: {
            motivation: 'seeking truth and justice',
            fears: ['failure', 'injustice', 'losing_loved_ones'],
            desires: ['solve_cases', 'protect_innocent', 'find_meaning'],
            internal_conflicts: ['duty_vs_personal_life', 'rules_vs_intuition']
          }
        },
        memory_settings: {
          reliability_factor: 0.9,
          bias_patterns: ['confirmation_bias', 'professional_skepticism'],
          attention_focus: ['details', 'inconsistencies', 'behavior_patterns'],
          memory_retention: 'excellent'
        }
      },
      romantic_lead: {
        role: 'love_interest',
        personality_profile: {
          core_traits: ['empathetic', 'passionate', 'vulnerable'],
          secondary_traits: ['supportive', 'complex', 'growth_oriented'],
          psychology_profile: {
            motivation: 'finding meaningful connection',
            fears: ['abandonment', 'vulnerability', 'not_being_enough'],
            desires: ['love', 'acceptance', 'personal_growth'],
            internal_conflicts: ['independence_vs_connection', 'past_trauma_vs_hope']
          }
        },
        memory_settings: {
          reliability_factor: 0.8,
          bias_patterns: ['emotional_filtering', 'idealization_tendency'],
          attention_focus: ['emotions', 'relationships', 'personal_meaning'],
          memory_retention: 'good'
        }
      },
      antagonist: {
        role: 'antagonist',
        personality_profile: {
          core_traits: ['intelligent', 'manipulative', 'goal_oriented'],
          secondary_traits: ['charismatic', 'ruthless', 'strategic'],
          psychology_profile: {
            motivation: 'achieving personal agenda',
            fears: ['exposure', 'failure', 'loss_of_control'],
            desires: ['power', 'recognition', 'revenge'],
            internal_conflicts: ['means_vs_ends', 'isolation_vs_connection']
          }
        },
        memory_settings: {
          reliability_factor: 0.85,
          bias_patterns: ['self_serving_bias', 'justification_tendency'],
          attention_focus: ['opportunities', 'weaknesses', 'strategic_advantage'],
          memory_retention: 'very_good'
        }
      }
    };

    const template = templates[archetype] || {};
    return {
      id: `character_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      name: '',
      role: template.role || 'supporting',
      personality_profile: template.personality_profile || {
        core_traits: [],
        secondary_traits: [],
        psychology_profile: {
          motivation: '',
          fears: [],
          desires: [],
          internal_conflicts: []
        }
      },
      memory_settings: template.memory_settings || {
        reliability_factor: 0.75,
        bias_patterns: [],
        attention_focus: [],
        memory_retention: 'average'
      },
      background: {
        key_relationships: {},
        personal_history: []
      }
    };
  }

  createRaterForGenre(genre: string): RaterConfig {
    const genreSpecifics: Record<string, Partial<RaterConfig>> = {
      mystery: {
        genre_specialization: 'mystery',
        evaluation_criteria: {
          primary_focus: ['clue_placement', 'red_herrings', 'logical_deduction'],
          secondary_focus: ['atmosphere', 'tension_building', 'revelation_timing'],
          quality_thresholds: {
            minimum_acceptable: 7.0,
            target_score: 8.5,
            exceptional_threshold: 9.5
          }
        }
      },
      romance: {
        genre_specialization: 'romance',
        evaluation_criteria: {
          primary_focus: ['relationship_development', 'emotional_authenticity', 'romantic_tension'],
          secondary_focus: ['chemistry', 'character_growth', 'satisfying_resolution'],
          quality_thresholds: {
            minimum_acceptable: 6.5,
            target_score: 8.0,
            exceptional_threshold: 9.0
          }
        }
      },
      fantasy: {
        genre_specialization: 'fantasy',
        evaluation_criteria: {
          primary_focus: ['world_building', 'magic_system', 'consistency'],
          secondary_focus: ['character_journey', 'mythological_elements', 'adventure_pacing'],
          quality_thresholds: {
            minimum_acceptable: 7.0,
            target_score: 8.5,
            exceptional_threshold: 9.5
          }
        }
      }
    };

    const template = genreSpecifics[genre.toLowerCase()] || {};

    return {
      id: `${genre.toLowerCase()}_rater`,
      name: `${genre} Genre Specialist`,
      type: 'genre_specific',
      genre_specialization: genre,
      evaluation_criteria: template.evaluation_criteria || {
        primary_focus: ['genre_conventions', 'reader_expectations', 'authenticity'],
        secondary_focus: ['pacing', 'character_development', 'plot_structure'],
        quality_thresholds: {
          minimum_acceptable: 6.5,
          target_score: 8.0,
          exceptional_threshold: 9.0
        }
      },
      feedback_style: {
        tone: 'constructive',
        suggestion_level: 'specific',
        encouragement_factor: 0.7
      }
    };
  }

  // Configuration Validation
  validateConfiguration(config: StoryConfiguration): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    // Validate writer config
    if (!config.writer_config) {
      errors.push('Writer configuration is missing');
    }

    // Validate characters
    config.characters.forEach((char, index) => {
      if (!char.name) {
        errors.push(`Character ${index + 1} is missing a name`);
      }
      if (!char.personality_profile.core_traits.length) {
        errors.push(`Character ${char.name || index + 1} has no core traits defined`);
      }
    });

    // Validate raters
    if (config.raters.length === 0) {
      errors.push('At least one rater must be configured');
    }

    config.raters.forEach((rater, index) => {
      if (!rater.evaluation_criteria.primary_focus.length) {
        errors.push(`Rater ${rater.name || index + 1} has no primary evaluation criteria`);
      }
    });

    return {
      valid: errors.length === 0,
      errors
    };
  }

  // Configuration Import/Export
  exportConfiguration(config: StoryConfiguration): Blob {
    const exportData = {
      export_metadata: {
        timestamp: new Date().toISOString(),
        version: '1.0',
        type: 'configuration'
      },
      configuration: config
    };

    const jsonString = JSON.stringify(exportData, null, 2);
    return new Blob([jsonString], { type: 'application/json' });
  }

  async importConfiguration(file: File): Promise<{ success: boolean; config?: StoryConfiguration; error?: string }> {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const importData = JSON.parse(e.target?.result as string);

          if (importData.configuration) {
            const validation = this.validateConfiguration(importData.configuration);
            if (validation.valid) {
              resolve({ success: true, config: importData.configuration });
            } else {
              resolve({ success: false, error: `Invalid configuration: ${validation.errors.join(', ')}` });
            }
          } else {
            resolve({ success: false, error: 'No configuration data found in file' });
          }
        } catch (error) {
          resolve({ success: false, error: `Failed to parse configuration file: ${error}` });
        }
      };
      reader.readAsText(file);
    });
  }
}
