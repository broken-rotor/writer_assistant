"""
Tests for chapter generation endpoint.
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


class TestGenerateChapterEndpoint:
    """Test chapter generation endpoint"""

    def test_generate_chapter_success(self, client, sample_generate_chapter_request):
        """Test successful chapter generation"""
        response = client.post("/api/v1/generate-chapter", json=sample_generate_chapter_request)
        data = extract_final_result_from_streaming_response(response)
        assert "chapterText" in data
        assert "wordCount" in data
        assert "metadata" in data

    def test_generate_chapter_response_structure(self, client, sample_generate_chapter_request):
        """Test chapter generation response structure"""
        response = client.post("/api/v1/generate-chapter", json=sample_generate_chapter_request)
        data = extract_final_result_from_streaming_response(response)

        assert isinstance(data["chapterText"], str)
        assert isinstance(data["wordCount"], int)
        assert isinstance(data["metadata"], dict)
        assert data["wordCount"] > 0
        assert len(data["chapterText"]) > 0

    def test_generate_chapter_metadata_contains_info(self, client, sample_generate_chapter_request):
        """Test chapter metadata contains expected information"""
        response = client.post("/api/v1/generate-chapter", json=sample_generate_chapter_request)
        data = extract_final_result_from_streaming_response(response)
        metadata = data["metadata"]

        assert "generatedAt" in metadata
        assert "plotPoint" in metadata
        assert "contextMode" in metadata
        assert "processingMode" in metadata
        assert metadata["contextMode"] == "structured"

    def test_generate_chapter_with_empty_plot_point(self, client, sample_generate_chapter_request):
        """Test chapter generation with empty plot point"""
        sample_generate_chapter_request["plotPoint"] = ""
        response = client.post("/api/v1/generate-chapter", json=sample_generate_chapter_request)
        data = extract_final_result_from_streaming_response(response)
        assert len(data["chapterText"]) > 0

    def test_generate_chapter_with_multiple_characters(self, client, sample_generate_chapter_request):
        """Test chapter generation with multiple characters"""
        from datetime import datetime
        
        # Add another character to the RequestContext
        sample_generate_chapter_request["request_context"]["characters"].append({
            "id": "john_doe",
            "name": "John Doe",
            "basic_bio": "A mysterious figure who appears at crime scenes, enigmatic and imposing with secretive motives.",
            "creation_source": "user",
            "last_modified": datetime.now().isoformat()
        })
        
        response = client.post("/api/v1/generate-chapter", json=sample_generate_chapter_request)
        data = extract_final_result_from_streaming_response(response)

    def test_generate_chapter_with_incorporated_feedback(self, client, sample_generate_chapter_request):
        """Test chapter generation with incorporated feedback via worldbuilding content"""
        # Add feedback information to the worldbuilding content
        original_content = sample_generate_chapter_request["request_context"]["worldbuilding"]["content"]
        feedback_content = (
            f"{original_content} "
            "FEEDBACK TO INCORPORATE: Consider adding more atmospheric details as suggested by reviewers. "
            "Focus on character emotions and environmental descriptions to enhance the scene."
        )
        sample_generate_chapter_request["request_context"]["worldbuilding"]["content"] = feedback_content
        
        response = client.post("/api/v1/generate-chapter", json=sample_generate_chapter_request)
        data = extract_final_result_from_streaming_response(response)
        # Verify that the response includes context metadata
        metadata = data["metadata"]
        assert "processingMode" in metadata

    def test_generate_chapter_word_count_accuracy(self, client, sample_generate_chapter_request):
        """Test that word count is reasonably accurate"""
        response = client.post("/api/v1/generate-chapter", json=sample_generate_chapter_request)
        data = extract_final_result_from_streaming_response(response)

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

    def test_generate_chapter_streaming_response(self, client, sample_generate_chapter_request):
        """Test that the endpoint returns a streaming response with proper SSE format"""
        response = client.post("/api/v1/generate-chapter", json=sample_generate_chapter_request)
        
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
        
        # If we have a result message, verify its structure
        result_messages = [msg for msg in messages if msg.get('type') == 'result']
        if result_messages:
            result_data = result_messages[0].get('data', {})
            assert 'chapterText' in result_data
            assert 'wordCount' in result_data
            assert 'metadata' in result_data
