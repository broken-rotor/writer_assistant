"""
Tests for chapter generation endpoint.
"""
import pytest
from fastapi.testclient import TestClient


class TestGenerateChapterEndpoint:
    """Test chapter generation endpoint"""

    def test_generate_chapter_success(self, client, sample_generate_chapter_request):
        """Test successful chapter generation"""
        response = client.post("/api/v1/generate-chapter", json=sample_generate_chapter_request)
        assert response.status_code == 200
        data = response.json()
        assert "chapterText" in data
        assert "wordCount" in data
        assert "metadata" in data

    def test_generate_chapter_response_structure(self, client, sample_generate_chapter_request):
        """Test chapter generation response structure"""
        response = client.post("/api/v1/generate-chapter", json=sample_generate_chapter_request)
        data = response.json()

        assert isinstance(data["chapterText"], str)
        assert isinstance(data["wordCount"], int)
        assert isinstance(data["metadata"], dict)
        assert data["wordCount"] > 0
        assert len(data["chapterText"]) > 0

    def test_generate_chapter_metadata_contains_info(self, client, sample_generate_chapter_request):
        """Test chapter metadata contains expected information"""
        response = client.post("/api/v1/generate-chapter", json=sample_generate_chapter_request)
        metadata = response.json()["metadata"]

        assert "generatedAt" in metadata
        assert "plotPoint" in metadata
        assert "feedbackItemsIncorporated" in metadata

    def test_generate_chapter_with_empty_plot_point(self, client, sample_generate_chapter_request):
        """Test chapter generation with empty plot point"""
        sample_generate_chapter_request["plotPoint"] = ""
        response = client.post("/api/v1/generate-chapter", json=sample_generate_chapter_request)
        assert response.status_code == 200
        data = response.json()
        assert len(data["chapterText"]) > 0

    def test_generate_chapter_with_multiple_characters(self, client, sample_generate_chapter_request):
        """Test chapter generation with multiple characters"""
        sample_generate_chapter_request["characters"].append({
            "name": "John Doe",
            "basicBio": "A mysterious stranger",
            "sex": "Male",
            "gender": "Male",
            "sexualPreference": "Heterosexual",
            "age": 40,
            "physicalAppearance": "Tall and imposing",
            "usualClothing": "Dark suits",
            "personality": "Enigmatic",
            "motivations": "Unknown",
            "fears": "Exposure",
            "relationships": "None known"
        })
        response = client.post("/api/v1/generate-chapter", json=sample_generate_chapter_request)
        assert response.status_code == 200

    def test_generate_chapter_with_incorporated_feedback(self, client, sample_generate_chapter_request):
        """Test chapter generation with incorporated feedback"""
        sample_generate_chapter_request["incorporatedFeedback"] = [
            {"source": "character1", "type": "action", "content": "Consider this", "incorporated": True},
            {"source": "rater1", "type": "suggestion", "content": "Add more detail", "incorporated": True}
        ]
        response = client.post("/api/v1/generate-chapter", json=sample_generate_chapter_request)
        assert response.status_code == 200
        metadata = response.json()["metadata"]
        assert metadata["feedbackItemsIncorporated"] == 2

    def test_generate_chapter_word_count_accuracy(self, client, sample_generate_chapter_request):
        """Test that word count is reasonably accurate"""
        response = client.post("/api/v1/generate-chapter", json=sample_generate_chapter_request)
        data = response.json()

        actual_word_count = len(data["chapterText"].split())
        reported_word_count = data["wordCount"]

        # Word count should be exact
        assert actual_word_count == reported_word_count

    def test_generate_chapter_missing_required_fields(self, client):
        """Test chapter generation fails without required fields"""
        invalid_request = {
            "systemPrompts": {"mainPrefix": "", "mainSuffix": ""}
        }
        response = client.post("/api/v1/generate-chapter", json=invalid_request)
        assert response.status_code == 422
