"""
Tests for agentic chapter modification endpoint.

This tests the /agentic-modify-chapter endpoint which uses iterative
generation-evaluation cycles to ensure feedback is properly incorporated.
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


def extract_all_events_from_streaming_response(response):
    """Extract all SSE events from streaming response."""
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    # Parse SSE content
    content = response.text
    lines = content.split('\n')

    # Extract data lines
    data_lines = [line for line in lines if line.startswith('data: ')]

    # Parse JSON from data lines
    events = []
    for line in data_lines:
        try:
            data = json.loads(line[6:])  # Remove 'data: ' prefix
            events.append(data)
        except json.JSONDecodeError:
            pass

    return events


class TestAgenticModifyChapterEndpoint:
    """Test agentic chapter modification endpoint"""

    def test_agentic_modify_chapter_success(self, client, sample_modify_chapter_request):
        """Test successful agentic chapter modification"""
        response = client.post("/api/v1/agentic-modify-chapter", json=sample_modify_chapter_request)
        data = extract_final_result_from_streaming_response(response)

        # Should have content in the result
        assert "content" in data
        assert len(data["content"]) > 0
        assert "status" in data
        assert data["status"] == "success"

    def test_agentic_modify_chapter_response_structure(self, client, sample_modify_chapter_request):
        """Test agentic modify chapter response structure"""
        response = client.post("/api/v1/agentic-modify-chapter", json=sample_modify_chapter_request)
        data = extract_final_result_from_streaming_response(response)

        # Validate response structure
        assert isinstance(data["content"], str)
        assert len(data["content"]) > 0
        assert "iterations_used" in data
        assert isinstance(data["iterations_used"], int)
        assert data["iterations_used"] >= 1
        assert data["iterations_used"] <= 3  # Max configured iterations
        assert "evaluation_feedback" in data
        assert "status" in data

    def test_agentic_modify_chapter_includes_content(self, client, sample_modify_chapter_request):
        """Test that modified chapter contains expected content"""
        response = client.post("/api/v1/agentic-modify-chapter", json=sample_modify_chapter_request)
        data = extract_final_result_from_streaming_response(response)
        modified_text = data["content"]

        # Modified chapter should contain meaningful content
        assert len(modified_text) > 100
        # Should maintain some reference to the story
        assert "Detective Chen" in modified_text or "Chen" in modified_text or "detective" in modified_text.lower()

    def test_agentic_modify_chapter_streaming_phases(self, client, sample_modify_chapter_request):
        """Test that streaming response includes all expected phases"""
        response = client.post("/api/v1/agentic-modify-chapter", json=sample_modify_chapter_request)
        events = extract_all_events_from_streaming_response(response)

        # Extract phase names from status events
        phases = [event.get('phase') for event in events if event.get('type') == 'status']

        # Should include context processing phase
        assert 'context_processing' in phases
        assert 'modifying' in phases

        # Should include generation and evaluation phases
        assert any('generating' in phase for phase in phases)
        assert any('evaluating' in phase for phase in phases)

        # Final result should be present
        result_events = [event for event in events if event.get('type') == 'result']
        assert len(result_events) == 1

    def test_agentic_modify_chapter_iteration_tracking(self, client, sample_modify_chapter_request):
        """Test that iterations are tracked in status updates"""
        response = client.post("/api/v1/agentic-modify-chapter", json=sample_modify_chapter_request)
        events = extract_all_events_from_streaming_response(response)

        # Look for iteration mentions in status messages
        status_messages = [
            event.get('message', '')
            for event in events
            if event.get('type') == 'status'
        ]

        # Should have iteration information in some messages
        iteration_messages = [msg for msg in status_messages if 'Iteration' in msg]
        assert len(iteration_messages) > 0

    def test_agentic_modify_chapter_with_user_feedback(self, client, sample_modify_chapter_request):
        """Test that chapter is modified according to user feedback"""
        # Set specific user feedback
        sample_modify_chapter_request["user_feedback"] = "Add more action and suspense"

        response = client.post("/api/v1/agentic-modify-chapter", json=sample_modify_chapter_request)
        data = extract_final_result_from_streaming_response(response)
        modified_chapter = data["content"]

        # Modified chapter should have content
        assert len(modified_chapter) > 0
        assert data["status"] == "success"

    def test_agentic_modify_chapter_with_character_feedback(self, client, sample_modify_chapter_request):
        """Test agentic modification with character feedback"""
        # Add character feedback items
        sample_modify_chapter_request["character_feedback"] = [
            {
                "character_name": "Detective Chen",
                "type": "emotion",
                "content": "Feels conflicted about the case"
            },
            {
                "character_name": "Detective Chen",
                "type": "action",
                "content": "Examines the evidence more carefully"
            }
        ]

        response = client.post("/api/v1/agentic-modify-chapter", json=sample_modify_chapter_request)
        data = extract_final_result_from_streaming_response(response)

        assert "content" in data
        assert len(data["content"]) > 0
        assert data["status"] == "success"

    def test_agentic_modify_chapter_with_rater_feedback(self, client, sample_modify_chapter_request):
        """Test agentic modification with rater feedback"""
        # Add rater feedback items
        sample_modify_chapter_request["rater_feedback"] = [
            {
                "rater_name": "Pacing Expert",
                "content": "The scene moves too quickly. Add more buildup."
            }
        ]

        response = client.post("/api/v1/agentic-modify-chapter", json=sample_modify_chapter_request)
        data = extract_final_result_from_streaming_response(response)

        assert "content" in data
        assert len(data["content"]) > 0

    def test_agentic_modify_chapter_with_editor_feedback(self, client, sample_modify_chapter_request):
        """Test agentic modification with editor feedback"""
        # Add editor feedback items
        sample_modify_chapter_request["editor_feedback"] = [
            {
                "content": "Strengthen the dialogue between characters"
            },
            {
                "content": "Add more sensory details to the scene"
            }
        ]

        response = client.post("/api/v1/agentic-modify-chapter", json=sample_modify_chapter_request)
        data = extract_final_result_from_streaming_response(response)

        assert "content" in data
        assert len(data["content"]) > 0

    def test_agentic_modify_chapter_with_combined_feedback(self, client, sample_modify_chapter_request):
        """Test agentic modification with multiple types of feedback"""
        # Combine all feedback types
        sample_modify_chapter_request["user_feedback"] = "Make it more intense"
        sample_modify_chapter_request["character_feedback"] = [
            {
                "character_name": "Detective Chen",
                "type": "emotion",
                "content": "Feels anxious"
            }
        ]
        sample_modify_chapter_request["rater_feedback"] = [
            {
                "rater_name": "Style Coach",
                "content": "Use more vivid language"
            }
        ]
        sample_modify_chapter_request["editor_feedback"] = [
            {
                "content": "Improve pacing"
            }
        ]

        response = client.post("/api/v1/agentic-modify-chapter", json=sample_modify_chapter_request)
        data = extract_final_result_from_streaming_response(response)

        assert "content" in data
        assert len(data["content"]) > 0
        assert data["status"] == "success"

    def test_agentic_modify_chapter_evaluation_feedback_present(self, client, sample_modify_chapter_request):
        """Test that evaluation feedback is included in response"""
        response = client.post("/api/v1/agentic-modify-chapter", json=sample_modify_chapter_request)
        data = extract_final_result_from_streaming_response(response)

        assert "evaluation_feedback" in data
        assert isinstance(data["evaluation_feedback"], str)
        assert len(data["evaluation_feedback"]) > 0

    def test_agentic_modify_chapter_progress_updates(self, client, sample_modify_chapter_request):
        """Test that progress updates are provided"""
        response = client.post("/api/v1/agentic-modify-chapter", json=sample_modify_chapter_request)
        events = extract_all_events_from_streaming_response(response)

        # Extract progress values from status events
        progress_values = [
            event.get('progress', 0)
            for event in events
            if event.get('type') == 'status' and 'progress' in event
        ]

        # Should have multiple progress updates
        assert len(progress_values) > 0
        # Progress should be between 0 and 100
        assert all(0 <= p <= 100 for p in progress_values)
        # Progress should generally increase (allow some flexibility)
        assert progress_values[0] < progress_values[-1]

    def test_agentic_modify_chapter_invalid_chapter_number(self, client, sample_modify_chapter_request):
        """Test error handling for invalid chapter number"""
        # Set invalid chapter number
        sample_modify_chapter_request["chapter_number"] = 999

        response = client.post("/api/v1/agentic-modify-chapter", json=sample_modify_chapter_request)
        events = extract_all_events_from_streaming_response(response)

        # Should have error event
        error_events = [event for event in events if event.get('type') == 'error']
        assert len(error_events) > 0

    def test_agentic_modify_chapter_empty_feedback(self, client, sample_modify_chapter_request):
        """Test agentic modification with no feedback (should still work)"""
        # Clear all feedback
        sample_modify_chapter_request["user_feedback"] = ""
        sample_modify_chapter_request["character_feedback"] = []
        sample_modify_chapter_request["rater_feedback"] = []
        sample_modify_chapter_request["editor_feedback"] = []

        response = client.post("/api/v1/agentic-modify-chapter", json=sample_modify_chapter_request)

        # Should still return a result (might just return similar content)
        # The endpoint should handle this gracefully
        assert response.status_code == 200

    def test_agentic_modify_chapter_maintains_chapter_structure(self, client, sample_modify_chapter_request):
        """Test that modified chapter maintains basic structure"""
        response = client.post("/api/v1/agentic-modify-chapter", json=sample_modify_chapter_request)
        data = extract_final_result_from_streaming_response(response)
        modified_chapter = data["content"]

        # Should have substantial content
        assert len(modified_chapter) > 200
        # Should be proper prose (has sentences)
        assert '.' in modified_chapter or '!' in modified_chapter or '?' in modified_chapter
