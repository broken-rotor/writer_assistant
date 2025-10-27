"""
LLM Chat endpoint for direct conversations with AI agents.
Separate from RAG chat functionality.
"""
from fastapi import APIRouter, HTTPException
from app.models.chat_models import LLMChatRequest, LLMChatResponse, ConversationMessage
from app.services.llm_inference import get_llm
from datetime import datetime, UTC
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def _build_agent_system_prompt(agent_type: str, compose_context=None, system_prompts=None) -> str:
    """Build system prompt based on agent type and context."""
    base_prompts = {
        'writer': "You are a skilled writer assistant helping with story creation. Provide creative, engaging responses that help develop compelling narratives.",
        'character': "You are a character development specialist. Help create authentic, well-rounded characters with realistic motivations and behaviors.",
        'editor': "You are an experienced editor providing constructive feedback on writing. Focus on narrative flow, consistency, and overall story quality.",
        'worldbuilding': "You are a worldbuilding specialist helping create rich, immersive fictional worlds. Guide users through developing comprehensive world details including geography, cultures, magic systems, politics, history, and societies. Ask thoughtful follow-up questions to help expand and deepen their world creation."
    }
    
    prompt = base_prompts.get(agent_type, base_prompts['writer'])
    
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
    """
    llm = get_llm()
    if not llm:
        raise HTTPException(status_code=503, detail="LLM not initialized. Start server with --model-path")
    
    try:
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
        
    except Exception as e:
        logger.error(f"Error in llm_chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in LLM chat: {str(e)}")
