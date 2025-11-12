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
from app.services.plot_outline_extractor import get_plot_outline_extractor
from app.core.config import settings
from app.models.context_models import (
    ContextProcessingConfig,
    AgentType
)
from app.models.generation_models import (
    StructuredContextContainer,
    SystemPrompts,
    CharacterInfo,
    ChapterInfo,
    FeedbackItem,
    ContextMetadata,
    PlotElement,
    CharacterContext,
    UserRequest,
    SystemInstruction
)
from app.models.request_context import RequestContext

logger = logging.getLogger(__name__)


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

    def _convert_request_context_to_structured(
        self, 
        request_context: RequestContext
    ) -> StructuredContextContainer:
        """
        Convert RequestContext to StructuredContextContainer for internal processing.
        
        This method maps the rich RequestContext structure to the format expected
        by the ContextManager, preserving all relevant information while organizing
        it according to the established context categories.
        """
        try:
            # Handle null request_context
            if request_context is None:
                from app.models.generation_models import ContextMetadata
                error_metadata = ContextMetadata(
                    total_elements=0,
                    processing_applied=False,
                    processing_mode="structured",
                    optimization_level="none"
                )
                return StructuredContextContainer(
                    plot_elements=[],
                    character_contexts=[],
                    user_requests=[],
                    system_instructions=[],
                    metadata=error_metadata
                )
            
            plot_elements = []
            character_contexts = []
            user_requests = []
            system_instructions = []
            
            # Map system prompts to system instructions
            if request_context.configuration.system_prompts.main_prefix:
                system_instructions.append(SystemInstruction(
                    id="main_prefix",
                    type="behavior",
                    content=request_context.configuration.system_prompts.main_prefix,
                    scope="global",
                    priority="high"
                ))
            
            if request_context.configuration.system_prompts.main_suffix:
                system_instructions.append(SystemInstruction(
                    id="main_suffix",
                    type="behavior", 
                    content=request_context.configuration.system_prompts.main_suffix,
                    scope="global",
                    priority="high"
                ))
            
            if request_context.configuration.system_prompts.assistant_prompt:
                system_instructions.append(SystemInstruction(
                    id="assistant_prompt",
                    type="behavior",
                    content=request_context.configuration.system_prompts.assistant_prompt,
                    scope="agent",
                    priority="high"
                ))
            
            if request_context.configuration.system_prompts.editor_prompt:
                system_instructions.append(SystemInstruction(
                    id="editor_prompt",
                    type="behavior",
                    content=request_context.configuration.system_prompts.editor_prompt,
                    scope="agent",
                    priority="high"
                ))
            
            # Map worldbuilding content to plot elements
            if request_context.worldbuilding.content:
                plot_elements.append(PlotElement(
                    id="worldbuilding_main",
                    type="setup",
                    content=request_context.worldbuilding.content,
                    priority="high",
                    tags=["worldbuilding"]
                ))
            
            # Map worldbuilding key elements
            for i, element in enumerate(request_context.worldbuilding.key_elements):
                plot_elements.append(PlotElement(
                    id=f"worldbuilding_element_{i}",
                    type="setup",
                    content=f"{element.name}: {element.description}",
                    priority=element.importance,
                    tags=["worldbuilding", element.type]
                ))
            
            # Map story outline to plot elements
            if request_context.story_outline.content:
                plot_elements.append(PlotElement(
                    id="story_outline_main",
                    type="outline",
                    content=request_context.story_outline.content,
                    priority="high",
                    tags=["outline"]
                ))
            
            if request_context.story_outline.summary:
                plot_elements.append(PlotElement(
                    id="story_summary",
                    type="summary",
                    content=request_context.story_outline.summary,
                    priority="high",
                    tags=["summary"]
                ))
            
            # Map outline items to plot elements
            for item in request_context.story_outline.outline_items:
                plot_elements.append(PlotElement(
                    id=f"outline_item_{item.id}",
                    type="scene" if item.type == "scene" else "outline",
                    content=f"{item.title}: {item.description}",
                    priority="medium",
                    tags=["outline", item.type]
                ))
            
            # Map characters to character contexts
            for char in request_context.characters:
                if char.is_hidden:
                    continue  # Skip hidden characters
                    
                character_contexts.append(CharacterContext(
                    character_id=char.id,
                    character_name=char.name,
                    current_state=char.current_state,
                    goals=char.goals,
                    recent_actions=char.recent_actions,
                    memories=char.memories,
                    personality_traits=[char.personality] if char.personality else []
                ))
            
            # Map recent chapters to plot elements (limit to last 3 chapters for context)
            recent_chapters = sorted(request_context.chapters, key=lambda x: x.number, reverse=True)[:3]
            for chapter in recent_chapters:
                if chapter.content:
                    plot_elements.append(PlotElement(
                        id=f"chapter_{chapter.number}",
                        type="recent_story",
                        content=f"Chapter {chapter.number}: {chapter.title}\n{chapter.content}",
                        priority="medium",
                        tags=["chapter", "recent_story"]
                    ))
                
                # Include chapter plot points
                if chapter.plot_point:
                    plot_elements.append(PlotElement(
                        id=f"chapter_{chapter.number}_plot_point",
                        type="scene",
                        content=chapter.plot_point,
                        priority="medium",
                        tags=["plot_point", "chapter"]
                    ))
                
                # Include key plot items from chapters
                for i, plot_item in enumerate(chapter.key_plot_items):
                    plot_elements.append(PlotElement(
                        id=f"chapter_{chapter.number}_plot_item_{i}",
                        type="scene",
                        content=plot_item,
                        priority="low",
                        tags=["plot_item", "chapter"]
                    ))
            
            # Create metadata for the conversion
            from app.models.generation_models import ContextMetadata
            metadata = ContextMetadata(
                total_elements=len(plot_elements) + len(character_contexts) + len(user_requests) + len(system_instructions),
                processing_applied=True,
                processing_mode="structured",
                optimization_level="none"
            )
            
            # Create the structured context container
            return StructuredContextContainer(
                plot_elements=plot_elements,
                character_contexts=character_contexts,
                user_requests=user_requests,
                system_instructions=system_instructions,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error converting RequestContext to StructuredContextContainer: {str(e)}")
            # Return minimal valid container on error
            from app.models.generation_models import ContextMetadata
            error_metadata = ContextMetadata(
                total_elements=0,
                processing_applied=False,
                processing_mode="structured",
                optimization_level="none"
            )
            return StructuredContextContainer(
                plot_elements=[],
                character_contexts=[],
                user_requests=[],
                system_instructions=[],
                metadata=error_metadata
            )

    def process_generate_chapter_context(
        self,
        request_context: Optional[RequestContext],
        context_processing_config: Optional[Dict[str, Any]] = None,
        # Legacy parameter for backward compatibility
        structured_context: Optional[StructuredContextContainer] = None
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

            # Convert RequestContext to StructuredContextContainer
            if structured_context:
                # Use legacy structured context if provided (backward compatibility)
                context_to_process = structured_context
            elif request_context:
                # Convert RequestContext to StructuredContextContainer
                context_to_process = self._convert_request_context_to_structured(request_context)
            else:
                # Neither structured_context nor request_context provided
                raise ValueError("Either request_context or structured_context must be provided")

            # Enhance structured context with plot outline information if available
            enhanced_context = self._enhance_with_plot_outline_context(
                context_to_process, context_processing_config, request_context
            )
            
            result = self._process_structured_context(
                structured_context=enhanced_context,
                agent_type=AgentType.WRITER,
                context_processing_config=context_processing_config,
                endpoint_strategy="full_narrative_assembly"
            )

            # Cache the result
            if self.enable_caching and cache_key:
                self._cache[cache_key] = result
                logger.debug(
                    f"Cached result for generate_chapter: {cache_key}")

            return result

        except Exception as e:
            logger.error(f"Error in process_generate_chapter_context: {str(e)}")
            # Fallback to legacy processing
            raise ValueError("Legacy context processing is no longer supported. Please provide structured_context.")

    def process_character_feedback_context(
        self,
        request_context: RequestContext,
        context_processing_config: Optional[Dict[str, Any]] = None,
        # Legacy parameter for backward compatibility
        structured_context: Optional[StructuredContextContainer] = None
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

            # Convert RequestContext to StructuredContextContainer
            if structured_context:
                # Use legacy structured context if provided (backward compatibility)
                context_to_process = structured_context
            else:
                # Convert RequestContext to StructuredContextContainer
                context_to_process = self._convert_request_context_to_structured(request_context)

            result = self._process_structured_context(
                structured_context=context_to_process,
                agent_type=AgentType.CHARACTER,
                context_processing_config=context_processing_config,
                endpoint_strategy="character_specific_prioritization"
            )

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
        request_context: RequestContext,
        context_processing_config: Optional[Dict[str, Any]] = None,
        # Legacy parameter for backward compatibility
        structured_context: Optional[StructuredContextContainer] = None
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

            # Convert RequestContext to StructuredContextContainer
            if structured_context:
                # Use legacy structured context if provided (backward compatibility)
                context_to_process = structured_context
            else:
                # Convert RequestContext to StructuredContextContainer
                context_to_process = self._convert_request_context_to_structured(request_context)

            result = self._process_structured_context(
                structured_context=context_to_process,
                agent_type=AgentType.EDITOR,
                context_processing_config=context_processing_config,
                endpoint_strategy="review_focused_filtering"
            )

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
        request_context: RequestContext,
        context_processing_config: Optional[Dict[str, Any]] = None,
        # Legacy fields (kept for backward compatibility in method signature)
        rater_prompt: Optional[str] = None,
        plot_point: Optional[str] = None,
        structured_context: Optional[StructuredContextContainer] = None
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

            # Convert RequestContext to StructuredContextContainer
            if structured_context:
                # Use legacy structured context if provided (backward compatibility)
                context_to_process = structured_context
            else:
                # Convert RequestContext to StructuredContextContainer
                context_to_process = self._convert_request_context_to_structured(request_context)

            result = self._process_structured_context(
                structured_context=context_to_process,
                agent_type=AgentType.RATER,
                context_processing_config=context_processing_config,
                endpoint_strategy="rater_specific_preparation"
            )

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
        request_context: RequestContext,
        context_processing_config: Optional[Dict[str, Any]] = None,
        # Legacy fields
        system_prompts: Optional[SystemPrompts] = None,
        worldbuilding: Optional[str] = None,
        story_summary: Optional[str] = None,
        characters: Optional[List[CharacterInfo]] = None,
        original_chapter: Optional[str] = None,
        modification_request: Optional[str] = None,
        structured_context: Optional[StructuredContextContainer] = None
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

            # Convert RequestContext to StructuredContextContainer
            if structured_context:
                # Use legacy structured context if provided (backward compatibility)
                context_to_process = structured_context
            else:
                # Convert RequestContext to StructuredContextContainer
                context_to_process = self._convert_request_context_to_structured(request_context)

            result = self._process_structured_context(
                structured_context=context_to_process,
                agent_type=AgentType.WRITER,
                context_processing_config=context_processing_config,
                endpoint_strategy="change_focused_management"
            )

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
        request_context: RequestContext,
        context_processing_config: Optional[Dict[str, Any]] = None,
        # Legacy fields
        system_prompts: Optional[SystemPrompts] = None,
        worldbuilding: Optional[str] = None,
        story_summary: Optional[str] = None,
        characters: Optional[List[CharacterInfo]] = None,
        outline_section: Optional[str] = None,
        structured_context: Optional[StructuredContextContainer] = None
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

            # Convert RequestContext to StructuredContextContainer
            if structured_context:
                # Use legacy structured context if provided (backward compatibility)
                context_to_process = structured_context
            else:
                # Convert RequestContext to StructuredContextContainer
                context_to_process = self._convert_request_context_to_structured(request_context)

            result = self._process_structured_context(
                structured_context=context_to_process,
                agent_type=AgentType.WRITER,
                context_processing_config=context_processing_config,
                endpoint_strategy="expansion_specific_assembly"
            )

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
        request_context: RequestContext,
        context_processing_config: Optional[Dict[str, Any]] = None,
        # Legacy fields
        system_prompts: Optional[SystemPrompts] = None,
        worldbuilding: Optional[str] = None,
        story_summary: Optional[str] = None,
        basic_bio: Optional[str] = None,
        existing_characters: Optional[List[Dict[str, str]]] = None,
        structured_context: Optional[StructuredContextContainer] = None
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

            # Convert RequestContext to StructuredContextContainer
            if structured_context:
                # Use legacy structured context if provided (backward compatibility)
                context_to_process = structured_context
            else:
                # Convert RequestContext to StructuredContextContainer
                context_to_process = self._convert_request_context_to_structured(request_context)

            result = self._process_structured_context(
                structured_context=context_to_process,
                agent_type=AgentType.WRITER,
                context_processing_config=context_processing_config,
                endpoint_strategy="character_generation_prioritization"
            )

            # Cache the result
            if self.enable_caching and cache_key:
                self._cache[cache_key] = result

            return result

        except Exception as e:
            logger.error(f"Error in process_character_generation_context: {str(e)}")
            # Fallback to legacy processing
            raise ValueError("Legacy context processing is no longer supported. Please provide structured_context.")

    def _process_structured_context(
        self,
        structured_context: StructuredContextContainer,
        agent_type: AgentType,
        context_processing_config: Optional[Dict[str, Any]],
        endpoint_strategy: str
    ) -> UnifiedContextResult:
        """Process structured context using ContextManager."""
        try:
            # Create processing configuration
            processing_config = ContextProcessingConfig(
                target_agent=agent_type,
                max_tokens=context_processing_config.get(
                    "max_context_length", 8000) if context_processing_config else 8000,
                summarization_threshold=context_processing_config.get(
                    "summarization_threshold", 6000) if context_processing_config else 6000,
                prioritize_recent=context_processing_config.get(
                    "prioritize_recent", True) if context_processing_config else True,
                include_relationships=context_processing_config.get(
                    "include_relationships", True) if context_processing_config else True
            )

            # Process context with ContextManager (using structured context method)
            formatted_context, metadata = self.context_manager.process_structured_context_for_agent(
                structured_context, processing_config
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

    def _enhance_with_plot_outline_context(
        self,
        structured_context: StructuredContextContainer,
        context_processing_config: Optional[Dict[str, Any]] = None,
        request_context: Optional[RequestContext] = None
    ) -> StructuredContextContainer:
        """
        Enhance structured context with plot outline information when available.
        
        This method extracts relevant plot outline information and adds it as
        PlotElement objects to the structured context for chapter generation.
        """
        try:
            # Extract plot outline information from config
            plot_outline_content = None
            draft_outline_items = None
            chapter_number = 1
            story_context = None

            # Try to extract from RequestContext first, then fall back to context processing config
            if request_context:
                plot_outline_content = request_context.story_outline.content
                draft_outline_items = [
                    {
                        'id': item.id,
                        'title': item.title,
                        'description': item.description,
                        'key_plot_items': item.key_plot_items,
                        'order': item.order,
                        'type': item.type
                    }
                    for item in request_context.story_outline.outline_items
                ]
                chapter_number = context_processing_config.get('chapter_number', 1) if context_processing_config else 1
                story_context = {
                    'story_title': request_context.context_metadata.story_title,
                    'worldbuilding': request_context.worldbuilding.content,
                    'characters': [char.name for char in request_context.characters if not char.is_hidden]
                }
            elif context_processing_config:
                plot_outline_content = context_processing_config.get('plot_outline_content')
                draft_outline_items = context_processing_config.get('draft_outline_items')
                chapter_number = context_processing_config.get('chapter_number', 1)
                story_context = context_processing_config.get('story_context')
            
            # If no plot outline data is available, return original context
            if not plot_outline_content and not draft_outline_items:
                logger.debug("No plot outline data available for context enhancement")
                return structured_context
            
            # Extract plot outline elements using the plot outline extractor
            plot_extractor = get_plot_outline_extractor()
            plot_outline_elements = plot_extractor.extract_chapter_outline_elements(
                plot_outline_content=plot_outline_content,
                draft_outline_items=draft_outline_items,
                chapter_number=chapter_number,
                story_context=story_context
            )
            
            if not plot_outline_elements:
                logger.debug(f"No relevant plot outline elements found for chapter {chapter_number}")
                return structured_context
            
            # Create a copy of the structured context and add plot outline elements
            enhanced_context = StructuredContextContainer(
                plot_elements=structured_context.plot_elements + plot_outline_elements,
                character_contexts=structured_context.character_contexts,
                user_requests=structured_context.user_requests,
                system_instructions=structured_context.system_instructions,
                metadata=structured_context.metadata
            )
            
            logger.info(f"Enhanced context with {len(plot_outline_elements)} plot outline elements for chapter {chapter_number}")
            return enhanced_context
            
        except Exception as e:
            logger.warning(f"Error enhancing context with plot outline: {str(e)}")
            # Return original context on error to maintain backward compatibility
            return structured_context

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
