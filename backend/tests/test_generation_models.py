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


class TestStructuredContextModels:
    """Test the structured context models."""
    
    def test_plot_element_creation(self):
        """Test creating a plot element."""
        plot_element = PlotElement(
            type="scene",
            content="The hero enters the dark forest",
            priority="high",
            tags=["current_scene", "forest"],
            metadata={"location": "dark_forest"}
        )
        
        assert plot_element.type == "scene"
        assert plot_element.content == "The hero enters the dark forest"
        assert plot_element.priority == "high"
        assert "current_scene" in plot_element.tags
        assert plot_element.metadata["location"] == "dark_forest"
    
    def test_character_context_creation(self):
        """Test creating a character context."""
        char_context = CharacterContext(
            character_id="hero",
            character_name="Aria",
            current_state={"emotion": "determined", "location": "forest_edge"},
            recent_actions=["Drew sword", "Entered forest"],
            relationships={"mentor": "trusting", "villain": "hostile"},
            goals=["Find the ancient artifact", "Save the kingdom"],
            memories=["Training with mentor", "Village attack"],
            personality_traits=["brave", "determined", "compassionate"]
        )
        
        assert char_context.character_id == "hero"
        assert char_context.character_name == "Aria"
        assert char_context.current_state["emotion"] == "determined"
        assert "Drew sword" in char_context.recent_actions
        assert char_context.relationships["mentor"] == "trusting"
    
    def test_user_request_creation(self):
        """Test creating a user request."""
        user_request = UserRequest(
            type="modification",
            content="Add more sensory details to the forest scene",
            priority="high",
            target="forest_scene",
            context="The scene feels too sparse",
            timestamp=datetime.now()
        )
        
        assert user_request.type == "modification"
        assert user_request.content == "Add more sensory details to the forest scene"
        assert user_request.priority == "high"
        assert user_request.target == "forest_scene"
    
    def test_system_instruction_creation(self):
        """Test creating a system instruction."""
        instruction = SystemInstruction(
            type="behavior",
            content="Always maintain character consistency",
            scope="character",
            priority="high",
            conditions={"phase": "chapter_generation"}
        )
        
        assert instruction.type == "behavior"
        assert instruction.content == "Always maintain character consistency"
        assert instruction.scope == "character"
        assert instruction.conditions["phase"] == "chapter_generation"
    
    def test_structured_context_container(self):
        """Test creating a structured context container."""
        plot_element = PlotElement(type="scene", content="Forest scene")
        char_context = CharacterContext(character_id="hero", character_name="Aria")
        user_request = UserRequest(type="general", content="Make it more exciting")
        system_instruction = SystemInstruction(type="behavior", content="Be creative")
        
        metadata = ContextMetadata(
            total_elements=4,
            processing_applied=True,
            optimization_level="light"
        )
        
        container = StructuredContextContainer(
            plot_elements=[plot_element],
            character_contexts=[char_context],
            user_requests=[user_request],
            system_instructions=[system_instruction],
            metadata=metadata
        )
        
        assert len(container.plot_elements) == 1
        assert len(container.character_contexts) == 1
        assert len(container.user_requests) == 1
        assert len(container.system_instructions) == 1
        assert container.metadata.total_elements == 4
    
    def test_structured_context_validation(self):
        """Test structured context validation."""
        # Test duplicate character contexts
        char_context1 = CharacterContext(character_id="hero", character_name="Aria")
        char_context2 = CharacterContext(character_id="hero", character_name="Aria")
        
        with pytest.raises(ValidationError):
            StructuredContextContainer(
                character_contexts=[char_context1, char_context2]
            )


