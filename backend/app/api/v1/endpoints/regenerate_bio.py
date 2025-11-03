"""
Regenerate bio endpoint for Writer Assistant.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.generation_models import (
    RegenerateBioRequest,
    RegenerateBioResponse
)
from app.services.llm_inference import get_llm
from app.services.unified_context_processor import get_unified_context_processor
from app.api.v1.endpoints.shared_utils import parse_json_response
from app.core.config import settings
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/regenerate-bio")
async def regenerate_bio(request: RegenerateBioRequest):
    """Regenerate character bio from detailed character information using LLM with SSE streaming."""
    llm = get_llm()
    if not llm:
        raise HTTPException(status_code=503, detail="LLM not initialized. Start server with --model-path")

    async def generate_with_updates():
        try:
            # Phase 1: Context Processing
            yield f"data: {json.dumps({'type': 'status', 'phase': 'context_processing', 'message': 'Processing character details...', 'progress': 20})}\n\n"
            
            # Build character details summary for context
            character_details = []
            if request.name:
                character_details.append(f"Name: {request.name}")
            if request.sex:
                character_details.append(f"Sex: {request.sex}")
            if request.gender:
                character_details.append(f"Gender: {request.gender}")
            if request.sexualPreference:
                character_details.append(f"Sexual Preference: {request.sexualPreference}")
            if request.age and request.age > 0:
                character_details.append(f"Age: {request.age}")
            if request.physicalAppearance:
                character_details.append(f"Physical Appearance: {request.physicalAppearance}")
            if request.usualClothing:
                character_details.append(f"Usual Clothing: {request.usualClothing}")
            if request.personality:
                character_details.append(f"Personality: {request.personality}")
            if request.motivations:
                character_details.append(f"Motivations: {request.motivations}")
            if request.fears:
                character_details.append(f"Fears: {request.fears}")
            if request.relationships:
                character_details.append(f"Relationships: {request.relationships}")
            
            character_summary = "\n".join(character_details)
            
            # Use context processor if structured context is provided
            context_result = None
            if request.structured_context:
                context_processor = get_unified_context_processor()
                context_result = context_processor.process_character_generation_context(
                    basic_bio=character_summary,  # Use character details as "bio" for context
                    existing_characters=[],  # Not needed for bio regeneration
                    compose_phase=request.compose_phase,
                    phase_context=request.phase_context,
                    structured_context=request.structured_context,
                    context_mode="structured",
                    context_processing_config=request.context_processing_config
                )
                
                # Log context processing results
                if context_result.optimization_applied:
                    logger.info(f"Bio regeneration context processing applied ({context_result.processing_mode} mode): "
                               f"{context_result.total_tokens} tokens, "
                               f"compression ratio: {context_result.compression_ratio:.2f}")
                else:
                    logger.debug(f"No bio regeneration context optimization needed ({context_result.processing_mode} mode): "
                                f"{context_result.total_tokens} tokens")

            # Phase 2: Analyzing
            yield f"data: {json.dumps({'type': 'status', 'phase': 'analyzing', 'message': 'Analyzing character details...', 'progress': 40})}\n\n"
            
            # Phase 3: Generating
            yield f"data: {json.dumps({'type': 'status', 'phase': 'generating', 'message': 'Generating bio summary...', 'progress': 70})}\n\n"
            
            # Prepare system prompt and user message
            system_prompt = """You are a skilled writer assistant specializing in character development. Your task is to create a concise, engaging character bio that captures the essence of a character based on their detailed attributes.

Create a bio that:
- Is 2-4 sentences long
- Captures the character's core personality and key traits
- Mentions their most important motivations or defining characteristics
- Flows naturally and reads like a compelling character introduction
- Avoids listing attributes mechanically

Focus on what makes this character unique and interesting."""

            user_message = f"""Based on the following character details, create a concise and engaging bio:

{character_summary}

Please respond with a JSON object containing the bio:
{{"basicBio": "your generated bio here"}}"""

            # Use context result if available
            if context_result:
                system_prompt = context_result.system_prompt.strip()
                user_message = context_result.user_message + f"\n\n{user_message}"
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message.strip()}
            ]
            
            # Collect generated text from streaming
            response_text = ""
            for token in llm.chat_completion_stream(
                messages, 
                max_tokens=settings.ENDPOINT_GENERATE_CHARACTER_DETAILS_MAX_TOKENS, 
                temperature=settings.ENDPOINT_GENERATE_CHARACTER_DETAILS_TEMPERATURE
            ):
                response_text += token
            
            # Phase 4: Parsing
            yield f"data: {json.dumps({'type': 'status', 'phase': 'parsing', 'message': 'Processing bio summary...', 'progress': 90})}\n\n"
            
            parsed = parse_json_response(response_text)
            
            if parsed and 'basicBio' in parsed:
                result = RegenerateBioResponse(
                    basicBio=parsed.get('basicBio', ''),
                    context_metadata=context_result.context_metadata if context_result else None
                )
            else:
                logger.warning("Failed to parse bio JSON, using fallback")
                # Fallback: try to extract bio from response text or create a simple one
                bio_text = response_text.strip()
                if len(bio_text) > 500:  # If response is too long, truncate
                    bio_text = bio_text[:500] + "..."
                
                # If no reasonable bio found, create a basic one from the character name and key traits
                if not bio_text or len(bio_text) < 10:
                    key_traits = []
                    if request.personality:
                        key_traits.append(request.personality.split('.')[0])  # First sentence of personality
                    if request.motivations:
                        key_traits.append(request.motivations.split('.')[0])  # First sentence of motivations
                    
                    if key_traits:
                        bio_text = f"{request.name} is a character who {'. '.join(key_traits).lower()}."
                    else:
                        bio_text = f"{request.name} is a unique character with their own story to tell."
                
                result = RegenerateBioResponse(
                    basicBio=bio_text,
                    context_metadata=context_result.context_metadata if context_result else None
                )
            
            yield f"data: {json.dumps({'type': 'result', 'data': result.model_dump(), 'status': 'complete'})}\n\n"
            
        except Exception as e:
            logger.error(f"Error in regenerate_bio: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_with_updates(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
