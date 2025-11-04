"""
Simple test for character feedback endpoint that doesn't hang.
"""
import pytest
from fastapi.testclient import TestClient


class TestCharacterFeedbackSimple:
    """Simple test for character feedback endpoint"""

    def test_character_feedback_endpoint_exists(self, client):
        """Test that the character feedback endpoint exists and returns proper response"""
        # Simple test data
        data = {
            'structured_context': {
                'plot_elements': [],
                'character_contexts': [],
                'user_requests': [],
                'system_instructions': []
            },
            'plotPoint': 'test'
        }
        
        response = client.post("/api/v1/character-feedback", json=data)
        
        # Should return 200 with proper headers for streaming
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        assert "Cache-Control" in response.headers
        assert "Connection" in response.headers
        
        # Don't try to read the full streaming response as it may hang
        # Just verify the endpoint is working and returns streaming headers
