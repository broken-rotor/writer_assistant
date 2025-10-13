"""
Generate character details endpoint for Writer Assistant.
"""
from fastapi import APIRouter, HTTPException
from app.models.generation_models import (
    GenerateCharacterDetailsRequest,
    GenerateCharacterDetailsResponse
)
from app.services.llm_inference import get_llm
from app.api.v1.endpoints.shared_utils import parse_json_response
import logging
import re

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/generate-character-details", response_model=GenerateCharacterDetailsResponse)
async def generate_character_details(request: GenerateCharacterDetailsRequest):
    """Generate detailed character information using LLM."""
    llm = get_llm()
    if not llm:
        raise HTTPException(status_code=503, detail="LLM not initialized. Start server with --model-path")

    try:
        existing_chars = "\n".join([
            f"- {c.get('name', 'Unknown')}: {c.get('basicBio', '')}"
            for c in request.existingCharacters[:3]
        ])

        system_prompt = f"""{request.systemPrompts.mainPrefix}

Create detailed characters for stories with rich personalities and backgrounds.

{request.systemPrompts.mainSuffix}"""

        user_message = f"""Story context:
- World: {request.worldbuilding}
- Story: {request.storySummary}

Character concept: {request.basicBio}

Existing characters:
{existing_chars}

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

        messages = [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_message.strip()}
        ]

        response_text = llm.chat_completion(messages, max_tokens=1000, temperature=0.7)
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
                relationships=parsed.get('relationships', '')
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
                relationships="Building connections with others"
            )
    except Exception as e:
        logger.error(f"Error in generate_character_details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating character details: {str(e)}")
