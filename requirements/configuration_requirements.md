# Configuration System Requirements

## Overview

The Writer Assistant uses JSON-based configuration files to define character personalities, rater preferences, writing styles, and system behavior. The configuration system supports dynamic loading, validation, and user customization while maintaining consistency across story development.

## Configuration Architecture

### Configuration File Structure

```
/config/
├── characters/
│   ├── character_templates/
│   │   ├── protagonist_template.json
│   │   ├── antagonist_template.json
│   │   └── supporting_character_template.json
│   └── story_specific/
│       └── story_123_characters.json
├── raters/
│   ├── rater_profiles/
│   │   ├── character_consistency_rater.json
│   │   ├── narrative_flow_rater.json
│   │   ├── literary_quality_rater.json
│   │   └── genre_specific_raters/
│   │       ├── mystery_rater.json
│   │       ├── romance_rater.json
│   │       └── thriller_rater.json
│   └── custom_raters/
│       └── user_custom_raters.json
├── styles/
│   ├── writing_styles/
│   │   ├── literary_style.json
│   │   ├── commercial_style.json
│   │   └── genre_styles/
│   │       └── mystery_style.json
│   └── editor_preferences/
│       └── editor_config.json
└── system/
    ├── workflow_config.json
    ├── memory_config.json
    └── llm_config.json
```

## Character Configuration

### Character Profile Schema

