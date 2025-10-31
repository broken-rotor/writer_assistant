"""
Modify chapter endpoint for Writer Assistant.
"""
from fastapi import APIRouter, HTTPException
from app.models.generation_models import (
    ModifyChapterRequest,
    ModifyChapterResponse
)
from app.services.llm_inference import get_llm
from app.services.context_optimization import get_context_optimization_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/modify-chapter", response_model=ModifyChapterResponse)
async def modify_chapter(request: ModifyChapterRequest):
    """Modify an existing chapter using LLM."""
    llm = get_llm()
    if not llm:
        raise HTTPException(status_code=503, detail="LLM not initialized. Start server with --model-path")

    try:
        system_prompt = f"""{request.systemPrompts.mainPrefix}
{request.systemPrompts.assistantPrompt or ''}

You are editing a chapter from a story.

{request.systemPrompts.mainSuffix}"""

        user_message = f"""Story context:
- World: {request.worldbuilding}
- Story: {request.storySummary}

Current chapter:
{request.currentChapter}

User's modification request: {request.userRequest}

Rewrite the chapter incorporating the requested changes while maintaining consistency with the story."""

        messages = [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_message.strip()}
        ]

        response_text = llm.chat_completion(messages, max_tokens=2500, temperature=0.7)
        word_count = len(response_text.split())

        return ModifyChapterResponse(
            modifiedChapter=response_text.strip(),
            wordCount=word_count,
            changesSummary=f"Modified based on: {request.userRequest[:150]}"
        )
    except Exception as e:
        logger.error(f"Error in modify_chapter: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error modifying chapter: {str(e)}")
