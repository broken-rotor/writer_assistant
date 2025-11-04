"""
Request transformation utilities for converting between different request formats.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.models.generation_models import CharacterFeedbackRequest
from app.models.context_models import (
    StructuredContextContainer,
    SystemContextElement,
    StoryContextElement,
    CharacterContextElement,
    UserContextElement,
    PhaseContextElement,
    ContextType,
    AgentType,
    ComposePhase
)


def transform_structured_character_feedback_request(structured_request: Dict[str, Any]) -> CharacterFeedbackRequest:
    """
    Transform a StructuredCharacterFeedbackRequest (from frontend) into a CharacterFeedbackRequest.
    
    Args:
        structured_request: Dictionary containing the structured request from frontend
        
    Returns:
        CharacterFeedbackRequest: Backend-compatible request object
    """
    # Extract core fields
    plot_point = structured_request.get('plotContext', {}).get('plotPoint', '')
    
    # Build structured context container
    context_elements = []
    
    # Add system prompts context
    if 'systemPrompts' in structured_request:
        system_prompts = structured_request['systemPrompts']
        system_element = SystemContextElement(
            content=f"Main Prefix: {system_prompts.get('mainPrefix', '')}\n"
                   f"Main Suffix: {system_prompts.get('mainSuffix', '')}",
            metadata={
                'target_agents': [AgentType.WRITER, AgentType.CHARACTER],
                'priority': 'high',
                'context_type': 'system_prompts'
            }
        )
        context_elements.append(system_element)
    
    # Add worldbuilding context
    if 'worldbuilding' in structured_request:
        worldbuilding = structured_request['worldbuilding']
        worldbuilding_element = StoryContextElement(
            content=worldbuilding.get('content', ''),
            metadata={
                'target_agents': [AgentType.WRITER, AgentType.CHARACTER],
                'priority': 'medium',
                'context_type': 'worldbuilding',
                'word_count': worldbuilding.get('wordCount')
            }
        )
        context_elements.append(worldbuilding_element)
    
    # Add story summary context
    if 'storySummary' in structured_request:
        story_summary = structured_request['storySummary']
        summary_element = StoryContextElement(
            content=story_summary.get('summary', ''),
            metadata={
                'target_agents': [AgentType.WRITER, AgentType.CHARACTER],
                'priority': 'high',
                'context_type': 'story_summary',
                'word_count': story_summary.get('wordCount')
            }
        )
        context_elements.append(summary_element)
    
    # Add previous chapters context
    if 'previousChapters' in structured_request:
        for chapter in structured_request['previousChapters']:
            chapter_element = StoryContextElement(
                content=f"Chapter {chapter.get('number', 'Unknown')}: {chapter.get('title', '')}\n"
                       f"{chapter.get('content', '')}",
                metadata={
                    'target_agents': [AgentType.WRITER, AgentType.CHARACTER],
                    'priority': 'medium',
                    'context_type': 'previous_chapter',
                    'chapter_number': chapter.get('number'),
                    'word_count': chapter.get('wordCount')
                }
            )
            context_elements.append(chapter_element)
    
    # Add character context
    if 'character' in structured_request:
        character = structured_request['character']
        character_content = f"""Character: {character.get('name', 'Unknown')}
