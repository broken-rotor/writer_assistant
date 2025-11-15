"""
Generate character details endpoint for Writer Assistant.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.generation_models import (
    GenerateCharacterDetailsRequest,
    GenerateCharacterDetailsResponse,
    CharacterInfo
)
from app.services.llm_inference import get_llm
from app.services.context_builder import ContextBuilder
from app.api.v1.endpoints.shared_utils import parse_json_response, get_character_details

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
            character_details = get_character_details(request.request_context, request.character_name)

            # Phase 1: Context Processing
            yield f"data: {json.dumps({'type': 'status', 'phase': 'context_processing', 'message': 'Processing character context...', 'progress': 20})}\n\n"

            context_builder = ContextBuilder(request.request_context)
            context_builder.add_system_prompt(request.request_context.configuration.system_prompts.assistant_prompt)
            context_builder.add_worldbuilding()
            context_builder.add_characters(tag='OTHER_CHARACTERS', exclude_characters={request.character_name})
            context_builder.add_characters(tag='CHARACTER_TO_GENERATE', include_characters={request.character_name})
            agent_instruction = """Generate complete character details for {request.character_name} based on CHARACTER_TO_GENERATE. Respond in JSON format:
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
}"""
            context_builder.add_agent_instruction(agent_instruction)

            # Phase 2: Generating
            yield f"data: {json.dumps({'type': 'status', 'phase': 'generating', 'message': 'Generating detailed character information...', 'progress': 40})}\n\n"

            # Collect generated text from streaming
            response_text = ""
            for token in llm.chat_completion_stream(
                    context_builder.build_messages(),
                    max_tokens=settings.ENDPOINT_GENERATE_CHARACTER_DETAILS_MAX_TOKENS,
                    temperature=settings.ENDPOINT_GENERATE_CHARACTER_DETAILS_TEMPERATURE,
                    json_schema_class=CharacterInfo):
                response_text += token

            # Phase 3: Parsing
            yield f"data: {json.dumps({'type': 'status', 'phase': 'parsing', 'message': 'Processing character details...', 'progress': 90})}\n\n"

            parsed = parse_json_response(response_text)
            if parsed and 'name' in parsed:
                basicBio = character_details.basic_bio or parsed.basicBio
                character_info = CharacterInfo(
                    name=parsed.get('name', 'Character'),
                    basicBio=basicBio,
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
                    relationships=parsed.get('relationships', '')
                )
                result = GenerateCharacterDetailsResponse(
                    character_info=character_info)
            else:
                logger.error(
                    "Failed to parse character JSON, using fallback")
                raise ValueError('Error parsing JSON output from LLM')

            yield f"data: {json.dumps({'type': 'result', 'data': result.model_dump(), 'status': 'complete'})}\n\n"

        except Exception as e:
            logger.error("Error in generate_character_details:", e)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate_with_updates(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
