"""
Pydantic models for worldbuilding sync functionality.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ChatMessage(BaseModel):
    """Chat message model matching frontend ChatMessage interface."""
    type: str = Field(..., description="Message type (user, assistant, system)")
    content: str = Field(..., description="Message content")
    timestamp: str = Field(..., description="ISO timestamp string")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional message metadata")


class WorldbuildingSyncRequest(BaseModel):
    """Request model for worldbuilding sync endpoint."""
    story_id: str = Field(..., description="Unique identifier for the story")
    messages: List[ChatMessage] = Field(..., description="Chat messages to process for worldbuilding")
    current_worldbuilding: str = Field(default="", description="Current worldbuilding content")
    force_sync: Optional[bool] = Field(default=False, description="Force sync even if no changes detected")


class WorldbuildingSyncMetadata(BaseModel):
    """Metadata for worldbuilding sync response."""
    story_id: str = Field(..., description="Story identifier")
    messages_processed: int = Field(..., description="Number of messages processed")
    content_length: int = Field(..., description="Length of updated worldbuilding content")
    topics_identified: List[str] = Field(default_factory=list, description="Worldbuilding topics identified")
    sync_timestamp: str = Field(..., description="ISO timestamp of sync operation")
    quality_score: float = Field(default=0.0, description="Quality score of worldbuilding content (0-1)")


class WorldbuildingSyncResponse(BaseModel):
    """Response model for worldbuilding sync endpoint."""
    success: bool = Field(..., description="Whether sync operation was successful")
    updated_worldbuilding: str = Field(..., description="Updated worldbuilding content")
    metadata: WorldbuildingSyncMetadata = Field(..., description="Sync operation metadata")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered during sync")


class WorldbuildingStatusResponse(BaseModel):
    """Response model for worldbuilding status/health check."""
    status: str = Field(default="ok", description="Service status")
    timestamp: str = Field(..., description="Current timestamp")
    version: str = Field(default="1.0.0", description="API version")

