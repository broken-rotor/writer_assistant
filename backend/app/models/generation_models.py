"""
Pydantic models for generation API requests and responses.

All API endpoints now accept only request_context data.
"""
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum
from app.models.request_context import RequestContext


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


# Character Feedback Request/Response
class CharacterFeedbackRequest(BaseModel):
    character_name: str = Field(description="Character name to get feedback from")

    plotPoint: str = Field(
        description="The plot point or scene for character feedback")

    request_context: RequestContext = Field(
        description="Complete request context with story configuration, worldbuilding, "
                    "characters, outline, and chapters")

class CharacterFeedback(BaseModel):
    actions: List[str] = Field(
        default_factory=list,
        description="Things the character does, actions taken"
    )
    dialog: List[str] = Field(
        default_factory=list,
        description="Things the character says"
    )
    physicalSensations: List[str] = Field(
        default_factory=list,
        description="Things the character physically experiences and reacts"
    )
    emotions: List[str] = Field(
        default_factory=list,
        description="Emotions experienced by the character, how he feels about the situation"
    )
    internalMonologue: List[str] = Field(
        default_factory=list,
        description="Internal monologue by the character, what he thinks and reflects about the situation"
    )
    goals: List[str] = Field(
        default_factory=list,
        description="Character's current goals and objectives"
    )
    memories: List[str] = Field(
        default_factory=list,
        description="Important memories affecting current behavior"
    )
    subtext: List[str] = Field(
        default_factory=list,
        description="What the character is communicating nonverbally or hiding beneath their words"
    )


class CharacterFeedbackResponse(BaseModel):
    characterName: str
    feedback: CharacterFeedback


# Rater Feedback Request/Response
class RaterFeedbackRequest(BaseModel):
    # Core request fields
    raterName: str = Field(description="The rater's name")
    plotPoint: str = Field(description="The plot point or scene to evaluate")

    request_context: RequestContext = Field(
        description="Complete request context with story configuration, worldbuilding, "
                    "characters, outline, and chapters")


class RaterSuggestion(BaseModel):
    issue: str
    suggestion: str
    priority: str  # "high", "medium", "low"


class RaterFeedback(BaseModel):
    opinion: str
    suggestions: List[RaterSuggestion]


class RaterFeedbackResponse(BaseModel):
    raterName: str
    feedback: RaterFeedback


# Chapter Generation Request/Response
class GenerateChapterRequest(BaseModel):
    chapter_number: int = Field(description="Chapter number to generate")

    request_context: RequestContext = Field(
        description="Complete request context with story configuration, worldbuilding, "
                    "characters, outline, and chapters")


class GenerateChapterResponse(BaseModel):
    chapterText: str
    wordCount: int
    metadata: Dict[str, Any]


# Chapter Modification Request/Response
class ModifyChapterRequest(BaseModel):
    chapter_number: int = Field(description="Chapter number to modify")

    userRequest: str = Field(description="User's modification request")

    request_context: RequestContext = Field(
        description="Complete request context with story configuration, worldbuilding, "
                    "characters, outline, and chapters")


class ModifyChapterResponse(BaseModel):
    modifiedChapter: str


# Editor Review Request/Response
class EditorReviewRequest(BaseModel):
    chapter_number: int = Field(description="The chapter number to be reviewed")

    request_context: RequestContext = Field(
        description="Complete request context with story configuration, worldbuilding, "
                    "characters, outline, and chapters")


class EditorSuggestion(BaseModel):
    issue: str
    suggestion: str
    priority: str  # "high", "medium", "low"


class EditorReviewResponse(BaseModel):
    suggestions: List[EditorSuggestion]


class FleshOutType(str, Enum):
    WORLDBUILDING = 'worldbuilding'
    CHAPTER = 'chapter'
    PLOT_OUTLINE = 'plot_outline'


# Flesh Out Request/Response (for plot points or worldbuilding)
class FleshOutRequest(BaseModel):
    request_type: FleshOutType = Field(description="Type of freshout request.")

    # Core request fields
    text_to_flesh_out: str = Field(
        description="Text content to be expanded or fleshed out")

    # Request context fields (required)
    request_context: RequestContext = Field(
        default=None,
        description="Complete request context with story configuration, worldbuilding, "
                    "characters, outline, and chapters")


class FleshOutResponse(BaseModel):
    fleshedOutText: str
    originalText: str
    metadata: Dict[str, Any]


# Generate Character Details Request/Response
class GenerateCharacterDetailsRequest(BaseModel):
    character_name: str = Field(description="Name of the character")

    request_context: RequestContext = Field(
        description="Complete request context with story configuration, worldbuilding, "
                    "characters, outline, and chapters")


class GenerateCharacterDetailsResponse(BaseModel):
    character_info: CharacterInfo


# Regenerate Bio Request/Response
class RegenerateBioRequest(BaseModel):
    character_name: str = Field(description="Name of the character to regenerate the basic bio")

    request_context: RequestContext = Field(
        description="Optional complete request context"
    )


class RegenerateBioResponse(BaseModel):
    basicBio: str = Field(
        description="Generated bio summary from character details")
