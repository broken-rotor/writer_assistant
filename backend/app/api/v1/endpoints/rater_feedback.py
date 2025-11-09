"""
Rater feedback endpoint for Writer Assistant.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.generation_models import (
    RaterFeedbackRequest,
    RaterFeedbackResponse,
    RaterFeedback
)
from app.models.streaming_models import (
    StreamingStatusEvent,
    StreamingResultEvent,
    StreamingErrorEvent,
    StreamingPhase,
    STREAMING_PHASES
)
from app.services.llm_inference import get_llm
from app.services.unified_context_processor import get_unified_context_processor
from app.api.v1.endpoints.shared_utils import parse_json_response, parse_list_response
from app.core.config import settings
import logging
import json
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/rater-feedback")
async def rater_feedback_stream(request: RaterFeedbackRequest):
    """Generate rater feedback with Server-Sent Events streaming for real-time progress updates."""

    async def generate_with_updates():
        try:
            # Phase 1: Context Processing
            status_event = StreamingStatusEvent(
                phase=StreamingPhase.CONTEXT_PROCESSING,
                message=STREAMING_PHASES[StreamingPhase.CONTEXT_PROCESSING]["message"],
                progress=STREAMING_PHASES[StreamingPhase.CONTEXT_PROCESSING]["progress"]
            )
            yield f"data: {status_event.model_dump_json()}\n\n"

            # Get unified context processor
            context_processor = get_unified_context_processor()
            context_result = context_processor.process_rater_feedback_context(
                rater_prompt=request.raterPrompt,
                plot_point=request.plotPoint,
                phase_context=request.phase_context,
                structured_context=request.structured_context,
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

            # Phase 2: Evaluating
            status_event = StreamingStatusEvent(
                phase=StreamingPhase.EVALUATING,
                message=STREAMING_PHASES[StreamingPhase.EVALUATING]["message"],
                progress=STREAMING_PHASES[StreamingPhase.EVALUATING]["progress"]
            )
            yield f"data: {status_event.model_dump_json()}\n\n"

            # Phase 3: Generating Feedback
            status_event = StreamingStatusEvent(
                phase=StreamingPhase.GENERATING_FEEDBACK,
                message=STREAMING_PHASES[StreamingPhase.GENERATING_FEEDBACK]["message"],
                progress=STREAMING_PHASES[StreamingPhase.GENERATING_FEEDBACK]["progress"]
            )
            yield f"data: {status_event.model_dump_json()}\n\n"

            # Prepare JSON instruction and messages
            json_instruction = '''
Provide feedback in JSON format:
{
  "opinion": "Your overall opinion (2-3 sentences)",
  "suggestions": ["4-6 specific suggestions for improvement"]
}'''

            user_message = context_result.user_message + json_instruction
            messages = [
                {"role": "system", "content": context_result.system_prompt.strip()},
                {"role": "user", "content": user_message.strip()}
            ]

            # Get LLM instance
            llm = get_llm()
            if not llm:
                error_event = StreamingErrorEvent(
                    message="LLM not initialized. Start server with --model-path"
                )
                yield f"data: {error_event.model_dump_json()}\n\n"
                return

            # Generate rater feedback using streaming LLM
            response_text = ""
            for chunk in llm.chat_completion_stream(
                messages,
                max_tokens=settings.ENDPOINT_RATER_FEEDBACK_MAX_TOKENS,
                temperature=settings.ENDPOINT_RATER_FEEDBACK_TEMPERATURE,
                json_schema_class=RaterFeedback
            ):
                response_text += chunk
                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.01)

            # Phase 4: Parsing
            status_event = StreamingStatusEvent(
                phase=StreamingPhase.PARSING,
                message=STREAMING_PHASES[StreamingPhase.PARSING]["message"],
                progress=STREAMING_PHASES[StreamingPhase.PARSING]["progress"]
            )
            yield f"data: {status_event.model_dump_json()}\n\n"

            # Parse the response
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

            # Final result
            result = RaterFeedbackResponse(
                raterName="Rater",
                feedback=feedback,
                context_metadata=context_result.context_metadata
            )

            # Phase 5: Complete
            result_event = StreamingResultEvent(
                data=result.model_dump(),
                status="complete"
            )
            yield f"data: {result_event.model_dump_json()}\n\n"

        except Exception as e:
            logger.error(f"Error in streaming rater_feedback: {str(e)}")
            error_event = StreamingErrorEvent(
                message=str(e)
            )
            yield f"data: {error_event.model_dump_json()}\n\n"

    return StreamingResponse(
        generate_with_updates(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )
