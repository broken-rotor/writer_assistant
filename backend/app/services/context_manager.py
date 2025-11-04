"""
Context Manager Service for Writer Assistant API.

This service handles:
- Context prioritization based on metadata and current phase
- Intelligent summarization when token limits are approached
- Agent-specific context filtering and formatting
- Context combination and deduplication
- Token budget management and optimization
- Context validation and consistency checking
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone
import logging
from collections import defaultdict
from dataclasses import dataclass

from app.models.generation_models import (
    ContextType,
    AgentType,
    ComposePhase,
    SummarizationRule,
    ContextProcessingConfig
)
# Legacy imports for backward compatibility during transition
from app.models.context_models import (
    StructuredContextContainer,
    BaseContextElement,
    SystemContextElement,
    StoryContextElement,
    CharacterContextElement,
    UserContextElement,
    PhaseContextElement,
    ConversationContextElement
)
from app.services.token_management.layers import LayerType

logger = logging.getLogger(__name__)


@dataclass
class ContextItem:
    """Simple context item for backward compatibility."""
    content: str
    context_type: ContextType
    priority: int
    layer_type: LayerType
    metadata: Dict[str, Any]


@dataclass
class ContextAnalysis:
    """Analysis results for context processing."""
    total_tokens: int
    items_by_type: Dict[ContextType, List[ContextItem]]
    priority_distribution: Dict[int, int]
    layer_distribution: Dict[LayerType, int]
    optimization_suggestions: List[str]


class ContextManager:
    """Service for managing structured context elements."""

    def __init__(self, enable_session_persistence: bool = True):
        """Initialize the context manager."""
        self.summarizer = ContextSummarizer()
        self.formatter = ContextFormatter()
        self.enable_session_persistence = enable_session_persistence

        # Import here to avoid circular imports
        if enable_session_persistence:
            from app.services.context_session_manager import get_context_state_manager
            self.state_manager = get_context_state_manager()
        else:
            self.state_manager = None

    def process_context_for_agent(
        self,
        context_container: StructuredContextContainer,
        config: ContextProcessingConfig
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Process context container for a specific agent and phase.

        Returns:
            Tuple of (formatted_context_string, processing_metadata)
        """
        try:
            # Step 1: Filter elements for target agent and phase
            relevant_elements = self._filter_elements_for_agent_and_phase(
                context_container, config.target_agent, config.current_phase
            )

            # Step 2: Apply custom filters if provided
            if config.custom_filters:
                relevant_elements = self._apply_custom_filters(relevant_elements, config.custom_filters)

            # Step 3: Sort by priority and recency
            sorted_elements = self._sort_elements_by_priority(
                relevant_elements, config.prioritize_recent
            )

            # Step 4: Include related elements if requested
            if config.include_relationships:
                sorted_elements = self._include_related_elements(
                    sorted_elements, context_container.relationships
                )

            # Step 5: Apply token budget management
            final_elements, was_summarized = self._apply_token_budget(
                sorted_elements, config.max_tokens, config.summarization_threshold
            )

            # Step 6: Format for the target agent
            formatted_context = self.formatter.format_for_agent(
                final_elements, config.target_agent, config.current_phase
            )

            # Step 7: Generate processing metadata
            metadata = self._generate_processing_metadata(
                original_count=len(context_container.elements),
                filtered_count=len(relevant_elements),
                final_count=len(final_elements),
                was_summarized=was_summarized,
                target_agent=config.target_agent,
                current_phase=config.current_phase
            )

            return formatted_context, metadata

        except Exception as e:
            logger.error(f"Error processing context for agent {config.target_agent}: {str(e)}")
            raise

    def process_context_with_state(
        self,
        context_container: StructuredContextContainer,
        config: ContextProcessingConfig,
        context_state: Optional[str] = None,
        story_id: Optional[str] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Process context container with stateless state management support.

        Args:
            context_container: Context container to process
            config: Processing configuration
            context_state: Optional serialized context state from client
            story_id: Optional story ID for new states

        Returns:
            Tuple of (formatted_context_string, processing_metadata_with_state_info)
        """
        if not self.enable_session_persistence or not self.state_manager:
            # Fall back to regular processing
            return self.process_context_for_agent(context_container, config)

        try:
            # Get or create state
            if context_state:
                try:
                    state = self.state_manager.deserialize_state(context_state)
                    logger.debug(f"Using existing context state {state.state_id}")
                except Exception as e:
                    logger.warning(f"Failed to deserialize context state, creating new: {e}")
                    state = self.state_manager.create_initial_state(
                        story_id=story_id,
                        initial_context=context_container
                    )
            else:
                state = self.state_manager.create_initial_state(
                    story_id=story_id,
                    initial_context=context_container
                )

            # Process context normally
            formatted_context, metadata = self.process_context_for_agent(context_container, config)

            # Update state with processing history
            processing_metadata = {
                'agent_type': config.target_agent.value,
                'phase': config.current_phase.value,
                'token_count': metadata.get('final_token_count', 0),
                'elements_processed': metadata.get('final_count', 0),
                'was_summarized': metadata.get('was_summarized', False)
            }

            state = self.state_manager.add_processing_history(
                state,
                'context_processing',
                processing_metadata
            )

            # Update state context if it was modified during processing
            if metadata.get('was_summarized', False):
                state = self.state_manager.update_state_context(
                    state,
                    context_container,
                    processing_metadata
                )

            # Serialize state for client
            serialized_state = self.state_manager.serialize_state(state)

            # Add state information to metadata
            metadata['context_state'] = serialized_state
            metadata['state_id'] = state.state_id
            metadata['state_persistence_enabled'] = True

            return formatted_context, metadata

        except Exception as e:
            logger.error(f"Error processing context with state: {str(e)}")
            # Fall back to regular processing
            return self.process_context_for_agent(context_container, config)

    def _filter_elements_for_agent_and_phase(
        self,
        container: StructuredContextContainer,
        agent_type: AgentType,
        phase: ComposePhase
    ) -> List[BaseContextElement]:
        """Filter context elements for specific agent and phase."""
        filtered_elements = []

        for element in container.elements:
            # Check if element is relevant for this agent
            if agent_type not in element.metadata.target_agents:
                continue

            # Check if element is relevant for this phase
            if phase not in element.metadata.relevant_phases:
                continue

            # Check if element has expired
            if element.metadata.expires_at and element.metadata.expires_at < datetime.now(timezone.utc):
                continue

            filtered_elements.append(element)

        return filtered_elements

    def _apply_custom_filters(
        self,
        elements: List[BaseContextElement],
        custom_filters: Dict[str, Any]
    ) -> List[BaseContextElement]:
        """Apply custom filtering criteria."""
        filtered_elements = []

        for element in elements:
            include_element = True

            # Filter by tags if specified
            if 'required_tags' in custom_filters:
                required_tags = custom_filters['required_tags']
                if not any(tag in element.metadata.tags for tag in required_tags):
                    include_element = False

            # Filter by excluded tags if specified
            if 'excluded_tags' in custom_filters:
                excluded_tags = custom_filters['excluded_tags']
                if any(tag in element.metadata.tags for tag in excluded_tags):
                    include_element = False

            # Filter by minimum priority if specified
            if 'min_priority' in custom_filters:
                if element.metadata.priority < custom_filters['min_priority']:
                    include_element = False

            # Filter by context type if specified
            if 'allowed_types' in custom_filters:
                if element.type not in custom_filters['allowed_types']:
                    include_element = False

            # Filter by character if specified (for character contexts)
            if 'character_ids' in custom_filters and isinstance(element, CharacterContextElement):
                if element.character_id not in custom_filters['character_ids']:
                    include_element = False

            if include_element:
                filtered_elements.append(element)

        return filtered_elements

    def _sort_elements_by_priority(
        self,
        elements: List[BaseContextElement],
        prioritize_recent: bool = True
    ) -> List[BaseContextElement]:
        """Sort elements by priority and optionally by recency."""
        def sort_key(element: BaseContextElement) -> Tuple[float, datetime]:
            priority = element.metadata.priority

            # If prioritizing recent, use updated_at as secondary sort
            if prioritize_recent:
                recency = element.metadata.updated_at
            else:
                recency = element.metadata.created_at

            # Return negative priority for descending sort, positive datetime for ascending
            return (-priority, -recency.timestamp())

        return sorted(elements, key=sort_key)

    def _include_related_elements(
        self,
        elements: List[BaseContextElement],
        relationships: List[Any]
    ) -> List[BaseContextElement]:
        """Include related context elements based on relationships."""
        # For now, return elements as-is
        # TODO: Implement relationship-based inclusion logic
        return elements

    def _apply_token_budget(
        self,
        elements: List[BaseContextElement],
        max_tokens: Optional[int],
        summarization_threshold: float
    ) -> Tuple[List[BaseContextElement], bool]:
        """Apply token budget constraints with intelligent summarization."""
        if not max_tokens:
            return elements, False

        # Calculate current token usage
        current_tokens = sum(
            element.metadata.estimated_tokens or len(element.content) // 4
            for element in elements
        )

        if current_tokens <= max_tokens:
            return elements, False

        # Need to reduce token usage
        threshold_tokens = int(max_tokens * summarization_threshold)

        if current_tokens <= threshold_tokens:
            # Just trim lowest priority elements
            return self._trim_by_priority(elements, max_tokens), False

        # Need summarization
        return self._summarize_elements(elements, max_tokens), True

    def _trim_by_priority(
        self,
        elements: List[BaseContextElement],
        max_tokens: int
    ) -> List[BaseContextElement]:
        """Trim elements by removing lowest priority ones."""
        result = []
        current_tokens = 0

        for element in elements:  # Already sorted by priority
            element_tokens = element.metadata.estimated_tokens or len(element.content) // 4

            if current_tokens + element_tokens <= max_tokens:
                result.append(element)
                current_tokens += element_tokens
            else:
                # Check if we can include this element by removing some lower priority ones
                if element.metadata.summarization_rule == SummarizationRule.PRESERVE_FULL:
                    # Try to make room for this high-priority element
                    while result and current_tokens + element_tokens > max_tokens:
                        removed = result.pop()
                        removed_tokens = removed.metadata.estimated_tokens or len(removed.content) // 4
                        current_tokens -= removed_tokens

                    if current_tokens + element_tokens <= max_tokens:
                        result.append(element)
                        current_tokens += element_tokens
                break

        return result

    def _summarize_elements(
        self,
        elements: List[BaseContextElement],
        max_tokens: int
    ) -> List[BaseContextElement]:
        """Summarize elements to fit within token budget."""
        # Group elements by summarization rule
        preserve_full = []
        allow_compression = []
        extract_key_points = []
        omit_if_needed = []

        for element in elements:
            if element.metadata.summarization_rule == SummarizationRule.PRESERVE_FULL:
                preserve_full.append(element)
            elif element.metadata.summarization_rule == SummarizationRule.ALLOW_COMPRESSION:
                allow_compression.append(element)
            elif element.metadata.summarization_rule == SummarizationRule.EXTRACT_KEY_POINTS:
                extract_key_points.append(element)
            else:  # OMIT_IF_NEEDED
                omit_if_needed.append(element)

        # Start with preserve_full elements
        result = preserve_full[:]
        current_tokens = sum(
            element.metadata.estimated_tokens or len(element.content) // 4
            for element in result
        )

        remaining_tokens = max_tokens - current_tokens

        if remaining_tokens <= 0:
            logger.warning("PRESERVE_FULL elements exceed token budget")
            return preserve_full

        # Add compressed elements
        for element in allow_compression:
            compressed = self.summarizer.compress_element(element, remaining_tokens // 2)
            if compressed:
                result.append(compressed)
                compressed_tokens = compressed.metadata.estimated_tokens or len(compressed.content) // 4
                remaining_tokens -= compressed_tokens

        # Add key points from remaining elements
        for element in extract_key_points:
            if remaining_tokens > 50:  # Minimum tokens for key points
                key_points = self.summarizer.extract_key_points(element, min(remaining_tokens // 3, 100))
                if key_points:
                    result.append(key_points)
                    key_points_tokens = key_points.metadata.estimated_tokens or len(key_points.content) // 4
                    remaining_tokens -= key_points_tokens

        return result

    def _generate_processing_metadata(
        self,
        original_count: int,
        filtered_count: int,
        final_count: int,
        was_summarized: bool,
        target_agent: AgentType,
        current_phase: ComposePhase
    ) -> Dict[str, Any]:
        """Generate metadata about context processing."""
        return {
            "original_element_count": original_count,
            "filtered_element_count": filtered_count,
            "final_element_count": final_count,
            "was_summarized": was_summarized,
            "target_agent": target_agent.value,
            "current_phase": current_phase.value,
            "processing_timestamp": datetime.now(timezone.utc).isoformat(),
            "reduction_ratio": final_count / original_count if original_count > 0 else 0
        }


class ContextSummarizer:
    """Service for summarizing context elements."""

    def compress_element(
        self,
        element: BaseContextElement,
        target_tokens: int
    ) -> Optional[BaseContextElement]:
        """Compress a context element to fit within target tokens."""
        if element.metadata.summarization_rule == SummarizationRule.PRESERVE_FULL:
            return element

        current_tokens = element.metadata.estimated_tokens or len(element.content) // 4

        if current_tokens <= target_tokens:
            return element

        # Simple compression: truncate to target length
        target_chars = target_tokens * 4
        if len(element.content) > target_chars:
            compressed_content = element.content[:target_chars - 3] + "..."

            # Create compressed copy
            compressed_element = element.model_copy(deep=True)
            compressed_element.content = compressed_content
            compressed_element.metadata.estimated_tokens = target_tokens
            compressed_element.metadata.tags.append("compressed")

            return compressed_element

        return element

    def extract_key_points(
        self,
        element: BaseContextElement,
        target_tokens: int
    ) -> Optional[BaseContextElement]:
        """Extract key points from a context element."""
        # Simple key point extraction: take first and last sentences
        sentences = element.content.split('. ')

        if len(sentences) <= 2:
            return self.compress_element(element, target_tokens)

        key_points = f"{sentences[0]}. ... {sentences[-1]}"

        # Create key points copy
        key_points_element = element.model_copy(deep=True)
        key_points_element.content = key_points
        key_points_element.metadata.estimated_tokens = len(key_points) // 4
        key_points_element.metadata.tags.append("key_points")

        return key_points_element


class ContextFormatter:
    """Service for formatting context elements for different agents."""

    def format_for_agent(
        self,
        elements: List[BaseContextElement],
        agent_type: AgentType,
        phase: ComposePhase
    ) -> str:
        """Format context elements for a specific agent type."""
        if agent_type == AgentType.WRITER:
            return self._format_for_writer(elements, phase)
        elif agent_type == AgentType.CHARACTER:
            return self._format_for_character(elements, phase)
        elif agent_type == AgentType.RATER:
            return self._format_for_rater(elements, phase)
        elif agent_type == AgentType.EDITOR:
            return self._format_for_editor(elements, phase)
        elif agent_type == AgentType.WORLDBUILDING:
            return self._format_for_worldbuilding(elements, phase)
        else:
            return self._format_generic(elements, phase)

    def _format_for_writer(self, elements: List[BaseContextElement], phase: ComposePhase) -> str:
        """Format context for the Writer agent."""
        sections = []

        # Group elements by type
        by_type = defaultdict(list)
        for element in elements:
            by_type[element.type].append(element)

        # System prompts first
        if by_type[ContextType.SYSTEM_PROMPT]:
            sections.append("=== SYSTEM INSTRUCTIONS ===")
            for element in by_type[ContextType.SYSTEM_PROMPT]:
                sections.append(element.content)

        # Story context
        story_types = [ContextType.WORLD_BUILDING, ContextType.STORY_SUMMARY, ContextType.PLOT_OUTLINE]
        story_elements = []
        for story_type in story_types:
            story_elements.extend(by_type[story_type])

        if story_elements:
            sections.append("\n=== STORY CONTEXT ===")
            for element in story_elements:
                sections.append(f"- {element.type.value.replace('_', ' ').title()}: {element.content}")

        # Character information
        if by_type[ContextType.CHARACTER_PROFILE]:
            sections.append("\n=== CHARACTERS ===")
            for element in by_type[ContextType.CHARACTER_PROFILE]:
                if isinstance(element, CharacterContextElement):
                    sections.append(f"- {element.character_name}: {element.content}")

        # User instructions and feedback
        user_types = [ContextType.USER_INSTRUCTION, ContextType.USER_FEEDBACK, ContextType.USER_REQUEST]
        user_elements = []
        for user_type in user_types:
            user_elements.extend(by_type[user_type])

        if user_elements:
            sections.append("\n=== USER GUIDANCE ===")
            for element in user_elements:
                sections.append(f"- {element.content}")

        # Phase-specific context
        if by_type[ContextType.PHASE_INSTRUCTION]:
            sections.append(f"\n=== {phase.value.upper()} PHASE INSTRUCTIONS ===")
            for element in by_type[ContextType.PHASE_INSTRUCTION]:
                sections.append(element.content)

        return "\n".join(sections)

    def _format_for_character(self, elements: List[BaseContextElement], phase: ComposePhase) -> str:
        """Format context for Character agents."""
        sections = []

        # Character-specific elements first
        character_elements = [e for e in elements if isinstance(e, CharacterContextElement)]
        if character_elements:
            sections.append("=== CHARACTER CONTEXT ===")
            for element in character_elements:
                char_info = f"{element.type.value.replace('_', ' ').title()}: {element.content}"
                if hasattr(element, 'character_name') and element.character_name:
                    char_info += f" (Character: {element.character_name})"
                sections.append(char_info)

        # Story context relevant to character
        story_elements = [e for e in elements if e.type in [ContextType.WORLD_BUILDING, ContextType.STORY_SUMMARY]]
        if story_elements:
            sections.append("\n=== STORY BACKGROUND ===")
            for element in story_elements:
                sections.append(element.content)

        return "\n".join(sections)

    def _format_for_rater(self, elements: List[BaseContextElement], phase: ComposePhase) -> str:
        """Format context for Rater agents."""
        sections = []

        # Evaluation criteria from system prompts
        system_elements = [e for e in elements if e.type == ContextType.SYSTEM_PROMPT]
        if system_elements:
            sections.append("=== EVALUATION CRITERIA ===")
            for element in system_elements:
                sections.append(element.content)

        # Story context for evaluation
        story_elements = [e for e in elements if e.type in [ContextType.STORY_SUMMARY, ContextType.PLOT_OUTLINE]]
        if story_elements:
            sections.append("\n=== STORY CONTEXT FOR EVALUATION ===")
            for element in story_elements:
                sections.append(element.content)

        return "\n".join(sections)

    def _format_for_editor(self, elements: List[BaseContextElement], phase: ComposePhase) -> str:
        """Format context for Editor agent."""
        sections = []

        # Editorial guidelines
        system_elements = [e for e in elements if e.type in [ContextType.SYSTEM_PROMPT, ContextType.SYSTEM_INSTRUCTION]]
        if system_elements:
            sections.append("=== EDITORIAL GUIDELINES ===")
            for element in system_elements:
                sections.append(element.content)

        # Story consistency context
        story_elements = [e for e in elements if e.type in [ContextType.STORY_SUMMARY, ContextType.CHARACTER_PROFILE]]
        if story_elements:
            sections.append("\n=== CONSISTENCY CONTEXT ===")
            for element in story_elements:
                sections.append(element.content)

        return "\n".join(sections)

    def _format_for_worldbuilding(self, elements: List[BaseContextElement], phase: ComposePhase) -> str:
        """Format context for Worldbuilding agent."""
        sections = []

        # Worldbuilding elements
        wb_elements = [e for e in elements if e.type == ContextType.WORLD_BUILDING]
        if wb_elements:
            sections.append("=== CURRENT WORLDBUILDING ===")
            for element in wb_elements:
                sections.append(element.content)

        # Story context for worldbuilding
        story_elements = [e for e in elements if e.type == ContextType.STORY_SUMMARY]
        if story_elements:
            sections.append("\n=== STORY CONTEXT ===")
            for element in story_elements:
                sections.append(element.content)

        return "\n".join(sections)

    def _format_generic(self, elements: List[BaseContextElement], phase: ComposePhase) -> str:
        """Generic formatting for unknown agent types."""
        sections = []

        for element in elements:
            sections.append(f"=== {element.type.value.upper().replace('_', ' ')} ===")
            content = element.content
            # Include character name for character elements
            if isinstance(element, CharacterContextElement) and hasattr(element, 'character_name') and element.character_name:
                content += f" (Character: {element.character_name})"
            sections.append(content)

        return "\n".join(sections)
