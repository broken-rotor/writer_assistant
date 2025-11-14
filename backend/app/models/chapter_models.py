"""
Chapter Outline Models for Writer Assistant API.

This module defines the data models used for chapter outline generation.
"""

from pydantic import BaseModel, Field, model_validator
from typing import List, Dict, Any, Optional
# Legacy import removed in B4 - CharacterContext class removed
from app.models.generation_models import SystemPrompts
from app.models.request_context import RequestContext
from app.models.context_models import ContextProcessingConfig


class ChapterOutlineRequest(BaseModel):
    """Request model for chapter outline generation"""
    
    # Unified context field (replaces individual context fields)
    request_context: RequestContext = Field(
        description="Complete request context with story configuration, worldbuilding, "
                    "characters, outline, and chapters"
    )
    
    # Optional processing configuration
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
    context_metadata: Dict[str, Any] = Field(default_factory=dict)
