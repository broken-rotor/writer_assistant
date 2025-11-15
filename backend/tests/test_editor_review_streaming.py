"""
Tests for editor review endpoint streaming functionality.
"""
import pytest
import json
from fastapi.testclient import TestClient


class TestEditorReviewStreaming:
    """Test editor review streaming functionality"""

    def test_editor_review_streaming_response_headers(self, client, sample_editor_review_request):
        """Test that streaming response has correct headers"""
        response = client.post("/api/v1/editor-review", json=sample_editor_review_request)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        assert "Cache-Control" in response.headers
        assert "Connection" in response.headers

    def test_editor_review_streaming_phases(self, client, sample_editor_review_request):
        """Test that all required streaming phases are present"""
        response = client.post("/api/v1/editor-review", json=sample_editor_review_request)
        assert response.status_code == 200
        
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
        
        # Check for required phases
        status_messages = [msg for msg in messages if msg.get('type') == 'status']
        phases = [msg.get('phase') for msg in status_messages]
        
        expected_phases = ['context_processing', 'analyzing', 'generating_suggestions', 'parsing']
        for phase in expected_phases:
            assert phase in phases, f"Missing phase: {phase}"

    def test_editor_review_streaming_progress_values(self, client, sample_editor_review_request):
        """Test that progress values match specification"""
        response = client.post("/api/v1/editor-review", json=sample_editor_review_request)
        assert response.status_code == 200
        
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
        
        # Check progress values
        status_messages = [msg for msg in messages if msg.get('type') == 'status']
        progress_values = [msg.get('progress') for msg in status_messages]
        
        expected_progress = [20, 50, 75, 90]
        for expected in expected_progress:
            assert expected in progress_values, f"Missing progress value: {expected}"

    def test_editor_review_streaming_phase_messages(self, client, sample_editor_review_request):
        """Test that phase messages are meaningful"""
        response = client.post("/api/v1/editor-review", json=sample_editor_review_request)
        assert response.status_code == 200
        
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
        
        # Check phase messages
        status_messages = [msg for msg in messages if msg.get('type') == 'status']
        
        expected_messages = {
            'context_processing': 'Processing chapter and story context...',
            'analyzing': 'Analyzing chapter for narrative issues...',
            'generating_suggestions': 'Generating improvement suggestions...',
            'parsing': 'Processing editor suggestions...'
        }
        
        for msg in status_messages:
            phase = msg.get('phase')
            message = msg.get('message')
            if phase in expected_messages:
                assert message == expected_messages[phase], f"Incorrect message for phase {phase}"

    def test_editor_review_streaming_final_result(self, client, sample_editor_review_request):
        """Test that final result has correct structure"""
        response = client.post("/api/v1/editor-review", json=sample_editor_review_request)
        assert response.status_code == 200
        
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
        
        # Find the result message
        result_messages = [msg for msg in messages if msg.get('type') == 'result']
        assert len(result_messages) == 1, "Should have exactly one result message"
        
        result = result_messages[0]
        assert result.get('status') == 'complete'
        
        data = result.get('data', {})
        assert 'suggestions' in data
        assert isinstance(data['suggestions'], list)
        assert len(data['suggestions']) > 0
        
        # Check suggestion structure
        for suggestion in data['suggestions']:
            assert 'issue' in suggestion
            assert 'suggestion' in suggestion
            assert 'priority' in suggestion

    def test_editor_review_streaming_error_handling(self, client):
        """Test streaming error handling"""
        # Test with invalid request (missing required fields)
        invalid_request = {
            "chapter_number": 1
            # Missing request_context
        }

        response = client.post("/api/v1/editor-review", json=invalid_request)
        # Should return 422 for validation error, not streaming error
        assert response.status_code == 422

    def test_editor_review_streaming_message_order(self, client, sample_editor_review_request):
        """Test that streaming messages are in correct order"""
        response = client.post("/api/v1/editor-review", json=sample_editor_review_request)
        assert response.status_code == 200
        
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
        
        # Check message order
        status_messages = [msg for msg in messages if msg.get('type') == 'status']
        result_messages = [msg for msg in messages if msg.get('type') == 'result']
        
        # Status messages should come before result
        assert len(status_messages) > 0
        assert len(result_messages) == 1
        
        # Progress should be increasing
        progress_values = [msg.get('progress') for msg in status_messages]
        assert progress_values == sorted(progress_values), "Progress values should be in ascending order"

    def test_editor_review_streaming_content_format(self, client, sample_editor_review_request):
        """Test that streaming content follows SSE format"""
        response = client.post("/api/v1/editor-review", json=sample_editor_review_request)
        assert response.status_code == 200
        
        content = response.text
        lines = content.split('\n')
        
        # Check SSE format
        data_lines = [line for line in lines if line.startswith('data: ')]
        assert len(data_lines) > 0, "Should have data lines"
        
        # Each data line should be followed by empty line
        for i, line in enumerate(lines):
            if line.startswith('data: '):
                # Next line should be empty (SSE format requirement)
                if i + 1 < len(lines):
                    assert lines[i + 1] == '', f"Data line at {i} should be followed by empty line"
