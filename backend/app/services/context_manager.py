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

from app.models.context_models import (
    AgentType,
    ContextProcessingConfig
)
from app.models.generation_models import (
    StructuredContextContainer,
    PlotElement,
    CharacterContext,
    UserRequest,
    SystemInstruction
)
from app.services.token_management.token_counter import (
    TokenCounter,
    ContentType,
    CountingStrategy
)
from app.services.token_management.layers import LayerType

logger = logging.getLogger(__name__)


@dataclass
class ContextItem:
    """Simple context item for backward compatibility."""
    content: str
    element_type: str  # Changed from ContextType to str
    priority: str  # Changed from int to str (high/medium/low)
    layer_type: LayerType
    metadata: Dict[str, Any]


@dataclass
class ContextAnalysis:
    """Analysis results for context processing."""
    total_tokens: int
    items_by_type: Dict[str, List[ContextItem]]  # Changed key from ContextType to str
    priority_distribution: Dict[str, int]  # Changed key from int to str
    layer_distribution: Dict[LayerType, int]
    optimization_suggestions: List[str]


class ContextManager:
    """Service for managing structured context elements."""

    def __init__(self, enable_session_persistence: bool = True):
        """Initialize the context manager."""
        self.formatter = ContextFormatter()
        self.token_counter = TokenCounter()  # Use TokenCounter for accurate token counting
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
            # Step 1: Filter collections for target agent
            relevant_collections = self._filter_elements_for_agent_and_phase(
                context_container, config.target_agent
            )

            # Step 2: Apply custom filters if provided
            if config.custom_filters:
                relevant_collections = self._apply_custom_filters(relevant_collections, config.custom_filters)

            # Step 3: Sort by priority
            sorted_collections = self._sort_elements_by_priority(
                relevant_collections, config.prioritize_recent
            )

            # Step 4: Include related elements if requested (no-op for new model)
            if config.include_relationships:
                sorted_collections = self._include_related_elements(sorted_collections)

            # Step 5: Apply token budget management
            final_collections, was_summarized = self._apply_token_budget(
                sorted_collections, config.max_tokens, config.summarization_threshold
            )

            # Step 6: Format for the target agent
            formatted_context = self.formatter.format_for_agent(
                final_collections, config.target_agent
            )

            # Step 7: Generate processing metadata
            original_count = (
                len(context_container.plot_elements) +
                len(context_container.character_contexts) +
                len(context_container.user_requests) +
                len(context_container.system_instructions)
            )
            filtered_count = sum(len(v) for v in relevant_collections.values())
            final_count = sum(len(v) for v in final_collections.values())

            metadata = self._generate_processing_metadata(
                original_count=original_count,
                filtered_count=filtered_count,
                final_count=final_count,
                was_summarized=was_summarized,
                target_agent=config.target_agent
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
        agent_type: AgentType
    ) -> Dict[str, List]:
        """
        Filter context elements for specific agent.

        Returns dict with keys: plot_elements, character_contexts, user_requests, system_instructions
        """
        filtered = {
            "plot_elements": [],
            "character_contexts": [],
            "user_requests": [],
            "system_instructions": []
        }

        # Plot elements - relevant for WRITER, RATER, EDITOR agents
        if agent_type in [AgentType.WRITER, AgentType.RATER, AgentType.EDITOR]:
            # Filter by phase-relevant tags if available
            for element in container.plot_elements:
                if self._is_plot_element_relevant(element, agent_type, phase):
                    filtered["plot_elements"].append(element)

        # Character contexts - relevant for CHARACTER and WRITER agents
        if agent_type in [AgentType.CHARACTER, AgentType.WRITER]:
            filtered["character_contexts"] = container.character_contexts

        # User requests - relevant for all agents (high priority user instructions)
        filtered["user_requests"] = [
            req for req in container.user_requests
            if self._is_user_request_relevant(req, agent_type, phase)
        ]

        # System instructions - relevant for all agents
        filtered["system_instructions"] = [
            inst for inst in container.system_instructions
            if self._is_system_instruction_relevant(inst, agent_type, phase)
        ]

        return filtered

    def _is_plot_element_relevant(self, element: PlotElement, agent_type: AgentType) -> bool:
        """Check if plot element is relevant for agent."""
        # High priority elements always included
        if element.priority == "high":
            return True

        # Medium priority included by default
        if element.priority == "medium":
            return True

        # Low priority included for WRITER
        if element.priority == "low" and agent_type == AgentType.WRITER:
            return True

        return False

    def _is_user_request_relevant(self, request: UserRequest, agent_type: AgentType) -> bool:
        """Check if user request is relevant for agent."""
        # High priority requests always included
        if request.priority == "high":
            return True

        # Medium priority for WRITER and EDITOR
        if request.priority == "medium" and agent_type in [AgentType.WRITER, AgentType.EDITOR]:
            return True

        return False

    def _is_system_instruction_relevant(self, instruction: SystemInstruction, agent_type: AgentType) -> bool:
        """Check if system instruction is relevant for agent."""
        # Global scope always included
        if instruction.scope == "global":
            return True

        # Agent-specific scope filtering
        scope_agent_map = {
            "character": [AgentType.CHARACTER, AgentType.WRITER],
            "scene": [AgentType.WRITER],
            "chapter": [AgentType.WRITER, AgentType.EDITOR],
            "story": [AgentType.WRITER, AgentType.RATER, AgentType.EDITOR]
        }

        relevant_agents = scope_agent_map.get(instruction.scope, [])
        if agent_type in relevant_agents:
            return True

        return False

    def _apply_custom_filters(
        self,
        collections: Dict[str, List],
        custom_filters: Dict[str, Any]
    ) -> Dict[str, List]:
        """Apply custom filtering criteria to collections."""
        filtered = {
            "plot_elements": [],
            "character_contexts": [],
            "user_requests": [],
            "system_instructions": []
        }

        # Filter plot elements
        for element in collections.get("plot_elements", []):
            if self._passes_custom_filter_plot(element, custom_filters):
                filtered["plot_elements"].append(element)

        # Filter character contexts
        for char in collections.get("character_contexts", []):
            if self._passes_custom_filter_character(char, custom_filters):
                filtered["character_contexts"].append(char)

        # Filter user requests
        for req in collections.get("user_requests", []):
            if self._passes_custom_filter_request(req, custom_filters):
                filtered["user_requests"].append(req)

        # Filter system instructions
        for inst in collections.get("system_instructions", []):
            if self._passes_custom_filter_instruction(inst, custom_filters):
                filtered["system_instructions"].append(inst)

        return filtered

    def _passes_custom_filter_plot(self, element: PlotElement, filters: Dict[str, Any]) -> bool:
        """Check if plot element passes custom filters."""
        # Filter by tags
        if 'required_tags' in filters:
            if not any(tag in element.tags for tag in filters['required_tags']):
                return False

        if 'excluded_tags' in filters:
            if any(tag in element.tags for tag in filters['excluded_tags']):
                return False

        # Filter by minimum priority
        if 'min_priority' in filters:
            priority_order = {"high": 3, "medium": 2, "low": 1}
            if priority_order.get(element.priority, 0) < priority_order.get(filters['min_priority'], 0):
                return False

        # Filter by type
        if 'allowed_types' in filters:
            if element.type not in filters['allowed_types']:
                return False

        return True

    def _passes_custom_filter_character(self, char: CharacterContext, filters: Dict[str, Any]) -> bool:
        """Check if character context passes custom filters."""
        # Filter by character IDs
        if 'character_ids' in filters:
            if char.character_id not in filters['character_ids']:
                return False

        return True

    def _passes_custom_filter_request(self, req: UserRequest, filters: Dict[str, Any]) -> bool:
        """Check if user request passes custom filters."""
        # Filter by minimum priority
        if 'min_priority' in filters:
            priority_order = {"high": 3, "medium": 2, "low": 1}
            if priority_order.get(req.priority, 0) < priority_order.get(filters['min_priority'], 0):
                return False

        return True

    def _passes_custom_filter_instruction(self, inst: SystemInstruction, filters: Dict[str, Any]) -> bool:
        """Check if system instruction passes custom filters."""
        # Filter by minimum priority
        if 'min_priority' in filters:
            priority_order = {"high": 3, "medium": 2, "low": 1}
            if priority_order.get(inst.priority, 0) < priority_order.get(filters['min_priority'], 0):
                return False

        return True

    def _sort_elements_by_priority(
        self,
        collections: Dict[str, List],
        prioritize_recent: bool = True
    ) -> Dict[str, List]:
        """Sort elements within each collection by priority."""
        sorted_collections = {
            "plot_elements": [],
            "character_contexts": [],
            "user_requests": [],
            "system_instructions": []
        }

        # Priority mapping for sorting
        priority_order = {"high": 3, "medium": 2, "low": 1}

        # Sort plot elements by priority (high first)
        sorted_collections["plot_elements"] = sorted(
            collections.get("plot_elements", []),
            key=lambda x: -priority_order.get(x.priority, 0)
        )

        # Character contexts - keep original order (no priority field)
        sorted_collections["character_contexts"] = collections.get("character_contexts", [])

        # Sort user requests by priority
        sorted_collections["user_requests"] = sorted(
            collections.get("user_requests", []),
            key=lambda x: -priority_order.get(x.priority, 0)
        )

        # Sort system instructions by priority
        sorted_collections["system_instructions"] = sorted(
            collections.get("system_instructions", []),
            key=lambda x: -priority_order.get(x.priority, 0)
        )

        return sorted_collections

    def _include_related_elements(
        self,
        collections: Dict[str, List]
    ) -> Dict[str, List]:
        """
        Include related context elements based on relationships.

        Note: In the new model, character relationships are embedded in
        CharacterContext.relationships (Dict[str, str]), so no additional
        relationship processing is needed.
        """
        # Character relationships are already embedded in CharacterContext objects
        # No additional processing needed
        return collections

    def _apply_token_budget(
        self,
        collections: Dict[str, List],
        max_tokens: Optional[int],
        summarization_threshold: int
    ) -> Tuple[Dict[str, List], bool]:
        """Apply token budget constraints using TokenCounter."""
        if not max_tokens:
            return collections, False

        # Calculate current token usage using TokenCounter
        current_tokens = self._count_collection_tokens(collections)

        if current_tokens <= max_tokens:
            return collections, False

        # Need to reduce token usage
        if current_tokens <= summarization_threshold:
            # Just trim lowest priority elements
            return self._trim_collections_by_priority(collections, max_tokens), False

        # Need summarization (simplified: trim more aggressively)
        return self._trim_collections_by_priority(collections, max_tokens), True

    def _count_collection_tokens(self, collections: Dict[str, List]) -> int:
        """Count tokens across all collections using TokenCounter."""
        total = 0

        # Count plot elements
        for element in collections.get("plot_elements", []):
            result = self.token_counter.count_tokens(
                element.content,
                content_type=ContentType.NARRATIVE,
                strategy=CountingStrategy.EXACT
            )
            total += result.token_count

        # Count character contexts
        for char in collections.get("character_contexts", []):
            char_text = self._format_character_for_counting(char)
            result = self.token_counter.count_tokens(
                char_text,
                content_type=ContentType.CHARACTER_DESCRIPTION,
                strategy=CountingStrategy.EXACT
            )
            total += result.token_count

        # Count user requests
        for req in collections.get("user_requests", []):
            result = self.token_counter.count_tokens(
                req.content,
                content_type=ContentType.METADATA,
                strategy=CountingStrategy.EXACT
            )
            total += result.token_count

        # Count system instructions
        for inst in collections.get("system_instructions", []):
            result = self.token_counter.count_tokens(
                inst.content,
                content_type=ContentType.SYSTEM_PROMPT,
                strategy=CountingStrategy.EXACT
            )
            total += result.token_count

        return total

    def _format_character_for_counting(self, char: CharacterContext) -> str:
        """Format character context for token counting."""
        parts = [f"Character: {char.character_name}"]
        if char.current_state:
            parts.append(f"State: {char.current_state}")
        if char.goals:
            parts.append(f"Goals: {', '.join(char.goals)}")
        if char.recent_actions:
            parts.append(f"Actions: {', '.join(char.recent_actions)}")
        if char.memories:
            parts.append(f"Memories: {', '.join(char.memories)}")
        if char.personality_traits:
            parts.append(f"Traits: {', '.join(char.personality_traits)}")
        if char.relationships:
            parts.append(f"Relationships: {char.relationships}")
        return "; ".join(parts)

    def _trim_collections_by_priority(
        self,
        collections: Dict[str, List],
        max_tokens: int
    ) -> Dict[str, List]:
        """Trim collections to fit within token budget, removing lowest priority items first."""
        result = {
            "plot_elements": [],
            "character_contexts": [],
            "user_requests": [],
            "system_instructions": []
        }

        current_tokens = 0

        # Priority: high-priority system instructions first
        for inst in collections.get("system_instructions", []):
            if inst.priority == "high":
                tokens = self.token_counter.count_tokens(
                    inst.content, ContentType.SYSTEM_PROMPT, CountingStrategy.EXACT
                ).token_count
                if current_tokens + tokens <= max_tokens:
                    result["system_instructions"].append(inst)
                    current_tokens += tokens

        # Then high-priority plot elements
        for element in collections.get("plot_elements", []):
            if element.priority == "high":
                tokens = self.token_counter.count_tokens(
                    element.content, ContentType.NARRATIVE, CountingStrategy.EXACT
                ).token_count
                if current_tokens + tokens <= max_tokens:
                    result["plot_elements"].append(element)
                    current_tokens += tokens

        # Then character contexts (always include if possible)
        for char in collections.get("character_contexts", []):
            char_text = self._format_character_for_counting(char)
            tokens = self.token_counter.count_tokens(
                char_text, ContentType.CHARACTER_DESCRIPTION, CountingStrategy.EXACT
            ).token_count
            if current_tokens + tokens <= max_tokens:
                result["character_contexts"].append(char)
                current_tokens += tokens

        # Then high-priority user requests
        for req in collections.get("user_requests", []):
            if req.priority == "high":
                tokens = self.token_counter.count_tokens(
                    req.content, ContentType.METADATA, CountingStrategy.EXACT
                ).token_count
                if current_tokens + tokens <= max_tokens:
                    result["user_requests"].append(req)
                    current_tokens += tokens

        # Then medium priority items if there's room
        for inst in collections.get("system_instructions", []):
            if inst.priority == "medium":
                tokens = self.token_counter.count_tokens(
                    inst.content, ContentType.SYSTEM_PROMPT, CountingStrategy.EXACT
                ).token_count
                if current_tokens + tokens <= max_tokens:
                    result["system_instructions"].append(inst)
                    current_tokens += tokens

        for element in collections.get("plot_elements", []):
            if element.priority == "medium":
                tokens = self.token_counter.count_tokens(
                    element.content, ContentType.NARRATIVE, CountingStrategy.EXACT
                ).token_count
                if current_tokens + tokens <= max_tokens:
                    result["plot_elements"].append(element)
                    current_tokens += tokens

        for req in collections.get("user_requests", []):
            if req.priority == "medium":
                tokens = self.token_counter.count_tokens(
                    req.content, ContentType.METADATA, CountingStrategy.EXACT
                ).token_count
                if current_tokens + tokens <= max_tokens:
                    result["user_requests"].append(req)
                    current_tokens += tokens

        return result

    def _generate_processing_metadata(
        self,
        original_count: int,
        filtered_count: int,
        final_count: int,
        was_summarized: bool,
        target_agent: AgentType
    ) -> Dict[str, Any]:
        """Generate metadata about context processing."""
        return {
            "original_element_count": original_count,
            "filtered_element_count": filtered_count,
            "final_element_count": final_count,
            "was_summarized": was_summarized,
            "target_agent": target_agent.value,
            "processing_timestamp": datetime.now(timezone.utc).isoformat(),
            "reduction_ratio": final_count / original_count if original_count > 0 else 0
        }


