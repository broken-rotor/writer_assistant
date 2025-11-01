import pytest
from unittest.mock import Mock, MagicMock, patch
from fastapi.testclient import TestClient
from pydantic import ConfigDict, Field
import json

from app.main import app
from app.core.config import Settings
from app.services.llm_inference import LLMInference



@pytest.fixture(autouse=True)
def patch_settings():
    Settings.model_config = ConfigDict(
        case_sensitive=True,
        env_file = ".env.example")


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
    """Sample character feedback request using structured context"""
    return {
        "context_mode": "structured",
        "structured_context": {
            "plot_elements": [
                {
                    "type": "scene",
                    "content": "The detective discovers a crucial clue at the crime scene",
                    "priority": "high",
                    "tags": ["current_scene", "investigation"],
                    "metadata": {"location": "crime_scene", "time": "night"}
                },
                {
                    "type": "setup",
                    "content": "A noir detective story set in 1940s Los Angeles",
                    "priority": "medium",
                    "tags": ["setting", "genre"],
                    "metadata": {"era": "1940s", "location": "los_angeles", "genre": "noir"}
                }
            ],
            "character_contexts": [
                {
                    "character_id": "detective_sarah_chen",
                    "character_name": "Detective Sarah Chen",
                    "current_state": {
                        "emotion": "focused",
                        "location": "crime_scene",
                        "mental_state": "analytical"
                    },
                    "recent_actions": ["Arrived at crime scene", "Began investigation"],
                    "relationships": {"partner": "works_alone", "suspects": "suspicious"},
                    "goals": ["Find the murderer", "Solve the case"],
                    "memories": ["Previous partner's death", "Similar cases"],
                    "personality_traits": ["cynical", "determined", "observant"]
                }
            ],
            "user_requests": [],
            "system_instructions": [
                {
                    "type": "behavior",
                    "content": "You are a creative writing assistant. Be detailed and authentic.",
                    "scope": "global",
                    "priority": "high"
                }
            ]
        },
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
        "plotPoint": "The detective discovers a crucial clue at the crime scene",
        "previousChapters": []
    }


@pytest.fixture
def sample_rater_feedback_request():
    """Sample rater feedback request using structured context"""
    return {
        "context_mode": "structured",
        "structured_context": {
            "plot_elements": [
                {
                    "type": "scene",
                    "content": "The detective discovers a crucial clue at the crime scene",
                    "priority": "high",
                    "tags": ["current_scene", "investigation"],
                    "metadata": {"location": "crime_scene", "time": "night"}
                },
                {
                    "type": "setup",
                    "content": "A noir detective story set in 1940s Los Angeles",
                    "priority": "medium",
                    "tags": ["setting", "genre"],
                    "metadata": {"era": "1940s", "location": "los_angeles", "genre": "noir"}
                }
            ],
            "character_contexts": [],
            "user_requests": [
                {
                    "type": "general",
                    "content": "Evaluate the narrative flow and character consistency",
                    "priority": "high",
                    "context": "rater_evaluation"
                }
            ],
            "system_instructions": [
                {
                    "type": "behavior",
                    "content": "You are a story quality rater. Provide constructive feedback.",
                    "scope": "global",
                    "priority": "high"
                }
            ]
        },
        "raterPrompt": "Evaluate the narrative flow and character consistency",
        "plotPoint": "The detective discovers a crucial clue at the crime scene",
        "previousChapters": []
    }


@pytest.fixture
def sample_generate_chapter_request():
    """Sample chapter generation request using structured context"""
    return {
        "context_mode": "structured",
        "structured_context": {
            "plot_elements": [
                {
                    "type": "scene",
                    "content": "The detective discovers a crucial clue at the crime scene",
                    "priority": "high",
                    "tags": ["current_scene", "investigation"],
                    "metadata": {"location": "crime_scene", "time": "night"}
                },
                {
                    "type": "setup",
                    "content": "A noir detective story set in 1940s Los Angeles",
                    "priority": "medium",
                    "tags": ["setting", "genre"],
                    "metadata": {"era": "1940s", "location": "los_angeles", "genre": "noir"}
                }
            ],
            "character_contexts": [
                {
                    "character_id": "detective_sarah_chen",
                    "character_name": "Detective Sarah Chen",
                    "current_state": {
                        "emotion": "determined",
                        "location": "crime_scene",
                        "mental_state": "focused"
                    },
                    "recent_actions": ["Arrived at scene", "Examining evidence"],
                    "relationships": {"partner": "works_alone"},
                    "goals": ["Solve the murder case", "Find justice"],
                    "memories": ["Previous cases", "Lost partner"],
                    "personality_traits": ["cynical", "determined", "observant"]
                }
            ],
            "user_requests": [],
            "system_instructions": [
                {
                    "type": "behavior",
                    "content": "You are a creative writing assistant. Write engaging prose.",
                    "scope": "global",
                    "priority": "high"
                },
                {
                    "type": "style",
                    "content": "Focus on vivid descriptions",
                    "scope": "chapter",
                    "priority": "medium"
                }
            ]
        },
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
        "previousChapters": [],
        "incorporatedFeedback": []
    }


