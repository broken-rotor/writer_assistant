"""
Pydantic models for worldbuilding conversation engine.
Handles conversation state, topic classification, and context management.
"""
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel
from datetime import datetime
from .generation_models import ConversationMessage


# Worldbuilding topic categories
WorldbuildingTopic = Literal[
    'geography', 'culture', 'magic_system', 'politics', 'history', 
    'technology', 'economy', 'religion', 'characters', 'languages',
    'conflicts', 'organizations', 'general'
]

# Conversation flow states
ConversationState = Literal[
    'initial', 'exploring', 'deepening', 'branching', 'summarizing', 'transitioning'
]


class TopicContext(BaseModel):
    """Context for a specific worldbuilding topic."""
    topic: WorldbuildingTopic
    accumulated_content: str = ""
    key_elements: List[str] = []
    questions_asked: List[str] = []
    last_updated: Optional[str] = None
    completeness_score: float = 0.0  # 0-1 scale


class ConversationBranch(BaseModel):
    """Represents a conversation branch with its own context."""
    branch_id: str
    parent_branch_id: Optional[str] = None
    branch_name: str = "main"
    created_at: str
    messages: List[ConversationMessage] = []
    current_topic: WorldbuildingTopic = 'general'
    topic_contexts: Dict[WorldbuildingTopic, TopicContext] = {}


class WorldbuildingConversationState(BaseModel):
    """Complete state of a worldbuilding conversation."""
    story_id: str
    current_state: ConversationState = 'initial'
    current_branch_id: str = 'main'
    current_topic: WorldbuildingTopic = 'general'
    
    # Conversation branches
    branches: Dict[str, ConversationBranch] = {}
    
    # Global worldbuilding context
    accumulated_worldbuilding: str = ""
    topic_priorities: Dict[WorldbuildingTopic, float] = {}
    
    # Conversation flow
    conversation_history: List[str] = []  # Topic transition history
    suggested_topics: List[WorldbuildingTopic] = []
    pending_questions: List[str] = []
    
    # Metadata
    created_at: str
    last_updated: str
    total_messages: int = 0


class TopicTransition(BaseModel):
    """Represents a transition between worldbuilding topics."""
    from_topic: WorldbuildingTopic
    to_topic: WorldbuildingTopic
    trigger_message: str
    confidence: float  # 0-1 scale
    suggested_questions: List[str] = []


class WorldbuildingChatContext(BaseModel):
    """Extended chat context specifically for worldbuilding conversations."""
    story_id: str
    current_topic: WorldbuildingTopic = 'general'
    conversation_state: ConversationState = 'initial'
    
    # Topic-specific context
    active_topics: List[WorldbuildingTopic] = []
    topic_contexts: Dict[WorldbuildingTopic, TopicContext] = {}
    
    # Conversation flow
    recent_messages: List[ConversationMessage] = []
    suggested_followups: List[str] = []
    topic_transitions: List[TopicTransition] = []
    
    # Integration with existing system
    story_context: Dict[str, Any] = {}
    accumulated_worldbuilding: str = ""


class FollowupQuestion(BaseModel):
    """A generated follow-up question for worldbuilding."""
    question: str
    topic: WorldbuildingTopic
    priority: float  # 0-1 scale
    context_dependent: bool = False
    reasoning: str = ""


class TopicClassificationResult(BaseModel):
    """Result of topic classification for a message."""
    primary_topic: WorldbuildingTopic
    confidence: float  # 0-1 scale
    secondary_topics: List[WorldbuildingTopic] = []
    keywords_found: List[str] = []
    suggested_transition: Optional[TopicTransition] = None


class WorldbuildingPromptTemplate(BaseModel):
    """Template for worldbuilding prompts by topic."""
    topic: WorldbuildingTopic
    system_prompt: str
    context_prompt: str
    followup_prompts: List[str] = []
    key_questions: List[str] = []
    completion_criteria: List[str] = []


class WorldbuildingResponse(BaseModel):
    """Enhanced response for worldbuilding conversations."""
    message: ConversationMessage
    topic_classification: TopicClassificationResult
    suggested_followups: List[FollowupQuestion] = []
    topic_context_update: Optional[TopicContext] = None
    conversation_state_update: Optional[ConversationState] = None
    worldbuilding_summary: str = ""
    metadata: Dict[str, Any] = {}
