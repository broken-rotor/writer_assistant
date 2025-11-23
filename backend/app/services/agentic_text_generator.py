"""
Agentic text generation service with iterative refinement.

This module implements an agentic system that:
1. Generates text using LLM
2. Evaluates the result against criteria
3. Refines and retries if evaluation fails
4. Returns final result after success or max iterations

The system is designed to be extensible with additional tools (RAG, web search, etc.)
"""

import logging
import re
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import AsyncIterator, Dict, Optional

from app.models.agentic_models import AgenticConfig
from app.models.streaming_models import (
    StreamingStatusEvent,
    StreamingResultEvent,
    StreamingErrorEvent
)
from app.services.context_builder import ContextBuilder
from app.services.llm_inference import LLMInference

logger = logging.getLogger(__name__)


class AgenticTool(ABC):
    """Base class for tools the agent can use."""

    @abstractmethod
    async def execute(self, context_builder: ContextBuilder, **kwargs) -> str:
        """
        Execute the tool and return result.

        Args:
            context_builder: ContextBuilder with current context
            **kwargs: Tool-specific parameters

        Returns:
            Tool execution result as string
        """
        pass


class LLMGenerationTool(AgenticTool):
    """Tool for LLM text generation."""

    def __init__(self, llm: LLMInference):
        self.llm = llm

    async def execute(
        self,
        context_builder: ContextBuilder,
        temperature: float = 0.8,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> str:
        """
        Generate text using the LLM.

        Args:
            context_builder: ContextBuilder with prompts and context
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream token-by-token

        Returns:
            Generated text
        """
        messages = context_builder.build_messages()

        if stream:
            content = ""
            for token in self.llm.chat_completion_stream(
                messages, temperature=temperature, max_tokens=max_tokens
            ):
                content += token
            return content
        else:
            return self.llm.chat_completion(
                messages, temperature=temperature, max_tokens=max_tokens
            )


class AgenticTextGenerator:
    """
    Agentic text generation with iterative refinement.

    The agent performs generate → evaluate → refine cycles until:
    - Evaluation criteria are met, OR
    - Max iterations reached

    Future expansion: Add more tools (web search, RAG, calculators, etc.)
    """

    def __init__(self, llm: LLMInference):
        """
        Initialize the agentic text generator.

        Args:
            llm: LLMInference instance for text generation
        """
        self.llm = llm
        self.tools: Dict[str, AgenticTool] = {
            'llm_generate': LLMGenerationTool(llm)
        }

    def add_tool(self, name: str, tool: AgenticTool):
        """
        Register a new tool for the agent to use.

        Args:
            name: Tool identifier
            tool: AgenticTool instance
        """
        self.tools[name] = tool
        logger.info(f"Registered tool: {name}")

    async def generate(
        self,
        base_context_builder: ContextBuilder,
        initial_generation_prompt: str,
        evaluation_criteria: str,
        config: Optional[AgenticConfig] = None
    ) -> AsyncIterator:
        """
        Agentic text generation with evaluation loop.

        Args:
            base_context_builder: Pre-configured ContextBuilder with long-term context
                                  (system prompts, characters, worldbuilding, recent story, etc.)
                                  The agent will COPY this and add iteration-specific instructions.
            initial_generation_prompt: Initial instruction for generation
            evaluation_criteria: Criteria for evaluating success
            config: Agentic behavior configuration (uses defaults if None)

        Yields:
            SSE events (StreamingStatusEvent, StreamingResultEvent, StreamingErrorEvent)
        """
        config = config or AgenticConfig()

        current_prompt = initial_generation_prompt
        previous_content = None
        last_feedback = ""

        for iteration in range(1, config.max_iterations + 1):
            try:
                # === GENERATION PHASE ===
                yield StreamingStatusEvent(
                    phase='generating',
                    message=f'Iteration {iteration}/{config.max_iterations}: Generating content...',
                    progress=self._calculate_progress(iteration, config.max_iterations, 'generate')
                )

                # Copy base context and add current generation prompt
                generation_context = self._copy_context_builder(base_context_builder)
                generation_context.add_agent_instruction(current_prompt)

                # Generate using LLM tool
                content = await self.tools['llm_generate'].execute(
                    generation_context,
                    temperature=config.generation_temperature,
                    max_tokens=config.generation_max_tokens,
                    stream=config.stream_partial_content
                )

                logger.info(f"Generated {len(content)} characters in iteration {iteration}")

                # === EVALUATION PHASE ===
                yield StreamingStatusEvent(
                    phase='evaluating',
                    message=f'Iteration {iteration}/{config.max_iterations}: Evaluating against criteria...',
                    progress=self._calculate_progress(iteration, config.max_iterations, 'evaluate')
                )

                passed, feedback = await self._evaluate_content(
                    base_context_builder,
                    content,
                    evaluation_criteria,
                    config
                )

                last_feedback = feedback
                logger.info(f"Evaluation result for iteration {iteration}: {'PASSED' if passed else 'FAILED'}")

                # Yield partial result with evaluation
                yield StreamingStatusEvent(
                    phase="evaluated",
                    message=f"Iteration {iteration}/{config.max_iterations}: Evaluated content as passed={passed}",
                    progress=self._calculate_progress(iteration, config.max_iterations, 'evaluate'),
                    data={
                        "content": content,
                        "iteration": iteration,
                        "evaluation_feedback": feedback,
                        "passed_evaluation": passed
                    }    
                )

                if passed:
                    # Success! Return final result
                    logger.info(f"Successfully completed in {iteration} iteration(s)")
                    yield StreamingResultEvent(
                        data={
                            'content': content,
                            'iterations_used': iteration,
                            'evaluation_feedback': feedback,
                            'status': 'success'
                        }
                    )
                    return

                # === REFINEMENT PHASE ===
                if iteration < config.max_iterations:
                    yield StreamingStatusEvent(
                        phase='refining',
                        message=f'Iteration {iteration}/{config.max_iterations}: Preparing refinement based on feedback...',
                        progress=self._calculate_progress(iteration, config.max_iterations, 'refine')
                    )

                    current_prompt = self._refine_prompt(
                        initial_generation_prompt,
                        content,
                        feedback,
                        iteration
                    )
                    previous_content = content

            except Exception as e:
                logger.exception(f"Error in iteration {iteration}")
                yield StreamingErrorEvent(
                    message=f"Error in iteration {iteration}: {str(e)}",
                    error_code='ITERATION_ERROR'
                )
                return

        # Max iterations reached without passing evaluation
        logger.warning(f"Max iterations ({config.max_iterations}) reached without passing evaluation")
        yield StreamingErrorEvent(
            message=f'Max iterations ({config.max_iterations}) reached. Last feedback: {last_feedback}',
            error_code='MAX_ITERATIONS_EXCEEDED',
            data={'last_content': content, 'last_feedback': last_feedback}
        )

    async def _evaluate_content(
        self,
        base_context_builder: ContextBuilder,
        content: str,
        evaluation_criteria: str,
        config: AgenticConfig
    ) -> tuple[bool, str]:
        """
        Evaluate generated content against criteria using a separate LLM call.

        Args:
            base_context_builder: Base context (though we build minimal eval context)
            content: Generated content to evaluate
            evaluation_criteria: Criteria for success
            config: Configuration with evaluation parameters

        Returns:
            Tuple of (passed: bool, feedback: str)
        """
        # Build minimal evaluation context
        # We use a fresh copy but could also build completely new context
        eval_context = self._copy_context_builder(base_context_builder)

        eval_prompt = f"""You are an evaluation agent. Your job is to critically assess whether the generated content meets ALL specified criteria.

<EVALUATION_CRITERIA>
{evaluation_criteria}
</EVALUATION_CRITERIA>

<GENERATED_CONTENT>
{content}
</GENERATED_CONTENT>

Carefully review each criterion and determine if the content fully satisfies it.

Respond in this exact format:
PASSED: [YES or NO]
FEEDBACK: [Detailed explanation of what works well and what needs improvement. If PASSED is NO, be specific about what must change.]
"""

        eval_context.add_agent_instruction(eval_prompt)

        # Use LLM tool for evaluation
        response = await self.tools['llm_generate'].execute(
            eval_context,
            temperature=config.evaluation_temperature,
            max_tokens=config.evaluation_max_tokens,
            stream=False
        )

        # Parse evaluation response
        passed_match = re.search(r'PASSED:\s*(YES|NO)', response, re.IGNORECASE)
        passed = passed_match and passed_match.group(1).upper() == 'YES' if passed_match else False

        feedback_match = re.search(r'FEEDBACK:\s*(.+)', response, re.DOTALL | re.IGNORECASE)
        feedback = feedback_match.group(1).strip() if feedback_match else response

        return passed, feedback

    def _refine_prompt(
        self,
        original_prompt: str,
        previous_content: str,
        evaluation_feedback: str,
        iteration: int
    ) -> str:
        """
        Refine the generation prompt based on evaluation feedback.

        This creates a new prompt that includes the original requirements
        plus specific guidance on addressing the evaluation feedback.

        Args:
            original_prompt: Original generation instructions
            previous_content: Content from previous iteration
            evaluation_feedback: Feedback from evaluation
            iteration: Current iteration number

        Returns:
            Refined prompt for next iteration
        """
        return f"""{original_prompt}

<ITERATION_REFINEMENT>
Your previous attempt (iteration {iteration}) did not fully meet the evaluation criteria.

Evaluation Feedback:
{evaluation_feedback}

Please generate a NEW version that addresses these specific concerns while still meeting all the original requirements above.
Focus on the areas identified in the feedback while maintaining overall quality.
</ITERATION_REFINEMENT>"""

    def _copy_context_builder(self, context_builder: ContextBuilder) -> ContextBuilder:
        """
        Create a deep copy of the context builder for this iteration.

        This ensures each iteration starts fresh without polluting the base context.

        Args:
            context_builder: Original context builder

        Returns:
            Deep copy of the context builder
        """
        # Create new instance with same request_context and model
        new_builder = ContextBuilder(
            context_builder._request_context,
            context_builder._model
        )
        # Deep copy the elements list
        new_builder._elements = deepcopy(context_builder._elements)
        return new_builder

    def _calculate_progress(self, iteration: int, max_iterations: int, phase: str) -> int:
        """
        Calculate progress percentage based on iteration and phase.

        Args:
            iteration: Current iteration number (1-based)
            max_iterations: Maximum iterations configured
            phase: Current phase ('generate', 'evaluate', 'refine')

        Returns:
            Progress percentage (0-100)
        """
        # Phase weights for progress within an iteration
        phase_weights = {'generate': 0.3, 'evaluate': 0.7, 'refine': 0.9}

        # Base progress from completed iterations
        base_progress = ((iteration - 1) / max_iterations) * 100

        # Add progress within current iteration
        phase_progress = (phase_weights.get(phase, 0.5) / max_iterations) * 100

        # Cap at 95% to leave room for finalization
        return min(95, int(base_progress + phase_progress))
