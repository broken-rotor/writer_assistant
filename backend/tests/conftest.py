import pytest
from unittest.mock import Mock, MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.services.llm_inference import LLMInference
import json


@pytest.fixture(autouse=True)
def mock_llm():
    """Mock the LLM for all tests"""
    mock_llm_instance = MagicMock(spec=LLMInference)

    # Mock generate method with intelligent responses
    def generate_side_effect(prompt, **kwargs):
        # Character feedback - return JSON
        if "embodying" in prompt.lower() or "character" in prompt.lower() and "actions" in prompt:
            return json.dumps({
                "actions": ["Takes a deep breath", "Looks around carefully", "Steps forward"],
                "dialog": ["This changes everything", "I need to think", "What now?"],
                "physicalSensations": ["Heart racing", "Palms sweating", "Adrenaline pumping"],
                "emotions": ["Anxious", "Determined", "Cautious"],
                "internalMonologue": ["I can do this", "Stay focused", "One step at a time"]
            })

        # Rater feedback - return JSON
        elif "rater" in prompt.lower() or ("opinion" in prompt and "suggestions" in prompt):
            return json.dumps({
                "opinion": "This plot point is engaging and moves the story forward effectively.",
                "suggestions": [
                    "Add more sensory details",
                    "Heighten emotional stakes",
                    "Connect to story arc",
                    "Improve pacing"
                ]
            })

        # Editor review - return JSON
        elif "editor" in prompt.lower() or "review" in prompt.lower():
            return json.dumps({
                "suggestions": [
                    {"issue": "Opening needs work", "suggestion": "Add sensory details", "priority": "high"},
                    {"issue": "Dialogue feels flat", "suggestion": "Make voices distinct", "priority": "medium"},
                    {"issue": "Pacing issues", "suggestion": "Tighten middle section", "priority": "medium"},
                    {"issue": "Weak transitions", "suggestion": "Add scene breaks", "priority": "low"}
                ]
            })

        # Character details - return JSON
        elif "character details" in prompt.lower() or "character concept" in prompt.lower():
            return json.dumps({
                "name": "Alex Morgan",
                "sex": "Female",
                "gender": "Female",
                "sexualPreference": "Bisexual",
                "age": 34,
                "physicalAppearance": "Tall and athletic with dark hair and piercing eyes",
                "usualClothing": "Practical jeans and leather jacket",
                "personality": "Independent, analytical, determined with hidden warmth",
                "motivations": "Seeking truth and justice while proving herself",
                "fears": "Failure, vulnerability, letting others down",
                "relationships": "Struggles with trust but loyal to those who earn it"
            })

        # Chapter generation or modification
        elif "chapter" in prompt.lower() or "write" in prompt.lower():
            return """The rain fell hard on the city streets as Detective Chen examined the scene. Every detail mattered now.

She knelt beside the evidence, her trained eye catching what others had missed. The implications were staggering - this case was about to break wide open.

"We need to move fast," she said, her voice steady despite the adrenaline. The pieces were finally coming together, but time was running out."""

        # Flesh out
        elif "expand" in prompt.lower() or "flesh out" in prompt.lower():
            text_to_expand = prompt.split("Text to expand:")[-1].strip() if "Text to expand:" in prompt else "the situation"
            return f"""{text_to_expand}

The atmosphere was thick with tension as the moment unfolded. Every sensory detail heightened the experience - the distant sound of traffic, the smell of rain on pavement, the cool metal of the detective's badge against her chest.

What had seemed simple moments ago now revealed layers of complexity. The characters involved each brought their own perspectives, their own histories that colored how they perceived and reacted to events."""

        # Default
        else:
            return "This is a generated response from the LLM for testing purposes."

    mock_llm_instance.generate.side_effect = generate_side_effect

    # Mock chat_completion with intelligent responses (same logic as generate)
    def chat_completion_side_effect(messages, **kwargs):
        # Extract the combined content from system and user messages
        combined_prompt = "\n".join(msg["content"] for msg in messages)
        # Use the same logic as generate
        return generate_side_effect(combined_prompt, **kwargs)

    mock_llm_instance.chat_completion.side_effect = chat_completion_side_effect

    # Patch get_llm to return our mock in all endpoint modules
    with patch('app.services.llm_inference.get_llm', return_value=mock_llm_instance):
        with patch('app.api.v1.endpoints.character_feedback.get_llm', return_value=mock_llm_instance):
            with patch('app.api.v1.endpoints.rater_feedback.get_llm', return_value=mock_llm_instance):
                with patch('app.api.v1.endpoints.generate_chapter.get_llm', return_value=mock_llm_instance):
                    with patch('app.api.v1.endpoints.modify_chapter.get_llm', return_value=mock_llm_instance):
                        with patch('app.api.v1.endpoints.editor_review.get_llm', return_value=mock_llm_instance):
                            with patch('app.api.v1.endpoints.flesh_out.get_llm', return_value=mock_llm_instance):
                                with patch('app.api.v1.endpoints.generate_character_details.get_llm', return_value=mock_llm_instance):
                                    yield mock_llm_instance


