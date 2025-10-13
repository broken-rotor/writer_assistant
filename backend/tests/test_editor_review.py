"""
Tests for editor review endpoint.
"""
import pytest
from fastapi.testclient import TestClient


class TestEditorReviewEndpoint:
    """Test editor review endpoint"""

    def test_editor_review_success(self, client, sample_editor_review_request):
        """Test successful editor review"""
        response = client.post("/api/v1/editor-review", json=sample_editor_review_request)
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data

    def test_editor_review_response_structure(self, client, sample_editor_review_request):
        """Test editor review response structure"""
        response = client.post("/api/v1/editor-review", json=sample_editor_review_request)
        data = response.json()

        assert isinstance(data["suggestions"], list)
        assert len(data["suggestions"]) > 0

    def test_editor_review_suggestion_structure(self, client, sample_editor_review_request):
        """Test individual suggestion structure"""
        response = client.post("/api/v1/editor-review", json=sample_editor_review_request)
        suggestions = response.json()["suggestions"]

        for suggestion in suggestions:
            assert "issue" in suggestion
            assert "suggestion" in suggestion
            assert "priority" in suggestion
            assert isinstance(suggestion["issue"], str)
            assert isinstance(suggestion["suggestion"], str)
            assert suggestion["priority"] in ["high", "medium", "low"]

    def test_editor_review_has_multiple_priorities(self, client, sample_editor_review_request):
        """Test editor review includes suggestions with different priorities"""
        response = client.post("/api/v1/editor-review", json=sample_editor_review_request)
        suggestions = response.json()["suggestions"]

        priorities = set(s["priority"] for s in suggestions)
        # Should have at least 2 different priority levels
        assert len(priorities) >= 2

    def test_editor_review_with_characters(self, client, sample_editor_review_request):
        """Test editor review with character information"""
        sample_editor_review_request["characters"] = [
            {
                "name": "Character 1",
                "basicBio": "A test character",
                "sex": "Female",
                "gender": "Female",
                "sexualPreference": "Heterosexual",
                "age": 30,
                "physicalAppearance": "Average",
                "usualClothing": "Casual",
                "personality": "Friendly",
                "motivations": "Success",
                "fears": "Failure",
                "relationships": "None"
            }
        ]
        response = client.post("/api/v1/editor-review", json=sample_editor_review_request)
        assert response.status_code == 200

    def test_editor_review_missing_chapter(self, client):
        """Test editor review fails without chapter to review"""
        invalid_request = {
            "systemPrompts": {"mainPrefix": "", "mainSuffix": ""},
            "worldbuilding": "Test",
            "storySummary": "Test",
            "previousChapters": [],
            "characters": []
        }
        response = client.post("/api/v1/editor-review", json=invalid_request)
        assert response.status_code == 422
