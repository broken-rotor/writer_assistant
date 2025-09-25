# Memory System Requirements

## Overview

The Writer Assistant implements a sophisticated multi-level memory system that supports agent-specific perspectives, subjective experiences, and efficient context management. The system embraces memory subjectivity as a feature, allowing different characters to have conflicting interpretations of the same events.

## Memory Architecture

### Hierarchical Memory Structure

#### 1. Working Memory (Active Context)
- **Scope**: Last 2-3 chapters + current chapter context
- **Size Limit**: ~2-4K tokens per agent
- **Content**: Recent narrative flow, active character states, current scene context
- **Update Frequency**: Real-time during story generation
- **Purpose**: Immediate context for agent decision-making

#### 2. Episodic Memory (Story Events)
- **Scope**: Key events, character developments, plot points per story arc
- **Content**: Compressed summaries of significant story moments
- **Organization**: Chronological with importance weighting
- **Access Pattern**: Retrieved based on relevance to current scene
- **Purpose**: Maintain story continuity and character development tracking

#### 3. Semantic Memory (Persistent Knowledge)
- **Scope**: Character traits, world rules, established facts
- **Content**: Rarely-changing foundational information
- **Persistence**: Remains stable across entire story
- **Update Pattern**: Only modified when fundamental changes occur
- **Purpose**: Ensure consistency of character and world elements

#### 4. Long-term Memory (Story Archive)
- **Scope**: Complete story history with compressed summaries
- **Content**: Full narrative archive with hierarchical compression
- **Access**: Retrieved for continuity checking and reference
- **Storage**: Efficient compression algorithms for large stories
- **Purpose**: Complete story preservation and deep continuity

### Agent-Specific Memory Implementation

#### Character Agent Memory

**Personal Memory Structure**:
```json
{
  "agent_id": "character_john",
  "memory_type": "character_subjective",
  "personal_experiences": {
    "internal_monologue": [
      {
        "chapter": 3,
        "scene": "kitchen_conversation",
        "timestamp": "2025-09-24T10:30:00",
        "thought": "Mary seems suspicious of something",
        "emotional_state": "defensive_anxiety",
        "triggers": ["mary_direct_questions", "letter_mention"],
        "confidence": 0.9,
        "hidden_from_others": true
      }
    ],
    "subjective_events": [
      {
        "event_id": "argument_scene_2",
        "character_interpretation": "Mary was being unreasonably accusatory",
        "emotional_coloring": "hurt_and_defensive",
        "focus_details": ["harsh_tone", "aggressive_posture"],
        "missed_details": ["own_defensiveness", "mary_underlying_worry"],
        "memory_bias": "self_protective_filtering"
      }
    ],
    "relationship_dynamics": {
      "mary": {
        "current_perception": "suspicious_and_critical",
        "emotional_response": "defensive_love",
        "trust_level": 0.6,
        "last_interaction": "tense_kitchen_scene",
        "relationship_trajectory": "declining_trust"
      }
    }
  },
  "observed_reality": {
    "witnessed_events": [...],
    "overheard_conversations": [...],
    "environmental_observations": [...],
    "other_character_behaviors": [...]
  }
}
```

**Memory Characteristics**:
- **Subjective Filtering**: Events filtered through personality and emotional state
- **Bias Patterns**: Consistent with character's psychological profile
- **Selective Attention**: Focus on details relevant to character's concerns
- **Emotional Coloring**: Memory influenced by emotional state during formation
- **Perspective Limitations**: Only knows what character realistically could know

#### Writer Agent Memory

**Omniscient Story Memory**:
```json
{
  "writer_memory": {
    "narrative_state": {
      "current_chapter": 5,
      "active_themes": ["trust", "family_secrets", "redemption"],
      "narrative_tension": 0.8,
      "pacing_notes": "building_to_major_revelation"
    },
    "character_access": {
      "all_perspectives": {
        "john": {
          "internal_state": {...},
          "hidden_motivations": [...],
          "subjective_memories": [...]
        },
        "mary": {
          "internal_state": {...},
          "private_thoughts": [...],
          "emotional_journey": [...]
        }
      },
      "relationship_matrices": {
        "john_mary": {
          "john_perspective": "mary_becoming_suspicious",
          "mary_perspective": "john_hiding_something",
          "objective_reality": "mutual_love_with_communication_breakdown",
          "narrative_potential": "reconciliation_through_truth"
        }
      }
    },
    "story_craft_elements": {
      "foreshadowing_planted": [...],
      "clues_distributed": [...],
      "payoffs_pending": [...],
      "subplot_threads": [...]
    }
  }
}
```

### Memory Integration with LangChain

#### Custom Memory Classes

