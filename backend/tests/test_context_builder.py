"""
Tests for the ContextBuilder service.

This module tests the ContextBuilder class which provides a flexible way to build
context for LLM prompts with token budget management and various summarization strategies.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from app.services.context_builder import (
    ContextBuilder,
    ContextRole,
    SummarizationStrategy,
    ContextItem
)
from app.models.request_context import (
    RequestContext,
    StoryConfiguration,
    SystemPrompts,
    WorldbuildingInfo,
    CharacterDetails,
    CharacterState,
    StoryOutline,
    RequestContextMetadata
)
from app.services.token_counter import TokenCount, ContentType, CountingStrategy

@pytest.fixture
def minimal_request_context():
    """Create a minimal RequestContext for testing."""
    return RequestContext(
        configuration=StoryConfiguration(
            system_prompts=SystemPrompts(
                main_prefix="",
                main_suffix="",
                assistant_prompt="",
                editor_prompt=""
            )
        ),
        context_metadata=RequestContextMetadata(
            story_id="test_story",
            story_title="Test Story"
        )
    )


@pytest.fixture
def full_request_context():
    """Create a full RequestContext with all fields populated."""
    return RequestContext(
        configuration=StoryConfiguration(
            system_prompts=SystemPrompts(
                main_prefix="You are a creative writing assistant.",
                main_suffix="Be detailed and authentic.",
                assistant_prompt="Help the writer create compelling narratives.",
                editor_prompt="Review and improve the content."
            )
        ),
        worldbuilding=WorldbuildingInfo(
            content="A noir detective story set in 1940s Los Angeles with dark atmosphere and rain-soaked streets."
        ),
        characters=[
            CharacterDetails(
                id="char_1",
                name="Detective Chen",
                basic_bio="A hardboiled detective with a troubled past.",
                sex="Female",
                gender="Female",
                sexual_preference="Heterosexual",
                age=35,
                physical_appearance="Tall and athletic with sharp eyes",
                usual_clothing="Trench coat and fedora",
                personality="Cynical but determined",
                motivations="Seeking justice and redemption",
                fears="Losing another partner",
                relationships="Works alone, trusts few people",
                is_hidden=False,
                last_modified=datetime.now()
            ),
            CharacterDetails(
                id="char_2",
                name="Hidden Character",
                basic_bio="A mysterious figure.",
                is_hidden=True,
                last_modified=datetime.now()
            )
        ],
        character_states=[
            CharacterState(
                name="Detective Chen",
                recent_actions=["Arrived at crime scene", "Examined evidence"],
                recent_dialog=["What do we have here?", "This doesn't add up"],
                physicalSensations=["Cold rain on face", "Tension in shoulders"],
                emotions=["Focused", "Apprehensive"],
                internalMonologue=["Another case", "I can solve this"],
                goals=["Solve the murder", "Find the truth"],
                memories=["Previous partner's death", "Similar case from last year"]
            )
        ],
        story_outline=StoryOutline(
            summary="A detective investigates a mysterious murder in 1940s Los Angeles.",
            content="Chapter 1: The Crime Scene\nChapter 2: Following Leads\nChapter 3: The Revelation"
        ),
        context_metadata=RequestContextMetadata(
            story_id="test_story",
            story_title="Test Story"
        )
    )


@pytest.fixture
def mock_token_counter():
    """Create a mock TokenCounter."""
    mock_counter = MagicMock()
    # Return token count based on content length (simple approximation)
    mock_counter.count_tokens.side_effect = lambda text: TokenCount(
        content=text,
        token_count=len(text.split()),
        content_type=ContentType.UNKNOWN,
        strategy=CountingStrategy.EXACT,
        overhead_applied=1.0,
        metadata={})
    return mock_counter


class TestContextBuilderInitialization:
    """Test ContextBuilder initialization."""

    @patch('app.services.context_builder.TokenCounter')
    def test_initialization_with_minimal_context(self, mock_token_counter_class, minimal_request_context):
        """Test that ContextBuilder initializes correctly with minimal context."""
        builder = ContextBuilder(minimal_request_context)

        assert builder._request_context == minimal_request_context
        assert builder._elements == []
        assert mock_token_counter_class.called

    @patch('app.services.context_builder.TokenCounter')
    def test_initialization_with_full_context(self, mock_token_counter_class, full_request_context):
        """Test that ContextBuilder initializes correctly with full context."""
        builder = ContextBuilder(full_request_context)

        assert builder._request_context == full_request_context
        assert builder._elements == []


class TestAddSystemPrompt:
    """Test add_system_prompt method."""

    @patch('app.services.context_builder.TokenCounter')
    def test_add_system_prompt_without_prefix_suffix(self, mock_token_counter_class, minimal_request_context):
        """Test adding system prompt without prefix/suffix."""
        builder = ContextBuilder(minimal_request_context)
        test_prompt = "Write a compelling story."

        builder.add_system_prompt(test_prompt)

        assert len(builder._elements) == 1
        element = builder._elements[0]
        assert element.role == ContextRole.SYSTEM
        assert test_prompt in element.content
        assert element.tag is None
        assert element.token_budget == 2000
        assert element.summarization_strategy == SummarizationStrategy.LITERAL

    @patch('app.services.context_builder.TokenCounter')
    def test_add_system_prompt_with_prefix_suffix(self, mock_token_counter_class, full_request_context):
        """Test adding system prompt with prefix and suffix."""
        builder = ContextBuilder(full_request_context)
        test_prompt = "Write a compelling story."

        builder.add_system_prompt(test_prompt)

        assert len(builder._elements) == 1
        element = builder._elements[0]
        assert "You are a creative writing assistant." in element.content
        assert "Write a compelling story." in element.content
        assert "Be detailed and authentic." in element.content
        assert element.role == ContextRole.SYSTEM


class TestAddWorldbuilding:
    """Test add_worldbuilding method."""

    @patch('app.services.context_builder.TokenCounter')
    def test_add_worldbuilding_with_content(self, mock_token_counter_class, full_request_context):
        """Test adding worldbuilding when content exists."""
        builder = ContextBuilder(full_request_context)

        builder.add_worldbuilding()

        assert len(builder._elements) == 1
        element = builder._elements[0]
        assert element.tag == 'WORLD_BUILDING'
        assert element.role == ContextRole.USER
        assert "1940s Los Angeles" in element.content
        assert element.token_budget == 2000
        assert element.summarization_strategy == SummarizationStrategy.SUMMARIZED

    @patch('app.services.context_builder.TokenCounter')
    def test_add_worldbuilding_without_content(self, mock_token_counter_class, minimal_request_context):
        """Test adding worldbuilding when content doesn't exist."""
        builder = ContextBuilder(minimal_request_context)

        builder.add_worldbuilding()

        assert len(builder._elements) == 0


