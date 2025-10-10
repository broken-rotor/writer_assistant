"""
AI Generation endpoints for Writer Assistant.
These provide mock responses for all AI generation functionality.
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

router = APIRouter()


@router.post("/character-feedback", response_model=CharacterFeedbackResponse)
async def character_feedback(request: CharacterFeedbackRequest):
    """
    Generate character feedback for a plot point.
    Returns mock data with character actions, dialog, sensations, emotions, and thoughts.
    """
    try:
        # Mock response based on character and plot point
        character_name = request.character.name or "Character"

        mock_feedback = CharacterFeedback(
            actions=[
                f"{character_name} carefully considers the situation",
                f"{character_name} takes a decisive step forward",
                f"{character_name} reaches out with determination"
            ],
            dialog=[
                "This changes everything we thought we knew",
                "I need to understand what this means",
                "We can't ignore this any longer"
            ],
            physicalSensations=[
                "Heart racing with anticipation",
                "Hands trembling slightly",
                "A chill running down the spine"
            ],
            emotions=[
                "A mix of excitement and apprehension",
                "Growing determination",
                "Underlying fear of the unknown"
            ],
            internalMonologue=[
                "This is the moment everything changes",
                "Can I trust what I'm seeing?",
                "There's no turning back now"
            ]
        )

        return CharacterFeedbackResponse(
            characterName=character_name,
            feedback=mock_feedback
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating character feedback: {str(e)}")


@router.post("/rater-feedback", response_model=RaterFeedbackResponse)
async def rater_feedback(request: RaterFeedbackRequest):
    """
    Generate rater feedback for a plot point.
    Returns mock data with opinion and suggestions.
    """
    try:
        # Extract rater name from prompt or use default
        rater_name = "Rater"

        mock_feedback = RaterFeedback(
            opinion="The plot point is engaging and moves the story forward effectively. The incorporation of character feedback adds depth and authenticity. There's good potential for tension and character development here.",
            suggestions=[
                "Consider adding more sensory details to ground the reader in the scene",
                "The emotional stakes could be heightened by emphasizing what the character stands to lose",
                "Think about how this moment connects to the overall story arc and foreshadow future events",
                "Ensure the pacing allows the reader to fully experience this pivotal moment"
            ]
        )

        return RaterFeedbackResponse(
            raterName=rater_name,
            feedback=mock_feedback
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating rater feedback: {str(e)}")


@router.post("/generate-chapter", response_model=GenerateChapterResponse)
async def generate_chapter(request: GenerateChapterRequest):
    """
    Generate a complete chapter based on plot point and incorporated feedback.
    Returns mock chapter text.
    """
    try:
        # Generate mock chapter incorporating the plot point
        plot_summary = request.plotPoint[:100] if request.plotPoint else "the story continues"

        mock_chapter = f"""The air was thick with anticipation as the moment arrived. {plot_summary}...

Everything had led to this point. The characters gathered their courage, each bringing their own perspective to bear on the situation at hand.

The tension mounted as decisions were made, words were spoken, and actions were taken that would ripple through the remainder of the story. Each person present felt the weight of the moment differently, their unique backgrounds and motivations coloring their experience.

As events unfolded, the true nature of the situation became clearer. What had seemed simple on the surface revealed layers of complexity that none had fully anticipated. The characters would need to draw on all their strengths to navigate what came next.

By the end of it all, nothing would be quite the same. The foundations had shifted, relationships had evolved, and new paths forward had opened up—even as others closed forever.

The chapter concluded with a sense of both resolution and anticipation, answering some questions while raising others that would drive the story forward into the chapters yet to come."""

        word_count = len(mock_chapter.split())

        return GenerateChapterResponse(
            chapterText=mock_chapter,
            wordCount=word_count,
            metadata={
                "generatedAt": datetime.now(UTC).isoformat(),
                "plotPoint": request.plotPoint,
                "feedbackItemsIncorporated": len(request.incorporatedFeedback)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating chapter: {str(e)}")


@router.post("/modify-chapter", response_model=ModifyChapterResponse)
async def modify_chapter(request: ModifyChapterRequest):
    """
    Modify an existing chapter based on user's requested changes.
    Returns mock modified chapter text.
    """
    try:
        # Mock modification - in reality would use AI to apply user's changes
        current_text = request.currentChapter
        user_changes = request.userRequest

        modified_chapter = f"""[Modified based on: {user_changes}]

{current_text}

