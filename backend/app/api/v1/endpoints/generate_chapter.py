"""
Generate chapter endpoint for Writer Assistant.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.generation_models import (
    GenerateChapterRequest,
    GenerateChapterResponse
)
from app.services.llm_inference import get_llm
from app.services.unified_context_processor import get_unified_context_processor
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
    llm = get_llm()
    if not llm:
        raise HTTPException(
            status_code=503,
            detail="LLM not initialized. Start server with --model-path")

    async def generate_with_updates():
        try:
            # Phase 1: Context Processing
            yield f"data: {json.dumps({'type': 'status', 'phase': 'context_processing', 'message': 'Processing structured context and preparing prompts...', 'progress': 20})}\n\n"

            # Get unified context processor and process context
            context_processor = get_unified_context_processor()
            context_result = context_processor.process_generate_chapter_context(
                phase_context=request.phase_context,
                structured_context=request.structured_context,
                context_processing_config=request.context_processing_config)

            # Log context processing results
            if context_result.optimization_applied:
                logger.info(
                    "Context processing applied ("
                    f"{context_result.processing_mode} mode): "
                    f"{context_result.total_tokens} tokens, "
                    f"compression ratio: {context_result.compression_ratio:.2f}")
            else:
                logger.debug(
                    "No context optimization needed ("
                    f"{context_result.processing_mode} mode): "
                    f"{context_result.total_tokens} tokens")

            # Phase 2: Generation
            yield f"data: {json.dumps({'type': 'status', 'phase': 'generating', 'message': 'Generating chapter content...', 'progress': 60})}\n\n"

            # Prepare messages and generate
            messages = [
                {"role": "system", "content": context_result.system_prompt.strip()},
                {"role": "user", "content": context_result.user_message.strip()}
            ]

            # Collect generated text from streaming
            response_text = ""
            for token in llm.chat_completion_stream(
                messages,
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
                context_metadata=context_result.context_metadata,
                metadata={
                    "generatedAt": datetime.now(UTC).isoformat(),
                    "plotPoint": request.plotPoint,
                    "phaseContextProvided": bool(
                        request.phase_context),
                    "contextMode": "structured",
                    "structuredContextProvided": bool(
                        request.structured_context),
                    "processingMode": context_result.processing_mode})

            yield f"data: {json.dumps({'type': 'result', 'data': result.model_dump(), 'status': 'complete'})}\n\n"

        except Exception as e:
            logger.error(f"Error in generate_chapter: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate_with_updates(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
