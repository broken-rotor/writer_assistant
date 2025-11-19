"""
Tests for rater feedback endpoint.
"""
import json
import pytest
from fastapi.testclient import TestClient


class TestRaterFeedbackEndpoint:
    """Test rater feedback generation endpoint"""

    def test_rater_feedback_success(self, client, sample_rater_feedback_request):
        """Test successful rater feedback generation (now streaming)"""
        response = client.post("/api/v1/rater-feedback", json=sample_rater_feedback_request)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Parse streaming response to get final result
        events = []
        for line in response.text.split('\n'):
            if line.startswith('data: '):
                try:
                    event_data = json.loads(line[6:])  # Remove 'data: ' prefix
                    events.append(event_data)
                except json.JSONDecodeError:
                    pass
        
        # Find the result event
        result_event = next((e for e in events if e.get('type') == 'result'), None)
        assert result_event is not None
        data = result_event['data']
        assert "raterName" in data
        assert "feedback" in data

    def test_rater_feedback_response_structure(self, client, sample_rater_feedback_request):
        """Test rater feedback response has correct structure (streaming)"""
        response = client.post("/api/v1/rater-feedback", json=sample_rater_feedback_request)
        assert response.status_code == 200
        
        # Parse streaming response to get final result
        events = []
        for line in response.text.split('\n'):
            if line.startswith('data: '):
                try:
                    event_data = json.loads(line[6:])
                    events.append(event_data)
                except json.JSONDecodeError:
                    pass
        
        result_event = next((e for e in events if e.get('type') == 'result'), None)
        assert result_event is not None
        data = result_event['data']

        feedback = data["feedback"]
        assert "opinion" in feedback
        assert "suggestions" in feedback
        assert isinstance(feedback["opinion"], str)
        assert isinstance(feedback["suggestions"], list)

    def test_rater_feedback_has_suggestions(self, client, sample_rater_feedback_request):
        """Test rater feedback includes suggestions (streaming)"""
        response = client.post("/api/v1/rater-feedback", json=sample_rater_feedback_request)
        
        # Parse streaming response
        events = []
        for line in response.text.split('\n'):
            if line.startswith('data: '):
                try:
                    event_data = json.loads(line[6:])
                    events.append(event_data)
                except json.JSONDecodeError:
                    pass
        
        result_event = next((e for e in events if e.get('type') == 'result'), None)
        suggestions = result_event['data']["feedback"]["suggestions"]

        assert len(suggestions) > 0
        for suggestion in suggestions:
            assert isinstance(suggestion, dict)
            assert "issue" in suggestion
            assert "suggestion" in suggestion
            assert "priority" in suggestion
            assert isinstance(suggestion["issue"], str)
            assert isinstance(suggestion["suggestion"], str)
            assert suggestion["priority"] in ["high", "medium", "low"]

    def test_rater_feedback_opinion_not_empty(self, client, sample_rater_feedback_request):
        """Test rater opinion is not empty (streaming)"""
        response = client.post("/api/v1/rater-feedback", json=sample_rater_feedback_request)
        
        # Parse streaming response
        events = []
        for line in response.text.split('\n'):
            if line.startswith('data: '):
                try:
                    event_data = json.loads(line[6:])
                    events.append(event_data)
                except json.JSONDecodeError:
                    pass
        
        result_event = next((e for e in events if e.get('type') == 'result'), None)
        opinion = result_event['data']["feedback"]["opinion"]
        assert len(opinion) > 0

    def test_rater_feedback_missing_rater_name(self, client):
        """Test rater feedback fails without rater name"""
        from datetime import datetime
        from app.models.request_context import RequestContext, StoryConfiguration, SystemPrompts, WorldbuildingInfo, StoryOutline, RequestContextMetadata

        request_context = RequestContext(
            configuration=StoryConfiguration(
                system_prompts=SystemPrompts(
                    main_prefix="Test",
                    main_suffix="Test",
                    assistant_prompt="Test",
                    editor_prompt="Test"
                )
            ),
            worldbuilding=WorldbuildingInfo(content="Test"),
            story_outline=StoryOutline(summary="Test", status="draft", content="Test"),
            context_metadata=RequestContextMetadata(
                story_id="test",
                story_title="Test",
                version="1.0",
                created_at=datetime.now()
            )
        )

        invalid_request = {
            "request_context": request_context.model_dump(mode='json'),
            "plotPoint": "Test"
            # Missing raterName field
        }
        response = client.post("/api/v1/rater-feedback", json=invalid_request)
        assert response.status_code == 422

    def test_rater_feedback_with_incorporated_feedback(self, client, sample_rater_feedback_request):
        """Test rater feedback with incorporated feedback items (streaming)"""
        sample_rater_feedback_request["incorporatedFeedback"] = [
            {"source": "character", "type": "action", "content": "Test", "incorporated": True}
        ]
        response = client.post("/api/v1/rater-feedback", json=sample_rater_feedback_request)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
