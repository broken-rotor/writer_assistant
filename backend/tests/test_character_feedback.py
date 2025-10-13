"""
Tests for character feedback endpoint.
"""
import pytest
from fastapi.testclient import TestClient


class TestCharacterFeedbackEndpoint:
    """Test character feedback generation endpoint"""

    def test_character_feedback_success(self, client, sample_character_feedback_request):
        """Test successful character feedback generation"""
        response = client.post("/api/v1/character-feedback", json=sample_character_feedback_request)
        assert response.status_code == 200
        data = response.json()
        assert "characterName" in data
        assert "feedback" in data

    def test_character_feedback_response_structure(self, client, sample_character_feedback_request):
        """Test character feedback response has correct structure"""
        response = client.post("/api/v1/character-feedback", json=sample_character_feedback_request)
        data = response.json()

        assert data["characterName"] == "Detective Sarah Chen"
        feedback = data["feedback"]
        assert "actions" in feedback
        assert "dialog" in feedback
        assert "physicalSensations" in feedback
        assert "emotions" in feedback
        assert "internalMonologue" in feedback

    def test_character_feedback_arrays_not_empty(self, client, sample_character_feedback_request):
        """Test character feedback arrays contain data"""
        response = client.post("/api/v1/character-feedback", json=sample_character_feedback_request)
        feedback = response.json()["feedback"]

        assert isinstance(feedback["actions"], list)
        assert len(feedback["actions"]) > 0
        assert isinstance(feedback["dialog"], list)
        assert len(feedback["dialog"]) > 0
        assert isinstance(feedback["physicalSensations"], list)
        assert len(feedback["physicalSensations"]) > 0
        assert isinstance(feedback["emotions"], list)
        assert len(feedback["emotions"]) > 0
        assert isinstance(feedback["internalMonologue"], list)
        assert len(feedback["internalMonologue"]) > 0

    def test_character_feedback_missing_required_fields(self, client):
        """Test character feedback fails without required fields"""
        invalid_request = {
            "systemPrompts": {"mainPrefix": "", "mainSuffix": ""},
            "worldbuilding": "Test world"
        }
        response = client.post("/api/v1/character-feedback", json=invalid_request)
        assert response.status_code == 422  # Validation error

    def test_character_feedback_with_empty_plot_point(self, client, sample_character_feedback_request):
        """Test character feedback works with empty plot point"""
        sample_character_feedback_request["plotPoint"] = ""
        response = client.post("/api/v1/character-feedback", json=sample_character_feedback_request)
        assert response.status_code == 200

    def test_character_feedback_with_previous_chapters(self, client, sample_character_feedback_request):
        """Test character feedback with previous chapters"""
        sample_character_feedback_request["previousChapters"] = [
            {"number": 1, "title": "Chapter 1", "content": "Chapter 1 content"},
            {"number": 2, "title": "Chapter 2", "content": "Chapter 2 content"}
        ]
        response = client.post("/api/v1/character-feedback", json=sample_character_feedback_request)
        assert response.status_code == 200
