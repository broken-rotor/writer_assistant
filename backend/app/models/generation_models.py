"""
Pydantic models for generation API requests and responses.
Based on the requirements in api_requirements.md and ui_requirements.md.

Updated for Phase 2.2: Backend API Migration to Structured Context Only.
All API endpoints now accept only structured context data.

The structured context approach uses granular, structured elements that enable
better context management and preservation:

## Structured Context Format

All requests must include a `structured_context` field with the following structure:

```json
{
  "structured_context": {
    "plot_elements": [
      {
        "type": "scene",
        "content": "The hero enters the dark forest",
        "priority": "high",
        "tags": ["current_scene"]
      }
    ],
    "character_contexts": [
      {
        "character_id": "hero",
        "character_name": "Aria",
        "current_state": {"emotion": "determined", "location": "forest_edge"},
        "goals": ["Find the ancient artifact"]
      }
    ],
    "user_requests": [
      {
        "type": "general",
        "content": "Focus on atmospheric details",
        "priority": "medium"
      }
    ],
    "system_instructions": [
      {
        "type": "behavior",
        "content": "Write in third person narrative",
        "scope": "global",
        "priority": "high"
      }
    ]
  }
}
```

## Context Processing

The `context_processing_config` field allows fine-tuned control over how context is processed:

```json
{
  "context_processing_config": {
    "summarization_enabled": true,
    "max_context_length": 4000,
    "priority_filtering": true,
    "character_focus": ["main_character", "antagonist"]
  }
}
```
"""
from typing import Dict, List, Optional, Any, Literal, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime, timezone
from enum import Enum


# Essential Enums from context_models for backward compatibility

class ContextType(str, Enum):
    """Hierarchical taxonomy of context element types."""
    # System-level contexts
    SYSTEM_PROMPT = "system_prompt"
    SYSTEM_INSTRUCTION = "system_instruction"
    SYSTEM_PREFERENCE = "system_preference"
    
    # Story-level contexts
    WORLD_BUILDING = "world_building"
    STORY_THEME = "story_theme"
    NARRATIVE_STATE = "narrative_state"
    STORY_SUMMARY = "story_summary"
    PLOT_OUTLINE = "plot_outline"
    
    # Character-level contexts
    CHARACTER_PROFILE = "character_profile"
    CHARACTER_RELATIONSHIP = "character_relationship"
    CHARACTER_MEMORY = "character_memory"
    CHARACTER_STATE = "character_state"
    
    # User-level contexts
    USER_PREFERENCE = "user_preference"
    USER_FEEDBACK = "user_feedback"
    USER_REQUEST = "user_request"
    USER_INSTRUCTION = "user_instruction"
    
    # Phase-level contexts
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


# Enhanced Metadata Models

class EnhancedContextMetadata(BaseModel):
    """Enhanced metadata for context elements supporting prioritization and summarization."""
    
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


# System Prompts Configuration
class SystemPrompts(BaseModel):
    mainPrefix: str = ""
    mainSuffix: str = ""
    assistantPrompt: Optional[str] = None
    editorPrompt: Optional[str] = None


# Character Models
class CharacterInfo(BaseModel):
    name: str
    basicBio: str
    sex: str = ""
    gender: str = ""
    sexualPreference: str = ""
    age: int = 0
    physicalAppearance: str = ""
    usualClothing: str = ""
    personality: str = ""
    motivations: str = ""
    fears: str = ""
    relationships: str = ""


class ChapterInfo(BaseModel):
    number: int
    title: str
    content: str


class FeedbackItem(BaseModel):
    source: str
    type: str
    content: str
    incorporated: bool = True


# Phase-specific models for three-phase compose system
# ComposePhase is now defined as an Enum above for enhanced functionality


class ConversationMessage(BaseModel):
    role: Literal['user', 'assistant']
    content: str
    timestamp: Optional[str] = None


