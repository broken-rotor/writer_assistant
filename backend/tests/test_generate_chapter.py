"""
Tests for chapter generation endpoint.
"""
import pytest
from fastapi.testclient import TestClient


class TestGenerateChapterEndpoint:
    """Test chapter generation endpoint"""

    def test_generate_chapter_success(self, client, sample_generate_chapter_request):
        """Test successful chapter generation"""
        response = client.post("/api/v1/generate-chapter", json=sample_generate_chapter_request)
        assert response.status_code == 200
        data = response.json()
        assert "chapterText" in data
        assert "wordCount" in data
        assert "metadata" in data

    def test_generate_chapter_response_structure(self, client, sample_generate_chapter_request):
        """Test chapter generation response structure"""
        response = client.post("/api/v1/generate-chapter", json=sample_generate_chapter_request)
        data = response.json()

        assert isinstance(data["chapterText"], str)
        assert isinstance(data["wordCount"], int)
        assert isinstance(data["metadata"], dict)
        assert data["wordCount"] > 0
        assert len(data["chapterText"]) > 0

    def test_generate_chapter_metadata_contains_info(self, client, sample_generate_chapter_request):
        """Test chapter metadata contains expected information"""
        response = client.post("/api/v1/generate-chapter", json=sample_generate_chapter_request)
        metadata = response.json()["metadata"]

        assert "generatedAt" in metadata
        assert "plotPoint" in metadata
        assert "contextMode" in metadata
        assert "processingMode" in metadata
        assert metadata["contextMode"] == "structured"

    def test_generate_chapter_with_empty_plot_point(self, client, sample_generate_chapter_request):
        """Test chapter generation with empty plot point"""
        sample_generate_chapter_request["plotPoint"] = ""
        response = client.post("/api/v1/generate-chapter", json=sample_generate_chapter_request)
        assert response.status_code == 200
        data = response.json()
        assert len(data["chapterText"]) > 0

    def test_generate_chapter_with_multiple_characters(self, client, sample_generate_chapter_request):
        """Test chapter generation with multiple characters"""
        sample_generate_chapter_request["structured_context"]["character_contexts"].append({
            "character_id": "john_doe",
            "character_name": "John Doe",
            "current_state": {
                "emotion": "mysterious",
                "location": "unknown",
                "mental_state": "calculating"
            },
            "recent_actions": ["Appeared at scene", "Watching from shadows"],
            "relationships": {"detective": "unknown"},
            "goals": ["Remain hidden", "Observe"],
            "memories": ["Past encounters", "Secret knowledge"],
            "personality_traits": ["enigmatic", "imposing", "secretive"]
        })
        response = client.post("/api/v1/generate-chapter", json=sample_generate_chapter_request)
        assert response.status_code == 200

    def test_generate_chapter_with_incorporated_feedback(self, client, sample_generate_chapter_request):
        """Test chapter generation with incorporated feedback via structured context"""
        # Add feedback as user requests in structured context
        sample_generate_chapter_request["structured_context"]["user_requests"].extend([
            {
                "type": "modification",
                "content": "Consider this feedback from character1",
                "priority": "high",
                "target": "character1",
                "context": "action_feedback"
            },
            {
                "type": "general", 
                "content": "Add more detail as suggested by rater1",
                "priority": "medium",
                "target": "rater1",
                "context": "suggestion_feedback"
            }
        ])
        response = client.post("/api/v1/generate-chapter", json=sample_generate_chapter_request)
        assert response.status_code == 200
        # Verify that the response includes context metadata
        metadata = response.json()["metadata"]
        assert "processingMode" in metadata

    def test_generate_chapter_word_count_accuracy(self, client, sample_generate_chapter_request):
        """Test that word count is reasonably accurate"""
        response = client.post("/api/v1/generate-chapter", json=sample_generate_chapter_request)
        data = response.json()

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
        import json
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
