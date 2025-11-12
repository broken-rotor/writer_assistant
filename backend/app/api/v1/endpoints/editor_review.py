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
from app.services.llm_inference import get_llm
from app.services.unified_context_processor import get_unified_context_processor
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
            # Phase 1: Context Processing
            yield f"data: {json.dumps({'type': 'status', 'phase': 'context_processing', 'message': 'Processing chapter and story context...', 'progress': 20})}\n\n"

            # Get unified context processor
            context_processor = get_unified_context_processor()

            # Process context using request context (preferred) or structured context (legacy)
            context_result = context_processor.process_editor_review_context(
                request_context=request.request_context,
                context_processing_config=request.context_processing_config,
                # Legacy parameter for backward compatibility
                structured_context=request.structured_context
            )

            # Log context processing results
            if context_result.optimization_applied:
                logger.info(
                    "Editor review context processing applied ("
                    f"{context_result.processing_mode} mode): "
                    f"{context_result.total_tokens} tokens, "
                    f"compression ratio: {context_result.compression_ratio:.2f}")
            else:
                logger.debug(
                    "No editor review context optimization needed ("
                    f"{context_result.processing_mode} mode): "
                    f"{context_result.total_tokens} tokens")

            # Phase 2: Analyzing
            yield f"data: {json.dumps({'type': 'status', 'phase': 'analyzing', 'message': 'Analyzing chapter for narrative issues...', 'progress': 50})}\n\n"

            # For editor review, we need to ensure the user message includes
            # the chapter to review and JSON format instruction
            chapter_review_content = f"""
Chapter to review:
{request.chapterToReview}

Provide 4-6 suggestions in JSON format:
{{
  "suggestions": [
    {{"issue": "brief issue description", "suggestion": "specific improvement suggestion", "priority": "high|medium|low"}}
  ]
}}"""

            # Combine context result with chapter review specific content
            if "Chapter to review:" not in context_result.user_message:
                user_message = context_result.user_message + chapter_review_content
            else:
                user_message = context_result.user_message

            # Prepare messages for LLM
            messages = [
                {"role": "system", "content": context_result.system_prompt.strip()},
                {"role": "user", "content": user_message.strip()}
            ]

            # Phase 3: Generating Suggestions
            yield f"data: {json.dumps({'type': 'status', 'phase': 'generating_suggestions', 'message': 'Generating improvement suggestions...', 'progress': 75})}\n\n"

            # Generate editor review using streaming LLM
            response_text = ""
            for token in llm.chat_completion_stream(
                messages,
                max_tokens=settings.ENDPOINT_EDITOR_REVIEW_MAX_TOKENS,
                temperature=settings.ENDPOINT_EDITOR_REVIEW_TEMPERATURE,
                json_schema_class=EditorSuggestion
            ):
                response_text += token
                # Optional: yield partial content updates (uncomment if desired)
                # yield f"data: {json.dumps({'type': 'partial', 'content':
                # token})}\n\n"

            # Phase 4: Parsing
            yield f"data: {json.dumps({'type': 'status', 'phase': 'parsing', 'message': 'Processing editor suggestions...', 'progress': 90})}\n\n"

            parsed = parse_json_response(response_text)

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

            if not suggestions:
                logger.warning(
                    "Failed to parse suggestions, using text fallback")
                lines = parse_list_response(response_text, "all")
                for i in range(0, min(len(lines), 6), 2):
                    if i + 1 < len(lines):
                        suggestions.append(EditorSuggestion(
                            issue=lines[i][:100],
                            suggestion=lines[i + 1][:200],
                            priority="medium"
                        ))

            if not suggestions:
                suggestions.append(
                    EditorSuggestion(
                        issue="General feedback",
                        suggestion="The chapter shows promise and could be enhanced with more specific details.",
                        priority="medium"))

            # Final result
            result = EditorReviewResponse(
                suggestions=suggestions,
                context_metadata=context_result.context_metadata
            )

            yield f"data: {json.dumps({'type': 'result', 'data': result.model_dump(), 'status': 'complete'})}\n\n"

        except Exception as e:
            logger.error(f"Error in editor_review: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate_with_updates(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
