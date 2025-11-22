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
from app.models.streaming_models import (
    StreamingStatusEvent,
    StreamingResultEvent,
    StreamingErrorEvent
)
from app.models.request_context import RequestContext
from app.services.llm_inference import get_llm
from app.services.context_builder import ContextBuilder
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

    async def generate_with_updates():
        try:
            # Phase 1: Context Processing
            status_event = StreamingStatusEvent(
                phase='context_processing',
                message='Processing character context and plot point...',
                progress=25
            )
            yield f"data: {status_event.model_dump_json()}\n\n"

            character = get_character_details(request.request_context, request.character_name)
            system_prompt = f"""You are {character.name}, inhabiting this character fully. You must provide deep, authentic psychological and emotional feedback from this character's perspective.

Your responses must reflect:
- {character.name}'s core personality traits, values, and worldview
- Unresolved emotional wounds and how they color your reactions
- The specific dynamic with each character present in this scene
- Your current emotional baseline (stressed, hopeful, guarded, etc.)
- Physical condition and energy level affecting your reactions
- Subconscious patterns and defense mechanisms

Go beyond surface reactions. Show the layers—what {character.name} feels immediately, what bubbles up after, what they try to suppress, and what their body betrays before their mind catches up."""

            context_builder = ContextBuilder(request.request_context, llm)
            context_builder.add_long_term_elements(system_prompt)
            context_builder.add_character_states()
            context_builder.add_recent_story_summary()
            context_builder.add_agent_instruction(
                f"""Generate {character.name}'s complete psychological and emotional reaction to this plot point:
<PLOT_POINT>
{request.plotPoint}
</PLOT_POINT>

Respond in JSON format with rich, specific details:
{{
  "actions": [
    "3-5 physical actions with specific body language details (e.g., 'grips the doorframe until knuckles whiten' not just 'holds door')"
  ],
  "dialog": [
    "3-5 lines of dialog capturing {character.name}'s voice, including tone indicators (e.g., '(voice dropping to barely a whisper) I never wanted this.')"
  ],
  "physicalSensations": [
    "3-5 visceral, embodied sensations with location and intensity (e.g., 'cold dread pooling in the pit of stomach' not just 'feels scared')"
  ],
  "emotions": [
    "3-5 emotions with their intensity and any conflicting layers (e.g., 'relief warring with guilt—glad the threat is gone but ashamed of that gladness')"
  ],
  "internalMonologue": [
    "5-7 thoughts showing {character.name}'s inner voice, including immediate gut reactions, self-talk or rationalization, intrusive memories this triggers, what they're trying NOT to think about, and any cognitive dissonance"
  ],
  "goals": [
    "1-3 immediate desires or impulses, noting which ones {character.name} will act on vs. suppress"
  ],
  "memories": [
    "2-4 memories this triggers, with sensory details that flash through {character.name}'s mind"
  ],
  "subtext": [
    "2-3 things {character.name} is communicating nonverbally or hiding beneath their words"
  ]
}}

Make every element specific to {character.name}'s unique psychology—avoid generic reactions anyone might have.""")

            # Phase 2: Generation
            status_event = StreamingStatusEvent(
                phase='generating',
                message=f'Generating {character.name} feedback...',
                progress=40
            )
            yield f"data: {status_event.model_dump_json()}\n\n"

            # Generate character feedback using LLM
            response_text = llm.chat_completion(
                context_builder.build_messages(),
                max_tokens=settings.ENDPOINT_CHARACTER_FEEDBACK_MAX_TOKENS,
                temperature=settings.ENDPOINT_CHARACTER_FEEDBACK_TEMPERATURE,
                json_schema_class=CharacterFeedback
            )

            # Phase 3: Parsing
            status_event = StreamingStatusEvent(
                phase='parsing',
                message='Parsing character feedback response...',
                progress=90
            )
            yield f"data: {status_event.model_dump_json()}\n\n"

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

            result_event = StreamingResultEvent(data=result.model_dump())
            yield f"data: {result_event.model_dump_json()}\n\n"

        except Exception as e:
            logger.exception(f"Error in character_feedback")
            error_event = StreamingErrorEvent(message=str(e))
            yield f"data: {error_event.model_dump_json()}\n\n"

    return StreamingResponse(
        generate_with_updates(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
