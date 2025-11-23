"""
Models for agentic text generation system.

This module defines configuration and event models for the agentic text generator,
which performs iterative generate-evaluate-refine cycles.
"""

from typing import Optional
from pydantic import BaseModel, Field
from app.models.streaming_models import StreamingEventType


class AgenticConfig(BaseModel):
    """Configuration for agentic text generation."""
    max_iterations: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum number of generate-evaluate cycles"
    )
    generation_temperature: float = Field(
        default=0.8,
        ge=0.0,
        le=2.0,
        description="Temperature for content generation"
    )
    generation_max_tokens: int = Field(
        default=2000,
        ge=100,
        le=10000,
        description="Max tokens for generation"
    )
    evaluation_temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="Temperature for evaluation (lower = more strict)"
    )
    evaluation_max_tokens: int = Field(
        default=500,
        ge=100,
        le=2000,
        description="Max tokens for evaluation feedback"
    )
    stream_partial_content: bool = Field(
        default=False,
        description="Stream tokens during generation (vs. batch)"
    )
