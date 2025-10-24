"""
Generate chapter endpoint for Writer Assistant.
"""
from fastapi import APIRouter, HTTPException
from app.models.generation_models import (
    GenerateChapterRequest,
    GenerateChapterResponse
)
from app.services.llm_inference import get_llm
from app.services.context_optimization import get_context_optimization_service
from datetime import datetime, UTC
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/generate-chapter", response_model=GenerateChapterResponse)
async def generate_chapter(request: GenerateChapterRequest):
    """Generate a complete chapter using LLM."""
    llm = get_llm()
    if not llm:
        raise HTTPException(status_code=503, detail="LLM not initialized. Start server with --model-path")

    try:
        # Get context optimization service
        context_service = get_context_optimization_service()
        
        # Optimize context transparently
        try:
            optimized_context = context_service.optimize_chapter_generation_context(
                system_prompts=request.systemPrompts,
                worldbuilding=request.worldbuilding,
                story_summary=request.storySummary,
                characters=request.characters,
                plot_point=request.plotPoint,
                incorporated_feedback=request.incorporatedFeedback,
                previous_chapters=request.previousChapters
            )
            
            system_prompt = optimized_context.system_prompt
            user_message = optimized_context.user_message
            
            # Log context optimization results
            if optimized_context.optimization_applied:
                logger.info(f"Context optimization applied: {optimized_context.total_tokens} tokens, "
                           f"compression ratio: {optimized_context.compression_ratio:.2f}")
            else:
                logger.debug(f"No context optimization needed: {optimized_context.total_tokens} tokens")
                
        except Exception as e:
            logger.warning(f"Context optimization failed, using fallback: {str(e)}")
            # Fallback to original context building
            char_context = "\n".join([
                f"- {c.name}: {c.basicBio} (Personality: {c.personality})"
                for c in request.characters[:3]  # Limit to avoid context overflow
            ])

            feedback_context = ""
            if request.incorporatedFeedback:
                feedback_items = [f"- {f.content}" for f in request.incorporatedFeedback[:5]]
                feedback_context = "Incorporated feedback:\n" + "\n".join(feedback_items)

            system_prompt = f"""{request.systemPrompts.mainPrefix}
{request.systemPrompts.assistantPrompt or ''}

{request.systemPrompts.mainSuffix}"""

            user_message = f"""Write a chapter for this story:

World: {request.worldbuilding}
Story: {request.storySummary}

Characters:
{char_context}

Plot point for this chapter: {request.plotPoint}

{feedback_context}

Write an engaging chapter (800-1500 words) that brings this plot point to life with vivid prose, authentic dialogue, and character development."""

        messages = [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_message.strip()}
        ]

        response_text = llm.chat_completion(messages, max_tokens=2000, temperature=0.8)
        word_count = len(response_text.split())

        return GenerateChapterResponse(
            chapterText=response_text.strip(),
            wordCount=word_count,
            metadata={
                "generatedAt": datetime.now(UTC).isoformat(),
                "plotPoint": request.plotPoint,
                "feedbackItemsIncorporated": len(request.incorporatedFeedback)
            }
        )
    except Exception as e:
        logger.error(f"Error in generate_chapter: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating chapter: {str(e)}")
