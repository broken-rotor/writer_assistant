"""
Structured Context Data Models for Writer Assistant API.

DEPRECATION NOTICE:
===================
The StructuredContextContainer and related element types in this module are DEPRECATED
as of January 2025 and will be removed in a future version.

Please use the new typed collections model from app.models.generation_models instead:
- app.models.generation_models.StructuredContextContainer (new model)
- app.models.generation_models.PlotElement (replaces StoryContextElement)
- app.models.generation_models.CharacterContext (replaces CharacterContextElement)
- app.models.generation_models.UserRequest (replaces UserContextElement)
- app.models.generation_models.SystemInstruction (replaces SystemContextElement)

Migration Guide: backend/STRUCTURED_CONTEXT_MIGRATION_GUIDE.md
Reference: backend/STRUCTURED_CONTEXT_REFERENCE.md

DEPRECATED CLASSES IN THIS MODULE:
- StructuredContextContainer (use generation_models.StructuredContextContainer)
- BaseContextElement (no direct replacement - use typed collections)
- SystemContextElement (use SystemInstruction)
- StoryContextElement (use PlotElement)
- CharacterContextElement (use CharacterContext)
- UserContextElement (use UserRequest)
- PhaseContextElement (use SystemInstruction or PlotElement)
- ConversationContextElement (use SystemInstruction or PlotElement)
- ContextMetadata (use generation_models element fields)
- ContextRelationship (use CharacterContext.relationships)

This module defines the old structured context schema to replace monolithic text fields
(systemPrompts, worldbuilding, storySummary) with granular, manageable context elements.

The schema supports:
- Hierarchical context organization
- Context prioritization and summarization
- Agent-specific context filtering
- Phase-aware context management
- Backward compatibility with existing PhaseContext system
"""

import warnings
from typing import Dict, List, Optional, Any, Literal, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone
from enum import Enum

# Deprecation warning for the entire module
warnings.warn(
    "app.models.context_models.StructuredContextContainer and related classes are deprecated. "
    "Use app.models.generation_models.StructuredContextContainer with typed collections instead. "
    "See backend/STRUCTURED_CONTEXT_MIGRATION_GUIDE.md for migration instructions.",
    DeprecationWarning,
    stacklevel=2
)


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


class ComposePhase(str, Enum):
    """Three-phase compose system phases."""
    PLOT_OUTLINE = "plot_outline"
    CHAPTER_DETAIL = "chapter_detail"
    FINAL_EDIT = "final_edit"


# Base Context Element
class ContextMetadata(BaseModel):
    """
    Metadata for context elements supporting prioritization and summarization.

    DEPRECATED: This class is deprecated. Use the priority and metadata fields
    directly on the new model element types (PlotElement, CharacterContext, etc.)
    from app.models.generation_models instead.
    """

    priority: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Priority weight for token budget management (0.0-1.0)"
    )

    summarization_rule: SummarizationRule = Field(
        default=SummarizationRule.ALLOW_COMPRESSION,
        description="How this context should be handled when summarization is needed"
    )

    target_agents: List[AgentType] = Field(
        default_factory=lambda: [AgentType.WRITER],
        description="Which agent types should receive this context"
    )

    relevant_phases: List[ComposePhase] = Field(
        default_factory=lambda: [ComposePhase.PLOT_OUTLINE, ComposePhase.CHAPTER_DETAIL, ComposePhase.FINAL_EDIT],
        description="Which compose phases this context is relevant for"
    )

    estimated_tokens: Optional[int] = Field(
        default=None,
        description="Estimated token count for budget planning"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        description="When this context element was created"
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        description="When this context element was last updated"
    )

    expires_at: Optional[datetime] = Field(
        default=None,
        description="When this context element expires (optional)"
    )

    tags: List[str] = Field(
        default_factory=list,
        description="Tags for categorization and filtering"
    )


class BaseContextElement(BaseModel):
    """
    Base class for all context elements.

    DEPRECATED: This class is deprecated. Use typed collections from
    app.models.generation_models instead (PlotElement, CharacterContext,
    UserRequest, SystemInstruction).
    """

    id: str = Field(
        description="Unique identifier for this context element"
    )

    type: ContextType = Field(
        description="Type of context element from the taxonomy"
    )

    content: str = Field(
        description="The actual content of this context element"
    )

    metadata: ContextMetadata = Field(
        default_factory=ContextMetadata,
        description="Metadata for prioritization and management"
    )

    source: Optional[str] = Field(
        default=None,
        description="Source of this context (user, agent, system, etc.)"
    )

    version: int = Field(
        default=1,
        description="Version number for tracking changes"
    )


