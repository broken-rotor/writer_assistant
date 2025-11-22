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
from app.models.streaming_models import (
    StreamingStatusEvent,
    StreamingResultEvent,
    StreamingErrorEvent
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
            status_event = StreamingStatusEvent(
                phase='context_processing',
                message='Processing character context...',
                progress=20
            )
            yield f"data: {status_event.model_dump_json()}\n\n"

            context_builder = ContextBuilder(request.request_context, llm)
            context_builder.add_system_prompt(request.request_context.configuration.system_prompts.assistant_prompt)
            context_builder.add_worldbuilding()
            context_builder.add_characters(tag='OTHER_CHARACTERS', exclude_characters={request.character_name})
            context_builder.add_characters(tag='CHARACTER_TO_GENERATE', include_characters={request.character_name})
            
            agent_instruction = f"""Generate comprehensive, authentic character details for {request.character_name} based on the information provided in CHARACTER_TO_GENERATE.

<CHARACTER_DEVELOPMENT_PRINCIPLES>
1. **Consistency First:** Build on existing character information - expand and detail, don't contradict
2. **Key Elements:** Ensure key elements in the bio are reflected in the detailed descriptions
3. **Depth Over Breadth:** Create a few rich, specific details rather than many shallow ones
4. **Internal Logic:** Ensure all aspects of the character fit together coherently
5. **Story Integration:** Consider how this character fits into the world and story context
6. **Authenticity:** Create a believable, three-dimensional person with strengths and flaws
</CHARACTER_DEVELOPMENT_PRINCIPLES>

<FIELD_GUIDANCE>
- **Physical Appearance:** Include specific, distinctive details (not just generic attractive/average). Consider how appearance relates to background and personality.
- **Clothing Style:** Reflect personality, occupation, culture, and practical needs. Be specific about colors, fabrics, style.
- **Personality:** Go beyond adjectives - include behavioral patterns, quirks, contradictions, and how they interact with others.
- **Motivations:** Identify core driving forces. What do they want more than anything? Why?
- **Fears:** Include both surface fears and deeper psychological anxieties. How do these shape behavior?
- **Relationships:** Consider relationship patterns, attachment style, and how they've shaped this character, and relations to other characters in the story.
</FIELD_GUIDANCE>

<CONTEXT_AWARENESS>
- Reference other characters in OTHER_CHARACTERS when describing relationships
- Align with the world's culture, technology level, and social norms
- Ensure age and background fit the story timeline
</CONTEXT_AWARENESS>

<OUTPUT_FORMAT>
Respond ONLY in JSON format with these exact fields (and no extra escaping):
{{
  "name": "character name",
  "sex": "Male/Female/Other",
  "gender": "gender identity",
  "sexualPreference": "sexual orientation",
  "age": numeric age,
  "physicalAppearance": "detailed, specific physical description with distinctive features",
  "usualClothing": "specific clothing style with details on colors, fabrics, and why they dress this way",
  "personality": "rich personality description including traits, patterns, quirks, contradictions, and behavioral tendencies",
  "motivations": "core driving forces with explanation of why these matter to the character",
  "fears": "fears and anxieties with insight into how these shape behavior",
  "relationships": "relationship patterns, attachment style, and how they typically interact with others, and relations to other characters in the story"
}}
</OUTPUT_FORMAT>
"""
            context_builder.add_agent_instruction(agent_instruction)

            # Phase 2: Generating
            status_event = StreamingStatusEvent(
                phase='generating',
                message='Generating detailed character information...',
                progress=40
            )
            yield f"data: {status_event.model_dump_json()}\n\n"

            # Collect generated text from streaming
            response_text = ""
            for token in llm.chat_completion_stream(
                    context_builder.build_messages(),
                    max_tokens=settings.ENDPOINT_GENERATE_CHARACTER_DETAILS_MAX_TOKENS,
                    temperature=settings.ENDPOINT_GENERATE_CHARACTER_DETAILS_TEMPERATURE,
                    json_schema_class=CharacterInfo):
                response_text += token

            # Phase 3: Parsing
            status_event = StreamingStatusEvent(
                phase='parsing',
                message='Processing character details...',
                progress=90
            )
            yield f"data: {status_event.model_dump_json()}\n\n"

            parsed = parse_json_response(response_text)
            if parsed and 'name' in parsed:
                basicBio = character_details.basic_bio or parsed.basicBio
                character_info = CharacterInfo(
                    name=parsed.get('name', 'Character'),
                    basicBio=basicBio,
                    sex=parsed.get('sex', ''),
                    gender=parsed.get('gender', ''),
                    sexualPreference=parsed.get('sexualPreference', ''),
                    age=int(parsed.get('age', 30)) if str(parsed.get('age','')).isdigit() else 30,
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
                logger.error("Failed to parse character JSON")
                raise ValueError('Error parsing JSON output from LLM')

            result_event = StreamingResultEvent(data=result.model_dump())
            yield f"data: {result_event.model_dump_json()}\n\n"

        except Exception as e:
            logger.exception("Error in generate_character_details")
            error_event = StreamingErrorEvent(message=str(e))
            yield f"data: {error_event.model_dump_json()}\n\n"

    return StreamingResponse(
        generate_with_updates(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
