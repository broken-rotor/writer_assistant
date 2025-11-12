"""
Chapter Outline Models for Writer Assistant API.

This module defines the data models used for chapter outline generation.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
# Legacy import removed in B4 - CharacterContext class removed
from app.models.generation_models import SystemPrompts


class ChapterOutlineRequest(BaseModel):
    """Request model for chapter outline generation"""
    story_outline: str = Field(..., description="The story outline content")
    story_context: Dict[str, Any] = Field(default_factory=dict, description="Additional story context")
    # TODO: Remove or replace with new character model - CharacterContext removed in B4
    # character_contexts: List[CharacterContext] = Field(default_factory=list, description="Character context information (preferred)")
    character_contexts: List[Dict[str, Any]] = Field(default_factory=list, description="Character context information (legacy field - use Dict format)")
    generation_preferences: Dict[str, Any] = Field(default_factory=dict, description="Generation preferences")
    system_prompts: Optional[SystemPrompts] = Field(None, description="Custom system prompt prefix and suffix")


class OutlineItem(BaseModel):
    """Generated outline item"""
    id: str
    type: str = "chapter"
    title: str
    description: str
    key_plot_items: List[str] = Field(default_factory=list, description="Key plot items that occur in this chapter")
    order: int
    status: str = "draft"
    involved_characters: List[str] = Field(default_factory=list, description="List of character names involved in this chapter")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChapterOutlineResponse(BaseModel):
    """Response model for chapter outline generation"""
    outline_items: List[OutlineItem]
    summary: str
    context_metadata: Dict[str, Any] = Field(default_factory=dict)
