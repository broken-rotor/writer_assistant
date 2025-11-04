"""
Unified Context Processor for Writer Assistant API.

This service provides a unified interface for processing structured contexts
using the ContextManager service.

Key Features:
- Dual request handling (legacy + structured contexts)
- Endpoint-specific context assembly strategies
- Context metadata generation
- Performance optimization with caching
- Comprehensive error handling and fallback logic
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Literal
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json

from app.services.context_manager import ContextManager
from app.core.config import settings
from app.models.context_models import (
    StructuredContextContainer as LegacyStructuredContextContainer,
    ContextProcessingConfig,
    AgentType,
    ComposePhase,
    StoryContextElement,
    CharacterContextElement,
    UserContextElement,
    SystemContextElement,
    ContextType,
    ContextMetadata as LegacyContextMetadata
)
from app.models.generation_models import (
    StructuredContextContainer,
    SystemPrompts,
    CharacterInfo,
    ChapterInfo,
    FeedbackItem,
    PhaseContext,
    ContextMetadata
)

logger = logging.getLogger(__name__)


def convert_api_to_legacy_context(
        api_context: StructuredContextContainer) -> LegacyStructuredContextContainer:
    """Convert StructuredContextContainer from generation_models.py to context_models.py format."""
    elements = []

    # Convert plot elements to story context elements
    for plot_element in api_context.plot_elements:
        element = StoryContextElement(
            id=plot_element.id or f"plot_{len(elements)}",
            type=ContextType.PLOT_OUTLINE,
            content=plot_element.content,
            metadata=LegacyContextMetadata(
                priority=(settings.CONTEXT_PRIORITY_PLOT_HIGH if plot_element.priority == "high"
                          else settings.CONTEXT_PRIORITY_PLOT_MEDIUM if plot_element.priority == "medium"
                          else settings.CONTEXT_PRIORITY_PLOT_LOW),
                target_agents=[AgentType.WRITER],
                tags=plot_element.tags
            )
        )
        elements.append(element)

    # Convert character contexts to story context elements
    for character_context in api_context.character_contexts:
        # Create content from character context
        content = f"Character: {character_context.character_name}\n"
        if character_context.current_state:
            content += f"Current State: {character_context.current_state}\n"
        if character_context.goals:
            content += f"Goals: {', '.join(character_context.goals)}\n"
        if character_context.personality_traits:
            content += f"Personality: {
                ', '.join(
                    character_context.personality_traits)}"

        element = CharacterContextElement(
            id=character_context.character_id or f"char_{len(elements)}",
            type=ContextType.CHARACTER_PROFILE,
            content=content,
            character_id=character_context.character_id or f"char_{
                len(elements)}",
            character_name=character_context.character_name,
            metadata=LegacyContextMetadata(
                priority=settings.CONTEXT_PRIORITY_CHARACTER,
                target_agents=[AgentType.CHARACTER, AgentType.WRITER],
                tags=["character"]
            )
        )
        elements.append(element)

    # Convert user requests to user context elements
    for user_request in api_context.user_requests:
        element = UserContextElement(
            id=user_request.id or f"user_{len(elements)}",
            type=ContextType.USER_REQUEST,
            content=user_request.content,
            metadata=LegacyContextMetadata(
                priority=(settings.CONTEXT_PRIORITY_USER_HIGH if user_request.priority == "high"
                          else settings.CONTEXT_PRIORITY_USER_MEDIUM if user_request.priority == "medium"
                          else settings.CONTEXT_PRIORITY_USER_LOW),
                target_agents=[AgentType.WRITER],
                tags=[]
            )
        )
        elements.append(element)

    # Convert system instructions to system context elements
    for sys_instruction in api_context.system_instructions:
        element = SystemContextElement(
            id=sys_instruction.id or f"sys_{len(elements)}",
            type=ContextType.SYSTEM_INSTRUCTION,
            content=sys_instruction.content,
            metadata=LegacyContextMetadata(
                priority=(settings.CONTEXT_PRIORITY_SYSTEM_HIGH if sys_instruction.priority == "high"
                          else settings.CONTEXT_PRIORITY_SYSTEM_MEDIUM if sys_instruction.priority == "medium"
                          else settings.CONTEXT_PRIORITY_SYSTEM_LOW),
                target_agents=[AgentType.WRITER],
                tags=[]
            )
        )
        elements.append(element)

    # Create legacy container
    return LegacyStructuredContextContainer(
        elements=elements,
        global_metadata={
            "total_elements": len(elements),
            "converted_from_api": True,
            "original_total_elements": api_context.metadata.total_elements if api_context.metadata else len(elements)
        }
    )


@dataclass
class UnifiedContextResult:
    """Result of unified context processing."""
    system_prompt: str
    user_message: str
    context_metadata: ContextMetadata
    processing_mode: Literal["structured"]
    optimization_applied: bool
    total_tokens: int
    compression_ratio: float = 1.0


class UnifiedContextProcessor:
    """
    Unified service for processing structured contexts.

    This service provides a consistent interface for context processing
    using the ContextManager for structured context handling.
    """

    def __init__(self, enable_caching: bool = True):
        """Initialize the unified context processor."""
        self.context_manager = ContextManager()
        self.enable_caching = enable_caching
        self._cache: Dict[str, UnifiedContextResult] = {}

        logger.info("UnifiedContextProcessor initialized")

    def process_generate_chapter_context(
        self,
        # Phase context
        compose_phase: Optional[ComposePhase] = None,
        phase_context: Optional[PhaseContext] = None,
        # Structured context
        structured_context: Optional[StructuredContextContainer] = None,
        context_processing_config: Optional[Dict[str, Any]] = None
    ) -> UnifiedContextResult:
        """
        Process context for chapter generation with full narrative context assembly.

        This method implements the endpoint-specific context assembly strategy
        for chapter generation, prioritizing narrative flow and character development.
        """
        try:
            # Generate cache key if caching is enabled
            cache_key = None
            if self.enable_caching:
                cache_key = self._generate_cache_key(
                    "generate_chapter", locals()
                )
                if cache_key in self._cache:
                    logger.debug(
                        f"Cache hit for generate_chapter: {cache_key}")
                    return self._cache[cache_key]

            if structured_context:
                result = self._process_structured_context(
                    structured_context=structured_context,
                    agent_type=AgentType.WRITER,
                    compose_phase=compose_phase or ComposePhase.CHAPTER_DETAIL,
                    context_processing_config=context_processing_config,
                    endpoint_strategy="full_narrative_assembly"
                )
            else:
                raise ValueError("Only structured context mode is supported. Please provide structured_context.")

            # Cache the result
            if self.enable_caching and cache_key:
                self._cache[cache_key] = result
                logger.debug(
                    f"Cached result for generate_chapter: {cache_key}")

            return result

        except Exception as e:
            logger.error(
                f"Error in process_generate_chapter_context: {
                    str(e)}")
            # Fallback to legacy processing
            raise ValueError("Legacy context processing is no longer supported. Please provide structured_context.")

    def process_character_feedback_context(
        self,
        # Phase context
        compose_phase: Optional[ComposePhase] = None,
        phase_context: Optional[PhaseContext] = None,
        # Structured context
        structured_context: Optional[StructuredContextContainer] = None,
        context_processing_config: Optional[Dict[str, Any]] = None
    ) -> UnifiedContextResult:
        """
        Process context for character feedback with character-specific prioritization.

        This method implements character-focused context assembly, prioritizing
        character-relevant information and emotional context.
        """
        try:
            # Generate cache key if caching is enabled
            cache_key = None
            if self.enable_caching:
                cache_key = self._generate_cache_key(
                    "character_feedback", locals()
                )
                if cache_key in self._cache:
                    logger.debug(
                        f"Cache hit for character_feedback: {cache_key}")
                    return self._cache[cache_key]

            if structured_context:
                result = self._process_structured_context(
                    structured_context=structured_context,
                    agent_type=AgentType.CHARACTER,
                    compose_phase=compose_phase or ComposePhase.CHAPTER_DETAIL,
                    context_processing_config=context_processing_config,
                    endpoint_strategy="character_specific_prioritization"
                )
            else:
                raise ValueError("Only structured context mode is supported. Please provide structured_context.")

            # Cache the result
            if self.enable_caching and cache_key:
                self._cache[cache_key] = result

            return result

        except Exception as e:
            logger.error(
                f"Error in process_character_feedback_context: {str(e)}")
            raise

    def process_editor_review_context(
        self,
        # Phase context
        compose_phase: Optional[ComposePhase] = None,
        phase_context: Optional[PhaseContext] = None,
        # Structured context
        structured_context: Optional[StructuredContextContainer] = None,
        context_processing_config: Optional[Dict[str, Any]] = None
    ) -> UnifiedContextResult:
        """
        Process context for editor review with review-focused context filtering.

        This method implements editorial context assembly, prioritizing
        consistency, quality, and narrative flow elements.
        """
        try:
            # Generate cache key if caching is enabled
            cache_key = None
            if self.enable_caching:
                cache_key = self._generate_cache_key(
                    "editor_review", locals()
                )
                if cache_key in self._cache:
                    logger.debug(f"Cache hit for editor_review: {cache_key}")
                    return self._cache[cache_key]

            if structured_context:
                result = self._process_structured_context(
                    structured_context=structured_context,
                    agent_type=AgentType.EDITOR,
                    compose_phase=compose_phase or ComposePhase.FINAL_EDIT,
                    context_processing_config=context_processing_config,
                    endpoint_strategy="review_focused_filtering"
                )
            else:
                raise ValueError("Legacy context processing is no longer supported. Please provide structured_context.")

            # Cache the result
            if self.enable_caching and cache_key:
                self._cache[cache_key] = result

            return result

        except Exception as e:
            logger.error(f"Error in process_editor_review_context: {str(e)}")
            # Fallback to legacy processing
            raise ValueError("Legacy context processing is no longer supported. Please provide structured_context.")

    def process_rater_feedback_context(
        self,
        # Legacy fields (kept for backward compatibility in method signature)
        rater_prompt: Optional[str] = None,
        plot_point: Optional[str] = None,
        # Phase context
        compose_phase: Optional[ComposePhase] = None,
        phase_context: Optional[PhaseContext] = None,
        # Structured context
        structured_context: Optional[StructuredContextContainer] = None,
        context_processing_config: Optional[Dict[str, Any]] = None
    ) -> UnifiedContextResult:
        """
        Process context for rater feedback with rater-specific context preparation.

        This method implements rater-focused context assembly, prioritizing
        evaluation criteria and quality assessment elements.
        """
        try:
            # Generate cache key if caching is enabled
            cache_key = None
            if self.enable_caching:
                cache_key = self._generate_cache_key(
                    "rater_feedback", locals()
                )
                if cache_key in self._cache:
                    logger.debug(f"Cache hit for rater_feedback: {cache_key}")
                    return self._cache[cache_key]

            if structured_context:
                result = self._process_structured_context(
                    structured_context=structured_context,
                    agent_type=AgentType.RATER,
                    compose_phase=compose_phase or ComposePhase.FINAL_EDIT,
                    context_processing_config=context_processing_config,
                    endpoint_strategy="rater_specific_preparation"
                )
            else:
                raise ValueError("Legacy context processing is no longer supported. Please provide structured_context.")

            # Cache the result
            if self.enable_caching and cache_key:
                self._cache[cache_key] = result

            return result

        except Exception as e:
            logger.error(f"Error in process_rater_feedback_context: {str(e)}")
            # Fallback to legacy processing
            raise ValueError("Legacy context processing is no longer supported. Please provide structured_context.")

    def process_modify_chapter_context(
        self,
        # Legacy fields
        system_prompts: Optional[SystemPrompts] = None,
        worldbuilding: Optional[str] = None,
        story_summary: Optional[str] = None,
        characters: Optional[List[CharacterInfo]] = None,
        original_chapter: Optional[str] = None,
        modification_request: Optional[str] = None,
        # Phase context
        compose_phase: Optional[ComposePhase] = None,
        phase_context: Optional[PhaseContext] = None,
        # Structured context
        structured_context: Optional[StructuredContextContainer] = None,
        context_processing_config: Optional[Dict[str, Any]] = None
    ) -> UnifiedContextResult:
        """
        Process context for chapter modification with change-focused context management.

        This method implements modification-focused context assembly, prioritizing
        change requests and consistency maintenance elements.
        """
        try:
            # Generate cache key if caching is enabled
            cache_key = None
            if self.enable_caching:
                cache_key = self._generate_cache_key(
                    "modify_chapter", locals()
                )
                if cache_key in self._cache:
                    logger.debug(f"Cache hit for modify_chapter: {cache_key}")
                    return self._cache[cache_key]

            if structured_context:
                result = self._process_structured_context(
                    structured_context=structured_context,
                    agent_type=AgentType.WRITER,
                    compose_phase=compose_phase or ComposePhase.FINAL_EDIT,
                    context_processing_config=context_processing_config,
                    endpoint_strategy="change_focused_management"
                )
            else:
                raise ValueError("Legacy context processing is no longer supported. Please provide structured_context.")

            # Cache the result
            if self.enable_caching and cache_key:
                self._cache[cache_key] = result

            return result

        except Exception as e:
            logger.error(f"Error in process_modify_chapter_context: {str(e)}")
            # Fallback to legacy processing
            raise ValueError("Legacy context processing is no longer supported. Please provide structured_context.")

    def process_flesh_out_context(
        self,
        # Legacy fields
        system_prompts: Optional[SystemPrompts] = None,
        worldbuilding: Optional[str] = None,
        story_summary: Optional[str] = None,
        characters: Optional[List[CharacterInfo]] = None,
        outline_section: Optional[str] = None,
        # Phase context
        compose_phase: Optional[ComposePhase] = None,
        phase_context: Optional[PhaseContext] = None,
        # Structured context
        structured_context: Optional[StructuredContextContainer] = None,
        context_processing_config: Optional[Dict[str, Any]] = None
    ) -> UnifiedContextResult:
        """
        Process context for flesh out with expansion-specific context assembly.

        This method implements expansion-focused context assembly, prioritizing
        detail enhancement and narrative development elements.
        """
        try:
            # Generate cache key if caching is enabled
            cache_key = None
            if self.enable_caching:
                cache_key = self._generate_cache_key(
                    "flesh_out", locals()
                )
                if cache_key in self._cache:
                    logger.debug(f"Cache hit for flesh_out: {cache_key}")
                    return self._cache[cache_key]

            if structured_context:
                result = self._process_structured_context(
                    structured_context=structured_context,
                    agent_type=AgentType.WRITER,
                    compose_phase=compose_phase or ComposePhase.CHAPTER_DETAIL,
                    context_processing_config=context_processing_config,
                    endpoint_strategy="expansion_specific_assembly"
                )
            else:
                raise ValueError("Legacy context processing is no longer supported. Please provide structured_context.")

            # Cache the result
            if self.enable_caching and cache_key:
                self._cache[cache_key] = result

            return result

        except Exception as e:
            logger.error(f"Error in process_flesh_out_context: {str(e)}")
            # Fallback to legacy processing
            raise ValueError("Legacy context processing is no longer supported. Please provide structured_context.")

    def process_character_generation_context(
        self,
        # Legacy fields
        system_prompts: Optional[SystemPrompts] = None,
        worldbuilding: Optional[str] = None,
        story_summary: Optional[str] = None,
        basic_bio: Optional[str] = None,
        existing_characters: Optional[List[Dict[str, str]]] = None,
        # Phase context
        compose_phase: Optional[ComposePhase] = None,
        phase_context: Optional[PhaseContext] = None,
        # Structured context
        structured_context: Optional[StructuredContextContainer] = None,
        context_processing_config: Optional[Dict[str, Any]] = None
    ) -> UnifiedContextResult:
        """
        Process context for character generation with character-creation-specific prioritization.

        This method implements character generation focused context assembly, prioritizing
        worldbuilding, existing character information, and character creation guidelines.
        """
        try:
            # Generate cache key if caching is enabled
            cache_key = None
            if self.enable_caching:
                cache_key = self._generate_cache_key(
                    "character_generation", locals()
                )
                if cache_key in self._cache:
                    logger.debug(
                        f"Cache hit for character_generation: {cache_key}")
                    return self._cache[cache_key]

            if structured_context:
                result = self._process_structured_context(
                    structured_context=structured_context,
                    agent_type=AgentType.WRITER,
                    compose_phase=compose_phase or ComposePhase.CHAPTER_DETAIL,
                    context_processing_config=context_processing_config,
                    endpoint_strategy="character_generation_prioritization"
                )
            else:
                raise ValueError("Legacy context processing is no longer supported. Please provide structured_context.")

            # Cache the result
            if self.enable_caching and cache_key:
                self._cache[cache_key] = result

            return result

        except Exception as e:
            logger.error(
                f"Error in process_character_generation_context: {
                    str(e)}")
            # Fallback to legacy processing
            raise ValueError("Legacy context processing is no longer supported. Please provide structured_context.")

    def _process_structured_context(
        self,
        structured_context: StructuredContextContainer,
        agent_type: AgentType,
        compose_phase: ComposePhase,
        context_processing_config: Optional[Dict[str, Any]],
        endpoint_strategy: str
    ) -> UnifiedContextResult:
        """Process structured context using ContextManager."""
        try:
            # Convert API structured context to legacy format for processing
            legacy_context = convert_api_to_legacy_context(structured_context)

            # Create processing configuration
            processing_config = ContextProcessingConfig(
                target_agent=agent_type,
                current_phase=compose_phase,
                max_tokens=context_processing_config.get(
                    "max_context_length", 8000) if context_processing_config else 8000,
                summarization_threshold=context_processing_config.get(
                    "summarization_threshold", 6000) if context_processing_config else 6000,
                prioritize_recent=context_processing_config.get(
                    "prioritize_recent", True) if context_processing_config else True,
                include_relationships=context_processing_config.get(
                    "include_relationships", True) if context_processing_config else True
            )

            # Process context with ContextManager
            formatted_context, metadata = self.context_manager.process_context_for_agent(
                legacy_context, processing_config
            )

            # Parse the formatted context to extract system prompt and user
            # message
            system_prompt, user_message = self._parse_formatted_context(
                formatted_context, agent_type, endpoint_strategy
            )

            # Create context metadata
            context_metadata = ContextMetadata(
                total_elements=metadata.get("original_element_count", 0),
                processing_applied=metadata.get("was_summarized", False),
                processing_mode="structured",
                optimization_level="moderate" if metadata.get(
                    "was_summarized", False) else "none",
                compression_ratio=metadata.get("reduction_ratio"),
                processing_time_ms=metadata.get("processing_time_ms", 0),
                created_at=datetime.now(timezone.utc).isoformat()
            )

            return UnifiedContextResult(
                system_prompt=system_prompt,
                user_message=user_message,
                context_metadata=context_metadata,
                processing_mode="structured",
                optimization_applied=metadata.get("was_summarized", False),
                total_tokens=metadata.get(
                    "final_element_count", 0) * 100,  # Rough estimate
                compression_ratio=metadata.get("reduction_ratio", 1.0)
            )

        except Exception as e:
            logger.error(f"Error processing structured context: {str(e)}")
            raise

    def _parse_formatted_context(
        self,
        formatted_context: str,
        agent_type: AgentType,
        endpoint_strategy: str
    ) -> Tuple[str, str]:
        """
        Parse formatted context from ContextManager into system prompt and user message.

        The ContextManager returns a formatted string that needs to be split into
        system prompt and user message components based on the agent type and strategy.
        """
        # Split the formatted context into sections
        sections = formatted_context.split("\n=== ")

        system_sections = []
        user_sections = []

        for section in sections:
            section = section.strip()
            if not section:
                continue

            # Add back the === prefix that was removed by split
            if not section.startswith("==="):
                section = "=== " + section

            # Categorize sections based on content
            if any(keyword in section.upper() for keyword in [
                "SYSTEM INSTRUCTIONS", "EDITORIAL GUIDELINES", "EVALUATION CRITERIA"
            ]):
                system_sections.append(section)
            else:
                user_sections.append(section)

        # Build system prompt and user message
        system_prompt = "\n\n".join(
            system_sections) if system_sections else "You are a helpful AI assistant."
        user_message = "\n\n".join(
            user_sections) if user_sections else formatted_context

        return system_prompt, user_message

    def _generate_cache_key(self, endpoint: str,
                            params: Dict[str, Any]) -> str:
        """Generate a cache key for the given endpoint and parameters."""
        # Create a simplified version of params for hashing
        cache_params = {}
        for key, value in params.items():
            if key in ["self", "cache_key"]:  # Skip these params
                continue
            if value is None:
                cache_params[key] = None
            elif isinstance(value, (str, int, float, bool)):
                cache_params[key] = value
            elif isinstance(value, (list, dict)):
                # Convert to JSON string for consistent hashing
                cache_params[key] = json.dumps(
                    value, sort_keys=True, default=str)
            else:
                # For complex objects, use their string representation
                cache_params[key] = str(value)

        # Create hash
        cache_string = f"{endpoint}:{json.dumps(cache_params, sort_keys=True)}"
        return hashlib.md5(cache_string.encode()).hexdigest()

    def clear_cache(self):
        """Clear the context processing cache."""
        self._cache.clear()
        logger.info("Context processing cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cache_size": len(self._cache),
            "cache_enabled": self.enable_caching
        }

# Global instance
_unified_context_processor = None


def get_unified_context_processor() -> UnifiedContextProcessor:
    """Get the global unified context processor instance."""
    global _unified_context_processor
    if _unified_context_processor is None:
        _unified_context_processor = UnifiedContextProcessor()
    return _unified_context_processor
