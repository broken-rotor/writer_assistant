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
from app.core.config import settings
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/regenerate-bio")
async def regenerate_bio(request: RegenerateBioRequest):
    """Regenerate character bio from detailed character information using LLM with SSE streaming."""

    def get_character_details() -> CharacterDetails:
        characters = [c for c in request.request_context.characters if c.name == request.character_name]
        if not characters:
            raise ValueError(f"Character {request.character_name} not found in request_context")
        elif len(characters) > 1:
            raise ValueError(f"Duplicate character name {request.character_name}")
        return characters[0]

    llm = get_llm()
    if not llm:
        raise HTTPException(
            status_code=503,
            detail="LLM not initialized. Start server with --model-path")

    async def generate_with_updates():
        try:
            character_details = get_character_details()

            # Phase 1: Context Processing
            yield f"data: {json.dumps({'type': 'status', 'phase': 'context_processing', 'message': 'Processing character details...', 'progress': 20})}\n\n"

            system_prompt = """You are a skilled writer assistant specializing in character development. Your task is to create a concise, engaging character bio that captures the essence of a character based on their detailed attributes.

Create a bio that:
- Is 2-4 sentences long
- Captures the character's core personality and key traits
- Mentions their most important motivations or defining characteristics
- Flows naturally and reads like a compelling character introduction
- Avoids listing attributes mechanically

Focus on what makes this character unique and interesting."""
            agent_instruction = "Based on the character details in CHARACTER_TO_GENERATE, create a concise and engaging bio. Please respond with just the bio text directly."

            context_builder = ContextBuilder(request.request_context)
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
