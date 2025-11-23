"""
Agentic chapter modification endpoint for Writer Assistant.

This endpoint uses the agentic text generator to iteratively refine
a chapter until all feedback is properly incorporated.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.generation_models import ModifyChapterRequest
from app.models.agentic_models import AgenticConfig
from app.services.llm_inference import get_llm
from app.services.context_builder import ContextBuilder
from app.services.agentic_text_generator import AgenticTextGenerator
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/agentic-modify-chapter")
async def agentic_modify_chapter(request: ModifyChapterRequest):
    """
    Modify a chapter with agentic iteration to ensure all feedback is incorporated.

    The agent will:
    1. Generate a revised chapter based on feedback
    2. Evaluate if ALL feedback points were addressed
    3. Refine and retry if evaluation fails
    4. Return final result after passing evaluation or max iterations

    This endpoint demonstrates the agentic text generator with iterative refinement.
    """
    llm = get_llm()
    if not llm:
        raise HTTPException(
            status_code=503,
            detail="LLM not initialized. Start server with MODEL_PATH configured.")

    async def generate_with_updates():
        try:
            # Validate chapter number
            if request.chapter_number <= 0 or request.chapter_number > len(request.request_context.chapters):
                raise ValueError(f"Invalid chapter number: {request.chapter_number}")

            chapter = request.request_context.chapters[request.chapter_number - 1]

            # === STEP 1: Build base context (all the long-term story elements) ===
            # This context is prepared once and copied for each iteration
            status_event = StreamingStatusEvent(
                phase='context_processing',
                message='Processing modification context...',
                progress=10
            )
            yield f"data: {status_event.model_dump_json()}\n\n"

            base_context = ContextBuilder(request.request_context, llm)
            base_context.add_long_term_elements(
                request.request_context.configuration.system_prompts.assistant_prompt
            )
            base_context.add_character_states()
            base_context.add_recent_story_summary()
            # Note: We DON'T add the agent instruction yet - the agent will do that

            # === STEP 2: Define initial generation prompt ===
            initial_prompt = _build_generation_prompt(request, chapter)

            # === STEP 3: Define evaluation criteria ===
            evaluation_criteria = _build_evaluation_criteria(request, chapter)

            # === STEP 4: Configure agentic behavior ===
            config = AgenticConfig(
                max_iterations=3,
                generation_temperature=settings.ENDPOINT_MODIFY_CHAPTER_TEMPERATURE,
                generation_max_tokens=settings.ENDPOINT_MODIFY_CHAPTER_MAX_TOKENS,
                evaluation_temperature=0.3,
                evaluation_max_tokens=800
            )

            logger.info(f"Starting agentic modification of chapter {request.chapter_number} with config: {config}")

            # === STEP 5: Run agentic generation ===
            status_event = StreamingStatusEvent(
                phase='modifying',
                message='Rewriting chapter with requested changes...',
                progress=25
            )
            yield f"data: {status_event.model_dump_json()}\n\n"

            agent = AgenticTextGenerator(llm, config=config)

            async for event in agent.generate(
                base_context_builder=base_context,
                initial_generation_prompt=initial_prompt,
                evaluation_criteria=evaluation_criteria
            ):
                # Relay events directly to FastAPI SSE stream
                yield f"data: {event.model_dump_json()}\n\n"

        except Exception as e:
            logger.exception("Error in agentic_modify_chapter")
            from app.models.streaming_models import StreamingErrorEvent
            error_event = StreamingErrorEvent(message=str(e))
            yield f"data: {error_event.model_dump_json()}\n\n"

    return StreamingResponse(
        generate_with_updates(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


def _build_generation_prompt(request: ModifyChapterRequest, chapter) -> str:
    """
    Build the initial generation prompt with all feedback to incorporate.

    Args:
        request: ModifyChapterRequest with feedback items
        chapter: ChapterDetails from request context

    Returns:
        Formatted generation prompt
    """
    # Helper to format key plot items
    def key_plot_items_section(chapter) -> str:
        if not chapter.key_plot_items:
            return ""
        items = "\n".join([f"  - {item}" for item in chapter.key_plot_items])
        return f"\n**Key Plot Items:**\n{items}"

    # Build feedback sections
    feedback_sections = []

    if request.user_feedback:
        feedback_sections.append(f"**User Request:**\n{request.user_feedback}")

    if request.character_feedback:
        char_feedback = "\n".join([
            f"- Character {item.character_name} ({item.type}): {item.content}"
            for item in request.character_feedback
        ])
        feedback_sections.append(f"**Character Feedback:**\n{char_feedback}")

    if request.editor_feedback:
        editor_feedback = "\n".join([
            f"- {item.content}"
            for item in request.editor_feedback
        ])
        feedback_sections.append(f"**Editor Feedback:**\n{editor_feedback}")

    if request.rater_feedback:
        rater_feedback = "\n".join([
            f"- {item.rater_name}: {item.content}"
            for item in request.rater_feedback
        ])
        feedback_sections.append(f"**Rater Feedback:**\n{rater_feedback}")

    all_feedback = "\n\n".join(feedback_sections) if feedback_sections else "None provided"

    # Build complete prompt
    prompt = f"""Revise Chapter {chapter.number} to incorporate ALL the provided feedback while maintaining narrative quality and consistency.

