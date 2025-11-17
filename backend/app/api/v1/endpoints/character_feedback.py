"""
Character feedback endpoint for Writer Assistant.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.generation_models import (
    CharacterFeedbackRequest,
    CharacterFeedbackResponse,
    CharacterFeedback
)
from app.models.request_context import RequestContext
from app.services.llm_inference import get_llm
from app.services.context_builder import ContextBuilder
from app.services.token_counter import TokenCounter
from app.api.v1.endpoints.shared_utils import parse_json_response, parse_list_response, get_character_details
from app.core.config import settings
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/character-feedback")
async def character_feedback(request: CharacterFeedbackRequest):
    """Generate character feedback for a plot point using LLM with structured context and SSE streaming."""
    llm = get_llm()
    if not llm:
        raise HTTPException(
            status_code=503,
            detail="LLM not initialized. Start server with --model-path")
    token_counter = TokenCounter(llm)

    async def generate_with_updates():
        try:
            # Phase 1: Context Processing
            yield f"data: {json.dumps({'type': 'status', 'phase': 'context_processing', 'message': 'Processing character context and plot point...', 'progress': 25})}\n\n"

            character = get_character_details(request.request_context, request.character_name)
            system_prompt = f"""You are {character.name}, a character in an ongoing story. Your role is to provide authentic emotional and behavioral feedback from your character's perspective.

When analyzing plot points or scenes:
- Respond as {character.name} would naturally react given your personality and current situation
- Draw from your established character traits, motivations, and fears
- Consider your relationships with other characters
- Reflect your current emotional state and recent experiences

Your feedback should be genuine to who {character.name} is, not what you think the story needs."""

            context_builder = ContextBuilder(request.request_context, token_counter)
            context_builder.add_long_term_elements(system_prompt)
            context_builder.add_character_states()
            context_builder.add_recent_story_summary()
            context_builder.add_agent_instruction(
                f"""Generate the reactions of {character.name} to the plot point that follow:
<PLOT_POINT>
{request.plotPoint}
</PLOT_POINT>

Respond in JSON format with exactly these keys:
{{
  "actions": ["3-5 physical actions {character.name} takes"],
  "dialog": ["3-5 things {character.name} might say"],
  "physicalSensations": ["3-5 physical sensations {character.name} experiences"],
  "emotions": ["3-5 emotions {character.name} feels"],
  "internalMonologue": ["3-5 thoughts in {character.name}'s mind"],
  "goals": ["0-2 current immediate goals and objectives {character.name} has"],
  "memories": ["0-3 Important memories affecting {character.name} current behavior and or relevant to their situation"]
}}""")

            # Phase 2: Generation
            yield f"data: {json.dumps({'type': 'status', 'phase': 'generating', 'message': f'Generating {character.name} feedback...', 'progress': 40})}\n\n"

            # Generate character feedback using LLM
            response_text = llm.chat_completion(
                context_builder.build_messages(),
                max_tokens=settings.ENDPOINT_CHARACTER_FEEDBACK_MAX_TOKENS,
                temperature=settings.ENDPOINT_CHARACTER_FEEDBACK_TEMPERATURE,
                json_schema_class=CharacterFeedback
            )

            # Phase 3: Parsing
            yield f"data: {json.dumps({'type': 'status', 'phase': 'parsing', 'message': 'Parsing character feedback response...', 'progress': 90})}\n\n"

            parsed = parse_json_response(response_text)
            if parsed and all(
                k in parsed for k in [
                    'actions',
                    'dialog',
                    'physicalSensations',
                    'emotions',
                    'internalMonologue']):
                feedback = CharacterFeedback(**parsed)
            else:
                logger.debug("Failed to parse JSON", response_text)
                raise ValueError("Failed to parse JSON from the LLM")

            # Final result
            result = CharacterFeedbackResponse(
                characterName=character.name,
                feedback=feedback
            )

            yield f"data: {json.dumps({'type': 'result', 'data': result.model_dump(), 'status': 'complete'})}\n\n"

        except Exception as e:
            logger.error(f"Error in character_feedback", e)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate_with_updates(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