# Specialized Context Elements
class SystemContextElement(BaseContextElement):
    """
    Context elements for system-level prompts and instructions.

    DEPRECATED: Use app.models.generation_models.SystemInstruction instead.
    """

    type: Literal[
        ContextType.SYSTEM_PROMPT,
        ContextType.SYSTEM_INSTRUCTION,
        ContextType.SYSTEM_PREFERENCE
    ]

    prompt_type: Optional[str] = Field(
        default=None,
        description="Specific type of system prompt (main_prefix, main_suffix, assistant_prompt, etc.)"
    )

    applies_to_agents: List[AgentType] = Field(
        default_factory=lambda: [AgentType.WRITER],
        description="Which agents this system context applies to"
    )


class StoryContextElement(BaseContextElement):
    """
    Context elements for story-level information.

    DEPRECATED: Use app.models.generation_models.PlotElement instead.
    """

    type: Literal[
        ContextType.WORLD_BUILDING,
        ContextType.STORY_THEME,
        ContextType.NARRATIVE_STATE,
        ContextType.STORY_SUMMARY,
        ContextType.PLOT_OUTLINE
    ]

    story_aspect: Optional[str] = Field(
        default=None,
        description="Specific aspect of the story (setting, magic_system, politics, etc.)"
    )

    chapter_relevance: Optional[List[int]] = Field(
        default=None,
        description="Which chapters this context is most relevant for"
    )


class CharacterContextElement(BaseContextElement):
    """
    Context elements for character-specific information.

    DEPRECATED: Use app.models.generation_models.CharacterContext instead.
    """

    type: Literal[
        ContextType.CHARACTER_PROFILE,
        ContextType.CHARACTER_RELATIONSHIP,
        ContextType.CHARACTER_MEMORY,
        ContextType.CHARACTER_STATE
    ]

    character_id: str = Field(
        description="ID of the character this context relates to"
    )

    character_name: str = Field(
        description="Name of the character for easy reference"
    )

    related_characters: List[str] = Field(
        default_factory=list,
        description="IDs of other characters related to this context"
    )

    is_subjective: bool = Field(
        default=False,
        description="Whether this context represents a character's subjective view"
    )


class UserContextElement(BaseContextElement):
    """
    Context elements for user preferences, feedback, and requests.

    DEPRECATED: Use app.models.generation_models.UserRequest instead.
    """

    type: Literal[
        ContextType.USER_PREFERENCE,
        ContextType.USER_FEEDBACK,
        ContextType.USER_REQUEST,
        ContextType.USER_INSTRUCTION
    ]

    user_intent: Optional[str] = Field(
        default=None,
        description="The user's intent behind this context"
    )

    feedback_type: Optional[str] = Field(
        default=None,
        description="Type of feedback (positive, negative, suggestion, etc.)"
    )

    incorporated: bool = Field(
        default=False,
        description="Whether this feedback has been incorporated"
    )


class PhaseContextElement(BaseContextElement):
    """
    Context elements for phase-specific instructions and outputs.

    DEPRECATED: Use app.models.generation_models.SystemInstruction or PlotElement instead.
    """

    type: Literal[
        ContextType.PHASE_INSTRUCTION,
        ContextType.PHASE_OUTPUT,
        ContextType.PHASE_GUIDANCE
    ]

    phase: ComposePhase = Field(
        description="Which compose phase this context relates to"
    )

    previous_phase_output: Optional[str] = Field(
        default=None,
        description="Output from the previous phase"
    )


class ConversationContextElement(BaseContextElement):
    """
    Context elements for conversation history and context.

    DEPRECATED: Use app.models.generation_models.SystemInstruction or PlotElement instead.
    """

    type: Literal[
        ContextType.CONVERSATION_HISTORY,
        ContextType.CONVERSATION_CONTEXT
    ]

    conversation_id: Optional[str] = Field(
        default=None,
        description="ID of the conversation this context relates to"
    )

    participant_roles: List[str] = Field(
        default_factory=list,
        description="Roles of conversation participants (user, assistant, character, etc.)"
    )

    message_count: Optional[int] = Field(
        default=None,
        description="Number of messages in the conversation"
    )


