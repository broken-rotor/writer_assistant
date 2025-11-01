"""
Flesh out text expansion endpoint for Writer Assistant.
"""
from fastapi import APIRouter, HTTPException
from app.models.generation_models import (
    FleshOutRequest,
    FleshOutResponse
)
from app.services.llm_inference import get_llm
from app.services.unified_context_processor import get_unified_context_processor
from datetime import datetime, UTC
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/flesh-out", response_model=FleshOutResponse)
async def flesh_out(request: FleshOutRequest):
    """Flesh out/expand brief text using LLM with structured context only."""
    llm = get_llm()
    if not llm:
        raise HTTPException(status_code=503, detail="LLM not initialized. Start server with --model-path")

    try:
        # Get unified context processor
        context_processor = get_unified_context_processor()

        # Process context using structured context only
        context_result = context_processor.process_flesh_out_context(
            # Core fields
            outline_section=request.textToFleshOut,
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
            logger.info(f"Flesh out context processing applied ({context_result.processing_mode} mode): "
                       f"{context_result.total_tokens} tokens, "
                       f"compression ratio: {context_result.compression_ratio:.2f}")
        else:
            logger.debug(f"No flesh out context optimization needed ({context_result.processing_mode} mode): "
                        f"{context_result.total_tokens} tokens")

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

        # Prepare messages for LLM
        messages = [
            {"role": "system", "content": context_result.system_prompt.strip()},
            {"role": "user", "content": user_message.strip()}
        ]

        # Generate expanded text using LLM
        response_text = llm.chat_completion(messages, max_tokens=600, temperature=0.8)

        # Create response with context metadata
        return FleshOutResponse(
            fleshedOutText=response_text.strip(),
            originalText=request.textToFleshOut,
            context_metadata=context_result.context_metadata,
            metadata={
                "expandedAt": datetime.now(UTC).isoformat(),
                "originalLength": len(request.textToFleshOut),
                "expandedLength": len(response_text.strip()),
                "contextType": request.context,
                "contextMode": "structured",
                "structuredContextProvided": bool(request.structured_context),
                "processingMode": context_result.processing_mode
            }
        )
    except Exception as e:
        logger.error(f"Error in flesh_out: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fleshing out text: {str(e)}")
