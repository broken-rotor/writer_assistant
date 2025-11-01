"""
Modify chapter endpoint for Writer Assistant.
"""
from fastapi import APIRouter, HTTPException
from app.models.generation_models import (
    ModifyChapterRequest,
    ModifyChapterResponse
)
from app.services.llm_inference import get_llm
from app.services.unified_context_processor import get_unified_context_processor
from datetime import datetime, UTC
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/modify-chapter", response_model=ModifyChapterResponse)
async def modify_chapter(request: ModifyChapterRequest):
    """Modify an existing chapter using LLM with structured context only."""
    llm = get_llm()
    if not llm:
        raise HTTPException(status_code=503, detail="LLM not initialized. Start server with --model-path")

    try:
        # Get unified context processor
        context_processor = get_unified_context_processor()

        # Process context using structured context only
        context_result = context_processor.process_modify_chapter_context(
            # Core fields
            original_chapter=request.currentChapter,
            modification_request=request.userRequest,
            # Phase context
            compose_phase=request.compose_phase,
            phase_context=request.phase_context,
            # Structured context (required)
            structured_context=request.structured_context,
            context_mode="structured",
            context_processing_config=request.context_processing_config
        )

        # Log context processing results
        if context_result.optimization_applied:
            logger.info(f"Modify chapter context processing applied ({context_result.processing_mode} mode): "
                       f"{context_result.total_tokens} tokens, "
                       f"compression ratio: {context_result.compression_ratio:.2f}")
        else:
            logger.debug(f"No modify chapter context optimization needed ({context_result.processing_mode} mode): "
                        f"{context_result.total_tokens} tokens")

        # For modify chapter, we need to ensure the user message includes the current chapter and modification request
        # if it's not already included in the structured context
        modification_content = f"""
Current chapter:
{request.currentChapter}

User's modification request: {request.userRequest}

Rewrite the chapter incorporating the requested changes while maintaining consistency with the story."""

        # Combine context result with modification specific content
        if "Current chapter:" not in context_result.user_message:
            user_message = context_result.user_message + modification_content
        else:
            user_message = context_result.user_message

        # Prepare messages for LLM
        messages = [
            {"role": "system", "content": context_result.system_prompt.strip()},
            {"role": "user", "content": user_message.strip()}
        ]

        # Generate modified chapter using LLM
        response_text = llm.chat_completion(messages, max_tokens=2500, temperature=0.7)
        word_count = len(response_text.split())

        # Create response with context metadata
        return ModifyChapterResponse(
            modifiedChapter=response_text.strip(),
            wordCount=word_count,
            changesSummary=f"Modified based on: {request.userRequest[:150]}",
            context_metadata=context_result.context_metadata,
            metadata={
                "modifiedAt": datetime.now(UTC).isoformat(),
                "originalWordCount": len(request.currentChapter.split()),
                "modificationRequest": request.userRequest,
                "contextMode": "structured",
                "structuredContextProvided": bool(request.structured_context),
                "processingMode": context_result.processing_mode
            }
        )
    except Exception as e:
        logger.error(f"Error in modify_chapter: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error modifying chapter: {str(e)}")
