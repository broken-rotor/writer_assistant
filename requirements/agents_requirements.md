# Agent System Requirements

## Overview

The Writer Assistant employs a multi-agent system where each agent has specialized roles, individual memory systems, and unique perspectives on story development. Agents collaborate through LangGraph workflows while maintaining their distinct viewpoints and expertise areas.

## Agent Types and Responsibilities

### 1. Writer Agent (Main Orchestrator)

**Primary Role**: Main story generator that synthesizes inputs from all other agents

**Core Responsibilities**:
- Generate story outlines based on user guidance
- Create detailed chapter content with character perspectives
- Access and synthesize all character internal monologues and memories
- Maintain narrative coherence and story progression
- Coordinate with other agents for comprehensive story development

**Memory Access**:
- **Omniscient Story Memory**: Complete access to all character memories and internal states
- **Narrative Craft Memory**: Track foreshadowing, themes, and story techniques
- **User Preference Memory**: Remember user feedback and story direction preferences
- **Revision History**: Track changes and improvements over story development

**Output Formats**:
- Story outlines with plot structure and character arcs
- Detailed chapter content with multi-perspective integration
- Revision responses incorporating feedback from raters and editor

### 2. Character Sub-Agents

**Primary Role**: Maintain individual character perspectives and authentic subjective experiences

**Core Responsibilities**:
- Generate authentic character-specific internal monologues
- Maintain character-consistent memory interpretation and bias
- Track individual character emotional journeys and growth
- Provide character-specific reactions to story events
- Ensure personality consistency across story development

**Individual Character Memory Structure**:
```json
{
  "personal_memory": {
    "internal_monologue": [...],
    "subjective_experiences": [...],
    "private_knowledge": [...],
    "emotional_states": [...],
    "personality_evolution": [...]
  },
  "observed_events": {
    "recent_summary": "...",
    "witnessed_actions": [...],
    "overheard_conversations": [...],
    "environmental_changes": [...]
  },
  "relationship_dynamics": {
    "character_name": {
      "perceived_relationship": "...",
      "hidden_feelings": "...",
      "interaction_history": [...],
      "trust_level": 0.7
    }
  }
}
```

**Key Features**:
- **Subjective Memory**: Characters remember events through their personality lens
- **Emotional Filtering**: Memory colored by emotional state during event
- **Knowledge Limitations**: Only know what they realistically could know
- **Perspective Authenticity**: Maintain character-specific viewpoints and biases

### 3. Rater Agents (Multi-Perspective Critics)

**Primary Role**: Provide specialized feedback from different evaluation perspectives

#### 3.1 Character Consistency Rater

**Focus Areas**:
- Character voice and personality consistency
- Psychological realism of character memories and reactions
- Character growth trajectory believability
- Dialogue authenticity and character-specific speech patterns

**Evaluation Criteria**:
- Memory authenticity and bias patterns
- Emotional reaction consistency with established personality
- Character development pacing and motivation
- Relationship dynamic believability

#### 3.2 Narrative Flow Rater

**Focus Areas**:
- Reader engagement and story pacing
- Perspective clarity and navigation
- Information revelation timing
- Emotional impact and reader connection

**Evaluation Criteria**:
- Scene transitions and story rhythm
- Perspective shift smoothness
- Reader confusion prevention
- Tension building and release patterns

#### 3.3 Literary Quality Rater

**Focus Areas**:
- Thematic depth and integration
- Artistic merit and originality
- Prose quality and style consistency
- Sophisticated narrative techniques

**Evaluation Criteria**:
- Theme development and symbolic resonance
- Unreliable narrator effectiveness
- Perspective sophistication and complexity
- Writing craft and technical execution

#### 3.4 Genre-Specific Raters

**Configurable Based on Story Genre**:
- Mystery: Clue management, red herrings, fair play principle
- Romance: Relationship development, emotional satisfaction, chemistry
- Thriller: Tension maintenance, pacing, suspense building
- Literary Fiction: Character depth, thematic complexity, artistic merit

### 4. Editor Agent (Final Quality Gate)

**Primary Role**: Ensure overall story consistency, tone coherence, and narrative flow

**Core Responsibilities**:
- Verify adherence to approved story outline
- Check continuity and consistency across chapters
- Maintain tone and voice consistency throughout story
- Ensure narrative coherence and logical progression
- Provide final technical polish before user presentation

