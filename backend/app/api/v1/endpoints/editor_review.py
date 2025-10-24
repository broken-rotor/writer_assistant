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
from app.services.context_optimization import get_context_optimization_service
from app.api.v1.endpoints.shared_utils import parse_json_response, parse_list_response
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/editor-review", response_model=EditorReviewResponse)
async def editor_review(request: EditorReviewRequest):
    """Generate editor review using LLM."""
    llm = get_llm()
    if not llm:
        raise HTTPException(status_code=503, detail="LLM not initialized. Start server with --model-path")

    try:
        # Get context optimization service
        context_service = get_context_optimization_service()
        
        # Optimize context transparently
        try:
            optimized_context = context_service.optimize_editor_review_context(
                system_prompts=request.systemPrompts,
                worldbuilding=request.worldbuilding,
                story_summary=request.storySummary,
                chapter_to_review=request.chapterToReview
            )
            
            system_prompt = optimized_context.system_prompt
            user_message = optimized_context.user_message
            
            # Log context optimization results
            if optimized_context.optimization_applied:
                logger.info(f"Editor review context optimization applied: {optimized_context.total_tokens} tokens, "
                           f"compression ratio: {optimized_context.compression_ratio:.2f}")
            else:
                logger.debug(f"No editor review context optimization needed: {optimized_context.total_tokens} tokens")
                
        except Exception as e:
            logger.warning(f"Editor review context optimization failed, using fallback: {str(e)}")
            # Fallback to original context building
            system_prompt = f"""{request.systemPrompts.mainPrefix}
{request.systemPrompts.editorPrompt or 'You are an expert editor.'}

Review chapters and provide specific suggestions for improvement.

{request.systemPrompts.mainSuffix}"""

            user_message = f"""Story context:
- World: {request.worldbuilding}
- Story: {request.storySummary}

Chapter to review:
{request.chapterToReview}

Provide 4-6 suggestions in JSON format:
{{
  "suggestions": [
    {{"issue": "brief issue description", "suggestion": "specific improvement suggestion", "priority": "high|medium|low"}}
  ]
}}"""

        messages = [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_message.strip()}
        ]

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

        return EditorReviewResponse(suggestions=suggestions)
    except Exception as e:
        logger.error(f"Error in editor_review: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating editor review: {str(e)}")