class TestAddCharacters:
    """Test add_characters method."""

    @patch('app.services.context_builder.TokenCounter')
    def test_add_characters_with_visible_characters(self, mock_token_counter_class, full_request_context):
        """Test adding characters filters out hidden characters."""
        builder = ContextBuilder(full_request_context)

        builder.add_characters()

        assert len(builder._elements) == 1
        element = builder._elements[0]
        assert element.tag == 'CHARACTERS'
        assert element.role == ContextRole.USER
        assert "Detective Chen" in element.content
        assert "Hidden Character" not in element.content
        assert "- Name: Detective Chen" in element.content
        assert "Basic Bio: A hardboiled detective" in element.content
        assert element.token_budget == 2000
        assert element.summarization_strategy == SummarizationStrategy.SUMMARIZED

    @patch('app.services.context_builder.TokenCounter')
    def test_add_characters_without_characters(self, mock_token_counter_class, minimal_request_context):
        """Test adding characters when none exist."""
        builder = ContextBuilder(minimal_request_context)

        builder.add_characters()

        assert len(builder._elements) == 0

    @patch('app.services.context_builder.TokenCounter')
    def test_add_characters_format(self, mock_token_counter_class, full_request_context):
        """Test that character formatting includes all fields."""
        builder = ContextBuilder(full_request_context)

        builder.add_characters()

        element = builder._elements[0]
        # Check that all character fields are included
        assert "Sex:" in element.content
        assert "Gender:" in element.content
        assert "Sexual Preference:" in element.content
        assert "Age:" in element.content
        assert "Physical Appearance:" in element.content
        assert "Usual Clothing:" in element.content
        assert "Personality:" in element.content
        assert "Motivations:" in element.content
        assert "Fears:" in element.content
        assert "Relationships:" in element.content


