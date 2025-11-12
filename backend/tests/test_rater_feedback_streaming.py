"""
Tests for streaming rater feedback endpoint.
"""
import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from app.main import app
from app.models.generation_models import RaterFeedbackRequest
from app.models.streaming_models import StreamingPhase


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_streaming_request():
    """Sample request for streaming rater feedback using new RequestContext format."""
    from datetime import datetime
    from app.models.request_context import RequestContext, StoryConfiguration, SystemPrompts, WorldbuildingInfo, StoryOutline, RequestContextMetadata, CharacterDetails
    
    request_context = RequestContext(
        configuration=StoryConfiguration(
            system_prompts=SystemPrompts(
                main_prefix="You are a creative writing assistant.",
                main_suffix="Write engaging prose with vivid descriptions.",
                assistant_prompt="Focus on creating compelling narrative scenes.",
                editor_prompt="Review and enhance the chapter content."
            )
        ),
        worldbuilding=WorldbuildingInfo(
            content="A fantasy adventure story with magical elements and hidden mysteries."
        ),
        story_outline=StoryOutline(
            summary="A hero's journey through a mysterious world filled with secrets",
            status="draft",
            content="The story follows a hero who discovers hidden doors and magical secrets."
        ),
        context_metadata=RequestContextMetadata(
            story_id="streaming_rater_test_001",
            story_title="The Hidden Door Adventure",
            version="1.0",
            created_at=datetime.now(),
            total_characters=1,
            total_chapters=1,
            total_word_count=800,
            context_size_estimate=400
        ),
        characters=[
            CharacterDetails(
                id="hero_character",
                name="The Hero",
                basic_bio="A brave adventurer seeking hidden truths and magical secrets.",
                creation_source="user",
                last_modified=datetime.now()
            )
        ]
    )
    
    return {
        "raterPrompt": "You are a story critic. Evaluate this plot point.",
        "plotPoint": "The hero discovers a hidden door in the basement.",
        "compose_phase": "plot_outline",
        "phase_context": {},
        "request_context": request_context.model_dump(mode='json')
    }


def test_streaming_endpoint_exists(client):
    """Test that the streaming endpoint exists and accepts POST requests."""
    # This will fail if the endpoint doesn't exist or has wrong method
    response = client.post("/api/v1/rater-feedback", json={})
    # We expect some response (even if it's an error due to missing data)
    assert response.status_code in [200, 422, 500]  # 422 for validation error, 500 for missing LLM


@patch('app.services.llm_inference.get_llm')
@patch('app.services.unified_context_processor.get_unified_context_processor')
def test_streaming_rater_feedback_success(mock_context_processor, mock_get_llm, client, sample_streaming_request):
    """Test successful streaming rater feedback generation."""
    # Mock LLM
    mock_llm = Mock()
    mock_llm.chat_completion_stream.return_value = [
        '{"opinion": "This is a good plot point.',
        ' It creates mystery and intrigue.",',
        ' "suggestions": ["Add more sensory details",',
        ' "Consider the character\'s emotional state",',
        ' "Describe the door\'s appearance"]}'
    ]
    mock_get_llm.return_value = mock_llm
    
    # Mock context processor
    mock_processor = Mock()
    mock_context_result = Mock()
    mock_context_result.system_prompt = "You are a story critic."
    mock_context_result.user_message = "Evaluate this plot point: The hero discovers a hidden door."
    mock_context_result.context_metadata = {"tokens": 100}
    mock_context_result.optimization_applied = False
    mock_context_result.processing_mode = "structured"
    mock_context_result.total_tokens = 100
    mock_processor.process_rater_feedback_context.return_value = mock_context_result
    mock_context_processor.return_value = mock_processor
    
    # Make streaming request
    response = client.post("/api/v1/rater-feedback", json=sample_streaming_request)
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    
    # Parse streaming response
    events = []
    for line in response.text.split('\n'):
        if line.startswith('data: '):
            try:
                event_data = json.loads(line[6:])  # Remove 'data: ' prefix
                events.append(event_data)
            except json.JSONDecodeError:
                pass
    
    # Verify we got the expected events
    assert len(events) >= 5  # At least 4 status events + 1 result event
    
    # Check that we have status events for each phase
    status_events = [e for e in events if e.get('type') == 'status']
    result_events = [e for e in events if e.get('type') == 'result']
    
    assert len(status_events) >= 4  # context_processing, evaluating, generating_feedback, parsing
    assert len(result_events) == 1  # One final result
    
    # Verify phase progression
    phases = [e.get('phase') for e in status_events]
    expected_phases = [
        StreamingPhase.CONTEXT_PROCESSING,
        StreamingPhase.EVALUATING,
        StreamingPhase.GENERATING_FEEDBACK,
        StreamingPhase.PARSING
    ]
    
    for expected_phase in expected_phases:
        assert expected_phase in phases
    
    # Verify final result
    final_result = result_events[0]
    assert final_result['type'] == 'result'
    assert final_result['status'] == 'complete'
    assert 'data' in final_result
    
    result_data = final_result['data']
    assert 'raterName' in result_data
    assert 'feedback' in result_data
    assert 'opinion' in result_data['feedback']
    assert 'suggestions' in result_data['feedback']


