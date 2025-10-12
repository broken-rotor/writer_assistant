"""
AI Generation endpoints for Writer Assistant.
Uses local LLM via llama.cpp for text generation.
"""
from fastapi import APIRouter, HTTPException
from app.models.generation_models import (
    CharacterFeedbackRequest,
    CharacterFeedbackResponse,
    CharacterFeedback,
    RaterFeedbackRequest,
    RaterFeedbackResponse,
    RaterFeedback,
    GenerateChapterRequest,
    GenerateChapterResponse,
    ModifyChapterRequest,
    ModifyChapterResponse,
    EditorReviewRequest,
    EditorReviewResponse,
    EditorSuggestion,
    FleshOutRequest,
    FleshOutResponse,
    GenerateCharacterDetailsRequest,
    GenerateCharacterDetailsResponse
)
from datetime import datetime, UTC
from app.services.llm_inference import get_llm
import json
import re
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def parse_json_response(text: str) -> dict:
    """Try to extract JSON from LLM response"""
    # Try to find JSON in code blocks
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find raw JSON
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def parse_list_response(text: str, key: str) -> list:
    """Extract a list from LLM response"""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    # Filter out lines that are just section headers
    return [line.lstrip('- ').lstrip('* ').lstrip('1234567890. ')
            for line in lines if line and not line.endswith(':')][:10]


@router.post("/character-feedback", response_model=CharacterFeedbackResponse)
async def character_feedback(request: CharacterFeedbackRequest):
    """Generate character feedback for a plot point using LLM."""
    llm = get_llm()
    if not llm:
        raise HTTPException(status_code=503, detail="LLM not initialized. Start server with --model-path")

    try:
        character_name = request.character.name or "Character"

        prompt = f"""{request.systemPrompts.mainPrefix}

You are embodying {character_name}, a character with the following traits:
- Bio: {request.character.basicBio}
- Personality: {request.character.personality}
- Motivations: {request.character.motivations}
- Fears: {request.character.fears}

Context:
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
}}

{request.systemPrompts.mainSuffix}"""

        response_text = llm.generate(prompt, max_tokens=800, temperature=0.8)
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


@router.post("/rater-feedback", response_model=RaterFeedbackResponse)
async def rater_feedback(request: RaterFeedbackRequest):
    """Generate rater feedback for a plot point using LLM."""
    llm = get_llm()
    if not llm:
        raise HTTPException(status_code=503, detail="LLM not initialized. Start server with --model-path")

    try:
        prompt = f"""{request.systemPrompts.mainPrefix}

{request.raterPrompt}

Evaluate this plot point:
- World: {request.worldbuilding}
- Story: {request.storySummary}
- Plot point: {request.plotPoint}

Provide feedback in JSON format:
{{
  "opinion": "Your overall opinion (2-3 sentences)",
  "suggestions": ["4-6 specific suggestions for improvement"]
}}

{request.systemPrompts.mainSuffix}"""

        response_text = llm.generate(prompt, max_tokens=600, temperature=0.7)
        parsed = parse_json_response(response_text)

        if parsed and 'opinion' in parsed and 'suggestions' in parsed:
            feedback = RaterFeedback(**parsed)
        else:
            logger.warning("Failed to parse JSON, using text fallback")
            lines = parse_list_response(response_text, "all")
            feedback = RaterFeedback(
                opinion=lines[0] if lines else "The plot point has potential.",
                suggestions=lines[1:5] if len(lines) > 1 else ["Consider adding more detail"]
            )

        return RaterFeedbackResponse(raterName="Rater", feedback=feedback)
    except Exception as e:
        logger.error(f"Error in rater_feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating rater feedback: {str(e)}")


@router.post("/generate-chapter", response_model=GenerateChapterResponse)
async def generate_chapter(request: GenerateChapterRequest):
    """Generate a complete chapter using LLM."""
    llm = get_llm()
    if not llm:
        raise HTTPException(status_code=503, detail="LLM not initialized. Start server with --model-path")

    try:
        # Build character context
        char_context = "\n".join([
            f"- {c.name}: {c.basicBio} (Personality: {c.personality})"
            for c in request.characters[:3]  # Limit to avoid context overflow
        ])

        # Build feedback context
        feedback_context = ""
        if request.incorporatedFeedback:
            feedback_items = [f"- {f.content}" for f in request.incorporatedFeedback[:5]]
            feedback_context = "Incorporated feedback:\n" + "\n".join(feedback_items)

        prompt = f"""{request.systemPrompts.mainPrefix}
{request.systemPrompts.assistantPrompt or ''}

Write a chapter for this story:

World: {request.worldbuilding}
Story: {request.storySummary}

Characters:
{char_context}

Plot point for this chapter: {request.plotPoint}

{feedback_context}

Write an engaging chapter (800-1500 words) that brings this plot point to life with vivid prose, authentic dialogue, and character development.

{request.systemPrompts.mainSuffix}"""

        response_text = llm.generate(prompt, max_tokens=2000, temperature=0.8)
        word_count = len(response_text.split())

        return GenerateChapterResponse(
            chapterText=response_text.strip(),
            wordCount=word_count,
            metadata={
                "generatedAt": datetime.now(UTC).isoformat(),
                "plotPoint": request.plotPoint,
                "feedbackItemsIncorporated": len(request.incorporatedFeedback)
            }
        )
    except Exception as e:
        logger.error(f"Error in generate_chapter: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating chapter: {str(e)}")


