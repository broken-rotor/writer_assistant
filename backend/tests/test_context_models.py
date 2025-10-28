"""
Tests for structured context models.
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from app.models.context_models import (
    StructuredContextContainer,
    SystemContextElement,
    StoryContextElement,
    CharacterContextElement,
    UserContextElement,
    PhaseContextElement,
    ConversationContextElement,
    ContextType,
    AgentType,
    ComposePhase,
    SummarizationRule,
    ContextMetadata,
    ContextRelationship
)


class TestContextMetadata:
    """Test ContextMetadata model."""
    
    def test_default_values(self):
        """Test default metadata values."""
        metadata = ContextMetadata()
        
        assert metadata.priority == 0.5
        assert metadata.summarization_rule == SummarizationRule.ALLOW_COMPRESSION
        assert metadata.target_agents == [AgentType.WRITER]
        assert len(metadata.relevant_phases) == 3  # All phases by default
        assert metadata.estimated_tokens is None
        assert isinstance(metadata.created_at, datetime)
        assert isinstance(metadata.updated_at, datetime)
        assert metadata.expires_at is None
        assert metadata.tags == []
    
    def test_priority_validation(self):
        """Test priority value validation."""
        # Valid priorities
        ContextMetadata(priority=0.0)
        ContextMetadata(priority=0.5)
        ContextMetadata(priority=1.0)
        
        # Invalid priorities
        with pytest.raises(ValidationError):
            ContextMetadata(priority=-0.1)
        
        with pytest.raises(ValidationError):
            ContextMetadata(priority=1.1)
    
    def test_custom_values(self):
        """Test custom metadata values."""
        expires_at = datetime.utcnow() + timedelta(days=1)
        
        metadata = ContextMetadata(
            priority=0.8,
            summarization_rule=SummarizationRule.PRESERVE_FULL,
            target_agents=[AgentType.WRITER, AgentType.CHARACTER],
            relevant_phases=[ComposePhase.CHAPTER_DETAIL],
            estimated_tokens=100,
            expires_at=expires_at,
            tags=["test", "important"]
        )
        
        assert metadata.priority == 0.8
        assert metadata.summarization_rule == SummarizationRule.PRESERVE_FULL
        assert metadata.target_agents == [AgentType.WRITER, AgentType.CHARACTER]
        assert metadata.relevant_phases == [ComposePhase.CHAPTER_DETAIL]
        assert metadata.estimated_tokens == 100
        assert metadata.expires_at == expires_at
        assert metadata.tags == ["test", "important"]


class TestSystemContextElement:
    """Test SystemContextElement model."""
    
    def test_creation(self):
        """Test creating a system context element."""
        element = SystemContextElement(
            id="sys_001",
            type=ContextType.SYSTEM_PROMPT,
            content="You are a creative writing assistant.",
            prompt_type="main_prefix",
            applies_to_agents=[AgentType.WRITER]
        )
        
        assert element.id == "sys_001"
        assert element.type == ContextType.SYSTEM_PROMPT
        assert element.content == "You are a creative writing assistant."
        assert element.prompt_type == "main_prefix"
        assert element.applies_to_agents == [AgentType.WRITER]
        assert element.version == 1
    
    def test_type_validation(self):
        """Test that only valid system types are allowed."""
        # Valid types
        SystemContextElement(
            id="test",
            type=ContextType.SYSTEM_PROMPT,
            content="test"
        )
        
        SystemContextElement(
            id="test",
            type=ContextType.SYSTEM_INSTRUCTION,
            content="test"
        )
        
        # Invalid type should raise validation error
        with pytest.raises(ValidationError):
            SystemContextElement(
                id="test",
                type=ContextType.WORLD_BUILDING,  # Not a system type
                content="test"
            )


class TestStoryContextElement:
    """Test StoryContextElement model."""
    
    def test_creation(self):
        """Test creating a story context element."""
        element = StoryContextElement(
            id="story_001",
            type=ContextType.WORLD_BUILDING,
            content="A medieval fantasy world with magic.",
            story_aspect="setting",
            chapter_relevance=[1, 2, 3]
        )
        
        assert element.id == "story_001"
        assert element.type == ContextType.WORLD_BUILDING
        assert element.content == "A medieval fantasy world with magic."
        assert element.story_aspect == "setting"
        assert element.chapter_relevance == [1, 2, 3]
    
    def test_type_validation(self):
        """Test that only valid story types are allowed."""
        valid_types = [
            ContextType.WORLD_BUILDING,
            ContextType.STORY_THEME,
            ContextType.NARRATIVE_STATE,
            ContextType.STORY_SUMMARY,
            ContextType.PLOT_OUTLINE
        ]
        
        for context_type in valid_types:
            StoryContextElement(
                id="test",
                type=context_type,
                content="test"
            )
        
        # Invalid type
        with pytest.raises(ValidationError):
            StoryContextElement(
                id="test",
                type=ContextType.CHARACTER_PROFILE,  # Not a story type
                content="test"
            )


class TestCharacterContextElement:
    """Test CharacterContextElement model."""
    
    def test_creation(self):
        """Test creating a character context element."""
        element = CharacterContextElement(
            id="char_001",
            type=ContextType.CHARACTER_PROFILE,
            content="A brave knight with a mysterious past.",
            character_id="knight_001",
            character_name="Sir Galahad",
            related_characters=["king_001", "wizard_001"],
            is_subjective=False
        )
        
        assert element.id == "char_001"
        assert element.type == ContextType.CHARACTER_PROFILE
        assert element.content == "A brave knight with a mysterious past."
        assert element.character_id == "knight_001"
        assert element.character_name == "Sir Galahad"
        assert element.related_characters == ["king_001", "wizard_001"]
        assert element.is_subjective is False
    
    def test_required_fields(self):
        """Test that character_id and character_name are required."""
        with pytest.raises(ValidationError):
            CharacterContextElement(
                id="test",
                type=ContextType.CHARACTER_PROFILE,
                content="test"
                # Missing character_id and character_name
            )


class TestUserContextElement:
    """Test UserContextElement model."""
    
    def test_creation(self):
        """Test creating a user context element."""
        element = UserContextElement(
            id="user_001",
            type=ContextType.USER_FEEDBACK,
            content="Make the dialogue more natural.",
            user_intent="improvement",
            feedback_type="suggestion",
            incorporated=False
        )
        
        assert element.id == "user_001"
        assert element.type == ContextType.USER_FEEDBACK
        assert element.content == "Make the dialogue more natural."
        assert element.user_intent == "improvement"
        assert element.feedback_type == "suggestion"
        assert element.incorporated is False


class TestPhaseContextElement:
    """Test PhaseContextElement model."""
    
    def test_creation(self):
        """Test creating a phase context element."""
        element = PhaseContextElement(
            id="phase_001",
            type=ContextType.PHASE_INSTRUCTION,
            content="Focus on character development in this phase.",
            phase=ComposePhase.CHAPTER_DETAIL,
            previous_phase_output="Plot outline completed successfully."
        )
        
        assert element.id == "phase_001"
        assert element.type == ContextType.PHASE_INSTRUCTION
        assert element.content == "Focus on character development in this phase."
        assert element.phase == ComposePhase.CHAPTER_DETAIL
        assert element.previous_phase_output == "Plot outline completed successfully."
    
    def test_required_phase(self):
        """Test that phase is required."""
        with pytest.raises(ValidationError):
            PhaseContextElement(
                id="test",
                type=ContextType.PHASE_INSTRUCTION,
                content="test"
                # Missing phase
            )


class TestConversationContextElement:
    """Test ConversationContextElement model."""
    
    def test_creation(self):
        """Test creating a conversation context element."""
        element = ConversationContextElement(
            id="conv_001",
            type=ContextType.CONVERSATION_HISTORY,
            content="User: Hello\nAssistant: Hi there!",
            conversation_id="conv_123",
            participant_roles=["user", "assistant"],
            message_count=2
        )
        
        assert element.id == "conv_001"
        assert element.type == ContextType.CONVERSATION_HISTORY
        assert element.content == "User: Hello\nAssistant: Hi there!"
        assert element.conversation_id == "conv_123"
        assert element.participant_roles == ["user", "assistant"]
        assert element.message_count == 2


class TestStructuredContextContainer:
    """Test StructuredContextContainer model."""
    
    def test_empty_container(self):
        """Test creating an empty container."""
        container = StructuredContextContainer()
        
        assert container.elements == []
        assert container.relationships == []
        assert container.global_metadata == {}
        assert container.total_estimated_tokens is None
        assert isinstance(container.created_at, datetime)
        assert container.version == "1.0"
    
    def test_container_with_elements(self):
        """Test creating a container with elements."""
        elements = [
            SystemContextElement(
                id="sys_001",
                type=ContextType.SYSTEM_PROMPT,
                content="Test prompt"
            ),
            StoryContextElement(
                id="story_001",
                type=ContextType.WORLD_BUILDING,
                content="Test worldbuilding"
            )
        ]
        
        container = StructuredContextContainer(elements=elements)
        
        assert len(container.elements) == 2
        assert container.elements[0].id == "sys_001"
        assert container.elements[1].id == "story_001"
    
    def test_unique_id_validation(self):
        """Test that element IDs must be unique."""
        elements = [
            SystemContextElement(
                id="duplicate_id",
                type=ContextType.SYSTEM_PROMPT,
                content="Test 1"
            ),
            StoryContextElement(
                id="duplicate_id",  # Duplicate ID
                type=ContextType.WORLD_BUILDING,
                content="Test 2"
            )
        ]
        
        with pytest.raises(ValidationError, match="All context element IDs must be unique"):
            StructuredContextContainer(elements=elements)
    
    def test_get_elements_by_type(self):
        """Test filtering elements by type."""
        elements = [
            SystemContextElement(
                id="sys_001",
                type=ContextType.SYSTEM_PROMPT,
                content="Test prompt"
            ),
            SystemContextElement(
                id="sys_002",
                type=ContextType.SYSTEM_INSTRUCTION,
                content="Test instruction"
            ),
            StoryContextElement(
                id="story_001",
                type=ContextType.WORLD_BUILDING,
                content="Test worldbuilding"
            )
        ]
        
        container = StructuredContextContainer(elements=elements)
        
        # Get system prompts
        prompts = container.get_elements_by_type(ContextType.SYSTEM_PROMPT)
        assert len(prompts) == 1
        assert prompts[0].id == "sys_001"
        
        # Get worldbuilding
        wb = container.get_elements_by_type(ContextType.WORLD_BUILDING)
        assert len(wb) == 1
        assert wb[0].id == "story_001"
        
        # Get non-existent type
        themes = container.get_elements_by_type(ContextType.STORY_THEME)
        assert len(themes) == 0
    
    def test_get_elements_for_agent(self):
        """Test filtering elements by agent type."""
        elements = [
            SystemContextElement(
                id="sys_001",
                type=ContextType.SYSTEM_PROMPT,
                content="For writer",
                metadata=ContextMetadata(target_agents=[AgentType.WRITER])
            ),
            SystemContextElement(
                id="sys_002",
                type=ContextType.SYSTEM_PROMPT,
                content="For editor",
                metadata=ContextMetadata(target_agents=[AgentType.EDITOR])
            ),
            SystemContextElement(
                id="sys_003",
                type=ContextType.SYSTEM_PROMPT,
                content="For both",
                metadata=ContextMetadata(target_agents=[AgentType.WRITER, AgentType.EDITOR])
            )
        ]
        
        container = StructuredContextContainer(elements=elements)
        
        # Get elements for writer
        writer_elements = container.get_elements_for_agent(AgentType.WRITER)
        assert len(writer_elements) == 2
        assert {e.id for e in writer_elements} == {"sys_001", "sys_003"}
        
        # Get elements for editor
        editor_elements = container.get_elements_for_agent(AgentType.EDITOR)
        assert len(editor_elements) == 2
        assert {e.id for e in editor_elements} == {"sys_002", "sys_003"}
        
        # Get elements for character (none)
        char_elements = container.get_elements_for_agent(AgentType.CHARACTER)
        assert len(char_elements) == 0
    
    def test_get_elements_for_phase(self):
        """Test filtering elements by compose phase."""
        elements = [
            SystemContextElement(
                id="sys_001",
                type=ContextType.SYSTEM_PROMPT,
                content="For outline",
                metadata=ContextMetadata(relevant_phases=[ComposePhase.PLOT_OUTLINE])
            ),
            SystemContextElement(
                id="sys_002",
                type=ContextType.SYSTEM_PROMPT,
                content="For chapter",
                metadata=ContextMetadata(relevant_phases=[ComposePhase.CHAPTER_DETAIL])
            ),
            SystemContextElement(
                id="sys_003",
                type=ContextType.SYSTEM_PROMPT,
                content="For all phases",
                metadata=ContextMetadata(relevant_phases=[
                    ComposePhase.PLOT_OUTLINE,
                    ComposePhase.CHAPTER_DETAIL,
                    ComposePhase.FINAL_EDIT
                ])
            )
        ]
        
        container = StructuredContextContainer(elements=elements)
        
        # Get elements for outline phase
        outline_elements = container.get_elements_for_phase(ComposePhase.PLOT_OUTLINE)
        assert len(outline_elements) == 2
        assert {e.id for e in outline_elements} == {"sys_001", "sys_003"}
        
        # Get elements for chapter phase
        chapter_elements = container.get_elements_for_phase(ComposePhase.CHAPTER_DETAIL)
        assert len(chapter_elements) == 2
        assert {e.id for e in chapter_elements} == {"sys_002", "sys_003"}
        
        # Get elements for edit phase
        edit_elements = container.get_elements_for_phase(ComposePhase.FINAL_EDIT)
        assert len(edit_elements) == 1
        assert edit_elements[0].id == "sys_003"
    
    def test_get_high_priority_elements(self):
        """Test filtering elements by priority."""
        elements = [
            SystemContextElement(
                id="low",
                type=ContextType.SYSTEM_PROMPT,
                content="Low priority",
                metadata=ContextMetadata(priority=0.3)
            ),
            SystemContextElement(
                id="medium",
                type=ContextType.SYSTEM_PROMPT,
                content="Medium priority",
                metadata=ContextMetadata(priority=0.6)
            ),
            SystemContextElement(
                id="high",
                type=ContextType.SYSTEM_PROMPT,
                content="High priority",
                metadata=ContextMetadata(priority=0.9)
            )
        ]
        
        container = StructuredContextContainer(elements=elements)
        
        # Default threshold (0.7)
        high_priority = container.get_high_priority_elements()
        assert len(high_priority) == 1
        assert high_priority[0].id == "high"
        
        # Custom threshold (0.5)
        medium_and_high = container.get_high_priority_elements(threshold=0.5)
        assert len(medium_and_high) == 2
        assert {e.id for e in medium_and_high} == {"medium", "high"}
    
    def test_calculate_total_tokens(self):
        """Test token calculation."""
        elements = [
            SystemContextElement(
                id="with_estimate",
                type=ContextType.SYSTEM_PROMPT,
                content="Test content",
                metadata=ContextMetadata(estimated_tokens=100)
            ),
            SystemContextElement(
                id="without_estimate",
                type=ContextType.SYSTEM_PROMPT,
                content="This is a test content with twenty characters."  # 20 chars = ~5 tokens
            )
        ]
        
        container = StructuredContextContainer(elements=elements)
        total_tokens = container.calculate_total_tokens()
        
        # 100 (estimated) + 12 (48 chars / 4) = 112
        assert total_tokens == 112


class TestContextRelationship:
    """Test ContextRelationship model."""
    
    def test_creation(self):
        """Test creating a context relationship."""
        relationship = ContextRelationship(
            source_id="char_001",
            target_id="char_002",
            relationship_type="conflicts_with",
            strength=0.8,
            description="These characters are rivals"
        )
        
        assert relationship.source_id == "char_001"
        assert relationship.target_id == "char_002"
        assert relationship.relationship_type == "conflicts_with"
        assert relationship.strength == 0.8
        assert relationship.description == "These characters are rivals"
    
    def test_default_strength(self):
        """Test default relationship strength."""
        relationship = ContextRelationship(
            source_id="a",
            target_id="b",
            relationship_type="depends_on"
        )
        
        assert relationship.strength == 1.0
        assert relationship.description is None

