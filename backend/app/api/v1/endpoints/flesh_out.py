"""
Flesh out text expansion endpoint for Writer Assistant.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.generation_models import (
    FleshOutRequest,
    FleshOutResponse,
    FleshOutType
)
from app.models.request_context import RequestContext
from app.services.llm_inference import get_llm
from app.services.context_builder import ContextBuilder
from app.core.config import settings
from datetime import datetime, UTC
from typing import Dict
import logging
import json
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/flesh-out")
async def flesh_out(request: FleshOutRequest):
    """Flesh out/expand brief text using LLM with structured context and SSE streaming."""
    llm = get_llm()
    if not llm:
        raise HTTPException(
            status_code=503,
            detail="LLM not initialized. Start server with --model-path")

    agent_instructions: Dict[FleshOutType, str] = {
        FleshOutType.WORLDBUILDING: """Expand and enrich the provided worldbuilding text with additional depth and detail.

<EXPANSION_APPROACH>
- Add concrete, specific details that make the world feel more real and lived-in
- Include sensory descriptions (sights, sounds, smells, textures, atmosphere)
- Develop cultural, historical, or social context where appropriate
- Introduce relevant world rules, customs, or unique elements
- Maintain consistency with established facts and tone
</EXPANSION_APPROACH>

<WHAT_TO_ADD>
- Vivid descriptive details that create mental imagery
- Contextual information that enriches understanding
- Logical extensions of existing concepts
- Interesting specifics that add flavor without overwhelming
</WHAT_TO_ADD>

<WHAT_TO_AVOID>
- Don't contradict existing information
- Don't add irrelevant tangents
- Don't over-explain obvious points
- Don't change the fundamental nature of what's described
</WHAT_TO_AVOID>

Aim to roughly double the length while maintaining quality and relevance. Focus on depth over breadth.""",

        FleshOutType.CHAPTER: """Expand the provided chapter text with additional narrative depth, detail, and richness.

<EXPANSION_APPROACH>
- Develop scenes with more vivid description and sensory detail
- Expand dialogue with more natural conversation and character voice
- Add internal character thoughts and emotional reactions
- Include setting details that establish atmosphere and mood
- Develop action sequences with clearer choreography and pacing
</EXPANSION_APPROACH>

<WHAT_TO_ADD>
- Sensory details that immerse the reader
- Character body language, expressions, and small actions
- Environmental details that set the scene
- Subtext in dialogue and character interactions
- Transitional moments between major beats
</WHAT_TO_ADD>

<WHAT_TO_AVOID>
- Don't add new plot points or major story changes
- Don't alter character motivations or behaviors
- Don't introduce new characters without cause
- Don't slow pacing with irrelevant details
- Don't change the chapter's fundamental arc
</WHAT_TO_AVOID>

Aim to expand by 50-100% while preserving the original's core narrative and maintaining consistent quality.""",

        FleshOutType.PLOT_OUTLINE: """Expand and enrich the provided plot outline with additional structural depth and narrative detail.

<EXPANSION_APPROACH>
- Develop story beats with more specific plot points and turning moments
- Add character development arcs and emotional journeys throughout the story
- Include conflict escalation patterns and tension building moments
- Expand on cause-and-effect relationships between plot events
- Add thematic elements and symbolic moments that support the story's meaning
- Include pacing notes and structural guidance for each section
</EXPANSION_APPROACH>

<WHAT_TO_ADD>
- Specific story beats and plot turning points within each act/section
- Character emotional states and development moments
- Conflict escalation and resolution patterns
- Subplots and how they weave into the main narrative
- Thematic elements and their development throughout the story
- Pacing guidance and structural notes
- Stakes and consequences for character actions
- Foreshadowing and setup/payoff moments
</WHAT_TO_ADD>

<WHAT_TO_AVOID>
- Don't write actual scenes or detailed prose
- Don't include specific dialogue or action descriptions
- Don't add new major characters or completely new plot threads
- Don't change the fundamental story structure or genre
- Don't write chapter content - focus on plot structure only
- Don't include scene-by-scene breakdowns - stay at the plot beat level
</WHAT_TO_AVOID>

Focus on expanding the structural and narrative elements while maintaining the outline format. Aim to roughly double the length by adding plot depth, character arcs, and thematic development without crossing into actual scene writing."""
    }

    async def generate_with_updates():
        try:
            # Phase 1: Context Processing
            yield f"data: {json.dumps({'type': 'status', 'phase': 'context_processing', 'message': 'Processing expansion context...', 'progress': 20})}\n\n"

            context_builder = ContextBuilder(request.request_context, llm)
            context_builder.add_long_term_elements(request.request_context.configuration.system_prompts.assistant_prompt)
            context_builder.add_character_states()
            context_builder.add_recent_story_summary()
            context_builder.add_agent_instruction(f"{agent_instructions[request.request_type]}. Text to expand: {request.text_to_flesh_out}")

            # Phase 2: Expanding
            yield f"data: {json.dumps({'type': 'status', 'phase': 'expanding', 'message': 'Generating expanded content...', 'progress': 40})}\n\n"

            # Collect generated text from streaming
            response_text = ""
            for token in llm.chat_completion_stream(
                context_builder.build_messages(),
                max_tokens=settings.ENDPOINT_FLESH_OUT_MAX_TOKENS,
                temperature=settings.ENDPOINT_FLESH_OUT_TEMPERATURE
            ):
                response_text += token
                # Optional: yield partial content updates (uncomment if desired)
                # yield f"data: {json.dumps({'type': 'partial', 'content':
                # token})}\n\n"

            # Phase 3: Finalizing
            yield f"data: {json.dumps({'type': 'status', 'phase': 'finalizing', 'message': 'Finalizing expanded text...', 'progress': 90})}\n\n"

            # Final result
            result = FleshOutResponse(
                fleshedOutText=response_text.strip(),
                originalText=request.text_to_flesh_out,
                metadata={
                    "expandedAt": datetime.now(UTC).isoformat(),
                    "originalLength": len(request.text_to_flesh_out),
                    "expandedLength": len(response_text.strip())})

            yield f"data: {json.dumps({'type': 'result', 'data': result.model_dump(), 'status': 'complete'})}\n\n"

        except Exception as e:
            logger.error(f"Error in flesh_out:", e)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate_with_updates(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