**BaseStoryMemory Extension**:
```python
# Conceptual structure - not actual code
class CharacterMemory(BaseMemory):
    """Character-specific memory with subjective filtering"""
    
    def __init__(self, character_id, personality_config):
        self.character_id = character_id
        self.personality_filter = personality_config
        self.working_memory = WorkingMemory()
        self.episodic_memory = EpisodicMemory()
        self.semantic_memory = SemanticMemory()
    
    def add_memory(self, event, context):
        # Apply personality-based filtering
        filtered_event = self.apply_personality_filter(event)
        # Store in appropriate memory level
        self.store_memory(filtered_event, context)
    
    def retrieve_relevant_context(self, current_scene):
        # Intelligent context selection based on relevance
        return self.select_context(current_scene)
```

**Memory Synchronization Protocol**:
- **Character → Writer**: All internal states and subjective memories flow to writer
- **Writer → Characters**: Objective story events and scene outcomes
- **Cross-Character**: Only observable actions and dialogue
- **Memory Conflicts**: Preserved as feature rather than resolved

### Memory Persistence and Export

#### JSON Export Structure

**Complete Memory State**:
```json
{
  "story_memory_export": {
    "metadata": {
      "export_timestamp": "2025-09-24T15:30:00Z",
      "story_id": "story_uuid_123",
      "memory_version": "1.0",
      "compression_level": "standard"
    },
    "agent_memories": {
      "writer_agent": {
        "omniscient_memory": {...},
        "narrative_state": {...},
        "craft_elements": {...}
      },
      "character_agents": {
        "john_smith": {
          "subjective_memory": {...},
          "personality_state": {...},
          "relationship_tracking": {...}
        },
        "mary_jones": {
          "subjective_memory": {...},
          "emotional_journey": {...},
          "perspective_evolution": [...]
        }
      },
      "rater_agents": {
        "consistency_rater": {
          "evaluation_history": [...],
          "pattern_recognition": {...},
          "feedback_tracking": [...]
        }
      }
    },
    "shared_memory_elements": {
      "story_timeline": [...],
      "world_state": {...},
      "established_facts": [...]
    }
  }
}
```

#### Memory Reconstruction

**Import Process Requirements**:
- **Schema Validation**: Ensure imported memory matches expected structure
- **Memory Integrity Checking**: Verify consistency and completeness
- **Agent Re-initialization**: Restore agent states with proper memory context
- **Workflow State Recovery**: Resume story development at correct phase
- **Graceful Degradation**: Handle missing or corrupted memory sections

### Memory Management Strategies

#### Context Window Optimization

**Dynamic Context Selection**:
- **Relevance Scoring**: Prioritize memories most relevant to current scene
- **Temporal Proximity**: Weight recent events higher than distant ones
- **Character Focus**: Load character-specific memories when they're active
- **Emotional Significance**: Preserve emotionally important memories longer
- **Plot Thread Tracking**: Maintain memories related to active storylines

**Memory Compression Techniques**:
- **Semantic Compression**: Combine similar memories into representative forms
- **Event Summarization**: Compress sequences of related events
- **Character State Deltas**: Store changes rather than complete states
- **Importance Weighting**: Preserve critical memories in detail

#### Performance Requirements

**Memory Access Patterns**:
- **Lazy Loading**: Load memory components only when needed
- **Predictive Caching**: Anticipate memory needs based on story progression
- **Memory Pooling**: Reuse memory objects to reduce allocation
- **Background Compression**: Compress old memories during idle time

**Resource Limits**:
- **Per-Agent Memory Budget**: Maximum memory allocation per agent type
- **Context Window Limits**: Stay within LLM context constraints
- **Storage Efficiency**: Minimize memory footprint while preserving quality
- **Access Speed**: Sub-second memory retrieval for real-time generation

### Memory Debugging and Monitoring

#### Development Tools

**Memory Inspector**:
- **Agent Memory Viewer**: Examine current memory state for any agent
- **Memory Timeline**: Track memory formation and evolution over time
- **Consistency Checker**: Identify potential memory conflicts or errors
- **Performance Monitor**: Track memory usage and access patterns

**Memory Testing Framework**:
- **Memory Scenarios**: Test memory behavior with predefined scenarios
- **Consistency Validation**: Automated testing for memory coherence
- **Performance Benchmarks**: Memory access and storage performance testing
- **Error Recovery Testing**: Validate graceful handling of memory issues

### Advanced Memory Features

#### Subjective Experience Modeling

**Perspective Authenticity**:
- **Personality Filters**: Events interpreted through character personality lens
- **Emotional State Influence**: Memory formation affected by emotional context
- **Attention Bias**: Characters notice different details based on focus areas
- **Memory Reliability**: Some characters more reliable narrators than others

**Memory Evolution**:
- **Reinterpretation**: Past memories may be reinterpreted based on new information
- **Emotional Processing**: Traumatic memories may change over time
- **Relationship Impact**: Memories of shared events evolve with relationship changes
- **Growth Reflection**: Character development reflected in memory interpretation

This memory system ensures that each agent maintains authentic, subjective experiences while providing the writer agent with comprehensive access to all perspectives for rich, multi-layered storytelling.