def test_streaming_rater_feedback_no_llm(client, sample_streaming_request):
    """Test streaming rater feedback when LLM is not available."""
    # Override the global mock to return None
    with patch('app.services.llm_inference.get_llm', return_value=None):
        with patch('app.api.v1.endpoints.rater_feedback.get_llm', return_value=None):
            response = client.post("/api/v1/rater-feedback", json=sample_streaming_request)
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
            
            # Parse streaming response
            events = []
            for line in response.text.split('\n'):
                if line.startswith('data: '):
                    try:
                        event_data = json.loads(line[6:])
                        events.append(event_data)
                    except json.JSONDecodeError:
                        pass
            
            # Should have at least one error event
            error_events = [e for e in events if e.get('type') == 'error']
            assert len(error_events) >= 1
            assert 'LLM not initialized' in error_events[0]['message']


def test_streaming_rater_feedback_invalid_request(client):
    """Test streaming rater feedback with invalid request data."""
    invalid_request = {"invalid": "data"}
    
    response = client.post("/api/v1/rater-feedback", json=invalid_request)
    
    # Should return validation error
    assert response.status_code == 422


def test_streaming_rater_feedback_llm_error(client, sample_streaming_request):
    """Test streaming rater feedback when LLM throws an error."""
    # Mock LLM that throws an error
    mock_llm = Mock()
    mock_llm.chat_completion_stream.side_effect = Exception("LLM generation failed")
    
    # Mock context processor
    mock_processor = Mock()
    mock_context_result = Mock()
    mock_context_result.system_prompt = "You are a story critic."
    mock_context_result.user_message = "Evaluate this plot point."
    mock_context_result.context_metadata = {"tokens": 100}
    mock_context_result.optimization_applied = False
    mock_processor.process_rater_feedback_context.return_value = mock_context_result
    
    # Override the global mocks
    with patch('app.services.llm_inference.get_llm', return_value=mock_llm):
        with patch('app.api.v1.endpoints.rater_feedback.get_llm', return_value=mock_llm):
            with patch('app.services.unified_context_processor.get_unified_context_processor', return_value=mock_processor):
                response = client.post("/api/v1/rater-feedback", json=sample_streaming_request)
                
                assert response.status_code == 200
                assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
                
                # Parse streaming response
                events = []
                for line in response.text.split('\n'):
                    if line.startswith('data: '):
                        try:
                            event_data = json.loads(line[6:])
                            events.append(event_data)
                        except json.JSONDecodeError:
                            pass
                
                # Should have error event
                error_events = [e for e in events if e.get('type') == 'error']
                assert len(error_events) >= 1
                assert 'LLM generation failed' in error_events[0]['message']
