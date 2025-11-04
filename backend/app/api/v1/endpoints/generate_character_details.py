"""
Generate character details endpoint for Writer Assistant.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
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
import json

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/generate-character-details")
async def generate_character_details(request: GenerateCharacterDetailsRequest):
    """Generate detailed character information using LLM with structured context and SSE streaming."""
    llm = get_llm()
    if not llm:
        raise HTTPException(
            status_code=503,
            detail="LLM not initialized. Start server with --model-path")

    async def generate_with_updates():
        try:
            # Phase 1: Context Processing
            yield f"data: {json.dumps({'type': 'status', 'phase': 'context_processing', 'message': 'Processing character context...', 'progress': 20})}\n\n"

            # Get unified context processor
            context_processor = get_unified_context_processor()
            context_result = context_processor.process_character_generation_context(
                basic_bio=request.basicBio,
                existing_characters=request.existingCharacters,
                compose_phase=request.compose_phase,
                phase_context=request.phase_context,
                structured_context=request.structured_context,
                context_mode="structured",
                context_processing_config=request.context_processing_config)

            # Log context processing results
            if context_result.optimization_applied:
                logger.info(
                    f"Character generation context processing applied ({
                        context_result.processing_mode} mode): " f"{
                        context_result.total_tokens} tokens, " f"compression ratio: {
                        context_result.compression_ratio:.2f}")
            else:
                logger.debug(
                    f"No character generation context optimization needed ({
                        context_result.processing_mode} mode): " f"{
                        context_result.total_tokens} tokens")

            # Phase 2: Analyzing
            yield f"data: {json.dumps({'type': 'status', 'phase': 'analyzing', 'message': 'Analyzing character bio and existing characters...', 'progress': 40})}\n\n"

            # Phase 3: Generating
            yield f"data: {json.dumps({'type': 'status', 'phase': 'generating', 'message': 'Generating detailed character information...', 'progress': 70})}\n\n"

            # Prepare JSON instruction and messages
            json_instruction = '''

Generate complete character details in JSON format:
{
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
}'''

            user_message = context_result.user_message + json_instruction
            messages = [
                {"role": "system", "content": context_result.system_prompt.strip()},
                {"role": "user", "content": user_message.strip()}
            ]

            # Collect generated text from streaming
            response_text = ""
            for token in llm.chat_completion_stream(
                    messages,
                    max_tokens=settings.ENDPOINT_GENERATE_CHARACTER_DETAILS_MAX_TOKENS,
                    temperature=settings.ENDPOINT_GENERATE_CHARACTER_DETAILS_TEMPERATURE):
                response_text += token

            # Phase 4: Parsing
            yield f"data: {json.dumps({'type': 'status', 'phase': 'parsing', 'message': 'Processing character details...', 'progress': 90})}\n\n"

            parsed = parse_json_response(response_text)

            if parsed and 'name' in parsed:
                result = GenerateCharacterDetailsResponse(
                    name=parsed.get('name', 'Character'),
                    sex=parsed.get('sex', ''),
                    gender=parsed.get('gender', ''),
                    sexualPreference=parsed.get('sexualPreference', ''),
                    age=int(
                        parsed.get(
                            'age',
                            30)) if str(
                        parsed.get(
                            'age',
                            '')).isdigit() else 30,
                    physicalAppearance=parsed.get('physicalAppearance', ''),
                    usualClothing=parsed.get('usualClothing', ''),
                    personality=parsed.get('personality', ''),
                    motivations=parsed.get('motivations', ''),
                    fears=parsed.get('fears', ''),
                    relationships=parsed.get('relationships', ''),
                    context_metadata=context_result.context_metadata
                )
            else:
                logger.warning(
                    "Failed to parse character JSON, using fallback")
                # Extract name from basic bio or generate one
                name_match = re.search(
                    r'([A-Z][a-z]+ [A-Z][a-z]+)', request.basicBio)
                name = name_match.group(1) if name_match else "Alex Morgan"

                result = GenerateCharacterDetailsResponse(
                    name=name,
                    sex="",
                    gender="",
                    sexualPreference="",
                    age=30,
                    physicalAppearance=f"A person matching the description: {
                        request.basicBio[
                            :100]}",
                    usualClothing="Practical, comfortable clothing",
                    personality=request.basicBio,
                    motivations="To achieve their goals",
                    fears="Failure and loss",
                    relationships="Building connections with others",
                    context_metadata=context_result.context_metadata
                )

            yield f"data: {json.dumps({'type': 'result', 'data': result.model_dump(), 'status': 'complete'})}\n\n"

        except Exception as e:
            logger.error(f"Error in generate_character_details: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate_with_updates(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
