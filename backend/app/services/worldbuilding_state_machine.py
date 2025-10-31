"""
Conversation state machine for worldbuilding conversations.
Manages conversation flow, topic transitions, and state persistence.
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, UTC
from app.models.worldbuilding_models import (
    WorldbuildingConversationState, ConversationState, WorldbuildingTopic,
    ConversationBranch, TopicContext, TopicTransition, WorldbuildingChatContext
)
from app.models.generation_models import ConversationMessage
from app.services.worldbuilding_persistence import WorldbuildingPersistenceService


class WorldbuildingStateMachine:
    """Manages worldbuilding conversation state and flow transitions."""

    def __init__(self, persistence_service: Optional[WorldbuildingPersistenceService] = None):
        self.state_transitions = self._initialize_state_transitions()
        self.topic_completion_thresholds = self._initialize_completion_thresholds()
        self.conversation_states: Dict[str, WorldbuildingConversationState] = {}
        self.persistence = persistence_service or WorldbuildingPersistenceService()

    def _initialize_state_transitions(self) -> Dict[ConversationState, List[ConversationState]]:
        """Initialize valid state transitions."""
        return {
            'initial': ['exploring', 'deepening'],
            'exploring': ['deepening', 'branching', 'transitioning', 'summarizing'],
            'deepening': ['exploring', 'branching', 'transitioning', 'summarizing'],
            'branching': ['exploring', 'deepening', 'transitioning'],
            'transitioning': ['exploring', 'deepening', 'branching'],
            'summarizing': ['exploring', 'deepening', 'transitioning', 'initial']
        }

    def _initialize_completion_thresholds(self) -> Dict[str, float]:
        """Initialize thresholds for determining topic completion."""
        return {
            'content_length': 500,  # Minimum characters for basic completion
            'key_elements': 3,      # Minimum key elements identified
            'questions_asked': 2,   # Minimum questions explored
            'completeness_score': 0.6  # Minimum completeness score
        }

    def get_or_create_conversation_state(self, story_id: str) -> WorldbuildingConversationState:
        """Get existing conversation state or create a new one."""
        if story_id not in self.conversation_states:
            # Try to load from persistence first
            persisted_state = self.persistence.load_conversation_state(story_id)
            if persisted_state:
                self.conversation_states[story_id] = persisted_state
            else:
                self.conversation_states[story_id] = self._create_initial_state(story_id)
        return self.conversation_states[story_id]

    def _create_initial_state(self, story_id: str) -> WorldbuildingConversationState:
        """Create initial conversation state for a story."""
        now = datetime.now(UTC).isoformat()

        # Create main branch
        main_branch = ConversationBranch(
            branch_id='main',
            branch_name='main',
            created_at=now,
            messages=[],
            current_topic='general',
            topic_contexts={}
        )

        return WorldbuildingConversationState(
            story_id=story_id,
            current_state='initial',
            current_branch_id='main',
            current_topic='general',
            branches={'main': main_branch},
            accumulated_worldbuilding="",
            topic_priorities={},
            conversation_history=[],
            suggested_topics=[],
            pending_questions=[],
            created_at=now,
            last_updated=now,
            total_messages=0
        )

    def process_message(
        self,
        story_id: str,
        message: ConversationMessage,
        topic_classification: Optional[Dict] = None
    ) -> Tuple[WorldbuildingConversationState, List[str]]:
        """Process a new message and update conversation state."""

        state = self.get_or_create_conversation_state(story_id)
        actions_taken = []

        # Add message to current branch
        current_branch = state.branches[state.current_branch_id]
        current_branch.messages.append(message)
        state.total_messages += 1

        # Update topic context if classification provided
        if topic_classification and message.role == 'user':
            new_topic = topic_classification.get('primary_topic', state.current_topic)

            # Handle topic transition
            if new_topic != state.current_topic:
                transition_result = self._handle_topic_transition(
                    state, state.current_topic, new_topic, message.content
                )
                actions_taken.extend(transition_result)

        # Update conversation state based on message content and context
        new_state = self._determine_conversation_state(state, message)
        if new_state != state.current_state:
            state.current_state = new_state
            actions_taken.append(f"Transitioned to {new_state} state")

        # Update topic context
        self._update_topic_context(state, message, topic_classification)

        # Update metadata
        state.last_updated = datetime.now(UTC).isoformat()

        # Persist the updated state
        self.persistence.save_conversation_state(state)

        return state, actions_taken

    def _handle_topic_transition(
        self,
        state: WorldbuildingConversationState,
        from_topic: WorldbuildingTopic,
        to_topic: WorldbuildingTopic,
        trigger_message: str
    ) -> List[str]:
        """Handle transition between worldbuilding topics."""
        actions = []

        # Record the transition
        transition = TopicTransition(
            from_topic=from_topic,
            to_topic=to_topic,
            trigger_message=trigger_message,
            confidence=0.8,  # Could be calculated based on classification confidence
            suggested_questions=[]
        )

        # Update conversation history
        state.conversation_history.append(f"{from_topic} -> {to_topic}")

        # Update current topic
        state.current_topic = to_topic
        current_branch = state.branches[state.current_branch_id]
        current_branch.current_topic = to_topic

        # Ensure topic context exists
        if to_topic not in current_branch.topic_contexts:
            current_branch.topic_contexts[to_topic] = TopicContext(
                topic=to_topic,
                accumulated_content="",
                key_elements=[],
                questions_asked=[],
                last_updated=datetime.now(UTC).isoformat(),
                completeness_score=0.0
            )

        actions.append(f"Transitioned from {from_topic} to {to_topic}")

        # Update conversation state to transitioning
        if state.current_state not in ['transitioning']:
            state.current_state = 'transitioning'
            actions.append("Entered transitioning state")

        return actions

    def _determine_conversation_state(
        self,
        state: WorldbuildingConversationState,
        message: ConversationMessage
    ) -> ConversationState:
        """Determine the appropriate conversation state based on context."""

        current_branch = state.branches[state.current_branch_id]
        message_count = len(current_branch.messages)

        # Initial state: First few messages
        if message_count <= 2:
            return 'initial'

        # Get current topic context
        current_topic_context = current_branch.topic_contexts.get(
            state.current_topic,
            TopicContext(topic=state.current_topic)
        )

        # Determine state based on conversation patterns and topic depth
        if message.role == 'user':
            message_lower = message.content.lower()

            # Branching: User wants to explore alternatives or create branches
            if any(phrase in message_lower for phrase in [
                'what if', 'alternatively', 'on the other hand', 'different approach'
            ]):
                return 'branching'

            # Summarizing: User asks for summary or overview
            if any(phrase in message_lower for phrase in [
                'summarize', 'overview', 'so far', 'recap', 'summary'
            ]):
                return 'summarizing'

            # Transitioning: User changes topics explicitly
            if any(phrase in message_lower for phrase in [
                'moving on', 'next topic', 'what about', 'tell me about'
            ]):
                return 'transitioning'

            # Deepening: User asks detailed questions about current topic
            if any(phrase in message_lower for phrase in [
                'more detail', 'specifically', 'how exactly', 'can you elaborate'
            ]):
                return 'deepening'

        # Default state based on topic completeness
        if current_topic_context.completeness_score < 0.3:
            return 'exploring'  # Still exploring basics
        elif current_topic_context.completeness_score < 0.7:
            return 'deepening'  # Adding depth and detail
        else:
            return 'exploring'  # Ready to explore new areas

    def _update_topic_context(
        self,
        state: WorldbuildingConversationState,
        message: ConversationMessage,
        topic_classification: Optional[Dict] = None
    ) -> None:
        """Update topic context based on message content."""

        current_branch = state.branches[state.current_branch_id]
        current_topic = state.current_topic

        # Ensure topic context exists
        if current_topic not in current_branch.topic_contexts:
            current_branch.topic_contexts[current_topic] = TopicContext(
                topic=current_topic,
                accumulated_content="",
                key_elements=[],
                questions_asked=[],
                last_updated=datetime.now(UTC).isoformat(),
                completeness_score=0.0
            )

        topic_context = current_branch.topic_contexts[current_topic]

        # Update accumulated content
        if message.role == 'assistant':
            topic_context.accumulated_content += f"\n{message.content}"

        # Extract key elements from user messages
        if message.role == 'user':
            key_elements = self._extract_key_elements(message.content, current_topic)
            topic_context.key_elements.extend(key_elements)
            topic_context.key_elements = list(set(topic_context.key_elements))  # Remove duplicates

            # Track questions asked
            if '?' in message.content:
                questions = [q.strip() for q in message.content.split('?') if q.strip()]
                topic_context.questions_asked.extend(questions)

        # Update completeness score
        topic_context.completeness_score = self._calculate_completeness_score(topic_context)
        topic_context.last_updated = datetime.now(UTC).isoformat()

    def _extract_key_elements(self, message: str, topic: WorldbuildingTopic) -> List[str]:
        """Extract key elements from a message based on the topic."""
        elements = []
        message_lower = message.lower()

        # Topic-specific keyword extraction
        topic_keywords = {
            'geography': ['mountain', 'river', 'forest', 'desert', 'city', 'climate', 'region'],
            'culture': ['tradition', 'custom', 'belief', 'value', 'society', 'people', 'art'],
            'magic_system': ['magic', 'spell', 'power', 'ability', 'wizard', 'mage', 'energy'],
            'politics': ['government', 'king', 'ruler', 'law', 'power', 'authority', 'council'],
            'history': ['history', 'past', 'ancient', 'war', 'event', 'legend', 'myth'],
            'technology': ['technology', 'tool', 'weapon', 'invention', 'craft', 'machine'],
            'economy': ['trade', 'merchant', 'money', 'wealth', 'market', 'goods', 'commerce'],
            'religion': ['god', 'deity', 'faith', 'worship', 'temple', 'priest', 'belief'],
            'characters': ['character', 'person', 'hero', 'villain', 'leader', 'personality'],
            'languages': ['language', 'tongue', 'dialect', 'writing', 'communication', 'script'],
            'conflicts': ['war', 'battle', 'conflict', 'enemy', 'fight', 'struggle', 'tension'],
            'organizations': ['guild', 'order', 'group', 'organization', 'society', 'institution']
        }

        keywords = topic_keywords.get(topic, [])
        for keyword in keywords:
            if keyword in message_lower:
                elements.append(keyword)

        # Extract proper nouns (capitalized words)
        import re
        proper_nouns = re.findall(r'\b[A-Z][a-z]+\b', message)
        elements.extend(proper_nouns[:3])  # Limit to avoid noise

        return elements[:5]  # Return top 5 elements

    def _calculate_completeness_score(self, topic_context: TopicContext) -> float:
        """Calculate completeness score for a topic context."""
        thresholds = self.topic_completion_thresholds

        # Content length score (0-1)
        content_score = min(len(topic_context.accumulated_content) / thresholds['content_length'], 1.0)

        # Key elements score (0-1)
        elements_score = min(len(topic_context.key_elements) / thresholds['key_elements'], 1.0)

        # Questions asked score (0-1)
        questions_score = min(len(topic_context.questions_asked) / thresholds['questions_asked'], 1.0)

        # Weighted average
        return (content_score * 0.4 + elements_score * 0.3 + questions_score * 0.3)

    def create_branch(
        self,
        story_id: str,
        branch_name: str,
        parent_branch_id: str = None
    ) -> Tuple[str, List[str]]:
        """Create a new conversation branch."""

        state = self.get_or_create_conversation_state(story_id)
        actions = []

        # Generate unique branch ID
        branch_id = f"branch_{len(state.branches)}_{int(datetime.now(UTC).timestamp())}"

        # Get parent branch or use current
        parent_id = parent_branch_id or state.current_branch_id
        parent_branch = state.branches.get(parent_id)

        if not parent_branch:
            raise ValueError(f"Parent branch {parent_id} not found")

        # Create new branch
        new_branch = ConversationBranch(
            branch_id=branch_id,
            parent_branch_id=parent_id,
            branch_name=branch_name,
            created_at=datetime.now(UTC).isoformat(),
            messages=parent_branch.messages.copy(),  # Copy parent messages
            current_topic=parent_branch.current_topic,
            topic_contexts=parent_branch.topic_contexts.copy()  # Copy topic contexts
        )

        state.branches[branch_id] = new_branch
        state.current_branch_id = branch_id
        state.current_state = 'branching'

        actions.append(f"Created branch '{branch_name}' from {parent_id}")
        actions.append(f"Switched to branch {branch_id}")

        return branch_id, actions

    def switch_branch(self, story_id: str, branch_id: str) -> List[str]:
        """Switch to a different conversation branch."""

        state = self.get_or_create_conversation_state(story_id)
        actions = []

        if branch_id not in state.branches:
            raise ValueError(f"Branch {branch_id} not found")

        old_branch_id = state.current_branch_id
        state.current_branch_id = branch_id

        # Update current topic and state based on new branch
        new_branch = state.branches[branch_id]
        state.current_topic = new_branch.current_topic

        actions.append(f"Switched from {old_branch_id} to {branch_id}")

        return actions

    def get_conversation_summary(self, story_id: str) -> Dict[str, any]:
        """Get a summary of the conversation state."""

        state = self.get_or_create_conversation_state(story_id)
        current_branch = state.branches[state.current_branch_id]

        # Calculate overall progress
        topic_scores = [
            context.completeness_score
            for context in current_branch.topic_contexts.values()
        ]
        overall_progress = sum(topic_scores) / len(topic_scores) if topic_scores else 0.0

        # Get active topics
        active_topics = [
            topic for topic, context in current_branch.topic_contexts.items()
            if context.completeness_score > 0.1
        ]

        return {
            'story_id': story_id,
            'current_state': state.current_state,
            'current_topic': state.current_topic,
            'current_branch': state.current_branch_id,
            'total_messages': state.total_messages,
            'active_topics': active_topics,
            'overall_progress': overall_progress,
            'topic_progress': {
                topic: context.completeness_score
                for topic, context in current_branch.topic_contexts.items()
            },
            'conversation_history': state.conversation_history,
            'branches': list(state.branches.keys()),
            'last_updated': state.last_updated
        }

    def suggest_next_actions(self, story_id: str) -> List[str]:
        """Suggest next actions based on current conversation state."""

        state = self.get_or_create_conversation_state(story_id)
        current_branch = state.branches[state.current_branch_id]
        suggestions = []

        # Analyze current state and suggest actions
        if state.current_state == 'initial':
            suggestions.append("Start exploring basic worldbuilding topics like geography or culture")

        elif state.current_state == 'exploring':
            current_context = current_branch.topic_contexts.get(state.current_topic)
            if current_context and current_context.completeness_score > 0.5:
                suggestions.append(f"Consider deepening your exploration of {state.current_topic}")
                suggestions.append("Or transition to a related topic for broader coverage")
            else:
                suggestions.append(f"Continue exploring {state.current_topic} with more specific questions")

        elif state.current_state == 'deepening':
            suggestions.append("Ask for specific examples or detailed descriptions")
            suggestions.append("Explore consequences and implications of current elements")

        elif state.current_state == 'transitioning':
            unexplored_topics = [
                topic for topic in ['geography', 'culture', 'magic_system', 'politics', 'history']
                if topic not in current_branch.topic_contexts or
                current_branch.topic_contexts[topic].completeness_score < 0.3
            ]
            if unexplored_topics:
                suggestions.append(f"Consider exploring: {', '.join(unexplored_topics[:3])}")

        elif state.current_state == 'summarizing':
            suggestions.append("Review and consolidate your worldbuilding so far")
            suggestions.append("Identify connections between different aspects of your world")

        # Add general suggestions based on progress
        if len(current_branch.topic_contexts) >= 3:
            suggestions.append("Consider how different aspects of your world connect and influence each other")

        return suggestions[:3]  # Return top 3 suggestions
