"""
Unit tests for context conversion utilities.
"""
import pytest
from datetime import datetime

from app.models.generation_models import (
    SystemPrompts,
    StructuredContextContainer,
    PlotElement,
    CharacterContext,
    UserRequest,
    SystemInstruction,
    CharacterInfo
)
from app.utils.context_converters import (
    ContextConverter,
    convert_legacy_request_to_structured,
    convert_structured_to_legacy_request
)


class TestContextConverter:
    """Test the ContextConverter class."""
    
    def test_legacy_to_structured_basic(self):
        """Test basic legacy to structured conversion."""
        system_prompts = SystemPrompts(
            mainPrefix="You are a helpful assistant",
            mainSuffix="Always be polite",
            assistantPrompt="Assist the user",
            editorPrompt="Edit carefully"
        )
        
        worldbuilding = "A fantasy world with magic and dragons"
        story_summary = "A hero's journey to save the kingdom"
        plot_point = "The hero enters the dark forest"
        user_request = "Add more sensory details"
        
        characters = [
            CharacterInfo(
                name="Aria",
                basicBio="A brave warrior",
                personality="Courageous, determined",
                motivations="Save her village, find her father",
                fears="Losing loved ones",
                relationships="Close to her mentor"
            )
        ]
        
        result = ContextConverter.legacy_to_structured(
            system_prompts=system_prompts,
            worldbuilding=worldbuilding,
            story_summary=story_summary,
            characters=characters,
            user_request=user_request,
            plot_point=plot_point
        )
        
        # Check plot elements
        assert len(result.plot_elements) == 3  # worldbuilding, story_summary, plot_point
        worldbuilding_element = next(
            (elem for elem in result.plot_elements if "worldbuilding" in elem.tags), None
        )
        assert worldbuilding_element is not None
        assert worldbuilding_element.content == worldbuilding
        assert worldbuilding_element.type == "setup"
        
        # Check character contexts
        assert len(result.character_contexts) == 1
        char_context = result.character_contexts[0]
        assert char_context.character_name == "Aria"
        assert char_context.character_id == "aria"
        assert char_context.current_state["bio"] == "A brave warrior"
        assert "Courageous" in char_context.personality_traits
        
        # Check user requests
        assert len(result.user_requests) == 1
        user_req = result.user_requests[0]
        assert user_req.content == user_request
        assert user_req.type == "general"
        
        # Check system instructions
        assert len(result.system_instructions) == 4  # All system prompt parts
        main_prefix_instruction = next(
            (instr for instr in result.system_instructions 
             if instr.content == "You are a helpful assistant"), None
        )
        assert main_prefix_instruction is not None
        assert main_prefix_instruction.priority == "high"
    
    def test_structured_to_legacy_basic(self):
        """Test basic structured to legacy conversion."""
        plot_elements = [
            PlotElement(
                type="setup",
                content="A fantasy world with magic",
                tags=["worldbuilding", "setting"]
            ),
            PlotElement(
                type="setup",
                content="Hero's journey story",
                tags=["story_summary", "background"]
            )
        ]
        
        system_instructions = [
            SystemInstruction(
                type="behavior",
                content="You are a helpful assistant",
                scope="global",
                priority="high"
            ),
            SystemInstruction(
                type="behavior",
                content="Always be polite",
                scope="global",
                priority="medium"
            )
        ]
        
        structured_context = StructuredContextContainer(
            plot_elements=plot_elements,
            system_instructions=system_instructions
        )
        
        system_prompts, worldbuilding, story_summary = ContextConverter.structured_to_legacy(
            structured_context
        )
        
        assert system_prompts.mainPrefix == "You are a helpful assistant"
        assert system_prompts.mainSuffix == "Always be polite"
        assert worldbuilding == "A fantasy world with magic"
        assert story_summary == "Hero's journey story"
    
    def test_round_trip_conversion(self):
        """Test that legacy -> structured -> legacy preserves essential information."""
        original_system_prompts = SystemPrompts(
            mainPrefix="You are a character",
            mainSuffix="Stay in character"
        )
        original_worldbuilding = "Medieval fantasy world"
        original_story_summary = "Knight's quest"
        
        # Convert to structured
        structured = ContextConverter.legacy_to_structured(
            system_prompts=original_system_prompts,
            worldbuilding=original_worldbuilding,
            story_summary=original_story_summary
        )
        
        # Convert back to legacy
        converted_prompts, converted_worldbuilding, converted_summary = (
            ContextConverter.structured_to_legacy(structured)
        )
        
        # Check that essential information is preserved
        assert converted_prompts.mainPrefix == original_system_prompts.mainPrefix
        assert converted_prompts.mainSuffix == original_system_prompts.mainSuffix
        assert converted_worldbuilding == original_worldbuilding
        assert converted_summary == original_story_summary
    
    def test_empty_input_handling(self):
        """Test handling of empty or None inputs."""
        result = ContextConverter.legacy_to_structured()
        
        assert len(result.plot_elements) == 0
        assert len(result.character_contexts) == 0
        assert len(result.user_requests) == 0
        assert len(result.system_instructions) == 0
        assert result.metadata.total_elements == 0
    
    def test_validation_success(self):
        """Test successful validation of conversion."""
        system_prompts = SystemPrompts(mainPrefix="Test prompt")
        worldbuilding = "Test world"
        story_summary = "Test story"
        
        structured = ContextConverter.legacy_to_structured(
            system_prompts=system_prompts,
            worldbuilding=worldbuilding,
            story_summary=story_summary
        )
        
        validation = ContextConverter.validate_conversion(
            system_prompts, worldbuilding, story_summary, structured
        )
        
        assert validation["valid"] is True
        assert len(validation["warnings"]) == 0
        assert validation["metrics"]["plot_elements_created"] == 2
        assert validation["metrics"]["system_instructions_created"] == 1
    
    def test_validation_warnings(self):
        """Test validation warnings for incomplete conversion."""
        system_prompts = SystemPrompts(mainPrefix="Test prompt")
        worldbuilding = "Test world"
        story_summary = "Test story"
        
        # Create a structured context that doesn't preserve worldbuilding
        structured = StructuredContextContainer(
            system_instructions=[
                SystemInstruction(type="behavior", content="Test prompt")
            ],
            plot_elements=[
                PlotElement(type="setup", content="Different content", tags=["other"])
            ]
        )
        
        validation = ContextConverter.validate_conversion(
            system_prompts, worldbuilding, story_summary, structured
        )
        
        assert len(validation["warnings"]) > 0
        assert any("worldbuilding" in warning.lower() for warning in validation["warnings"])
    
    def test_character_conversion_with_empty_fields(self):
        """Test character conversion when some fields are empty."""
        characters = [
            CharacterInfo(
                name="Test Character",
                basicBio="Basic bio",
                personality="",  # Empty personality
                motivations="",  # Empty motivations
                fears="Some fears",
                relationships=""  # Empty relationships
            )
        ]
        
        result = ContextConverter.legacy_to_structured(characters=characters)
        
        assert len(result.character_contexts) == 1
        char_context = result.character_contexts[0]
        assert char_context.character_name == "Test Character"
        assert char_context.current_state["fears"] == "Some fears"
        assert len(char_context.personality_traits) == 0  # Empty personality should result in empty list
        assert len(char_context.goals) == 0  # Empty motivations should result in empty list