[Additional content or modifications would be applied here based on the user's specific request. The AI would carefully integrate the requested changes while maintaining consistency with the existing chapter structure and story context.]"""

        word_count = len(modified_chapter.split())

        return ModifyChapterResponse(
            modifiedChapter=modified_chapter,
            wordCount=word_count,
            changesSummary=f"Applied modifications based on user request: {user_changes[:100]}..."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error modifying chapter: {str(e)}")


@router.post("/editor-review", response_model=EditorReviewResponse)
async def editor_review(request: EditorReviewRequest):
    """
    Generate editor review suggestions for a chapter.
    Returns mock editor feedback.
    """
    try:
        mock_suggestions = [
            EditorSuggestion(
                issue="Opening lacks sensory detail",
                suggestion="Add descriptions of sounds, smells, or tactile sensations to immerse the reader in the scene from the first sentence",
                priority="high"
            ),
            EditorSuggestion(
                issue="Dialogue could be more distinctive",
                suggestion="Ensure each character's voice is unique by varying speech patterns, vocabulary, and sentence structure",
                priority="medium"
            ),
            EditorSuggestion(
                issue="Pacing in the middle section",
                suggestion="Consider tightening the middle section to maintain momentum and reader engagement",
                priority="medium"
            ),
            EditorSuggestion(
                issue="Emotional reactions could be stronger",
                suggestion="Show the physical manifestations of emotions rather than just naming them",
                priority="high"
            ),
            EditorSuggestion(
                issue="Transition between scenes",
                suggestion="Add a clear transition or scene break to help readers follow the shift in time or location",
                priority="low"
            )
        ]

        return EditorReviewResponse(suggestions=mock_suggestions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating editor review: {str(e)}")


@router.post("/flesh-out", response_model=FleshOutResponse)
async def flesh_out(request: FleshOutRequest):
    """
    Flesh out/expand brief text (plot points, worldbuilding, etc).
    Returns mock expanded text.
    """
    try:
        original = request.textToFleshOut
        context_info = request.context

        # Mock expansion
        fleshed_out = f"""{original}

[Expanded with additional detail based on {context_info}:]

The situation unfolds with greater complexity than initially apparent. Multiple layers of meaning and consequence emerge as we examine the details more closely. The characters involved each bring their own histories, motivations, and perspectives that color how events transpire.

The setting itself plays a crucial role, with environmental factors and atmospheric elements contributing to the overall mood and impact of what occurs. Time pressure, available resources, and unexpected complications all influence the trajectory of events.

Key relationships are tested and evolve through this experience, with alliances forming or fracturing based on how individuals respond to the challenges they face. The choices made in these moments will echo through the remainder of the story, setting up conflicts and resolutions yet to come."""

        return FleshOutResponse(
            fleshedOutText=fleshed_out,
            originalText=original
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fleshing out text: {str(e)}")


@router.post("/generate-character-details", response_model=GenerateCharacterDetailsResponse)
async def generate_character_details(request: GenerateCharacterDetailsRequest):
    """
    Generate detailed character information from a basic bio.
    Returns mock character details.
    """
    try:
        basic_bio = request.basicBio

        # Mock character generation based on bio
        mock_character = GenerateCharacterDetailsResponse(
            name="Alex Morrison",
            sex="Female",
            gender="Female",
            sexualPreference="Bisexual",
            age=34,
            physicalAppearance="Tall and athletic with shoulder-length dark hair often pulled back in a practical ponytail. Sharp hazel eyes that miss nothing. A small scar above her left eyebrow from a childhood accident. Moves with confidence and purpose.",
            usualClothing="Prefers practical clothing - dark jeans, comfortable boots, and layers she can move in. Often wears a worn leather jacket that belonged to her father. Keeps things simple and functional.",
            personality="Direct and analytical, Alex doesn't waste time on small talk. She's fiercely independent and sometimes struggles to ask for help. Beneath her tough exterior lies a strong sense of justice and unexpected empathy for those society has overlooked. Can be stubborn but also deeply loyal to those who earn her trust.",
            motivations="Driven by a need to uncover the truth and bring justice to those without a voice. Haunted by an unsolved case from her past that cost someone close to her their life. Seeks redemption through her work while maintaining her independence and integrity.",
            fears="Fears being too late to help someone in need, repeating past mistakes. Afraid of becoming emotionally vulnerable and being let down. Worries that her independence might be pushing people away when she actually needs connection.",
            relationships=f"Has complicated relationships with existing characters. {' '.join([f'Knows {char.get('name', 'someone')} from previous encounters.' for char in request.existingCharacters[:2]])} Building trust with new people is a slow process for her."
        )

        return mock_character
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating character details: {str(e)}")
