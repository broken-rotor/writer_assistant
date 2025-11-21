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
from app.services.llm_inference import LLMInference, TokenTruncation
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
def mock_llm_inference():
    """Create a mock LLMInference."""
    mock_llm = MagicMock(spec=LLMInference)

    # Mock truncate_to_tokens to return TokenTruncation based on content length
    def mock_truncate(text: str, max_tokens: int) -> TokenTruncation:
        # Simple approximation: 1 word = 1 token
        words = text.split() if text else []
        token_count = len(words)

        if token_count <= max_tokens:
            return TokenTruncation(tail=text, tail_token_count=token_count)

        # Truncate to max_tokens
        tail_words = words[:max_tokens]
        head_words = words[max_tokens:]
        return TokenTruncation(
            head=' '.join(head_words),
            tail=' '.join(tail_words),
            tail_token_count=max_tokens
        )

    # Mock generate to return a summary
    def mock_generate(prompt: str, **kwargs) -> str:
        # Extract content from the prompt and return a shortened version
        if "Content to summarize:" in prompt:
            content = prompt.split("Content to summarize:")[1].split("Summary:")[0].strip()
            words = content.split()
            # Return first 20% of words as summary
            summary_length = max(1, len(words) // 5)
            return ' '.join(words[:summary_length])
        return "Summary of content"

    # Mock count_tokens to return token count based on word count
    def mock_count_tokens(text: str) -> int:
        return len(text.split()) if text else 0

    mock_llm.truncate_to_tokens.side_effect = mock_truncate
    mock_llm.generate.side_effect = mock_generate
    mock_llm.count_tokens.side_effect = mock_count_tokens
    return mock_llm


class TestContextBuilderInitialization:
    """Test ContextBuilder initialization."""

    def test_initialization_with_minimal_context(self, minimal_request_context, mock_llm_inference):
        """Test that ContextBuilder initializes correctly with minimal context."""
        builder = ContextBuilder(minimal_request_context, mock_llm_inference)

        assert builder._request_context == minimal_request_context
        assert builder._elements == []
        assert builder._model == mock_llm_inference

    def test_initialization_with_full_context(self, full_request_context, mock_llm_inference):
        """Test that ContextBuilder initializes correctly with full context."""
        builder = ContextBuilder(full_request_context, mock_llm_inference)

        assert builder._request_context == full_request_context
        assert builder._elements == []


class TestAddSystemPrompt:
    """Test add_system_prompt method."""

    def test_add_system_prompt_without_prefix_suffix(self, minimal_request_context, mock_llm_inference):
        """Test adding system prompt without prefix/suffix."""
        builder = ContextBuilder(minimal_request_context, mock_llm_inference)
        test_prompt = "Write a compelling story."

        builder.add_system_prompt(test_prompt)

        assert len(builder._elements) == 1
        element = builder._elements[0]
        assert element.role == ContextRole.SYSTEM
        assert test_prompt in element.content
        assert element.tag is None
        assert element.token_budget == 2000
        assert element.summarization_strategy == SummarizationStrategy.LITERAL

    def test_add_system_prompt_with_prefix_suffix(self, full_request_context):
        """Test adding system prompt with prefix and suffix."""
        builder = ContextBuilder(full_request_context, mock_llm_inference)
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

    def test_add_worldbuilding_with_content(self, full_request_context):
        """Test adding worldbuilding when content exists."""
        builder = ContextBuilder(full_request_context, mock_llm_inference)

        builder.add_worldbuilding()

        assert len(builder._elements) == 1
        element = builder._elements[0]
        assert element.tag == 'WORLD_BUILDING'
        assert element.role == ContextRole.USER
        assert "1940s Los Angeles" in element.content
        assert element.token_budget == 2000
        assert element.summarization_strategy == SummarizationStrategy.SUMMARIZED

    def test_add_worldbuilding_without_content(self, minimal_request_context):
        """Test adding worldbuilding when content doesn't exist."""
        builder = ContextBuilder(minimal_request_context, mock_llm_inference)

        builder.add_worldbuilding()

        assert len(builder._elements) == 0


class TestAddCharacters:
    """Test add_characters method."""

    def test_add_characters_with_visible_characters(self, full_request_context):
        """Test adding characters filters out hidden characters."""
        builder = ContextBuilder(full_request_context, mock_llm_inference)

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

    def test_add_characters_without_characters(self, minimal_request_context):
        """Test adding characters when none exist."""
        builder = ContextBuilder(minimal_request_context, mock_llm_inference)

        builder.add_characters()

        assert len(builder._elements) == 0

    def test_add_characters_format(self, full_request_context):
        """Test that character formatting includes all fields."""
        builder = ContextBuilder(full_request_context, mock_llm_inference)

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

    def test_add_story_outline_with_summary_and_content(self, full_request_context):
        """Test adding story outline with both summary and content."""
        builder = ContextBuilder(full_request_context, mock_llm_inference)

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

    def test_add_story_outline_without_outline(self, minimal_request_context):
        """Test adding story outline when none exists."""
        builder = ContextBuilder(minimal_request_context, mock_llm_inference)

        builder.add_story_outline()

        assert len(builder._elements) == 1
        summary_element = builder._elements[0]
        assert summary_element.tag == 'STORY_TITLE'


class TestAddCharacterStates:
    """Test add_character_states method."""

    def test_add_character_states_with_states(self, full_request_context):
        """Test adding character states when they exist."""
        builder = ContextBuilder(full_request_context, mock_llm_inference)

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

    def test_add_character_states_without_states(self, minimal_request_context):
        """Test adding character states when none exist."""
        builder = ContextBuilder(minimal_request_context, mock_llm_inference)

        builder.add_character_states()

        assert len(builder._elements) == 0


class TestAddAgentInstruction:
    """Test add_agent_instruction method."""

    def test_add_agent_instruction(self, minimal_request_context):
        """Test adding agent instruction."""
        builder = ContextBuilder(minimal_request_context, mock_llm_inference)
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

    def test_add_chat_user_message(self, minimal_request_context):
        """Test adding user chat message."""
        builder = ContextBuilder(minimal_request_context, mock_llm_inference)
        message = "Tell me more about the character."

        builder.add_chat(ContextRole.USER, message)

        assert len(builder._elements) == 1
        element = builder._elements[0]
        assert element.role == ContextRole.USER
        assert element.content == message
        assert element.token_budget == 5000
        assert element.summarization_strategy == SummarizationStrategy.ROLLING_WINDOW

    def test_add_chat_assistant_message(self, minimal_request_context):
        """Test adding assistant chat message."""
        builder = ContextBuilder(minimal_request_context, mock_llm_inference)
        message = "The character is a hardboiled detective."

        builder.add_chat(ContextRole.ASSISTANT, message)

        assert len(builder._elements) == 1
        element = builder._elements[0]
        assert element.role == ContextRole.ASSISTANT
        assert element.content == message


class TestBuildMessages:
    """Test build_messages method."""

    def test_build_messages_empty(self, minimal_request_context, mock_llm_inference):
        """Test building chat with no elements."""
        builder = ContextBuilder(minimal_request_context, mock_llm_inference)

        chat = builder.build_messages()

        assert chat == []

    def test_build_messages_single_element(self, minimal_request_context, mock_llm_inference):
        """Test building chat with single element."""
        builder = ContextBuilder(minimal_request_context, mock_llm_inference)
        builder.add_system_prompt("Write a story.")

        chat = builder.build_messages()

        assert len(chat) == 1
        assert chat[0]['role'] == ContextRole.SYSTEM
        assert 'content' in chat[0]

    def test_build_messages_multiple_elements(self, full_request_context, mock_llm_inference):
        """Test building chat with multiple elements."""
        builder = ContextBuilder(full_request_context, mock_llm_inference)
        builder.add_system_prompt("Write a story.")
        builder.add_worldbuilding()
        builder.add_characters()

        chat = builder.build_messages()

        assert len(chat) == 3
        assert chat[0]['role'] == ContextRole.SYSTEM
        assert chat[1]['role'] == ContextRole.USER
        assert chat[2]['role'] == ContextRole.USER

    def test_build_messages_respects_token_budget(self, minimal_request_context, mock_llm_inference):
        """Test that build_messages respects token budgets."""
        builder = ContextBuilder(minimal_request_context, mock_llm_inference)
        builder.add_system_prompt("System prompt.")
        builder.add_agent_instruction("Agent instruction.")

        chat = builder.build_messages()

        # Verify that chat was built
        assert len(chat) == 2
        # Token truncation should have been called for each element
        assert mock_llm_inference.truncate_to_tokens.call_count >= 2


class TestBuildPrompt:
    """Test build_prompt method."""

    def test_build_prompt(self, minimal_request_context, mock_llm_inference):
        """Test building prompt string."""
        builder = ContextBuilder(minimal_request_context, mock_llm_inference)
        builder.add_system_prompt("System prompt.")
        builder.add_agent_instruction("User instruction.")

        prompt = builder.build_prompt()

        assert isinstance(prompt, str)
        assert "System prompt." in prompt
        assert "User instruction." in prompt
        # Should be joined with newlines
        assert '\n' in prompt


class TestGetContent:
    """Test _get_content method."""

    def test_get_content_with_tag(self, minimal_request_context, mock_llm_inference):
        """Test _get_content wraps tagged content correctly."""
        builder = ContextBuilder(minimal_request_context, mock_llm_inference)

        element = ContextItem(
            tag='TEST_TAG',
            role=ContextRole.USER,
            content="Test content",
            token_budget=1000,
            summarization_strategy=SummarizationStrategy.LITERAL
        )

        content, token_count = builder._get_content(element, 1000)

        assert '<TEST_TAG>' in content
        assert 'Test content' in content
        assert '</TEST_TAG>' in content
        assert token_count > 0

    def test_get_content_without_tag(self, minimal_request_context, mock_llm_inference):
        """Test _get_content returns content without tags when tag is None."""
        builder = ContextBuilder(minimal_request_context, mock_llm_inference)

        element = ContextItem(
            tag=None,
            role=ContextRole.USER,
            content="Test content",
            token_budget=1000,
            summarization_strategy=SummarizationStrategy.LITERAL
        )

        content, token_count = builder._get_content(element, 1000)

        assert content == "Test content"
        assert '<' not in content
        assert token_count > 0

    def test_get_content_within_budget(self, minimal_request_context, mock_llm_inference):
        """Test _get_content when content fits within budget."""
        builder = ContextBuilder(minimal_request_context, mock_llm_inference)

        element = ContextItem(
            tag=None,
            role=ContextRole.USER,
            content="Short content",
            token_budget=100,
            summarization_strategy=SummarizationStrategy.LITERAL
        )

        content, token_count = builder._get_content(element, 100)

        assert content == "Short content"
        # Token count is based on word count (2 words)
        assert token_count == 2

    def test_get_content_exceeds_budget_literal(self, minimal_request_context, mock_llm_inference):
        """Test _get_content raises error when budget exceeded with LITERAL strategy."""
        builder = ContextBuilder(minimal_request_context, mock_llm_inference)

        element = ContextItem(
            tag='TEST',
            role=ContextRole.USER,
            content="Very long content that exceeds budget",
            token_budget=5,
            summarization_strategy=SummarizationStrategy.LITERAL
        )

        with pytest.raises(ValueError, match="Token budget exceeded"):
            builder._get_content(element, 5)


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_full_context_build_workflow(self, full_request_context, mock_llm_inference):
        """Test building a complete context with all elements."""
        builder = ContextBuilder(full_request_context, mock_llm_inference)

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

    def test_conversation_workflow(self, minimal_request_context, mock_llm_inference):
        """Test building a conversation with multiple turns."""
        builder = ContextBuilder(minimal_request_context, mock_llm_inference)

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


class TestSummarize:
    """Test _summarize method."""

    def test_summarize_with_content(self, minimal_request_context, mock_llm_inference):
        """Test summarizing content using LLM."""
        builder = ContextBuilder(minimal_request_context, mock_llm_inference)
        content = "This is a long piece of content that needs to be summarized to reduce token usage and fit within budget constraints."

        summary, token_count = builder._summarize(content, 1024)

        # Summary should be shorter than original
        assert len(summary.split()) < len(content.split())
        # Token count should match the summary
        assert token_count == len(summary.split())
        # LLM generate should have been called
        mock_llm_inference.generate.assert_called_once()
        # Generate should be called with lower temperature for consistency
        call_kwargs = mock_llm_inference.generate.call_args[1]
        assert call_kwargs['temperature'] == 0.3

    def test_summarize_empty_content(self, minimal_request_context, mock_llm_inference):
        """Test summarizing empty content."""
        builder = ContextBuilder(minimal_request_context, mock_llm_inference)

        summary, token_count = builder._summarize("", 1024)

        assert summary == ""
        assert token_count == 0
        # LLM should not be called for empty content
        mock_llm_inference.generate.assert_not_called()

    def test_summarize_whitespace_only(self, minimal_request_context, mock_llm_inference):
        """Test summarizing whitespace-only content."""
        builder = ContextBuilder(minimal_request_context, mock_llm_inference)

        summary, token_count = builder._summarize("   \n  \t  ", 1024)

        assert summary == ""
        assert token_count == 0
        # LLM should not be called for whitespace-only content
        mock_llm_inference.generate.assert_not_called()

    def test_summarize_with_llm_failure(self, minimal_request_context, mock_llm_inference):
        """Test that summarize raises ValueError when LLM fails."""
        builder = ContextBuilder(minimal_request_context, mock_llm_inference)
        content = "Content to summarize"

        # Make generate raise an exception
        mock_llm_inference.generate.side_effect = RuntimeError("LLM error")

        # Should raise ValueError when summarization fails
        with pytest.raises(ValueError, match="Text summarization failed"):
            builder._summarize(content, 1024)

    def test_get_content_uses_summarize(self, minimal_request_context, mock_llm_inference):
        """Test that _get_content calls _summarize for SUMMARIZED strategy when over budget."""
        builder = ContextBuilder(minimal_request_context, mock_llm_inference)

        # Create content that exceeds budget
        long_content = " ".join(["word"] * 100)  # 100 words
        element = ContextItem(
            tag='TEST',
            role=ContextRole.USER,
            content=long_content,
            token_budget=10,  # Only 10 tokens allowed
            summarization_strategy=SummarizationStrategy.SUMMARIZED
        )

        content, token_count = builder._get_content(element, 10)

        # Generate should have been called to summarize
        mock_llm_inference.generate.assert_called_once()
        # The result should be a summary
        assert len(content.split()) < len(long_content.split())


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_system_prompt(self, minimal_request_context, mock_llm_inference):
        """Test adding empty system prompt."""
        builder = ContextBuilder(minimal_request_context, mock_llm_inference)

        builder.add_system_prompt("")

        assert len(builder._elements) == 1
        # Should still have newline
        assert builder._elements[0].content == "\n"

    def test_multiple_worldbuilding_calls(self, full_request_context):
        """Test calling add_worldbuilding multiple times."""
        builder = ContextBuilder(full_request_context, mock_llm_inference)

        builder.add_worldbuilding()
        builder.add_worldbuilding()

        # Should add element each time
        assert len(builder._elements) == 2

    def test_all_hidden_characters(self):
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

        builder = ContextBuilder(context, mock_llm_inference)
        builder.add_characters()

        # Should not add any elements
        assert len(builder._elements) == 0
