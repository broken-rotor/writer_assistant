import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create a test client for FastAPI application"""
    return TestClient(app)


@pytest.fixture
def sample_outline_request():
    """Sample outline generation request"""
    return {
        "title": "The Mystery of Echo Manor",
        "genre": "Mystery",
        "description": "A detective investigates strange occurrences in an old manor",
        "user_guidance": "Focus on atmospheric tension and character development",
        "configuration": {
            "style_profile": "noir_detective",
            "target_length": "novel",
            "complexity_level": "high"
        }
    }


@pytest.fixture
def sample_chapter_request():
    """Sample chapter generation request"""
    return {
        "session_id": "test-session-123",
        "chapter_number": 1,
        "user_guidance": "Introduce the detective and establish the mystery",
        "story_context": {
            "outline": {
                "acts": [{"act": 1, "title": "Setup"}],
                "characters": [{"name": "Detective Morrison", "role": "protagonist"}]
            }
        },
        "configuration": {
            "style_profile": "standard"
        }
    }


@pytest.fixture
def sample_feedback_request():
    """Sample feedback request"""
    return {
        "phase": "outline_development",
        "feedback_type": "user_review",
        "feedback": {
            "approval_status": "approved",
            "comments": "Great outline, proceed to chapter development"
        }
    }


@pytest.fixture
def sample_character_config():
    """Sample character configuration"""
    return {
        "name": "Detective Morrison",
        "role": "protagonist",
        "personality_traits": ["analytical", "reserved", "determined"],
        "background": {
            "age": 42,
            "occupation": "homicide_detective",
            "key_events": ["Lost partner 3 years ago", "Decorated veteran"]
        }
    }


@pytest.fixture
def sample_generation_config():
    """Sample generation configuration"""
    return {
        "style_profile": "literary_fiction",
        "character_templates": ["complex_protagonist", "mysterious_antagonist"],
        "rater_preferences": ["character_consistency", "narrative_flow", "literary_quality"],
        "target_length": "novel",
        "complexity_level": "high"
    }
