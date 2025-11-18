"""
Editor review endpoint for Writer Assistant.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.generation_models import (
    EditorReviewRequest,
    EditorReviewResponse,
    EditorSuggestion
)
from app.models.request_context import RequestContext
from app.services.llm_inference import get_llm
from app.services.context_builder import ContextBuilder
from app.api.v1.endpoints.shared_utils import parse_json_response, parse_list_response
from app.core.config import settings
import logging
import json
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/editor-review")
async def editor_review(request: EditorReviewRequest):
    """Generate editor review using LLM with structured context and SSE streaming."""
    llm = get_llm()
    if not llm:
        raise HTTPException(
            status_code=503,
            detail="LLM not initialized. Start server with --model-path")

    async def generate_with_updates():
        try:
            if request.chapter_number < 1 or request.chapter_number > len(request.request_context.chapters):
                raise ValueError(f"Invalid chapter number {request.chapter_number}")
            chapter = request.request_context.chapters[request.chapter_number-1]

            # Phase 1: Context Processing
            yield f"data: {json.dumps({'type': 'status', 'phase': 'context_processing', 'message': 'Processing chapter and story context...', 'progress': 20})}\n\n"

            context_builder = ContextBuilder(request.request_context, llm)
            context_builder.add_long_term_elements(request.request_context.configuration.system_prompts.editor_prompt)
            context_builder.add_character_states()
            context_builder.add_recent_story(include_up_to=request.chapter_number)
            agent_instruction = f"""
Review Chapter {request.chapter_number} for narrative quality and provide actionable improvement suggestions.

<EVALUATION_CRITERIA>
Focus on these aspects (in priority order):
1. **Narrative Consistency:** Does the chapter align with established plot, character behavior, and world rules?
2. **Pacing & Structure:** Does the chapter flow well? Are scenes properly balanced?
3. **Character Voice:** Do characters speak and act consistently with their established personalities?
4. **Show vs Tell:** Is the writing vivid and immersive, or overly expository?
5. **Clarity:** Is the prose clear and easy to follow?
6. **Style & Polish:** Are there opportunities to enhance the writing quality?
</EVALUATION_CRITERIA>

<CHAPTER_TO_REVIEW>
Chapter {chapter.number}: {chapter.title}

{chapter.content}
</CHAPTER_TO_REVIEW>

<PRIORITY_GUIDELINES>
- HIGH: Issues that break narrative consistency, confuse readers, or significantly harm pacing
- MEDIUM: Opportunities to enhance character voice, improve flow, or strengthen scenes
- LOW: Minor style improvements, word choice refinements, polish suggestions
</PRIORITY_GUIDELINES>

<OUTPUT_FORMAT>
Provide 4-6 specific, actionable suggestions in JSON format:
{{
  "suggestions": [
    {{"issue": "brief issue description", "suggestion": "specific improvement with example if possible", "priority": "high|medium|low"}}
  ]
}}
</OUTPUT_FORMAT>

Note: Focus on constructive improvements, not just criticism. Each suggestion should include a specific way to improve.
"""
            context_builder.add_agent_instruction(agent_instruction)

            # Phase 2: Generating Suggestions
            yield f"data: {json.dumps({'type': 'status', 'phase': 'generating_suggestions', 'message': 'Generating improvement suggestions...', 'progress': 40})}\n\n"

            # Generate editor review using streaming LLM
            response_text = ""
            for token in llm.chat_completion_stream(
                context_builder.build_messages(),
                max_tokens=settings.ENDPOINT_EDITOR_REVIEW_MAX_TOKENS,
                temperature=settings.ENDPOINT_EDITOR_REVIEW_TEMPERATURE,
                json_schema_class=EditorReviewResponse
            ):
                response_text += token
                # Optional: yield partial content updates (uncomment if desired)
                # yield f"data: {json.dumps({'type': 'partial', 'content':
                # token})}\n\n"

            # Phase 3: Parsing
            yield f"data: {json.dumps({'type': 'status', 'phase': 'parsing', 'message': 'Processing editor suggestions...', 'progress': 90})}\n\n"

            parsed = parse_json_response(response_text)
            if not parsed:
                logger.debug(f"Failed to parse suggestions: {response_text}")
                raise ValueError("Failed to parse JSON response from LLM")

            suggestions = []
            if parsed and 'suggestions' in parsed and isinstance(
                    parsed['suggestions'], list):
                for s in parsed['suggestions']:
                    if isinstance(
                            s, dict) and 'issue' in s and 'suggestion' in s:
                        suggestions.append(EditorSuggestion(
                            issue=s['issue'],
                            suggestion=s['suggestion'],
                            priority=s.get('priority', 'medium')
                        ))

            # Final result
            result = EditorReviewResponse(
                suggestions=suggestions
            )

            yield f"data: {json.dumps({'type': 'result', 'data': result.model_dump(), 'status': 'complete'})}\n\n"

        except Exception as e:
            logger.error(f"Error in editor_review", e)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate_with_updates(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
