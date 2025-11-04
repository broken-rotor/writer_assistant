"""
Context Conversion Utilities for Writer Assistant API.

This module provides utilities to convert between the legacy context_models
and the enhanced generation_models during the migration process.

Key Features:
- Convert from generation_models to context_models format
- Convert from context_models to generation_models format
- Handle metadata mapping and default value assignment
- Maintain backward compatibility during transition
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone

# Import from generation_models (new format)
from app.models.generation_models import (
    StructuredContextContainer as NewStructuredContextContainer,
    PlotElement,
    CharacterContext,
    UserRequest,
    SystemInstruction,
    EnhancedContextMetadata,
    ContextType,
    AgentType,
    ComposePhase,
    SummarizationRule,
    ContextProcessingConfig
)

# Import from context_models (legacy format)
from app.models.context_models import (
    StructuredContextContainer as LegacyStructuredContextContainer,
    BaseContextElement,
    SystemContextElement,
    StoryContextElement,
    CharacterContextElement,
    UserContextElement,
    PhaseContextElement,
    ConversationContextElement,
    ContextMetadata as LegacyContextMetadata,
    ContextRelationship,
    ContextProcessingConfig as LegacyContextProcessingConfig
)

logger = logging.getLogger(__name__)


def convert_new_to_legacy_context(
    new_context: NewStructuredContextContainer
) -> LegacyStructuredContextContainer:
    """
    Convert from enhanced generation_models format to legacy context_models format.
    
    This function is used during the transition period to maintain compatibility
    with services that haven't been migrated yet.
    """
    elements = []
    
    # Convert plot elements to story context elements
    for plot_element in new_context.plot_elements:
        metadata = _convert_enhanced_to_legacy_metadata(plot_element.metadata)
        
        element = StoryContextElement(
            id=plot_element.id or f"plot_{len(elements)}",
            type=ContextType.PLOT_OUTLINE,
            content=plot_element.content,
            metadata=metadata,
            story_aspect=plot_element.type,
            chapter_relevance=None
        )
        elements.append(element)
    
    # Convert character contexts to character context elements
    for char_context in new_context.character_contexts:
        metadata = _convert_enhanced_to_legacy_metadata(char_context.metadata)
        
        # Create content from character context
        content = f"Character: {char_context.character_name}\n"
        if char_context.current_state:
            content += f"Current State: {char_context.current_state}\n"
        if char_context.goals:
            content += f"Goals: {', '.join(char_context.goals)}\n"
        if char_context.personality_traits:
            content += f"Personality: {', '.join(char_context.personality_traits)}\n"
        if char_context.memories:
            content += f"Memories: {'; '.join(char_context.memories)}"
        
        element = CharacterContextElement(
            id=char_context.character_id,
            type=ContextType.CHARACTER_PROFILE,
            content=content,
            character_id=char_context.character_id,
            character_name=char_context.character_name,
            related_characters=[],
            is_subjective=False,
            metadata=metadata
        )
        elements.append(element)
    
    # Convert user requests to user context elements
    for user_request in new_context.user_requests:
        metadata = _convert_enhanced_to_legacy_metadata(user_request.metadata)
        
        element = UserContextElement(
            id=user_request.id or f"user_{len(elements)}",
            type=ContextType.USER_REQUEST,
            content=user_request.content,
            user_intent=user_request.type,
            feedback_type=user_request.type if user_request.type in ["modification", "addition", "removal"] else None,
            incorporated=False,
            metadata=metadata
        )
        elements.append(element)
    
    # Convert system instructions to system context elements
    for sys_instruction in new_context.system_instructions:
        metadata = _convert_enhanced_to_legacy_metadata(sys_instruction.metadata)
        
        element = SystemContextElement(
            id=sys_instruction.id or f"sys_{len(elements)}",
            type=ContextType.SYSTEM_INSTRUCTION,
            content=sys_instruction.content,
            prompt_type=sys_instruction.type,
            applies_to_agents=metadata.target_agents if metadata else [AgentType.WRITER],
            metadata=metadata
        )
        elements.append(element)
    
    # Create legacy container
    return LegacyStructuredContextContainer(
        elements=elements,
        relationships=[],
        global_metadata={
            "total_elements": len(elements),
            "converted_from_new": True,
            "conversion_timestamp": datetime.now(tz=timezone.utc).isoformat()
        },
        total_estimated_tokens=new_context.calculate_total_tokens(),
        created_at=datetime.now(tz=timezone.utc),
        version="1.0"
    )


def convert_legacy_to_new_context(
    legacy_context: LegacyStructuredContextContainer
) -> NewStructuredContextContainer:
    """
    Convert from legacy context_models format to enhanced generation_models format.
    
    This function is used to migrate existing data to the new format.
    """
    plot_elements = []
    character_contexts = []
    user_requests = []
    system_instructions = []
    
    for element in legacy_context.elements:
        if isinstance(element, StoryContextElement):
            if element.type == ContextType.PLOT_OUTLINE:
                metadata = _convert_legacy_to_enhanced_metadata(element.metadata)
                
                plot_element = PlotElement(
                    id=element.id,
                    type="scene",  # Default type
                    content=element.content,
                    priority=_priority_float_to_literal(element.metadata.priority if element.metadata else 0.5),
                    tags=element.metadata.tags if element.metadata else [],
                    metadata=metadata
                )
                plot_elements.append(plot_element)
        
        elif isinstance(element, CharacterContextElement):
            metadata = _convert_legacy_to_enhanced_metadata(element.metadata)
            
            # Parse content back to structured format (basic parsing)
            current_state = {}
            goals = []
            memories = []
            personality_traits = []
            
            # Simple parsing of the content
            lines = element.content.split('\n')
            for line in lines:
                if line.startswith('Goals:'):
                    goals = [g.strip() for g in line.replace('Goals:', '').split(',') if g.strip()]
                elif line.startswith('Personality:'):
                    personality_traits = [p.strip() for p in line.replace('Personality:', '').split(',') if p.strip()]
                elif line.startswith('Memories:'):
                    memories = [m.strip() for m in line.replace('Memories:', '').split(';') if m.strip()]
            
            char_context = CharacterContext(
                character_id=element.character_id,
                character_name=element.character_name,
                current_state=current_state,
                recent_actions=[],
                relationships={},
                goals=goals,
                memories=memories,
                personality_traits=personality_traits,
                metadata=metadata
            )
            character_contexts.append(char_context)
        
        elif isinstance(element, UserContextElement):
            metadata = _convert_legacy_to_enhanced_metadata(element.metadata)
            
            user_request = UserRequest(
                id=element.id,
                type="general",  # Default type
                content=element.content,
                priority=_priority_float_to_literal(element.metadata.priority if element.metadata else 0.5),
                target=None,
                context=None,
                timestamp=element.metadata.created_at if element.metadata else None,
                metadata=metadata
            )
            user_requests.append(user_request)
        
        elif isinstance(element, SystemContextElement):
            metadata = _convert_legacy_to_enhanced_metadata(element.metadata)
            
            sys_instruction = SystemInstruction(
                id=element.id,
                type="behavior",  # Default type
                content=element.content,
                scope="global",
                priority=_priority_float_to_literal(element.metadata.priority if element.metadata else 0.5),
                conditions=None,
                metadata=metadata
            )
            system_instructions.append(sys_instruction)
    
    return NewStructuredContextContainer(
        plot_elements=plot_elements,
        character_contexts=character_contexts,
        user_requests=user_requests,
        system_instructions=system_instructions,
        metadata=None
    )


def convert_legacy_to_new_processing_config(
    legacy_config: LegacyContextProcessingConfig
) -> ContextProcessingConfig:
    """Convert legacy processing config to new format."""
    return ContextProcessingConfig(
        target_agent=legacy_config.target_agent,
        current_phase=legacy_config.current_phase,
        max_tokens=legacy_config.max_tokens,
        prioritize_recent=legacy_config.prioritize_recent,
        include_relationships=legacy_config.include_relationships,
        summarization_threshold=legacy_config.summarization_threshold,
        custom_filters=legacy_config.custom_filters
    )


def convert_new_to_legacy_processing_config(
    new_config: ContextProcessingConfig
) -> LegacyContextProcessingConfig:
    """Convert new processing config to legacy format."""
    return LegacyContextProcessingConfig(
        target_agent=new_config.target_agent,
        current_phase=new_config.current_phase,
        max_tokens=new_config.max_tokens,
        prioritize_recent=new_config.prioritize_recent,
        include_relationships=new_config.include_relationships,
        summarization_threshold=new_config.summarization_threshold,
        custom_filters=new_config.custom_filters
    )


def _convert_enhanced_to_legacy_metadata(
    enhanced_metadata: Optional[EnhancedContextMetadata]
) -> LegacyContextMetadata:
    """Convert enhanced metadata to legacy format."""
    if not enhanced_metadata:
        return LegacyContextMetadata()
    
    return LegacyContextMetadata(
        priority=enhanced_metadata.priority,
        summarization_rule=enhanced_metadata.summarization_rule,
        target_agents=enhanced_metadata.target_agents,
        relevant_phases=enhanced_metadata.relevant_phases,
        estimated_tokens=enhanced_metadata.estimated_tokens,
        created_at=enhanced_metadata.created_at,
        updated_at=enhanced_metadata.updated_at,
        expires_at=enhanced_metadata.expires_at,
        tags=enhanced_metadata.tags
    )


def _convert_legacy_to_enhanced_metadata(
    legacy_metadata: Optional[LegacyContextMetadata]
) -> Optional[EnhancedContextMetadata]:
    """Convert legacy metadata to enhanced format."""
    if not legacy_metadata:
        return None
    
    return EnhancedContextMetadata(
        priority=legacy_metadata.priority,
        summarization_rule=legacy_metadata.summarization_rule,
        target_agents=legacy_metadata.target_agents,
        relevant_phases=legacy_metadata.relevant_phases,
        estimated_tokens=legacy_metadata.estimated_tokens,
        created_at=legacy_metadata.created_at,
        updated_at=legacy_metadata.updated_at,
        expires_at=legacy_metadata.expires_at,
        tags=legacy_metadata.tags
    )


def _priority_float_to_literal(priority: float) -> str:
    """Convert float priority to literal string."""
    if priority >= 0.7:
        return "high"
    elif priority >= 0.4:
        return "medium"
    else:
        return "low"


def _priority_literal_to_float(priority: str) -> float:
    """Convert literal priority to float."""
    if priority == "high":
        return 0.8
    elif priority == "medium":
        return 0.5
    else:
        return 0.2