@pytest.fixture
def sample_modify_chapter_request():
    """Sample chapter modification request using structured context"""
    return {
        "context_mode": "structured",
        "structured_context": {
            "plot_elements": [
                {
                    "type": "scene",
                    "content": "Detective examining crime scene in the rain",
                    "priority": "high",
                    "tags": ["current_scene", "investigation", "weather"],
                    "metadata": {"location": "crime_scene", "time": "night", "weather": "rain"}
                },
                {
                    "type": "setup",
                    "content": "A noir detective story set in 1940s Los Angeles",
                    "priority": "medium",
                    "tags": ["setting", "genre"],
                    "metadata": {"era": "1940s", "location": "los_angeles", "genre": "noir"}
                }
            ],
            "character_contexts": [
                {
                    "character_id": "detective_chen",
                    "character_name": "Detective Chen",
                    "current_state": {
                        "emotion": "focused",
                        "location": "crime_scene",
                        "mental_state": "analytical"
                    },
                    "recent_actions": ["Arrived at scene", "Examining evidence"],
                    "relationships": {},
                    "goals": ["Examine the crime scene thoroughly"],
                    "memories": ["Previous crime scenes"],
                    "personality_traits": ["experienced", "methodical", "observant"]
                }
            ],
            "user_requests": [
                {
                    "type": "modification",
                    "content": "Add more atmospheric details about the weather and setting",
                    "priority": "high",
                    "target": "current_chapter",
                    "context": "enhancement"
                }
            ],
            "system_instructions": [
                {
                    "type": "behavior",
                    "content": "You are a creative writing assistant. Maintain consistency.",
                    "scope": "global",
                    "priority": "high"
                },
                {
                    "type": "constraint",
                    "content": "Apply changes carefully",
                    "scope": "chapter",
                    "priority": "high"
                }
            ]
        },
        "currentChapter": "The rain fell hard on the city streets. Detective Chen examined the crime scene with practiced eyes."
    }


@pytest.fixture
def sample_editor_review_request():
    """Sample editor review request using structured context"""
    return {
        "context_mode": "structured",
        "structured_context": {
            "plot_elements": [
                {
                    "type": "scene",
                    "content": "Detective examining crime scene in the rain",
                    "priority": "high",
                    "tags": ["current_scene", "investigation", "weather"],
                    "metadata": {"location": "crime_scene", "time": "night", "weather": "rain"}
                },
                {
                    "type": "setup",
                    "content": "A noir detective story set in 1940s Los Angeles",
                    "priority": "medium",
                    "tags": ["setting", "genre"],
                    "metadata": {"era": "1940s", "location": "los_angeles", "genre": "noir"}
                }
            ],
            "character_contexts": [
                {
                    "character_id": "detective_chen",
                    "character_name": "Detective Chen",
                    "current_state": {
                        "emotion": "focused",
                        "location": "crime_scene",
                        "mental_state": "analytical"
                    },
                    "recent_actions": ["Examining crime scene"],
                    "relationships": {},
                    "goals": ["Investigate the case"],
                    "memories": [],
                    "personality_traits": ["methodical", "observant"]
                }
            ],
            "user_requests": [],
            "system_instructions": [
                {
                    "type": "behavior",
                    "content": "You are an editor. Provide constructive suggestions.",
                    "scope": "global",
                    "priority": "high"
                },
                {
                    "type": "constraint",
                    "content": "Focus on prose quality and consistency",
                    "scope": "chapter",
                    "priority": "high"
                }
            ]
        },
        "characters": [],
        "chapterToReview": "The rain fell hard on the city streets. Detective Chen examined the crime scene."
    }


