"""
Tests for chapter modification endpoint.
"""
import pytest
from fastapi.testclient import TestClient


class TestModifyChapterEndpoint:
    """Test chapter modification endpoint"""

    def test_modify_chapter_success(self, client, sample_modify_chapter_request):
        """Test successful chapter modification"""
        response = client.post("/api/v1/modify-chapter", json=sample_modify_chapter_request)
        assert response.status_code == 200
        data = response.json()
        assert "modifiedChapter" in data
        assert "wordCount" in data
        assert "changesSummary" in data

    def test_modify_chapter_response_structure(self, client, sample_modify_chapter_request):
        """Test modify chapter response structure"""
        response = client.post("/api/v1/modify-chapter", json=sample_modify_chapter_request)
        data = response.json()

        assert isinstance(data["modifiedChapter"], str)
        assert isinstance(data["wordCount"], int)
        assert isinstance(data["changesSummary"], str)
        assert data["wordCount"] > 0

    def test_modify_chapter_includes_original_content(self, client, sample_modify_chapter_request):
        """Test that modified chapter is returned"""
        response = client.post("/api/v1/modify-chapter", json=sample_modify_chapter_request)
        modified_text = response.json()["modifiedChapter"]

        # Modified chapter should contain meaningful content
        assert len(modified_text) > 0
        assert "Detective Chen" in modified_text or "Chen" in modified_text

    def test_modify_chapter_changes_summary_mentions_request(self, client, sample_modify_chapter_request):
        """Test that changes summary mentions the modification"""
        user_request = sample_modify_chapter_request["userRequest"]
        response = client.post("/api/v1/modify-chapter", json=sample_modify_chapter_request)
        changes_summary = response.json()["changesSummary"]

        # Summary should contain information about the changes
        assert len(changes_summary) > 0
        assert "modified" in changes_summary.lower() or "based on" in changes_summary.lower()

    def test_modify_chapter_with_long_user_request(self, client, sample_modify_chapter_request):
        """Test modify chapter with long user request"""
        long_request = "Please modify this chapter by " + "adding more detail " * 50
        sample_modify_chapter_request["userRequest"] = long_request
        response = client.post("/api/v1/modify-chapter", json=sample_modify_chapter_request)
        assert response.status_code == 200

    def test_modify_chapter_missing_current_chapter(self, client):
        """Test modify chapter fails without current chapter"""
        invalid_request = {
            "systemPrompts": {"mainPrefix": "", "mainSuffix": ""},
            "worldbuilding": "Test",
            "storySummary": "Test",
            "previousChapters": [],
            "userRequest": "Change something"
        }
        response = client.post("/api/v1/modify-chapter", json=invalid_request)
        assert response.status_code == 422
