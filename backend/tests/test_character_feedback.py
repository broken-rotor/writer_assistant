"""
Tests for character feedback endpoint.
"""
import pytest
import json
from fastapi.testclient import TestClient


def extract_final_result_from_streaming_response(response):
    """Helper function to extract the final result from a streaming SSE response."""
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    
    # Parse SSE content
    content = response.text
    lines = content.split('\n')
    
    # Should contain data lines
    data_lines = [line for line in lines if line.startswith('data: ')]
    assert len(data_lines) > 0
    
    # Parse JSON from data lines
    messages = []
    for line in data_lines:
        try:
            data = json.loads(line[6:])  # Remove 'data: ' prefix
            messages.append(data)
        except json.JSONDecodeError:
            pass
    
    # Find the result message
    result_messages = [msg for msg in messages if msg.get('type') == 'result']
    assert len(result_messages) > 0, "No result message found in streaming response"
    
    return result_messages[0].get('data', {})


class TestCharacterFeedbackEndpoint:
    """Test character feedback generation endpoint"""

    def test_character_feedback_success(self, client, sample_character_feedback_request):
        """Test successful character feedback generation"""
        response = client.post("/api/v1/character-feedback", json=sample_character_feedback_request)
        data = extract_final_result_from_streaming_response(response)
        assert "characterName" in data
        assert "feedback" in data

    def test_character_feedback_response_structure(self, client, sample_character_feedback_request):
        """Test character feedback response has correct structure"""
        response = client.post("/api/v1/character-feedback", json=sample_character_feedback_request)
        data = extract_final_result_from_streaming_response(response)

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
        data = extract_final_result_from_streaming_response(response)
        feedback = data["feedback"]

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

    def test_character_feedback_streaming_response(self, client, sample_character_feedback_request):
        """Test that the endpoint returns a streaming response with proper SSE format"""
        response = client.post("/api/v1/character-feedback", json=sample_character_feedback_request)
        
        # Should return 200 for streaming
        assert response.status_code == 200
        
        # Should have proper SSE headers
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        assert "no-cache" in response.headers.get("cache-control", "")
        
        # Parse SSE content
        content = response.text
        lines = content.split('\n')
        
        # Should contain data lines
        data_lines = [line for line in lines if line.startswith('data: ')]
        assert len(data_lines) > 0
        
        # Parse JSON from data lines
        messages = []
        for line in data_lines:
            try:
                data = json.loads(line[6:])  # Remove 'data: ' prefix
                messages.append(data)
            except json.JSONDecodeError:
                pass
        
        # Should have at least status and result messages
        assert len(messages) > 0
        
        # Check for expected message types
        message_types = [msg.get('type') for msg in messages]
        assert 'status' in message_types
        
        # Check for expected phases in status messages
        status_messages = [msg for msg in messages if msg.get('type') == 'status']
        phases = [msg.get('phase') for msg in status_messages]
        expected_phases = ['context_processing', 'generating', 'parsing']
        for expected_phase in expected_phases:
            assert expected_phase in phases, f"Expected phase '{expected_phase}' not found in streaming response"
        
        # If we have a result message, verify its structure
        result_messages = [msg for msg in messages if msg.get('type') == 'result']
        if result_messages:
            result_data = result_messages[0].get('data', {})
            assert 'characterName' in result_data
            assert 'feedback' in result_data
