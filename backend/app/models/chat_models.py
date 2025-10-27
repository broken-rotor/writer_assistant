"""
Pydantic models for LLM chat API requests and responses.
Separate from RAG chat functionality.
"""
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel
from .generation_models import ConversationMessage, ComposePhase, SystemPrompts


# Agent types for LLM chat
AgentType = Literal['writer', 'character', 'editor']


class ChatComposeContext(BaseModel):
    """Context for three-phase compose system chat."""
    current_phase: ComposePhase
    story_context: Dict[str, Any]  # Flexible story context
    chapter_draft: Optional[str] = None
    conversation_branch_id: Optional[str] = None


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