class PhaseContext(BaseModel):
    previous_phase_output: Optional[str] = None
    phase_specific_instructions: Optional[str] = None
    conversation_history: Optional[List[ConversationMessage]] = None
    conversation_branch_id: Optional[str] = None


# Structured Context Models
class PlotElement(BaseModel):
    """Individual plot element with enhanced metadata."""
    id: Optional[str] = Field(
        None, description="Unique identifier for the plot element")
    type: Literal["scene", "conflict", "resolution", "twist", "setup", "payoff", "transition"] = Field(
        description="Type of plot element"
    )
    content: str = Field(description="The actual plot content or description")
    priority: Literal["high", "medium", "low"] = Field(
        default="medium",
        description="Priority level for context inclusion"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for categorization and filtering"
    )
    metadata: Optional[EnhancedContextMetadata] = Field(
        default=None,
        description="Enhanced metadata for context processing"
    )
    
    # Legacy metadata field for backward compatibility
    legacy_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional legacy metadata for the plot element"
    )


class CharacterContext(BaseModel):
    """Character-specific context information with enhanced metadata."""
    character_id: str = Field(
        description="Unique identifier for the character")
    character_name: str = Field(description="Character name")
    current_state: Dict[str, Any] = Field(
        default_factory=dict,
        description="Current emotional, physical, and mental state"
    )
    recent_actions: List[str] = Field(
        default_factory=list,
        description="Recent actions taken by the character"
    )
    relationships: Dict[str, str] = Field(
        default_factory=dict,
        description="Current relationship dynamics with other characters"
    )
    goals: List[str] = Field(
        default_factory=list,
        description="Character's current goals and motivations"
    )
    memories: List[str] = Field(
        default_factory=list,
        description="Relevant memories that should influence behavior"
    )
    personality_traits: List[str] = Field(
        default_factory=list,
        description="Active personality traits relevant to current context"
    )
    metadata: Optional[EnhancedContextMetadata] = Field(
        default=None,
        description="Enhanced metadata for context processing"
    )


class UserRequest(BaseModel):
    """User-provided request or instruction with enhanced metadata."""
    id: Optional[str] = Field(
        None, description="Unique identifier for the request")
    type: Literal["modification", "addition", "removal", "style_change", "tone_adjustment", "general"] = Field(
        description="Type of user request"
    )
    content: str = Field(description="The actual user request or instruction")
    priority: Literal["high", "medium", "low"] = Field(
        default="medium",
        description="Priority level for request processing"
    )
    target: Optional[str] = Field(
        None,
        description="Specific target of the request (character, scene, etc.)"
    )
    context: Optional[str] = Field(
        None,
        description="Additional context for the request"
    )
    timestamp: Optional[datetime] = Field(
        None,
        description="When the request was made"
    )
    metadata: Optional[EnhancedContextMetadata] = Field(
        default=None,
        description="Enhanced metadata for context processing"
    )


class SystemInstruction(BaseModel):
    """System-level instruction for AI behavior with enhanced metadata."""
    id: Optional[str] = Field(
        None, description="Unique identifier for the instruction")
    type: Literal["behavior", "style", "constraint", "preference", "rule"] = Field(
        description="Type of system instruction"
    )
    content: str = Field(description="The actual instruction content")
    scope: Literal["global", "character", "scene", "chapter", "story"] = Field(
        default="global",
        description="Scope of application for the instruction"
    )
    priority: Literal["high", "medium", "low"] = Field(
        default="medium",
        description="Priority level for instruction enforcement"
    )
    conditions: Optional[Dict[str, Any]] = Field(
        None,
        description="Conditions under which this instruction applies"
    )
    metadata: Optional[EnhancedContextMetadata] = Field(
        default=None,
        description="Enhanced metadata for context processing"
    )
    
    # Legacy metadata field for backward compatibility
    legacy_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional legacy metadata for the instruction"
    )


