"""
Pydantic models for generation API requests and responses.
Based on the requirements in api_requirements.md and ui_requirements.md.

Updated to support structured context data schema alongside legacy fields
for backward compatibility during the transition period.
"""
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field, validator
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


# Character Feedback Request/Response
class CharacterFeedbackRequest(BaseModel):
    # Legacy fields (maintained for backward compatibility)
    systemPrompts: Optional[SystemPrompts] = None
    worldbuilding: Optional[str] = ""
    storySummary: Optional[str] = ""
    
    # Core request fields
    previousChapters: List[ChapterInfo]
    character: CharacterInfo
    plotPoint: str
    incorporatedFeedback: Optional[List[FeedbackItem]] = []
    
    # Phase-specific fields (optional for backward compatibility)
    compose_phase: Optional[ComposePhase] = None
    phase_context: Optional[PhaseContext] = None
    
    # New structured context fields
    structured_context: Optional[Any] = Field(
        default=None,
        description="Structured context container (StructuredContextContainer)"
    )
    context_mode: Literal["legacy", "structured", "hybrid"] = Field(
        default="legacy",
        description="Which context format to use"
    )
    context_processing_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration for context processing (summarization, filtering, etc.)"
    )
    
    @validator('systemPrompts', 'worldbuilding', 'storySummary', 'structured_context')
    def validate_context_provided(cls, v, values, field):
        """Ensure either legacy or structured context is provided."""
        context_mode = values.get('context_mode', 'legacy')
        
        if context_mode == 'structured':
            if field.name == 'structured_context' and v is None:
                raise ValueError("structured_context is required when context_mode is 'structured'")
        elif context_mode == 'legacy':
            if field.name in ['systemPrompts', 'worldbuilding', 'storySummary']:
                # At least one legacy field should be provided
                legacy_fields = [
                    values.get('systemPrompts'),
                    values.get('worldbuilding'),
                    values.get('storySummary')
                ]
                if all(f is None or f == "" for f in legacy_fields):
                    raise ValueError("At least one legacy context field must be provided when context_mode is 'legacy'")
        
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


# Rater Feedback Request/Response
class RaterFeedbackRequest(BaseModel):
    # Legacy fields (maintained for backward compatibility)
    systemPrompts: Optional[SystemPrompts] = None
    raterPrompt: str
    worldbuilding: Optional[str] = ""
    storySummary: Optional[str] = ""
    
    # Core request fields
    previousChapters: List[ChapterInfo]
    plotPoint: str
    incorporatedFeedback: Optional[List[FeedbackItem]] = []
    
    # Phase-specific fields (optional for backward compatibility)
    compose_phase: Optional[ComposePhase] = None
    phase_context: Optional[PhaseContext] = None
    
    # New structured context fields
    structured_context: Optional[Any] = Field(
        default=None,
        description="Structured context container (StructuredContextContainer)"
    )
    context_mode: Literal["legacy", "structured", "hybrid"] = Field(
        default="legacy",
        description="Which context format to use"
    )
    context_processing_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration for context processing (summarization, filtering, etc.)"
    )


class RaterFeedback(BaseModel):
    opinion: str
    suggestions: List[str]


class RaterFeedbackResponse(BaseModel):
    raterName: str
    feedback: RaterFeedback


# Chapter Generation Request/Response
class GenerateChapterRequest(BaseModel):
    # Legacy fields (maintained for backward compatibility)
    systemPrompts: Optional[SystemPrompts] = None
    worldbuilding: Optional[str] = ""
    storySummary: Optional[str] = ""
    
    # Core request fields
    previousChapters: List[ChapterInfo]
    characters: List[CharacterInfo]
    plotPoint: str
    incorporatedFeedback: List[FeedbackItem]
    
    # Phase-specific fields (optional for backward compatibility)
    compose_phase: Optional[ComposePhase] = None
    phase_context: Optional[PhaseContext] = None
    
    # New structured context fields
    structured_context: Optional[Any] = Field(
        default=None,
        description="Structured context container (StructuredContextContainer)"
    )
    context_mode: Literal["legacy", "structured", "hybrid"] = Field(
        default="legacy",
        description="Which context format to use"
    )
    context_processing_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration for context processing (summarization, filtering, etc.)"
    )


class GenerateChapterResponse(BaseModel):
    chapterText: str
    wordCount: int
    metadata: Dict[str, Any]


# Chapter Modification Request/Response
class ModifyChapterRequest(BaseModel):
    systemPrompts: SystemPrompts
    worldbuilding: str
    storySummary: str
    previousChapters: List[ChapterInfo]
    currentChapter: str
    userRequest: str


class ModifyChapterResponse(BaseModel):
    modifiedChapter: str
    wordCount: int
    changesSummary: str


# Editor Review Request/Response
class EditorReviewRequest(BaseModel):
    # Legacy fields (maintained for backward compatibility)
    systemPrompts: Optional[SystemPrompts] = None
    worldbuilding: Optional[str] = ""
    storySummary: Optional[str] = ""
    
    # Core request fields
    previousChapters: List[ChapterInfo]
    characters: List[CharacterInfo]
    chapterToReview: str
    
    # Phase-specific fields (optional for backward compatibility)
    compose_phase: Optional[ComposePhase] = None
    phase_context: Optional[PhaseContext] = None
    
    # New structured context fields
    structured_context: Optional[Any] = Field(
        default=None,
        description="Structured context container (StructuredContextContainer)"
    )
    context_mode: Literal["legacy", "structured", "hybrid"] = Field(
        default="legacy",
        description="Which context format to use"
    )
    context_processing_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration for context processing (summarization, filtering, etc.)"
    )


class EditorSuggestion(BaseModel):
    issue: str
    suggestion: str
    priority: str  # "high", "medium", "low"


class EditorReviewResponse(BaseModel):
    suggestions: List[EditorSuggestion]


# Flesh Out Request/Response (for plot points or worldbuilding)
class FleshOutRequest(BaseModel):
    systemPrompts: SystemPrompts
    worldbuilding: str
    storySummary: str
    textToFleshOut: str
    context: str


class FleshOutResponse(BaseModel):
    fleshedOutText: str
    originalText: str


# Generate Character Details Request/Response
class GenerateCharacterDetailsRequest(BaseModel):
    systemPrompts: SystemPrompts
    worldbuilding: str
    storySummary: str
    basicBio: str
    existingCharacters: List[Dict[str, str]]  # List of {name, basicBio, relationships}


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
