"""
Tests for character details generation endpoint.
"""
import pytest
import json
from fastapi.testclient import TestClient


def parse_streaming_response(response):
    """Helper function to parse SSE streaming response and extract final result"""
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    
    final_data = None
    status_updates = []
    
    for line in response.text.split('\n'):
        if line.startswith('data: '):
            event_data = json.loads(line[6:])  # Remove 'data: ' prefix
            if event_data.get('type') == 'result':
                final_data = event_data['data']
            elif event_data.get('type') == 'status':
                status_updates.append(event_data)
    
    return final_data, status_updates


class TestGenerateCharacterDetailsEndpoint:
    """Test character details generation endpoint"""

    def test_generate_character_details_success(self, client, sample_generate_character_request):
        """Test successful character details generation with SSE streaming"""
        response = client.post("/api/v1/generate-character-details", json=sample_generate_character_request)
        assert response.status_code == 200
        
        final_data, status_updates = parse_streaming_response(response)
        
        assert final_data is not None
        assert "character_info" in final_data
        character_info = final_data["character_info"]
        assert "name" in character_info
        assert "sex" in character_info
        assert "gender" in character_info
        assert "age" in character_info
        
        # Verify we received status updates
        assert len(status_updates) > 0
        phases = [update['phase'] for update in status_updates]
        expected_phases = ['context_processing', 'analyzing', 'generating', 'parsing']
        for phase in expected_phases:
            assert phase in phases

    def test_generate_character_details_response_structure(self, client, sample_generate_character_request):
        """Test character details response has all required fields"""
        response = client.post("/api/v1/generate-character-details", json=sample_generate_character_request)
        assert response.status_code == 200
        
        final_data, _ = parse_streaming_response(response)

        # Check top-level structure
        assert "character_info" in final_data
        assert "context_metadata" in final_data

        # Check character_info fields
        character_info = final_data["character_info"]
        required_fields = [
            "name", "basicBio", "sex", "gender", "sexualPreference", "age",
            "physicalAppearance", "usualClothing", "personality",
            "motivations", "fears", "relationships"
        ]

        for field in required_fields:
            assert field in character_info

    def test_generate_character_details_field_types(self, client, sample_generate_character_request):
        """Test character details field types are correct"""
        response = client.post("/api/v1/generate-character-details", json=sample_generate_character_request)
        assert response.status_code == 200
        
        final_data, _ = parse_streaming_response(response)
        character_info = final_data["character_info"]

        assert isinstance(character_info["name"], str)
        assert isinstance(character_info["basicBio"], str)
        assert isinstance(character_info["sex"], str)
        assert isinstance(character_info["gender"], str)
        assert isinstance(character_info["sexualPreference"], str)
        assert isinstance(character_info["age"], int)
        assert isinstance(character_info["physicalAppearance"], str)
        assert isinstance(character_info["usualClothing"], str)
        assert isinstance(character_info["personality"], str)
        assert isinstance(character_info["motivations"], str)
        assert isinstance(character_info["fears"], str)
        assert isinstance(character_info["relationships"], str)

    def test_generate_character_details_age_is_positive(self, client, sample_generate_character_request):
        """Test generated character age is positive"""
        response = client.post("/api/v1/generate-character-details", json=sample_generate_character_request)
        assert response.status_code == 200
        
        final_data, _ = parse_streaming_response(response)
        age = final_data["character_info"]["age"]
        assert age > 0

    def test_generate_character_details_with_existing_characters(self, client, sample_generate_character_request):
        """Test character generation with existing characters"""
        sample_generate_character_request["existingCharacters"] = [
            {"name": "John Doe", "basicBio": "A detective", "relationships": "None"},
            {"name": "Jane Smith", "basicBio": "A journalist", "relationships": "Colleague of John"}
        ]
        response = client.post("/api/v1/generate-character-details", json=sample_generate_character_request)
        assert response.status_code == 200
        
        final_data, _ = parse_streaming_response(response)
        relationships = final_data["character_info"]["relationships"]
        # Should reference existing characters
        assert len(relationships) > 0

    def test_generate_character_details_without_existing_characters(self, client, sample_generate_character_request):
        """Test character generation without existing characters"""
        sample_generate_character_request["existingCharacters"] = []
        response = client.post("/api/v1/generate-character-details", json=sample_generate_character_request)
        assert response.status_code == 200
        
        final_data, _ = parse_streaming_response(response)
        assert final_data is not None

    def test_generate_character_details_fields_not_empty(self, client, sample_generate_character_request):
        """Test that key fields are not empty"""
        response = client.post("/api/v1/generate-character-details", json=sample_generate_character_request)
        assert response.status_code == 200
        
        final_data, _ = parse_streaming_response(response)
        character_info = final_data["character_info"]

        # These fields should have meaningful content
        assert len(character_info["name"]) > 0
        assert len(character_info["physicalAppearance"]) > 10
        assert len(character_info["personality"]) > 10
        assert len(character_info["motivations"]) > 10
        assert len(character_info["fears"]) > 10

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