class ContextMetadata(BaseModel):
    """Metadata about context processing and optimization."""
    total_elements: int = Field(description="Total number of context elements")
    processing_applied: bool = Field(
        description="Whether context processing was applied")
    processing_mode: Literal["structured"] = Field(
        default="structured",
        description="Which context processing mode was used"
    )
    optimization_level: Literal["none", "light", "moderate", "aggressive"] = Field(
        default="none",
        description="Level of context optimization applied"
    )
    compression_ratio: Optional[float] = Field(
        None,
        description="Compression ratio if optimization was applied"
    )
    filtered_elements: Optional[Dict[str, int]] = Field(
        None,
        description="Count of elements filtered by type"
    )
    processing_time_ms: Optional[float] = Field(
        None,
        description="Time taken for context processing in milliseconds"
    )
    created_at: Optional[str] = Field(
        None,
        description="Timestamp when context processing was performed"
    )
    version: str = Field(
        default="1.0",
        description="Context processing version"
    )


class StructuredContextContainer(BaseModel):
    """Container for all structured context elements."""
    plot_elements: List[PlotElement] = Field(
        default_factory=list,
        description="Plot-related context elements"
    )
    character_contexts: List[CharacterContext] = Field(
        default_factory=list,
        description="Character-specific context information"
    )
    user_requests: List[UserRequest] = Field(
        default_factory=list,
        description="User-provided requests and instructions"
    )
    system_instructions: List[SystemInstruction] = Field(
        default_factory=list,
        description="System-level instructions for AI behavior"
    )
    metadata: Optional[ContextMetadata] = Field(
        None,
        description="Metadata about the context container"
    )
    
    def get_elements_for_agent(self, agent_type: AgentType) -> List[Union[PlotElement, CharacterContext, UserRequest, SystemInstruction]]:
        """Get all context elements relevant for a specific agent type."""
        relevant_elements = []
        
        # Check plot elements
        for element in self.plot_elements:
            if element.metadata and agent_type in element.metadata.target_agents:
                relevant_elements.append(element)
            elif not element.metadata:  # Default to WRITER if no metadata
                if agent_type == AgentType.WRITER:
                    relevant_elements.append(element)
        
        # Check character contexts
        for element in self.character_contexts:
            if element.metadata and agent_type in element.metadata.target_agents:
                relevant_elements.append(element)
            elif not element.metadata:  # Default to CHARACTER and WRITER
                if agent_type in [AgentType.CHARACTER, AgentType.WRITER]:
                    relevant_elements.append(element)
        
        # Check user requests
        for element in self.user_requests:
            if element.metadata and agent_type in element.metadata.target_agents:
                relevant_elements.append(element)
            elif not element.metadata:  # Default to WRITER
                if agent_type == AgentType.WRITER:
                    relevant_elements.append(element)
        
        # Check system instructions
        for element in self.system_instructions:
            if element.metadata and agent_type in element.metadata.target_agents:
                relevant_elements.append(element)
            elif not element.metadata:  # Default to WRITER
                if agent_type == AgentType.WRITER:
                    relevant_elements.append(element)
        
        return relevant_elements
    
    def get_elements_for_phase(self, phase: ComposePhase) -> List[Union[PlotElement, CharacterContext, UserRequest, SystemInstruction]]:
        """Get all context elements relevant for a specific compose phase."""
        relevant_elements = []
        
        # Check plot elements
        for element in self.plot_elements:
            if element.metadata and phase in element.metadata.relevant_phases:
                relevant_elements.append(element)
            elif not element.metadata:  # Default to all phases
                relevant_elements.append(element)
        
        # Check character contexts
        for element in self.character_contexts:
            if element.metadata and phase in element.metadata.relevant_phases:
                relevant_elements.append(element)
            elif not element.metadata:  # Default to all phases
                relevant_elements.append(element)
        
        # Check user requests
        for element in self.user_requests:
            if element.metadata and phase in element.metadata.relevant_phases:
                relevant_elements.append(element)
            elif not element.metadata:  # Default to all phases
                relevant_elements.append(element)
        
        # Check system instructions
        for element in self.system_instructions:
            if element.metadata and phase in element.metadata.relevant_phases:
                relevant_elements.append(element)
            elif not element.metadata:  # Default to all phases
                relevant_elements.append(element)
        
        return relevant_elements
    
    def get_high_priority_elements(self, threshold: float = 0.7) -> List[Union[PlotElement, CharacterContext, UserRequest, SystemInstruction]]:
        """Get context elements with priority above the threshold."""
        high_priority_elements = []
        
        # Check plot elements
        for element in self.plot_elements:
            if element.metadata and element.metadata.priority >= threshold:
                high_priority_elements.append(element)
            elif not element.metadata and element.priority == "high":
                high_priority_elements.append(element)
        
        # Check character contexts
        for element in self.character_contexts:
            if element.metadata and element.metadata.priority >= threshold:
                high_priority_elements.append(element)
        
        # Check user requests
        for element in self.user_requests:
            if element.metadata and element.metadata.priority >= threshold:
                high_priority_elements.append(element)
            elif not element.metadata and element.priority == "high":
                high_priority_elements.append(element)
        
        # Check system instructions
        for element in self.system_instructions:
            if element.metadata and element.metadata.priority >= threshold:
                high_priority_elements.append(element)
            elif not element.metadata and element.priority == "high":
                high_priority_elements.append(element)
        
        return high_priority_elements
    
    def calculate_total_tokens(self) -> int:
        """Calculate total estimated tokens for all elements."""
        total = 0
        
        # Calculate tokens for plot elements
        for element in self.plot_elements:
            if element.metadata and element.metadata.estimated_tokens:
                total += element.metadata.estimated_tokens
            else:
                # Rough estimate: 4 characters per token
                total += len(element.content) // 4
        
        # Calculate tokens for character contexts
        for element in self.character_contexts:
            if element.metadata and element.metadata.estimated_tokens:
                total += element.metadata.estimated_tokens
            else:
                # Estimate based on all character context fields
                content_length = len(str(element.current_state)) + len(' '.join(element.goals)) + len(' '.join(element.memories))
                total += content_length // 4
        
        # Calculate tokens for user requests
        for element in self.user_requests:
            if element.metadata and element.metadata.estimated_tokens:
                total += element.metadata.estimated_tokens
            else:
                total += len(element.content) // 4
        
        # Calculate tokens for system instructions
        for element in self.system_instructions:
            if element.metadata and element.metadata.estimated_tokens:
                total += element.metadata.estimated_tokens
            else:
                total += len(element.content) // 4
        
        return total

    @model_validator(mode='after')
    def validate_context_consistency(self):
        """Validate consistency across context elements."""
        # Check for duplicate character contexts
        character_ids = [ctx.character_id for ctx in self.character_contexts]
        if len(character_ids) != len(set(character_ids)):
            raise ValueError("Duplicate character contexts found")

        # Validate character references in plot elements
        character_names = {ctx.character_name.lower()
                           for ctx in self.character_contexts}
        for plot_element in self.plot_elements:
            # Check if plot element mentions characters that aren't in context
            content_lower = plot_element.content.lower()
            for char_name in character_names:
                if char_name in content_lower:
                    # Character is mentioned and exists in context - good
                    break

        return self


