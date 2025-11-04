"""
Tests for context manager service.
"""

import pytest
from datetime import datetime, timedelta, timezone

from app.services.context_manager import ContextManager, ContextSummarizer, ContextFormatter
from app.models.generation_models import (
    StructuredContextContainer,
    SystemContextElement,
    StoryContextElement,
    CharacterContextElement,
    UserContextElement,
    ContextType,
    AgentType,
    ComposePhase,
    SummarizationRule,
    ContextMetadata,
    ContextProcessingConfig
)


class TestContextManager:
    """Test ContextManager service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ContextManager()
        
        # Create test elements
        self.elements = [
            SystemContextElement(
                id="sys_001",
                type=ContextType.SYSTEM_PROMPT,
                content="You are a creative writing assistant.",
                metadata=ContextMetadata(
                    priority=0.9,
                    target_agents=[AgentType.WRITER],
                    relevant_phases=[ComposePhase.CHAPTER_DETAIL],
                    estimated_tokens=10
                )
            ),
            StoryContextElement(
                id="story_001",
                type=ContextType.WORLD_BUILDING,
                content="A medieval fantasy world with magic systems.",
                metadata=ContextMetadata(
                    priority=0.7,
                    target_agents=[AgentType.WRITER, AgentType.CHARACTER],
                    relevant_phases=[ComposePhase.CHAPTER_DETAIL, ComposePhase.FINAL_EDIT],
                    estimated_tokens=15
                )
            ),
            CharacterContextElement(
                id="char_001",
                type=ContextType.CHARACTER_PROFILE,
                content="A brave knight with mysterious past.",
                character_id="knight_001",
                character_name="Sir Galahad",
                metadata=ContextMetadata(
                    priority=0.8,
                    target_agents=[AgentType.CHARACTER],
                    relevant_phases=[ComposePhase.CHAPTER_DETAIL],
                    estimated_tokens=12
                )
            ),
            UserContextElement(
                id="user_001",
                type=ContextType.USER_FEEDBACK,
                content="Make dialogue more natural.",
                metadata=ContextMetadata(
                    priority=0.6,
                    target_agents=[AgentType.WRITER, AgentType.EDITOR],
                    relevant_phases=[ComposePhase.FINAL_EDIT],
                    estimated_tokens=8
                )
            ),
            SystemContextElement(
                id="sys_002",
                type=ContextType.SYSTEM_PROMPT,
                content="Low priority system prompt.",
                metadata=ContextMetadata(
                    priority=0.3,
                    target_agents=[AgentType.WRITER],
                    relevant_phases=[ComposePhase.PLOT_OUTLINE],
                    estimated_tokens=10
                )
            )
        ]
        
        self.container = StructuredContextContainer(elements=self.elements)
    
    def test_filter_elements_for_agent_and_phase(self):
        """Test filtering elements by agent and phase."""
        config = ContextProcessingConfig(
            target_agent=AgentType.WRITER,
            current_phase=ComposePhase.CHAPTER_DETAIL
        )
        
        filtered = self.manager._filter_elements_for_agent_and_phase(
            self.container, config.target_agent, config.current_phase
        )
        
        # Should include sys_001 and story_001 (both target WRITER and relevant for CHAPTER_DETAIL)
        assert len(filtered) == 2
        filtered_ids = {e.id for e in filtered}
        assert "sys_001" in filtered_ids
        assert "story_001" in filtered_ids
    
    def test_filter_elements_with_expired_context(self):
        """Test that expired elements are filtered out."""
        # Add expired element
        expired_element = SystemContextElement(
            id="expired",
            type=ContextType.SYSTEM_PROMPT,
            content="Expired content",
            metadata=ContextMetadata(
                target_agents=[AgentType.WRITER],
                relevant_phases=[ComposePhase.CHAPTER_DETAIL],
                expires_at=datetime.now(timezone.utc) - timedelta(hours=1)  # Expired
            )
        )
        
        container_with_expired = StructuredContextContainer(
            elements=self.elements + [expired_element]
        )
        
        config = ContextProcessingConfig(
            target_agent=AgentType.WRITER,
            current_phase=ComposePhase.CHAPTER_DETAIL
        )
        
        filtered = self.manager._filter_elements_for_agent_and_phase(
            container_with_expired, config.target_agent, config.current_phase
        )
        
        # Expired element should not be included
        filtered_ids = {e.id for e in filtered}
        assert "expired" not in filtered_ids
    
    def test_apply_custom_filters(self):
        """Test custom filtering functionality."""
        elements = [
            SystemContextElement(
                id="tagged",
                type=ContextType.SYSTEM_PROMPT,
                content="Tagged element",
                metadata=ContextMetadata(
                    priority=0.8,
                    tags=["important", "test"]
                )
            ),
            SystemContextElement(
                id="untagged",
                type=ContextType.SYSTEM_PROMPT,
                content="Untagged element",
                metadata=ContextMetadata(priority=0.5)
            ),
            SystemContextElement(
                id="low_priority",
                type=ContextType.SYSTEM_PROMPT,
                content="Low priority element",
                metadata=ContextMetadata(priority=0.2)
            )
        ]
        
        # Filter by required tags
        custom_filters = {"required_tags": ["important"]}
        filtered = self.manager._apply_custom_filters(elements, custom_filters)
        assert len(filtered) == 1
        assert filtered[0].id == "tagged"
        
        # Filter by minimum priority
        custom_filters = {"min_priority": 0.4}
        filtered = self.manager._apply_custom_filters(elements, custom_filters)
        assert len(filtered) == 2
        filtered_ids = {e.id for e in filtered}
        assert "tagged" in filtered_ids
        assert "untagged" in filtered_ids
        
        # Filter by excluded tags
        custom_filters = {"excluded_tags": ["test"]}
        filtered = self.manager._apply_custom_filters(elements, custom_filters)
        assert len(filtered) == 2
        filtered_ids = {e.id for e in filtered}
        assert "tagged" not in filtered_ids
    
    def test_sort_elements_by_priority(self):
        """Test sorting elements by priority."""
        # Test with prioritize_recent=False
        sorted_elements = self.manager._sort_elements_by_priority(
            self.elements, prioritize_recent=False
        )
        
        # Should be sorted by priority (descending)
        priorities = [e.metadata.priority for e in sorted_elements]
        assert priorities == sorted(priorities, reverse=True)
        
        # First element should be highest priority
        assert sorted_elements[0].metadata.priority == 0.9
        assert sorted_elements[0].id == "sys_001"
    
    def test_trim_by_priority(self):
        """Test trimming elements by priority to fit token budget."""
        # Total tokens: 10 + 15 + 12 + 8 + 10 = 55
        # Set max_tokens to 30, should keep highest priority elements
        
        sorted_elements = self.manager._sort_elements_by_priority(self.elements)
        trimmed = self.manager._trim_by_priority(sorted_elements, max_tokens=30)
        
        # Should keep elements until token limit is reached
        total_tokens = sum(e.metadata.estimated_tokens for e in trimmed)
        assert total_tokens <= 30
        
        # Should prioritize higher priority elements
        assert len(trimmed) >= 2  # Should keep at least 2 elements
        priorities = [e.metadata.priority for e in trimmed]
        assert all(p >= 0.7 for p in priorities)  # Should keep high priority elements
    
    def test_process_context_for_agent_basic(self):
        """Test basic context processing for an agent."""
        config = ContextProcessingConfig(
            target_agent=AgentType.WRITER,
            current_phase=ComposePhase.CHAPTER_DETAIL,
            max_tokens=100,  # Generous limit
            prioritize_recent=True
        )
        
        formatted_context, metadata = self.manager.process_context_for_agent(
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
        assert "current_phase" in metadata
        
        assert metadata["target_agent"] == "writer"
        assert metadata["current_phase"] == "chapter_detail"
    
    def test_process_context_with_token_limit(self):
        """Test context processing with strict token limits."""
        config = ContextProcessingConfig(
            target_agent=AgentType.WRITER,
            current_phase=ComposePhase.CHAPTER_DETAIL,
            max_tokens=20,  # Very strict limit
            summarization_threshold=0.8
        )
        
        formatted_context, metadata = self.manager.process_context_for_agent(
            self.container, config
        )
        
        # Should still return valid context
        assert isinstance(formatted_context, str)
        assert len(formatted_context) > 0
        
        # Should indicate summarization occurred
        assert metadata["was_summarized"] is True
        
        # Should have fewer final elements than original
        assert metadata["final_element_count"] < metadata["original_element_count"]
    
    def test_process_context_with_custom_filters(self):
        """Test context processing with custom filters."""
        config = ContextProcessingConfig(
            target_agent=AgentType.WRITER,
            current_phase=ComposePhase.CHAPTER_DETAIL,
            custom_filters={
                "min_priority": 0.8,
                "allowed_types": [ContextType.SYSTEM_PROMPT, ContextType.WORLD_BUILDING]
            }
        )
        
        formatted_context, metadata = self.manager.process_context_for_agent(
            self.container, config
        )
        
        # Should apply filters
        assert metadata["filtered_element_count"] <= metadata["original_element_count"]
        
        # Should still produce valid output
        assert isinstance(formatted_context, str)
        assert len(formatted_context) > 0


class TestContextSummarizer:
    """Test ContextSummarizer service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.summarizer = ContextSummarizer()
    
    def test_compress_element_within_limit(self):
        """Test compressing element that's already within token limit."""
        element = SystemContextElement(
            id="test",
            type=ContextType.SYSTEM_PROMPT,
            content="Short content",
            metadata=ContextMetadata(estimated_tokens=5)
        )
        
        compressed = self.summarizer.compress_element(element, target_tokens=10)
        
        # Should return original element unchanged
        assert compressed.content == element.content
        assert compressed.id == element.id
    
    def test_compress_element_over_limit(self):
        """Test compressing element that exceeds token limit."""
        long_content = "This is a very long piece of content that definitely exceeds the target token limit and should be compressed."
        element = SystemContextElement(
            id="test",
            type=ContextType.SYSTEM_PROMPT,
            content=long_content,
            metadata=ContextMetadata(
                estimated_tokens=50,
                summarization_rule=SummarizationRule.ALLOW_COMPRESSION
            )
        )
        
        compressed = self.summarizer.compress_element(element, target_tokens=10)
        
        # Should return compressed version
        assert len(compressed.content) < len(element.content)
        assert compressed.content.endswith("...")
        assert compressed.metadata.estimated_tokens == 10
        assert "compressed" in compressed.metadata.tags
    
    def test_compress_preserve_full_element(self):
        """Test that PRESERVE_FULL elements are not compressed."""
        element = SystemContextElement(
            id="test",
            type=ContextType.SYSTEM_PROMPT,
            content="Very important content that should not be compressed",
            metadata=ContextMetadata(
                estimated_tokens=50,
                summarization_rule=SummarizationRule.PRESERVE_FULL
            )
        )
        
        compressed = self.summarizer.compress_element(element, target_tokens=10)
        
        # Should return original element unchanged
        assert compressed.content == element.content
        assert compressed.metadata.estimated_tokens == element.metadata.estimated_tokens
    
    def test_extract_key_points(self):
        """Test extracting key points from element."""
        content = "First sentence is important. Middle sentence provides context. Last sentence is also crucial."
        element = SystemContextElement(
            id="test",
            type=ContextType.SYSTEM_PROMPT,
            content=content
        )
        
        key_points = self.summarizer.extract_key_points(element, target_tokens=20)
        
        # Should extract first and last sentences
        assert "First sentence is important" in key_points.content
        assert "Last sentence is also crucial" in key_points.content
        assert "..." in key_points.content
        assert "key_points" in key_points.metadata.tags
    
    def test_extract_key_points_short_content(self):
        """Test extracting key points from short content."""
        content = "Short content."
        element = SystemContextElement(
            id="test",
            type=ContextType.SYSTEM_PROMPT,
            content=content
        )
        
        key_points = self.summarizer.extract_key_points(element, target_tokens=20)
        
        # Should fall back to compression for short content
        assert key_points.content == content or key_points.content.endswith("...")