```json
{
  "$schema": "https://writer-assistant.com/schemas/character-v1.json",
  "character_id": "john_smith_protagonist",
  "metadata": {
    "name": "John Smith",
    "role": "protagonist",
    "archetype": "reluctant_hero",
    "created_date": "2025-09-24",
    "version": "1.0",
    "description": "Introverted software engineer with protective instincts",
    "is_hidden": false,
    "creation_source": "user_defined"
  },
  "personality_profile": {
    "core_traits": {
      "primary": ["analytical", "introverted", "loyal"],
      "secondary": ["perfectionist", "cautious", "empathetic"],
      "negative": ["overthinking", "conflict_avoidant", "self_critical"]
    },
    "psychological_patterns": {
      "decision_making_style": "analytical_with_emotional_consideration",
      "stress_response": "withdrawal_and_internal_processing",
      "conflict_style": "avoidance_then_direct_confrontation",
      "emotional_expression": "reserved_but_deep",
      "trust_patterns": "slow_to_trust_but_deeply_loyal"
    },
    "values_and_motivations": {
      "core_values": ["family_protection", "honesty", "competence"],
      "primary_motivations": ["keep_loved_ones_safe", "maintain_integrity"],
      "fears": ["losing_control", "hurting_others", "being_inadequate"],
      "desires": ["meaningful_connections", "professional_recognition", "peace"]
    }
  },
  "background": {
    "demographics": {
      "age": 34,
      "occupation": "senior_software_engineer",
      "education": "computer_science_masters",
      "location": "suburban_tech_hub"
    },
    "personal_history": {
      "formative_experiences": [
        {
          "event": "father_abandonment_age_12",
          "impact": "hypervigilance_about_family_stability",
          "emotional_residue": "fear_of_abandonment"
        },
        {
          "event": "successful_career_building",
          "impact": "confidence_in_technical_abilities",
          "emotional_residue": "imposter_syndrome_in_relationships"
        }
      ],
      "relationships": {
        "mary_wife": {
          "relationship_type": "spouse",
          "duration": "8_years",
          "quality": "deep_love_with_communication_challenges",
          "dynamics": "protector_protected_but_shifting"
        },
        "deceased_father": {
          "relationship_type": "parent",
          "impact": "abandonment_issues_drive_protective_behavior",
          "unresolved_feelings": "anger_and_longing"
        }
      }
    }
  },
  "behavioral_patterns": {
    "communication_style": {
      "verbal_patterns": ["precise_language", "technical_metaphors", "understated_emotions"],
      "dialogue_characteristics": ["formal_but_warm", "explanatory", "hedge_words"],
      "non_verbal_patterns": ["controlled_body_language", "intense_eye_contact", "fidgeting_when_stressed"]
    },
    "emotional_expression": {
      "comfort_emotions": ["quiet_satisfaction", "protective_concern", "analytical_curiosity"],
      "difficult_emotions": ["anger", "vulnerability", "overwhelm"],
      "expression_methods": ["through_actions_not_words", "delayed_processing", "problem_solving_focus"]
    },
    "decision_making": {
      "process": ["gather_information", "analyze_options", "consider_impact_on_others", "act_decisively"],
      "biases": ["over_analysis", "worst_case_planning", "self_sacrifice_for_others"],
      "stress_modifications": ["rushed_decisions", "increased_control_needs", "isolation_tendency"]
    }
  },
  "memory_characteristics": {
    "memory_reliability": {
      "baseline_accuracy": 0.8,
      "stress_impact": -0.3,
      "emotional_event_impact": -0.2,
      "technical_detail_boost": +0.2
    },
    "attention_patterns": {
      "focus_areas": ["technical_details", "potential_threats", "others_emotional_states"],
      "blind_spots": ["own_emotional_needs", "positive_social_cues", "self_care_requirements"],
      "selective_attention": ["problem_solving_opportunities", "relationship_dynamics"]
    },
    "bias_tendencies": {
      "confirmation_bias": 0.6,
      "self_protective_filtering": 0.8,
      "responsibility_attribution": "internal_for_problems_external_for_successes",
      "emotional_suppression": 0.7
    },
    "memory_evolution": {
      "reinterpretation_triggers": ["new_relationship_information", "stress_reduction", "perspective_shifts"],
      "stability_factors": ["technical_memories", "core_value_conflicts", "protective_instinct_events"]
    }
  },
  "character_arc_potential": {
    "starting_state": {
      "emotional": "guarded_but_caring",
      "relational": "protective_but_uncommunicative",
      "internal": "competent_but_self_doubting"
    },
    "growth_opportunities": {
      "primary": "learning_vulnerable_communication",
      "secondary": "accepting_help_from_others",
      "tertiary": "balancing_protection_with_trust"
    },
    "potential_endpoints": {
      "positive": "emotionally_open_connected_partner",
      "negative": "isolated_controlling_protector",
      "realistic": "improved_communicator_with_ongoing_challenges"
    },
    "catalyst_requirements": {
      "external_pressure": "threat_to_relationship_or_family",
      "internal_realization": "protection_can_become_barrier",
      "support_system": "patient_understanding_from_loved_ones"
    }
  },
  "story_integration": {
    "narrative_functions": ["protagonist", "POV_character", "emotional_center"],
    "thematic_connections": ["trust_vs_control", "love_vs_fear", "growth_vs_safety"],
    "plot_utilities": ["problem_solver", "information_gatherer", "emotional_catalyst"],
    "reader_connection": ["relatable_flaws", "understandable_motivations", "growth_potential"]
  },
  "character_management": {
    "visibility_status": {
      "is_hidden": false,
      "hidden_date": null,
      "hidden_reason": ""
    },
    "ai_expansion_history": {
      "expansion_requests": [
        {
          "date": "2025-09-24",
          "expansion_type": "personality_details",
          "user_prompt": "Expand John's analytical traits",
          "ai_generated_content": {
            "section": "personality_profile.psychological_patterns",
            "added_details": "..."
          }
        }
      ],
      "last_expansion": "2025-09-24"
    }
  }
}
```

### Character Management Features

**Character Creation and Modification**:
- **User-Defined Characters**: Users provide basic physical, psychological, emotional characteristics and personality
- **AI-Assisted Expansion**: Users can request AI to expand and elaborate character details, which are stored directly in character configuration
- **Dynamic Character Management**: Characters can be added or removed (hidden) at any point during story development
- **Character Visibility Control**: Soft-delete system using `is_hidden` flag to hide characters without data loss

