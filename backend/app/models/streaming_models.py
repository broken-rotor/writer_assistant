"""
Streaming response models for Server-Sent Events (SSE) endpoints.
"""
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field
from enum import Enum


class StreamingEventType(str, Enum):
    """Types of streaming events that can be sent via SSE."""
    STATUS = "status"
    RESULT = "result"
    ERROR = "error"


class StreamingStatusEvent(BaseModel):
    """Status update event for streaming progress."""
    type: StreamingEventType = Field(default=StreamingEventType.STATUS)
    phase: str = Field(description="Current processing phase")
    message: str = Field(description="Human-readable status message")
    progress: int = Field(description="Progress percentage (0-100)", ge=0, le=100)
    data: Optional[Dict[str, Any]] = Field(default=None, description="Partial response data")


class StreamingResultEvent(BaseModel):
    """Final result event containing the complete response."""
    type: StreamingEventType = Field(default=StreamingEventType.RESULT)
    data: Dict[str, Any] = Field(description="Complete response data")
    status: str = Field(default="complete")


class StreamingErrorEvent(BaseModel):
    """Error event for streaming failures."""
    type: StreamingEventType = Field(default=StreamingEventType.ERROR)
    message: str = Field(description="Error message")
    error_code: Optional[str] = Field(default=None, description="Optional error code")