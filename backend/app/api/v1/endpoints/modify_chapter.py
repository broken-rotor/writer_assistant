"""
Modify chapter endpoint for Writer Assistant.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.generation_models import (
    ModifyChapterRequest,
    ModifyChapterResponse
)
from app.models.streaming_models import (
    StreamingStatusEvent,
    StreamingResultEvent,
    StreamingErrorEvent
)
from app.models.request_context import RequestContext, ChapterDetails
from app.services.llm_inference import get_llm
from app.services.context_builder import ContextBuilder
from app.core.config import settings
from datetime import datetime, UTC
from typing import List
from pydantic import BaseModel
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/modify-chapter")
async def modify_chapter(request: ModifyChapterRequest):
    """Modify an existing chapter using LLM with structured context and SSE streaming."""

    def key_plot_items(chapter: ChapterDetails) -> str:
        key_plot_items = [f"  - {i}\n" for i in chapter.key_plot_items]
        return f"**Key Plot Items:**\n{key_plot_items}" if key_plot_items else ""

    def get_incorporated_feedback(items: List[BaseModel], format: str) -> str:
        return '\n'.join([format.format(**i.model_dump()) for i in items])

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
            status_event = StreamingStatusEvent(
                phase='context_processing',
                message='Processing modification context...',
                progress=20
            )
            yield f"data: {status_event.model_dump_json()}\n\n"

            context_builder = ContextBuilder(request.request_context, llm)
            context_builder.add_long_term_elements(request.request_context.configuration.system_prompts.assistant_prompt)
            context_builder.add_character_states()
            context_builder.add_recent_story_summary()
            agent_instruction = f"""
Revise Chapter {chapter.number} based on the provided feedback and modification requests.

<ORIGINAL_CHAPTER>
**Title:** {chapter.title}
{f"**Plot Point:** {chapter.plot_point}" if chapter.plot_point else ""}

{key_plot_items(chapter)}

**Current Chapter Text:**
{chapter.content}
</ORIGINAL_CHAPTER>

<MODIFICATION_INSTRUCTIONS>
{f"**Primary User Request:** {request.user_feedback}" if request.user_feedback else ""}
{get_incorporated_feedback(request.character_feedback, 'Character {character_name} {type} Feedback: {content}')}
{get_incorporated_feedback(request.rater_feedback, 'Rater {rater_name} Feedback: {content}')}
{get_incorporated_feedback(request.editor_feedback, 'Editor Feedback: {content}')}
</MODIFICATION_INSTRUCTIONS>

<REVISION_GUIDELINES>
1. **Priority Order:**
   - Address explicit user requests first
   - Incorporate provided feedback where it improves the chapter
   - Maintain narrative consistency throughout

2. **Preservation:**
   - Keep elements that work well and don't need changes
   - Preserve character voices and established continuity
   - Maintain the chapter's core plot progression

3. **Integration:**
   - Blend changes naturally into the existing narrative
   - Ensure modified sections match the chapter's style and tone
   - Keep pacing and structure coherent

4. **Quality:**
   - Make improvements beyond just addressing feedback where appropriate
   - Ensure all changes enhance rather than dilute the story
   - Maintain vivid, engaging prose throughout
</REVISION_GUIDELINES>

Rewrite the complete chapter incorporating these revisions while preserving its strengths. Don't include the chapter title or number header.
"""
            context_builder.add_agent_instruction(agent_instruction)

            # Phase 2: Modifying
            status_event = StreamingStatusEvent(
                phase='modifying',
                message='Rewriting chapter with requested changes...',
                progress=40
            )
            yield f"data: {status_event.model_dump_json()}\n\n"

            # Collect generated text from streaming
            response_text = ""
            for token in llm.chat_completion_stream(
                context_builder.build_messages(),
                max_tokens=settings.ENDPOINT_MODIFY_CHAPTER_MAX_TOKENS,
                temperature=settings.ENDPOINT_MODIFY_CHAPTER_TEMPERATURE
            ):
                response_text += token
                # Optional: yield partial content updates (uncomment if desired)
                # yield f"data: {json.dumps({'type': 'partial', 'content':
                # token})}\n\n"

            # Phase 3: Finalizing
            status_event = StreamingStatusEvent(
                phase='finalizing',
                message='Finalizing modified chapter...',
                progress=90
            )
            yield f"data: {status_event.model_dump_json()}\n\n"

            # Final result
            result = ModifyChapterResponse(
                modifiedChapter=response_text.strip()
            )

            result_event = StreamingResultEvent(data=result.model_dump())
            yield f"data: {result_event.model_dump_json()}\n\n"

        except Exception as e:
            logger.exception("Error in modify_chapter")
            error_event = StreamingErrorEvent(message=str(e))
            yield f"data: {error_event.model_dump_json()}\n\n"

    return StreamingResponse(
        generate_with_updates(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