**Character Visibility States**:
- **Active (`is_hidden: false`)**: Character participates in agent interactions, appears in user selection prompts, and receives feedback/reaction opportunities
- **Hidden (`is_hidden: true`)**: Character excluded from future agent interactions and user prompts but data preserved for potential restoration
- **Restoration**: Users can unhide previously hidden characters to restore full participation

**AI Expansion Workflow**:
1. User creates character with basic details
2. User requests AI expansion for specific aspects (personality, background, relationships, etc.)
3. AI generates detailed content based on user prompt
4. Expanded details stored directly in character configuration JSON
5. Expansion history tracked for reference and auditability

**Character Introduction Guidelines**:
- **Mid-Story Addition**: When users add characters during chapter development, they guide the introduction process
- **User-Controlled Integration**: No automatic backstory generation - user directs how new characters appear
- **Memory Continuity**: New characters start with fresh memory state unless user specifies otherwise

### Character Template System

**Template Categories**:
- **Archetype Templates**: Hero, mentor, shadow, etc.
- **Genre Templates**: Mystery detective, romance lead, fantasy wizard
- **Role Templates**: Protagonist, antagonist, supporting character
- **Personality Templates**: Introvert, extrovert, analytical, emotional

**Template Inheritance**:
```json
{
  "character_template_example": {
    "inherits_from": ["protagonist_archetype", "analytical_personality"],
    "overrides": {
      "personality_profile.core_traits.primary": ["analytical", "protective", "loyal"],
      "behavioral_patterns.communication_style.verbal_patterns": ["technical_metaphors", "precise_language"]
    },
    "extensions": {
      "profession_specific": {
        "occupation": "software_engineer",
        "expertise_areas": ["system_architecture", "problem_solving"],
        "professional_vocabulary": ["technical_terms", "process_language"]
      }
    }
  }
}
```

## Rater Configuration

### Rater Profile Schema

