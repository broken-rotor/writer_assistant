"""
Rater feedback endpoint for Writer Assistant.
"""
from fastapi import APIRouter, HTTPException
from app.models.generation_models import (
    RaterFeedbackRequest,
    RaterFeedbackResponse,
    RaterFeedback
)
from app.services.llm_inference import get_llm
from app.services.unified_context_processor import get_unified_context_processor
from app.api.v1.endpoints.shared_utils import parse_json_response, parse_list_response
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/rater-feedback", response_model=RaterFeedbackResponse)
async def rater_feedback(request: RaterFeedbackRequest):
    """Generate rater feedback for a plot point using LLM with structured context support."""
    llm = get_llm()
    if not llm:
        raise HTTPException(status_code=503, detail="LLM not initialized. Start server with --model-path")

    try:
        # Get unified context processor
        context_processor = get_unified_context_processor()

        # Process context using unified processor (supports both legacy and structured contexts)
        context_result = context_processor.process_rater_feedback_context(
            # Legacy fields
            system_prompts=request.systemPrompts,
            rater_prompt=request.raterPrompt,
            worldbuilding=request.worldbuilding,
            story_summary=request.storySummary,
            previous_chapters=request.previousChapters,
            plot_point=request.plotPoint,
            incorporated_feedback=request.incorporatedFeedback,
            # Phase context
            compose_phase=request.compose_phase,
            phase_context=request.phase_context,
            # Structured context
            structured_context=request.structured_context,
            context_mode=request.context_mode,
            context_processing_config=request.context_processing_config
        )

        # Log context processing results
        if context_result.optimization_applied:
            logger.info(f"Rater feedback context processing applied ({context_result.processing_mode} mode): "
                       f"{context_result.total_tokens} tokens, "
                       f"compression ratio: {context_result.compression_ratio:.2f}")
        else:
            logger.debug(f"No rater feedback context optimization needed ({context_result.processing_mode} mode): "
                        f"{context_result.total_tokens} tokens")

        # For rater feedback, we need to ensure the user message includes the JSON format instruction
        # if it's not already included in the structured context
        if not any("JSON format" in context_result.user_message for _ in [1]):
            json_instruction = f"""
Provide feedback in JSON format:
{{
  "opinion": "Your overall opinion (2-3 sentences)",
  "suggestions": ["4-6 specific suggestions for improvement"]
}}"""
            user_message = context_result.user_message + json_instruction
        else:
            user_message = context_result.user_message

        # Prepare messages for LLM
        messages = [
            {"role": "system", "content": context_result.system_prompt.strip()},
            {"role": "user", "content": user_message.strip()}
        ]

        # Generate rater feedback using LLM
        response_text = llm.chat_completion(messages, max_tokens=600, temperature=0.7)
        parsed = parse_json_response(response_text)

        if parsed and 'opinion' in parsed and 'suggestions' in parsed:
            feedback = RaterFeedback(**parsed)
        else:
            logger.warning("Failed to parse JSON, using text fallback")
            lines = parse_list_response(response_text, "all")
            feedback = RaterFeedback(
                opinion=lines[0] if lines else "The plot point has potential.",
                suggestions=lines[1:5] if len(lines) > 1 else ["Consider adding more detail"]
            )

        # Create response with context metadata
        return RaterFeedbackResponse(
            raterName="Rater",
            feedback=feedback,
            context_metadata=context_result.context_metadata
        )
    except Exception as e:
        logger.error(f"Error in rater_feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating rater feedback: {str(e)}")