class TestRequestModels:
    """Test the request models with structured context support."""
    
    def test_character_feedback_request_structured_mode(self):
        """Test CharacterFeedbackRequest in structured mode."""
        plot_element = PlotElement(type="scene", content="Forest entrance")
        char_context = CharacterContext(character_id="aria", character_name="Aria")
        system_instruction = SystemInstruction(
            type="behavior",
            content="You are a character responding in character",
            scope="global"
        )
        
        structured_context = StructuredContextContainer(
            plot_elements=[plot_element],
            character_contexts=[char_context],
            system_instructions=[system_instruction]
        )
        
        request = CharacterFeedbackRequest(
            structured_context=structured_context,
            plotPoint="Entering the forest"
        )
        
        assert request.structured_context is not None
        assert len(request.structured_context.plot_elements) == 1
        assert request.structured_context.plot_elements[0].content == "Forest entrance"
        assert request.structured_context.character_contexts[0].character_name == "Aria"
    
    def test_character_feedback_request_validation(self):
        """Test CharacterFeedbackRequest validation with structured context."""
        plot_element = PlotElement(type="scene", content="Forest entrance")
        char_context = CharacterContext(character_id="aria", character_name="Aria")
        
        structured_context = StructuredContextContainer(
            plot_elements=[plot_element],
            character_contexts=[char_context]
        )
        
        request = CharacterFeedbackRequest(
            structured_context=structured_context,
            plotPoint="Entering the forest"
        )
        
        assert request.structured_context is not None
        assert len(request.structured_context.plot_elements) == 1
        assert request.structured_context.plot_elements[0].content == "Forest entrance"
    
    def test_character_feedback_request_with_system_instructions(self):
        """Test CharacterFeedbackRequest with system instructions in structured context."""
        system_instruction = SystemInstruction(
            type="behavior",
            content="You are a character responding in character",
            scope="global"
        )
        structured_context = StructuredContextContainer(
            plot_elements=[PlotElement(type="scene", content="Forest")],
            system_instructions=[system_instruction]
        )
        
        request = CharacterFeedbackRequest(
            structured_context=structured_context,
            plotPoint="Entering the forest"
        )
        
        assert request.structured_context is not None
        assert len(request.structured_context.system_instructions) == 1
        assert request.structured_context.system_instructions[0].content == "You are a character responding in character"
    
    def test_structured_context_validation_error(self):
        """Test that structured_context is required."""
        with pytest.raises(ValidationError):
            CharacterFeedbackRequest(
                structured_context=None,  # This should cause validation error
                plotPoint="Entering the forest"
            )
    

    



class TestUpdatedLegacyModels:
    """Test that previously legacy-only models now support structured context."""
    
    def test_modify_chapter_request_structured(self):
        """Test ModifyChapterRequest with structured context."""
        structured_context = StructuredContextContainer(
            user_requests=[UserRequest(type="modification", content="Add more detail")]
        )
        
        request = ModifyChapterRequest(
            structured_context=structured_context,
            currentChapter="Chapter text",
            userRequest="Make it more exciting"
        )
        
        assert request.structured_context is not None
        assert len(request.structured_context.user_requests) == 1
    
    def test_flesh_out_request_structured(self):
        """Test FleshOutRequest with structured context."""
        structured_context = StructuredContextContainer(
            plot_elements=[PlotElement(type="setup", content="World background")]
        )
        
        request = FleshOutRequest(
            structured_context=structured_context,
            textToFleshOut="The ancient castle"
        )
        
        assert request.structured_context is not None
        assert len(request.structured_context.plot_elements) == 1
    
    def test_generate_character_details_request_structured(self):
        """Test GenerateCharacterDetailsRequest with structured context."""
        structured_context = StructuredContextContainer(
            character_contexts=[
                CharacterContext(character_id="existing", character_name="Existing Character")
            ]
        )
        
        request = GenerateCharacterDetailsRequest(
            structured_context=structured_context,
            basicBio="A mysterious stranger"
        )
        
        assert request.structured_context is not None
        assert len(request.structured_context.character_contexts) == 1


class TestResponseModels:
    """Test that response models include context metadata."""
    
    def test_response_models_have_context_metadata(self):
        """Test that all response models have context_metadata field."""
        from app.models.generation_models import (
            CharacterFeedbackResponse,
            RaterFeedbackResponse,
            GenerateChapterResponse,
            ModifyChapterResponse,
            EditorReviewResponse,
            FleshOutResponse,
            GenerateCharacterDetailsResponse
        )
        
        # Test that all response models have the context_metadata field
        response_models = [
            CharacterFeedbackResponse,
            RaterFeedbackResponse,
            GenerateChapterResponse,
            ModifyChapterResponse,
            EditorReviewResponse,
            FleshOutResponse,
            GenerateCharacterDetailsResponse
        ]
        
        for model_class in response_models:
            assert 'context_metadata' in model_class.model_fields
            field = model_class.model_fields['context_metadata']
            assert field.default is None  # Should be optional


if __name__ == "__main__":
    pytest.main([__file__])