class TestAddStoryOutline:
    """Test add_story_outline method."""

    @patch('app.services.context_builder.TokenCounter')
    def test_add_story_outline_with_summary_and_content(self, mock_token_counter_class, full_request_context):
        """Test adding story outline with both summary and content."""
        builder = ContextBuilder(full_request_context)

        builder.add_story_outline()

        # Note: There's a bug in the original code - it references worldbuilding instead of story_outline
        # The test will fail until the bug is fixed
        # Should create 2 elements: one for summary, one for content
        assert len(builder._elements) == 3

        summary_element = builder._elements[0]
        assert summary_element.tag == 'STORY_TITLE'
        assert summary_element.summarization_strategy == SummarizationStrategy.LITERAL

        summary_element = builder._elements[1]
        assert summary_element.tag == 'STORY_SUMMARY'
        assert summary_element.summarization_strategy == SummarizationStrategy.LITERAL

        outline_element = builder._elements[2]
        assert outline_element.tag == 'STORY_OUTLINE'
        assert outline_element.summarization_strategy == SummarizationStrategy.LITERAL

    @patch('app.services.context_builder.TokenCounter')
    def test_add_story_outline_without_outline(self, mock_token_counter_class, minimal_request_context):
        """Test adding story outline when none exists."""
        builder = ContextBuilder(minimal_request_context)

        builder.add_story_outline()

        assert len(builder._elements) == 1
        summary_element = builder._elements[0]
        assert summary_element.tag == 'STORY_TITLE'


class TestAddCharacterStates:
    """Test add_character_states method."""

    @patch('app.services.context_builder.TokenCounter')
    def test_add_character_states_with_states(self, mock_token_counter_class, full_request_context):
        """Test adding character states when they exist."""
        builder = ContextBuilder(full_request_context)

        builder.add_character_states()

        # Note: There's a bug in the original code with undefined variables
        # This test will fail until the bug is fixed
        assert len(builder._elements) == 1
        element = builder._elements[0]
        assert element.tag == 'CHARACTER_STATES'
        assert element.role == ContextRole.USER
        assert "Detective Chen" in element.content
        assert element.token_budget == 2000
        assert element.summarization_strategy == SummarizationStrategy.SUMMARIZED

    @patch('app.services.context_builder.TokenCounter')
    def test_add_character_states_without_states(self, mock_token_counter_class, minimal_request_context):
        """Test adding character states when none exist."""
        builder = ContextBuilder(minimal_request_context)

        builder.add_character_states()

        assert len(builder._elements) == 0


class TestAddAgentInstruction:
    """Test add_agent_instruction method."""

    @patch('app.services.context_builder.TokenCounter')
    def test_add_agent_instruction(self, mock_token_counter_class, minimal_request_context):
        """Test adding agent instruction."""
        builder = ContextBuilder(minimal_request_context)
        instruction = "Generate a compelling opening paragraph."

        builder.add_agent_instruction(instruction)

        assert len(builder._elements) == 1
        element = builder._elements[0]
        assert element.role == ContextRole.USER
        assert element.content == instruction
        assert element.tag is None
        assert element.token_budget == 2000
        assert element.summarization_strategy == SummarizationStrategy.LITERAL


class TestAddChat:
    """Test add_chat method."""

    @patch('app.services.context_builder.TokenCounter')
    def test_add_chat_user_message(self, mock_token_counter_class, minimal_request_context):
        """Test adding user chat message."""
        builder = ContextBuilder(minimal_request_context)
        message = "Tell me more about the character."

        builder.add_chat(ContextRole.USER, message)

        assert len(builder._elements) == 1
        element = builder._elements[0]
        assert element.role == ContextRole.USER
        assert element.content == message
        assert element.token_budget == 5000
        assert element.summarization_strategy == SummarizationStrategy.ROLLING_WINDOW

    @patch('app.services.context_builder.TokenCounter')
    def test_add_chat_assistant_message(self, mock_token_counter_class, minimal_request_context):
        """Test adding assistant chat message."""
        builder = ContextBuilder(minimal_request_context)
        message = "The character is a hardboiled detective."

        builder.add_chat(ContextRole.ASSISTANT, message)

        assert len(builder._elements) == 1
        element = builder._elements[0]
        assert element.role == ContextRole.ASSISTANT
        assert element.content == message