@pytest.fixture
def client():
    """Create a test client for FastAPI application"""
    return TestClient(app)


@pytest.fixture
def sample_character_feedback_request():
    """Sample character feedback request"""
    return {
        "systemPrompts": {
            "mainPrefix": "You are a creative writing assistant.",
            "mainSuffix": "Be detailed and authentic."
        },
        "worldbuilding": "A noir detective story set in 1940s Los Angeles",
        "storySummary": "A detective investigates a mysterious murder case",
        "previousChapters": [],
        "character": {
            "name": "Detective Sarah Chen",
            "basicBio": "A hardboiled detective with a troubled past",
            "sex": "Female",
            "gender": "Female",
            "sexualPreference": "Heterosexual",
            "age": 35,
            "physicalAppearance": "Tall, athletic, with sharp eyes",
            "usualClothing": "Trench coat and fedora",
            "personality": "Cynical but determined",
            "motivations": "Seeking justice and redemption",
            "fears": "Losing another partner",
            "relationships": "Works alone, trusts few people"
        },
        "plotPoint": "The detective discovers a crucial clue at the crime scene"
    }


@pytest.fixture
def sample_rater_feedback_request():
    """Sample rater feedback request"""
    return {
        "systemPrompts": {
            "mainPrefix": "You are a story quality rater.",
            "mainSuffix": "Provide constructive feedback."
        },
        "raterPrompt": "Evaluate the narrative flow and character consistency",
        "worldbuilding": "A noir detective story set in 1940s Los Angeles",
        "storySummary": "A detective investigates a mysterious murder case",
        "previousChapters": [],
        "plotPoint": "The detective discovers a crucial clue at the crime scene"
    }


@pytest.fixture
def sample_generate_chapter_request():
    """Sample chapter generation request"""
    return {
        "systemPrompts": {
            "mainPrefix": "You are a creative writing assistant.",
            "mainSuffix": "Write engaging prose.",
            "assistantPrompt": "Focus on vivid descriptions"
        },
        "worldbuilding": "A noir detective story set in 1940s Los Angeles",
        "storySummary": "A detective investigates a mysterious murder case",
        "previousChapters": [],
        "characters": [
            {
                "name": "Detective Sarah Chen",
                "basicBio": "A hardboiled detective",
                "sex": "Female",
                "gender": "Female",
                "sexualPreference": "Heterosexual",
                "age": 35,
                "physicalAppearance": "Tall and athletic",
                "usualClothing": "Trench coat",
                "personality": "Cynical but determined",
                "motivations": "Seeking justice",
                "fears": "Losing another partner",
                "relationships": "Works alone"
            }
        ],
        "plotPoint": "The detective discovers a crucial clue at the crime scene",
        "incorporatedFeedback": []
    }


@pytest.fixture
def sample_modify_chapter_request():
    """Sample chapter modification request"""
    return {
        "systemPrompts": {
            "mainPrefix": "You are a creative writing assistant.",
            "mainSuffix": "Maintain consistency.",
            "assistantPrompt": "Apply changes carefully"
        },
        "worldbuilding": "A noir detective story set in 1940s Los Angeles",
        "storySummary": "A detective investigates a mysterious murder case",
        "previousChapters": [],
        "currentChapter": "The rain fell hard on the city streets. Detective Chen examined the crime scene with practiced eyes.",
        "userRequest": "Add more atmospheric details about the weather and setting"
    }


@pytest.fixture
def sample_editor_review_request():
    """Sample editor review request"""
    return {
        "systemPrompts": {
            "mainPrefix": "You are an editor.",
            "mainSuffix": "Provide constructive suggestions.",
            "editorPrompt": "Focus on prose quality and consistency"
        },
        "worldbuilding": "A noir detective story set in 1940s Los Angeles",
        "storySummary": "A detective investigates a mysterious murder case",
        "previousChapters": [],
        "characters": [],
        "chapterToReview": "The rain fell hard on the city streets. Detective Chen examined the crime scene."
    }


@pytest.fixture
def sample_flesh_out_request():
    """Sample flesh out request"""
    return {
        "systemPrompts": {
            "mainPrefix": "You are a creative writing assistant.",
            "mainSuffix": "Expand with relevant detail."
        },
        "worldbuilding": "A noir detective story set in 1940s Los Angeles",
        "storySummary": "A detective investigates a mysterious murder case",
        "textToFleshOut": "The detective finds a mysterious photograph",
        "context": "worldbuilding"
    }


@pytest.fixture
def sample_generate_character_request():
    """Sample generate character details request"""
    return {
        "systemPrompts": {
            "mainPrefix": "You are a character creator.",
            "mainSuffix": "Create believable characters."
        },
        "worldbuilding": "A noir detective story set in 1940s Los Angeles",
        "storySummary": "A detective investigates a mysterious murder case",
        "basicBio": "A tough but fair detective with a mysterious past",
        "existingCharacters": []
    }
