"""
Tests for context adapter service.
"""

import pytest
from datetime import datetime

from app.services.context_adapter import ContextAdapter
from app.models.context_models import (
    StructuredContextContainer,
    SystemContextElement,
    StoryContextElement,
    PhaseContextElement,
    ConversationContextElement,
    ContextType,
    AgentType,
    ComposePhase,
    SummarizationRule
)
from app.models.generation_models import SystemPrompts, PhaseContext, ConversationMessage


class TestContextAdapter:
    """Test ContextAdapter service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.adapter = ContextAdapter()
    
    def test_convert_system_prompts(self):
        """Test converting SystemPrompts to structured context."""
        system_prompts = SystemPrompts(
            mainPrefix="You are a creative writing assistant.",
            mainSuffix="Always maintain consistency.",
            assistantPrompt="Focus on character development.",
            editorPrompt="Check for plot holes."
        )
        
        elements, mapping = self.adapter._convert_system_prompts(system_prompts)
        
        # Should create 4 elements
        assert len(elements) == 4
        
        # Should create mapping for all fields
        assert "mainPrefix" in mapping
        assert "mainSuffix" in mapping
        assert "assistantPrompt" in mapping
        assert "editorPrompt" in mapping
        
        # Check element properties
        prefix_element = next(e for e in elements if e.prompt_type == "main_prefix")
        assert prefix_element.content == "You are a creative writing assistant."
        assert prefix_element.type == ContextType.SYSTEM_PROMPT
        assert AgentType.WRITER in prefix_element.applies_to_agents
        assert prefix_element.metadata.priority == 0.9
        assert prefix_element.metadata.summarization_rule == SummarizationRule.PRESERVE_FULL
        
        # Check assistant prompt targeting
        assistant_element = next(e for e in elements if e.prompt_type == "assistant_prompt")
        assert assistant_element.applies_to_agents == [AgentType.WRITER]
        
        # Check editor prompt targeting
        editor_element = next(e for e in elements if e.prompt_type == "editor_prompt")
        assert editor_element.applies_to_agents == [AgentType.EDITOR]
    
    def test_convert_system_prompts_partial(self):
        """Test converting SystemPrompts with only some fields."""
        system_prompts = SystemPrompts(
            mainPrefix="Main prefix only",
            # Other fields are None/empty
        )
        
        elements, mapping = self.adapter._convert_system_prompts(system_prompts)
        
        # Should create only 1 element
        assert len(elements) == 1
        assert "mainPrefix" in mapping
        assert "mainSuffix" not in mapping
        assert "assistantPrompt" not in mapping
        assert "editorPrompt" not in mapping
        
        assert elements[0].content == "Main prefix only"
        assert elements[0].prompt_type == "main_prefix"
    
    def test_convert_worldbuilding(self):
        """Test converting worldbuilding string to structured context."""
        worldbuilding = "A medieval fantasy world with magic systems and political intrigue."
        
        elements = self.adapter._convert_worldbuilding(worldbuilding)
        
        # Should create 1 element
        assert len(elements) == 1
        
        element = elements[0]
        assert element.type == ContextType.WORLD_BUILDING
        assert element.content == worldbuilding
        assert element.story_aspect == "general"
        assert element.metadata.priority == 0.7
        assert element.metadata.summarization_rule == SummarizationRule.ALLOW_COMPRESSION
        assert AgentType.WRITER in element.metadata.target_agents
        assert AgentType.WORLDBUILDING in element.metadata.target_agents
        assert "worldbuilding" in element.metadata.tags
        assert "legacy_converted" in element.metadata.tags
    
    def test_convert_story_summary(self):
        """Test converting story summary string to structured context."""
        story_summary = "A young hero discovers their destiny and must save the kingdom."
        
        elements = self.adapter._convert_story_summary(story_summary)
        
        # Should create 1 element
        assert len(elements) == 1
        
        element = elements[0]
        assert element.type == ContextType.STORY_SUMMARY
        assert element.content == story_summary
        assert element.metadata.priority == 0.8
        assert element.metadata.summarization_rule == SummarizationRule.ALLOW_COMPRESSION
        assert AgentType.WRITER in element.metadata.target_agents
        assert AgentType.CHARACTER in element.metadata.target_agents
        assert "story_summary" in element.metadata.tags
        assert "legacy_converted" in element.metadata.tags
    
    def test_convert_phase_context(self):
        """Test converting PhaseContext to structured context."""
        phase_context = PhaseContext(
            previous_phase_output="Plot outline completed successfully.",
            phase_specific_instructions="Focus on character dialogue and development.",
            conversation_history=[
                ConversationMessage(role="user", content="Make it more dramatic"),
                ConversationMessage(role="assistant", content="I'll add more tension")
            ]
        )
        
        elements = self.adapter._convert_phase_context(phase_context, "chapter_detail")
        
        # Should create 3 elements (output, instructions, conversation)
        assert len(elements) == 3
        
        # Check phase output element
        output_element = next(e for e in elements if e.type == ContextType.PHASE_OUTPUT)
        assert output_element.content == "Plot outline completed successfully."
        assert output_element.phase == ComposePhase.CHAPTER_DETAIL
        assert output_element.metadata.priority == 0.8
        
        # Check phase instruction element
        instruction_element = next(e for e in elements if e.type == ContextType.PHASE_INSTRUCTION)
        assert instruction_element.content == "Focus on character dialogue and development."
        assert instruction_element.phase == ComposePhase.CHAPTER_DETAIL
        assert instruction_element.metadata.priority == 0.9
        assert instruction_element.metadata.summarization_rule == SummarizationRule.PRESERVE_FULL
        
        # Check conversation element
        conv_element = next(e for e in elements if e.type == ContextType.CONVERSATION_HISTORY)
        assert "User: Make it more dramatic" in conv_element.content
        assert "Assistant: I'll add more tension" in conv_element.content
        assert conv_element.participant_roles == ["user", "assistant"]
        assert conv_element.message_count == 2
        assert conv_element.metadata.summarization_rule == SummarizationRule.EXTRACT_KEY_POINTS
    
    def test_legacy_to_structured_complete(self):
        """Test complete legacy to structured conversion."""
        system_prompts = SystemPrompts(
            mainPrefix="You are a writer",
            mainSuffix="Be consistent"
        )
        worldbuilding = "Fantasy world with magic"
        story_summary = "Hero saves kingdom"
        phase_context = PhaseContext(
            previous_phase_output="Outline done",
            phase_specific_instructions="Focus on dialogue"
        )
        
        container, mapping = self.adapter.legacy_to_structured(
            system_prompts=system_prompts,
            worldbuilding=worldbuilding,
            story_summary=story_summary,
            phase_context=phase_context,
            compose_phase="chapter_detail"
        )
        
        # Should create elements for all inputs
        # 2 system prompts + 1 worldbuilding + 1 story summary + 2 phase context = 6 elements
        assert len(container.elements) == 6
        
        # Check global metadata
        assert container.global_metadata["converted_from_legacy"] is True
        assert "conversion_timestamp" in container.global_metadata
        assert container.global_metadata["legacy_compose_phase"] == "chapter_detail"
        
        # Check mapping
        assert len(mapping.system_prompts_mapping) == 2
        assert len(mapping.worldbuilding_elements) == 1
        assert len(mapping.story_summary_elements) == 1
        assert len(mapping.phase_context_elements) == 2
    
    def test_legacy_to_structured_partial(self):
        """Test legacy to structured conversion with only some fields."""
        system_prompts = SystemPrompts(mainPrefix="You are a writer")
        # Only system prompts provided
        
        container, mapping = self.adapter.legacy_to_structured(
            system_prompts=system_prompts
        )
        
        # Should create only 1 element
        assert len(container.elements) == 1
        assert container.elements[0].type == ContextType.SYSTEM_PROMPT
        
        # Mapping should reflect what was provided
        assert len(mapping.system_prompts_mapping) == 1
        assert len(mapping.worldbuilding_elements) == 0
        assert len(mapping.story_summary_elements) == 0
        assert len(mapping.phase_context_elements) == 0
    
    def test_extract_system_prompts(self):
        """Test extracting SystemPrompts from structured context."""
        elements = [
            SystemContextElement(
                id="prefix",
                type=ContextType.SYSTEM_PROMPT,
                content="Main prefix content",
                prompt_type="main_prefix"
            ),
            SystemContextElement(
                id="suffix",
                type=ContextType.SYSTEM_PROMPT,
                content="Main suffix content",
                prompt_type="main_suffix"
            ),
            SystemContextElement(
                id="assistant",
                type=ContextType.SYSTEM_PROMPT,
                content="Assistant prompt content",
                prompt_type="assistant_prompt"
            )
        ]
        
        container = StructuredContextContainer(elements=elements)
        system_prompts = self.adapter._extract_system_prompts(container)
        
        assert system_prompts.mainPrefix == "Main prefix content"
        assert system_prompts.mainSuffix == "Main suffix content"
        assert system_prompts.assistantPrompt == "Assistant prompt content"
        assert system_prompts.editorPrompt is None
    
    def test_extract_worldbuilding(self):
        """Test extracting worldbuilding from structured context."""
        elements = [
            StoryContextElement(
                id="wb1",
                type=ContextType.WORLD_BUILDING,
                content="First worldbuilding element"
            ),
            StoryContextElement(
                id="wb2",
                type=ContextType.WORLD_BUILDING,
                content="Second worldbuilding element"
            )
        ]
        
        container = StructuredContextContainer(elements=elements)
        worldbuilding = self.adapter._extract_worldbuilding(container)
        
        # Should combine elements with double newlines
        assert "First worldbuilding element" in worldbuilding
        assert "Second worldbuilding element" in worldbuilding
        assert "\n\n" in worldbuilding
    
    def test_extract_story_summary(self):
        """Test extracting story summary from structured context."""
        elements = [
            StoryContextElement(
                id="summary1",
                type=ContextType.STORY_SUMMARY,
                content="First part of summary"
            ),
            StoryContextElement(
                id="summary2",
                type=ContextType.STORY_SUMMARY,
                content="Second part of summary"
            )
        ]
        
        container = StructuredContextContainer(elements=elements)
        story_summary = self.adapter._extract_story_summary(container)
        
        # Should combine elements
        assert "First part of summary" in story_summary
        assert "Second part of summary" in story_summary
        assert "\n\n" in story_summary
    
    def test_extract_phase_context(self):
        """Test extracting PhaseContext from structured context."""
        elements = [
            PhaseContextElement(
                id="output",
                type=ContextType.PHASE_OUTPUT,
                content="Previous phase output",
                phase=ComposePhase.CHAPTER_DETAIL
            ),
            PhaseContextElement(
                id="instruction",
                type=ContextType.PHASE_INSTRUCTION,
                content="Phase instructions",
                phase=ComposePhase.CHAPTER_DETAIL
            ),
            ConversationContextElement(
                id="conv",
                type=ContextType.CONVERSATION_HISTORY,
                content="User: Hello\nAssistant: Hi there"
            )
        ]
        
        container = StructuredContextContainer(elements=elements)
        phase_context = self.adapter._extract_phase_context(container)
        
        assert phase_context.previous_phase_output == "Previous phase output"
        assert phase_context.phase_specific_instructions == "Phase instructions"
        assert len(phase_context.conversation_history) == 2
        assert phase_context.conversation_history[0].role == "user"
        assert phase_context.conversation_history[0].content == "Hello"
        assert phase_context.conversation_history[1].role == "assistant"
        assert phase_context.conversation_history[1].content == "Hi there"
    
    def test_structured_to_legacy_round_trip(self):
        """Test round-trip conversion from legacy to structured and back."""
        # Original legacy data
        original_system_prompts = SystemPrompts(
            mainPrefix="Original prefix",
            mainSuffix="Original suffix",
            assistantPrompt="Original assistant"
        )
        original_worldbuilding = "Original worldbuilding content"
        original_story_summary = "Original story summary"
        original_phase_context = PhaseContext(
            previous_phase_output="Original output",
            phase_specific_instructions="Original instructions"
        )
        
        # Convert to structured
        container, mapping = self.adapter.legacy_to_structured(
            system_prompts=original_system_prompts,
            worldbuilding=original_worldbuilding,
            story_summary=original_story_summary,
            phase_context=original_phase_context
        )
        
        # Convert back to legacy
        converted_system_prompts, converted_worldbuilding, converted_story_summary, converted_phase_context = self.adapter.structured_to_legacy(
            container, mapping
        )
        
        # Should match original values
        assert converted_system_prompts.mainPrefix == original_system_prompts.mainPrefix
        assert converted_system_prompts.mainSuffix == original_system_prompts.mainSuffix
        assert converted_system_prompts.assistantPrompt == original_system_prompts.assistantPrompt
        assert converted_worldbuilding == original_worldbuilding
        assert converted_story_summary == original_story_summary
        assert converted_phase_context.previous_phase_output == original_phase_context.previous_phase_output
        assert converted_phase_context.phase_specific_instructions == original_phase_context.phase_specific_instructions
    
    def test_enhance_phase_context(self):
        """Test enhancing PhaseContext with structured context."""
        original_phase_context = PhaseContext(
            previous_phase_output="Original output"
        )
        
        structured_elements = [
            PhaseContextElement(
                id="instruction",
                type=ContextType.PHASE_INSTRUCTION,
                content="Additional phase instructions",
                phase=ComposePhase.CHAPTER_DETAIL
            ),
            ConversationContextElement(
                id="conv",
                type=ContextType.CONVERSATION_HISTORY,
                content="User: New message\nAssistant: Response"
            )
        ]
        
        structured_container = StructuredContextContainer(elements=structured_elements)
        
        enhanced_context = self.adapter.enhance_phase_context(
            original_phase_context, structured_container
        )
        
        # Should preserve original content
        assert enhanced_context.previous_phase_output == "Original output"
        
        # Should add structured content
        assert "Additional phase instructions" in enhanced_context.phase_specific_instructions
        assert len(enhanced_context.conversation_history) == 2
        assert enhanced_context.conversation_history[0].content == "New message"
    
    def test_migrate_legacy_data(self):
        """Test migrating legacy data dictionary."""
        legacy_data = {
            "systemPrompts": {
                "mainPrefix": "System prefix",
                "mainSuffix": "System suffix"
            },
            "worldbuilding": "World content",
            "storySummary": "Story content",
            "compose_phase": "chapter_detail"
        }
        
        container = self.adapter.migrate_legacy_data(legacy_data)
        
        # Should create appropriate elements
        assert len(container.elements) >= 3  # At least system prompts, worldbuilding, story summary
        
        # Should have migration metadata
        assert container.global_metadata["migration_source"] == "legacy_data"
        assert "migration_timestamp" in container.global_metadata
        assert container.global_metadata["original_data_keys"] == list(legacy_data.keys())
        
        # Should contain expected content
        system_elements = container.get_elements_by_type(ContextType.SYSTEM_PROMPT)
        assert len(system_elements) == 2
        
        wb_elements = container.get_elements_by_type(ContextType.WORLD_BUILDING)
        assert len(wb_elements) == 1
        assert wb_elements[0].content == "World content"
        
        summary_elements = container.get_elements_by_type(ContextType.STORY_SUMMARY)
        assert len(summary_elements) == 1
        assert summary_elements[0].content == "Story content"
    
    def test_empty_legacy_fields(self):
        """Test handling empty legacy fields."""
        # Test with empty strings
        container, mapping = self.adapter.legacy_to_structured(
            worldbuilding="",
            story_summary="   ",  # Whitespace only
        )
        
        # Should not create elements for empty content
        assert len(container.elements) == 0
        assert len(mapping.worldbuilding_elements) == 0
        assert len(mapping.story_summary_elements) == 0
    
    def test_none_legacy_fields(self):
        """Test handling None legacy fields."""
        container, mapping = self.adapter.legacy_to_structured(
            system_prompts=None,
            worldbuilding=None,
            story_summary=None,
            phase_context=None
        )
        
        # Should not create any elements
        assert len(container.elements) == 0
        assert len(mapping.system_prompts_mapping) == 0
        assert len(mapping.worldbuilding_elements) == 0
        assert len(mapping.story_summary_elements) == 0
        assert len(mapping.phase_context_elements) == 0

