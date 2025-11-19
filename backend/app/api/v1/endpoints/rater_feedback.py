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
from app.models.request_context import RequestContext
from app.models.streaming_models import (
    StreamingStatusEvent,
    StreamingResultEvent,
    StreamingErrorEvent,
    StreamingPhase,
    STREAMING_PHASES
)
from app.services.llm_inference import get_llm
from app.services.context_builder import ContextBuilder
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

    def get_rater_prompt() -> str:
        raters = [r for r in request.request_context.configuration.raters
                  if r.name==request.raterName and r.enabled]
        if len(raters) == 0:
            raise ValueError(f"Rater {request.raterName} not found in request_context")
        elif len(raters) > 1:
            raise ValueError(f"Duplicate rater name {request.raterName}")
        return raters[0].system_prompt

    llm = get_llm()
    if not llm:
        raise HTTPException(
            status_code=503,
            detail="LLM not initialized. Start server with --model-path")

    async def generate_with_updates():
        try:
            raterPrompt = get_rater_prompt()

            # Phase 1: Context Processing
            yield f"data: {json.dumps({'type': 'status', 'phase': 'context_processing', 'message': 'Processing chapter and story context...', 'progress': 20})}\n\n"

            system_prompt = """You are an expert story evaluator with deep knowledge of narrative craft, character development, and storytelling techniques.

Your role is to:
1. Evaluate story elements against established quality criteria
2. Identify both strengths and areas for improvement
3. Provide specific, actionable feedback that helps improve the story
4. Balance constructive criticism with recognition of what works well

Your feedback should be:
- **Specific:** Point to exact elements, not general impressions
- **Actionable:** Suggest concrete ways to improve
- **Balanced:** Note both strengths and weaknesses
- **Constructive:** Frame criticism as opportunities for growth
- **Evidence-based:** Ground your evaluation in storytelling principles

Maintain a supportive but honest tone - your goal is to help the writer create the best story possible."""

            context_builder = ContextBuilder(request.request_context, llm)
            context_builder.add_long_term_elements(system_prompt)
            context_builder.add_character_states()
            context_builder.add_recent_story_summary()
            context_builder.add_agent_instruction(f"""Your criteria to evaluate the text is: {raterPrompt}

<TEXT_TO_EVALUATE>
{request.plotPoint}
</TEXT_TO_EVALUATE>

Provide feedback in JSON format:
{{
  "opinion": "Your overall opinion (2-3 sentences)",
  "suggestions": [
    {{
      "issue": "Brief description of the issue",
      "suggestion": "Specific actionable suggestion for improvement",
      "priority": "high/medium/low"
    }}
  ]
}}

Generate 4-6 suggestions, each with an issue, suggestion, and priority level.
""")

            # Phase 2: Generating Suggestions
            yield f"data: {json.dumps({'type': 'status', 'phase': 'generating_suggestions', 'message': 'Generating improvement suggestions...', 'progress': 40})}\n\n"

            # Generate editor review using streaming LLM
            response_text = ""
            for token in llm.chat_completion_stream(
                context_builder.build_messages(),
                max_tokens=settings.ENDPOINT_RATER_FEEDBACK_MAX_TOKENS,
                temperature=settings.ENDPOINT_RATER_FEEDBACK_TEMPERATURE,
                json_schema_class=RaterFeedback
            ):
                response_text += token
                # Optional: yield partial content updates (uncomment if desired)
                # yield f"data: {json.dumps({'type': 'partial', 'content':
                # token})}\n\n"

            # Phase 3: Parsing
            yield f"data: {json.dumps({'type': 'status', 'phase': 'parsing', 'message': 'Processing editor suggestions...', 'progress': 90})}\n\n"

            # Parse the response
            parsed = parse_json_response(response_text)

            if parsed and 'opinion' in parsed and 'suggestions' in parsed:
                feedback = RaterFeedback(**parsed)
            else:
                logger.debug(f"Failed to parse JSON: {response_text}")
                raise ValueError("Failed to parse JSON output from LLM")

            # Final result
            result = RaterFeedbackResponse(
                raterName=request.raterName,
                feedback=feedback
            )

            # Phase 5: Complete
            yield f"data: {json.dumps({'type': 'result', 'data': result.model_dump(), 'status': 'complete'})}\n\n"

        except Exception as e:
            logger.exception("Error in streaming rater_feedback")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate_with_updates(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
