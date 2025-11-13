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
from app.models.request_context import RequestContext
from app.models.context_models import ContextProcessingConfig


# System Prompts Configuration
class SystemPrompts(BaseModel):
    mainPrefix: str = ""
    mainSuffix: str = ""
    assistantPrompt: Optional[str] = None
    editorPrompt: Optional[str] = None


# Character Models
class CharacterInfo(BaseModel):
    name: str = Field(description="Character name")
    basicBio: str = Field(description="Character basic biography")
    sex: str = Field(default="", description="Character sex")
    gender: str = Field(default="", description="Character gender identity")
    sexualPreference: str = Field(default="", description="Character sexual preference")
    age: int = Field(default=0, description="Character age")
    physicalAppearance: str = Field(default="", description="Character physical appearance")
    usualClothing: str = Field(default="", description="Character usual clothing")
    personality: str = Field(default="", description="Character personality traits")
    motivations: str = Field(default="", description="Character motivations")
    fears: str = Field(default="", description="Character fears")
    relationships: str = Field(default="", description="Character relationships")


class ChapterInfo(BaseModel):
    number: int
    title: str
    content: str


class FeedbackItem(BaseModel):
    source: str
    type: str
    content: str
    incorporated: bool = True


class ConversationMessage(BaseModel):
    role: Literal['user', 'assistant']
    content: str
    timestamp: Optional[str] = None


# Legacy Structured Context Models have been removed in B4
# Use RequestContext from app.models.request_context instead


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


# StructuredContextContainer has been removed in B4
# Use RequestContext from app.models.request_context instead


# Character Feedback Request/Response
class CharacterFeedbackRequest(BaseModel):
    # Core request fields
    plotPoint: str = Field(
        description="The plot point or scene for character feedback")

    # Phase-specific fields

    # Request context fields (required)
    request_context: Optional[RequestContext] = Field(
        default=None,
        description="Complete request context with story configuration, worldbuilding, "
                    "characters, outline, and chapters")
    context_processing_config: Optional[ContextProcessingConfig] = Field(
        default=None,
        description="Configuration for context processing (summarization, filtering, etc.)"
    )

    @model_validator(mode='before')
    @classmethod
    def validate_context_fields(cls, values):
        """Ensure request_context is provided."""
        if isinstance(values, dict):
            # Ensure request_context is provided
            if not values.get('request_context'):
                raise ValueError("request_context is required")
        return values


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

    # Request context fields (required)
    request_context: Optional[RequestContext] = Field(
        default=None,
        description="Complete request context with story configuration, worldbuilding, "
                    "characters, outline, and chapters")
    context_processing_config: Optional[ContextProcessingConfig] = Field(
        default=None,
        description="Configuration for context processing (summarization, filtering, etc.)"
    )

    @model_validator(mode='before')
    @classmethod
    def validate_context_fields(cls, values):
        """Ensure request_context is provided."""
        if isinstance(values, dict):
            # Ensure request_context is provided
            if not values.get('request_context'):
                raise ValueError("request_context is required")
        return values


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

    # Request context fields (required)
    request_context: Optional[RequestContext] = Field(
        default=None,
        description="Complete request context with story configuration, worldbuilding, "
                    "characters, outline, and chapters")
    context_processing_config: Optional[ContextProcessingConfig] = Field(
        default=None,
        description="Configuration for context processing (summarization, filtering, etc.)"
    )

    @model_validator(mode='before')
    @classmethod
    def validate_context_fields(cls, values):
        """Ensure request_context is provided."""
        if isinstance(values, dict):
            # Ensure request_context is provided
            if not values.get('request_context'):
                raise ValueError("request_context is required")
        return values


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

    # Request context fields (required)
    request_context: Optional[RequestContext] = Field(
        default=None,
        description="Complete request context with story configuration, worldbuilding, "
                    "characters, outline, and chapters")
    context_processing_config: Optional[ContextProcessingConfig] = Field(
        default=None,
        description="Configuration for context processing (summarization, filtering, etc.)"
    )

    @model_validator(mode='before')
    @classmethod
    def validate_context_fields(cls, values):
        """Ensure request_context is provided."""
        if isinstance(values, dict):
            # Ensure request_context is provided
            if not values.get('request_context'):
                raise ValueError("request_context is required")
        return values


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

    # Request context fields (required)
    request_context: Optional[RequestContext] = Field(
        default=None,
        description="Complete request context with story configuration, worldbuilding, "
                    "characters, outline, and chapters")
    context_processing_config: Optional[ContextProcessingConfig] = Field(
        default=None,
        description="Configuration for context processing (summarization, filtering, etc.)"
    )

    @model_validator(mode='before')
    @classmethod
    def validate_context_fields(cls, values):
        """Ensure request_context is provided."""
        if isinstance(values, dict):
            # Ensure request_context is provided
            if not values.get('request_context'):
                raise ValueError("request_context is required")
        return values


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

    # Request context fields (required)
    request_context: Optional[RequestContext] = Field(
        default=None,
        description="Complete request context with story configuration, worldbuilding, "
                    "characters, outline, and chapters")
    context_processing_config: Optional[ContextProcessingConfig] = Field(
        default=None,
        description="Configuration for context processing (summarization, filtering, etc.)"
    )

    @model_validator(mode='before')
    @classmethod
    def validate_context_fields(cls, values):
        """Ensure request_context is provided."""
        if isinstance(values, dict):
            # Ensure request_context is provided
            if not values.get('request_context'):
                raise ValueError("request_context is required")
        return values


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

    # Request context fields (required)
    request_context: Optional[RequestContext] = Field(
        default=None,
        description="Complete request context with story configuration, worldbuilding, "
                    "characters, outline, and chapters")
    context_processing_config: Optional[ContextProcessingConfig] = Field(
        default=None,
        description="Configuration for context processing (summarization, filtering, etc.)"
    )

    @model_validator(mode='before')
    @classmethod
    def validate_context_fields(cls, values):
        """Ensure request_context is provided."""
        if isinstance(values, dict):
            # Ensure request_context is provided
            if not values.get('request_context'):
                raise ValueError("request_context is required")
        return values


class GenerateCharacterDetailsResponse(BaseModel):
    character_info: CharacterInfo
    context_metadata: Optional[ContextMetadata] = Field(
        None,
        description="Metadata about how context was processed for this response"
    )


# Regenerate Bio Request/Response
class RegenerateBioRequest(BaseModel):
    # Character information to summarize into bio
    character_info: CharacterInfo = Field(description="Character information to generate bio from")

    # Context fields (optional for bio regeneration)
    request_context: Optional[RequestContext] = Field(
        default=None,
        description="Optional complete request context"
    )
    context_processing_config: Optional[ContextProcessingConfig] = Field(
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
