"""
Context Optimization Service for Writer Assistant

This service provides transparent context optimization for existing generation endpoints.
It integrates with the Context Manager system to automatically optimize context when
token limits are approached, while maintaining complete API compatibility.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

from app.services.context_manager import ContextManager, ContextItem, ContextAnalysis
from app.models.context_models import ContextType
from app.services.token_management.layers import LayerType
from app.services.content_prioritization import (
    LayeredPrioritizer, RAGRetriever, RetrievalStrategy, RetrievalMode,
    PrioritizationConfig, AgentType
)
from app.services.context_distillation import (
    AdaptiveSummarizationEngine, AdaptiveSummarizationConfig, GenerationType
)
from app.services.llm_inference import get_llm
from app.utils.relevance_calculator import ContentCategory, ContentItem
from app.models.generation_models import (
    SystemPrompts, CharacterInfo, ChapterInfo, FeedbackItem
)
from app.models.context_models import AgentType as ContextAgentType, ComposePhase

logger = logging.getLogger(__name__)


@dataclass
class OptimizedContext:
    """Result of context optimization with optimized content and metadata."""
    system_prompt: str
    user_message: str
    total_tokens: int
    optimization_applied: bool
    compression_ratio: float
    metadata: Dict[str, Any]


class ContextOptimizationService:
    """
    Service for transparent context optimization in generation endpoints.

    This service analyzes context size and applies optimization when needed,
    while maintaining complete compatibility with existing API contracts.
    """

    def __init__(
        self,
        max_context_tokens: int = 8000,
        optimization_threshold: int = 6000,
        enable_optimization: bool = True
    ):
        """
        Initialize the context optimization service.

        Args:
            max_context_tokens: Maximum tokens allowed in context
            optimization_threshold: Token count that triggers optimization
            enable_optimization: Whether to enable automatic optimization
        """
        self.max_context_tokens = max_context_tokens
        self.optimization_threshold = optimization_threshold
        self.enable_optimization = enable_optimization

        # Initialize context manager
        self.context_manager = ContextManager()

        # Initialize content prioritization components
        self.layered_prioritizer = LayeredPrioritizer(
            config=PrioritizationConfig(
                token_budget=max_context_tokens // 4,  # Allocate 25% for Layer D
                max_items_per_category=10,
                min_score_threshold=0.1
            )
        )

        self.rag_retriever = RAGRetriever()

        # Initialize adaptive summarization engine
        try:
            llm_service = get_llm()
            self.adaptive_summarizer = AdaptiveSummarizationEngine(
                llm_service=llm_service,
                config=AdaptiveSummarizationConfig()
            )
        except Exception as e:
            logger.warning(f"Failed to initialize adaptive summarizer: {e}")
            self.adaptive_summarizer = None

        logger.info(
            f"ContextOptimizationService initialized: max_tokens={max_context_tokens}, threshold={optimization_threshold}")

    def _apply_adaptive_summarization(
        self,
        content: str,
        target_tokens: int,
        generation_type: GenerationType,
        context_type: Optional[ContextType] = None,
        agent_type: Optional[ContextAgentType] = None,
        compose_phase: Optional[ComposePhase] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Apply adaptive summarization to content using the appropriate strategy.
        
        Returns:
            Tuple of (summarized_content, metadata)
        """
        if not self.adaptive_summarizer:
            # Fallback to simple truncation if adaptive summarizer is not available
            words = content.split()
            if len(words) > target_tokens:
                truncated = " ".join(words[:target_tokens])
                return truncated, {"fallback_truncation": True, "original_tokens": len(words)}
            return content, {"no_summarization_needed": True}
        
        try:
            result = self.adaptive_summarizer.summarize_adaptively(
                content=content,
                target_tokens=target_tokens,
                generation_type=generation_type,
                context_type=context_type,
                agent_type=agent_type,
                compose_phase=compose_phase,
                additional_context=additional_context or {}
            )
            
            return result.summary, {
                "adaptive_summarization": True,
                "strategies_used": result.strategies_used,
                "quality_score": result.quality_score,
                "compression_ratio": result.compression_ratio,
                "key_information": result.key_information,
                "warnings": result.warnings
            }
            
        except Exception as e:
            logger.error(f"Adaptive summarization failed: {e}")
            # Fallback to simple truncation
            words = content.split()
            if len(words) > target_tokens:
                truncated = " ".join(words[:target_tokens])
                return truncated, {"fallback_after_error": True, "error": str(e)}
            return content, {"error_but_no_truncation_needed": True, "error": str(e)}

    def optimize_chapter_generation_context(
        self,
        system_prompts: SystemPrompts,
        worldbuilding: str,
        story_summary: str,
        characters: List[CharacterInfo],
        plot_point: str,
        incorporated_feedback: List[FeedbackItem],
        previous_chapters: Optional[List[ChapterInfo]] = None,
        compose_phase: Optional[Any] = None,
        phase_context: Optional[Any] = None
    ) -> OptimizedContext:
        """
        Optimize context for chapter generation endpoint.

        Args:
            system_prompts: System prompts configuration
            worldbuilding: World building information
            story_summary: Story summary
            characters: Character information
            plot_point: Plot point for the chapter
            incorporated_feedback: Feedback items to incorporate
            previous_chapters: Previous chapters (optional)

        Returns:
            OptimizedContext with system prompt and user message
        """
        try:
            # Build context items with priorities
            context_items = []

            # System prompts (highest priority)
            system_content = f"{system_prompts.mainPrefix}\n{system_prompts.assistantPrompt or ''}\n{system_prompts.mainSuffix}".strip()
            context_items.append(ContextItem(
                content=system_content,
                context_type=ContextType.SYSTEM_PROMPT,
                priority=10,
                layer_type=LayerType.WORKING_MEMORY,
                metadata={"source": "system_prompts"}
            ))

            # Plot point (very high priority - this is the main task)
            context_items.append(ContextItem(
                content=f"Plot point for this chapter: {plot_point}",
                context_type=ContextType.STORY_SUMMARY,
                priority=9,
                layer_type=LayerType.WORKING_MEMORY,
                metadata={"source": "plot_point"}
            ))

            # Characters (high priority, but can be compressed)
            # Use RAG retriever to get most relevant characters for this plot point
            try:
                character_content_items = []
                current_time = datetime.now()
                for i, char in enumerate(characters):
                    char_content = f"{char.name}: {char.basicBio} (Personality: {char.personality})"
                    if hasattr(char, 'motivations') and char.motivations:
                        char_content += f" (Motivations: {char.motivations})"
                    if hasattr(char, 'fears') and char.fears:
                        char_content += f" (Fears: {char.fears})"

                    character_content_items.append(ContentItem(
                        id=f"char_{i}_{char.name}",
                        content=char_content,
                        category=ContentCategory.CHARACTER,
                        created_at=current_time,
                        last_accessed=current_time,
                        access_count=1,
                        character_names={char.name},
                        metadata={'name': char.name, 'source': 'character_info'}
                    ))

                # Use RAG retriever to prioritize characters based on plot point relevance
                if character_content_items:
                    # Convert plot_point string to proper context dictionary
                    context_dict = {
                        'keywords': plot_point.lower().split(),  # Extract keywords from plot point
                        'active_characters': [char.name for char in characters],  # All characters are potentially active
                        'active_locations': [],  # Could be extracted from plot_point if needed
                        'current_scene_type': 'chapter_generation'
                    }

                    prioritized_chars = self.layered_prioritizer.prioritize_content(
                        content_items=character_content_items,
                        context=context_dict,
                        agent_type=AgentType.WRITER,
                        token_budget=1000  # Allocate up to 1000 tokens for characters
                    )

                    char_context = "\n".join([
                        f"- {content_score.content_item.content}"
                        for content_score in prioritized_chars.selected_content[:5]
                    ])
                else:
                    char_context = "\n".join([
                        f"- {c.name}: {c.basicBio} (Personality: {c.personality})"
                        for c in characters[:5]  # Fallback to simple format
                    ])
            except Exception as e:
                logger.warning(f"Character prioritization failed, using fallback: {str(e)}")
                char_context = "\n".join([
                    f"- {c.name}: {c.basicBio} (Personality: {c.personality})"
                    for c in characters[:5]  # Fallback to simple format
                ])

            context_items.append(ContextItem(
                content=f"Characters:\n{char_context}",
                context_type=ContextType.CHARACTER_PROFILE,
                priority=8,
                layer_type=LayerType.WORKING_MEMORY,
                metadata={"source": "characters", "count": len(characters)}
            ))

            # Story summary (medium-high priority)
            context_items.append(ContextItem(
                content=f"Story: {story_summary}",
                context_type=ContextType.STORY_SUMMARY,
                priority=7,
                layer_type=LayerType.EPISODIC_MEMORY,
                metadata={"source": "story_summary"}
            ))

            # World building (medium priority, can be compressed significantly)
            context_items.append(ContextItem(
                content=f"World: {worldbuilding}",
                context_type=ContextType.WORLD_BUILDING,
                priority=6,
                layer_type=LayerType.LONG_TERM_MEMORY,
                metadata={"source": "worldbuilding"}
            ))

            # Incorporated feedback (lower priority)
            if incorporated_feedback:
                feedback_content = "Incorporated feedback:\n" + "\n".join([
                    f"- {f.content}" for f in incorporated_feedback[:5]
                ])
                context_items.append(ContextItem(
                    content=feedback_content,
                    context_type=ContextType.USER_FEEDBACK,
                    priority=5,
                    layer_type=LayerType.AGENT_SPECIFIC_MEMORY,
                    metadata={"source": "feedback", "count": len(incorporated_feedback)}
                ))

            # Previous chapters (lowest priority, most compressible)
            if previous_chapters:
                chapters_content = "Previous chapters:\n" + "\n".join([
                    f"Chapter {c.number}: {c.title}\n{c.content[:200]}..."
                    for c in previous_chapters[-3:]  # Only last 3 chapters
                ])
                context_items.append(ContextItem(
                    content=chapters_content,
                    context_type=ContextType.CHARACTER_MEMORY,
                    priority=3,
                    layer_type=LayerType.EPISODIC_MEMORY,
                    metadata={"source": "previous_chapters", "count": len(previous_chapters)}
                ))

            # Analyze and optimize context
            return self._optimize_context_items(
                context_items=context_items,
                task_description="Write an engaging chapter (800-1500 words) that brings this plot point to life with vivid prose, authentic dialogue, and character development.",
                generation_type=GenerationType.CHAPTER_GENERATION,
                agent_type=ContextAgentType.WRITER,
                compose_phase=compose_phase
            )

        except Exception as e:
            logger.error(f"Error in chapter context optimization: {str(e)}")
            # Fall back to basic context building
            return self._build_fallback_chapter_context(
                system_prompts, worldbuilding, story_summary, characters, plot_point, incorporated_feedback
            )

    def optimize_character_feedback_context(
        self,
        system_prompts: SystemPrompts,
        worldbuilding: str,
        story_summary: str,
        character: CharacterInfo,
        plot_point: str,
        compose_phase: Optional[Any] = None,
        phase_context: Optional[Any] = None
    ) -> OptimizedContext:
        """
        Optimize context for character feedback endpoint.

        Args:
            system_prompts: System prompts configuration
            worldbuilding: World building information
            story_summary: Story summary
            character: Character information
            plot_point: Plot point to respond to

        Returns:
            OptimizedContext with system prompt and user message
        """
        try:
            context_items = []

            # Character-specific system prompt (highest priority)
            character_system = f"""{system_prompts.mainPrefix}

You are embodying {character.name}, a character with the following traits:
- Bio: {character.basicBio}
- Personality: {character.personality}
- Motivations: {character.motivations}
- Fears: {character.fears}

{system_prompts.mainSuffix}"""

            context_items.append(ContextItem(
                content=character_system,
                context_type=ContextType.SYSTEM_PROMPT,
                priority=10,
                layer_type=LayerType.WORKING_MEMORY,
                metadata={"source": "character_system", "character": character.name}
            ))

            # Current situation (very high priority)
            context_items.append(ContextItem(
                content=f"Current situation: {plot_point}",
                context_type=ContextType.STORY_SUMMARY,
                priority=9,
                layer_type=LayerType.WORKING_MEMORY,
                metadata={"source": "plot_point"}
            ))

            # Story context (medium priority)
            context_items.append(ContextItem(
                content=f"Story: {story_summary}",
                context_type=ContextType.STORY_SUMMARY,
                priority=7,
                layer_type=LayerType.EPISODIC_MEMORY,
                metadata={"source": "story_summary"}
            ))

            # World context (lower priority, compressible)
            context_items.append(ContextItem(
                content=f"World: {worldbuilding}",
                context_type=ContextType.WORLD_BUILDING,
                priority=6,
                layer_type=LayerType.LONG_TERM_MEMORY,
                metadata={"source": "worldbuilding"}
            ))

            # Task instruction
            task_content = f"""Respond in JSON format with exactly these keys:
{{
  "actions": ["3-5 physical actions {character.name} takes"],
  "dialog": ["3-5 things {character.name} might say"],
  "physicalSensations": ["3-5 physical sensations {character.name} experiences"],
  "emotions": ["3-5 emotions {character.name} feels"],
  "internalMonologue": ["3-5 thoughts in {character.name}'s mind"]
}}"""

            return self._optimize_context_items(
                context_items=context_items,
                task_description=task_content,
                generation_type=GenerationType.CHARACTER_FEEDBACK,
                agent_type=ContextAgentType.CHARACTER,
                compose_phase=compose_phase
            )

        except Exception as e:
            logger.error(f"Error in character feedback context optimization: {str(e)}")
            return self._build_fallback_character_context(
                system_prompts, worldbuilding, story_summary, character, plot_point
            )

    def optimize_rater_feedback_context(
        self,
        system_prompts: SystemPrompts,
        rater_prompt: str,
        worldbuilding: str,
        story_summary: str,
        plot_point: str,
        compose_phase: Optional[Any] = None,
        phase_context: Optional[Any] = None
    ) -> OptimizedContext:
        """
        Optimize context for rater feedback endpoint.

        Args:
            system_prompts: System prompts configuration
            rater_prompt: Rater-specific prompt
            worldbuilding: World building information
            story_summary: Story summary
            plot_point: Plot point to evaluate

        Returns:
            OptimizedContext with system prompt and user message
        """
        try:
            context_items = []

            # Rater system prompt (highest priority)
            rater_system = f"{system_prompts.mainPrefix}\n\n{rater_prompt}\n\n{system_prompts.mainSuffix}"
            context_items.append(ContextItem(
                content=rater_system,
                context_type=ContextType.SYSTEM_PROMPT,
                priority=10,
                layer_type=LayerType.WORKING_MEMORY,
                metadata={"source": "rater_system"}
            ))

            # Plot point to evaluate (very high priority)
            context_items.append(ContextItem(
                content=f"Plot point: {plot_point}",
                context_type=ContextType.STORY_SUMMARY,
                priority=9,
                layer_type=LayerType.WORKING_MEMORY,
                metadata={"source": "plot_point"}
            ))

            # Story context (medium priority)
            context_items.append(ContextItem(
                content=f"Story: {story_summary}",
                context_type=ContextType.STORY_SUMMARY,
                priority=7,
                layer_type=LayerType.EPISODIC_MEMORY,
                metadata={"source": "story_summary"}
            ))

            # World context (lower priority)
            context_items.append(ContextItem(
                content=f"World: {worldbuilding}",
                context_type=ContextType.WORLD_BUILDING,
                priority=6,
                layer_type=LayerType.LONG_TERM_MEMORY,
                metadata={"source": "worldbuilding"}
            ))

            task_content = """Provide feedback in JSON format:
{
  "opinion": "Your overall opinion (2-3 sentences)",
  "suggestions": ["4-6 specific suggestions for improvement"]
}"""

            return self._optimize_context_items(
                context_items=context_items,
                task_description=task_content,
                generation_type=GenerationType.RATER_FEEDBACK,
                agent_type=ContextAgentType.RATER,
                compose_phase=compose_phase
            )

        except Exception as e:
            logger.error(f"Error in rater feedback context optimization: {str(e)}")
            return self._build_fallback_rater_context(
                system_prompts, rater_prompt, worldbuilding, story_summary, plot_point
            )

    def optimize_editor_review_context(
        self,
        system_prompts: SystemPrompts,
        worldbuilding: str,
        story_summary: str,
        previous_chapters: List[ChapterInfo],
        plot_point: str,
        compose_phase: Optional[Any] = None,
        phase_context: Optional[Any] = None
    ) -> OptimizedContext:
        """
        Optimize context for editor review endpoint.

        Args:
            system_prompts: System prompts configuration
            worldbuilding: World building information
            story_summary: Story summary
            previous_chapters: List of previous chapters
            plot_point: Plot point or chapter content to review
            compose_phase: Optional compose phase (unused in legacy optimization)
            phase_context: Optional phase context (unused in legacy optimization)

        Returns:
            OptimizedContext with system prompt and user message
        """
        try:
            context_items = []

            # Editor system prompt (highest priority)
            editor_system = f"""{system_prompts.mainPrefix}
{system_prompts.editorPrompt or 'You are an expert editor.'}

Review chapters and provide specific suggestions for improvement.

{system_prompts.mainSuffix}"""

            context_items.append(ContextItem(
                content=editor_system,
                context_type=ContextType.SYSTEM_PROMPT,
                priority=10,
                layer_type=LayerType.WORKING_MEMORY,
                metadata={"source": "editor_system"}
            ))

            # Chapter to review (very high priority - cannot be compressed)
            context_items.append(ContextItem(
                content=f"Chapter to review:\n{plot_point}",
                context_type=ContextType.STORY_SUMMARY,
                priority=9,
                layer_type=LayerType.WORKING_MEMORY,
                metadata={"source": "chapter_content"}
            ))

            # Story context (medium priority)
            context_items.append(ContextItem(
                content=f"Story: {story_summary}",
                context_type=ContextType.STORY_SUMMARY,
                priority=7,
                layer_type=LayerType.EPISODIC_MEMORY,
                metadata={"source": "story_summary"}
            ))

            # World context (lower priority, compressible)
            context_items.append(ContextItem(
                content=f"World: {worldbuilding}",
                context_type=ContextType.WORLD_BUILDING,
                priority=6,
                layer_type=LayerType.LONG_TERM_MEMORY,
                metadata={"source": "worldbuilding"}
            ))

            task_content = """Provide 4-6 suggestions in JSON format:
{
  "suggestions": [
    {"issue": "brief issue description", "suggestion": "specific improvement suggestion", "priority": "high|medium|low"}
  ]
}"""

            return self._optimize_context_items(
                context_items=context_items,
                task_description=task_content,
                generation_type=GenerationType.EDITOR_REVIEW,
                agent_type=ContextAgentType.EDITOR,
                compose_phase=compose_phase
            )

        except Exception as e:
            logger.error(f"Error in editor review context optimization: {str(e)}")
            return self._build_fallback_editor_context(
                system_prompts, worldbuilding, story_summary, plot_point
            )

    def _optimize_context_items(
        self,
        context_items: List[ContextItem],
        task_description: str,
        generation_type: GenerationType = GenerationType.CHAPTER_GENERATION,
        agent_type: Optional[ContextAgentType] = None,
        compose_phase: Optional[ComposePhase] = None
    ) -> OptimizedContext:
        """
        Internal method to optimize context items and build final prompts.

        Args:
            context_items: List of context items to optimize
            task_description: Description of the task for the user message
            generation_type: Type of generation for adaptive summarization
            agent_type: Target agent type
            compose_phase: Current compose phase

        Returns:
            OptimizedContext with optimized prompts
        """
        try:
            # First, build original context to check if optimization is needed
            system_prompt, user_message, original_tokens = self._build_original_context(context_items, task_description)
            
            optimization_applied = False
            compression_ratio = 1.0
            optimization_metadata = {}

            # Check if optimization is needed
            if original_tokens > self.optimization_threshold:
                logger.info(f"Context optimization needed: {original_tokens} > {self.optimization_threshold}")
                
                # Apply adaptive summarization to compressible content
                optimized_items = []
                total_compression_metadata = {}
                
                for item in context_items:
                    if item.context_type in [ContextType.WORLD_BUILDING, ContextType.CHARACTER_PROFILE, 
                                           ContextType.STORY_SUMMARY, ContextType.USER_FEEDBACK]:
                        # Calculate target tokens for this item (proportional reduction)
                        item_tokens = len(item.content.split())
                        if item_tokens > 200:  # Only summarize if substantial content
                            target_tokens = max(100, int(item_tokens * 0.6))  # 40% compression
                            
                            summarized_content, metadata = self._apply_adaptive_summarization(
                                content=item.content,
                                target_tokens=target_tokens,
                                generation_type=generation_type,
                                context_type=item.context_type,
                                agent_type=agent_type,
                                compose_phase=compose_phase,
                                additional_context=item.metadata
                            )
                            
                            # Create optimized item
                            optimized_item = ContextItem(
                                content=summarized_content,
                                context_type=item.context_type,
                                priority=item.priority,
                                layer_type=item.layer_type,
                                metadata={**item.metadata, "summarized": True, "summarization_metadata": metadata}
                            )
                            optimized_items.append(optimized_item)
                            total_compression_metadata[item.context_type.value] = metadata
                        else:
                            optimized_items.append(item)
                    else:
                        # Keep system prompts and high-priority items unchanged
                        optimized_items.append(item)
                
                # Build optimized context
                system_prompt, user_message, final_tokens = self._build_original_context(optimized_items, task_description)
                optimization_applied = True
                compression_ratio = final_tokens / original_tokens if original_tokens > 0 else 1.0
                optimization_metadata = {
                    "adaptive_summarization_applied": True,
                    "compression_details": total_compression_metadata
                }
                
                logger.info(f"Context optimized: {original_tokens} -> {final_tokens} tokens (ratio: {compression_ratio:.2f})")
            else:
                final_tokens = original_tokens

            metadata = {
                "original_tokens": original_tokens,
                "final_tokens": final_tokens,
                "optimization_threshold": self.optimization_threshold,
                "optimization_needed": original_tokens > self.optimization_threshold,
                "optimization_applied": optimization_applied,
                "compression_ratio": compression_ratio,
                **optimization_metadata
            }

            return OptimizedContext(
                system_prompt=system_prompt,
                user_message=user_message,
                total_tokens=final_tokens,
                optimization_applied=optimization_applied,
                compression_ratio=compression_ratio,
                metadata=metadata
            )

        except Exception as e:
            logger.error(f"Error in context optimization: {str(e)}")
            # Final fallback - build basic context
            system_prompt, user_message, tokens = self._build_original_context(context_items, task_description)
            return OptimizedContext(
                system_prompt=system_prompt,
                user_message=user_message,
                total_tokens=tokens,
                optimization_applied=False,
                compression_ratio=1.0,
                metadata={"error": str(e)}
            )

    def _build_original_context(
        self,
        context_items: List[ContextItem],
        task_description: str
    ) -> Tuple[str, str, int]:
        """Build context using original method without optimization."""
        system_parts = []
        user_parts = []

        for item in context_items:
            if item.context_type == ContextType.SYSTEM_PROMPT:
                system_parts.append(item.content)
            else:
                user_parts.append(item.content)

        user_parts.append(task_description)

        system_prompt = "\n\n".join(system_parts)
        user_message = "\n\n".join(user_parts)

        # Rough token estimation
        total_tokens = len(system_prompt.split()) + len(user_message.split())

        return system_prompt, user_message, total_tokens

    # Fallback methods for when optimization fails
    def _build_fallback_chapter_context(
        self,
        system_prompts: SystemPrompts,
        worldbuilding: str,
        story_summary: str,
        characters: List[CharacterInfo],
        plot_point: str,
        incorporated_feedback: List[FeedbackItem]
    ) -> OptimizedContext:
        """Fallback context building for chapter generation."""
        char_context = "\n".join([
            f"- {c.name}: {c.basicBio} (Personality: {c.personality})"
            for c in characters[:3]
        ])

        feedback_context = ""
        if incorporated_feedback:
            feedback_items = [f"- {f.content}" for f in incorporated_feedback[:5]]
            feedback_context = "Incorporated feedback:\n" + "\n".join(feedback_items)

        system_prompt = f"""{system_prompts.mainPrefix}
{system_prompts.assistantPrompt or ''}

{system_prompts.mainSuffix}"""

        user_message = f"""Write a chapter for this story:

World: {worldbuilding}
Story: {story_summary}

Characters:
{char_context}

Plot point for this chapter: {plot_point}

{feedback_context}

Write an engaging chapter (800-1500 words) that brings this plot point to life with vivid prose, authentic dialogue, and character development."""

        total_tokens = len(system_prompt.split()) + len(user_message.split())

        return OptimizedContext(
            system_prompt=system_prompt.strip(),
            user_message=user_message.strip(),
            total_tokens=total_tokens,
            optimization_applied=False,
            compression_ratio=1.0,
            metadata={"fallback": True}
        )

    def _build_fallback_character_context(
        self,
        system_prompts: SystemPrompts,
        worldbuilding: str,
        story_summary: str,
        character: CharacterInfo,
        plot_point: str
    ) -> OptimizedContext:
        """Fallback context building for character feedback."""
        system_prompt = f"""{system_prompts.mainPrefix}

You are embodying {character.name}, a character with the following traits:
- Bio: {character.basicBio}
- Personality: {character.personality}
- Motivations: {character.motivations}
- Fears: {character.fears}

{system_prompts.mainSuffix}"""

        user_message = f"""Context:
- World: {worldbuilding}
- Story: {story_summary}
- Current situation: {plot_point}

Respond in JSON format with exactly these keys:
{{
  "actions": ["3-5 physical actions {character.name} takes"],
  "dialog": ["3-5 things {character.name} might say"],
  "physicalSensations": ["3-5 physical sensations {character.name} experiences"],
  "emotions": ["3-5 emotions {character.name} feels"],
  "internalMonologue": ["3-5 thoughts in {character.name}'s mind"]
}}"""

        total_tokens = len(system_prompt.split()) + len(user_message.split())

        return OptimizedContext(
            system_prompt=system_prompt.strip(),
            user_message=user_message.strip(),
            total_tokens=total_tokens,
            optimization_applied=False,
            compression_ratio=1.0,
            metadata={"fallback": True}
        )

    def _build_fallback_rater_context(
        self,
        system_prompts: SystemPrompts,
        rater_prompt: str,
        worldbuilding: str,
        story_summary: str,
        plot_point: str
    ) -> OptimizedContext:
        """Fallback context building for rater feedback."""
        system_prompt = f"""{system_prompts.mainPrefix}

{rater_prompt}

{system_prompts.mainSuffix}"""

        user_message = f"""Evaluate this plot point:
- World: {worldbuilding}
- Story: {story_summary}
- Plot point: {plot_point}

Provide feedback in JSON format:
{{
  "opinion": "Your overall opinion (2-3 sentences)",
  "suggestions": ["4-6 specific suggestions for improvement"]
}}"""

        total_tokens = len(system_prompt.split()) + len(user_message.split())

        return OptimizedContext(
            system_prompt=system_prompt.strip(),
            user_message=user_message.strip(),
            total_tokens=total_tokens,
            optimization_applied=False,
            compression_ratio=1.0,
            metadata={"fallback": True}
        )

    def _build_fallback_editor_context(
        self,
        system_prompts: SystemPrompts,
        worldbuilding: str,
        story_summary: str,
        plot_point: str
    ) -> OptimizedContext:
        """Fallback context building for editor review."""
        system_prompt = f"""{system_prompts.mainPrefix}
{system_prompts.editorPrompt or 'You are an expert editor.'}

Review chapters and provide specific suggestions for improvement.

{system_prompts.mainSuffix}"""

        user_message = f"""Story context:
- World: {worldbuilding}
- Story: {story_summary}

Chapter to review:
{plot_point}

Provide 4-6 suggestions in JSON format:
{{
  "suggestions": [
    {{"issue": "brief issue description", "suggestion": "specific improvement suggestion", "priority": "high|medium|low"}}
  ]
}}"""

        total_tokens = len(system_prompt.split()) + len(user_message.split())

        return OptimizedContext(
            system_prompt=system_prompt.strip(),
            user_message=user_message.strip(),
            total_tokens=total_tokens,
            optimization_applied=False,
            compression_ratio=1.0,
            metadata={"fallback": True}
        )

    def optimize_modify_chapter_context(
        self,
        system_prompts: SystemPrompts,
        worldbuilding: str,
        story_summary: str,
        characters: List[CharacterInfo],
        original_chapter: str,
        modification_request: str,
        compose_phase: Optional[Any] = None,
        phase_context: Optional[Any] = None
    ) -> OptimizedContext:
        """
        Optimize context for chapter modification endpoint.

        Args:
            system_prompts: System prompts configuration
            worldbuilding: World building information
            story_summary: Story summary
            characters: List of character information
            original_chapter: Original chapter content
            modification_request: User's modification request
            compose_phase: Optional compose phase (unused in legacy optimization)
            phase_context: Optional phase context (unused in legacy optimization)

        Returns:
            OptimizedContext with system prompt and user message
        """
        try:
            context_items = []

            # System prompt for modification
            system_prompt = f"""{system_prompts.mainPrefix}

You are a skilled writer tasked with modifying a chapter based on user feedback.

World Building:
{worldbuilding}

Story Summary:
{story_summary}

Characters:
{chr(10).join([f"- {char.name}: {char.basicBio}" for char in characters])}

Modify the chapter according to the user's request while maintaining consistency with the established world, story, and characters."""

            # User message with original chapter and modification request
            user_message = f"""Original Chapter:
{original_chapter}

Modification Request:
{modification_request}

Please provide the modified chapter that incorporates the requested changes while maintaining narrative flow and character consistency."""

            total_tokens = len(system_prompt.split()) + len(user_message.split())

            return OptimizedContext(
                system_prompt=system_prompt.strip(),
                user_message=user_message.strip(),
                total_tokens=total_tokens,
                optimization_applied=False,
                compression_ratio=1.0,
                metadata={"fallback": True}
            )

        except Exception as e:
            logger.error(f"Error optimizing modify chapter context: {str(e)}")
            # Return fallback context
            system_prompt = f"{system_prompts.mainPrefix}\n\nYou are a skilled writer modifying a chapter."
            user_message = f"Original: {original_chapter}\n\nRequest: {modification_request}"
            
            return OptimizedContext(
                system_prompt=system_prompt,
                user_message=user_message,
                total_tokens=len(system_prompt.split()) + len(user_message.split()),
                optimization_applied=False,
                compression_ratio=1.0,
                metadata={"fallback": True, "error": str(e)}
            )

    def optimize_flesh_out_context(
        self,
        system_prompts: SystemPrompts,
        worldbuilding: str,
        story_summary: str,
        context: str,
        text_to_flesh_out: str,
        compose_phase: Optional[Any] = None,
        phase_context: Optional[Any] = None
    ) -> OptimizedContext:
        """
        Optimize context for flesh out endpoint.

        Args:
            system_prompts: System prompts configuration
            worldbuilding: World building information
            story_summary: Story summary
            context: Context type
            text_to_flesh_out: Text to expand

        Returns:
            OptimizedContext with optimized prompts and metadata
        """
        try:
            # Build context items for analysis
            context_items = []

            # System prompts (high priority)
            if system_prompts.mainPrefix:
                context_items.append(ContextItem(
                    content=system_prompts.mainPrefix,
                    context_type=ContextType.SYSTEM_PROMPT,
                    priority=10,
                    layer_type=LayerType.LAYER_A,
                    metadata={'source': 'main_prefix'}
                ))

            if system_prompts.mainSuffix:
                context_items.append(ContextItem(
                    content=system_prompts.mainSuffix,
                    context_type=ContextType.SYSTEM_PROMPT,
                    priority=10,
                    layer_type=LayerType.LAYER_A,
                    metadata={'source': 'main_suffix'}
                ))

            # Story context (medium priority)
            if worldbuilding:
                context_items.append(ContextItem(
                    content=worldbuilding,
                    context_type=ContextType.WORLD_BUILDING,
                    priority=7,
                    layer_type=LayerType.LAYER_B,
                    metadata={'source': 'worldbuilding'}
                ))

            if story_summary:
                context_items.append(ContextItem(
                    content=story_summary,
                    context_type=ContextType.STORY_SUMMARY,
                    priority=6,
                    layer_type=LayerType.LAYER_B,
                    metadata={'source': 'story_summary'}
                ))

            # Text to flesh out (highest priority)
            context_items.append(ContextItem(
                content=text_to_flesh_out,
                context_type=ContextType.USER_REQUEST,
                priority=10,
                layer_type=LayerType.LAYER_A,
                metadata={'source': 'text_to_flesh_out'}
            ))

            # Context type information
            if context:
                context_items.append(ContextItem(
                    content=f"Context type: {context}",
                    context_type=ContextType.USER_INSTRUCTION,
                    priority=8,
                    layer_type=LayerType.LAYER_A,
                    metadata={'source': 'context_type'}
                ))

            # Calculate total tokens
            total_tokens = sum(len(item.content) // 4 for item in context_items)

            # Check if optimization is needed
            optimization_applied = False
            compression_ratio = 1.0

            if total_tokens > self.optimization_threshold:
                logger.info(f"Optimizing flesh_out context: {total_tokens} tokens > {self.optimization_threshold} threshold")

                # Apply context optimization
                analysis = self.context_manager.analyze_context(context_items)

                optimization_result = self.context_manager.optimize_context(
                    context_items,
                    target_tokens=self.max_context_tokens // 2,  # Conservative target
                    preserve_high_priority=True
                )

                if optimization_result:
                    context_items = optimization_result
                    new_total_tokens = sum(len(item.content) // 4 for item in context_items)
                    compression_ratio = new_total_tokens / total_tokens if total_tokens > 0 else 1.0
                    total_tokens = new_total_tokens
                    optimization_applied = True

                    logger.info(f"Flesh_out context optimized: {total_tokens} tokens (compression: {compression_ratio:.2f})")

            # Build optimized prompts
            system_parts = []
            story_parts = []
            user_parts = []

            for item in context_items:
                if item.context_type == ContextType.SYSTEM_PROMPT:
                    system_parts.append(item.content)
                elif item.context_type in [ContextType.WORLD_BUILDING, ContextType.STORY_SUMMARY]:
                    story_parts.append(f"- {item.context_type.value.replace('_', ' ').title()}: {item.content}")
                elif item.context_type in [ContextType.USER_REQUEST, ContextType.USER_INSTRUCTION]:
                    user_parts.append(item.content)

            # Construct system prompt
            system_prompt_parts = system_parts + [
                "Expand and flesh out brief text with rich detail, adding depth, sensory details, and narrative richness."
            ]
            system_prompt = "\n\n".join(system_prompt_parts)

            # Construct user message
            user_message_parts = []
            if story_parts:
                user_message_parts.append("Story context:")
                user_message_parts.extend(story_parts)
                user_message_parts.append("")

            user_message_parts.extend(user_parts)
            user_message_parts.append("Provide a detailed, atmospheric expansion (200-400 words).")

            user_message = "\n".join(user_message_parts)

            metadata = {
                'original_token_count': sum(len(item.content) // 4 for item in context_items),
                'optimization_applied': optimization_applied,
                'compression_ratio': compression_ratio,
                'context_items_count': len(context_items)
            }

            return OptimizedContext(
                system_prompt=system_prompt,
                user_message=user_message,
                total_tokens=total_tokens,
                optimization_applied=optimization_applied,
                compression_ratio=compression_ratio,
                metadata=metadata
            )

        except Exception as e:
            logger.error(f"Error optimizing flesh_out context: {str(e)}")
            # Return fallback context
            system_prompt = f"""{system_prompts.mainPrefix}

Expand and flesh out brief text with rich detail, adding depth, sensory details, and narrative richness.

{system_prompts.mainSuffix}"""

            user_message = f"""Story context:
- World: {worldbuilding}
- Story: {story_summary}
- Context type: {context}

Text to expand: {text_to_flesh_out}

Provide a detailed, atmospheric expansion (200-400 words)."""

            total_tokens = (len(system_prompt) + len(user_message)) // 4

            return OptimizedContext(
                system_prompt=system_prompt,
                user_message=user_message,
                total_tokens=total_tokens,
                optimization_applied=False,
                compression_ratio=1.0,
                metadata={'fallback_used': True, 'error': str(e)}
            )


# Global service instance
_context_optimization_service = None


def get_context_optimization_service() -> ContextOptimizationService:
    """Get the global context optimization service instance."""
    global _context_optimization_service
    if _context_optimization_service is None:
        _context_optimization_service = ContextOptimizationService()
    return _context_optimization_service