# Context Relationships
class ContextRelationship(BaseModel):
    """
    Defines relationships between context elements.

    DEPRECATED: Use CharacterContext.relationships (Dict[str, str]) instead
    for character relationships.
    """

    source_id: str = Field(description="ID of the source context element")
    target_id: str = Field(description="ID of the target context element")
    relationship_type: str = Field(description="Type of relationship (depends_on, conflicts_with, enhances, etc.)")
    strength: float = Field(default=1.0, ge=0.0, le=1.0, description="Strength of the relationship")
    description: Optional[str] = Field(default=None, description="Description of the relationship")


# Main Structured Context Container
class StructuredContextContainer(BaseModel):
    """
    Main container for all structured context elements.

    DEPRECATED: This class is deprecated as of January 2025.

    Use app.models.generation_models.StructuredContextContainer instead, which uses
    typed collections (plot_elements, character_contexts, user_requests, system_instructions)
    instead of a generic elements list.

    Migration Guide: backend/STRUCTURED_CONTEXT_MIGRATION_GUIDE.md

    Old Model (DEPRECATED):
        container = StructuredContextContainer(elements=[...])

    New Model (USE THIS):
        from app.models.generation_models import StructuredContextContainer
        container = StructuredContextContainer(
            plot_elements=[...],
            character_contexts=[...],
            user_requests=[...],
            system_instructions=[...]
        )
    """

    elements: List[Union[
        SystemContextElement,
        StoryContextElement,
        CharacterContextElement,
        UserContextElement,
        PhaseContextElement,
        ConversationContextElement
    ]] = Field(
        default_factory=list,
        description="List of all context elements"
    )

    relationships: List[ContextRelationship] = Field(
        default_factory=list,
        description="Relationships between context elements"
    )

    global_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Global metadata for the entire context container"
    )

    total_estimated_tokens: Optional[int] = Field(
        default=None,
        description="Total estimated tokens for all context elements"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        description="When this context container was created"
    )

    version: str = Field(
        default="1.0",
        description="Version of the context schema"
    )

    def get_elements_by_type(self, context_type: ContextType) -> List[BaseContextElement]:
        """Get all context elements of a specific type."""
        return [element for element in self.elements if element.type == context_type]

    def get_elements_for_agent(self, agent_type: AgentType) -> List[BaseContextElement]:
        """Get all context elements relevant for a specific agent type."""
        return [
            element for element in self.elements
            if agent_type in element.metadata.target_agents
        ]

    def get_elements_for_phase(self, phase: ComposePhase) -> List[BaseContextElement]:
        """Get all context elements relevant for a specific compose phase."""
        return [
            element for element in self.elements
            if phase in element.metadata.relevant_phases
        ]

    def get_high_priority_elements(self, threshold: float = None) -> List[BaseContextElement]:
        """Get context elements with priority above the threshold."""
        if threshold is None:
            from app.core.config import settings
            threshold = settings.CONTEXT_HIGH_PRIORITY_THRESHOLD
        return [
            element for element in self.elements
            if element.metadata.priority >= threshold
        ]

    def calculate_total_tokens(self) -> int:
        """Calculate total estimated tokens for all elements."""
        total = 0
        for element in self.elements:
            if element.metadata.estimated_tokens:
                total += element.metadata.estimated_tokens
            else:
                # Rough estimate: 4 characters per token
                total += len(element.content) // 4
        return total

    @field_validator('elements')
    @classmethod
    def validate_unique_ids(cls, v):
        """Ensure all context element IDs are unique."""
        ids = [element.id for element in v]
        if len(ids) != len(set(ids)):
            raise ValueError("All context element IDs must be unique")
        return v



# Context Processing Configuration
class ContextProcessingConfig(BaseModel):
    """Configuration for how context should be processed and filtered."""

    target_agent: AgentType = Field(
        description="Target agent type for context processing"
    )

    current_phase: ComposePhase = Field(
        description="Current compose phase"
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
