"""
Pydantic models for LLM chat API requests and responses.
Separate from RAG chat functionality.
"""
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel
from .generation_models import ConversationMessage, SystemPrompts


# Agent types for LLM chat
AgentType = Literal['writer', 'character', 'editor', 'worldbuilding']


class ChatComposeContext(BaseModel):
    """Context for compose system chat."""
    story_context: Dict[str, Any]  # Flexible story context
    chapter_draft: Optional[str] = None
    conversation_branch_id: Optional[str] = None
    # Worldbuilding-specific context
    worldbuilding_topic: Optional[str] = None
    worldbuilding_state: Optional[str] = None
    accumulated_worldbuilding: Optional[str] = None


class LLMChatRequest(BaseModel):
    """Request model for direct LLM chat (separate from RAG)."""
    messages: List[ConversationMessage]
    agent_type: AgentType
    compose_context: Optional[ChatComposeContext] = None
    system_prompts: Optional[SystemPrompts] = None
    # Optional parameters for chat behavior
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.8


class LLMChatResponse(BaseModel):
    """Response model for LLM chat."""
    message: ConversationMessage
    agent_type: AgentType
    metadata: Dict[str, Any]
