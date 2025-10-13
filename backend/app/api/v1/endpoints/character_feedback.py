"""
Character feedback endpoint for Writer Assistant.
"""
from fastapi import APIRouter, HTTPException
from app.models.generation_models import (
    CharacterFeedbackRequest,
    CharacterFeedbackResponse,
    CharacterFeedback
)
from app.services.llm_inference import get_llm
from app.api.v1.endpoints.shared_utils import parse_json_response, parse_list_response
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/character-feedback", response_model=CharacterFeedbackResponse)
async def character_feedback(request: CharacterFeedbackRequest):
    """Generate character feedback for a plot point using LLM."""
    llm = get_llm()
    if not llm:
        raise HTTPException(status_code=503, detail="LLM not initialized. Start server with --model-path")

    try:
        character_name = request.character.name or "Character"

        system_prompt = f"""{request.systemPrompts.mainPrefix}

You are embodying {character_name}, a character with the following traits:
- Bio: {request.character.basicBio}
- Personality: {request.character.personality}
- Motivations: {request.character.motivations}
- Fears: {request.character.fears}

{request.systemPrompts.mainSuffix}"""

        user_message = f"""Context:
- World: {request.worldbuilding}
- Story: {request.storySummary}
- Current situation: {request.plotPoint}

Respond in JSON format with exactly these keys:
{{
  "actions": ["3-5 physical actions {character_name} takes"],
  "dialog": ["3-5 things {character_name} might say"],
  "physicalSensations": ["3-5 physical sensations {character_name} experiences"],
  "emotions": ["3-5 emotions {character_name} feels"],
  "internalMonologue": ["3-5 thoughts in {character_name}'s mind"]
}}"""

        messages = [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_message.strip()}
        ]

        response_text = llm.chat_completion(messages, max_tokens=800, temperature=0.8)
        parsed = parse_json_response(response_text)

        if parsed and all(k in parsed for k in ['actions', 'dialog', 'physicalSensations', 'emotions', 'internalMonologue']):
            feedback = CharacterFeedback(**parsed)
        else:
            logger.warning("Failed to parse JSON, using text fallback")
            lines = parse_list_response(response_text, "all")
            feedback = CharacterFeedback(
                actions=lines[0:3] if len(lines) > 0 else [f"{character_name} responds"],
                dialog=lines[3:6] if len(lines) > 3 else ["..."],
                physicalSensations=lines[6:9] if len(lines) > 6 else ["Feeling tense"],
                emotions=lines[9:12] if len(lines) > 9 else ["Anxious"],
                internalMonologue=lines[12:15] if len(lines) > 12 else ["What now?"]
            )

        return CharacterFeedbackResponse(characterName=character_name, feedback=feedback)
    except Exception as e:
        logger.error(f"Error in character_feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating character feedback: {str(e)}")
