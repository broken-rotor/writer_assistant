"""
Generate chapter endpoint for Writer Assistant.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.generation_models import (
    GenerateChapterRequest,
    GenerateChapterResponse
)
from app.models.request_context import RequestContext, ChapterDetails
from app.services.llm_inference import get_llm
from app.services.context_builder import ContextBuilder
from app.core.config import settings
from datetime import datetime, UTC
import logging
import json
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/generate-chapter")
async def generate_chapter(request: GenerateChapterRequest):
    """Generate a complete chapter using LLM with structured context and SSE streaming."""

    def key_plot_items(chapter: ChapterDetails) -> str:
        key_plot_items = [f"  - {i}\n" for i in chapter.key_plot_items]
        return f"**Key Plot Items to Include:**\n{key_plot_items}" if key_plot_items else ""

    llm = get_llm()
    if not llm:
        raise HTTPException(
            status_code=503,
            detail="LLM not initialized. Start server with --model-path")

    async def generate_with_updates():
        try:
            if request.chapter_number <= 0 or request.chapter_number > len(request.request_context.chapters):
                raise ValueError("Invalid chapter number")
            chapter = request.request_context.chapters[request.chapter_number-1]

            # Phase 1: Context Processing
            yield f"data: {json.dumps({'type': 'status', 'phase': 'context_processing', 'message': 'Processing structured context and preparing prompts...', 'progress': 20})}\n\n"

            context_builder = ContextBuilder(request.request_context, llm)
            context_builder.add_long_term_elements(request.request_context.configuration.system_prompts.assistant_prompt)
            context_builder.add_character_states()
            context_builder.add_recent_story(include_up_to=chapter.number)

            agent_instruction = f"""
Write Chapter {chapter.number} of the story, maintaining consistency with the established narrative, characters, and world.

<CHAPTER_REQUIREMENTS>
**Title:** {chapter.title}
{f"**Overall Plot Point:** {chapter.plot_point}" if chapter.plot_point else ""}

{key_plot_items(chapter)}
</CHAPTER_REQUIREMENTS>

<WRITING_GUIDELINES>
1. **Narrative Consistency:** Align with established character voices, world rules, and ongoing plot threads
2. **Scene Structure:** Use clear scene breaks, vivid settings, and purposeful pacing
3. **Character Behavior:** Ensure characters act consistently with their personalities and motivations
4. **Show Don't Tell:** Prefer action and dialogue over exposition when possible
5. **Pacing:** Balance action, dialogue, description, and reflection appropriately
6. **Chapter Arc:** Give this chapter its own beginning, development, and conclusion while advancing the larger story
</WRITING_GUIDELINES>

<CONTEXT_AWARENESS>
- Review recent story events and character states to ensure continuity
- Reference worldbuilding details where relevant
- Build naturally on previous chapters' events and emotional arcs
</CONTEXT_AWARENESS>

Write the complete chapter now, developing the required plot elements in a narratively compelling way. Don't include the chapter title or number header.
"""
            context_builder.add_agent_instruction(agent_instruction)

            # Phase 2: Generation
            yield f"data: {json.dumps({'type': 'status', 'phase': 'generating', 'message': 'Generating chapter content...', 'progress': 40})}\n\n"

            # Collect generated text from streaming
            response_text = ""
            for token in llm.chat_completion_stream(
                context_builder.build_messages(),
                max_tokens=settings.ENDPOINT_GENERATE_CHAPTER_MAX_TOKENS,
                temperature=settings.ENDPOINT_GENERATE_CHAPTER_TEMPERATURE
            ):
                response_text += token
                # Optional: yield partial content updates (uncomment if desired)
                # yield f"data: {json.dumps({'type': 'partial', 'content':
                # token})}\n\n"

            # Phase 3: Finalizing
            yield f"data: {json.dumps({'type': 'status', 'phase': 'finalizing', 'message': 'Processing generated content...', 'progress': 90})}\n\n"

            word_count = len(response_text.split())

            # Final result
            result = GenerateChapterResponse(
                chapterText=response_text.strip(),
                wordCount=word_count,
                metadata={
                    "generatedAt": datetime.now(UTC).isoformat()})

            yield f"data: {json.dumps({'type': 'result', 'data': result.model_dump(), 'status': 'complete'})}\n\n"

        except Exception as e:
            logger.exception("Error in generate_chapter")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate_with_updates(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
