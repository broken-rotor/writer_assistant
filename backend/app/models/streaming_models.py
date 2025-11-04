"""
Streaming response models for Server-Sent Events (SSE) endpoints.
"""
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field
from enum import Enum


class StreamingPhase(str, Enum):
    """Enumeration of streaming phases for various endpoints."""
    # Rater feedback phases
    CONTEXT_PROCESSING = "context_processing"
    EVALUATING = "evaluating"
    GENERATING_FEEDBACK = "generating_feedback"
    PARSING = "parsing"

    # RAG query phases
    INITIALIZING = "initializing"
    RETRIEVING = "retrieving"
    GENERATING = "generating"
    FORMATTING = "formatting"

    # Common completion phase
    COMPLETE = "complete"


class StreamingEventType(str, Enum):
    """Types of streaming events that can be sent via SSE."""
    STATUS = "status"
    RESULT = "result"
    ERROR = "error"


class StreamingStatusEvent(BaseModel):
    """Status update event for streaming progress."""
    type: StreamingEventType = Field(default=StreamingEventType.STATUS)
    phase: StreamingPhase = Field(description="Current processing phase")
    message: str = Field(description="Human-readable status message")
    progress: int = Field(description="Progress percentage (0-100)", ge=0, le=100)


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


# Phase configuration with progress percentages and messages
STREAMING_PHASES = {
    # Rater feedback phases
    StreamingPhase.CONTEXT_PROCESSING: {
        "progress": 20,
        "message": "Processing rater context and plot point..."
    },
    StreamingPhase.EVALUATING: {
        "progress": 50,
        "message": "Evaluating plot point against criteria..."
    },
    StreamingPhase.GENERATING_FEEDBACK: {
        "progress": 75,
        "message": "Generating detailed feedback..."
    },
    StreamingPhase.PARSING: {
        "progress": 90,
        "message": "Processing rater feedback..."
    },

    # RAG query phases
    StreamingPhase.INITIALIZING: {
        "progress": 15,
        "message": "Initializing RAG query..."
    },
    StreamingPhase.RETRIEVING: {
        "progress": 40,
        "message": "Searching for relevant context..."
    },
    StreamingPhase.GENERATING: {
        "progress": 70,
        "message": "Generating answer from context..."
    },
    StreamingPhase.FORMATTING: {
        "progress": 90,
        "message": "Formatting response and sources..."
    },

    # Common completion phase
    StreamingPhase.COMPLETE: {
        "progress": 100,
        "message": "Processing complete"
    }
}