class TestBuildMessages:
    """Test build_messages method."""

    @patch('app.services.context_builder.TokenCounter')
    def test_build_messages_empty(self, mock_token_counter_class, minimal_request_context, mock_token_counter):
        """Test building chat with no elements."""
        mock_token_counter_class.return_value = mock_token_counter
        builder = ContextBuilder(minimal_request_context)

        chat = builder.build_messages()

        assert chat == []

    @patch('app.services.context_builder.TokenCounter')
    def test_build_messages_single_element(self, mock_token_counter_class, minimal_request_context, mock_token_counter):
        """Test building chat with single element."""
        mock_token_counter_class.return_value = mock_token_counter
        builder = ContextBuilder(minimal_request_context)
        builder.add_system_prompt("Write a story.")

        chat = builder.build_messages()

        assert len(chat) == 1
        assert chat[0]['role'] == ContextRole.SYSTEM
        assert 'content' in chat[0]

    @patch('app.services.context_builder.TokenCounter')
    def test_build_messages_multiple_elements(self, mock_token_counter_class, full_request_context, mock_token_counter):
        """Test building chat with multiple elements."""
        mock_token_counter_class.return_value = mock_token_counter
        builder = ContextBuilder(full_request_context)
        builder.add_system_prompt("Write a story.")
        builder.add_worldbuilding()
        builder.add_characters()

        chat = builder.build_messages()

        assert len(chat) == 3
        assert chat[0]['role'] == ContextRole.SYSTEM
        assert chat[1]['role'] == ContextRole.USER
        assert chat[2]['role'] == ContextRole.USER

    @patch('app.services.context_builder.TokenCounter')
    def test_build_messages_respects_token_budget(self, mock_token_counter_class, minimal_request_context, mock_token_counter):
        """Test that build_messages respects token budgets."""
        mock_token_counter_class.return_value = mock_token_counter
        builder = ContextBuilder(minimal_request_context)
        builder.add_system_prompt("System prompt.")
        builder.add_agent_instruction("Agent instruction.")

        chat = builder.build_messages()

        # Verify that chat was built
        assert len(chat) == 2
        # Token counting should have been called for each element
        assert mock_token_counter.count_tokens.call_count >= 2


class TestBuildPrompt:
    """Test build_prompt method."""

    @patch('app.services.context_builder.TokenCounter')
    def test_build_prompt(self, mock_token_counter_class, minimal_request_context, mock_token_counter):
        """Test building prompt string."""
        mock_token_counter_class.return_value = mock_token_counter
        builder = ContextBuilder(minimal_request_context)
        builder.add_system_prompt("System prompt.")
        builder.add_agent_instruction("User instruction.")

        prompt = builder.build_prompt()

        assert isinstance(prompt, str)
        assert "System prompt." in prompt
        assert "User instruction." in prompt
        # Should be joined with newlines
        assert '\n' in prompt


class TestGetContent:
    """Test _getContent method."""

    @patch('app.services.context_builder.TokenCounter')
    def test_get_content_with_tag(self, mock_token_counter_class, minimal_request_context, mock_token_counter):
        """Test _getContent wraps tagged content correctly."""
        mock_token_counter_class.return_value = mock_token_counter
        builder = ContextBuilder(minimal_request_context)

        element = ContextItem(
            tag='TEST_TAG',
            role=ContextRole.USER,
            content="Test content",
            token_budget=1000,
            summarization_strategy=SummarizationStrategy.LITERAL
        )

        content, token_count = builder._getContent(element, 1000)

        assert '<TEST_TAG>' in content
        assert 'Test content' in content
        assert '</TEST_TAG>' in content
        assert token_count > 0

    @patch('app.services.context_builder.TokenCounter')
    def test_get_content_without_tag(self, mock_token_counter_class, minimal_request_context, mock_token_counter):
        """Test _getContent returns content without tags when tag is None."""
        mock_token_counter_class.return_value = mock_token_counter
        builder = ContextBuilder(minimal_request_context)

        element = ContextItem(
            tag=None,
            role=ContextRole.USER,
            content="Test content",
            token_budget=1000,
            summarization_strategy=SummarizationStrategy.LITERAL
        )

        content, token_count = builder._getContent(element, 1000)

        assert content == "Test content"
        assert '<' not in content
        assert token_count > 0

    @patch('app.services.context_builder.TokenCounter')
    def test_get_content_within_budget(self, mock_token_counter_class, minimal_request_context, mock_token_counter):
        """Test _getContent when content fits within budget."""
        mock_token_counter_class.return_value = mock_token_counter
        builder = ContextBuilder(minimal_request_context)

        element = ContextItem(
            tag=None,
            role=ContextRole.USER,
            content="Short content",
            token_budget=100,
            summarization_strategy=SummarizationStrategy.LITERAL
        )

        content, token_count = builder._getContent(element, 100)

        assert content == "Short content"
        # Token count is based on word count (2 words)
        assert token_count == 2

    @patch('app.services.context_builder.TokenCounter')
    def test_get_content_exceeds_budget_literal(self, mock_token_counter_class, minimal_request_context, mock_token_counter):
        """Test _getContent raises error when budget exceeded with LITERAL strategy."""
        mock_token_counter_class.return_value = mock_token_counter
        builder = ContextBuilder(minimal_request_context)

        element = ContextItem(
            tag='TEST',
            role=ContextRole.USER,
            content="Very long content that exceeds budget",
            token_budget=5,
            summarization_strategy=SummarizationStrategy.LITERAL
        )

        with pytest.raises(ValueError, match="Token budget exceeded"):
            builder._getContent(element, 5)


