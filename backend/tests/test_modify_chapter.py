"""
Tests for chapter modification endpoint.
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


class TestModifyChapterEndpoint:
    """Test chapter modification endpoint"""

    def test_modify_chapter_success(self, client, sample_modify_chapter_request):
        """Test successful chapter modification"""
        response = client.post("/api/v1/modify-chapter", json=sample_modify_chapter_request)
        data = extract_final_result_from_streaming_response(response)
        assert "modifiedChapter" in data

    def test_modify_chapter_response_structure(self, client, sample_modify_chapter_request):
        """Test modify chapter response structure"""
        response = client.post("/api/v1/modify-chapter", json=sample_modify_chapter_request)
        data = extract_final_result_from_streaming_response(response)

        assert isinstance(data["modifiedChapter"], str)
        assert len(data["modifiedChapter"]) > 0

    def test_modify_chapter_includes_original_content(self, client, sample_modify_chapter_request):
        """Test that modified chapter is returned"""
        response = client.post("/api/v1/modify-chapter", json=sample_modify_chapter_request)
        data = extract_final_result_from_streaming_response(response)
        modified_text = data["modifiedChapter"]

        # Modified chapter should contain meaningful content
        assert len(modified_text) > 0
        assert "Detective Chen" in modified_text or "Chen" in modified_text

    def test_modify_chapter_with_user_request(self, client, sample_modify_chapter_request):
        """Test that chapter is modified according to user request"""
        user_request = sample_modify_chapter_request["userRequest"]
        response = client.post("/api/v1/modify-chapter", json=sample_modify_chapter_request)
        data = extract_final_result_from_streaming_response(response)
        modified_chapter = data["modifiedChapter"]

        # Modified chapter should have content
        assert len(modified_chapter) > 0

    def test_modify_chapter_with_long_user_request(self, client, sample_modify_chapter_request):
        """Test modify chapter with long user request"""
        long_request = "Please modify this chapter by " + "adding more detail " * 50
        sample_modify_chapter_request["userRequest"] = long_request
        response = client.post("/api/v1/modify-chapter", json=sample_modify_chapter_request)
        data = extract_final_result_from_streaming_response(response)
        assert "modifiedChapter" in data

    def test_modify_chapter_streaming_phases(self, client, sample_modify_chapter_request):
        """Test that streaming response includes all expected phases"""
        response = client.post("/api/v1/modify-chapter", json=sample_modify_chapter_request)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Parse SSE content
        content = response.text
        lines = content.split('\n')
        data_lines = [line for line in lines if line.startswith('data: ')]
        
        # Parse JSON from data lines
        messages = []
        for line in data_lines:
            try:
                data = json.loads(line[6:])  # Remove 'data: ' prefix
                messages.append(data)
            except json.JSONDecodeError:
                pass
        
        # Check for expected phases
        status_messages = [msg for msg in messages if msg.get('type') == 'status']
        phases = [msg.get('phase') for msg in status_messages]
        
        expected_phases = ['context_processing', 'modifying', 'finalizing']
        for expected_phase in expected_phases:
            assert expected_phase in phases, f"Missing phase: {expected_phase}"
        
        # Check for final result
        result_messages = [msg for msg in messages if msg.get('type') == 'result']
        assert len(result_messages) == 1, "Should have exactly one result message"
        assert result_messages[0].get('status') == 'complete'

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
