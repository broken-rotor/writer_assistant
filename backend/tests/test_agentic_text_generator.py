"""
Tests for AgenticTextGenerator class.

This tests the core agentic generation logic with iterative refinement.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import re

from app.services.agentic_text_generator import (
    AgenticTextGenerator,
    AgenticTool,
    LLMGenerationTool
)
from app.models.agentic_models import AgenticConfig
from app.models.streaming_models import (
    StreamingStatusEvent,
    StreamingResultEvent,
    StreamingErrorEvent
)
from app.services.context_builder import ContextBuilder
from app.models.request_context import (
    RequestContext,
    StoryConfiguration,
    SystemPrompts,
    WorldbuildingInfo,
    StoryOutline,
    RequestContextMetadata
)


@pytest.fixture
def mock_llm():
    """Create a mock LLM for testing"""
    llm = MagicMock()

    # Mock tokenization
    def count_tokens(text):
        return len(text.split())

    llm.count_tokens.side_effect = count_tokens
    llm.count_tokens_batch.side_effect = lambda texts: [count_tokens(t) for t in texts]

    # Mock truncation
    def truncate_to_tokens(text, max_tokens):
        from app.services.llm_inference import TokenTruncation
        words = text.split()
        if len(words) <= max_tokens:
            return TokenTruncation(tail=text, tail_token_count=len(words))
        return TokenTruncation(
            tail=' '.join(words[:max_tokens]),
            tail_token_count=max_tokens
        )

    llm.truncate_to_tokens.side_effect = truncate_to_tokens

    return llm


@pytest.fixture
def simple_context_builder(mock_llm):
    """Create a simple context builder for testing"""
    context = RequestContext(
        configuration=StoryConfiguration(
            system_prompts=SystemPrompts(
                main_prefix="You are a helpful assistant.",
                main_suffix="",
                assistant_prompt="Be creative.",
                editor_prompt=""
            ),
            raters=[],
            generation_preferences={}
        ),
        worldbuilding=WorldbuildingInfo(
            content="A fantasy world",
            chat_history=[],
            key_elements=[]
        ),
        characters=[],
        story_outline=StoryOutline(
            summary="A story",
            status="draft",
            content="",
            outline_items=[],
            rater_feedback=[],
            chat_history=[]
        ),
        chapters=[],
        context_metadata=RequestContextMetadata(
            story_id="test-id",
            story_title="Test Story",
            version="1.0",
            created_at="2024-01-01T00:00:00",
            total_characters=0,
            total_chapters=0,
            total_word_count=0,
            context_size_estimate=0,
            processing_hints={}
        )
    )

    return ContextBuilder(context, mock_llm)


class TestAgenticConfig:
    """Test AgenticConfig model"""

    def test_default_config(self):
        """Test default configuration values"""
        config = AgenticConfig()

        assert config.max_iterations == 3
        assert config.generation_temperature == 0.8
        assert config.generation_max_tokens == 2000
        assert config.evaluation_temperature == 0.3
        assert config.evaluation_max_tokens == 500

    def test_custom_config(self):
        """Test custom configuration values"""
        config = AgenticConfig(
            max_iterations=5,
            generation_temperature=0.9,
            generation_max_tokens=3000,
            evaluation_temperature=0.2,
            evaluation_max_tokens=1000
        )

        assert config.max_iterations == 5
        assert config.generation_temperature == 0.9
        assert config.generation_max_tokens == 3000
        assert config.evaluation_temperature == 0.2
        assert config.evaluation_max_tokens == 1000

    def test_config_validation(self):
        """Test configuration validation"""
        # Max iterations must be >= 1
        with pytest.raises(ValueError):
            AgenticConfig(max_iterations=0)

        # Max iterations must be <= 10
        with pytest.raises(ValueError):
            AgenticConfig(max_iterations=11)

        # Temperature must be >= 0
        with pytest.raises(ValueError):
            AgenticConfig(generation_temperature=-0.1)

        # Max tokens must be >= 100
        with pytest.raises(ValueError):
            AgenticConfig(generation_max_tokens=50)


class TestLLMGenerationTool:
    """Test LLMGenerationTool"""

    @pytest.mark.asyncio
    async def test_llm_generation_tool_execute(self, mock_llm, simple_context_builder):
        """Test LLM generation tool execution"""
        tool = LLMGenerationTool(mock_llm)

        # Mock streaming response
        def chat_completion_stream(*args, **kwargs):
            yield "Generated "
            yield "text "
            yield "content"

        mock_llm.chat_completion_stream = chat_completion_stream

        result = await tool.execute(simple_context_builder)

        assert result == "Generated text content"

    @pytest.mark.asyncio
    async def test_llm_generation_tool_with_parameters(self, mock_llm, simple_context_builder):
        """Test LLM generation tool with custom parameters"""
        tool = LLMGenerationTool(mock_llm)

        # Mock streaming response
        def chat_completion_stream(messages, temperature=0.8, max_tokens=2000):
            # Verify parameters were passed
            assert temperature == 0.5
            assert max_tokens == 1000
            yield "test"

        mock_llm.chat_completion_stream = chat_completion_stream

        result = await tool.execute(simple_context_builder, temperature=0.5, max_tokens=1000)

        assert result == "test"


class TestAgenticTextGenerator:
    """Test AgenticTextGenerator"""

    def test_initialization(self, mock_llm):
        """Test agent initialization"""
        agent = AgenticTextGenerator(mock_llm)

        assert agent.llm == mock_llm
        assert isinstance(agent.config, AgenticConfig)
        assert 'llm_generate' in agent.tools
        assert isinstance(agent.tools['llm_generate'], LLMGenerationTool)

    def test_initialization_with_config(self, mock_llm):
        """Test agent initialization with custom config"""
        config = AgenticConfig(max_iterations=5)
        agent = AgenticTextGenerator(mock_llm, config=config)

        assert agent.config.max_iterations == 5

    def test_add_tool(self, mock_llm):
        """Test adding custom tool to agent"""
        agent = AgenticTextGenerator(mock_llm)

        # Create mock tool
        class MockTool(AgenticTool):
            async def execute(self, context_builder, **kwargs):
                return "mock result"

        tool = MockTool()
        agent.add_tool('mock_tool', tool)

        assert 'mock_tool' in agent.tools
        assert agent.tools['mock_tool'] == tool

    @pytest.mark.asyncio
    async def test_generate_success_first_iteration(self, mock_llm, simple_context_builder):
        """Test successful generation on first iteration"""
        agent = AgenticTextGenerator(mock_llm, config=AgenticConfig(max_iterations=3))

        # Mock LLM responses
        generated_content = "This is the generated content with sufficient detail."
        evaluation_response = "PASSED: YES\nFEEDBACK: The content meets all criteria."

        call_count = [0]

        def chat_completion_stream(messages, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call - generation
                yield generated_content
            else:
                # Second call - evaluation
                yield evaluation_response

        mock_llm.chat_completion_stream = chat_completion_stream

        events = []
        async for event in agent.generate(
            base_context_builder=simple_context_builder,
            content="Original content",
            initial_generation_prompt="Generate something good",
            evaluation_criteria="Must be good"
        ):
            events.append(event)

        # Verify we got events
        assert len(events) > 0

        # Should have status events
        status_events = [e for e in events if isinstance(e, StreamingStatusEvent)]
        assert len(status_events) > 0

        # Should have a result event with success
        result_events = [e for e in events if isinstance(e, StreamingResultEvent)]
        assert len(result_events) == 1

        result = result_events[0]
        assert result.data['status'] == 'success'
        assert result.data['content'] == generated_content
        assert result.data['iterations_used'] == 1

    @pytest.mark.asyncio
    async def test_generate_multiple_iterations(self, mock_llm, simple_context_builder):
        """Test generation with multiple iterations before success"""
        agent = AgenticTextGenerator(mock_llm, config=AgenticConfig(max_iterations=3))

        # Mock LLM responses - fail first, then succeed
        call_count = [0]

        def chat_completion_stream(messages, **kwargs):
            call_count[0] += 1

            # Alternate between generation and evaluation
            if call_count[0] == 1:
                # First generation
                yield "First attempt content"
            elif call_count[0] == 2:
                # First evaluation - fail
                yield "PASSED: NO\nFEEDBACK: Needs improvement"
            elif call_count[0] == 3:
                # Second generation
                yield "Improved content"
            elif call_count[0] == 4:
                # Second evaluation - pass
                yield "PASSED: YES\nFEEDBACK: Excellent work"

        mock_llm.chat_completion_stream = chat_completion_stream

        events = []
        async for event in agent.generate(
            base_context_builder=simple_context_builder,
            content="Original content",
            initial_generation_prompt="Generate something",
            evaluation_criteria="Must be excellent"
        ):
            events.append(event)

        # Should have result with 2 iterations
        result_events = [e for e in events if isinstance(e, StreamingResultEvent)]
        assert len(result_events) == 1
        assert result_events[0].data['iterations_used'] == 2
        assert result_events[0].data['content'] == "Improved content"

    @pytest.mark.asyncio
    async def test_generate_max_iterations_exceeded(self, mock_llm, simple_context_builder):
        """Test when max iterations is reached without passing"""
        agent = AgenticTextGenerator(mock_llm, config=AgenticConfig(max_iterations=2))

        # Mock LLM responses - always fail evaluation
        call_count = [0]

        def chat_completion_stream(messages, **kwargs):
            call_count[0] += 1

            if call_count[0] % 2 == 1:
                # Generation
                yield f"Attempt {(call_count[0] + 1) // 2} content"
            else:
                # Evaluation - always fail
                yield "PASSED: NO\nFEEDBACK: Still not good enough"

        mock_llm.chat_completion_stream = chat_completion_stream

        events = []
        async for event in agent.generate(
            base_context_builder=simple_context_builder,
            content="Original content",
            initial_generation_prompt="Generate something",
            evaluation_criteria="Must be perfect"
        ):
            events.append(event)

        # Should have error event for max iterations
        error_events = [e for e in events if isinstance(e, StreamingErrorEvent)]
        assert len(error_events) == 1
        assert error_events[0].error_code == 'MAX_ITERATIONS_EXCEEDED'
        assert 'last_content' in error_events[0].data
        assert 'last_feedback' in error_events[0].data

    @pytest.mark.asyncio
    async def test_generate_with_exception(self, mock_llm, simple_context_builder):
        """Test error handling during generation"""
        agent = AgenticTextGenerator(mock_llm, config=AgenticConfig(max_iterations=3))

        # Mock LLM to raise exception
        def chat_completion_stream(*args, **kwargs):
            raise RuntimeError("LLM error")

        mock_llm.chat_completion_stream = chat_completion_stream

        events = []
        async for event in agent.generate(
            base_context_builder=simple_context_builder,
            content="Original content",
            initial_generation_prompt="Generate something",
            evaluation_criteria="Must be good"
        ):
            events.append(event)

        # Should have error event
        error_events = [e for e in events if isinstance(e, StreamingErrorEvent)]
        assert len(error_events) == 1
        assert error_events[0].error_code == 'ITERATION_ERROR'
        assert 'LLM error' in error_events[0].message

    @pytest.mark.asyncio
    async def test_evaluate_content_pass(self, mock_llm, simple_context_builder):
        """Test evaluation that passes"""
        agent = AgenticTextGenerator(mock_llm)

        # Mock evaluation response
        def chat_completion_stream(*args, **kwargs):
            yield "PASSED: YES\nFEEDBACK: Everything looks great!"

        mock_llm.chat_completion_stream = chat_completion_stream

        passed, feedback = await agent._evaluate_content(
            simple_context_builder,
            "Test content",
            "Must be good"
        )

        assert passed is True
        assert "Everything looks great!" in feedback

    @pytest.mark.asyncio
    async def test_evaluate_content_fail(self, mock_llm, simple_context_builder):
        """Test evaluation that fails"""
        agent = AgenticTextGenerator(mock_llm)

        # Mock evaluation response
        def chat_completion_stream(*args, **kwargs):
            yield "PASSED: NO\nFEEDBACK: Needs significant improvement in structure."

        mock_llm.chat_completion_stream = chat_completion_stream

        passed, feedback = await agent._evaluate_content(
            simple_context_builder,
            "Test content",
            "Must be excellent"
        )

        assert passed is False
        assert "improvement" in feedback.lower()

    def test_refine_prompt(self, mock_llm):
        """Test prompt refinement"""
        agent = AgenticTextGenerator(mock_llm)

        original_prompt = "Write a good story"
        feedback = "The story lacks detail and character development"

        refined = agent._refine_prompt(original_prompt, feedback)

        # Should include original prompt
        assert "Write a good story" in refined
        # Should include feedback
        assert "lacks detail" in refined
        # Should have refinement section
        assert "ITERATION_REFINEMENT" in refined

    def test_calculate_progress(self, mock_llm):
        """Test progress calculation"""
        agent = AgenticTextGenerator(mock_llm, config=AgenticConfig(max_iterations=3))

        # Test different phases
        progress_gen_1 = agent._calculate_progress(1, 'generate')
        progress_eval_1 = agent._calculate_progress(1, 'evaluate')
        progress_gen_2 = agent._calculate_progress(2, 'generate')

        # Progress should increase through phases and iterations
        assert 0 <= progress_gen_1 <= 100
        assert 0 <= progress_eval_1 <= 100
        assert 0 <= progress_gen_2 <= 100
        assert progress_gen_1 < progress_eval_1
        assert progress_eval_1 < progress_gen_2

        # Should cap at 95%
        progress_high = agent._calculate_progress(10, 'refine')
        assert progress_high <= 95

    @pytest.mark.asyncio
    async def test_generate_emits_correct_event_sequence(self, mock_llm, simple_context_builder):
        """Test that events are emitted in correct sequence"""
        agent = AgenticTextGenerator(mock_llm, config=AgenticConfig(max_iterations=1))

        # Mock LLM for quick success
        call_count = [0]

        def chat_completion_stream(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                yield "Generated content"
            else:
                yield "PASSED: YES\nFEEDBACK: Good"

        mock_llm.chat_completion_stream = chat_completion_stream

        events = []
        async for event in agent.generate(
            base_context_builder=simple_context_builder,
            content="Original",
            initial_generation_prompt="Generate",
            evaluation_criteria="Good"
        ):
            events.append(event)

        # Verify event types in sequence
        event_types = [type(e).__name__ for e in events]

        # Should have StatusEvent -> StatusEvent -> ResultEvent pattern
        assert 'StreamingStatusEvent' in event_types
        assert 'StreamingResultEvent' in event_types

        # Result should be last
        assert isinstance(events[-1], StreamingResultEvent)
