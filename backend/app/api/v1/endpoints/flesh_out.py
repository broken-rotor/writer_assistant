"""
Flesh out text expansion endpoint for Writer Assistant.
"""
from fastapi import APIRouter, HTTPException
from app.models.generation_models import (
    FleshOutRequest,
    FleshOutResponse
)
from app.services.llm_inference import get_llm
from app.services.context_optimization import get_context_optimization_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/flesh-out", response_model=FleshOutResponse)
async def flesh_out(request: FleshOutRequest):
    """Flesh out/expand brief text using LLM."""
    llm = get_llm()
    if not llm:
        raise HTTPException(status_code=503, detail="LLM not initialized. Start server with --model-path")

    try:
        # Get context optimization service
        context_service = get_context_optimization_service()
        
        # Optimize context transparently
        try:
            optimized_context = context_service.optimize_flesh_out_context(
                system_prompts=request.systemPrompts,
                worldbuilding=request.worldbuilding,
                story_summary=request.storySummary,
                context=request.context,
                text_to_flesh_out=request.textToFleshOut
            )
            
            system_prompt = optimized_context.system_prompt
            user_message = optimized_context.user_message
            
            # Log context optimization results
            if optimized_context.optimization_applied:
                logger.info(f"Context optimization applied for flesh_out: {optimized_context.total_tokens} tokens, "
                           f"compression ratio: {optimized_context.compression_ratio:.2f}")
            else:
                logger.debug(f"No context optimization needed for flesh_out: {optimized_context.total_tokens} tokens")
                
        except Exception as e:
            logger.warning(f"Context optimization failed for flesh_out, using fallback: {str(e)}")
            # Fallback to original context building
            system_prompt = f"""{request.systemPrompts.mainPrefix}

Expand and flesh out brief text with rich detail, adding depth, sensory details, and narrative richness.

{request.systemPrompts.mainSuffix}"""

            user_message = f"""Story context:
- World: {request.worldbuilding}
- Story: {request.storySummary}
- Context type: {request.context}

Text to expand: {request.textToFleshOut}

Provide a detailed, atmospheric expansion (200-400 words)."""

        messages = [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_message.strip()}
        ]

        response_text = llm.chat_completion(messages, max_tokens=600, temperature=0.8)

        return FleshOutResponse(
            fleshedOutText=response_text.strip(),
            originalText=request.textToFleshOut
        )
    except Exception as e:
        logger.error(f"Error in flesh_out: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fleshing out text: {str(e)}")
