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
        FleshOutType.WORLDBUILDING: "Expand the following text which is the world building of the story. Add relevant details while maintaining narrative consistency",
        FleshOutType.CHAPTER: "Expand the following text which is a chapter of the story. Add relevant details while maintaining narrative consistency"
    }
    async def generate_with_updates():
        try:
            # Phase 1: Context Processing
            yield f"data: {json.dumps({'type': 'status', 'phase': 'context_processing', 'message': 'Processing expansion context...', 'progress': 20})}\n\n"

            context_builder = ContextBuilder(request.request_context)
            context_builder.add_long_term_elements(request.request_context.configuration.system_prompts.assistant_prompt)
            context_builder.add_character_states()
            context_builder.add_recent_story_summary()
            context_builder.add_agent_instruction(f"{agent_instructions[request.request_type]}: {request.text_to_flesh_out}")

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
