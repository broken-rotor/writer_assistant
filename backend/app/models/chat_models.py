"""
Pydantic models for LLM chat API requests and responses.
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from .generation_models import ConversationMessage
from .request_context import RequestContext


# Agent types for LLM chat
AgentType = Literal['writer', 'character', 'editor', 'worldbuilding']


class LLMChatRequest(BaseModel):
    """Request model for direct LLM chat (separate from RAG)."""
    messages: List[ConversationMessage]
    agent_type: AgentType
    
    request_context: RequestContext = Field(
        description="Complete request context with story configuration, worldbuilding, "
                    "characters, outline, and chapters"
    )
    
    # Optional parameters for chat behavior
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.8


class LLMChatResponse(BaseModel):
    """Response model for LLM chat."""
    message: ConversationMessage