class TestContextFormatter:
    """Test ContextFormatter service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = ContextFormatter()
        
        self.elements = [
            SystemContextElement(
                id="sys_001",
                type=ContextType.SYSTEM_PROMPT,
                content="You are a creative writing assistant."
            ),
            StoryContextElement(
                id="story_001",
                type=ContextType.WORLD_BUILDING,
                content="Medieval fantasy world with magic."
            ),
            StoryContextElement(
                id="story_002",
                type=ContextType.STORY_SUMMARY,
                content="Hero's journey to save the kingdom."
            ),
            CharacterContextElement(
                id="char_001",
                type=ContextType.CHARACTER_PROFILE,
                content="Brave knight with mysterious past.",
                character_id="knight_001",
                character_name="Sir Galahad"
            ),
            UserContextElement(
                id="user_001",
                type=ContextType.USER_FEEDBACK,
                content="Make dialogue more natural."
            ),
            UserContextElement(
                id="user_002",
                type=ContextType.USER_INSTRUCTION,
                content="Focus on character development."
            )
        ]
    
    def test_format_for_writer(self):
        """Test formatting context for Writer agent."""
        formatted = self.formatter.format_for_agent(
            self.elements, AgentType.WRITER, ComposePhase.CHAPTER_DETAIL
        )
        
        # Should include all relevant sections
        assert "=== SYSTEM INSTRUCTIONS ===" in formatted
        assert "=== STORY CONTEXT ===" in formatted
        assert "=== CHARACTERS ===" in formatted
        assert "=== USER GUIDANCE ===" in formatted
        
        # Should include content from elements
        assert "You are a creative writing assistant" in formatted
        assert "Medieval fantasy world" in formatted
        assert "Sir Galahad" in formatted
        assert "Make dialogue more natural" in formatted
    
    def test_format_for_character(self):
        """Test formatting context for Character agent."""
        formatted = self.formatter.format_for_agent(
            self.elements, AgentType.CHARACTER, ComposePhase.CHAPTER_DETAIL
        )
        
        # Should focus on character-relevant content
        assert "=== CHARACTER CONTEXT ===" in formatted
        assert "=== STORY BACKGROUND ===" in formatted
        
        # Should include character-specific content
        assert "Sir Galahad" in formatted
        assert "Medieval fantasy world" in formatted
    
    def test_format_for_rater(self):
        """Test formatting context for Rater agent."""
        formatted = self.formatter.format_for_agent(
            self.elements, AgentType.RATER, ComposePhase.CHAPTER_DETAIL
        )
        
        # Should focus on evaluation-relevant content
        assert "=== EVALUATION CRITERIA ===" in formatted
        assert "=== STORY CONTEXT FOR EVALUATION ===" in formatted
        
        # Should include system prompts and story context
        assert "You are a creative writing assistant" in formatted
        assert "Hero's journey" in formatted
    
    def test_format_for_editor(self):
        """Test formatting context for Editor agent."""
        formatted = self.formatter.format_for_agent(
            self.elements, AgentType.EDITOR, ComposePhase.FINAL_EDIT
        )
        
        # Should focus on editorial content
        assert "=== EDITORIAL GUIDELINES ===" in formatted
        assert "=== CONSISTENCY CONTEXT ===" in formatted
        
        # Should include relevant content for editing
        assert "You are a creative writing assistant" in formatted
    
    def test_format_for_worldbuilding(self):
        """Test formatting context for Worldbuilding agent."""
        formatted = self.formatter.format_for_agent(
            self.elements, AgentType.WORLDBUILDING, ComposePhase.PLOT_OUTLINE
        )
        
        # Should focus on worldbuilding content
        assert "=== CURRENT WORLDBUILDING ===" in formatted
        assert "=== STORY CONTEXT ===" in formatted
        
        # Should include worldbuilding and story content
        assert "Medieval fantasy world" in formatted
        assert "Hero's journey" in formatted
    
    def test_format_generic(self):
        """Test generic formatting for unknown agent types."""
        # Create a mock agent type that doesn't have specific formatting
        formatted = self.formatter._format_generic(
            self.elements, ComposePhase.CHAPTER_DETAIL
        )
        
        # Should include all elements with their types as headers
        assert "=== SYSTEM PROMPT ===" in formatted
        assert "=== WORLD BUILDING ===" in formatted
        assert "=== CHARACTER PROFILE ===" in formatted
        
        # Should include content from all elements
        assert "You are a creative writing assistant" in formatted
        assert "Medieval fantasy world" in formatted
        assert "Sir Galahad" in formatted


class TestContextProcessingConfig:
    """Test ContextProcessingConfig model."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = ContextProcessingConfig(
            target_agent=AgentType.WRITER,
            current_phase=ComposePhase.CHAPTER_DETAIL
        )
        
        assert config.target_agent == AgentType.WRITER
        assert config.current_phase == ComposePhase.CHAPTER_DETAIL
        assert config.max_tokens is None
        assert config.prioritize_recent is True
        assert config.include_relationships is True
        assert config.summarization_threshold == 0.8
        assert config.custom_filters == {}
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = ContextProcessingConfig(
            target_agent=AgentType.CHARACTER,
            current_phase=ComposePhase.FINAL_EDIT,
            max_tokens=2000,
            prioritize_recent=False,
            include_relationships=False,
            summarization_threshold=0.6,
            custom_filters={"min_priority": 0.5}
        )
        
        assert config.target_agent == AgentType.CHARACTER
        assert config.current_phase == ComposePhase.FINAL_EDIT
        assert config.max_tokens == 2000
        assert config.prioritize_recent is False
        assert config.include_relationships is False
        assert config.summarization_threshold == 0.6
        assert config.custom_filters == {"min_priority": 0.5}
