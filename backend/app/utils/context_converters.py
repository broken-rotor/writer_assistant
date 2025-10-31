"""
Context conversion utilities for transforming between legacy and structured context formats.

This module provides utilities to convert data between the monolithic legacy format
(systemPrompts, worldbuilding, storySummary) and the new structured format with
granular context elements (plot_elements, character_contexts, user_requests, system_instructions).
"""
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime

from app.models.generation_models import (
    SystemPrompts,
    StructuredContextContainer,
    PlotElement,
    CharacterContext,
    UserRequest,
    SystemInstruction,
    ContextMetadata,
    CharacterInfo
)

logger = logging.getLogger(__name__)


class ContextConverter:
    """Utility class for converting between legacy and structured context formats."""

    @staticmethod
    def legacy_to_structured(
        system_prompts: Optional[SystemPrompts] = None,
        worldbuilding: Optional[str] = None,
        story_summary: Optional[str] = None,
        characters: Optional[List[CharacterInfo]] = None,
        user_request: Optional[str] = None,
        plot_point: Optional[str] = None
    ) -> StructuredContextContainer:
        """
        Convert legacy monolithic context to structured format.

        Args:
            system_prompts: Legacy system prompts configuration
            worldbuilding: Legacy worldbuilding text
            story_summary: Legacy story summary text
            characters: List of character information
            user_request: User's request or instruction
            plot_point: Current plot point being processed

        Returns:
            StructuredContextContainer with converted data
        """
        plot_elements = []
        character_contexts = []
        user_requests = []
        system_instructions = []

        # Convert worldbuilding to plot elements
        if worldbuilding and worldbuilding.strip():
            plot_elements.append(PlotElement(
                type="setup",
                content=worldbuilding,
                priority="high",
                tags=["worldbuilding", "setting"],
                metadata={"source": "legacy_worldbuilding"}
            ))

        # Convert story summary to plot elements
        if story_summary and story_summary.strip():
            plot_elements.append(PlotElement(
                type="setup",
                content=story_summary,
                priority="high",
                tags=["story_summary", "background"],
                metadata={"source": "legacy_story_summary"}
            ))

        # Convert current plot point to plot element
        if plot_point and plot_point.strip():
            plot_elements.append(PlotElement(
                type="scene",
                content=plot_point,
                priority="high",
                tags=["current_scene", "active"],
                metadata={"source": "current_plot_point"}
            ))

        # Convert characters to character contexts
        if characters:
            for char in characters:
                character_contexts.append(CharacterContext(
                    character_id=char.name.lower().replace(" ", "_"),
                    character_name=char.name,
                    current_state={
                        "bio": char.basicBio,
                        "personality": char.personality,
                        "motivations": char.motivations,
                        "fears": char.fears
                    },
                    relationships={"general": char.relationships} if char.relationships else {},
                    personality_traits=char.personality.split(", ") if char.personality else [],
                    goals=char.motivations.split(", ") if char.motivations else []
                ))

        # Convert user request to user requests
        if user_request and user_request.strip():
            user_requests.append(UserRequest(
                type="general",
                content=user_request,
                priority="high",
                timestamp=datetime.now()
            ))

        # Convert system prompts to system instructions
        if system_prompts:
            if system_prompts.mainPrefix and system_prompts.mainPrefix.strip():
                system_instructions.append(SystemInstruction(
                    type="behavior",
                    content=system_prompts.mainPrefix,
                    scope="global",
                    priority="high",
                    metadata={"source": "mainPrefix"}
                ))

            if system_prompts.mainSuffix and system_prompts.mainSuffix.strip():
                system_instructions.append(SystemInstruction(
                    type="behavior",
                    content=system_prompts.mainSuffix,
                    scope="global",
                    priority="high",
                    metadata={"source": "mainSuffix"}
                ))

            if system_prompts.assistantPrompt and system_prompts.assistantPrompt.strip():
                system_instructions.append(SystemInstruction(
                    type="behavior",
                    content=system_prompts.assistantPrompt,
                    scope="global",
                    priority="medium"
                ))

            if system_prompts.editorPrompt and system_prompts.editorPrompt.strip():
                system_instructions.append(SystemInstruction(
                    type="behavior",
                    content=system_prompts.editorPrompt,
                    scope="global",
                    priority="medium"
                ))

        # Create metadata
        metadata = ContextMetadata(
            total_elements=len(plot_elements) + len(character_contexts) + len(user_requests) + len(system_instructions),
            processing_applied=True,
            optimization_level="none"
        )

        return StructuredContextContainer(
            plot_elements=plot_elements,
            character_contexts=character_contexts,
            user_requests=user_requests,
            system_instructions=system_instructions,
            metadata=metadata
        )

    @staticmethod
    def structured_to_legacy(
        structured_context: StructuredContextContainer
    ) -> Tuple[Optional[SystemPrompts], str, str]:
        """
        Convert structured context back to legacy format.

        Args:
            structured_context: Structured context container

        Returns:
            Tuple of (SystemPrompts, worldbuilding, story_summary)
        """
        # Reconstruct system prompts
        main_prefix_parts = []
        main_suffix_parts = []
        assistant_prompt_parts = []
        editor_prompt_parts = []

        for instruction in structured_context.system_instructions:
            if instruction.type == "behavior":
                if instruction.scope == "global":
                    # Use metadata to distinguish between prefix and suffix
                    if instruction.metadata and instruction.metadata.get("source") == "mainPrefix":
                        main_prefix_parts.append(instruction.content)
                    elif instruction.metadata and instruction.metadata.get("source") == "mainSuffix":
                        main_suffix_parts.append(instruction.content)
                    elif instruction.priority == "high":
                        # Fallback for instructions without metadata
                        main_prefix_parts.append(instruction.content)
                    else:
                        main_suffix_parts.append(instruction.content)
                elif "assistant" in instruction.content.lower():
                    assistant_prompt_parts.append(instruction.content)
                elif "editor" in instruction.content.lower():
                    editor_prompt_parts.append(instruction.content)

        system_prompts = SystemPrompts(
            mainPrefix="\n\n".join(main_prefix_parts),
            mainSuffix="\n\n".join(main_suffix_parts),
            assistantPrompt="\n\n".join(assistant_prompt_parts) if assistant_prompt_parts else None,
            editorPrompt="\n\n".join(editor_prompt_parts) if editor_prompt_parts else None
        )

        # Reconstruct worldbuilding and story summary
        worldbuilding_parts = []
        story_summary_parts = []

        for plot_element in structured_context.plot_elements:
            if "worldbuilding" in plot_element.tags or "setting" in plot_element.tags:
                worldbuilding_parts.append(plot_element.content)
            elif "story_summary" in plot_element.tags or "background" in plot_element.tags:
                story_summary_parts.append(plot_element.content)
            elif plot_element.type in ["setup", "scene"]:
                # Default to story summary for general plot elements
                story_summary_parts.append(plot_element.content)

        worldbuilding = "\n\n".join(worldbuilding_parts)
        story_summary = "\n\n".join(story_summary_parts)

        return system_prompts, worldbuilding, story_summary

    @staticmethod
    def validate_conversion(
        original_system_prompts: Optional[SystemPrompts],
        original_worldbuilding: Optional[str],
        original_story_summary: Optional[str],
        structured_context: StructuredContextContainer
    ) -> Dict[str, Any]:
        """
        Validate that conversion preserved essential information.

        Args:
            original_system_prompts: Original system prompts
            original_worldbuilding: Original worldbuilding text
            original_story_summary: Original story summary text
            structured_context: Converted structured context

        Returns:
            Dictionary with validation results and metrics
        """
        validation_results = {
            "valid": True,
            "warnings": [],
            "metrics": {
                "plot_elements_created": len(structured_context.plot_elements),
                "character_contexts_created": len(structured_context.character_contexts),
                "user_requests_created": len(structured_context.user_requests),
                "system_instructions_created": len(structured_context.system_instructions)
            }
        }

        # Check if essential content was preserved
        if original_worldbuilding and original_worldbuilding.strip():
            worldbuilding_preserved = any(
                "worldbuilding" in elem.tags for elem in structured_context.plot_elements
            )
            if not worldbuilding_preserved:
                validation_results["warnings"].append("Worldbuilding content may not have been properly preserved")

        if original_story_summary and original_story_summary.strip():
            story_summary_preserved = any(
                "story_summary" in elem.tags for elem in structured_context.plot_elements
            )
            if not story_summary_preserved:
                validation_results["warnings"].append("Story summary content may not have been properly preserved")

        if original_system_prompts:
            system_prompts_preserved = len(structured_context.system_instructions) > 0
            if not system_prompts_preserved:
                validation_results["warnings"].append("System prompts may not have been properly preserved")

        # Check for empty conversion
        if structured_context.metadata and structured_context.metadata.total_elements == 0:
            validation_results["valid"] = False
            validation_results["warnings"].append("No context elements were created during conversion")

        return validation_results


def convert_legacy_request_to_structured(
    system_prompts: Optional[SystemPrompts] = None,
    worldbuilding: Optional[str] = None,
    story_summary: Optional[str] = None,
    characters: Optional[List[CharacterInfo]] = None,
    user_request: Optional[str] = None,
    plot_point: Optional[str] = None
) -> StructuredContextContainer:
    """
    Convenience function to convert legacy request data to structured format.

    This is a wrapper around ContextConverter.legacy_to_structured for easier use.
    """
    return ContextConverter.legacy_to_structured(
        system_prompts=system_prompts,
        worldbuilding=worldbuilding,
        story_summary=story_summary,
        characters=characters,
        user_request=user_request,
        plot_point=plot_point
    )


def convert_structured_to_legacy_request(
    structured_context: StructuredContextContainer
) -> Tuple[Optional[SystemPrompts], str, str]:
    """
    Convenience function to convert structured context back to legacy format.

    This is a wrapper around ContextConverter.structured_to_legacy for easier use.
    """
    return ContextConverter.structured_to_legacy(structured_context)
