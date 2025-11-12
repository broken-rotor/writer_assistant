"""
LLM Chat endpoint for direct conversations with AI agents.
Separate from RAG chat functionality.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.chat_models import LLMChatRequest, LLMChatResponse, ConversationMessage
from app.services.llm_inference import get_llm
from datetime import datetime, UTC
import logging
import json
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()


def _build_agent_system_prompt(
        agent_type: str, request_context=None) -> str:
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

    prompt = base_prompts.get(agent_type, base_prompts['writer'])

    # Add custom system prompts if provided
    if request_context and request_context.configuration.system_prompts:
        if request_context.configuration.system_prompts.main_prefix:
            prompt = f"{request_context.configuration.system_prompts.main_prefix}\n{prompt}"
        if request_context.configuration.system_prompts.main_suffix:
            prompt = f"{prompt}\n{request_context.configuration.system_prompts.main_suffix}"

    return prompt


def _build_conversation_context(messages, request_context=None) -> str:
    """Build context from conversation history and request context."""
    context_parts = []

    if request_context:
        # Add story title and worldbuilding context
        if request_context.context_metadata.story_title:
            context_parts.append(f"Story Title: {request_context.context_metadata.story_title}")
        
        if request_context.worldbuilding.worldbuilding_details:
            context_parts.append(f"Worldbuilding: {request_context.worldbuilding.worldbuilding_details}")
        
        # Add character information
        if request_context.characters:
            context_parts.append("Characters:")
            for char in request_context.characters:
                char_info = f"- {char.character_name}"
                if char.basic_bio:
                    char_info += f": {char.basic_bio}"
                context_parts.append(char_info)
        
        # Add story outline if available
        if request_context.story_outline.outline_summary:
            context_parts.append(f"Story Outline: {request_context.story_outline.outline_summary}")

    return "\n".join(context_parts) if context_parts else ""


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
            yield f"data: {json.dumps({'type': 'status', 'phase': 'context_building', 'message': f'Building {request.agent_type} agent context...', 'progress': 30})}\n\n"

            # Build system prompt based on agent type and context
            system_prompt = _build_agent_system_prompt(
                request.agent_type,
                request.request_context
            )

            # Build conversation context
            context = _build_conversation_context(
                request.messages, request.request_context)

            # Prepare messages for LLM
            llm_messages = [{"role": "system", "content": system_prompt}]

            # Add context as first user message if available
            if context:
                llm_messages.append(
                    {"role": "user", "content": f"Context:\n{context}"})
                llm_messages.append(
                    {"role": "assistant", "content": "I understand the context. How can I help you?"})

            # Add conversation history
            for msg in request.messages:
                llm_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

            # Phase 2: Generation
            yield f"data: {json.dumps({'type': 'status', 'phase': 'generating', 'message': f'{request.agent_type.title()} agent is thinking...', 'progress': 70})}\n\n"

            # Get LLM response
            response_text = llm.chat_completion(
                llm_messages,
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
                message=response_message,
                agent_type=request.agent_type,
                metadata={
                    "generatedAt": datetime.now(UTC).isoformat(),
                    "conversationLength": len(request.messages),
                    "contextProvided": bool(context)})

            yield f"data: {json.dumps({'type': 'result', 'data': result.dict(), 'status': 'complete'})}\n\n"

        except Exception as e:
            logger.error(f"Error in llm_chat: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate_with_updates(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
