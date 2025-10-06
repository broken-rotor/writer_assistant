from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

app = FastAPI(
    title="Writer Assistant API",
    description="Stateless API for multi-agent collaborative storytelling",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Angular dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Response models
class ApiResponse(BaseModel):
    success: bool
    data: Any
    metadata: Optional[Dict[str, Any]] = None
    errors: Optional[Any] = None

# Request models for story generation
class StoryInput(BaseModel):
    theme: str
    style: str
    length: str
    focusAreas: List[str]

class UserInput(BaseModel):
    type: str
    content: str
    expansion_request: str

class UserPreferences(BaseModel):
    style_profile: str
    length_preference: str
    focus_areas: List[str]

class StoryContext(BaseModel):
    existing_content: Optional[Any] = None
    characters: List[Dict[str, Any]] = []
    previous_drafts: List[Dict[str, Any]] = []
    user_feedback_history: List[Dict[str, Any]] = []

class GenerateDraftRequest(BaseModel):
    user_input: UserInput
    user_preferences: UserPreferences
    story_context: StoryContext

# Mock response generators
def generate_mock_story_draft(story_input: StoryInput) -> Dict[str, Any]:
    """Generate a mock story draft based on input"""
    return {
        "title": f"The {story_input.theme.split()[0]} Mystery",
        "outline": [
            f"Opening scene establishing the {story_input.theme.lower()} theme",
            "Introduction of main character with compelling motivation",
            "First major plot point that drives the story forward",
            "Character development and world building",
            "Rising action with increasing tension",
            "Climactic confrontation or revelation",
            "Resolution that ties back to the opening theme"
        ],
        "characters": [
            {
                "id": "char_001",
                "name": "Alex Morgan",
                "role": "protagonist",
                "personality": "Determined, analytical, with hidden vulnerabilities",
                "background": f"Someone deeply connected to the {story_input.theme.lower()} at the story's heart",
                "currentState": {
                    "currentKnowledge": "Limited understanding of the full situation",
                    "emotionalState": "Curious but apprehensive"
                }
            },
            {
                "id": "char_002",
                "name": "Dr. Elena Vasquez",
                "role": "mentor/ally",
                "personality": "Wise, experienced, but harboring secrets",
                "background": "Expert in the field relevant to the story's central mystery",
                "currentState": {
                    "currentKnowledge": "Much more than they initially reveal",
                    "emotionalState": "Protective yet conflicted"
                }
            }
        ],
        "themes": [
            story_input.theme,
            "Identity and self-discovery",
            "The nature of truth",
            "Courage in the face of uncertainty"
        ]
    }

def generate_mock_character_dialog(character_id: str, message: str) -> Dict[str, Any]:
    """Generate mock character dialog response"""
    responses = {
        "char_001": {
            "response": f"I've been thinking about what you said: '{message}'. It makes me wonder if we're missing something important here. My instincts tell me there's more beneath the surface.",
            "emotionalState": "thoughtful",
            "internalThoughts": "This person seems to understand the situation better than I initially thought. I should be more open about my concerns."
        },
        "char_002": {
            "response": f"Your question about '{message}' touches on something I've been researching for years. The answer isn't simple, but I think you're ready to hear the truth.",
            "emotionalState": "serious",
            "internalThoughts": "It's time to reveal more. They've proven they can handle the complexity of this situation."
        }
    }
    return responses.get(character_id, {
        "response": f"That's an interesting perspective on '{message}'. Let me share what I know about this situation.",
        "emotionalState": "neutral",
        "internalThoughts": "I need to be careful about how much I reveal right now."
    })

def generate_mock_feedback(content: Any, agents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate mock feedback from agents"""
    feedback_data = []

    for agent in agents:
        if agent["id"] == "character_consistency":
            feedback_data.append({
                "agentId": agent["id"],
                "agentName": agent["name"],
                "score": 8.5,
                "strengths": [
                    "Characters maintain distinct voices throughout",
                    "Personality traits are consistent with established backgrounds",
                    "Character development feels natural and earned"
                ],
                "concerns": [
                    "Some dialogue could be more distinctive between characters",
                    "Minor inconsistency in character knowledge levels"
                ],
                "suggestions": [
                    {
                        "id": "suggestion_001",
                        "agentId": agent["id"],
                        "type": "improvement",
                        "content": "Consider adding more character-specific speech patterns to distinguish voices",
                        "priority": "medium",
                        "actionable": True,
                        "selected": False
                    }
                ],
                "priority": "medium",
                "timestamp": datetime.now()
            })
        elif agent["id"] == "narrative_flow":
            feedback_data.append({
                "agentId": agent["id"],
                "agentName": agent["name"],
                "score": 7.8,
                "strengths": [
                    "Good pacing in action sequences",
                    "Smooth transitions between scenes",
                    "Effective use of tension and release"
                ],
                "concerns": [
                    "Some exposition feels slightly forced",
                    "Pacing slows in the middle section"
                ],
                "suggestions": [
                    {
                        "id": "suggestion_002",
                        "agentId": agent["id"],
                        "type": "revision",
                        "content": "Break up exposition with more character interaction or action",
                        "priority": "high",
                        "actionable": True,
                        "selected": False
                    }
                ],
                "priority": "high",
                "timestamp": datetime.now()
            })

    return feedback_data

# API Routes
@app.get("/")
async def root():
    return {"message": "Writer Assistant API", "status": "running"}

@app.get("/health")
async def health_check():
    return ApiResponse(
        success=True,
        data={"status": "healthy", "timestamp": datetime.now()},
        metadata={
            "timestamp": datetime.now().isoformat(),
            "requestId": "health_check",
            "processingTime": 1
        }
    )

@app.post("/api/generate/draft")
async def generate_draft(request: GenerateDraftRequest):
    """Generate a story draft based on user input"""
    try:
        # Extract story input from request
        story_input = StoryInput(
            theme=request.user_input.content,
            style=request.user_preferences.style_profile,
            length=request.user_preferences.length_preference,
            focusAreas=request.user_preferences.focus_areas
        )

        # Generate mock draft
        draft_data = generate_mock_story_draft(story_input)

        return ApiResponse(
            success=True,
            data=draft_data,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "requestId": f"draft_{int(datetime.now().timestamp())}",
                "processingTime": 2500
            }
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            data=None,
            errors=str(e)
        )

@app.post("/api/generate/revise-draft")
async def revise_draft(request: Dict[str, Any]):
    """Revise a story draft based on user feedback"""
    try:
        original_draft = request.get("original_draft", {})
        user_feedback = request.get("user_feedback", "")
        specific_changes = request.get("specific_changes", [])

        # Mock revision - modify the original draft
        revised_draft = original_draft.copy()
        revised_draft["title"] = f"{original_draft.get('title', 'Untitled')} (Revised)"

        # Add a note about the revision
        if "outline" in revised_draft:
            revised_draft["outline"].append(f"Revised based on feedback: {user_feedback[:50]}...")

        return ApiResponse(
            success=True,
            data=revised_draft,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "requestId": f"revision_{int(datetime.now().timestamp())}",
                "processingTime": 3200
            }
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            data=None,
            errors=str(e)
        )

@app.post("/api/character/dialog")
async def generate_character_dialog(request: Dict[str, Any]):
    """Generate character dialog response"""
    try:
        character_def = request.get("character_definition", {})
        user_message = request.get("user_message", "")
        character_id = character_def.get("character_id", "unknown")

        dialog_response = generate_mock_character_dialog(character_id, user_message)

        return ApiResponse(
            success=True,
            data=dialog_response,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "requestId": f"dialog_{int(datetime.now().timestamp())}",
                "processingTime": 1800
            }
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            data=None,
            errors=str(e)
        )

@app.post("/api/generate/detailed-content")
async def generate_detailed_content(request: Dict[str, Any]):
    """Generate detailed story content"""
    try:
        story_draft = request.get("story_draft", {})
        user_guidance = request.get("user_guidance", "")

        # Mock detailed content generation
        detailed_content = {
            "title": story_draft.get("title", "Generated Story"),
            "content": f"""
            The story begins with a sense of mystery and anticipation. {user_guidance[:100]}...

            As our protagonist navigates the challenges ahead, the themes of {', '.join(story_draft.get('themes', ['mystery', 'discovery']))} become increasingly apparent.

            The characters develop through meaningful interactions, with each scene building upon the previous to create a cohesive narrative that honors the original outline while incorporating the rich character perspectives that emerged through our collaborative process.

            The detailed story unfolds with careful attention to pacing, character development, and thematic resonance, creating an engaging reading experience that fulfills the promise of the initial concept while surprising both writer and reader with its depth and authenticity.
            """,
            "wordCount": 2500,
            "metadata": {
                "generatedAt": datetime.now().isoformat(),
                "guidanceIncorporated": user_guidance,
                "charactersIncluded": len(story_draft.get("characters", []))
            }
        }

        return ApiResponse(
            success=True,
            data=detailed_content,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "requestId": f"content_{int(datetime.now().timestamp())}",
                "processingTime": 5200
            }
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            data=None,
            errors=str(e)
        )

@app.post("/api/feedback/generate")
async def generate_feedback(request: Dict[str, Any]):
    """Generate feedback from selected agents"""
    try:
        content = request.get("content_to_review", {})
        story_context = request.get("story_context", {})
        feedback_agents = request.get("feedback_agents", [])

        feedback_data = generate_mock_feedback(content, feedback_agents)

        return ApiResponse(
            success=True,
            data=feedback_data,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "requestId": f"feedback_{int(datetime.now().timestamp())}",
                "processingTime": 4100
            }
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            data=None,
            errors=str(e)
        )

@app.post("/api/generate/apply-feedback")
async def apply_feedback(request: Dict[str, Any]):
    """Apply selected feedback to content"""
    try:
        original_content = request.get("original_content", {})
        selected_feedback = request.get("selected_feedback", [])

        # Mock feedback application
        refined_content = original_content.copy()
        refined_content["content"] = f"{original_content.get('content', '')} [Content refined based on {len(selected_feedback)} feedback items]"
        refined_content["improvements"] = [f"Applied: {fb.get('content', '')[:50]}..." for fb in selected_feedback]

        return ApiResponse(
            success=True,
            data=refined_content,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "requestId": f"apply_feedback_{int(datetime.now().timestamp())}",
                "processingTime": 3800
            }
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            data=None,
            errors=str(e)
        )

@app.get("/api/agents/types")
async def get_agent_types():
    """Get available agent types"""
    agent_types = [
        {
            "id": "writer",
            "name": "Writer Agent",
            "type": "generator",
            "description": "Main content generation agent"
        },
        {
            "id": "character_consistency",
            "name": "Character Consistency Rater",
            "type": "rater",
            "description": "Evaluates character consistency"
        },
        {
            "id": "narrative_flow",
            "name": "Narrative Flow Rater",
            "type": "rater",
            "description": "Analyzes story flow and pacing"
        }
    ]

    return ApiResponse(
        success=True,
        data=agent_types
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)