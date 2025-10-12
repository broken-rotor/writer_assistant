import pytest
from fastapi.testclient import TestClient
from app.main import app


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
