"""
Flesh out text expansion endpoint for Writer Assistant.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.generation_models import (
    FleshOutRequest,
    FleshOutResponse
)
from app.models.request_context import RequestContext
from app.services.llm_inference import get_llm
from app.services.unified_context_processor import get_unified_context_processor
from app.core.config import settings
from datetime import datetime, UTC
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

    async def generate_with_updates():
        try:
            # Phase 1: Context Processing
            yield f"data: {json.dumps({'type': 'status', 'phase': 'context_processing', 'message': 'Processing expansion context...', 'progress': 20})}\n\n"

            # Get unified context processor
            context_processor = get_unified_context_processor()
            context_result = context_processor.process_flesh_out_context(
                request_context=request.request_context,
                # Core fields
                outline_section=request.textToFleshOut,
                context_processing_config=request.context_processing_config
            )

            # Log context processing results
            if context_result.optimization_applied:
                logger.info(
                    "Flesh out context processing applied ("
                    f"{context_result.processing_mode} mode): "
                    f"{context_result.total_tokens} tokens, "
                    f"compression ratio: {context_result.compression_ratio:.2f}")
            else:
                logger.debug(
                    "No flesh out context optimization needed ("
                    f"{context_result.processing_mode} mode): "
                    f"{context_result.total_tokens} tokens")

            # Phase 2: Analyzing
            yield f"data: {json.dumps({'type': 'status', 'phase': 'analyzing', 'message': 'Analyzing text for expansion opportunities...', 'progress': 40})}\n\n"

            # For flesh out, we need to ensure the user message includes the text to expand
            # if it's not already included in the structured context
            expansion_content = f"""
Context type: {request.context}

Text to expand: {request.textToFleshOut}

Provide a detailed, atmospheric expansion (200-400 words)."""

            # Combine context result with expansion specific content
            if "Text to expand:" not in context_result.user_message:
                user_message = context_result.user_message + expansion_content
            else:
                user_message = context_result.user_message

            # Phase 3: Expanding
            yield f"data: {json.dumps({'type': 'status', 'phase': 'expanding', 'message': 'Generating expanded content...', 'progress': 70})}\n\n"

            # Prepare messages for LLM
            messages = [
                {"role": "system", "content": context_result.system_prompt.strip()},
                {"role": "user", "content": user_message.strip()}
            ]

            # Collect generated text from streaming
            response_text = ""
            for token in llm.chat_completion_stream(
                messages,
                max_tokens=settings.ENDPOINT_FLESH_OUT_MAX_TOKENS,
                temperature=settings.ENDPOINT_FLESH_OUT_TEMPERATURE
            ):
                response_text += token
                # Optional: yield partial content updates (uncomment if desired)
                # yield f"data: {json.dumps({'type': 'partial', 'content':
                # token})}\n\n"

            # Phase 4: Finalizing
            yield f"data: {json.dumps({'type': 'status', 'phase': 'finalizing', 'message': 'Finalizing expanded text...', 'progress': 90})}\n\n"

            # Final result
            result = FleshOutResponse(
                fleshedOutText=response_text.strip(),
                originalText=request.textToFleshOut,
                context_metadata=context_result.context_metadata,
                metadata={
                    "expandedAt": datetime.now(UTC).isoformat(),
                    "originalLength": len(
                        request.textToFleshOut),
                    "expandedLength": len(
                        response_text.strip()),
                    "contextType": request.context,
                    "contextMode": "structured",
                    "requestContextProvided": bool(
                        request.request_context),
                    "structuredContextProvided": bool(
                        request.structured_context),
                    "processingMode": context_result.processing_mode})

            yield f"data: {json.dumps({'type': 'result', 'data': result.model_dump(), 'status': 'complete'})}\n\n"

        except Exception as e:
            logger.error(f"Error in flesh_out: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate_with_updates(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
