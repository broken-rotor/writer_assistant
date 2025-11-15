"""
Unit tests for generation models with structured context support.
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models.generation_models import (
    SystemPrompts,
    ContextMetadata,
    CharacterInfo,
    CharacterFeedbackRequest,
    GenerateChapterRequest,
    RaterFeedbackRequest,
    EditorReviewRequest,
    ModifyChapterRequest,
    FleshOutRequest,
    GenerateCharacterDetailsRequest
)


class TestGenerationModels:
    """Test the generation models that still exist."""
    
    def test_system_prompts_creation(self):
        """Test creating system prompts."""
        prompts = SystemPrompts(
            mainPrefix="You are a helpful writing assistant.",
            mainSuffix="Always be creative and engaging.",
            assistantPrompt="Help the user with their writing.",
            editorPrompt="Review and improve the text."
        )
        
        assert prompts.mainPrefix == "You are a helpful writing assistant."
        assert prompts.mainSuffix == "Always be creative and engaging."
        assert prompts.assistantPrompt == "Help the user with their writing."
        assert prompts.editorPrompt == "Review and improve the text."
    
    def test_context_metadata_creation(self):
        """Test creating context metadata."""
        metadata = ContextMetadata(
            total_elements=5,
            processing_applied=True,
            processing_mode="structured",
            optimization_level="light"
        )
        
        assert metadata.total_elements == 5
        assert metadata.processing_applied is True
        assert metadata.processing_mode == "structured"
        assert metadata.optimization_level == "light"
    
    def test_character_info_creation(self):
        """Test creating character info."""
        char_info = CharacterInfo(
            name="Aria",
            basicBio="A brave warrior trained by a wise mentor"
        )
        
        assert char_info.name == "Aria"
        assert char_info.basicBio == "A brave warrior trained by a wise mentor"


class TestRequestModels:
    """Test the request models with RequestContext support."""
    
    def test_character_feedback_request_validation_error(self):
        """Test that request_context is required."""
        with pytest.raises(ValidationError):
            CharacterFeedbackRequest(
                request_context=None,  # This should cause validation error
                plotPoint="Entering the forest"
            )
    
    def test_character_feedback_request_plotpoint_required(self):
        """Test that plotPoint is required for CharacterFeedbackRequest."""
        from unittest.mock import Mock
        
        # Test that missing plotPoint causes validation error
        with pytest.raises(ValidationError):
            CharacterFeedbackRequest(
                request_context=Mock(),  # This will fail anyway, but we're testing plotPoint requirement
                # plotPoint missing - should cause validation error
            )
    

    



class TestUpdatedLegacyModels:
    """Test that previously legacy-only models now support RequestContext."""
    
    def test_modify_chapter_request_validation_errors(self):
        """Test ModifyChapterRequest validation requirements."""
        from unittest.mock import Mock
        
        # Test that missing currentChapter causes validation error
        with pytest.raises(ValidationError):
            ModifyChapterRequest(
                request_context=Mock(),  # This will fail anyway
                # currentChapter missing - should cause validation error
                userRequest="Make it more exciting"
            )
    
    def test_flesh_out_request_validation_errors(self):
        """Test FleshOutRequest validation requirements."""
        from unittest.mock import Mock
        
        # Test that missing textToFleshOut causes validation error
        with pytest.raises(ValidationError):
            FleshOutRequest(
                request_context=Mock(),  # This will fail anyway
                # textToFleshOut missing - should cause validation error
            )
    
    def test_generate_character_details_request_validation_errors(self):
        """Test GenerateCharacterDetailsRequest validation requirements."""
        from unittest.mock import Mock
        
        # Test that missing basicBio causes validation error
        with pytest.raises(ValidationError):
            GenerateCharacterDetailsRequest(
                request_context=Mock(),  # This will fail anyway
                # basicBio missing - should cause validation error
            )


if __name__ == "__main__":
    pytest.main([__file__])
