"""
Context Models for Writer Assistant API.

This module defines enums and configuration classes for context processing.

Legacy structured context models (StructuredContextContainer, PlotElement, CharacterContext, 
UserRequest, SystemInstruction) have been removed in B4. Use RequestContext from 
app.models.request_context instead.

Classes in this module:
- ContextType: Enum of context element types
- SummarizationRule: Enum of summarization strategies
- AgentType: Enum of agent types
- ContextProcessingConfig: Configuration for context processing
"""

from typing import Dict, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


# Context Element Types Taxonomy
class ContextType(str, Enum):
    """Hierarchical taxonomy of context element types."""

    # System-level contexts (prompts, instructions, preferences)
    SYSTEM_PROMPT = "system_prompt"
    SYSTEM_INSTRUCTION = "system_instruction"
    SYSTEM_PREFERENCE = "system_preference"

    # Story-level contexts (world-building, themes, narrative state)
    WORLD_BUILDING = "world_building"
    STORY_THEME = "story_theme"
    NARRATIVE_STATE = "narrative_state"
    STORY_SUMMARY = "story_summary"
    PLOT_OUTLINE = "plot_outline"

    # Character-level contexts (personalities, relationships, memories)
    CHARACTER_PROFILE = "character_profile"
    CHARACTER_RELATIONSHIP = "character_relationship"
    CHARACTER_MEMORY = "character_memory"
    CHARACTER_STATE = "character_state"

    # User-level contexts (preferences, feedback, requests)
    USER_PREFERENCE = "user_preference"
    USER_FEEDBACK = "user_feedback"
    USER_REQUEST = "user_request"
    USER_INSTRUCTION = "user_instruction"

    # Phase-level contexts (outline, chapter, editing instructions)
    PHASE_INSTRUCTION = "phase_instruction"
    PHASE_OUTPUT = "phase_output"
    PHASE_GUIDANCE = "phase_guidance"

    # Conversation contexts
    CONVERSATION_HISTORY = "conversation_history"
    CONVERSATION_CONTEXT = "conversation_context"


class SummarizationRule(str, Enum):
    """Rules for how context elements should be summarized when token limits are approached."""
    PRESERVE_FULL = "preserve_full"  # Never summarize, always include in full
    ALLOW_COMPRESSION = "allow_compression"  # Can be compressed but key info preserved
    EXTRACT_KEY_POINTS = "extract_key_points"  # Extract only the most important points
    OMIT_IF_NEEDED = "omit_if_needed"  # Can be completely omitted if necessary


class AgentType(str, Enum):
    """Types of agents that can consume context."""
    WRITER = "writer"
    CHARACTER = "character"
    RATER = "rater"
    EDITOR = "editor"
    WORLDBUILDING = "worldbuilding"


# Context Processing Configuration
class ContextProcessingConfig(BaseModel):
    """Configuration for how context should be processed and filtered."""

    target_agent: AgentType = Field(
        description="Target agent type for context processing"
    )

    max_tokens: Optional[int] = Field(
        default=None,
        description="Maximum tokens allowed for context"
    )

    prioritize_recent: bool = Field(
        default=True,
        description="Whether to prioritize more recently updated elements"
    )

    include_relationships: bool = Field(
        default=True,
        description="Whether to include related context elements"
    )

    summarization_threshold: float = Field(
        default=0.8,
        description="Token usage threshold at which summarization begins"
    )

    custom_filters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom filtering criteria"
    )
