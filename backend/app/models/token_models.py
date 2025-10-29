"""
Pydantic models for token counting API endpoints.

This module defines the request and response models for the token counting API,
supporting batch processing, content type detection, and comprehensive metadata.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum

from app.services.token_management import ContentType, CountingStrategy


class TokenCountRequestItem(BaseModel):
    """Individual text item for token counting."""
    
    text: str = Field(
        ...,
        description="Text content to count tokens for",
        json_schema_extra={
            'example': "You are a helpful writing assistant. Please help the user create engaging stories.",
        }
    )
    content_type: Optional[ContentType] = Field(
        None,
        description="Content type for the text (auto-detected if not provided)",
        json_schema_extra={
            'example': "system_prompt",
        }
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
    strategy: CountingStrategy = Field(
        CountingStrategy.EXACT,
        description="Token counting strategy to use"
    )
    include_metadata: bool = Field(
        True,
        description="Whether to include detailed metadata in response"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "texts": [
                    {
                        "text": "You are a helpful writing assistant.",
                        "content_type": "system_prompt"
                    },
                    {
                        "text": "Once upon a time, in a distant kingdom...",
                        "content_type": "narrative"
                    }
                ],
                "strategy": "exact",
                "include_metadata": True
            }
        }
    }


class TokenCountResultItem(BaseModel):
    """Individual token count result."""
    
    text: str = Field(..., description="Original text content")
    token_count: int = Field(..., description="Number of tokens in the text")
    content_type: ContentType = Field(..., description="Detected or specified content type")
    strategy: CountingStrategy = Field(..., description="Counting strategy used")
    overhead_applied: float = Field(..., description="Overhead multiplier applied")
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata about the token counting"
    )


class TokenCountResponse(BaseModel):
    """Response model for batch token counting."""
    
    success: bool = Field(True, description="Whether the request was successful")
    results: List[TokenCountResultItem] = Field(
        ...,
        description="Token count results for each input text"
    )
    summary: Dict[str, Any] = Field(
        ...,
        description="Summary statistics for the batch"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "results": [
                    {
                        "text": "You are a helpful writing assistant.",
                        "token_count": 8,
                        "content_type": "system_prompt",
                        "strategy": "exact",
                        "overhead_applied": 1.15,
                        "metadata": {
                            "base_count": 7,
                            "content_length": 35,
                            "content_multiplier": 1.15,
                            "tokenizer_used": True
                        }
                    }
                ],
                "summary": {
                    "total_texts": 1,
                    "total_tokens": 8,
                    "total_characters": 35,
                    "avg_tokens_per_text": 8.0,
                    "strategy_used": "exact"
                }
            }
        }
    }


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
    strategy: CountingStrategy = Field(
        CountingStrategy.CONSERVATIVE,
        description="Token counting strategy to use for validation"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "texts": [
                    "System prompt text here",
                    "User input text here",
                    "Assistant response text here"
                ],
                "budget": 4096,
                "strategy": "conservative"
            }
        }
    }


class TokenValidationResponse(BaseModel):
    """Response model for token budget validation."""
    
    success: bool = Field(True, description="Whether the request was successful")
    fits_budget: bool = Field(..., description="Whether all texts fit within the budget")
    total_tokens: int = Field(..., description="Total tokens used by all texts")
    budget: int = Field(..., description="Token budget limit")
    utilization: float = Field(..., description="Budget utilization percentage (0.0-1.0+)")
    remaining_tokens: int = Field(..., description="Remaining tokens in budget")
    overflow_tokens: int = Field(..., description="Tokens over budget (0 if within budget)")
    strategy_used: CountingStrategy = Field(..., description="Counting strategy used")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "fits_budget": True,
                "total_tokens": 3500,
                "budget": 4096,
                "utilization": 0.854,
                "remaining_tokens": 596,
                "overflow_tokens": 0,
                "strategy_used": "conservative"
            }
        }
    }


class ErrorResponse(BaseModel):
    """Error response model."""
    
    success: bool = Field(False, description="Always false for error responses")
    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error details"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": False,
                "error": "Validation error",
                "details": {
                    "field": "texts",
                    "message": "Text content too large (max 100KB)"
                }
            }
        }
    }