Basic Bio: {character.get('basicBio', '')}
Sex: {character.get('sex', '')}
Gender: {character.get('gender', '')}
Sexual Preference: {character.get('sexualPreference', '')}
Age: {character.get('age', 'Unknown')}
Physical Appearance: {character.get('physicalAppearance', '')}
Usual Clothing: {character.get('usualClothing', '')}
Personality: {character.get('personality', '')}
Motivations: {character.get('motivations', '')}
Fears: {character.get('fears', '')}
Relationships: {character.get('relationships', '')}"""
        
        character_element = CharacterContextElement(
            content=character_content,
            character_name=character.get('name', 'Unknown'),
            metadata={
                'target_agents': [AgentType.CHARACTER],
                'priority': 'high',
                'context_type': 'character_profile',
                'character_name': character.get('name', 'Unknown')
            }
        )
        context_elements.append(character_element)
    
    # Add plot context as user request
    if 'plotContext' in structured_request:
        plot_context = structured_request['plotContext']
        plot_element = UserContextElement(
            content=f"Plot Point: {plot_context.get('plotPoint', '')}\n"
                   f"Plot Outline: {plot_context.get('plotOutline', '')}\n"
                   f"Plot Status: {plot_context.get('plotOutlineStatus', '')}",
            metadata={
                'target_agents': [AgentType.CHARACTER],
                'priority': 'high',
                'context_type': 'plot_context'
            }
        )
        context_elements.append(plot_element)
    
    # Add phase context if present
    compose_phase = None
    phase_context = None
    if 'phaseContext' in structured_request:
        phase_data = structured_request['phaseContext']
        current_phase = phase_data.get('currentPhase', 'chapter_detail')
        
        # Map frontend phase names to backend enum
        phase_mapping = {
            'plot_outline': ComposePhase.PLOT_OUTLINE,
            'chapter_detail': ComposePhase.CHAPTER_DETAIL,
            'final_edit': ComposePhase.FINAL_EDIT
        }
        compose_phase = phase_mapping.get(current_phase, ComposePhase.CHAPTER_DETAIL)
        
        phase_element = PhaseContextElement(
            content=f"Current Phase: {current_phase}\n"
                   f"Previous Phase Output: {phase_data.get('previousPhaseOutput', '')}\n"
                   f"Phase Instructions: {phase_data.get('phaseSpecificInstructions', '')}",
            phase=compose_phase,
            metadata={
                'target_agents': [AgentType.CHARACTER],
                'priority': 'medium',
                'context_type': 'phase_context'
            }
        )
        context_elements.append(phase_element)
        
        # Build phase context object
        phase_context = {
            'current_phase': compose_phase,
            'previous_phase_output': phase_data.get('previousPhaseOutput'),
            'phase_specific_instructions': phase_data.get('phaseSpecificInstructions'),
            'conversation_history': phase_data.get('conversationHistory', []),
            'conversation_branch_id': phase_data.get('conversationBranchId')
        }
    
    # Create structured context container
    structured_context = StructuredContextContainer(
        elements=context_elements,
        global_metadata={
            'request_source': 'structured_frontend',
            'transformation_timestamp': datetime.now(tz=timezone.utc).isoformat(),
            'original_request_metadata': structured_request.get('requestMetadata', {})
        }
    )
    
    # Create and return the backend request
    return CharacterFeedbackRequest(
        plotPoint=plot_point,
        compose_phase=compose_phase,
        phase_context=phase_context,
        structured_context=structured_context,
        context_processing_config=None  # Use defaults
    )


def is_structured_request(request_data: Dict[str, Any]) -> bool:
    """
    Determine if a request is in the structured format (from frontend) or legacy format.
    
    Args:
        request_data: Raw request dictionary
        
    Returns:
        bool: True if this is a structured request, False if legacy format
    """
    # Structured requests have these top-level keys that legacy requests don't
    structured_keys = {'systemPrompts', 'worldbuilding', 'storySummary', 'character', 'plotContext'}
    
    # Legacy requests have these keys that structured requests don't
    legacy_keys = {'structured_context', 'compose_phase', 'phase_context'}
    
    # Check if we have structured keys
    has_structured_keys = any(key in request_data for key in structured_keys)
    
    # Check if we have legacy keys
    has_legacy_keys = any(key in request_data for key in legacy_keys)
    
    # If we have structured keys and no legacy keys, it's a structured request
    if has_structured_keys and not has_legacy_keys:
        return True
    
    # If we have legacy keys and no structured keys, it's a legacy request
    if has_legacy_keys and not has_structured_keys:
        return False
    
    # If we have both or neither, default to legacy for backward compatibility
    return False