```json
{
  "$schema": "https://writer-assistant.com/schemas/rater-v1.json",
  "rater_id": "character_consistency_expert",
  "metadata": {
    "name": "Character Consistency Rater",
    "type": "character_focused",
    "expertise": "psychological_realism_and_character_development",
    "version": "2.1",
    "description": "Evaluates character authenticity and consistency"
  },
  "evaluation_framework": {
    "primary_criteria": {
      "character_voice_consistency": {
        "weight": 0.9,
        "description": "Does character maintain unique voice and perspective?",
        "metrics": [
          "dialogue_authenticity",
          "internal_monologue_consistency",
          "behavioral_pattern_maintenance",
          "emotional_response_believability"
        ],
        "quality_thresholds": {
          "excellent": 9.0,
          "good": 7.0,
          "acceptable": 5.0,
          "needs_improvement": 3.0
        }
      },
      "psychological_realism": {
        "weight": 0.8,
        "description": "Do character actions and thoughts feel psychologically authentic?",
        "focus_areas": [
          "motivation_clarity",
          "emotional_logic",
          "reaction_appropriateness",
          "growth_believability"
        ],
        "evaluation_questions": [
          "Would a real person with this personality react this way?",
          "Are the character's internal contradictions realistic?",
          "Does the character's growth feel earned?"
        ]
      },
      "memory_authenticity": {
        "weight": 0.7,
        "description": "Do character memories and interpretations feel genuine?",
        "assessment_criteria": [
          "bias_pattern_consistency",
          "emotional_coloring_appropriateness",
          "selective_attention_realism",
          "memory_reliability_factors"
        ]
      }
    },
    "secondary_criteria": {
      "relationship_dynamics": {
        "weight": 0.6,
        "focus": "inter_character_relationship_authenticity"
      },
      "character_arc_progression": {
        "weight": 0.5,
        "focus": "believable_character_development_pacing"
      }
    }
  },
  "feedback_configuration": {
    "style_preferences": {
      "tone": "constructive_analytical",
      "directness_level": 0.7,
      "encouragement_ratio": 0.4,
      "detail_level": "comprehensive_with_examples",
      "criticism_approach": "problem_focused_with_solutions"
    },
    "feedback_structure": {
      "opening": "acknowledge_strengths_first",
      "body": "specific_issues_with_examples_and_suggestions",
      "closing": "encouragement_and_next_steps",
      "rating_explanation": "detailed_breakdown_of_scoring_rationale"
    },
    "language_preferences": {
      "technical_terminology": "moderate_use_with_explanations",
      "examples": "specific_quotes_and_references",
      "suggestions": "actionable_concrete_steps",
      "tone_markers": ["respectful", "professional", "encouraging"]
    }
  },
  "standards_and_tolerances": {
    "quality_expectations": {
      "minimum_acceptable_score": 5.0,
      "target_score_range": [7.0, 9.0],
      "excellence_threshold": 9.0
    },
    "consistency_tolerances": {
      "minor_inconsistency_threshold": 0.1,
      "major_inconsistency_threshold": 0.3,
      "critical_inconsistency_threshold": 0.5
    },
    "improvement_tracking": {
      "progress_recognition_threshold": 0.5,
      "plateau_concern_threshold": 3,
      "regression_alert_threshold": -0.3
    }
  },
  "contextual_adaptations": {
    "story_phase_adjustments": {
      "outline_phase": {
        "criteria_weights": "focus_on_potential_and_setup",
        "tolerance_adjustments": "higher_tolerance_for_development_areas"
      },
      "early_chapters": {
        "criteria_weights": "establishment_over_consistency",
        "special_considerations": "character_introduction_allowances"
      },
      "middle_chapters": {
        "criteria_weights": "consistency_and_development_balance",
        "focus_areas": "growth_tracking_and_relationship_evolution"
      },
      "climax_chapters": {
        "criteria_weights": "authenticity_under_pressure",
        "special_considerations": "extreme_situation_believability"
      }
    },
    "genre_adaptations": {
      "literary_fiction": {
        "emphasis": "psychological_depth_and_complexity",
        "tolerance": "higher_ambiguity_acceptance"
      },
      "commercial_fiction": {
        "emphasis": "relatability_and_clear_motivation",
        "tolerance": "streamlined_psychology_acceptance"
      },
      "mystery": {
        "emphasis": "information_management_and_red_herrings",
        "special_focus": "character_knowledge_limitations"
      }
    }
  },
  "learning_and_adaptation": {
    "feedback_effectiveness_tracking": {
      "metrics": ["suggestion_implementation_rate", "score_improvement_correlation", "user_satisfaction"],
      "adaptation_triggers": ["low_implementation_rate", "user_feedback", "score_stagnation"]
    },
    "pattern_recognition": {
      "track_recurring_issues": true,
      "identify_writer_strengths": true,
      "adapt_feedback_focus": true
    }
  }
}
```

### Genre-Specific Rater Configurations

```json
{
  "mystery_genre_rater": {
    "inherits_from": "base_genre_rater",
    "specialized_criteria": {
      "clue_management": {
        "weight": 0.9,
        "focus": "fair_play_principle_and_logical_deduction",
        "metrics": ["clue_distribution", "red_herring_effectiveness", "solution_foreshadowing"]
      },
      "suspense_building": {
        "weight": 0.8,
        "focus": "tension_maintenance_and_pacing",
        "assessment": "mystery_specific_pacing_requirements"
      },
      "information_revelation": {
        "weight": 0.7,
        "focus": "strategic_information_disclosure",
        "requirements": "balance_mystery_with_reader_engagement"
      }
    }
  }
}
```

## Writing Style Configuration

### Style Profile Schema

