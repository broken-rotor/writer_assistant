"""
Pydantic models for token counting API endpoints.

This module defines the request and response models for the token counting API,
supporting batch processing, content type detection, and comprehensive metadata.
"""

from typing import List
from pydantic import BaseModel, Field, field_validator


class TokenCountRequestItem(BaseModel):
    """Individual text item for token counting."""

    text: str = Field(
        ...,
        description="Text content to count tokens for"
    )

    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        if len(v) > 100000:  # 100KB limit
            raise ValueError("Text content too large (max 100KB)")
        return v


class TokenCountRequest(BaseModel):
    """Request model for batch token counting."""

    texts: List[TokenCountRequestItem] = Field(
        ...,
        description="List of text items to count tokens for",
        min_length=1,
        max_length=50  # Reasonable batch limit
    )


class TokenCountResultItem(BaseModel):
    """Individual token count result."""

    text: str = Field(..., description="Original text content")
    token_count: int = Field(..., description="Number of tokens in the text")


class TokenCountResponse(BaseModel):
    """Response model for batch token counting."""

    success: bool = Field(True, description="Whether the request was successful")
    results: List[TokenCountResultItem] = Field(
        ...,
        description="Token count results for each input text"
    )


class TokenValidationRequest(BaseModel):
    """Request model for token budget validation."""

    texts: List[str] = Field(
        ...,
        description="List of text contents to validate against budget",
        min_length=1,
        max_length=50
    )
    budget: int = Field(
        ...,
        description="Maximum token budget",
        gt=0
    )


class TokenValidationResponse(BaseModel):
    """Response model for token budget validation."""

    success: bool = Field(True, description="Whether the request was successful")
    fits_budget: bool = Field(..., description="Whether all texts fit within the budget")
    total_tokens: int = Field(..., description="Total tokens used by all texts")
    budget: int = Field(..., description="Token budget limit")
    utilization: float = Field(..., description="Budget utilization percentage (0.0-1.0+)")
    remaining_tokens: int = Field(..., description="Remaining tokens in budget")
    overflow_tokens: int = Field(..., description="Tokens over budget (0 if within budget)")


class ErrorResponse(BaseModel):
    """Error response model."""

    success: bool = Field(False, description="Always false for error responses")
    error: str = Field(..., description="Error message")

class TokenLimitsRequest(BaseModel):
    pass

class TokenLimitsResponse(BaseModel):
  system_prompt_prefix: int = Field(description="System prompt prefix limit")
  system_prompt_suffix: int = Field(description="System prompt suffix limit")
  writing_assistant_prompt: int = Field(description="Writing assistant prompt limit")
  writing_editor_prompt: int = Field(description="Writing editor prompt limit")
  worldbuilding: int = Field(description="Worldbuilding token limit")
  plot_outline: int = Field(description="Plot outline token limit")