class ContextFormatter:
    """Service for formatting context elements for different agents."""

    def format_for_agent(
        self,
        collections: Dict[str, List],
        agent_type: AgentType
    ) -> str:
        """Format typed collections for a specific agent type."""
        if agent_type == AgentType.WRITER:
            return self._format_for_writer(collections)
        elif agent_type == AgentType.CHARACTER:
            return self._format_for_character(collections)
        elif agent_type == AgentType.RATER:
            return self._format_for_rater(collections)
        elif agent_type == AgentType.EDITOR:
            return self._format_for_editor(collections)
        elif agent_type == AgentType.WORLDBUILDING:
            return self._format_for_worldbuilding(collections)
        else:
            return self._format_for_generic(collections)

    def _format_for_writer(self, collections: Dict[str, List]) -> str:
        """Format context for the Writer agent using new model."""
        sections = []

        # System instructions
        if collections.get("system_instructions"):
            sections.append("=== SYSTEM INSTRUCTIONS ===")
            for inst in collections["system_instructions"]:
                sections.append(inst.content)

        # Plot elements
        if collections.get("plot_elements"):
            sections.append("\n=== PLOT CONTEXT ===")
            for element in collections["plot_elements"]:
                sections.append(f"- [{element.type}] {element.content}")

        # Character contexts
        if collections.get("character_contexts"):
            sections.append("\n=== CHARACTERS ===")
            for char in collections["character_contexts"]:
                char_info = self._format_character_context(char)
                sections.append(f"- {char.character_name}: {char_info}")

        # User requests
        if collections.get("user_requests"):
            sections.append("\n=== USER GUIDANCE ===")
            for req in collections["user_requests"]:
                sections.append(f"- [{req.type}] {req.content}")

        return "\n".join(sections)

    def _format_character_context(self, char: CharacterContext) -> str:
        """Format a character context into a readable string."""
        parts = []
        if char.current_state:
            parts.append(f"State: {char.current_state}")
        if char.goals:
            parts.append(f"Goals: {', '.join(char.goals)}")
        if char.personality_traits:
            parts.append(f"Traits: {', '.join(char.personality_traits)}")
        if char.relationships:
            parts.append(f"Relationships: {char.relationships}")
        return "; ".join(parts)

    def _format_for_character(self, collections: Dict[str, List]) -> str:
        """Format context for Character agents using new model."""
        sections = []

        # Character-specific elements first
        if collections.get("character_contexts"):
            sections.append("=== CHARACTER CONTEXT ===")
            for char in collections["character_contexts"]:
                char_info = self._format_character_context(char)
                sections.append(f"{char.character_name}: {char_info}")

        # Plot context relevant to character
        if collections.get("plot_elements"):
            sections.append("\n=== STORY BACKGROUND ===")
            for element in collections["plot_elements"]:
                sections.append(element.content)

        return "\n".join(sections)

    def _format_for_rater(self, collections: Dict[str, List]) -> str:
        """Format context for Rater agents using new model."""
        sections = []

        # Evaluation criteria from system instructions
        if collections.get("system_instructions"):
            sections.append("=== EVALUATION CRITERIA ===")
            for inst in collections["system_instructions"]:
                sections.append(inst.content)

        # Story context for evaluation
        if collections.get("plot_elements"):
            sections.append("\n=== STORY CONTEXT FOR EVALUATION ===")
            for element in collections["plot_elements"]:
                sections.append(element.content)

        return "\n".join(sections)

    def _format_for_editor(self, collections: Dict[str, List]) -> str:
        """Format context for Editor agent using new model."""
        sections = []

        # Editorial guidelines
        if collections.get("system_instructions"):
            sections.append("=== EDITORIAL GUIDELINES ===")
            for inst in collections["system_instructions"]:
                sections.append(inst.content)

        # Story consistency context
        if collections.get("character_contexts"):
            sections.append("\n=== CONSISTENCY CONTEXT ===")
            for char in collections["character_contexts"]:
                sections.append(f"{char.character_name}: {self._format_character_context(char)}")

        return "\n".join(sections)

    def _format_for_worldbuilding(self, collections: Dict[str, List]) -> str:
        """Format context for Worldbuilding agent using new model."""
        sections = []

        # Plot elements (may contain worldbuilding)
        if collections.get("plot_elements"):
            sections.append("=== CURRENT WORLDBUILDING ===")
            for element in collections["plot_elements"]:
                sections.append(element.content)

        return "\n".join(sections)

    def _format_generic(self, collections: Dict[str, List]) -> str:
        """Generic formatting for unknown agent types using new model."""
        sections = []

        for collection_name, items in collections.items():
            if items:
                sections.append(f"=== {collection_name.upper().replace('_', ' ')} ===")
                for item in items:
                    if hasattr(item, 'content'):
                        sections.append(item.content)
                    else:
                        sections.append(str(item))

        return "\n".join(sections)