<ORIGINAL_CHAPTER>
**Title:** {chapter.title}
{f"**Plot Point:** {chapter.plot_point}" if chapter.plot_point else ""}
{key_plot_items_section(chapter)}

**Current Content:**
{chapter.content}
</ORIGINAL_CHAPTER>

<FEEDBACK_TO_INCORPORATE>
{all_feedback}
</FEEDBACK_TO_INCORPORATE>

<REVISION_INSTRUCTIONS>
1. **Address ALL Feedback:** Every feedback item must be addressed in your revision
2. **Maintain Quality:** Preserve narrative quality, pacing, and character voices
3. **Natural Integration:** Blend changes smoothly into the existing narrative
4. **Consistency:** Ensure continuity with established story elements
5. **Complete Rewrite:** Provide the full revised chapter, not just changes
</REVISION_INSTRUCTIONS>

Write the complete revised chapter now (without chapter title/number header):"""

    return prompt


def _build_evaluation_criteria(request: ModifyChapterRequest, chapter) -> str:
    """
    Build specific evaluation criteria based on the feedback provided.

    The evaluation criteria ensure each feedback item is explicitly checked.

    Args:
        request: ModifyChapterRequest with feedback items
        chapter: ChapterDetails from request context

    Returns:
        Formatted evaluation criteria
    """
    criteria_parts = [
        "The revised chapter must meet ALL of the following criteria:\n"
    ]

    criteria_num = 1

    # User feedback criterion
    if request.user_feedback:
        criteria_parts.append(
            f"{criteria_num}. User Request Addressed: The revision must fully address the user's request: \"{request.user_feedback}\""
        )
        criteria_num += 1

    # Character feedback criteria
    if request.character_feedback:
        for cf in request.character_feedback:
            criteria_parts.append(
                f"{criteria_num}. Character {cf.character_name} ({cf.type}): {cf.content}"
            )
            criteria_num += 1

    # Editor feedback criteria
    if request.editor_feedback:
        for ef in request.editor_feedback:
            criteria_parts.append(
                f"{criteria_num}. Editor Feedback: {ef.content}"
            )
            criteria_num += 1

    # Rater feedback criteria
    if request.rater_feedback:
        for rf in request.rater_feedback:
            criteria_parts.append(
                f"{criteria_num}. {rf.rater_name} Feedback: {rf.content}"
            )
            criteria_num += 1

    # Quality criteria
    criteria_parts.append(
        f"{criteria_num}. Narrative Quality: The chapter must maintain or improve narrative consistency, "
        "character authenticity, pacing, and prose quality compared to the original."
    )

    return "\n".join(criteria_parts)
