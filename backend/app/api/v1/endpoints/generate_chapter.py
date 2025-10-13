"""
Generate chapter endpoint for Writer Assistant.
"""
from fastapi import APIRouter, HTTPException
from app.models.generation_models import (
    GenerateChapterRequest,
    GenerateChapterResponse
)
from app.services.llm_inference import get_llm
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
        # Build character context
        char_context = "\n".join([
            f"- {c.name}: {c.basicBio} (Personality: {c.personality})"
            for c in request.characters[:3]  # Limit to avoid context overflow
        ])

        # Build feedback context
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
