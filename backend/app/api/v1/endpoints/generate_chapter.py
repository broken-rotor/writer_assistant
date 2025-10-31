"""
Generate chapter endpoint for Writer Assistant.
"""
from fastapi import APIRouter, HTTPException
from app.models.generation_models import (
    GenerateChapterRequest,
    GenerateChapterResponse
)
from app.services.llm_inference import get_llm
from app.services.unified_context_processor import get_unified_context_processor
from datetime import datetime, UTC
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/generate-chapter", response_model=GenerateChapterResponse)
async def generate_chapter(request: GenerateChapterRequest):
    """Generate a complete chapter using LLM with structured context support."""
    llm = get_llm()
    if not llm:
        raise HTTPException(status_code=503, detail="LLM not initialized. Start server with --model-path")

    try:
        # Get unified context processor
        context_processor = get_unified_context_processor()

        # Process context using unified processor (supports both legacy and structured contexts)
        context_result = context_processor.process_generate_chapter_context(
            # Legacy fields
            system_prompts=request.systemPrompts,
            worldbuilding=request.worldbuilding,
            story_summary=request.storySummary,
            characters=request.characters,
            plot_point=request.plotPoint,
            incorporated_feedback=request.incorporatedFeedback,
            previous_chapters=request.previousChapters,
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
            logger.info(f"Context processing applied ({context_result.processing_mode} mode): "
                       f"{context_result.total_tokens} tokens, "
                       f"compression ratio: {context_result.compression_ratio:.2f}")
        else:
            logger.debug(f"No context optimization needed ({context_result.processing_mode} mode): "
                        f"{context_result.total_tokens} tokens")

        # Prepare messages for LLM
        messages = [
            {"role": "system", "content": context_result.system_prompt.strip()},
            {"role": "user", "content": context_result.user_message.strip()}
        ]

        # Generate chapter using LLM
        response_text = llm.chat_completion(messages, max_tokens=2000, temperature=0.8)
        word_count = len(response_text.split())

        # Create response with context metadata
        return GenerateChapterResponse(
            chapterText=response_text.strip(),
            wordCount=word_count,
            context_metadata=context_result.context_metadata,
            metadata={
                "generatedAt": datetime.now(UTC).isoformat(),
                "plotPoint": request.plotPoint,
                "feedbackItemsIncorporated": len(request.incorporatedFeedback or []),
                "composePhase": request.compose_phase,
                "phaseContextProvided": bool(request.phase_context),
                "contextMode": request.context_mode,
                "structuredContextProvided": bool(request.structured_context),
                "processingMode": context_result.processing_mode,
                "contextOptimizationApplied": context_result.optimization_applied
            }
        )
    except Exception as e:
        logger.error(f"Error in generate_chapter: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating chapter: {str(e)}")
