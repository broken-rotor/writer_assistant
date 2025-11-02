"""
Tests for flesh out text expansion endpoint streaming functionality.
"""
import pytest
import json
from fastapi.testclient import TestClient


class TestFleshOutStreamingEndpoint:
    """Test flesh out streaming functionality"""

    def test_flesh_out_streaming_response_format(self, client, sample_flesh_out_request):
        """Test that response has correct streaming format"""
        response = client.post("/api/v1/flesh-out", json=sample_flesh_out_request)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    def test_flesh_out_streaming_phases(self, client, sample_flesh_out_request):
        """Test that all required phases are emitted with correct progress values"""
        response = client.post("/api/v1/flesh-out", json=sample_flesh_out_request)
        
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
        
        # Check for status messages with correct phases and progress
        status_messages = [msg for msg in messages if msg.get('type') == 'status']
        
        # Should have 4 status phases
        assert len(status_messages) >= 4
        
        # Check specific phases and progress values
        phases_found = {}
        for msg in status_messages:
            phase = msg.get('phase')
            progress = msg.get('progress')
            if phase:
                phases_found[phase] = progress
        
        # Verify required phases with correct progress values
        assert 'context_processing' in phases_found
        assert phases_found['context_processing'] == 20
        
        assert 'analyzing' in phases_found
        assert phases_found['analyzing'] == 40
        
        assert 'expanding' in phases_found
        assert phases_found['expanding'] == 70
        
        assert 'finalizing' in phases_found
        assert phases_found['finalizing'] == 90

    def test_flesh_out_streaming_final_result(self, client, sample_flesh_out_request):
        """Test that final result contains correct data structure"""
        response = client.post("/api/v1/flesh-out", json=sample_flesh_out_request)
        
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
        assert len(result_messages) == 1
        
        result_data = result_messages[0].get('data', {})
        
        # Verify result structure
        assert 'fleshedOutText' in result_data
        assert 'originalText' in result_data
        assert 'metadata' in result_data
        assert 'context_metadata' in result_data
        
        # Verify metadata structure
        metadata = result_data['metadata']
        assert 'expandedAt' in metadata
        assert 'originalLength' in metadata
        assert 'expandedLength' in metadata
        assert 'contextType' in metadata
        assert 'contextMode' in metadata
        assert 'structuredContextProvided' in metadata
        assert 'processingMode' in metadata
        
        # Verify data types
        assert isinstance(result_data['fleshedOutText'], str)
        assert isinstance(result_data['originalText'], str)
        assert isinstance(metadata, dict)
        assert isinstance(metadata['originalLength'], int)
        assert isinstance(metadata['expandedLength'], int)

    def test_flesh_out_streaming_status_messages(self, client, sample_flesh_out_request):
        """Test that status messages have correct structure"""
        response = client.post("/api/v1/flesh-out", json=sample_flesh_out_request)
        
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
        
        # Check status messages structure
        status_messages = [msg for msg in messages if msg.get('type') == 'status']
        
        for msg in status_messages:
            assert 'type' in msg
            assert msg['type'] == 'status'
            assert 'phase' in msg
            assert 'message' in msg
            assert 'progress' in msg
            assert isinstance(msg['phase'], str)
            assert isinstance(msg['message'], str)
            assert isinstance(msg['progress'], int)
            assert 0 <= msg['progress'] <= 100

    def test_flesh_out_streaming_error_handling(self, client):
        """Test error handling in streaming mode"""
        # Create invalid request (missing required field)
        invalid_request = {
            "textToFleshOut": "",  # Empty text should cause validation error
            "context": "test",
            "structured_context": {
                "plot_elements": {},
                "character_contexts": {},
                "user_requests": {},
                "system_instructions": {}
            }
        }
        
        response = client.post("/api/v1/flesh-out", json=invalid_request)
        
        # Validation errors should return 422 before streaming starts
        assert response.status_code == 422
        
        # Should return JSON error response, not streaming
        error_data = response.json()
        assert "detail" in error_data

    def test_flesh_out_streaming_complete_flow(self, client, sample_flesh_out_request):
        """Test complete streaming flow from start to finish"""
        response = client.post("/api/v1/flesh-out", json=sample_flesh_out_request)
        
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
        
        # Should have at least 5 messages (4 status + 1 result)
        assert len(messages) >= 5
        
        # Check message order and types
        message_types = [msg.get('type') for msg in messages]
        
        # Should have status messages followed by result
        status_count = message_types.count('status')
        result_count = message_types.count('result')
        
        assert status_count >= 4  # At least 4 status phases
        assert result_count == 1  # Exactly 1 result
        
        # Result should be the last message
        assert message_types[-1] == 'result'
        
        # Status messages should come before result
        result_index = message_types.index('result')
        for i in range(result_index):
            assert message_types[i] == 'status'
