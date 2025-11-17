"""
Regenerate bio endpoint for Writer Assistant.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.generation_models import (
    RegenerateBioRequest,
    RegenerateBioResponse
)
from app.models.request_context import RequestContext, CharacterDetails
from app.services.llm_inference import get_llm
from app.services.context_builder import ContextBuilder
from app.services.token_counter import TokenCounter
from app.api.v1.endpoints.shared_utils import get_character_details
from app.core.config import settings
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/regenerate-bio")
async def regenerate_bio(request: RegenerateBioRequest):
    """Regenerate character bio from detailed character information using LLM with SSE streaming."""
    llm = get_llm()
    if not llm:
        raise HTTPException(
            status_code=503,
            detail="LLM not initialized. Start server with --model-path")
    token_counter = TokenCounter(llm)

    async def generate_with_updates():
        try:
            character_details = get_character_details(request.request_context, request.character_name)

            # Phase 1: Context Processing
            yield f"data: {json.dumps({'type': 'status', 'phase': 'context_processing', 'message': 'Processing character details...', 'progress': 20})}\n\n"

            system_prompt = """You are a skilled writer assistant specializing in character development. Your task is to distill detailed character information into a concise, compelling bio that captures a character's essence.

Create a bio that:
- **Length:** 2-4 sentences (aim for 3 as the sweet spot)
- **Content:** Focus on the character's core personality, defining traits, and primary motivation
- **Style:** Write in an engaging, natural voice - think book jacket or character introduction
- **Approach:** Weave attributes into flowing prose rather than listing them mechanically
- **Hook:** Lead with what makes this character distinctive and memorable

<EXAMPLES>
Good: "Sarah Chen moves through life with the calculated precision of a chess master, always three steps ahead of everyone around her. But beneath her controlled exterior lies a desperate fear of losing control, born from a childhood she's spent decades trying to forget. Her brilliance has earned her respect; her emotional walls have earned her loneliness."

Avoid: "Sarah is smart and calculating. She is afraid of losing control. She had a difficult childhood and now has trouble connecting with people."
</EXAMPLES>

Write a bio that makes the reader immediately understand and care about who this character is."""
            agent_instruction = "Based on the character details in CHARACTER_TO_GENERATE, create a concise and engaging bio. Please respond with just the bio text directly."

            context_builder = ContextBuilder(request.request_context, token_counter)
            context_builder.add_system_prompt(system_prompt)
            context_builder.add_worldbuilding()
            context_builder.add_characters(tag='OTHER_CHARACTERS', exclude_characters={request.character_name})
            context_builder.add_characters(tag='CHARACTER_TO_GENERATE', include_characters={request.character_name})
            context_builder.add_agent_instruction(agent_instruction)

            # Phase 2: Generating
            yield f"data: {json.dumps({'type': 'status', 'phase': 'generating', 'message': 'Generating bio summary...', 'progress': 40})}\n\n"

            # Collect generated text from streaming
            response_text = ""
            for token in llm.chat_completion_stream(
                    context_builder.build_messages(),
                    max_tokens=settings.ENDPOINT_GENERATE_CHARACTER_DETAILS_MAX_TOKENS,
                    temperature=settings.ENDPOINT_GENERATE_CHARACTER_DETAILS_TEMPERATURE):
                response_text += token
            
            # Phase 3: Processing
            yield f"data: {json.dumps({'type': 'status', 'phase': 'processing', 'message': 'Processing bio summary...', 'progress': 90})}\n\n"
            
            # Use the LLM response directly without any validation or fallback
            result = RegenerateBioResponse(
                basicBio=response_text.strip()
            )
            
            yield f"data: {json.dumps({'type': 'result', 'data': result.model_dump(), 'status': 'complete'})}\n\n"

        except Exception as e:
            logger.error(f"Error in regenerate_bio: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate_with_updates(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