```json
{
  "$schema": "https://writer-assistant.com/schemas/style-v1.json",
  "style_id": "literary_contemporary",
  "metadata": {
    "name": "Literary Contemporary Fiction Style",
    "category": "literary",
    "target_audience": "adult_literary_readers",
    "description": "Sophisticated prose with psychological depth"
  },
  "prose_characteristics": {
    "sentence_structure": {
      "average_length": "medium_to_long",
      "complexity_preference": "varied_complex",
      "rhythm_patterns": ["flowing", "contemplative", "building"],
      "punctuation_style": "sophisticated_varied"
    },
    "vocabulary_preferences": {
      "register": "elevated_but_accessible",
      "technical_terms": "minimal_contextual",
      "metaphor_frequency": "moderate_meaningful",
      "sensory_language": "rich_evocative"
    },
    "narrative_techniques": {
      "point_of_view": "close_third_person_limited",
      "tense_preference": "past_tense_primary",
      "dialogue_style": "realistic_subtext_heavy",
      "description_balance": "character_focused_selective_detail"
    }
  },
  "thematic_integration": {
    "theme_development": "subtle_layered_symbolic",
    "motif_usage": "recurring_meaningful_patterns",
    "symbolism": "integrated_not_heavy_handed",
    "emotional_depth": "complex_nuanced_authentic"
  },
  "pacing_preferences": {
    "overall_rhythm": "contemplative_with_dynamic_moments",
    "scene_transitions": "smooth_thematic_connections",
    "tension_building": "psychological_gradual",
    "revelation_style": "layered_interpretive"
  },
  "genre_adaptations": {
    "mystery_elements": {
      "clue_presentation": "subtle_psychological",
      "red_herrings": "character_motivation_based",
      "resolution_style": "emotional_truth_over_plot_mechanics"
    }
  }
}
```

## System Configuration

### Workflow Configuration

```json
{
  "workflow_config": {
    "phase_settings": {
      "outline_development": {
        "max_iterations": 5,
        "timeout_per_iteration": "30_minutes",
        "required_approvals": ["user", "majority_raters"],
        "quality_gate_threshold": 6.0
      },
      "chapter_development": {
        "max_iterations": 3,
        "timeout_per_step": "45_minutes",
        "parallel_agent_timeout": "15_minutes",
        "editor_review_required": true
      }
    },
    "agent_coordination": {
      "character_agent_activation": "scene_based_selective",
      "rater_agent_execution": "parallel_with_timeout",
      "memory_sync_frequency": "after_major_updates",
      "error_recovery_mode": "graceful_degradation"
    }
  }
}
```

### Memory Configuration

```json
{
  "memory_config": {
    "context_limits": {
      "working_memory_tokens": 4000,
      "episodic_memory_events": 50,
      "semantic_memory_facts": 200,
      "character_memory_budget": 2000
    },
    "compression_settings": {
      "trigger_threshold": 0.8,
      "compression_ratio": 0.3,
      "importance_weighting": "recency_and_emotional_significance",
      "preservation_criteria": ["user_marked_important", "character_defining_moments"]
    },
    "synchronization_rules": {
      "cross_agent_sharing": "observable_events_only",
      "writer_agent_access": "full_omniscient",
      "conflict_resolution": "preserve_subjectivity",
      "update_propagation": "immediate_for_critical_changes"
    }
  }
}
```

## Configuration Management

### Dynamic Loading and Validation

**Configuration Loading Process**:
1. **Schema Validation**: Validate against JSON schemas
2. **Dependency Resolution**: Load inherited and referenced configurations
3. **Conflict Detection**: Identify and resolve configuration conflicts
4. **Runtime Validation**: Verify configuration compatibility with current story
5. **Hot Reloading**: Support configuration updates without system restart

**Validation Rules**:
- All required fields must be present
- Value ranges must be within acceptable limits
- Referenced configurations must exist and be valid
- Circular dependencies must be prevented
- Type constraints must be satisfied

### User Customization

**Customization Levels**:
- **System Level**: Global defaults for all stories
- **User Level**: Personal preferences across stories
- **Story Level**: Specific configurations for individual stories
- **Session Level**: Temporary modifications for current session

**Configuration Override Hierarchy**:
```
Session Config → Story Config → User Config → System Default
```

This configuration system provides comprehensive control over all aspects of the Writer Assistant while maintaining ease of use and consistency across story development.