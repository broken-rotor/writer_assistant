"""
Flesh out text expansion endpoint for Writer Assistant.
"""
from fastapi import APIRouter, HTTPException
from app.models.generation_models import (
    FleshOutRequest,
    FleshOutResponse
)
from app.services.llm_inference import get_llm
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
