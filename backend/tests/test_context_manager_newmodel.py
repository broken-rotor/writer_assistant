"""
Tests for ContextManager with new StructuredContextContainer model.

This test suite covers the refactored ContextManager that works with typed
collections (PlotElement, CharacterContext, UserRequest, SystemInstruction)
instead of the legacy BaseContextElement list.
"""

import pytest
from datetime import datetime, timezone

from app.services.context_manager import ContextManager
from app.models.context_models import (
    AgentType,
    ContextProcessingConfig
)
from app.models.request_context import (
    RequestContext,
    CharacterDetails,
    StoryOutline,
    WorldbuildingInfo,
    StoryConfiguration
)


class TestContextManagerNewModel:
    """Test ContextManager service with new model."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ContextManager()

        # Create test data using new model
        self.container = StructuredContextContainer(
            plot_elements=[
                PlotElement(
                    id="plot_001",
                    type="scene",
                    content="The hero enters the dark forest",
                    priority="high",
                    tags=["current_scene", "forest"]
                ),
                PlotElement(
                    id="plot_002",
                    type="setup",
                    content="Earlier: The hero received a mysterious map",
                    priority="medium",
                    tags=["backstory"]
                ),
                PlotElement(
                    id="plot_003",
                    type="transition",
                    content="The forest has ancient magic",
                    priority="low",
                    tags=["worldbuilding"]
                )
            ],
            character_contexts=[
                CharacterContext(
                    character_id="hero",
                    character_name="Aria",
                    current_state={"emotional": "determined but cautious"},
                    goals=["Find the ancient artifact", "Save the kingdom"],
                    recent_actions=["Drew sword", "Entered forest"],
                    memories=["Training with mentor", "Village attack"],
                    personality_traits=["brave", "determined"],
                    relationships={"mentor": "trusting", "villain": "hostile"}
                ),
                CharacterContext(
                    character_id="mentor",
                    character_name="Master Orin",
                    current_state={"emotional": "worried about Aria"},
                    goals=["Guide Aria", "Protect the knowledge"],
                    recent_actions=["Gave Aria the map"],
                    memories=["Training Aria"],
                    personality_traits=["wise", "cautious"],
                    relationships={"Aria": "protective"}
                )
            ],
            user_requests=[
                UserRequest(
                    id="user_001",
                    type="style_change",
                    content="Make the dialogue more natural",
                    priority="high",
                    target="dialogue"
                ),
                UserRequest(
                    id="user_002",
                    type="general",
                    content="Focus on sensory details",
                    priority="medium",
                    target="description"
                )
            ],
            system_instructions=[
                SystemInstruction(
                    id="sys_001",
                    type="behavior",
                    content="Maintain consistent character voices",
                    scope="global",
                    priority="high"
                ),
                SystemInstruction(
                    id="sys_002",
                    type="style",
                    content="Use vivid imagery",
                    scope="scene",
                    priority="medium"
                )
            ]
        )

    def test_filter_elements_for_writer_agent(self):
        """Test filtering elements for WRITER agent."""
        filtered = self.manager._filter_elements_for_agent_and_phase(
            self.container, AgentType.WRITER
        )

        # Writer should get plot elements, character contexts, user requests, and system instructions
        assert len(filtered["plot_elements"]) > 0
        assert len(filtered["character_contexts"]) > 0
        assert len(filtered["user_requests"]) > 0
        assert len(filtered["system_instructions"]) > 0

    def test_filter_elements_for_character_agent(self):
        """Test filtering elements for CHARACTER agent."""
        filtered = self.manager._filter_elements_for_agent_and_phase(
            self.container, AgentType.CHARACTER
        )

        # Character agent should get character contexts and some user requests
        assert len(filtered["character_contexts"]) > 0
        assert len(filtered["plot_elements"]) == 0  # Character agents don't get plot elements

    def test_filter_plot_elements_by_priority(self):
        """Test that plot elements are filtered by priority."""
        filtered = self.manager._filter_elements_for_agent_and_phase(
            self.container, AgentType.WRITER
        )

        # High priority plot element should be included
        plot_ids = {p.id for p in filtered["plot_elements"]}
        assert "plot_001" in plot_ids  # High priority

    def test_sort_elements_by_priority(self):
        """Test sorting collections by priority."""
        collections = {
            "plot_elements": self.container.plot_elements,
            "character_contexts": self.container.character_contexts,
            "user_requests": self.container.user_requests,
            "system_instructions": self.container.system_instructions
        }

        sorted_collections = self.manager._sort_elements_by_priority(
            collections, prioritize_recent=True
        )

        # Check that plot elements are sorted by priority (high first)
        priorities = [p.priority for p in sorted_collections["plot_elements"]]
        assert priorities[0] == "high"

        # Check that user requests are sorted
        user_priorities = [r.priority for r in sorted_collections["user_requests"]]
        assert user_priorities[0] == "high"

    def test_apply_custom_filters(self):
        """Test custom filtering functionality."""
        collections = {
            "plot_elements": self.container.plot_elements,
            "character_contexts": self.container.character_contexts,
            "user_requests": self.container.user_requests,
            "system_instructions": self.container.system_instructions
        }

        # Filter by required tags
        custom_filters = {"required_tags": ["current_scene"]}
        filtered = self.manager._apply_custom_filters(collections, custom_filters)

        # Should only include plot element with "current_scene" tag
        assert len(filtered["plot_elements"]) == 1
        assert filtered["plot_elements"][0].id == "plot_001"

    def test_apply_token_budget_under_limit(self):
        """Test token budget when content is under limit."""
        collections = {
            "plot_elements": self.container.plot_elements[:1],  # Just one element
            "character_contexts": self.container.character_contexts[:1],
            "user_requests": [],
            "system_instructions": []
        }

        result_collections, was_summarized = self.manager._apply_token_budget(
            collections, max_tokens=10000, summarization_threshold=8000
        )

        # Should not be summarized
        assert was_summarized is False
        # Should have same number of elements
        assert len(result_collections["plot_elements"]) == 1
        assert len(result_collections["character_contexts"]) == 1

    def test_apply_token_budget_over_limit(self):
        """Test token budget when content exceeds limit."""
        collections = {
            "plot_elements": self.container.plot_elements,
            "character_contexts": self.container.character_contexts,
            "user_requests": self.container.user_requests,
            "system_instructions": self.container.system_instructions
        }

        # Set very strict limit
        result_collections, was_summarized = self.manager._apply_token_budget(
            collections, max_tokens=100, summarization_threshold=80
        )

        # Should be trimmed
        total_elements = sum(len(v) for v in result_collections.values())
        original_total = sum(len(v) for v in collections.values())
        assert total_elements <= original_total

    def test_trim_collections_by_priority(self):
        """Test trimming collections to fit token budget."""
        collections = {
            "plot_elements": self.container.plot_elements,
            "character_contexts": self.container.character_contexts,
            "user_requests": self.container.user_requests,
            "system_instructions": self.container.system_instructions
        }

        # Trim to very small budget
        trimmed = self.manager._trim_collections_by_priority(collections, max_tokens=50)

        # Should keep high priority items
        # High-priority system instruction should be included
        sys_ids = {s.id for s in trimmed["system_instructions"]}
        assert "sys_001" in sys_ids

        # High-priority plot element should be included
        if trimmed["plot_elements"]:
            assert any(p.priority == "high" for p in trimmed["plot_elements"])

    def test_process_context_for_agent_basic(self):
        """Test basic context processing for an agent."""
        config = ContextProcessingConfig(
            target_agent=AgentType.WRITER,
            max_tokens=10000,  # Generous limit
            prioritize_recent=True
        )

        formatted_context, metadata = self.manager.process_structured_context_for_agent(
            self.container, config
        )

        # Should return formatted string
        assert isinstance(formatted_context, str)
        assert len(formatted_context) > 0

        # Should include metadata
        assert isinstance(metadata, dict)
        assert "original_element_count" in metadata
        assert "filtered_element_count" in metadata
        assert "final_element_count" in metadata
        assert "target_agent" in metadata

        assert metadata["target_agent"] == "writer"

    def test_process_context_with_token_limit(self):
        """Test context processing with strict token limits."""
        config = ContextProcessingConfig(
            target_agent=AgentType.WRITER,
            max_tokens=200,  # Strict limit
            summarization_threshold=150
        )

        formatted_context, metadata = self.manager.process_structured_context_for_agent(
            self.container, config
        )

        # Should still return valid context
        assert isinstance(formatted_context, str)
        assert len(formatted_context) > 0

        # Should indicate that trimming occurred
        assert metadata["final_element_count"] <= metadata["original_element_count"]

    def test_process_context_with_custom_filters(self):
        """Test context processing with custom filters."""
        config = ContextProcessingConfig(
            target_agent=AgentType.WRITER,
            custom_filters={
                "required_tags": ["current_scene"]
            }
        )

        formatted_context, metadata = self.manager.process_structured_context_for_agent(
            self.container, config
        )

        # Should apply filters
        assert metadata["filtered_element_count"] <= metadata["original_element_count"]

        # Should still produce valid output
        assert isinstance(formatted_context, str)
        assert len(formatted_context) > 0


class TestContextFormatterNewModel:
    """Test ContextFormatter service with new model."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = ContextFormatter()

        self.collections = {
            "plot_elements": [
                PlotElement(
                    id="plot_001",
                    type="scene",
                    content="Hero enters dark forest",
                    priority="high",
                    tags=["current_scene"]
                )
            ],
            "character_contexts": [
                CharacterContext(
                    character_id="hero",
                    character_name="Aria",
                    current_state={"emotional": "determined"},
                    goals=["Find artifact"],
                    personality_traits=["brave"]
                )
            ],
            "user_requests": [
                UserRequest(
                    id="user_001",
                    type="style_change",
                    content="Make dialogue more natural",
                    priority="high"
                )
            ],
            "system_instructions": [
                SystemInstruction(
                    id="sys_001",
                    type="behavior",
                    content="Maintain character consistency",
                    scope="global",
                    priority="high"
                )
            ]
        }

    def test_format_for_writer(self):
        """Test formatting context for Writer agent."""
        formatted = self.formatter.format_for_agent(
            self.collections, AgentType.WRITER
        )

        # Should include all relevant sections
        assert "=== SYSTEM INSTRUCTIONS ===" in formatted
        assert "=== PLOT CONTEXT ===" in formatted
        assert "=== CHARACTERS ===" in formatted
        assert "=== USER GUIDANCE ===" in formatted

        # Should include content
        assert "Maintain character consistency" in formatted
        assert "Hero enters dark forest" in formatted
        assert "Aria" in formatted
        assert "Make dialogue more natural" in formatted

    def test_format_for_character(self):
        """Test formatting context for Character agent."""
        formatted = self.formatter.format_for_agent(
            self.collections, AgentType.CHARACTER
        )

        # Should focus on character-relevant content
        assert "=== CHARACTER CONTEXT ===" in formatted
        assert "Aria" in formatted

    def test_format_for_rater(self):
        """Test formatting context for Rater agent."""
        formatted = self.formatter.format_for_agent(
            self.collections, AgentType.RATER
        )

        # Should focus on evaluation-relevant content
        assert "=== EVALUATION CRITERIA ===" in formatted
        assert "=== STORY CONTEXT FOR EVALUATION ===" in formatted

    def test_format_for_editor(self):
        """Test formatting context for Editor agent."""
        formatted = self.formatter.format_for_agent(
            self.collections, AgentType.EDITOR
        )

        # Should focus on editorial content
        assert "=== EDITORIAL GUIDELINES ===" in formatted
        assert "Maintain character consistency" in formatted

    def test_format_character_context(self):
        """Test formatting a character context into a readable string."""
        char = CharacterContext(
            character_id="test",
            character_name="Test Character",
            current_state={"emotional": "happy"},
            goals=["goal1", "goal2"],
            personality_traits=["trait1", "trait2"],
            relationships={"other": "friend"}
        )

        formatted = self.formatter._format_character_context(char)

        assert "State: " in formatted
        assert "Goals: goal1, goal2" in formatted
        assert "Traits: trait1, trait2" in formatted
        assert "Relationships: " in formatted


class TestContextProcessingConfig:
    """Test ContextProcessingConfig model."""

    def test_default_values(self):
        """Test default configuration values."""
        config = ContextProcessingConfig(
            target_agent=AgentType.WRITER
        )

        assert config.target_agent == AgentType.WRITER
        assert config.max_tokens is None
        assert config.prioritize_recent is True
        assert config.include_relationships is True
        assert config.summarization_threshold == 0.8
        assert config.custom_filters == {}

    def test_custom_values(self):
        """Test custom configuration values."""
        config = ContextProcessingConfig(
            target_agent=AgentType.CHARACTER,
            max_tokens=2000,
            prioritize_recent=False,
            include_relationships=False,
            summarization_threshold=0.6,
            custom_filters={"required_tags": ["important"]}
        )

        assert config.target_agent == AgentType.CHARACTER
        assert config.max_tokens == 2000
        assert config.prioritize_recent is False
        assert config.include_relationships is False
        assert config.summarization_threshold == 0.6
        assert config.custom_filters == {"required_tags": ["important"]}