class TestIntegration:
    """Integration tests for complete workflows."""

    @patch('app.services.context_builder.TokenCounter')
    def test_full_context_build_workflow(self, mock_token_counter_class, full_request_context, mock_token_counter):
        """Test building a complete context with all elements."""
        mock_token_counter_class.return_value = mock_token_counter
        builder = ContextBuilder(full_request_context)

        # Add all context elements
        builder.add_system_prompt("Write a noir detective story.")
        builder.add_worldbuilding()
        builder.add_characters()
        builder.add_story_outline()
        builder.add_agent_instruction("Generate Chapter 1.")

        # Build chat
        chat = builder.build_messages()

        # Verify structure
        assert len(chat) > 0
        assert all('role' in msg and 'content' in msg for msg in chat)

        # Verify prompt
        prompt = builder.build_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    @patch('app.services.context_builder.TokenCounter')
    def test_conversation_workflow(self, mock_token_counter_class, minimal_request_context, mock_token_counter):
        """Test building a conversation with multiple turns."""
        mock_token_counter_class.return_value = mock_token_counter
        builder = ContextBuilder(minimal_request_context)

        # Build conversation
        builder.add_system_prompt("You are a helpful assistant.")
        builder.add_chat(ContextRole.USER, "Tell me about noir fiction.")
        builder.add_chat(ContextRole.ASSISTANT, "Noir fiction is characterized by dark themes...")
        builder.add_chat(ContextRole.USER, "Can you write me a noir story?")

        chat = builder.build_messages()

        assert len(chat) == 4
        assert chat[0]['role'] == ContextRole.SYSTEM
        assert chat[1]['role'] == ContextRole.USER
        assert chat[2]['role'] == ContextRole.ASSISTANT
        assert chat[3]['role'] == ContextRole.USER


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @patch('app.services.context_builder.TokenCounter')
    def test_empty_system_prompt(self, mock_token_counter_class, minimal_request_context, mock_token_counter):
        """Test adding empty system prompt."""
        mock_token_counter_class.return_value = mock_token_counter
        builder = ContextBuilder(minimal_request_context)

        builder.add_system_prompt("")

        assert len(builder._elements) == 1
        # Should still have newline
        assert builder._elements[0].content == "\n"

    @patch('app.services.context_builder.TokenCounter')
    def test_multiple_worldbuilding_calls(self, mock_token_counter_class, full_request_context):
        """Test calling add_worldbuilding multiple times."""
        builder = ContextBuilder(full_request_context)

        builder.add_worldbuilding()
        builder.add_worldbuilding()

        # Should add element each time
        assert len(builder._elements) == 2

    @patch('app.services.context_builder.TokenCounter')
    def test_all_hidden_characters(self, mock_token_counter_class):
        """Test when all characters are hidden."""
        context = RequestContext(
            configuration=StoryConfiguration(
                system_prompts=SystemPrompts(
                    main_prefix="",
                    main_suffix="",
                    assistant_prompt="",
                    editor_prompt=""
                )
            ),
            characters=[
                CharacterDetails(
                    id="char_1",
                    name="Hidden 1",
                    basic_bio="Hidden character",
                    is_hidden=True,
                    last_modified=datetime.now()
                ),
                CharacterDetails(
                    id="char_2",
                    name="Hidden 2",
                    basic_bio="Another hidden character",
                    is_hidden=True,
                    last_modified=datetime.now()
                )
            ],
            context_metadata=RequestContextMetadata(
                story_id="test",
                story_title="Test"
            )
        )

        builder = ContextBuilder(context)
        builder.add_characters()

        # Should not add any elements
        assert len(builder._elements) == 0
