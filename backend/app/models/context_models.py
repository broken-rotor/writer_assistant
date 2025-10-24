"""
Pydantic models for context management API requests and responses.

This module defines the data models for the context management endpoints,
including request validation, response formatting, and context statistics.
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum
from datetime import datetime


class ContextTypeEnum(str, Enum):
    """Types of context content for API requests."""
    SYSTEM = "system"
    STORY = "story"
    CHARACTER = "character"
    WORLD = "world"
    FEEDBACK = "feedback"
    MEMORY = "memory"


class LayerTypeEnum(str, Enum):
    """Layer types for hierarchical context management."""
    WORKING_MEMORY = "working_memory"
    SHORT_TERM_MEMORY = "short_term_memory"
    LONG_TERM_MEMORY = "long_term_memory"
    EPISODIC_MEMORY = "episodic_memory"
    AGENT_SPECIFIC_MEMORY = "agent_specific_memory"


class ContextItemRequest(BaseModel):
    """Individual context item in a management request."""
    content: str = Field(..., min_length=1, description="Content text to be managed")
    context_type: ContextTypeEnum = Field(..., description="Type of context content")
    priority: int = Field(default=0, ge=0, description="Priority level (higher = more important)")
    layer_type: LayerTypeEnum = Field(default=LayerTypeEnum.WORKING_MEMORY, description="Memory layer assignment")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    
    @validator('content')
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError('Content cannot be empty or whitespace only')
        return v.strip()
    
    @validator('metadata')
    def validate_metadata(cls, v):
        if v is None:
            return {}
        return v


class ContextManageRequest(BaseModel):
    """Request model for context management operations."""
    context_items: List[ContextItemRequest] = Field(..., min_items=1, description="List of context items to manage")
    target_tokens: Optional[int] = Field(default=None, gt=0, le=16000, description="Target token count for optimization")
    enable_compression: bool = Field(default=True, description="Whether to enable context compression")
    optimization_mode: str = Field(default="balanced", regex="^(aggressive|balanced|conservative)$", description="Optimization strategy")
    preserve_types: List[ContextTypeEnum] = Field(default=[], description="Context types to preserve from compression")
    
    @validator('context_items')
    def validate_context_items(cls, v):
        if not v:
            raise ValueError('At least one context item is required')
        
        # Check for required system context
        has_system = any(item.context_type == ContextTypeEnum.SYSTEM for item in v)
        if not has_system:
            raise ValueError('At least one SYSTEM context item is required')
        
        return v
    
    @validator('preserve_types')
    def validate_preserve_types(cls, v):
        # Always preserve SYSTEM context
        if ContextTypeEnum.SYSTEM not in v:
            v.append(ContextTypeEnum.SYSTEM)
        return v


class ContextAnalysisResponse(BaseModel):
    """Analysis results for context content."""
    total_tokens: int = Field(..., description="Total token count across all items")
    total_items: int = Field(..., description="Total number of context items")
    tokens_by_type: Dict[str, int] = Field(..., description="Token count breakdown by context type")
    tokens_by_layer: Dict[str, int] = Field(..., description="Token count breakdown by layer type")
    optimization_needed: bool = Field(..., description="Whether optimization is recommended")
    compression_candidates: List[str] = Field(..., description="Layers that could benefit from compression")
    recommendations: List[str] = Field(..., description="Optimization recommendations")
    utilization_ratio: float = Field(..., description="Context utilization as ratio of maximum")


class ContextOptimizationResponse(BaseModel):
    """Results of context optimization process."""
    optimized_content: Dict[str, str] = Field(..., description="Optimized content by context type")
    original_tokens: int = Field(..., description="Original token count before optimization")
    optimized_tokens: int = Field(..., description="Final token count after optimization")
    compression_ratio: float = Field(..., description="Compression ratio (optimized/original)")
    distillation_applied: bool = Field(..., description="Whether context distillation was applied")
    layers_compressed: List[str] = Field(..., description="List of layers that were compressed")
    token_reduction: int = Field(..., description="Number of tokens reduced")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


class ContextValidationResponse(BaseModel):
    """Results of context validation."""
    is_valid: bool = Field(..., description="Whether the context is valid")
    errors: List[str] = Field(..., description="List of validation errors")
    warnings: List[str] = Field(default=[], description="List of validation warnings")


class ContextStatistics(BaseModel):
    """Comprehensive context statistics."""
    total_items: int = Field(..., description="Total number of context items")
    total_tokens: int = Field(..., description="Total token count")
    tokens_by_type: Dict[str, int] = Field(..., description="Tokens by context type")
    tokens_by_layer: Dict[str, int] = Field(..., description="Tokens by layer type")
    optimization_needed: bool = Field(..., description="Whether optimization is needed")
    compression_candidates: List[str] = Field(..., description="Compression candidates")
    recommendations: List[str] = Field(..., description="Recommendations")
    utilization_ratio: float = Field(..., description="Context utilization ratio")
    distillation_threshold: int = Field(..., description="Token threshold for distillation")
    max_context_tokens: int = Field(..., description="Maximum allowed context tokens")


class ContextManageResponse(BaseModel):
    """Complete response for context management operations."""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Human-readable status message")
    analysis: ContextAnalysisResponse = Field(..., description="Context analysis results")
    optimization: Optional[ContextOptimizationResponse] = Field(default=None, description="Optimization results if applied")
    validation: ContextValidationResponse = Field(..., description="Validation results")
    statistics: ContextStatistics = Field(..., description="Comprehensive statistics")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ContextHealthCheckResponse(BaseModel):
    """Response for context management health check."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Context manager version")
    services: Dict[str, str] = Field(..., description="Status of dependent services")
    configuration: Dict[str, Any] = Field(..., description="Current configuration")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Error response models