@router.post("/modify-chapter", response_model=ModifyChapterResponse)
async def modify_chapter(request: ModifyChapterRequest):
    """Modify an existing chapter using LLM."""
    llm = get_llm()
    if not llm:
        raise HTTPException(status_code=503, detail="LLM not initialized. Start server with --model-path")

    try:
        prompt = f"""{request.systemPrompts.mainPrefix}
{request.systemPrompts.assistantPrompt or ''}

You are editing a chapter from a story.

Story context:
- World: {request.worldbuilding}
- Story: {request.storySummary}

Current chapter:
{request.currentChapter}

User's modification request: {request.userRequest}

Rewrite the chapter incorporating the requested changes while maintaining consistency with the story.

{request.systemPrompts.mainSuffix}"""

        response_text = llm.generate(prompt, max_tokens=2500, temperature=0.7)
        word_count = len(response_text.split())

        return ModifyChapterResponse(
            modifiedChapter=response_text.strip(),
            wordCount=word_count,
            changesSummary=f"Modified based on: {request.userRequest[:150]}"
        )
    except Exception as e:
        logger.error(f"Error in modify_chapter: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error modifying chapter: {str(e)}")


@router.post("/editor-review", response_model=EditorReviewResponse)
async def editor_review(request: EditorReviewRequest):
    """Generate editor review using LLM."""
    llm = get_llm()
    if not llm:
        raise HTTPException(status_code=503, detail="LLM not initialized. Start server with --model-path")

    try:
        prompt = f"""{request.systemPrompts.mainPrefix}
{request.systemPrompts.editorPrompt or 'You are an expert editor.'}

Review this chapter and provide specific suggestions for improvement.

Story context:
- World: {request.worldbuilding}
- Story: {request.storySummary}

Chapter to review:
{request.chapterToReview}

Provide 4-6 suggestions in JSON format:
{{
  "suggestions": [
    {{"issue": "brief issue description", "suggestion": "specific improvement suggestion", "priority": "high|medium|low"}}
  ]
}}

{request.systemPrompts.mainSuffix}"""

        response_text = llm.generate(prompt, max_tokens=800, temperature=0.6)
        parsed = parse_json_response(response_text)

        suggestions = []
        if parsed and 'suggestions' in parsed and isinstance(parsed['suggestions'], list):
            for s in parsed['suggestions']:
                if isinstance(s, dict) and 'issue' in s and 'suggestion' in s:
                    suggestions.append(EditorSuggestion(
                        issue=s['issue'],
                        suggestion=s['suggestion'],
                        priority=s.get('priority', 'medium')
                    ))

        if not suggestions:
            logger.warning("Failed to parse suggestions, using text fallback")
            lines = parse_list_response(response_text, "all")
            for i in range(0, min(len(lines), 6), 2):
                if i + 1 < len(lines):
                    suggestions.append(EditorSuggestion(
                        issue=lines[i][:100],
                        suggestion=lines[i + 1][:200],
                        priority="medium"
                    ))

        if not suggestions:
            suggestions.append(EditorSuggestion(
                issue="General feedback",
                suggestion="The chapter shows promise and could be enhanced with more specific details.",
                priority="medium"
            ))

        return EditorReviewResponse(suggestions=suggestions)
    except Exception as e:
        logger.error(f"Error in editor_review: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating editor review: {str(e)}")


@router.post("/flesh-out", response_model=FleshOutResponse)
async def flesh_out(request: FleshOutRequest):
    """Flesh out/expand brief text using LLM."""
    llm = get_llm()
    if not llm:
        raise HTTPException(status_code=503, detail="LLM not initialized. Start server with --model-path")

    try:
        prompt = f"""{request.systemPrompts.mainPrefix}

Expand and flesh out the following text with rich detail.

Story context:
- World: {request.worldbuilding}
- Story: {request.storySummary}
- Context type: {request.context}

Text to expand: {request.textToFleshOut}

Provide a detailed, atmospheric expansion (200-400 words) that adds depth, sensory details, and narrative richness.

{request.systemPrompts.mainSuffix}"""

        response_text = llm.generate(prompt, max_tokens=600, temperature=0.8)

        return FleshOutResponse(
            fleshedOutText=response_text.strip(),
            originalText=request.textToFleshOut
        )
    except Exception as e:
        logger.error(f"Error in flesh_out: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fleshing out text: {str(e)}")


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

        prompt = f"""{request.systemPrompts.mainPrefix}

Create a detailed character for this story:

Story context:
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
}}

{request.systemPrompts.mainSuffix}"""

        response_text = llm.generate(prompt, max_tokens=1000, temperature=0.7)
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
