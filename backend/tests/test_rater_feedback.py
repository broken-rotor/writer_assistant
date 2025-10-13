"""
Tests for rater feedback endpoint.
"""
import pytest
from fastapi.testclient import TestClient


class TestRaterFeedbackEndpoint:
    """Test rater feedback generation endpoint"""

    def test_rater_feedback_success(self, client, sample_rater_feedback_request):
        """Test successful rater feedback generation"""
        response = client.post("/api/v1/rater-feedback", json=sample_rater_feedback_request)
        assert response.status_code == 200
        data = response.json()
        assert "raterName" in data
        assert "feedback" in data

    def test_rater_feedback_response_structure(self, client, sample_rater_feedback_request):
        """Test rater feedback response has correct structure"""
        response = client.post("/api/v1/rater-feedback", json=sample_rater_feedback_request)
        data = response.json()

        feedback = data["feedback"]
        assert "opinion" in feedback
        assert "suggestions" in feedback
        assert isinstance(feedback["opinion"], str)
        assert isinstance(feedback["suggestions"], list)

    def test_rater_feedback_has_suggestions(self, client, sample_rater_feedback_request):
        """Test rater feedback includes suggestions"""
        response = client.post("/api/v1/rater-feedback", json=sample_rater_feedback_request)
        suggestions = response.json()["feedback"]["suggestions"]

        assert len(suggestions) > 0
        for suggestion in suggestions:
            assert isinstance(suggestion, str)
            assert len(suggestion) > 0

    def test_rater_feedback_opinion_not_empty(self, client, sample_rater_feedback_request):
        """Test rater opinion is not empty"""
        response = client.post("/api/v1/rater-feedback", json=sample_rater_feedback_request)
        opinion = response.json()["feedback"]["opinion"]
        assert len(opinion) > 0

    def test_rater_feedback_missing_rater_prompt(self, client):
        """Test rater feedback fails without rater prompt"""
        invalid_request = {
            "systemPrompts": {"mainPrefix": "", "mainSuffix": ""},
            "worldbuilding": "Test",
            "storySummary": "Test",
            "previousChapters": [],
            "plotPoint": "Test"
        }
        response = client.post("/api/v1/rater-feedback", json=invalid_request)
        assert response.status_code == 422

    def test_rater_feedback_with_incorporated_feedback(self, client, sample_rater_feedback_request):
        """Test rater feedback with incorporated feedback items"""
        sample_rater_feedback_request["incorporatedFeedback"] = [
            {"source": "character", "type": "action", "content": "Test", "incorporated": True}
        ]
        response = client.post("/api/v1/rater-feedback", json=sample_rater_feedback_request)
        assert response.status_code == 200
