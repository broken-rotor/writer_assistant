"""
Pydantic models for generation API requests and responses.
Based on the requirements in api_requirements.md and ui_requirements.md.
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
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


# Character Feedback Request/Response
class CharacterFeedbackRequest(BaseModel):
    systemPrompts: SystemPrompts
    worldbuilding: str
    storySummary: str
    previousChapters: List[ChapterInfo]
    character: CharacterInfo
    plotPoint: str
    incorporatedFeedback: Optional[List[FeedbackItem]] = []


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
    systemPrompts: SystemPrompts
    raterPrompt: str
    worldbuilding: str
    storySummary: str
    previousChapters: List[ChapterInfo]
    plotPoint: str
    incorporatedFeedback: Optional[List[FeedbackItem]] = []


class RaterFeedback(BaseModel):
    opinion: str
    suggestions: List[str]


class RaterFeedbackResponse(BaseModel):
    raterName: str
    feedback: RaterFeedback


# Chapter Generation Request/Response
class GenerateChapterRequest(BaseModel):
    systemPrompts: SystemPrompts
    worldbuilding: str
    storySummary: str
    previousChapters: List[ChapterInfo]
    characters: List[CharacterInfo]
    plotPoint: str
    incorporatedFeedback: List[FeedbackItem]


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
    systemPrompts: SystemPrompts
    worldbuilding: str
    storySummary: str
    previousChapters: List[ChapterInfo]
    characters: List[CharacterInfo]
    chapterToReview: str


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
