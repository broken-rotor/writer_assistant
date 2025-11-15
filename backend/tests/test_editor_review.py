"""
Tests for editor review endpoint.
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


class TestEditorReviewEndpoint:
    """Test editor review endpoint"""

    def test_editor_review_success(self, client, sample_editor_review_request):
        """Test successful editor review"""
        response = client.post("/api/v1/editor-review", json=sample_editor_review_request)
        data = extract_final_result_from_streaming_response(response)
        assert "suggestions" in data

    def test_editor_review_response_structure(self, client, sample_editor_review_request):
        """Test editor review response structure"""
        response = client.post("/api/v1/editor-review", json=sample_editor_review_request)
        data = extract_final_result_from_streaming_response(response)

        assert isinstance(data["suggestions"], list)
        assert len(data["suggestions"]) > 0

    def test_editor_review_suggestion_structure(self, client, sample_editor_review_request):
        """Test individual suggestion structure"""
        response = client.post("/api/v1/editor-review", json=sample_editor_review_request)
        data = extract_final_result_from_streaming_response(response)
        suggestions = data["suggestions"]

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
        data = extract_final_result_from_streaming_response(response)
        suggestions = data["suggestions"]

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
        data = extract_final_result_from_streaming_response(response)
        assert "suggestions" in data

    def test_editor_review_missing_chapter(self, client):
        """Test editor review fails without chapter_number"""
        from app.models.request_context import RequestContext, StoryConfiguration, SystemPrompts, RequestContextMetadata
        from datetime import datetime

        # Create a minimal request_context without chapters
        request_context = RequestContext(
            configuration=StoryConfiguration(
                system_prompts=SystemPrompts(
                    main_prefix="Test",
                    main_suffix="Test",
                    assistant_prompt="Test",
                    editor_prompt="Test"
                )
            ),
            context_metadata=RequestContextMetadata(
                story_id="test",
                story_title="Test",
                version="1.0",
                created_at=datetime.now()
            )
        )

        # Missing chapter_number field
        invalid_request = {
            "request_context": request_context.model_dump(mode='json')
        }
        response = client.post("/api/v1/editor-review", json=invalid_request)
        assert response.status_code == 422
