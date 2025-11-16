"""
Unit tests for generation models with structured context support.
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models.generation_models import (
    SystemPrompts,
    CharacterInfo,
    CharacterFeedbackRequest,
    GenerateChapterRequest,
    RaterFeedbackRequest,
    EditorReviewRequest,
    ModifyChapterRequest,
    FleshOutRequest,
    GenerateCharacterDetailsRequest
)
from app.models.request_context import RequestContextMetadata


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
    
    def test_request_context_metadata_creation(self):
        """Test creating request context metadata."""
        metadata = RequestContextMetadata(
            story_id="test-story-123",
            story_title="Test Story",
            version="1.0",
            total_characters=5,
            total_chapters=3
        )

        assert metadata.story_id == "test-story-123"
        assert metadata.story_title == "Test Story"
        assert metadata.version == "1.0"
        assert metadata.total_characters == 5
        assert metadata.total_chapters == 3
    
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

    def test_character_feedback_request_missing_character_name(self):
        """Test that character_name is required."""
        from app.models.request_context import RequestContext, StoryConfiguration, SystemPrompts, RequestContextMetadata

        # Create minimal valid request context
        request_context = RequestContext(
            configuration=StoryConfiguration(
                system_prompts=SystemPrompts(
                    main_prefix="",
                    main_suffix="",
                    assistant_prompt="",
                    editor_prompt=""
                )
            ),
            context_metadata=RequestContextMetadata(
                story_id="test",
                story_title="Test Story"
            )
        )

        # Test that missing character_name causes validation error
        with pytest.raises(ValidationError):
            CharacterFeedbackRequest(
                request_context=request_context,
                plotPoint="Entering the forest"
                # character_name missing - should cause validation error
            )

    def test_character_feedback_request_plotpoint_required(self):
        """Test that plotPoint is required for CharacterFeedbackRequest."""
        from app.models.request_context import RequestContext, StoryConfiguration, SystemPrompts, RequestContextMetadata

        # Create minimal valid request context
        request_context = RequestContext(
            configuration=StoryConfiguration(
                system_prompts=SystemPrompts(
                    main_prefix="",
                    main_suffix="",
                    assistant_prompt="",
                    editor_prompt=""
                )
            ),
            context_metadata=RequestContextMetadata(
                story_id="test",
                story_title="Test Story"
            )
        )

        # Test that missing plotPoint causes validation error
        with pytest.raises(ValidationError):
            CharacterFeedbackRequest(
                request_context=request_context,
                character_name="Aria"
                # plotPoint missing - should cause validation error
            )
    

    



class TestUpdatedLegacyModels:
    """Test that previously legacy-only models now support RequestContext."""

    def test_modify_chapter_request_validation_errors(self):
        """Test ModifyChapterRequest validation requirements."""
        from app.models.request_context import RequestContext, StoryConfiguration, SystemPrompts, RequestContextMetadata

        # Create minimal valid request context
        request_context = RequestContext(
            configuration=StoryConfiguration(
                system_prompts=SystemPrompts(
                    main_prefix="",
                    main_suffix="",
                    assistant_prompt="",
                    editor_prompt=""
                )
            ),
            context_metadata=RequestContextMetadata(
                story_id="test",
                story_title="Test Story"
            )
        )

        # Test that missing chapter_number causes validation error
        with pytest.raises(ValidationError):
            ModifyChapterRequest(
                request_context=request_context,
                # chapter_number missing - should cause validation error
                userRequest="Make it more exciting"
            )

        # Test that missing userRequest causes validation error
        with pytest.raises(ValidationError):
            ModifyChapterRequest(
                request_context=request_context,
                chapter_number=1
                # userRequest missing - should cause validation error
            )

    def test_flesh_out_request_validation_errors(self):
        """Test FleshOutRequest validation requirements."""
        from app.models.request_context import RequestContext, StoryConfiguration, SystemPrompts, RequestContextMetadata
        from app.models.generation_models import FleshOutType

        # Create minimal valid request context
        request_context = RequestContext(
            configuration=StoryConfiguration(
                system_prompts=SystemPrompts(
                    main_prefix="",
                    main_suffix="",
                    assistant_prompt="",
                    editor_prompt=""
                )
            ),
            context_metadata=RequestContextMetadata(
                story_id="test",
                story_title="Test Story"
            )
        )

        # Test that missing text_to_flesh_out causes validation error
        with pytest.raises(ValidationError):
            FleshOutRequest(
                request_context=request_context,
                request_type=FleshOutType.WORLDBUILDING
                # text_to_flesh_out missing - should cause validation error
            )

        # Test that missing request_type causes validation error
        with pytest.raises(ValidationError):
            FleshOutRequest(
                request_context=request_context,
                text_to_flesh_out="Some text to expand"
                # request_type missing - should cause validation error
            )

    def test_generate_character_details_request_validation_errors(self):
        """Test GenerateCharacterDetailsRequest validation requirements."""
        from app.models.request_context import RequestContext, StoryConfiguration, SystemPrompts, RequestContextMetadata

        # Create minimal valid request context
        request_context = RequestContext(
            configuration=StoryConfiguration(
                system_prompts=SystemPrompts(
                    main_prefix="",
                    main_suffix="",
                    assistant_prompt="",
                    editor_prompt=""
                )
            ),
            context_metadata=RequestContextMetadata(
                story_id="test",
                story_title="Test Story"
            )
        )

        # Test that missing character_name causes validation error
        with pytest.raises(ValidationError):
            GenerateCharacterDetailsRequest(
                request_context=request_context
                # character_name missing - should cause validation error
            )


if __name__ == "__main__":
    pytest.main([__file__])