**Review Criteria**:
```json
{
  "consistency_checking": {
    "plot_continuity": "Do events unfold logically?",
    "character_consistency": "Are characters behaving consistently?",
    "world_consistency": "Do setting and rules remain stable?",
    "timeline_verification": "Is sequence of events logical?"
  },
  "tone_maintenance": {
    "voice_consistency": "Is narrative voice stable?",
    "emotional_tone": "Do emotional beats serve story arc?",
    "style_coherence": "Is writing style consistent?",
    "mood_appropriateness": "Does chapter mood fit progression?"
  },
  "quality_assurance": {
    "outline_adherence": "Does chapter deliver outline promises?",
    "reader_experience": "Will chapter satisfy readers?",
    "professional_polish": "Is content ready for publication?",
    "narrative_flow": "Does chapter flow smoothly to next?"
  }
}
```

## Agent Communication Patterns

### Memory Sharing Protocol

**Character → Writer Agent**:
- Internal monologues and private thoughts
- Subjective memory interpretations
- Character-specific emotional responses
- Hidden motivations and desires

**Character → Character** (Limited):
- Only observable actions and dialogue
- Public reactions and behaviors
- Shared experiences from different perspectives

**Writer → All Agents**:
- Narrative decisions and story direction
- Scene outcomes and plot developments
- User feedback and revision requirements

**Rater → Writer** (Direct Feedback):
- Specific improvement suggestions
- Quality assessments and ratings
- Problem identification and solutions
- Opportunity highlighting

**Editor → Writer**:
- Consistency issues and corrections
- Tone and coherence adjustments
- Technical polish requirements
- Final approval or revision requests

### Workflow Coordination

**Agent Activation Patterns**:
- Scene-based activation (only relevant character agents)
- Parallel processing where appropriate
- Sequential review stages (raters → editor)
- Conditional flows based on story needs and feedback

**Conflict Resolution**:
- Writer agent synthesizes conflicting perspectives
- Editor agent provides final consistency arbitration
- User preferences override agent recommendations
- Compromise solutions addressing multiple concerns

## Agent Configuration Requirements

### Personality Configuration

**Character Agents**:
```json
{
  "character_id": "john_smith",
  "personality_traits": {
    "core_traits": ["introverted", "analytical", "protective"],
    "emotional_patterns": ["tends_to_internalize", "conflict_avoidant"],
    "speech_patterns": ["formal", "precise", "understated"],
    "bias_tendencies": ["defensive_attribution", "protective_filtering"]
  },
  "background": {
    "age": 34,
    "occupation": "software_engineer",
    "key_experiences": [...],
    "relationships": {...},
    "fears_and_desires": [...]
  },
  "memory_characteristics": {
    "reliability_level": 0.8,
    "emotional_filtering": "high",
    "attention_focus": ["technical_details", "relationship_dynamics"],
    "bias_patterns": ["confirmation_bias", "self_protective"]
  }
}
```

**Rater Agents**:
```json
{
  "rater_id": "character_consistency_expert",
  "evaluation_focus": {
    "primary_criteria": ["authenticity", "consistency", "psychological_realism"],
    "weight_preferences": {
      "character_voice": 0.9,
      "memory_authenticity": 0.8,
      "growth_believability": 0.7
    }
  },
  "feedback_style": {
    "tone": "analytical_constructive",
    "directness": 0.7,
    "encouragement_level": 0.5,
    "detail_level": "comprehensive"
  },
  "standards": {
    "quality_threshold": 7.0,
    "consistency_tolerance": 0.2,
    "improvement_focus": "character_development"
  }
}
```

## Agent Performance Requirements

### Response Quality
- Character agents must maintain personality consistency across all interactions
- Rater agents must provide actionable, specific feedback
- Writer agent must effectively synthesize multiple perspectives
- Editor agent must catch consistency errors and quality issues

### Performance Metrics
- Response time: < 30 seconds for chapter generation
- Memory efficiency: < 4KB context per agent per chapter
- Consistency scores: > 85% character consistency across story
- User satisfaction: > 4.0/5.0 rating on generated content

### Error Handling
- Graceful degradation when agents encounter errors
- Recovery procedures for memory corruption or inconsistencies
- Fallback modes when specific agents are unavailable
- User notification for system limitations or issues