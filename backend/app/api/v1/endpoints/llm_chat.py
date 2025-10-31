"""
LLM Chat endpoint for direct conversations with AI agents.
Separate from RAG chat functionality.
"""
from fastapi import APIRouter, HTTPException
from app.models.chat_models import LLMChatRequest, LLMChatResponse, ConversationMessage
from app.models.worldbuilding_models import WorldbuildingChatContext
from app.services.llm_inference import get_llm
from app.services.worldbuilding_classifier import WorldbuildingTopicClassifier
from app.services.worldbuilding_prompts import WorldbuildingPromptService
from app.services.worldbuilding_followup import WorldbuildingFollowupGenerator
from app.services.worldbuilding_state_machine import WorldbuildingStateMachine
from datetime import datetime, UTC
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize worldbuilding services
worldbuilding_classifier = WorldbuildingTopicClassifier()
worldbuilding_prompts = WorldbuildingPromptService()
worldbuilding_followup = WorldbuildingFollowupGenerator()
worldbuilding_state_machine = WorldbuildingStateMachine()


def _build_agent_system_prompt(agent_type: str, compose_context=None, system_prompts=None, worldbuilding_context=None) -> str:
    """Build system prompt based on agent type and context."""
    base_prompts = {
        'writer': "You are a skilled writer assistant helping with story creation. "
                  "Provide creative, engaging responses that help develop compelling narratives.",
        'character': "You are a character development specialist. Help create authentic, "
                     "well-rounded characters with realistic motivations and behaviors.",
        'editor': "You are an experienced editor providing constructive feedback on writing. "
                  "Focus on narrative flow, consistency, and overall story quality.",
        'worldbuilding': "You are a worldbuilding specialist helping create rich, immersive fictional worlds. "
                         "Guide users through developing comprehensive world details including geography, cultures, "
                         "magic systems, politics, history, and societies. Ask thoughtful follow-up questions to "
                         "help expand and deepen their world creation."}

    prompt = base_prompts.get(agent_type, base_prompts['writer'])

    # Enhanced worldbuilding prompt handling
    if agent_type == 'worldbuilding' and worldbuilding_context:
        # Use specialized worldbuilding prompts
        current_topic = worldbuilding_context.get('current_topic', 'general')
        conversation_context = worldbuilding_context.get('conversation_context', '')
        story_context = worldbuilding_context.get('story_context', '')

        prompt = worldbuilding_prompts.build_contextual_prompt(
            current_topic, conversation_context, story_context
        )

    # Add phase-specific context if available
    if compose_context:
        phase_guidance = {
            'plot_outline': "Focus on plot structure, story beats, and narrative arc development.",
            'chapter_detail': "Help with scene development, character interactions, and detailed storytelling.",
            'final_edit': "Provide polishing suggestions, consistency checks, and final refinements."
        }
        phase_context = phase_guidance.get(compose_context.current_phase, "")
        if phase_context:
            prompt += f"\n\nCurrent phase: {compose_context.current_phase}. {phase_context}"

    # Add custom system prompts if provided
    if system_prompts:
        if system_prompts.mainPrefix:
            prompt = f"{system_prompts.mainPrefix}\n{prompt}"
        if system_prompts.mainSuffix:
            prompt = f"{prompt}\n{system_prompts.mainSuffix}"

    return prompt


def _build_conversation_context(messages, compose_context=None) -> str:
    """Build context from conversation history and compose context."""
    context_parts = []

    if compose_context and compose_context.story_context:
        context_parts.append("Story Context:")
        for key, value in compose_context.story_context.items():
            if value:
                context_parts.append(f"- {key}: {value}")

    if compose_context and compose_context.chapter_draft:
        context_parts.append(f"\nCurrent Chapter Draft:\n{compose_context.chapter_draft}")

    return "\n".join(context_parts) if context_parts else ""


@router.post("/chat/llm", response_model=LLMChatResponse)
async def llm_chat(request: LLMChatRequest):
    """
    Direct LLM chat for interactive conversations with AI agents.
    Separate from RAG chat functionality.
    Enhanced with worldbuilding conversation intelligence.
    """
    llm = get_llm()
    if not llm:
        raise HTTPException(status_code=503, detail="LLM not initialized. Start server with --model-path")

    try:
        # Handle worldbuilding agent requests with specialized processing
        if request.agent_type == 'worldbuilding':
            return await _handle_worldbuilding_chat(request, llm)

        # Standard chat processing for other agent types
        return await _handle_standard_chat(request, llm)

    except Exception as e:
        logger.error(f"Error in llm_chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in LLM chat: {str(e)}")