# Character Feedback Request/Response
class CharacterFeedbackRequest(BaseModel):
    # Core request fields
    plotPoint: str = Field(
        description="The plot point or scene for character feedback")

    # Phase-specific fields
    compose_phase: Optional[ComposePhase] = None
    phase_context: Optional[PhaseContext] = None

    # Structured context fields (required)
    structured_context: StructuredContextContainer = Field(
        description="Structured context container with plot elements, character contexts, "
                    "user requests, and system instructions")
    context_processing_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration for context processing (summarization, filtering, etc.)"
    )

    @field_validator('structured_context')
    @classmethod
    def validate_structured_context(cls, v):
        """Validate that structured context is provided."""
        if v is None:
            raise ValueError("structured_context is required")
        return v


class CharacterFeedback(BaseModel):
    actions: List[str]
    dialog: List[str]
    physicalSensations: List[str]
    emotions: List[str]
    internalMonologue: List[str]


class CharacterFeedbackResponse(BaseModel):
    characterName: str
    feedback: CharacterFeedback
    context_metadata: Optional[ContextMetadata] = Field(
        None,
        description="Metadata about how context was processed for this response"
    )


# Rater Feedback Request/Response
class RaterFeedbackRequest(BaseModel):
    # Core request fields
    raterPrompt: str = Field(description="The rater's evaluation prompt")
    plotPoint: str = Field(description="The plot point or scene to evaluate")

    # Phase-specific fields
    compose_phase: Optional[ComposePhase] = None
    phase_context: Optional[PhaseContext] = None

    # Structured context fields (required)
    structured_context: StructuredContextContainer = Field(
        description="Structured context container with plot elements, character contexts, "
                    "user requests, and system instructions")
    context_processing_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration for context processing (summarization, filtering, etc.)"
    )

    @field_validator('structured_context')
    @classmethod
    def validate_structured_context(cls, v):
        """Validate that structured context is provided."""
        if v is None:
            raise ValueError("structured_context is required")
        return v


