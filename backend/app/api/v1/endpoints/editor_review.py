"""
Editor review endpoint for Writer Assistant.
"""
from fastapi import APIRouter, HTTPException
from app.models.generation_models import (
    EditorReviewRequest,
    EditorReviewResponse,
    EditorSuggestion
)
from app.services.llm_inference import get_llm
from app.services.unified_context_processor import get_unified_context_processor
from app.api.v1.endpoints.shared_utils import parse_json_response, parse_list_response
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/editor-review", response_model=EditorReviewResponse)
async def editor_review(request: EditorReviewRequest):
    """Generate editor review using LLM with structured context support."""
    llm = get_llm()
    if not llm:
        raise HTTPException(status_code=503, detail="LLM not initialized. Start server with --model-path")

    try:
        # Get unified context processor
        context_processor = get_unified_context_processor()

        # Process context using unified processor (supports both legacy and structured contexts)
        context_result = context_processor.process_editor_review_context(
            # Legacy fields
            system_prompts=request.systemPrompts,
            worldbuilding=request.worldbuilding,
            story_summary=request.storySummary,
            previous_chapters=[],  # Editor review doesn't use previous chapters in current implementation
            plot_point=getattr(request, 'chapterToReview', '')[:200],  # Use first 200 chars as plot point
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
            logger.info(f"Editor review context processing applied ({context_result.processing_mode} mode): "
                       f"{context_result.total_tokens} tokens, "
                       f"compression ratio: {context_result.compression_ratio:.2f}")
        else:
            logger.debug(f"No editor review context optimization needed ({context_result.processing_mode} mode): "
                        f"{context_result.total_tokens} tokens")

        # For editor review, we need to ensure the user message includes the chapter to review and JSON format instruction
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

        # Generate editor review using LLM
        response_text = llm.chat_completion(messages, max_tokens=800, temperature=0.6)
        parsed = parse_json_response(response_text)

        suggestions = []
        if parsed and 'suggestions' in parsed and isinstance(parsed['suggestions'], list):
            for s in parsed['suggestions']:
                if isinstance(s, dict) and 'issue' in s and 'suggestion' in s:
                    suggestions.append(EditorSuggestion(
                        issue=s['issue'],
                        suggestion=s['suggestion'],
                        priority=s.get('priority', 'medium')
                    ))

        if not suggestions:
            logger.warning("Failed to parse suggestions, using text fallback")
            lines = parse_list_response(response_text, "all")
            for i in range(0, min(len(lines), 6), 2):
                if i + 1 < len(lines):
                    suggestions.append(EditorSuggestion(
                        issue=lines[i][:100],
                        suggestion=lines[i + 1][:200],
                        priority="medium"
                    ))

        if not suggestions:
            suggestions.append(EditorSuggestion(
                issue="General feedback",
                suggestion="The chapter shows promise and could be enhanced with more specific details.",
                priority="medium"
            ))

        # Create response with context metadata
        return EditorReviewResponse(
            suggestions=suggestions,
            context_metadata=context_result.context_metadata
        )
    except Exception as e:
        logger.error(f"Error in editor_review: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating editor review: {str(e)}")