async def _handle_worldbuilding_chat(request: LLMChatRequest, llm) -> LLMChatResponse:
    """Handle worldbuilding chat with specialized processing."""

    # Extract story ID from compose context
    story_id = request.compose_context.story_context.get('story_id', 'default') if request.compose_context else 'default'

    # Get or create conversation state
    conversation_state = worldbuilding_state_machine.get_or_create_conversation_state(story_id)

    # Classify the latest user message if available
    topic_classification = None
    latest_user_message = None

    for msg in reversed(request.messages):
        if msg.role == 'user':
            latest_user_message = msg
            break

    if latest_user_message:
        classification_result = worldbuilding_classifier.classify_message(
            latest_user_message.content,
            conversation_state.current_topic
        )
        topic_classification = {
            'primary_topic': classification_result.primary_topic,
            'confidence': classification_result.confidence,
            'secondary_topics': classification_result.secondary_topics,
            'keywords_found': classification_result.keywords_found
        }

    # Update conversation state
    if latest_user_message:
        updated_state, actions = worldbuilding_state_machine.process_message(
            story_id, latest_user_message, topic_classification
        )
    else:
        updated_state = conversation_state
        actions = []

    # Build worldbuilding context for prompt generation
    worldbuilding_context = {
        'current_topic': updated_state.current_topic,
        'conversation_context': _build_worldbuilding_conversation_context(updated_state),
        'story_context': _build_conversation_context(request.messages, request.compose_context)
    }

    # Build system prompt with worldbuilding context
    system_prompt = _build_agent_system_prompt(
        request.agent_type,
        request.compose_context,
        request.system_prompts,
        worldbuilding_context
    )

    # Build conversation context
    context = worldbuilding_context['story_context']

    # Prepare messages for LLM
    llm_messages = [{"role": "system", "content": system_prompt}]

    # Add context as first user message if available
    if context:
        llm_messages.append({"role": "user", "content": f"Context:\n{context}"})
        llm_messages.append({"role": "assistant",
                             "content": "I understand the context. How can I help you with your worldbuilding?"})

    # Add conversation history
    for msg in request.messages:
        llm_messages.append({
            "role": msg.role,
            "content": msg.content
        })

    # Get LLM response
    response_text = llm.chat_completion(
        llm_messages,
        max_tokens=request.max_tokens,
        temperature=request.temperature
    )

    # Create response message
    response_message = ConversationMessage(
        role="assistant",
        content=response_text.strip(),
        timestamp=datetime.now(UTC).isoformat()
    )

    # Update conversation state with assistant response
    worldbuilding_state_machine.process_message(story_id, response_message)

    # Generate follow-up questions
    wb_context = WorldbuildingChatContext(
        story_id=story_id,
        current_topic=updated_state.current_topic,
        conversation_state=updated_state.current_state,
        active_topics=list(updated_state.branches[updated_state.current_branch_id].topic_contexts.keys()),
        topic_contexts=updated_state.branches[updated_state.current_branch_id].topic_contexts,
        recent_messages=request.messages[-5:],  # Last 5 messages
        story_context=request.compose_context.story_context if request.compose_context else {}
    )

    followup_questions = worldbuilding_followup.generate_followup_questions(
        wb_context, request.messages, max_questions=3
    )

    # Build enhanced metadata
    metadata = {
        "generatedAt": datetime.now(UTC).isoformat(),
        "phase": request.compose_context.current_phase if request.compose_context else None,
        "conversationLength": len(request.messages),
        "contextProvided": bool(context),
        "worldbuilding": {
            "currentTopic": updated_state.current_topic,
            "conversationState": updated_state.current_state,
            "topicClassification": topic_classification,
            "followupQuestions": [q.question for q in followup_questions],
            "stateActions": actions,
            "overallProgress": sum(
                ctx.completeness_score
                for ctx in updated_state.branches[updated_state.current_branch_id].topic_contexts.values()
            ) / max(len(updated_state.branches[updated_state.current_branch_id].topic_contexts), 1)
        }
    }

    return LLMChatResponse(
        message=response_message,
        agent_type=request.agent_type,
        metadata=metadata
    )


async def _handle_standard_chat(request: LLMChatRequest, llm) -> LLMChatResponse:
    """Handle standard chat for non-worldbuilding agents."""

    # Build system prompt based on agent type and context
    system_prompt = _build_agent_system_prompt(
        request.agent_type,
        request.compose_context,
        request.system_prompts
    )

    # Build conversation context
    context = _build_conversation_context(request.messages, request.compose_context)

    # Prepare messages for LLM
    llm_messages = [{"role": "system", "content": system_prompt}]

    # Add context as first user message if available
    if context:
        llm_messages.append({"role": "user", "content": f"Context:\n{context}"})
        llm_messages.append({"role": "assistant", "content": "I understand the context. How can I help you?"})

    # Add conversation history
    for msg in request.messages:
        llm_messages.append({
            "role": msg.role,
            "content": msg.content
        })

    # Get LLM response
    response_text = llm.chat_completion(
        llm_messages,
        max_tokens=request.max_tokens,
        temperature=request.temperature
    )

    # Create response message
    response_message = ConversationMessage(
        role="assistant",
        content=response_text.strip(),
        timestamp=datetime.now(UTC).isoformat()
    )

    return LLMChatResponse(
        message=response_message,
        agent_type=request.agent_type,
        metadata={
            "generatedAt": datetime.now(UTC).isoformat(),
            "phase": request.compose_context.current_phase if request.compose_context else None,
            "conversationLength": len(request.messages),
            "contextProvided": bool(context)
        }
    )


def _build_worldbuilding_conversation_context(state) -> str:
    """Build conversation context specific to worldbuilding."""
    context_parts = []

    current_branch = state.branches[state.current_branch_id]

    # Add current topic context
    if state.current_topic in current_branch.topic_contexts:
        topic_context = current_branch.topic_contexts[state.current_topic]
        if topic_context.accumulated_content:
            context_parts.append(f"Current {state.current_topic} context:")
            context_parts.append(topic_context.accumulated_content[:500])  # Limit length

    # Add key elements from active topics
    active_elements = []
    for topic, context in current_branch.topic_contexts.items():
        if context.key_elements:
            active_elements.extend([f"{topic}: {elem}" for elem in context.key_elements[:3]])

    if active_elements:
        context_parts.append("Key worldbuilding elements:")
        context_parts.extend(active_elements[:10])  # Limit to top 10

    # Add conversation flow context
    if state.conversation_history:
        context_parts.append(f"Topic flow: {' -> '.join(state.conversation_history[-3:])}")

    return "\n".join(context_parts)