class RaterFeedback(BaseModel):
    opinion: str
    suggestions: List[str]


class RaterFeedbackResponse(BaseModel):
    raterName: str
    feedback: RaterFeedback
    context_metadata: Optional[ContextMetadata] = Field(
        None,
        description="Metadata about how context was processed for this response"
    )


# Chapter Generation Request/Response
class GenerateChapterRequest(BaseModel):
    # Core request fields
    plotPoint: str = Field(description="The plot point or scene to generate")

    # Phase-specific fields
    compose_phase: Optional[ComposePhase] = None
    phase_context: Optional[PhaseContext] = None

    # Structured context fields (required)
    structured_context: StructuredContextContainer = Field(
        description="Structured context container with plot elements, character contexts, "
                    "user requests, and system instructions")
    context_processing_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration for context processing (summarization, filtering, etc.)"
    )

    @field_validator('structured_context')
    @classmethod
    def validate_structured_context(cls, v):
        """Validate that structured context is provided."""
        if v is None:
            raise ValueError("structured_context is required")
        return v


class GenerateChapterResponse(BaseModel):
    chapterText: str
    wordCount: int
    metadata: Dict[str, Any]
    context_metadata: Optional[ContextMetadata] = Field(
        None,
        description="Metadata about how context was processed for this response"
    )


# Chapter Modification Request/Response
class ModifyChapterRequest(BaseModel):
    # Core request fields
    currentChapter: str = Field(description="The chapter text to be modified")
    userRequest: str = Field(description="User's modification request")

    # Phase-specific fields
    compose_phase: Optional[ComposePhase] = None
    phase_context: Optional[PhaseContext] = None

    # Structured context fields (required)
    structured_context: StructuredContextContainer = Field(
        description="Structured context container with plot elements, character contexts, "
                    "user requests, and system instructions")
    context_processing_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration for context processing (summarization, filtering, etc.)"
    )

    @field_validator('structured_context')
    @classmethod
    def validate_structured_context(cls, v):
        """Validate that structured context is provided."""
        if v is None:
            raise ValueError("structured_context is required")
        return v


class ModifyChapterResponse(BaseModel):
    modifiedChapter: str
    wordCount: int
    changesSummary: str
    context_metadata: Optional[ContextMetadata] = Field(
        None,
        description="Metadata about how context was processed for this response"
    )


