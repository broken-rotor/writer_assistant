from typing import List, Dict, Any
from pydantic import BaseModel
from enum import Enum

class StoryPhase(str, Enum):
    OUTLINE_DEVELOPMENT = "outline_development"
    CHAPTER_DEVELOPMENT = "chapter_development"
    COMPLETED = "completed"

class StoryStatus(str, Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    APPROVED = "approved"

# Simplified models for generation requests/responses only
class CharacterConfig(BaseModel):
    name: str
    role: str
    personality_traits: List[str] = []
    background: Dict[str, Any] = {}

class GenerationConfig(BaseModel):
    style_profile: str = "standard"
    character_templates: List[str] = []
    rater_preferences: List[str] = []
    target_length: str = "novel"
    complexity_level: str = "moderate"

class OutlineStructure(BaseModel):
    acts: List[Dict[str, Any]] = []
    chapters: List[Dict[str, Any]] = []
    characters: List[CharacterConfig] = []
    themes: List[str] = []

class ChapterContent(BaseModel):
    text: str
    word_count: int
    character_perspectives: Dict[str, Any] = {}

class AgentFeedback(BaseModel):
    score: float
    feedback: str
    suggestions: List[str] = []
    priority: str = "medium"