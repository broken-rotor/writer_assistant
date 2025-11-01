"""
Generate character details endpoint for Writer Assistant.
"""
from fastapi import APIRouter, HTTPException
from app.models.generation_models import (
    GenerateCharacterDetailsRequest,
    GenerateCharacterDetailsResponse
)
from app.services.llm_inference import get_llm
from app.services.unified_context_processor import get_unified_context_processor
from app.api.v1.endpoints.shared_utils import parse_json_response
from app.core.config import settings
import logging
import re

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/generate-character-details", response_model=GenerateCharacterDetailsResponse)
async def generate_character_details(request: GenerateCharacterDetailsRequest):
    """Generate detailed character information using LLM with structured context support."""
    llm = get_llm()
    if not llm:
        raise HTTPException(status_code=503, detail="LLM not initialized. Start server with --model-path")

    try:
        # Get unified context processor
        context_processor = get_unified_context_processor()

        # Process context using structured context only
        context_result = context_processor.process_character_generation_context(
            # Core fields
            basic_bio=request.basicBio,
            existing_characters=request.existingCharacters,
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
            logger.info(f"Character generation context processing applied ({context_result.processing_mode} mode): "
                       f"{context_result.total_tokens} tokens, "
                       f"compression ratio: {context_result.compression_ratio:.2f}")
        else:
            logger.debug(f"No character generation context optimization needed ({context_result.processing_mode} mode): "
                        f"{context_result.total_tokens} tokens")

        # For character generation, we need to ensure the user message includes the JSON format instruction
        # if it's not already included in the structured context
        if not any("JSON format" in context_result.user_message for _ in [1]):
            json_instruction = f"""

Generate complete character details in JSON format:
{{
  "name": "character name",
  "sex": "Male/Female/Other",
  "gender": "gender identity",
  "sexualPreference": "sexual orientation",
  "age": numeric age,
  "physicalAppearance": "detailed physical description",
  "usualClothing": "typical clothing style",
  "personality": "personality traits and quirks",
  "motivations": "what drives them",
  "fears": "what they fear",
  "relationships": "how they relate to others"
}}"""
            user_message = context_result.user_message + json_instruction
        else:
            user_message = context_result.user_message

        # Prepare messages for LLM
        messages = [
            {"role": "system", "content": context_result.system_prompt.strip()},
            {"role": "user", "content": user_message.strip()}
        ]

        # Generate character details using LLM
        response_text = llm.chat_completion(
        messages, 
        max_tokens=settings.ENDPOINT_GENERATE_CHARACTER_DETAILS_MAX_TOKENS, 
        temperature=settings.ENDPOINT_GENERATE_CHARACTER_DETAILS_TEMPERATURE
    )
        parsed = parse_json_response(response_text)

        if parsed and 'name' in parsed:
            return GenerateCharacterDetailsResponse(
                name=parsed.get('name', 'Character'),
                sex=parsed.get('sex', ''),
                gender=parsed.get('gender', ''),
                sexualPreference=parsed.get('sexualPreference', ''),
                age=int(parsed.get('age', 30)) if str(parsed.get('age', '')).isdigit() else 30,
                physicalAppearance=parsed.get('physicalAppearance', ''),
                usualClothing=parsed.get('usualClothing', ''),
                personality=parsed.get('personality', ''),
                motivations=parsed.get('motivations', ''),
                fears=parsed.get('fears', ''),
                relationships=parsed.get('relationships', ''),
                context_metadata=context_result.context_metadata
            )
        else:
            logger.warning("Failed to parse character JSON, using fallback")
            # Extract name from basic bio or generate one
            name_match = re.search(r'([A-Z][a-z]+ [A-Z][a-z]+)', request.basicBio)
            name = name_match.group(1) if name_match else "Alex Morgan"

            return GenerateCharacterDetailsResponse(
                name=name,
                sex="",
                gender="",
                sexualPreference="",
                age=30,
                physicalAppearance=f"A person matching the description: {request.basicBio[:100]}",
                usualClothing="Practical, comfortable clothing",
                personality=request.basicBio,
                motivations="To achieve their goals",
                fears="Failure and loss",
                relationships="Building connections with others",
                context_metadata=context_result.context_metadata
            )
    except Exception as e:
        logger.error(f"Error in generate_character_details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating character details: {str(e)}")