class TestConvenienceFunctions:
    """Test the convenience functions."""
    
    def test_convert_legacy_request_to_structured(self):
        """Test the convenience function for legacy to structured conversion."""
        system_prompts = SystemPrompts(mainPrefix="Test")
        worldbuilding = "Test world"
        
        result = convert_legacy_request_to_structured(
            system_prompts=system_prompts,
            worldbuilding=worldbuilding
        )
        
        assert isinstance(result, StructuredContextContainer)
        assert len(result.plot_elements) == 1
        assert len(result.system_instructions) == 1
    
    def test_convert_structured_to_legacy_request(self):
        """Test the convenience function for structured to legacy conversion."""
        structured = StructuredContextContainer(
            plot_elements=[
                PlotElement(type="setup", content="World", tags=["worldbuilding"])
            ],
            system_instructions=[
                SystemInstruction(type="behavior", content="Prompt", priority="high")
            ]
        )
        
        system_prompts, worldbuilding, story_summary = convert_structured_to_legacy_request(
            structured
        )
        
        assert system_prompts.mainPrefix == "Prompt"
        assert worldbuilding == "World"
        assert story_summary == ""


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_multiple_worldbuilding_elements(self):
        """Test handling multiple worldbuilding elements in structured context."""
        structured = StructuredContextContainer(
            plot_elements=[
                PlotElement(type="setup", content="World 1", tags=["worldbuilding"]),
                PlotElement(type="setup", content="World 2", tags=["worldbuilding"]),
                PlotElement(type="setup", content="Story", tags=["story_summary"])
            ]
        )
        
        _, worldbuilding, story_summary = ContextConverter.structured_to_legacy(structured)
        
        assert "World 1" in worldbuilding
        assert "World 2" in worldbuilding
        assert story_summary == "Story"
    
    def test_character_name_normalization(self):
        """Test that character names are properly normalized for IDs."""
        characters = [
            CharacterInfo(name="John Smith", basicBio="A person"),
            CharacterInfo(name="Mary-Jane Watson", basicBio="Another person")
        ]
        
        result = ContextConverter.legacy_to_structured(characters=characters)
        
        char_ids = [ctx.character_id for ctx in result.character_contexts]
        assert "john_smith" in char_ids
        assert "mary-jane_watson" in char_ids
    
    def test_system_instruction_categorization(self):
        """Test that system instructions are properly categorized during conversion."""
        system_prompts = SystemPrompts(
            mainPrefix="Main prefix",
            mainSuffix="Main suffix",
            assistantPrompt="Assistant specific prompt",
            editorPrompt="Editor specific prompt"
        )
        
        result = ContextConverter.legacy_to_structured(system_prompts=system_prompts)
        
        # Should create 4 system instructions
        assert len(result.system_instructions) == 4
        
        # Check that they have appropriate priorities
        high_priority_count = sum(
            1 for instr in result.system_instructions if instr.priority == "high"
        )
        medium_priority_count = sum(
            1 for instr in result.system_instructions if instr.priority == "medium"
        )
        
        assert high_priority_count == 2  # mainPrefix and mainSuffix
        assert medium_priority_count == 2  # assistantPrompt and editorPrompt


if __name__ == "__main__":
    pytest.main([__file__])
