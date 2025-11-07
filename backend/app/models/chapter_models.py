"""
Chapter Outline Models for Writer Assistant API.

This module defines the data models used for chapter outline generation.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.models.generation_models import CharacterContext, SystemPrompts


class ChapterOutlineRequest(BaseModel):
    """Request model for chapter outline generation"""
    story_outline: str = Field(..., description="The story outline content")
    story_context: Dict[str, Any] = Field(default_factory=dict, description="Additional story context")
    character_contexts: List[CharacterContext] = Field(default_factory=list, description="Character context information (preferred)")
    generation_preferences: Dict[str, Any] = Field(default_factory=dict, description="Generation preferences")
    system_prompts: Optional[SystemPrompts] = Field(None, description="Custom system prompt prefix and suffix")


class OutlineItem(BaseModel):
    """Generated outline item"""
    id: str
    type: str = "chapter"
    title: str
    description: str
    order: int
    status: str = "draft"
    involved_characters: List[str] = Field(default_factory=list, description="List of character names involved in this chapter")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChapterOutlineResponse(BaseModel):
    """Response model for chapter outline generation"""
    outline_items: List[OutlineItem]
    summary: str
    context_metadata: Dict[str, Any] = Field(default_factory=dict)
