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
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime


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
ComposePhase = Literal['plot_outline', 'chapter_detail', 'final_edit']


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
    """Individual plot element with metadata."""
    id: Optional[str] = Field(None, description="Unique identifier for the plot element")
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
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the plot element"
    )


class CharacterContext(BaseModel):
    """Character-specific context information."""
    character_id: str = Field(description="Unique identifier for the character")
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


class UserRequest(BaseModel):
    """User-provided request or instruction."""
    id: Optional[str] = Field(None, description="Unique identifier for the request")
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


class SystemInstruction(BaseModel):
    """System-level instruction for AI behavior."""
    id: Optional[str] = Field(None, description="Unique identifier for the instruction")
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
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata for the instruction"
    )


class ContextMetadata(BaseModel):
    """Metadata about context processing and optimization."""
    total_elements: int = Field(description="Total number of context elements")
    processing_applied: bool = Field(description="Whether context processing was applied")
    processing_mode: Literal["legacy", "structured", "hybrid"] = Field(
        default="legacy",
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

    @model_validator(mode='after')
    def validate_context_consistency(self):
        """Validate consistency across context elements."""
        # Check for duplicate character contexts
        character_ids = [ctx.character_id for ctx in self.character_contexts]
        if len(character_ids) != len(set(character_ids)):
            raise ValueError("Duplicate character contexts found")

        # Validate character references in plot elements
        character_names = {ctx.character_name.lower() for ctx in self.character_contexts}
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
    plotPoint: str = Field(description="The plot point or scene for character feedback")

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
    textToFleshOut: str = Field(description="Text content to be expanded or fleshed out")
    context: Optional[str] = Field(default="", description="Additional context for the flesh out operation")

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
    context_metadata: Optional[ContextMetadata] = Field(
        None,
        description="Metadata about how context was processed for this response"
    )


# Generate Character Details Request/Response
class GenerateCharacterDetailsRequest(BaseModel):
    # Core request fields
    basicBio: str = Field(description="Basic biography or description of the character to generate details for")
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
