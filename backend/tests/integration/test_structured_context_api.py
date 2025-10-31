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

from app.main import app
from app.models.context_models import (
    StructuredContextContainer,
    ContextElement,
    ContextType,
    AgentType,
    ComposePhase
)
from app.models.generation_models import (
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
    def mock_llm(self):
        """Mock LLM for testing."""
        with patch('app.services.llm_inference.get_llm') as mock:
            llm_instance = Mock()
            llm_instance.chat_completion.return_value = "Generated test content"
            mock.return_value = llm_instance
            yield llm_instance
    
    @pytest.fixture
    def sample_structured_context(self):
        """Sample structured context for testing."""
        return StructuredContextContainer(
            plot_elements=[
                ContextElement(
                    type=ContextType.PLOT_OUTLINE,
                    content="The hero discovers a hidden truth about their past",
                    priority="high",
                    tags=["current_plot", "character_development"],
                    metadata={"chapter": 5, "act": 2}
                )
            ],
            character_contexts=[
                {
                    "character_id": "hero_001",
                    "character_name": "Aria",
                    "current_state": {
                        "emotion": "determined",
                        "location": "ancient_library",
                        "goals": ["find_the_truth", "protect_friends"]
                    },
                    "personality_traits": ["brave", "curious", "loyal"],
                    "relationships": {
                        "mentor_001": "trusting",
                        "villain_001": "suspicious"
                    }
                }
            ],
            user_requests=[
                ContextElement(
                    type=ContextType.USER_REQUEST,
                    content="Make this chapter more emotionally intense",
                    priority="medium",
                    tags=["emotional_depth", "pacing"]
                )
            ],
            system_instructions=[
                ContextElement(
                    type=ContextType.SYSTEM_INSTRUCTION,
                    content="Focus on character development and emotional depth",
                    priority="high",
                    tags=["writing_style", "character_focus"]
                )
            ],
            context_metadata={
                "total_elements": 3,
                "processing_mode": "structured",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "version": "1.0"
            }
        )
    
    def test_generate_chapter_structured_context(self, client, mock_llm, sample_structured_context):
        """Test chapter generation with structured context."""
        request_data = {
            "context_mode": "structured",
            "structured_context": sample_structured_context.dict(),
            "compose_phase": "chapter_writing",
            "plotPoint": "Discovery of hidden truth",
            "characters": [
                {
                    "name": "Aria",
                    "description": "Brave young hero",
                    "personality": "determined and curious"
                }
            ]
        }
        
        response = client.post("/api/v1/generate-chapter", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "chapterText" in data
        assert "wordCount" in data
        assert "context_metadata" in data
        assert "metadata" in data
        
        # Validate context metadata
        context_metadata = data["context_metadata"]
        assert context_metadata["processing_mode"] == "structured"
        assert context_metadata["total_elements"] == 3
        
        # Validate generation metadata
        metadata = data["metadata"]
        assert metadata["contextMode"] == "structured"
        assert metadata["structuredContextProvided"] is True
        assert "processingMode" in metadata
        
        # Verify LLM was called with structured context
        mock_llm.chat_completion.assert_called_once()
        call_args = mock_llm.chat_completion.call_args[0]
        messages = call_args[0]
        
        assert len(messages) == 2  # system and user messages
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        
        # Verify structured context elements are in the prompt
        system_content = messages[0]["content"]
        assert "character development and emotional depth" in system_content.lower()
        assert "aria" in system_content.lower()
    
    def test_character_feedback_structured_context(self, client, mock_llm, sample_structured_context):
        """Test character feedback with structured context."""
        request_data = {
            "context_mode": "structured",
            "structured_context": sample_structured_context.dict(),
            "character": {
                "name": "Aria",
                "description": "Brave young hero",
                "personality": "determined and curious"
            },
            "plotPoint": "Discovery of hidden truth"
        }
        
        response = client.post("/api/v1/character-feedback", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "feedback" in data
        assert "context_metadata" in data
        assert data["context_metadata"]["processing_mode"] == "structured"
    
    def test_rater_feedback_structured_context(self, client, mock_llm, sample_structured_context):
        """Test rater feedback with structured context."""
        request_data = {
            "context_mode": "structured",
            "structured_context": sample_structured_context.dict(),
            "chapterText": "Sample chapter text for rating",
            "raterType": "character_consistency",
            "characters": [
                {
                    "name": "Aria",
                    "description": "Brave young hero"
                }
            ]
        }
        
        response = client.post("/api/v1/rater-feedback", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "feedback" in data
        assert "score" in data
        assert "context_metadata" in data
        assert data["context_metadata"]["processing_mode"] == "structured"
    
    def test_editor_review_structured_context(self, client, mock_llm, sample_structured_context):
        """Test editor review with structured context."""
        request_data = {
            "context_mode": "structured",
            "structured_context": sample_structured_context.dict(),
            "chapterText": "Sample chapter text for editing",
            "characters": [
                {
                    "name": "Aria",
                    "description": "Brave young hero"
                }
            ]
        }
        
        response = client.post("/api/v1/editor-review", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "feedback" in data
        assert "context_metadata" in data
        assert data["context_metadata"]["processing_mode"] == "structured"
    
    def test_structured_context_validation(self, client, mock_llm):
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
    
    def test_structured_context_metadata_generation(self, client, mock_llm, sample_structured_context):
        """Test that structured context generates proper metadata."""
        request_data = {
            "context_mode": "structured",
            "structured_context": sample_structured_context.dict(),
            "plotPoint": "Test plot point"
        }
        
        response = client.post("/api/v1/generate-chapter", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
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
    
    def test_context_element_prioritization(self, client, mock_llm):
        """Test that context elements are properly prioritized."""
        structured_context = StructuredContextContainer(
            plot_elements=[
                ContextElement(
                    type=ContextType.PLOT_OUTLINE,
                    content="High priority plot element",
                    priority="high",
                    tags=["critical"]
                ),
                ContextElement(
                    type=ContextType.PLOT_OUTLINE,
                    content="Low priority plot element",
                    priority="low",
                    tags=["background"]
                )
            ],
            context_metadata={
                "total_elements": 2,
                "processing_mode": "structured"
            }
        )
        
        request_data = {
            "context_mode": "structured",
            "structured_context": structured_context.dict(),
            "plotPoint": "Test prioritization"
        }
        
        response = client.post("/api/v1/generate-chapter", json=request_data)
        
        assert response.status_code == 200
        
        # Verify LLM was called and high priority content appears first
        mock_llm.chat_completion.assert_called_once()
        call_args = mock_llm.chat_completion.call_args[0]
        messages = call_args[0]
        
        system_content = messages[0]["content"]
        high_priority_pos = system_content.find("High priority plot element")
        low_priority_pos = system_content.find("Low priority plot element")
        
        # High priority should appear before low priority (or low priority might be filtered out)
        assert high_priority_pos != -1
        if low_priority_pos != -1:
            assert high_priority_pos < low_priority_pos
    
    def test_agent_specific_context_filtering(self, client, mock_llm):
        """Test that context is filtered appropriately for different agent types."""
        structured_context = StructuredContextContainer(
            character_contexts=[
                {
                    "character_id": "hero_001",
                    "character_name": "Aria",
                    "current_state": {"emotion": "determined"}
                }
            ],
            system_instructions=[
                ContextElement(
                    type=ContextType.SYSTEM_INSTRUCTION,
                    content="Character-specific instruction",
                    priority="high",
                    tags=["character_focus"]
                )
            ],
            context_metadata={
                "total_elements": 2,
                "processing_mode": "structured"
            }
        )
        
        # Test character feedback (should include character contexts)
        request_data = {
            "context_mode": "structured",
            "structured_context": structured_context.dict(),
            "character": {
                "name": "Aria",
                "description": "Test character"
            }
        }
        
        response = client.post("/api/v1/character-feedback", json=request_data)
        
        assert response.status_code == 200
        
        # Verify character-specific context was used
        mock_llm.chat_completion.assert_called()
        call_args = mock_llm.chat_completion.call_args[0]
        messages = call_args[0]
        
        system_content = messages[0]["content"]
        assert "aria" in system_content.lower()
        assert "character-specific instruction" in system_content.lower()
    
    def test_performance_with_large_structured_context(self, client, mock_llm):
        """Test performance with large structured context."""
        # Create large structured context
        large_context = StructuredContextContainer(
            plot_elements=[
                ContextElement(
                    type=ContextType.PLOT_OUTLINE,
                    content=f"Plot element {i}" * 100,  # Large content
                    priority="medium"
                ) for i in range(50)  # Many elements
            ],
            context_metadata={
                "total_elements": 50,
                "processing_mode": "structured"
            }
        )
        
        request_data = {
            "context_mode": "structured",
            "structured_context": large_context.dict(),
            "plotPoint": "Performance test"
        }
        
        import time
        start_time = time.time()
        
        response = client.post("/api/v1/generate-chapter", json=request_data)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        assert response.status_code == 200
        
        # Should complete within reasonable time (adjust threshold as needed)
        assert processing_time < 30.0  # 30 seconds max
        
        # Verify context was processed (might be optimized/summarized)
        data = response.json()
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
    
    def test_backward_compatibility_fallback(self, client, mock_llm):
        """Test that system gracefully handles mixed context modes."""
        # Test request with both legacy and structured context
        mixed_request = {
            "context_mode": "hybrid",  # Hybrid mode
            "systemPrompts": {
                "mainPrefix": "Legacy system prompt"
            },
            "worldbuilding": "Legacy worldbuilding",
            "structured_context": {
                "plot_elements": [
                    {
                        "type": "plot_outline",
                        "content": "Structured plot element",
                        "priority": "high"
                    }
                ],
                "context_metadata": {
                    "total_elements": 1,
                    "processing_mode": "structured"
                }
            },
            "plotPoint": "Compatibility test"
        }
        
        response = client.post("/api/v1/generate-chapter", json=mixed_request)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should process successfully with hybrid mode
        assert data["metadata"]["contextMode"] == "hybrid"
        assert "context_metadata" in data
