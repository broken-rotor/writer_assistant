"""
Tests for character details generation endpoint.
"""
import pytest
from fastapi.testclient import TestClient


class TestGenerateCharacterDetailsEndpoint:
    """Test character details generation endpoint"""

    def test_generate_character_details_success(self, client, sample_generate_character_request):
        """Test successful character details generation"""
        response = client.post("/api/v1/generate-character-details", json=sample_generate_character_request)
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "sex" in data
        assert "gender" in data
        assert "age" in data

    def test_generate_character_details_response_structure(self, client, sample_generate_character_request):
        """Test character details response has all required fields"""
        response = client.post("/api/v1/generate-character-details", json=sample_generate_character_request)
        data = response.json()

        required_fields = [
            "name", "sex", "gender", "sexualPreference", "age",
            "physicalAppearance", "usualClothing", "personality",
            "motivations", "fears", "relationships"
        ]

        for field in required_fields:
            assert field in data

    def test_generate_character_details_field_types(self, client, sample_generate_character_request):
        """Test character details field types are correct"""
        response = client.post("/api/v1/generate-character-details", json=sample_generate_character_request)
        data = response.json()

        assert isinstance(data["name"], str)
        assert isinstance(data["sex"], str)
        assert isinstance(data["gender"], str)
        assert isinstance(data["sexualPreference"], str)
        assert isinstance(data["age"], int)
        assert isinstance(data["physicalAppearance"], str)
        assert isinstance(data["usualClothing"], str)
        assert isinstance(data["personality"], str)
        assert isinstance(data["motivations"], str)
        assert isinstance(data["fears"], str)
        assert isinstance(data["relationships"], str)

    def test_generate_character_details_age_is_positive(self, client, sample_generate_character_request):
        """Test generated character age is positive"""
        response = client.post("/api/v1/generate-character-details", json=sample_generate_character_request)
        age = response.json()["age"]
        assert age > 0

    def test_generate_character_details_with_existing_characters(self, client, sample_generate_character_request):
        """Test character generation with existing characters"""
        sample_generate_character_request["existingCharacters"] = [
            {"name": "John Doe", "basicBio": "A detective", "relationships": "None"},
            {"name": "Jane Smith", "basicBio": "A journalist", "relationships": "Colleague of John"}
        ]
        response = client.post("/api/v1/generate-character-details", json=sample_generate_character_request)
        assert response.status_code == 200
        relationships = response.json()["relationships"]
        # Should reference existing characters
        assert len(relationships) > 0

    def test_generate_character_details_without_existing_characters(self, client, sample_generate_character_request):
        """Test character generation without existing characters"""
        sample_generate_character_request["existingCharacters"] = []
        response = client.post("/api/v1/generate-character-details", json=sample_generate_character_request)
        assert response.status_code == 200

    def test_generate_character_details_fields_not_empty(self, client, sample_generate_character_request):
        """Test that key fields are not empty"""
        response = client.post("/api/v1/generate-character-details", json=sample_generate_character_request)
        data = response.json()

        # These fields should have meaningful content
        assert len(data["name"]) > 0
        assert len(data["physicalAppearance"]) > 10
        assert len(data["personality"]) > 10
        assert len(data["motivations"]) > 10
        assert len(data["fears"]) > 10

    def test_generate_character_details_missing_basic_bio(self, client):
        """Test character generation fails without basic bio"""
        invalid_request = {
            "systemPrompts": {"mainPrefix": "", "mainSuffix": ""},
            "worldbuilding": "Test",
            "storySummary": "Test",
            "existingCharacters": []
        }
        response = client.post("/api/v1/generate-character-details", json=invalid_request)
        assert response.status_code == 422
