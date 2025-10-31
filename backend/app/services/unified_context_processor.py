"""
Unified Context Processor for Writer Assistant API.

This service provides a unified interface for processing both legacy and structured contexts,
integrating the ContextManager service with the existing context_optimization service
while maintaining backward compatibility.

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
from app.services.context_optimization import ContextOptimizationService, OptimizedContext
from app.services.context_adapter import ContextAdapter
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


def convert_api_to_legacy_context(api_context: StructuredContextContainer) -> LegacyStructuredContextContainer:
    """Convert StructuredContextContainer from generation_models.py to context_models.py format."""
    elements = []
    
    # Convert plot elements to story context elements
    for plot_element in api_context.plot_elements:
        element = StoryContextElement(
            id=plot_element.id or f"plot_{len(elements)}",
            type=ContextType.PLOT_OUTLINE,
            content=plot_element.content,
            metadata=LegacyContextMetadata(
                priority=0.8 if plot_element.priority == "high" else 0.5 if plot_element.priority == "medium" else 0.2,
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
            content += f"Personality: {', '.join(character_context.personality_traits)}"
        
        element = CharacterContextElement(
            id=character_context.character_id or f"char_{len(elements)}",
            type=ContextType.CHARACTER_PROFILE,
            content=content,
            character_id=character_context.character_id or f"char_{len(elements)}",
            character_name=character_context.character_name,
            metadata=LegacyContextMetadata(
                priority=0.7,  # Character contexts are generally important
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
                priority=0.8 if user_request.priority == "high" else 0.5 if user_request.priority == "medium" else 0.2,
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
                priority=0.8 if sys_instruction.priority == "high" else 0.5 if sys_instruction.priority == "medium" else 0.2,
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
    processing_mode: Literal["legacy", "structured", "hybrid"]
    optimization_applied: bool
    total_tokens: int
    compression_ratio: float = 1.0


class UnifiedContextProcessor:
    """
    Unified service for processing both legacy and structured contexts.
    
    This service acts as a facade that routes context processing requests
    to the appropriate service (ContextManager or ContextOptimizationService)
    based on the context mode and provides a consistent interface.
    """

    def __init__(self, enable_caching: bool = True):
        """Initialize the unified context processor."""
        self.context_manager = ContextManager()
        self.context_optimization = ContextOptimizationService()
        self.context_adapter = ContextAdapter()
        self.enable_caching = enable_caching
        self._cache: Dict[str, UnifiedContextResult] = {}
        
        logger.info("UnifiedContextProcessor initialized")

    def process_generate_chapter_context(
        self,
        # Legacy fields
        system_prompts: Optional[SystemPrompts] = None,
        worldbuilding: Optional[str] = None,
        story_summary: Optional[str] = None,
        characters: Optional[List[CharacterInfo]] = None,
        plot_point: Optional[str] = None,
        incorporated_feedback: Optional[List[FeedbackItem]] = None,
        previous_chapters: Optional[List[ChapterInfo]] = None,
        # Phase context
        compose_phase: Optional[ComposePhase] = None,
        phase_context: Optional[PhaseContext] = None,
        # Structured context
        structured_context: Optional[StructuredContextContainer] = None,
        context_mode: Literal["legacy", "structured", "hybrid"] = "legacy",
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
                    logger.debug(f"Cache hit for generate_chapter: {cache_key}")
                    return self._cache[cache_key]

            if context_mode == "structured" and structured_context:
                result = self._process_structured_context(
                    structured_context=structured_context,
                    agent_type=AgentType.WRITER,
                    compose_phase=compose_phase or ComposePhase.CHAPTER_WRITING,
                    context_processing_config=context_processing_config,
                    endpoint_strategy="full_narrative_assembly"
                )
            elif context_mode == "hybrid":
                result = self._process_hybrid_context(
                    # Legacy params
                    system_prompts=system_prompts,
                    worldbuilding=worldbuilding,
                    story_summary=story_summary,
                    characters=characters,
                    plot_point=plot_point,
                    incorporated_feedback=incorporated_feedback,
                    previous_chapters=previous_chapters,
                    compose_phase=compose_phase,
                    phase_context=phase_context,
                    # Structured params
                    structured_context=structured_context,
                    agent_type=AgentType.WRITER,
                    endpoint_strategy="full_narrative_assembly",
                    context_processing_config=context_processing_config
                )
            else:  # legacy mode
                result = self._process_legacy_context_for_chapter(
                    system_prompts=system_prompts,
                    worldbuilding=worldbuilding,
                    story_summary=story_summary,
                    characters=characters or [],
                    plot_point=plot_point or "",
                    incorporated_feedback=incorporated_feedback or [],
                    previous_chapters=previous_chapters,
                    compose_phase=compose_phase,
                    phase_context=phase_context
                )

            # Cache the result
            if self.enable_caching and cache_key:
                self._cache[cache_key] = result
                logger.debug(f"Cached result for generate_chapter: {cache_key}")

            return result

        except Exception as e:
            logger.error(f"Error in process_generate_chapter_context: {str(e)}")
            # Fallback to legacy processing
            return self._process_legacy_context_for_chapter(
                system_prompts=system_prompts,
                worldbuilding=worldbuilding,
                story_summary=story_summary,
                characters=characters or [],
                plot_point=plot_point or "",
                incorporated_feedback=incorporated_feedback or [],
                previous_chapters=previous_chapters,
                compose_phase=compose_phase,
                phase_context=phase_context
            )

    def process_character_feedback_context(
        self,
        # Legacy fields
        system_prompts: Optional[SystemPrompts] = None,
        worldbuilding: Optional[str] = None,
        story_summary: Optional[str] = None,
        character: Optional[CharacterInfo] = None,
        plot_point: Optional[str] = None,
        # Phase context
        compose_phase: Optional[ComposePhase] = None,
        phase_context: Optional[PhaseContext] = None,
        # Structured context
        structured_context: Optional[StructuredContextContainer] = None,
        context_mode: Literal["legacy", "structured", "hybrid"] = "legacy",
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
                    logger.debug(f"Cache hit for character_feedback: {cache_key}")
                    return self._cache[cache_key]

            if context_mode == "structured" and structured_context:
                result = self._process_structured_context(
                    structured_context=structured_context,
                    agent_type=AgentType.CHARACTER,
                    compose_phase=compose_phase or ComposePhase.CHAPTER_DETAIL,
                    context_processing_config=context_processing_config,
                    endpoint_strategy="character_specific_prioritization"
                )
            elif context_mode == "hybrid":
                result = self._process_hybrid_context(
                    # Legacy params
                    system_prompts=system_prompts,
                    worldbuilding=worldbuilding,
                    story_summary=story_summary,
                    character=character,
                    plot_point=plot_point,
                    compose_phase=compose_phase,
                    phase_context=phase_context,
                    # Structured params
                    structured_context=structured_context,
                    agent_type=AgentType.CHARACTER,
                    endpoint_strategy="character_specific_prioritization",
                    context_processing_config=context_processing_config
                )
            else:  # legacy mode
                result = self._process_legacy_context_for_character(
                    system_prompts=system_prompts,
                    worldbuilding=worldbuilding,
                    story_summary=story_summary,
                    character=character,
                    plot_point=plot_point or "",
                    compose_phase=compose_phase,
                    phase_context=phase_context
                )

            # Cache the result
            if self.enable_caching and cache_key:
                self._cache[cache_key] = result

            return result

        except Exception as e:
            logger.error(f"Error in process_character_feedback_context: {str(e)}")
            # Fallback to legacy processing
            return self._process_legacy_context_for_character(
                system_prompts=system_prompts,
                worldbuilding=worldbuilding,
                story_summary=story_summary,
                character=character,
                plot_point=plot_point or "",
                compose_phase=compose_phase,
                phase_context=phase_context
            )

    def process_editor_review_context(
        self,
        # Legacy fields
        system_prompts: Optional[SystemPrompts] = None,
        worldbuilding: Optional[str] = None,
        story_summary: Optional[str] = None,
        previous_chapters: Optional[List[ChapterInfo]] = None,
        plot_point: Optional[str] = None,
        # Phase context
        compose_phase: Optional[ComposePhase] = None,
        phase_context: Optional[PhaseContext] = None,
        # Structured context
        structured_context: Optional[StructuredContextContainer] = None,
        context_mode: Literal["legacy", "structured", "hybrid"] = "legacy",
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

            if context_mode == "structured" and structured_context:
                result = self._process_structured_context(
                    structured_context=structured_context,
                    agent_type=AgentType.EDITOR,
                    compose_phase=compose_phase or ComposePhase.EDITING,
                    context_processing_config=context_processing_config,
                    endpoint_strategy="review_focused_filtering"
                )
            elif context_mode == "hybrid":
                result = self._process_hybrid_context(
                    # Legacy params
                    system_prompts=system_prompts,
                    worldbuilding=worldbuilding,
                    story_summary=story_summary,
                    previous_chapters=previous_chapters,
                    plot_point=plot_point,
                    compose_phase=compose_phase,
                    phase_context=phase_context,
                    # Structured params
                    structured_context=structured_context,
                    agent_type=AgentType.EDITOR,
                    endpoint_strategy="review_focused_filtering",
                    context_processing_config=context_processing_config
                )
            else:  # legacy mode
                result = self._process_legacy_context_for_editor(
                    system_prompts=system_prompts,
                    worldbuilding=worldbuilding,
                    story_summary=story_summary,
                    previous_chapters=previous_chapters or [],
                    plot_point=plot_point or "",
                    compose_phase=compose_phase,
                    phase_context=phase_context
                )

            # Cache the result
            if self.enable_caching and cache_key:
                self._cache[cache_key] = result

            return result

        except Exception as e:
            logger.error(f"Error in process_editor_review_context: {str(e)}")
            # Fallback to legacy processing
            return self._process_legacy_context_for_editor(
                system_prompts=system_prompts,
                worldbuilding=worldbuilding,
                story_summary=story_summary,
                previous_chapters=previous_chapters or [],
                plot_point=plot_point or "",
                compose_phase=compose_phase,
                phase_context=phase_context
            )

    def process_rater_feedback_context(
        self,
        # Legacy fields
        system_prompts: Optional[SystemPrompts] = None,
        rater_prompt: Optional[str] = None,
        worldbuilding: Optional[str] = None,
        story_summary: Optional[str] = None,
        previous_chapters: Optional[List[ChapterInfo]] = None,
        plot_point: Optional[str] = None,
        incorporated_feedback: Optional[List[FeedbackItem]] = None,
        # Phase context
        compose_phase: Optional[ComposePhase] = None,
        phase_context: Optional[PhaseContext] = None,
        # Structured context
        structured_context: Optional[StructuredContextContainer] = None,
        context_mode: Literal["legacy", "structured", "hybrid"] = "legacy",
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

            if context_mode == "structured" and structured_context:
                result = self._process_structured_context(
                    structured_context=structured_context,
                    agent_type=AgentType.RATER,
                    compose_phase=compose_phase or ComposePhase.FEEDBACK,
                    context_processing_config=context_processing_config,
                    endpoint_strategy="rater_specific_preparation"
                )
            elif context_mode == "hybrid":
                result = self._process_hybrid_context(
                    # Legacy params
                    system_prompts=system_prompts,
                    rater_prompt=rater_prompt,
                    worldbuilding=worldbuilding,
                    story_summary=story_summary,
                    previous_chapters=previous_chapters,
                    plot_point=plot_point,
                    incorporated_feedback=incorporated_feedback,
                    compose_phase=compose_phase,
                    phase_context=phase_context,
                    # Structured params
                    structured_context=structured_context,
                    agent_type=AgentType.RATER,
                    endpoint_strategy="rater_specific_preparation",
                    context_processing_config=context_processing_config
                )
            else:  # legacy mode
                result = self._process_legacy_context_for_rater(
                    system_prompts=system_prompts,
                    rater_prompt=rater_prompt or "",
                    worldbuilding=worldbuilding,
                    story_summary=story_summary,
                    previous_chapters=previous_chapters or [],
                    plot_point=plot_point or "",
                    incorporated_feedback=incorporated_feedback or [],
                    compose_phase=compose_phase,
                    phase_context=phase_context
                )

            # Cache the result
            if self.enable_caching and cache_key:
                self._cache[cache_key] = result

            return result

        except Exception as e:
            logger.error(f"Error in process_rater_feedback_context: {str(e)}")
            # Fallback to legacy processing
            return self._process_legacy_context_for_rater(
                system_prompts=system_prompts,
                rater_prompt=rater_prompt or "",
                worldbuilding=worldbuilding,
                story_summary=story_summary,
                previous_chapters=previous_chapters or [],
                plot_point=plot_point or "",
                incorporated_feedback=incorporated_feedback or [],
                compose_phase=compose_phase,
                phase_context=phase_context
            )

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
        context_mode: Literal["legacy", "structured", "hybrid"] = "legacy",
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

            if context_mode == "structured" and structured_context:
                result = self._process_structured_context(
                    structured_context=structured_context,
                    agent_type=AgentType.WRITER,
                    compose_phase=compose_phase or ComposePhase.REVISION,
                    context_processing_config=context_processing_config,
                    endpoint_strategy="change_focused_management"
                )
            elif context_mode == "hybrid":
                result = self._process_hybrid_context(
                    # Legacy params
                    system_prompts=system_prompts,
                    worldbuilding=worldbuilding,
                    story_summary=story_summary,
                    characters=characters,
                    original_chapter=original_chapter,
                    modification_request=modification_request,
                    compose_phase=compose_phase,
                    phase_context=phase_context,
                    # Structured params
                    structured_context=structured_context,
                    agent_type=AgentType.WRITER,
                    endpoint_strategy="change_focused_management",
                    context_processing_config=context_processing_config
                )
            else:  # legacy mode
                result = self._process_legacy_context_for_modify(
                    system_prompts=system_prompts,
                    worldbuilding=worldbuilding,
                    story_summary=story_summary,
                    characters=characters or [],
                    original_chapter=original_chapter or "",
                    modification_request=modification_request or "",
                    compose_phase=compose_phase,
                    phase_context=phase_context
                )

            # Cache the result
            if self.enable_caching and cache_key:
                self._cache[cache_key] = result

            return result

        except Exception as e:
            logger.error(f"Error in process_modify_chapter_context: {str(e)}")
            # Fallback to legacy processing
            return self._process_legacy_context_for_modify(
                system_prompts=system_prompts,
                worldbuilding=worldbuilding,
                story_summary=story_summary,
                characters=characters or [],
                original_chapter=original_chapter or "",
                modification_request=modification_request or "",
                compose_phase=compose_phase,
                phase_context=phase_context
            )

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
        context_mode: Literal["legacy", "structured", "hybrid"] = "legacy",
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

            if context_mode == "structured" and structured_context:
                result = self._process_structured_context(
                    structured_context=structured_context,
                    agent_type=AgentType.WRITER,
                    compose_phase=compose_phase or ComposePhase.EXPANSION,
                    context_processing_config=context_processing_config,
                    endpoint_strategy="expansion_specific_assembly"
                )
            elif context_mode == "hybrid":
                result = self._process_hybrid_context(
                    # Legacy params
                    system_prompts=system_prompts,
                    worldbuilding=worldbuilding,
                    story_summary=story_summary,
                    characters=characters,
                    outline_section=outline_section,
                    compose_phase=compose_phase,
                    phase_context=phase_context,
                    # Structured params
                    structured_context=structured_context,
                    agent_type=AgentType.WRITER,
                    endpoint_strategy="expansion_specific_assembly",
                    context_processing_config=context_processing_config
                )
            else:  # legacy mode
                result = self._process_legacy_context_for_flesh_out(
                    system_prompts=system_prompts,
                    worldbuilding=worldbuilding,
                    story_summary=story_summary,
                    characters=characters or [],
                    outline_section=outline_section or "",
                    compose_phase=compose_phase,
                    phase_context=phase_context
                )

            # Cache the result
            if self.enable_caching and cache_key:
                self._cache[cache_key] = result

            return result

        except Exception as e:
            logger.error(f"Error in process_flesh_out_context: {str(e)}")
            # Fallback to legacy processing
            return self._process_legacy_context_for_flesh_out(
                system_prompts=system_prompts,
                worldbuilding=worldbuilding,
                story_summary=story_summary,
                characters=characters or [],
                outline_section=outline_section or "",
                compose_phase=compose_phase,
                phase_context=phase_context
            )

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
                max_tokens=context_processing_config.get("max_context_length", 8000) if context_processing_config else 8000,
                summarization_threshold=context_processing_config.get("summarization_threshold", 6000) if context_processing_config else 6000,
                prioritize_recent=context_processing_config.get("prioritize_recent", True) if context_processing_config else True,
                include_relationships=context_processing_config.get("include_relationships", True) if context_processing_config else True
            )

            # Process context with ContextManager
            formatted_context, metadata = self.context_manager.process_context_for_agent(
                legacy_context, processing_config
            )

            # Parse the formatted context to extract system prompt and user message
            system_prompt, user_message = self._parse_formatted_context(
                formatted_context, agent_type, endpoint_strategy
            )

            # Create context metadata
            context_metadata = ContextMetadata(
                total_elements=metadata.get("original_element_count", 0),
                processing_applied=metadata.get("was_summarized", False),
                optimization_level="moderate" if metadata.get("was_summarized", False) else "none",
                compression_ratio=metadata.get("reduction_ratio"),
                processing_time_ms=metadata.get("processing_time_ms", 0)
            )

            return UnifiedContextResult(
                system_prompt=system_prompt,
                user_message=user_message,
                context_metadata=context_metadata,
                processing_mode="structured",
                optimization_applied=metadata.get("was_summarized", False),
                total_tokens=metadata.get("final_element_count", 0) * 100,  # Rough estimate
                compression_ratio=metadata.get("reduction_ratio", 1.0)
            )

        except Exception as e:
            logger.error(f"Error processing structured context: {str(e)}")
            raise

    def _process_hybrid_context(
        self,
        structured_context: StructuredContextContainer,
        agent_type: AgentType,
        endpoint_strategy: str,
        context_processing_config: Optional[Dict[str, Any]],
        **legacy_params
    ) -> UnifiedContextResult:
        """Process hybrid context using both legacy and structured data."""
        try:
            # Convert legacy context to structured format
            legacy_container, mapping = self.context_adapter.legacy_to_structured(
                system_prompts=legacy_params.get("system_prompts"),
                worldbuilding=legacy_params.get("worldbuilding"),
                story_summary=legacy_params.get("story_summary"),
                phase_context=legacy_params.get("phase_context"),
                compose_phase=legacy_params.get("compose_phase")
            )

            # Convert API structured context to legacy format for processing
            legacy_structured_context = convert_api_to_legacy_context(structured_context)
            
            # Merge legacy and structured contexts
            merged_elements = list(legacy_structured_context.elements) + list(legacy_container.elements)
            merged_container = LegacyStructuredContextContainer(
                elements=merged_elements,
                relationships=legacy_structured_context.relationships + legacy_container.relationships,
                global_metadata={
                    **legacy_structured_context.global_metadata,
                    **legacy_container.global_metadata,
                    "processing_mode": "hybrid",
                    "legacy_mapping": mapping.model_dump()
                }
            )

            # Process the merged context
            return self._process_structured_context(
                structured_context=merged_container,
                agent_type=agent_type,
                compose_phase=legacy_params.get("compose_phase", ComposePhase.CHAPTER_WRITING),
                context_processing_config=context_processing_config,
                endpoint_strategy=endpoint_strategy
            )

        except Exception as e:
            logger.error(f"Error processing hybrid context: {str(e)}")
            raise

    def _process_legacy_context_for_chapter(
        self,
        system_prompts: Optional[SystemPrompts],
        worldbuilding: Optional[str],
        story_summary: Optional[str],
        characters: List[CharacterInfo],
        plot_point: str,
        incorporated_feedback: List[FeedbackItem],
        previous_chapters: Optional[List[ChapterInfo]],
        compose_phase: Optional[ComposePhase],
        phase_context: Optional[PhaseContext]
    ) -> UnifiedContextResult:
        """Process legacy context for chapter generation using context optimization."""
        try:
            optimized = self.context_optimization.optimize_chapter_generation_context(
                system_prompts=system_prompts or SystemPrompts(),
                worldbuilding=worldbuilding or "",
                story_summary=story_summary or "",
                characters=characters,
                plot_point=plot_point,
                incorporated_feedback=incorporated_feedback,
                previous_chapters=previous_chapters,
                compose_phase=compose_phase,
                phase_context=phase_context
            )

            # Create context metadata for legacy processing
            context_metadata = ContextMetadata(
                total_elements=len(characters) + len(incorporated_feedback) + (1 if previous_chapters else 0),
                processing_applied=optimized.optimization_applied,
                optimization_level="moderate" if optimized.optimization_applied else "none",
                compression_ratio=optimized.compression_ratio if optimized.optimization_applied else None,
                processing_time_ms=0  # Not tracked in legacy system
            )

            return UnifiedContextResult(
                system_prompt=optimized.system_prompt,
                user_message=optimized.user_message,
                context_metadata=context_metadata,
                processing_mode="legacy",
                optimization_applied=optimized.optimization_applied,
                total_tokens=optimized.total_tokens,
                compression_ratio=optimized.compression_ratio
            )

        except Exception as e:
            logger.error(f"Error processing legacy context for chapter: {str(e)}")
            raise

    def _process_legacy_context_for_character(
        self,
        system_prompts: Optional[SystemPrompts],
        worldbuilding: Optional[str],
        story_summary: Optional[str],
        character: Optional[CharacterInfo],
        plot_point: str,
        compose_phase: Optional[ComposePhase],
        phase_context: Optional[PhaseContext]
    ) -> UnifiedContextResult:
        """Process legacy context for character feedback using context optimization."""
        try:
            optimized = self.context_optimization.optimize_character_feedback_context(
                system_prompts=system_prompts or SystemPrompts(),
                worldbuilding=worldbuilding or "",
                story_summary=story_summary or "",
                character=character or CharacterInfo(name="Character", basicBio="", sex=""),
                plot_point=plot_point,
                compose_phase=compose_phase,
                phase_context=phase_context
            )

            # Create context metadata for legacy processing
            context_metadata = ContextMetadata(
                total_elements=3,  # system_prompts, worldbuilding, story_summary
                processing_applied=optimized.optimization_applied,
                optimization_level="moderate" if optimized.optimization_applied else "none",
                compression_ratio=optimized.compression_ratio if optimized.optimization_applied else None,
                processing_time_ms=0  # Not tracked in legacy system
            )

            return UnifiedContextResult(
                system_prompt=optimized.system_prompt,
                user_message=optimized.user_message,
                context_metadata=context_metadata,
                processing_mode="legacy",
                optimization_applied=optimized.optimization_applied,
                total_tokens=optimized.total_tokens,
                compression_ratio=optimized.compression_ratio
            )

        except Exception as e:
            logger.error(f"Error processing legacy context for character: {str(e)}")
            raise

    def _process_legacy_context_for_editor(
        self,
        system_prompts: Optional[SystemPrompts],
        worldbuilding: Optional[str],
        story_summary: Optional[str],
        previous_chapters: List[ChapterInfo],
        plot_point: str,
        compose_phase: Optional[ComposePhase],
        phase_context: Optional[PhaseContext]
    ) -> UnifiedContextResult:
        """Process legacy context for editor review using context optimization."""
        try:
            optimized = self.context_optimization.optimize_editor_review_context(
                system_prompts=system_prompts or SystemPrompts(),
                worldbuilding=worldbuilding or "",
                story_summary=story_summary or "",
                previous_chapters=previous_chapters,
                plot_point=plot_point,
                compose_phase=compose_phase,
                phase_context=phase_context
            )

            # Create context metadata for legacy processing
            context_metadata = ContextMetadata(
                total_elements=len(previous_chapters) + 3,  # chapters + system_prompts, worldbuilding, story_summary
                processing_applied=optimized.optimization_applied,
                optimization_level="moderate" if optimized.optimization_applied else "none",
                compression_ratio=optimized.compression_ratio if optimized.optimization_applied else None,
                processing_time_ms=0  # Not tracked in legacy system
            )

            return UnifiedContextResult(
                system_prompt=optimized.system_prompt,
                user_message=optimized.user_message,
                context_metadata=context_metadata,
                processing_mode="legacy",
                optimization_applied=optimized.optimization_applied,
                total_tokens=optimized.total_tokens,
                compression_ratio=optimized.compression_ratio
            )

        except Exception as e:
            logger.error(f"Error processing legacy context for editor: {str(e)}")
            raise

    def _process_legacy_context_for_rater(
        self,
        system_prompts: Optional[SystemPrompts],
        rater_prompt: str,
        worldbuilding: Optional[str],
        story_summary: Optional[str],
        previous_chapters: List[ChapterInfo],
        plot_point: str,
        incorporated_feedback: List[FeedbackItem],
        compose_phase: Optional[ComposePhase],
        phase_context: Optional[PhaseContext]
    ) -> UnifiedContextResult:
        """Process legacy context for rater feedback using context optimization."""
        try:
            optimized = self.context_optimization.optimize_rater_feedback_context(
                system_prompts=system_prompts or SystemPrompts(),
                rater_prompt=rater_prompt,
                worldbuilding=worldbuilding or "",
                story_summary=story_summary or "",
                plot_point=plot_point,
                compose_phase=compose_phase,
                phase_context=phase_context
            )

            # Create context metadata for legacy processing
            context_metadata = ContextMetadata(
                total_elements=4,  # system_prompts, rater_prompt, worldbuilding, story_summary, plot_point
                processing_applied=optimized.optimization_applied,
                optimization_level="moderate" if optimized.optimization_applied else "none",
                compression_ratio=optimized.compression_ratio if optimized.optimization_applied else None,
                processing_time_ms=0  # Not tracked in legacy system
            )

            return UnifiedContextResult(
                system_prompt=optimized.system_prompt,
                user_message=optimized.user_message,
                context_metadata=context_metadata,
                processing_mode="legacy",
                optimization_applied=optimized.optimization_applied,
                total_tokens=optimized.total_tokens,
                compression_ratio=optimized.compression_ratio
            )

        except Exception as e:
            logger.error(f"Error processing legacy context for rater: {str(e)}")
            raise

    def _process_legacy_context_for_modify(
        self,
        system_prompts: Optional[SystemPrompts],
        worldbuilding: Optional[str],
        story_summary: Optional[str],
        characters: List[CharacterInfo],
        original_chapter: str,
        modification_request: str,
        compose_phase: Optional[ComposePhase],
        phase_context: Optional[PhaseContext]
    ) -> UnifiedContextResult:
        """Process legacy context for chapter modification using context optimization."""
        try:
            optimized = self.context_optimization.optimize_modify_chapter_context(
                system_prompts=system_prompts or SystemPrompts(),
                worldbuilding=worldbuilding or "",
                story_summary=story_summary or "",
                characters=characters,
                original_chapter=original_chapter,
                modification_request=modification_request,
                compose_phase=compose_phase,
                phase_context=phase_context
            )

            # Create context metadata for legacy processing
            context_metadata = ContextMetadata(
                total_elements=len(characters) + 5,  # + system_prompts, worldbuilding, story_summary, original_chapter, modification_request
                processing_applied=optimized.optimization_applied,
                optimization_level="moderate" if optimized.optimization_applied else "none",
                compression_ratio=optimized.compression_ratio if optimized.optimization_applied else None,
                processing_time_ms=0  # Not tracked in legacy system
            )

            return UnifiedContextResult(
                system_prompt=optimized.system_prompt,
                user_message=optimized.user_message,
                context_metadata=context_metadata,
                processing_mode="legacy",
                optimization_applied=optimized.optimization_applied,
                total_tokens=optimized.total_tokens,
                compression_ratio=optimized.compression_ratio
            )

        except Exception as e:
            logger.error(f"Error processing legacy context for modify: {str(e)}")
            raise

    def _process_legacy_context_for_flesh_out(
        self,
        system_prompts: Optional[SystemPrompts],
        worldbuilding: Optional[str],
        story_summary: Optional[str],
        characters: List[CharacterInfo],
        outline_section: str,
        compose_phase: Optional[ComposePhase],
        phase_context: Optional[PhaseContext]
    ) -> UnifiedContextResult:
        """Process legacy context for flesh out using context optimization."""
        try:
            optimized = self.context_optimization.optimize_flesh_out_context(
                system_prompts=system_prompts or SystemPrompts(),
                worldbuilding=worldbuilding or "",
                story_summary=story_summary or "",
                context="flesh_out",  # Fixed parameter name
                text_to_flesh_out=outline_section,  # Fixed parameter name
                compose_phase=compose_phase,
                phase_context=phase_context
            )

            # Create context metadata for legacy processing
            context_metadata = ContextMetadata(
                total_elements=4,  # system_prompts, worldbuilding, story_summary, context, text_to_flesh_out
                processing_applied=optimized.optimization_applied,
                optimization_level="moderate" if optimized.optimization_applied else "none",
                compression_ratio=optimized.compression_ratio if optimized.optimization_applied else None,
                processing_time_ms=0  # Not tracked in legacy system
            )

            return UnifiedContextResult(
                system_prompt=optimized.system_prompt,
                user_message=optimized.user_message,
                context_metadata=context_metadata,
                processing_mode="legacy",
                optimization_applied=optimized.optimization_applied,
                total_tokens=optimized.total_tokens,
                compression_ratio=optimized.compression_ratio
            )

        except Exception as e:
            logger.error(f"Error processing legacy context for flesh out: {str(e)}")
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
        system_prompt = "\n\n".join(system_sections) if system_sections else "You are a helpful AI assistant."
        user_message = "\n\n".join(user_sections) if user_sections else formatted_context
        
        return system_prompt, user_message

    def _generate_cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
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
                cache_params[key] = json.dumps(value, sort_keys=True, default=str)
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
