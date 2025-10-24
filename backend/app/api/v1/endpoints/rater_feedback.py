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
from app.services.context_optimization import get_context_optimization_service
from app.api.v1.endpoints.shared_utils import parse_json_response, parse_list_response
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/rater-feedback", response_model=RaterFeedbackResponse)
async def rater_feedback(request: RaterFeedbackRequest):
    """Generate rater feedback for a plot point using LLM."""
    llm = get_llm()
    if not llm:
        raise HTTPException(status_code=503, detail="LLM not initialized. Start server with --model-path")

    try:
        # Get context optimization service
        context_service = get_context_optimization_service()
        
        # Optimize context transparently
        try:
            optimized_context = context_service.optimize_rater_feedback_context(
                system_prompts=request.systemPrompts,
                rater_prompt=request.raterPrompt,
                worldbuilding=request.worldbuilding,
                story_summary=request.storySummary,
                plot_point=request.plotPoint
            )
            
            system_prompt = optimized_context.system_prompt
            user_message = optimized_context.user_message
            
            # Log context optimization results
            if optimized_context.optimization_applied:
                logger.info(f"Rater feedback context optimization applied: {optimized_context.total_tokens} tokens, "
                           f"compression ratio: {optimized_context.compression_ratio:.2f}")
            else:
                logger.debug(f"No rater feedback context optimization needed: {optimized_context.total_tokens} tokens")
                
        except Exception as e:
            logger.warning(f"Rater feedback context optimization failed, using fallback: {str(e)}")
            # Fallback to original context building
            system_prompt = f"""{request.systemPrompts.mainPrefix}

{request.raterPrompt}

{request.systemPrompts.mainSuffix}"""

            user_message = f"""Evaluate this plot point:
- World: {request.worldbuilding}
- Story: {request.storySummary}
- Plot point: {request.plotPoint}

Provide feedback in JSON format:
{{
  "opinion": "Your overall opinion (2-3 sentences)",
  "suggestions": ["4-6 specific suggestions for improvement"]
}}"""

        messages = [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_message.strip()}
        ]

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

        return RaterFeedbackResponse(raterName="Rater", feedback=feedback)
    except Exception as e:
        logger.error(f"Error in rater_feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating rater feedback: {str(e)}")
