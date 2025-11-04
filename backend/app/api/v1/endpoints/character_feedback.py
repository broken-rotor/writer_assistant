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
from app.services.llm_inference import get_llm
from app.services.unified_context_processor import get_unified_context_processor
from app.api.v1.endpoints.shared_utils import parse_json_response, parse_list_response
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
            yield f"data: {json.dumps({'type': 'status', 'phase': 'context_processing', 'message': 'Processing character context and plot point...', 'progress': 25})}\n\n"

            # Extract character name from structured context
            character_name = "Character"
            if request.structured_context.character_contexts:
                character_name = request.structured_context.character_contexts[0].character_name

            # Get unified context processor
            context_processor = get_unified_context_processor()

            # Process context using structured context only
            context_result = context_processor.process_character_feedback_context(
                # Core fields
                plot_point=request.plotPoint,
                # Phase context
                compose_phase=request.compose_phase,
                phase_context=request.phase_context,
                # Structured context (required)
                structured_context=request.structured_context,
                context_mode="structured",
                context_processing_config=request.context_processing_config
            )

            # Log context processing results
            if context_result.optimization_applied:
                logger.info(
                    "Character feedback context processing applied ("
                    f"{context_result.processing_mode} mode): "
                    f"{context_result.total_tokens} tokens, "
                    f"compression ratio: {context_result.compression_ratio:.2f}")
            else:
                logger.debug(
                    "No character feedback context optimization needed ("
                    f"{context_result.processing_mode} mode): "
                    f"{context_result.total_tokens} tokens")

            # Phase 2: Generation
            yield f"data: {json.dumps({'type': 'status', 'phase': 'generating', 'message': f'Generating {character_name} feedback...', 'progress': 65})}\n\n"

            # For character feedback, we need to ensure the user message includes the JSON format instruction
            # if it's not already included in the structured context
            if not any(
                    "JSON format" in context_result.user_message for _ in [1]):
                json_instruction = f"""
Respond in JSON format with exactly these keys:
{{
  "actions": ["3-5 physical actions {character_name} takes"],
  "dialog": ["3-5 things {character_name} might say"],
  "physicalSensations": ["3-5 physical sensations {character_name} experiences"],
  "emotions": ["3-5 emotions {character_name} feels"],
  "internalMonologue": ["3-5 thoughts in {character_name}'s mind"]
}}"""
                user_message = context_result.user_message + json_instruction
            else:
                user_message = context_result.user_message

            # Prepare messages for LLM
            messages = [
                {"role": "system", "content": context_result.system_prompt.strip()},
                {"role": "user", "content": user_message.strip()}
            ]

            # Generate character feedback using LLM
            response_text = llm.chat_completion(
                messages,
                max_tokens=settings.ENDPOINT_CHARACTER_FEEDBACK_MAX_TOKENS,
                temperature=settings.ENDPOINT_CHARACTER_FEEDBACK_TEMPERATURE
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
                logger.warning("Failed to parse JSON, using text fallback")
                lines = parse_list_response(response_text, "all")
                feedback = CharacterFeedback(
                    actions=lines[0:3] if len(lines) > 0 else [
                        f"{character_name} responds"],
                    dialog=lines[3:6] if len(lines) > 3 else ["..."],
                    physicalSensations=lines[6:9] if len(lines) > 6 else [
                        "Feeling tense"],
                    emotions=lines[9:12] if len(lines) > 9 else ["Anxious"],
                    internalMonologue=lines[12:15] if len(
                        lines) > 12 else ["What now?"]
                )

            # Final result
            result = CharacterFeedbackResponse(
                characterName=character_name,
                feedback=feedback,
                context_metadata=context_result.context_metadata
            )

            yield f"data: {json.dumps({'type': 'result', 'data': result.model_dump(), 'status': 'complete'})}\n\n"

        except Exception as e:
            logger.error(f"Error in character_feedback: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate_with_updates(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