@pytest.fixture
def sample_flesh_out_request():
    """Sample flesh out request using structured context"""
    return {
        "context_mode": "structured",
        "structured_context": {
            "plot_elements": [
                {
                    "type": "scene",
                    "content": "The detective finds a mysterious photograph",
                    "priority": "high",
                    "tags": ["current_scene", "evidence", "mystery"],
                    "metadata": {"item": "photograph", "significance": "mysterious"}
                },
                {
                    "type": "setup",
                    "content": "A noir detective story set in 1940s Los Angeles",
                    "priority": "medium",
                    "tags": ["setting", "genre"],
                    "metadata": {"era": "1940s", "location": "los_angeles", "genre": "noir"}
                }
            ],
            "character_contexts": [],
            "user_requests": [
                {
                    "type": "addition",
                    "content": "Expand with relevant detail about the photograph",
                    "priority": "high",
                    "target": "photograph_scene",
                    "context": "worldbuilding"
                }
            ],
            "system_instructions": [
                {
                    "type": "behavior",
                    "content": "You are a creative writing assistant. Expand with relevant detail.",
                    "scope": "global",
                    "priority": "high"
                }
            ]
        },
        "textToFleshOut": "The detective finds a mysterious photograph"
    }


@pytest.fixture
def sample_generate_character_request():
    """Sample generate character details request using structured context"""
    return {
        "context_mode": "structured",
        "structured_context": {
            "plot_elements": [
                {
                    "type": "setup",
                    "content": "A noir detective story set in 1940s Los Angeles",
                    "priority": "medium",
                    "tags": ["setting", "genre"],
                    "metadata": {"era": "1940s", "location": "los_angeles", "genre": "noir"}
                }
            ],
            "character_contexts": [],
            "user_requests": [
                {
                    "type": "addition",
                    "content": "Create a tough but fair detective with a mysterious past",
                    "priority": "high",
                    "target": "new_character",
                    "context": "character_creation"
                }
            ],
            "system_instructions": [
                {
                    "type": "behavior",
                    "content": "You are a character creator. Create believable characters.",
                    "scope": "global",
                    "priority": "high"
                }
            ]
        },
        "basicBio": "A tough but fair detective with a mysterious past",
        "existingCharacters": []
    }


@pytest.fixture
def sample_structured_context_container():
    """Sample structured context container for testing"""
    from app.models.generation_models import (
        StructuredContextContainer,
        PlotElement,
        CharacterContext,
        UserRequest,
        SystemInstruction,
        ContextMetadata
    )
    from datetime import datetime
    
    return StructuredContextContainer(
        plot_elements=[
            PlotElement(
                id="scene_001",
                type="scene",
                content="The detective arrives at the crime scene on a rainy night",
                priority="high",
                tags=["current_scene", "investigation", "weather"],
                metadata={"location": "crime_scene", "time": "night", "weather": "rain"}
            ),
            PlotElement(
                id="setup_001",
                type="setup",
                content="A noir detective story set in 1940s Los Angeles",
                priority="medium",
                tags=["setting", "genre", "background"],
                metadata={"era": "1940s", "location": "los_angeles", "genre": "noir"}
            )
        ],
        character_contexts=[
            CharacterContext(
                character_id="detective_sarah_chen",
                character_name="Detective Sarah Chen",
                current_state={
                    "emotion": "focused",
                    "location": "crime_scene",
                    "mental_state": "analytical",
                    "physical_state": "alert"
                },
                recent_actions=["Arrived at scene", "Examining evidence", "Taking notes"],
                relationships={"partner": "works_alone", "suspects": "suspicious"},
                goals=["Solve the murder case", "Find justice", "Protect the innocent"],
                memories=["Previous partner's death", "Similar cases", "Training"],
                personality_traits=["cynical", "determined", "observant", "methodical"]
            )
        ],
        user_requests=[
            UserRequest(
                id="req_001",
                type="general",
                content="Focus on atmospheric details and character development",
                priority="medium",
                context="story_enhancement",
                timestamp=datetime.now()
            )
        ],
        system_instructions=[
            SystemInstruction(
                id="inst_001",
                type="behavior",
                content="You are a creative writing assistant focused on noir storytelling",
                scope="global",
                priority="high",
                metadata={"genre": "noir", "style": "atmospheric"}
            ),
            SystemInstruction(
                id="inst_002",
                type="style",
                content="Use vivid descriptions and maintain consistent tone",
                scope="chapter",
                priority="medium"
            )
        ],
        metadata=ContextMetadata(
            total_elements=6,
            processing_applied=True,
            processing_mode="structured",
            optimization_level="light",
            compression_ratio=0.85,
            filtered_elements={"plot": 2, "character": 1, "user": 1, "system": 2},
            processing_time_ms=150.5,
            created_at=datetime.now().isoformat(),
            version="1.0"
        )
    )


@pytest.fixture
def sample_legacy_context_request():
    """Sample legacy context request for backward compatibility testing"""
    return {
        "context_mode": "legacy",
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
