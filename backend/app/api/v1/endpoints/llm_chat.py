"""
LLM Chat endpoint for direct conversations with AI agents.
Separate from RAG chat functionality.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.chat_models import LLMChatRequest, LLMChatResponse, ConversationMessage
from app.models.request_context import RequestContext
from app.services.llm_inference import get_llm
from app.services.context_builder import ContextBuilder
from datetime import datetime, UTC
import logging
import json
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()


def _build_agent_system_prompt(agent_type: str, request_context: RequestContext) -> str:
    """Build system prompt based on agent type and context."""
    base_prompts = {
        'writer': "You are a skilled writer assistant helping with story creation. "
                  "Provide creative, engaging responses that help develop compelling narratives.",
        'character': "You are a character development specialist. Help create authentic, "
                     "well-rounded characters with realistic motivations and behaviors.",
        'editor': "You are an experienced editor providing constructive feedback on writing. "
                  "Focus on narrative flow, consistency, and overall story quality.",
        'worldbuilding': "You are a worldbuilding specialist helping create rich, immersive fictional worlds. "
                         "Guide users through developing comprehensive world details including geography, cultures, "
                         "magic systems, politics, history, and societies. Ask thoughtful follow-up questions to "
                         "help expand and deepen their world creation."}

    return base_prompts.get(agent_type, base_prompts['writer'])


@router.post("/chat/llm")
async def llm_chat(request: LLMChatRequest):
    """
    Direct LLM chat for interactive conversations with AI agents using SSE streaming.
    Separate from RAG chat functionality.
    """
    llm = get_llm()
    if not llm:
        raise HTTPException(
            status_code=503,
            detail="LLM not initialized. Start server with --model-path")

    async def generate_with_updates():
        try:
            # Phase 1: Context Building
            yield f"data: {json.dumps({'type': 'status', 'phase': 'context_building', 'message': f'Building {request.agent_type} agent context...', 'progress': 20})}\n\n"

            # Build system prompt based on agent type and context
            system_prompt = _build_agent_system_prompt(
                request.agent_type,
                request.request_context
            )

            context_builder = ContextBuilder(request.request_context)
            context_builder.add_long_term_elements(request.request_context.configuration.system_prompts.assistant_prompt)
            context_builder.add_character_states()
            context_builder.add_recent_story_summary()

            # Add conversation history
            for msg in request.messages:
                context_builder.add_chat(msg.role, msg.content)

            # Phase 2: Generation
            yield f"data: {json.dumps({'type': 'status', 'phase': 'generating', 'message': f'{request.agent_type.title()} agent is thinking...', 'progress': 40})}\n\n"

            # Get LLM response
            response_text = llm.chat_completion(
                context_builder.build_messages(),
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )

            # Phase 3: Formatting
            yield f"data: {json.dumps({'type': 'status', 'phase': 'formatting', 'message': 'Formatting response...', 'progress': 90})}\n\n"

            # Create response message
            response_message = ConversationMessage(
                role="assistant",
                content=response_text.strip(),
                timestamp=datetime.now(UTC).isoformat()
            )

            # Final result
            result = LLMChatResponse(
                message=response_message)

            yield f"data: {json.dumps({'type': 'result', 'data': result.dict(), 'status': 'complete'})}\n\n"

        except Exception as e:
            logger.error(f"Error in llm_chat", e)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate_with_updates(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
