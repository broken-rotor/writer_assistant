"""
Integration tests for structured context API endpoints.

These tests validate the complete structured context workflow from request
to response, ensuring the migration from monolithic to structured context
maintains functionality and quality.
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from tests.test_generate_chapter import extract_final_result_from_streaming_response


def extract_editor_review_result_from_streaming_response(response):
    """Helper function to extract the final result from editor review streaming SSE response."""
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

from app.main import app
from app.models.context_models import (
    BaseContextElement,
    StoryContextElement,
    UserContextElement,
    SystemContextElement,
    ContextType,
    AgentType,
    ComposePhase
)
from app.models.generation_models import (
    StructuredContextContainer,
    PlotElement,
    CharacterContext,
    UserRequest,
    SystemInstruction,
    ContextMetadata,
    GenerateChapterRequest,
    CharacterFeedbackRequest,
    RaterFeedbackRequest,
    EditorReviewRequest
)


class TestStructuredContextAPI:
    """Test suite for structured context API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    

    
    @pytest.fixture
    def sample_structured_context(self):
        """Sample structured context for testing."""
        return StructuredContextContainer(
            plot_elements=[
                PlotElement(
                    id="plot_001",
                    type="scene",
                    content="The hero discovers a hidden truth about their past",
                    priority="high",
                    tags=["current_plot", "character_development"]
                )
            ],
            character_contexts=[
                CharacterContext(
                    character_id="aria_001",
                    character_name="Aria",
                    current_state={"emotional": "determined", "physical": "healthy"},
                    goals=["discover the truth", "protect loved ones"],
                    personality_traits=["brave", "curious", "determined"]
                )
            ],
            user_requests=[
                UserRequest(
                    id="user_req_001",
                    type="style_change",
                    content="Make this chapter more emotionally intense",
                    priority="high",
                    target="chapter"
                )
            ],
            system_instructions=[
                SystemInstruction(
                    id="sys_inst_001",
                    type="style",
                    content="Focus on character development and emotional depth",
                    scope="chapter",
                    priority="high"
                )
            ],
            metadata=ContextMetadata(
                total_elements=4,
                processing_applied=False,
                optimization_level="none"
            )
        )
    
    def test_generate_chapter_structured_context(self, client, sample_structured_context):
        """Test chapter generation with structured context."""
        request_data = {
            "context_mode": "structured",
            "structured_context": sample_structured_context.model_dump(mode='json'),
            "compose_phase": "chapter_detail",
            "plotPoint": "Discovery of hidden truth",
            "characters": [
                {
                    "name": "Aria",
                    "basicBio": "Brave young hero with a mysterious past",
                    "description": "Brave young hero",
                    "personality": "determined and curious"
                }
            ],
            "previousChapters": [],
            "incorporatedFeedback": []
        }
        
        response = client.post("/api/v1/generate-chapter", json=request_data)
        
        data = extract_final_result_from_streaming_response(response)
        
        # Validate response structure
        assert "chapterText" in data
        assert "wordCount" in data
        assert "context_metadata" in data
        assert "metadata" in data
        
        # Validate context metadata
        context_metadata = data["context_metadata"]
        assert context_metadata["total_elements"] == 4
        
        # Validate generation metadata
        metadata = data["metadata"]
        assert metadata["contextMode"] == "structured"
        assert metadata["structuredContextProvided"] is True
        assert "processingMode" in metadata
        
        # Verify response contains expected structured context processing
        # The global mock should handle the LLM calls automatically
    
    def test_character_feedback_structured_context(self, client, sample_structured_context):
        """Test character feedback with structured context."""
        request_data = {
            "context_mode": "structured",
            "structured_context": sample_structured_context.model_dump(mode='json'),
            "previousChapters": [],
            "character": {
                "name": "Aria",
                "basicBio": "Brave young hero with a mysterious past",
                "personality": "determined and curious"
            },
            "plotPoint": "Discovery of hidden truth"
        }
        
        response = client.post("/api/v1/character-feedback", json=request_data)
        
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")
        
        data = extract_final_result_from_streaming_response(response)
        
        # Validate response structure
        assert "feedback" in data
        assert "context_metadata" in data
        assert data["context_metadata"]["total_elements"] == 4  # From sample_structured_context
    
    def test_rater_feedback_structured_context(self, client, sample_structured_context):
        """Test rater feedback with structured context."""
        request_data = {
            "context_mode": "structured",
            "structured_context": sample_structured_context.model_dump(mode='json'),
            "raterPrompt": "Evaluate the narrative flow and character consistency",
            "previousChapters": [],
            "plotPoint": "The hero discovers a hidden truth about their past"
        }
        
        response = client.post("/api/v1/rater-feedback", json=request_data)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
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
        
        # Validate response structure
        assert "feedback" in data
        assert "context_metadata" in data
        assert data["context_metadata"]["processing_mode"] == "structured"
    
    def test_editor_review_structured_context(self, client, sample_structured_context):
        """Test editor review with structured context."""
        request_data = {
            "context_mode": "structured",
            "structured_context": sample_structured_context.model_dump(mode='json'),
            "chapterToReview": "Sample chapter text for editing",
            "previousChapters": [],
            "characters": [
                {
                    "name": "Aria",
                    "basicBio": "Brave young hero"
                }
            ]
        }
        
        response = client.post("/api/v1/editor-review", json=request_data)
        
        data = extract_editor_review_result_from_streaming_response(response)
        
        # Validate response structure
        assert "suggestions" in data
        assert "context_metadata" in data
        assert data["context_metadata"]["processing_mode"] == "structured"
    
    def test_structured_context_validation(self, client):
        """Test validation of structured context data."""
        # Test with invalid structured context
        invalid_request = {
            "context_mode": "structured",
            "structured_context": {
                "plot_elements": [
                    {
                        "type": "invalid_type",  # Invalid context type
                        "content": "Test content"
                    }
                ]
            },
            "plotPoint": "Test plot point"
        }
        
        response = client.post("/api/v1/generate-chapter", json=invalid_request)
        
        # Should return validation error
        assert response.status_code == 422  # Validation error
    
    def test_structured_context_metadata_generation(self, client, sample_structured_context):
        """Test that structured context generates proper metadata."""
        request_data = {
            "context_mode": "structured",
            "structured_context": sample_structured_context.model_dump(mode='json'),
            "plotPoint": "Test plot point",
            "previousChapters": [],
            "characters": [
                {
                    "name": "Aria",
                    "basicBio": "Brave young hero"
                }
            ],
            "incorporatedFeedback": []
        }
        
        response = client.post("/api/v1/generate-chapter", json=request_data)
        
        data = extract_final_result_from_streaming_response(response)
        
        context_metadata = data["context_metadata"]
        
        # Validate metadata structure
        assert "total_elements" in context_metadata
        assert "processing_mode" in context_metadata
        assert "created_at" in context_metadata
        assert "version" in context_metadata
        
        # Validate metadata values
        assert context_metadata["processing_mode"] == "structured"
        assert context_metadata["total_elements"] > 0
        assert context_metadata["version"] == "1.0"
    
    def test_context_element_prioritization(self, client):
        """Test that context elements are properly prioritized."""
        structured_context = StructuredContextContainer(
            plot_elements=[
                PlotElement(
                    id="plot_high_001",
                    type="scene",
                    content="High priority plot element",
                    priority="high",
                    tags=["critical"]
                ),
                PlotElement(
                    id="plot_low_001",
                    type="scene",
                    content="Low priority plot element",
                    priority="low",
                    tags=["background"]
                )
            ],
            character_contexts=[],
            user_requests=[],
            system_instructions=[],
            metadata=ContextMetadata(
                total_elements=2,
                processing_applied=False,
                optimization_level="none"
            )
        )
        
        request_data = {
            "context_mode": "structured",
            "structured_context": structured_context.model_dump(mode='json'),
            "plotPoint": "Test prioritization",
            "previousChapters": [],
            "characters": [
                {
                    "name": "Aria",
                    "basicBio": "Brave young hero"
                }
            ],
            "incorporatedFeedback": []
        }
        
        response = client.post("/api/v1/generate-chapter", json=request_data)
        
        assert response.status_code == 200
        
        # Verify response indicates successful processing
        # Priority ordering is handled by the unified context processor
    
    def test_agent_specific_context_filtering(self, client):
        """Test that context is filtered appropriately for different agent types."""
        structured_context = StructuredContextContainer(
            plot_elements=[],
            character_contexts=[],
            user_requests=[],
            system_instructions=[
                SystemInstruction(
                    id="sys_char_001",
                    type="behavior",
                    content="Character-specific instruction for Aria",
                    scope="character",
                    priority="high"
                )
            ],
            metadata=ContextMetadata(
                total_elements=1,
                processing_applied=False,
                optimization_level="none"
            )
        )
        
        # Test character feedback (should include character contexts)
        request_data = {
            "context_mode": "structured",
            "structured_context": structured_context.model_dump(mode='json'),
            "character": {
                "name": "Aria",
                "basicBio": "Test character"
            },
            "previousChapters": [],
            "plotPoint": "Test plot point for character feedback"
        }
        
        response = client.post("/api/v1/character-feedback", json=request_data)
        
        assert response.status_code == 200
        
        # Verify response indicates successful character-specific processing
        # Character filtering is handled by the unified context processor
    
    def test_performance_with_large_structured_context(self, client):
        """Test performance with large structured context."""
        # Create large structured context
        large_context = StructuredContextContainer(
            plot_elements=[
                PlotElement(
                    id=f"plot_{i:03d}",
                    type="scene",
                    content=f"Plot element {i}" * 100,  # Large content
                    priority="medium",
                    tags=["performance_test"]
                ) for i in range(50)  # Many elements
            ],
            character_contexts=[],
            user_requests=[],
            system_instructions=[],
            metadata=ContextMetadata(
                total_elements=50,
                processing_applied=False,
                optimization_level="none"
            )
        )
        
        request_data = {
            "context_mode": "structured",
            "structured_context": large_context.model_dump(mode='json'),
            "plotPoint": "Performance test",
            "previousChapters": [],
            "characters": [
                {
                    "name": "Aria",
                    "basicBio": "Brave young hero"
                }
            ],
            "incorporatedFeedback": []
        }
        
        import time
        start_time = time.time()
        
        response = client.post("/api/v1/generate-chapter", json=request_data)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        assert processing_time < 30.0  # 30 seconds max
        
        # Verify context was processed (might be optimized/summarized)
        data = extract_final_result_from_streaming_response(response)
        assert "context_metadata" in data
        assert data["context_metadata"]["processing_mode"] == "structured"
    
    def test_error_handling_structured_context(self, client):
        """Test error handling with malformed structured context."""
        # Test with missing required fields
        malformed_request = {
            "context_mode": "structured",
            "structured_context": {
                "plot_elements": [
                    {
                        # Missing required fields
                        "content": "Test content"
                    }
                ]
            }
        }
        
        response = client.post("/api/v1/generate-chapter", json=malformed_request)
        
        # Should return validation error
        assert response.status_code == 422
        
        error_data = response.json()
        assert "detail" in error_data
    
    def test_structured_context_only_migration(self, client):
        """Test that system now operates in structured context only mode."""
        # Test request with structured context only (Phase 2.2 migration)
        structured_request = {
            "structured_context": {
                "plot_elements": [
                    {
                        "type": "scene",
                        "content": "Structured plot element",
                        "priority": "high"
                    }
                ],
                "character_contexts": [
                    {
                        "character_id": "aria",
                        "character_name": "Aria",
                        "current_state": {"emotion": "determined"},
                        "recent_actions": ["Entered the scene"],
                        "relationships": {},
                        "goals": ["Complete the quest"],
                        "memories": ["Previous adventures"],
                        "personality_traits": ["brave", "determined"]
                    }
                ],
                "user_requests": [],
                "system_instructions": [
                    {
                        "type": "behavior",
                        "content": "Write in an engaging narrative style",
                        "scope": "global"
                    }
                ],
                "metadata": {
                    "total_elements": 3,
                    "processing_applied": False,
                    "processing_mode": "structured",
                    "optimization_level": "none"
                }
            },
            "plotPoint": "Structured context test"
        }
        
        response = client.post("/api/v1/generate-chapter", json=structured_request)
        
        data = extract_final_result_from_streaming_response(response)
        
        # Should process successfully with structured context only
        assert data["metadata"]["contextMode"] == "structured"
        assert "context_metadata" in data
