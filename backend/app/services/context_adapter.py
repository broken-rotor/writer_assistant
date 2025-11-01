"""
Context Adapter Service for Writer Assistant API.

This service provides backward compatibility between the new structured context schema
and the existing legacy fields (SystemPrompts, worldbuilding, storySummary).

Handles:
- Converting legacy fields to structured context elements
- Converting structured context back to legacy format
- Enhancing PhaseContext with structured data
- Migration utilities for existing data
- Gradual transition support with feature flags
"""

from typing import Dict, List, Optional, Any, Tuple
import uuid
from datetime import datetime, timezone
from app.core.config import settings

from app.models.context_models import (
    StructuredContextContainer,
    SystemContextElement,
    StoryContextElement,
    UserContextElement,
    PhaseContextElement,
    ConversationContextElement,
    ContextType,
    AgentType,
    ComposePhase,
    SummarizationRule,
    ContextMetadata,
    LegacyContextMapping
)
from app.models.generation_models import SystemPrompts, PhaseContext, ConversationMessage


class ContextAdapter:
    """Service for converting between legacy and structured context formats."""

    def __init__(self):
        """Initialize the context adapter."""
        pass

    def legacy_to_structured(
        self,
        system_prompts: Optional[SystemPrompts] = None,
        worldbuilding: Optional[str] = None,
        story_summary: Optional[str] = None,
        phase_context: Optional[PhaseContext] = None,
        compose_phase: Optional[str] = None
    ) -> Tuple[StructuredContextContainer, LegacyContextMapping]:
        """
        Convert legacy context fields to structured context container.

        Returns:
            Tuple of (StructuredContextContainer, LegacyContextMapping)
        """
        elements = []
        mapping = LegacyContextMapping(
            system_prompts_mapping={},
            worldbuilding_elements=[],
            story_summary_elements=[],
            phase_context_elements=[]
        )

        # Convert SystemPrompts
        if system_prompts:
            system_elements, system_mapping = self._convert_system_prompts(system_prompts)
            elements.extend(system_elements)
            mapping.system_prompts_mapping.update(system_mapping)

        # Convert worldbuilding
        if worldbuilding and worldbuilding.strip():
            wb_elements = self._convert_worldbuilding(worldbuilding)
            elements.extend(wb_elements)
            mapping.worldbuilding_elements.extend([e.id for e in wb_elements])

        # Convert story summary
        if story_summary and story_summary.strip():
            summary_elements = self._convert_story_summary(story_summary)
            elements.extend(summary_elements)
            mapping.story_summary_elements.extend([e.id for e in summary_elements])

        # Convert PhaseContext
        if phase_context:
            phase_elements = self._convert_phase_context(phase_context, compose_phase)
            elements.extend(phase_elements)
            mapping.phase_context_elements.extend([e.id for e in phase_elements])

        # Create container
        container = StructuredContextContainer(
            elements=elements,
            global_metadata={
                "converted_from_legacy": True,
                "conversion_timestamp": datetime.now(timezone.utc).isoformat(),
                "legacy_compose_phase": compose_phase
            }
        )

        return container, mapping

    def structured_to_legacy(
        self,
        container: StructuredContextContainer,
        mapping: Optional[LegacyContextMapping] = None
    ) -> Tuple[SystemPrompts, str, str, PhaseContext]:
        """
        Convert structured context container back to legacy format.

        Returns:
            Tuple of (SystemPrompts, worldbuilding, story_summary, PhaseContext)
        """
        # Convert to SystemPrompts
        system_prompts = self._extract_system_prompts(container, mapping)

        # Convert to worldbuilding string
        worldbuilding = self._extract_worldbuilding(container, mapping)

        # Convert to story summary string
        story_summary = self._extract_story_summary(container, mapping)

        # Convert to PhaseContext
        phase_context = self._extract_phase_context(container, mapping)

        return system_prompts, worldbuilding, story_summary, phase_context

    def enhance_phase_context(
        self,
        phase_context: PhaseContext,
        structured_context: StructuredContextContainer
    ) -> PhaseContext:
        """
        Enhance existing PhaseContext with structured context data.
        """
        enhanced_context = phase_context.model_copy(deep=True) if phase_context else PhaseContext()

        # Add structured context elements as additional context
        phase_elements = structured_context.get_elements_by_type(ContextType.PHASE_INSTRUCTION)
        if phase_elements:
            additional_instructions = "\n".join([e.content for e in phase_elements])
            if enhanced_context.phase_specific_instructions:
                enhanced_context.phase_specific_instructions += f"\n\n{additional_instructions}"
            else:
                enhanced_context.phase_specific_instructions = additional_instructions

        # Add conversation context from structured elements
        conv_elements = structured_context.get_elements_by_type(ContextType.CONVERSATION_HISTORY)
        if conv_elements and not enhanced_context.conversation_history:
            # Convert structured conversation to PhaseContext format
            enhanced_context.conversation_history = []
            for element in conv_elements:
                if isinstance(element, ConversationContextElement):
                    # Parse conversation content (simplified)
                    lines = element.content.split('\n')
                    for line in lines:
                        if line.startswith('User: '):
                            enhanced_context.conversation_history.append(
                                ConversationMessage(role='user', content=line[6:])
                            )
                        elif line.startswith('Assistant: '):
                            enhanced_context.conversation_history.append(
                                ConversationMessage(role='assistant', content=line[11:])
                            )

        return enhanced_context

    def _convert_system_prompts(self, system_prompts: SystemPrompts) -> Tuple[List[SystemContextElement], Dict[str, str]]:
        """Convert SystemPrompts to structured context elements."""
        elements = []
        mapping = {}

        if system_prompts.mainPrefix:
            element_id = f"system_prompt_{uuid.uuid4().hex[:8]}"
            element = SystemContextElement(
                id=element_id,
                type=ContextType.SYSTEM_PROMPT,
                content=system_prompts.mainPrefix,
                prompt_type="main_prefix",
                applies_to_agents=[AgentType.WRITER, AgentType.CHARACTER, AgentType.RATER, AgentType.EDITOR],
                metadata=ContextMetadata(
                    priority=settings.CONTEXT_ADAPTER_SYSTEM_PREFIX_PRIORITY,
                    summarization_rule=SummarizationRule.PRESERVE_FULL,
                    target_agents=[AgentType.WRITER, AgentType.CHARACTER, AgentType.RATER, AgentType.EDITOR]
                )
            )
            elements.append(element)
            mapping["mainPrefix"] = element_id

        if system_prompts.mainSuffix:
            element_id = f"system_prompt_{uuid.uuid4().hex[:8]}"
            element = SystemContextElement(
                id=element_id,
                type=ContextType.SYSTEM_PROMPT,
                content=system_prompts.mainSuffix,
                prompt_type="main_suffix",
                applies_to_agents=[AgentType.WRITER, AgentType.CHARACTER, AgentType.RATER, AgentType.EDITOR],
                metadata=ContextMetadata(
                    priority=settings.CONTEXT_ADAPTER_SYSTEM_SUFFIX_PRIORITY,
                    summarization_rule=SummarizationRule.PRESERVE_FULL,
                    target_agents=[AgentType.WRITER, AgentType.CHARACTER, AgentType.RATER, AgentType.EDITOR]
                )
            )
            elements.append(element)
            mapping["mainSuffix"] = element_id

        if system_prompts.assistantPrompt:
            element_id = f"system_prompt_{uuid.uuid4().hex[:8]}"
            element = SystemContextElement(
                id=element_id,
                type=ContextType.SYSTEM_PROMPT,
                content=system_prompts.assistantPrompt,
                prompt_type="assistant_prompt",
                applies_to_agents=[AgentType.WRITER],
                metadata=ContextMetadata(
                    priority=settings.CONTEXT_ADAPTER_WRITING_ASSISTANT_PRIORITY,
                    summarization_rule=SummarizationRule.PRESERVE_FULL,
                    target_agents=[AgentType.WRITER]
                )
            )
            elements.append(element)
            mapping["assistantPrompt"] = element_id

        if system_prompts.editorPrompt:
            element_id = f"system_prompt_{uuid.uuid4().hex[:8]}"
            element = SystemContextElement(
                id=element_id,
                type=ContextType.SYSTEM_PROMPT,
                content=system_prompts.editorPrompt,
                prompt_type="editor_prompt",
                applies_to_agents=[AgentType.EDITOR],
                metadata=ContextMetadata(
                    priority=settings.CONTEXT_ADAPTER_WRITING_EDITOR_PRIORITY,
                    summarization_rule=SummarizationRule.PRESERVE_FULL,
                    target_agents=[AgentType.EDITOR]
                )
            )
            elements.append(element)
            mapping["editorPrompt"] = element_id

        return elements, mapping

    def _convert_worldbuilding(self, worldbuilding: str) -> List[StoryContextElement]:
        """Convert worldbuilding string to structured context elements."""
        elements = []

        # For now, create a single worldbuilding element
        # In the future, this could be enhanced to parse and split worldbuilding into categories
        element_id = f"worldbuilding_{uuid.uuid4().hex[:8]}"
        element = StoryContextElement(
            id=element_id,
            type=ContextType.WORLD_BUILDING,
            content=worldbuilding,
            story_aspect="general",
            metadata=ContextMetadata(
                priority=settings.CONTEXT_ADAPTER_CHARACTER_PROMPT_PRIORITY,
                summarization_rule=SummarizationRule.ALLOW_COMPRESSION,
                target_agents=[AgentType.WRITER, AgentType.CHARACTER, AgentType.WORLDBUILDING],
                tags=["worldbuilding", "legacy_converted"]
            )
        )
        elements.append(element)

        return elements

    def _convert_story_summary(self, story_summary: str) -> List[StoryContextElement]:
        """Convert story summary string to structured context elements."""
        elements = []

        element_id = f"story_summary_{uuid.uuid4().hex[:8]}"
        element = StoryContextElement(
            id=element_id,
            type=ContextType.STORY_SUMMARY,
            content=story_summary,
            metadata=ContextMetadata(
                priority=settings.CONTEXT_ADAPTER_RATER_PROMPT_PRIORITY,
                summarization_rule=SummarizationRule.ALLOW_COMPRESSION,
                target_agents=[AgentType.WRITER, AgentType.CHARACTER, AgentType.RATER, AgentType.EDITOR],
                tags=["story_summary", "legacy_converted"]
            )
        )
        elements.append(element)

        return elements

    def _convert_phase_context(
        self,
        phase_context: PhaseContext,
        compose_phase: Optional[str] = None
    ) -> List[PhaseContextElement]:
        """Convert PhaseContext to structured context elements."""
        elements = []

        # Convert previous phase output
        if phase_context.previous_phase_output:
            element_id = f"phase_output_{uuid.uuid4().hex[:8]}"
            element = PhaseContextElement(
                id=element_id,
                type=ContextType.PHASE_OUTPUT,
                content=phase_context.previous_phase_output,
                phase=ComposePhase(compose_phase) if compose_phase else ComposePhase.PLOT_OUTLINE,
                metadata=ContextMetadata(
                    priority=settings.CONTEXT_ADAPTER_EDITOR_PROMPT_PRIORITY,
                    summarization_rule=SummarizationRule.ALLOW_COMPRESSION,
                    target_agents=[AgentType.WRITER],
                    tags=["phase_output", "legacy_converted"]
                )
            )
            elements.append(element)

        # Convert phase-specific instructions
        if phase_context.phase_specific_instructions:
            element_id = f"phase_instruction_{uuid.uuid4().hex[:8]}"
            element = PhaseContextElement(
                id=element_id,
                type=ContextType.PHASE_INSTRUCTION,
                content=phase_context.phase_specific_instructions,
                phase=ComposePhase(compose_phase) if compose_phase else ComposePhase.PLOT_OUTLINE,
                metadata=ContextMetadata(
                    priority=settings.CONTEXT_ADAPTER_INSTRUCTION_PRIORITY,
                    summarization_rule=SummarizationRule.PRESERVE_FULL,
                    target_agents=[AgentType.WRITER],
                    tags=["phase_instruction", "legacy_converted"]
                )
            )
            elements.append(element)

        # Convert conversation history
        if phase_context.conversation_history:
            element_id = f"conversation_{uuid.uuid4().hex[:8]}"

            # Convert conversation messages to text format
            conversation_text = []
            for msg in phase_context.conversation_history:
                conversation_text.append(f"{msg.role.title()}: {msg.content}")

            element = ConversationContextElement(
                id=element_id,
                type=ContextType.CONVERSATION_HISTORY,
                content="\n".join(conversation_text),
                participant_roles=[msg.role for msg in phase_context.conversation_history],
                message_count=len(phase_context.conversation_history),
                metadata=ContextMetadata(
                    priority=settings.CONTEXT_ADAPTER_OUTPUT_PRIORITY,
                    summarization_rule=SummarizationRule.EXTRACT_KEY_POINTS,
                    target_agents=[AgentType.WRITER, AgentType.CHARACTER],
                    tags=["conversation", "legacy_converted"]
                )
            )
            elements.append(element)

        return elements

    def _extract_system_prompts(
        self,
        container: StructuredContextContainer,
        mapping: Optional[LegacyContextMapping] = None
    ) -> SystemPrompts:
        """Extract SystemPrompts from structured context."""
        system_prompts = SystemPrompts()

        system_elements = container.get_elements_by_type(ContextType.SYSTEM_PROMPT)

        for element in system_elements:
            if isinstance(element, SystemContextElement):
                if element.prompt_type == "main_prefix":
                    system_prompts.mainPrefix = element.content
                elif element.prompt_type == "main_suffix":
                    system_prompts.mainSuffix = element.content
                elif element.prompt_type == "assistant_prompt":
                    system_prompts.assistantPrompt = element.content
                elif element.prompt_type == "editor_prompt":
                    system_prompts.editorPrompt = element.content

        return system_prompts

    def _extract_worldbuilding(
        self,
        container: StructuredContextContainer,
        mapping: Optional[LegacyContextMapping] = None
    ) -> str:
        """Extract worldbuilding string from structured context."""
        wb_elements = container.get_elements_by_type(ContextType.WORLD_BUILDING)

        if not wb_elements:
            return ""

        # Combine all worldbuilding elements
        wb_parts = []
        for element in wb_elements:
            wb_parts.append(element.content)

        return "\n\n".join(wb_parts)

    def _extract_story_summary(
        self,
        container: StructuredContextContainer,
        mapping: Optional[LegacyContextMapping] = None
    ) -> str:
        """Extract story summary string from structured context."""
        summary_elements = container.get_elements_by_type(ContextType.STORY_SUMMARY)

        if not summary_elements:
            return ""

        # Combine all story summary elements
        summary_parts = []
        for element in summary_elements:
            summary_parts.append(element.content)

        return "\n\n".join(summary_parts)

    def _extract_phase_context(
        self,
        container: StructuredContextContainer,
        mapping: Optional[LegacyContextMapping] = None
    ) -> PhaseContext:
        """Extract PhaseContext from structured context."""
        phase_context = PhaseContext()

        # Extract phase output
        output_elements = container.get_elements_by_type(ContextType.PHASE_OUTPUT)
        if output_elements:
            phase_context.previous_phase_output = output_elements[0].content

        # Extract phase instructions
        instruction_elements = container.get_elements_by_type(ContextType.PHASE_INSTRUCTION)
        if instruction_elements:
            instructions = []
            for element in instruction_elements:
                instructions.append(element.content)
            phase_context.phase_specific_instructions = "\n\n".join(instructions)

        # Extract conversation history
        conv_elements = container.get_elements_by_type(ContextType.CONVERSATION_HISTORY)
        if conv_elements:
            phase_context.conversation_history = []
            for element in conv_elements:
                if isinstance(element, ConversationContextElement):
                    # Parse conversation content back to messages
                    lines = element.content.split('\n')
                    for line in lines:
                        if line.startswith('User: '):
                            phase_context.conversation_history.append(
                                ConversationMessage(role='user', content=line[6:])
                            )
                        elif line.startswith('Assistant: '):
                            phase_context.conversation_history.append(
                                ConversationMessage(role='assistant', content=line[11:])
                            )

        return phase_context

    def migrate_legacy_data(
        self,
        legacy_data: Dict[str, Any]
    ) -> StructuredContextContainer:
        """
        Migrate existing legacy data to structured format.

        Args:
            legacy_data: Dictionary containing legacy fields

        Returns:
            StructuredContextContainer with migrated data
        """
        system_prompts = None
        if 'systemPrompts' in legacy_data:
            system_prompts = SystemPrompts(**legacy_data['systemPrompts'])

        worldbuilding = legacy_data.get('worldbuilding', '')
        story_summary = legacy_data.get('storySummary', '')

        phase_context = None
        if 'phase_context' in legacy_data:
            phase_context = PhaseContext(**legacy_data['phase_context'])

        compose_phase = legacy_data.get('compose_phase')

        container, mapping = self.legacy_to_structured(
            system_prompts=system_prompts,
            worldbuilding=worldbuilding,
            story_summary=story_summary,
            phase_context=phase_context,
            compose_phase=compose_phase
        )

        # Add migration metadata
        container.global_metadata.update({
            "migration_source": "legacy_data",
            "migration_timestamp": datetime.now(timezone.utc).isoformat(),
            "original_data_keys": list(legacy_data.keys())
        })

        return container
