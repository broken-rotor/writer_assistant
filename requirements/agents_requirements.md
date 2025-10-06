# Agent System Requirements

## Overview

The Writer Assistant employs a user-driven multi-agent system where specialized agents provide their unique perspectives and expertise only when selected and engaged by the user. Each agent maintains individual memory systems and distinct viewpoints, with all agent interactions subject to user control, selection, and approval.

## Agent Types and Responsibilities

### 1. Writer Agent (User-Directed Content Generator)

**Primary Role**: Generate story content based on user direction and selectively incorporate user-chosen agent inputs

**Core Responsibilities**:
- Generate expanded story drafts from user-provided themes, topics, or outlines
- Create detailed content incorporating only user-selected character responses
- Access memories and perspectives only when user grants permission
- Revise content based on user-specified modifications and feedback
- Respond to user requests for specific changes or improvements
- Synthesize only user-approved inputs from other agents

**User-Controlled Memory Access**:
- **User-Granted Story Memory**: Access to character memories only when user permits
- **User-Directed Narrative Memory**: Track only user-approved themes and techniques
- **User Preference Memory**: Remember all user feedback and decisions
- **User-Visible Revision History**: Complete transparent tracking of all changes and user decisions

**User-Requested Output Formats**:
- Expanded story drafts based on user input
- Detailed content incorporating user-selected character inputs
- Revision responses addressing user-specified modifications
- Final polished content incorporating user-chosen feedback

### 2. Character Sub-Agents (User-Interactive Character Voices)

**Primary Role**: Engage in direct dialog with users while maintaining authentic character perspectives

**Core Responsibilities**:
- React to user-proposed story events and outlines from character perspective
- Engage in iterative dialog with users about story developments
- Provide character-specific insights and concerns about proposed plot points
- Maintain character-consistent responses throughout user conversations
- Present authentic character viewpoints for user consideration
- Respond to user questions about character motivations and reactions

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

## User-Mediated Agent Communication Patterns

### User-Controlled Interaction Protocol

**Character Agents → User** (Direct Dialog):
- Character reactions to user-proposed story events
- Responses to user questions about character perspectives
- Character-specific concerns and insights about plot developments
- Direct conversation about character motivations and feelings

**User → Character Agents** (Interactive Dialog):
- Questions about character reactions and motivations
- Requests for character perspectives on story events
- Iterative conversation to explore character viewpoints
- User feedback on character responses and authenticity

**User → Writer Agent** (Content Direction):
- Story themes, topics, and outline proposals
- Specific content modification requests
- Selection of character responses to incorporate
- Approval or rejection of generated content

**Feedback Agents → User** (When Requested):
- Quality assessments and improvement suggestions
- Specific problem identification and solutions
- Evaluations based on user-selected criteria
- Recommendations for story enhancement

**User → All Agents** (Central Control):
- Agent selection and activation decisions
- Memory access permissions and restrictions
- Workflow direction and progression choices
- Final approval for all agent outputs

### User-Directed Workflow Coordination

**User-Controlled Agent Activation**:
- User selects which character agents to engage for each story phase
- User decides when to request feedback from rater and editor agents
- User controls parallel vs. sequential agent engagement
- User determines workflow progression based on their satisfaction with outputs

**User-Centered Conflict Resolution**:
- User reviews all agent perspectives and makes final decisions
- User chooses which agent recommendations to follow or ignore
- User preferences always take precedence over agent suggestions
- User creates custom solutions by selecting elements from different agent outputs

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