class ContextErrorDetail(BaseModel):
    """Detailed error information."""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    field: Optional[str] = Field(default=None, description="Field that caused the error")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional error context")


class ContextErrorResponse(BaseModel):
    """Error response for context management operations."""
    success: bool = Field(default=False, description="Always false for error responses")
    error: str = Field(..., description="Main error message")
    details: List[ContextErrorDetail] = Field(default=[], description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    request_id: Optional[str] = Field(default=None, description="Request identifier for tracking")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Utility models for integration with existing endpoints
class OptimizedContextData(BaseModel):
    """Optimized context data for integration with generation endpoints."""
    system_context: str = Field(..., description="Optimized system prompts and configuration")
    story_context: str = Field(..., description="Optimized story and world information")
    character_context: str = Field(..., description="Optimized character information")
    feedback_context: str = Field(..., description="Optimized feedback and memory")
    total_tokens: int = Field(..., description="Total tokens in optimized context")
    compression_applied: bool = Field(..., description="Whether compression was applied")
    metadata: Dict[str, Any] = Field(default={}, description="Optimization metadata")


class ContextIntegrationRequest(BaseModel):
    """Request model for integrating context management with existing endpoints."""
    # Standard generation request fields
    worldbuilding: str = Field(..., description="World building information")
    story_summary: str = Field(..., description="Story summary")
    characters: List[Dict[str, Any]] = Field(..., description="Character information")
    system_prompts: Dict[str, str] = Field(..., description="System prompts")
    feedback: List[Dict[str, Any]] = Field(default=[], description="Feedback items")
    
    # Context management options
    enable_context_optimization: bool = Field(default=True, description="Enable context optimization")
    target_tokens: Optional[int] = Field(default=None, description="Target token count")
    preserve_context_types: List[ContextTypeEnum] = Field(default=[], description="Context types to preserve")
    
    @validator('preserve_context_types')
    def ensure_system_preserved(cls, v):
        if ContextTypeEnum.SYSTEM not in v:
            v.append(ContextTypeEnum.SYSTEM)
        return v