# Editor Review Request/Response
class EditorReviewRequest(BaseModel):
    # Core request fields
    chapterToReview: str = Field(description="The chapter text to be reviewed")

    # Phase-specific fields
    compose_phase: Optional[ComposePhase] = None
    phase_context: Optional[PhaseContext] = None

    # Structured context fields (required)
    structured_context: StructuredContextContainer = Field(
        description="Structured context container with plot elements, character contexts, "
                    "user requests, and system instructions")
    context_processing_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration for context processing (summarization, filtering, etc.)"
    )

    @field_validator('structured_context')
    @classmethod
    def validate_structured_context(cls, v):
        """Validate that structured context is provided."""
        if v is None:
            raise ValueError("structured_context is required")
        return v


class EditorSuggestion(BaseModel):
    issue: str
    suggestion: str
    priority: str  # "high", "medium", "low"


class EditorReviewResponse(BaseModel):
    suggestions: List[EditorSuggestion]
    context_metadata: Optional[ContextMetadata] = Field(
        None,
        description="Metadata about how context was processed for this response"
    )


# Flesh Out Request/Response (for plot points or worldbuilding)
class FleshOutRequest(BaseModel):
    # Core request fields
    textToFleshOut: str = Field(
        description="Text content to be expanded or fleshed out")
    context: Optional[str] = Field(
        default="", description="Additional context for the flesh out operation")

    # Phase-specific fields
    compose_phase: Optional[ComposePhase] = None
    phase_context: Optional[PhaseContext] = None

    # Structured context fields (required)
    structured_context: StructuredContextContainer = Field(
        description="Structured context container with plot elements, character contexts, "
                    "user requests, and system instructions")
    context_processing_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration for context processing (summarization, filtering, etc.)"
    )

    @field_validator('structured_context')
    @classmethod
    def validate_structured_context(cls, v):
        """Validate that structured context is provided."""
        if v is None:
            raise ValueError("structured_context is required")
        return v


class FleshOutResponse(BaseModel):
    fleshedOutText: str
    originalText: str
    metadata: Dict[str, Any]
    context_metadata: Optional[ContextMetadata] = Field(
        None,
        description="Metadata about how context was processed for this response"
    )


# Generate Character Details Request/Response
class GenerateCharacterDetailsRequest(BaseModel):
    # Core request fields
    basicBio: str = Field(
        description="Basic biography or description of the character to generate details for")
    existingCharacters: List[Dict[str, str]] = Field(
        default_factory=list,
        description="List of existing characters with name, basicBio, and relationships"
    )

    # Phase-specific fields
    compose_phase: Optional[ComposePhase] = None
    phase_context: Optional[PhaseContext] = None

    # Structured context fields (required)
    structured_context: StructuredContextContainer = Field(
        description="Structured context container with plot elements, character contexts, "
                    "user requests, and system instructions")
    context_processing_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration for context processing (summarization, filtering, etc.)"
    )

    @field_validator('structured_context')
    @classmethod
    def validate_structured_context(cls, v):
        """Validate that structured context is provided."""
        if v is None:
            raise ValueError("structured_context is required")
        return v


class GenerateCharacterDetailsResponse(BaseModel):
    name: str
    sex: str
    gender: str
    sexualPreference: str
    age: int
    physicalAppearance: str
    usualClothing: str
    personality: str
    motivations: str
    fears: str
    relationships: str
    context_metadata: Optional[ContextMetadata] = Field(
        None,
        description="Metadata about how context was processed for this response"
    )


# Regenerate Bio Request/Response
class RegenerateBioRequest(BaseModel):
    # Character details to summarize into bio
    name: str = Field(description="Character name")
    sex: str = Field(default="", description="Character sex")
    gender: str = Field(default="", description="Character gender identity")
    sexualPreference: str = Field(default="",
                                  description="Character sexual preference")
    age: int = Field(default=0, description="Character age")
    physicalAppearance: str = Field(
        default="", description="Character physical appearance")
    usualClothing: str = Field(default="",
                               description="Character usual clothing")
    personality: str = Field(default="",
                             description="Character personality traits")
    motivations: str = Field(default="", description="Character motivations")
    fears: str = Field(default="", description="Character fears")
    relationships: str = Field(default="",
                               description="Character relationships")

    # Context fields (optional for bio regeneration)
    compose_phase: Optional[ComposePhase] = None
    phase_context: Optional[PhaseContext] = None
    structured_context: Optional[StructuredContextContainer] = Field(
        default=None,
        description="Optional structured context container"
    )
    context_processing_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration for context processing"
    )


