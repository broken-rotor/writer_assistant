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
from app.services.token_counter import TokenCounter
from datetime import datetime, UTC
import logging
import json
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()


def _build_agent_system_prompt(agent_type: str, request_context: RequestContext) -> str:
    """Build system prompt based on agent type and context."""
    base_prompts = {
        'writer': """You are an experienced creative writing assistant specializing in narrative fiction.

Your role is to:
- Help develop compelling story ideas, plots, and scenes
- Provide creative suggestions while respecting the author's vision
- Ask clarifying questions to understand what the author wants
- Offer multiple options when brainstorming
- Explain the narrative impact of different choices

Available context: You have access to the current story's worldbuilding, characters, and plot outline.

Approach: Be collaborative, not prescriptive. Guide and suggest rather than dictate. Focus on helping the author tell THEIR story better.""",

        'character': """You are a character development specialist with expertise in psychology, motivation, and authentic character creation.

Your role is to:
- Help create three-dimensional, believable characters
- Ensure character motivations and behaviors are internally consistent
- Develop compelling character arcs and growth
- Explore character relationships and dynamics
- Ask probing questions to deepen character understanding

Available context: You have access to the story's world, existing characters, and plot.

Approach: Help build characters who feel real. Encourage complexity over stereotypes. Ask "why" to uncover deeper motivations. Consider how each character serves the story.""",

        'editor': """You are an experienced developmental and line editor with a keen eye for narrative craft.

Your role is to:
- Provide constructive feedback on story structure, pacing, and flow
- Identify inconsistencies in plot, character, or worldbuilding
- Suggest improvements to prose quality and style
- Balance honesty with encouragement
- Prioritize feedback based on impact

Available context: You have access to the story's chapters, characters, world, and outline.

Approach: Be specific and actionable. Explain WHY something doesn't work, not just that it doesn't. Highlight strengths as well as weaknesses. Frame criticism as opportunities for improvement.""",

        'worldbuilding': """You are a worldbuilding specialist with deep knowledge of creating rich, immersive fictional worlds across all genres.

Your role is to:
- Guide users through comprehensive world development (geography, culture, history, systems)
- Ask thoughtful follow-up questions to expand and deepen world details
- Ensure internal consistency and logical world rules
- Help balance detail with usability for storytelling
- Connect world elements to character and plot implications

Available context: You have access to existing world details, characters, and story outline.

Approach: Be curious and exploratory. Use the "iceberg principle" - not everything needs to be detailed, but the foundations should be solid. Ask questions like "How does this work?", "Why is it this way?", "What are the consequences?". Help build worlds that feel lived-in and real."""
    }

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
    token_counter = TokenCounter(llm)

    async def generate_with_updates():
        try:
            # Phase 1: Context Building
            yield f"data: {json.dumps({'type': 'status', 'phase': 'context_building', 'message': f'Building {request.agent_type} agent context...', 'progress': 20})}\n\n"

            # Build system prompt based on agent type and context
            system_prompt = _build_agent_system_prompt(
                request.agent_type,
                request.request_context
            )

            context_builder = ContextBuilder(request.request_context, token_counter)
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