class RegenerateBioResponse(BaseModel):
    basicBio: str = Field(
        description="Generated bio summary from character details")
    context_metadata: Optional[ContextMetadata] = Field(
        None,
        description="Metadata about how context was processed for this response"
    )


# Legacy Context Element Classes for backward compatibility
class BaseContextElement(BaseModel):
    """Base class for all context elements."""

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


class SystemContextElement(BaseContextElement):
    """Context elements for system-level prompts and instructions."""

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
    """Context elements for story-level information."""

    type: Literal[
        ContextType.WORLD_BUILDING,
        ContextType.STORY_THEME,
        ContextType.NARRATIVE_STATE,
        ContextType.STORY_SUMMARY,
        ContextType.PLOT_OUTLINE
    ]

    story_id: Optional[str] = Field(
        default=None,
        description="ID of the story this context belongs to"
    )

    chapter_id: Optional[str] = Field(
        default=None,
        description="ID of the chapter this context belongs to"
    )


class CharacterContextElement(BaseContextElement):
    """Context elements for character-specific information."""

    type: Literal[
        ContextType.CHARACTER_PROFILE,
        ContextType.CHARACTER_RELATIONSHIP,
        ContextType.CHARACTER_MEMORY,
        ContextType.CHARACTER_STATE
    ]

    character_id: Optional[str] = Field(
        default=None,
        description="ID of the character this context belongs to"
    )

    character_name: Optional[str] = Field(
        default=None,
        description="Name of the character for easy reference"
    )

    relationship_target: Optional[str] = Field(
        default=None,
        description="Target character for relationship contexts"
    )


class UserContextElement(BaseContextElement):
    """Context elements for user-provided information."""

    type: Literal[
        ContextType.USER_PREFERENCE,
        ContextType.USER_FEEDBACK,
        ContextType.USER_REQUEST,
        ContextType.USER_INSTRUCTION
    ]

    user_id: Optional[str] = Field(
        default=None,
        description="ID of the user who provided this context"
    )

    request_type: Optional[str] = Field(
        default=None,
        description="Type of user request (generation, revision, feedback, etc.)"
    )


class PhaseContextElement(BaseContextElement):
    """Context elements for phase-specific information."""

    type: Literal[
        ContextType.PHASE_INSTRUCTION,
        ContextType.PHASE_OUTPUT,
        ContextType.PHASE_GUIDANCE
    ]

    target_phase: ComposePhase = Field(
        description="Which composition phase this context applies to"
    )

    phase_priority: float = Field(
        default=1.0,
        description="Priority within the target phase"
    )


class ConversationContextElement(BaseContextElement):
    """Context elements for conversation history."""

    type: Literal[ContextType.CONVERSATION_HISTORY]

    conversation_id: Optional[str] = Field(
        default=None,
        description="ID of the conversation this context belongs to"
    )

    turn_number: Optional[int] = Field(
        default=None,
        description="Turn number in the conversation"
    )

    speaker: Optional[str] = Field(
        default=None,
        description="Who spoke in this turn (user, assistant, character, etc.)"
    )


# Context Relationships
class ContextRelationship(BaseModel):
    """Defines relationships between context elements."""

    source_id: str = Field(description="ID of the source context element")
    target_id: str = Field(description="ID of the target context element")
    relationship_type: str = Field(description="Type of relationship (depends_on, conflicts_with, enhances, etc.)")
    strength: float = Field(default=1.0, ge=0.0, le=1.0, description="Strength of the relationship")
    description: Optional[str] = Field(default=None, description="Description of the relationship")
