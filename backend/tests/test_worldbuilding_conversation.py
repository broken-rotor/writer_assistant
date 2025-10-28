"""
Unit tests for worldbuilding conversation engine components.
Tests the integration of all worldbuilding services.
"""
import pytest
from datetime import datetime, UTC
from app.models.worldbuilding_models import (
    WorldbuildingTopic, ConversationState, TopicContext, WorldbuildingChatContext
)
from app.models.generation_models import ConversationMessage
from app.services.worldbuilding_classifier import WorldbuildingTopicClassifier
from app.services.worldbuilding_prompts import WorldbuildingPromptService
from app.services.worldbuilding_followup import WorldbuildingFollowupGenerator
from app.services.worldbuilding_state_machine import WorldbuildingStateMachine
from app.services.worldbuilding_persistence import WorldbuildingPersistenceService


class TestWorldbuildingConversationEngine:
    """Test the complete worldbuilding conversation engine."""

    @pytest.fixture(autouse=True)
    def setup(self, temp_persistence_service):
        """Set up test fixtures with temporary storage."""
        self.classifier = WorldbuildingTopicClassifier()
        self.prompts = WorldbuildingPromptService()
        self.followup = WorldbuildingFollowupGenerator()
        self.persistence = temp_persistence_service
        self.state_machine = WorldbuildingStateMachine(self.persistence)

        # Test data
        self.test_story_id = "test_story_123"
        self.test_messages = [
            ConversationMessage(
                role="user",
                content="Tell me about the geography of my fantasy world. There are mountains in the north.",
                timestamp=datetime.now(UTC).isoformat()
            ),
            ConversationMessage(
                role="assistant",
                content="That's a great start! Mountains in the north can create interesting climate patterns. What kind of mountains are they - tall and snow-capped, or rolling hills?",
                timestamp=datetime.now(UTC).isoformat()
            ),
            ConversationMessage(
                role="user",
                content="They're tall snow-capped peaks called the Frostspire Mountains. They're home to ancient dragons.",
                timestamp=datetime.now(UTC).isoformat()
            )
        ]
    
    def test_topic_classification_integration(self):
        """Test topic classification with realistic messages."""
        # Test geography classification
        result = self.classifier.classify_message(
            "The kingdom is surrounded by vast deserts to the south and dense forests to the east.",
            'general'
        )
        
        assert result.primary_topic == 'geography'
        assert result.confidence > 0.5
        assert 'desert' in result.keywords_found or 'forest' in result.keywords_found
        
        # Test magic system classification
        result = self.classifier.classify_message(
            "Magic users must channel energy through crystal focuses to cast spells.",
            'general'
        )
        
        assert result.primary_topic == 'magic_system'
        assert result.confidence > 0.5
        assert 'magic' in result.keywords_found or 'spell' in result.keywords_found
    
    def test_prompt_template_generation(self):
        """Test worldbuilding prompt template generation."""
        # Test geography prompt
        template = self.prompts.get_prompt_template('geography')
        assert template.topic == 'geography'
        assert 'geography' in template.system_prompt.lower()
        assert len(template.followup_prompts) > 0
        assert len(template.key_questions) > 0
        
        # Test contextual prompt building
        contextual_prompt = self.prompts.build_contextual_prompt(
            'culture',
            conversation_context="We've discussed mountain-dwelling people",
            story_context="Fantasy world with dragons"
        )
        
        assert 'culture' in contextual_prompt.lower()
        assert len(contextual_prompt) > 100  # Should be substantial
    
    def test_followup_question_generation(self):
        """Test context-aware follow-up question generation."""
        # Create test context
        context = WorldbuildingChatContext(
            story_id=self.test_story_id,
            current_topic='geography',
            conversation_state='exploring',
            active_topics=['geography'],
            topic_contexts={
                'geography': TopicContext(
                    topic='geography',
                    accumulated_content="Mountains in the north called Frostspire Mountains with dragons",
                    key_elements=['mountains', 'dragons', 'north'],
                    questions_asked=['What kind of mountains?'],
                    completeness_score=0.3
                )
            },
            recent_messages=self.test_messages,
            story_context={'genre': 'fantasy'}
        )
        
        questions = self.followup.generate_followup_questions(context, self.test_messages, max_questions=3)
        
        assert len(questions) > 0
        assert len(questions) <= 3
        
        # Check question quality
        for question in questions:
            assert len(question.question) > 10  # Substantial questions
            assert question.priority >= 0.0 and question.priority <= 1.0
            assert question.topic in ['geography', 'general', 'culture', 'magic_system', 'politics', 'history']
    
    def test_state_machine_conversation_flow(self):
        """Test conversation state machine with realistic flow."""
        # Start conversation
        state = self.state_machine.get_or_create_conversation_state(self.test_story_id)
        assert state.current_state == 'initial'
        assert state.current_topic == 'general'
        
        # Process first user message
        user_message = self.test_messages[0]
        classification = {
            'primary_topic': 'geography',
            'confidence': 0.8,
            'secondary_topics': [],
            'keywords_found': ['mountains', 'north']
        }
        
        updated_state, actions = self.state_machine.process_message(
            self.test_story_id, user_message, classification
        )
        
        assert updated_state.current_topic == 'geography'
        assert updated_state.total_messages == 1
        assert len(actions) > 0
        
        # Process assistant response
        assistant_message = self.test_messages[1]
        updated_state, actions = self.state_machine.process_message(
            self.test_story_id, assistant_message
        )
        
        assert updated_state.total_messages == 2
        
        # Check topic context was created and updated
        current_branch = updated_state.branches[updated_state.current_branch_id]
        assert 'geography' in current_branch.topic_contexts
        
        geography_context = current_branch.topic_contexts['geography']
        assert len(geography_context.key_elements) > 0
        assert geography_context.completeness_score > 0.0
    
    def test_conversation_branching(self):
        """Test conversation branching functionality."""
        # Create initial state with some content
        state = self.state_machine.get_or_create_conversation_state(self.test_story_id)
        
        # Add some messages to main branch
        for message in self.test_messages:
            self.state_machine.process_message(self.test_story_id, message)
        
        # Create a branch
        branch_id, actions = self.state_machine.create_branch(
            self.test_story_id, "alternative_geography", "main"
        )
        
        assert branch_id != "main"
        assert len(actions) > 0
        
        # Verify branch was created
        updated_state = self.state_machine.get_or_create_conversation_state(self.test_story_id)
        assert branch_id in updated_state.branches
        assert updated_state.current_branch_id == branch_id
        
        # Verify branch has copied content from parent
        new_branch = updated_state.branches[branch_id]
        main_branch = updated_state.branches["main"]
        assert len(new_branch.messages) == len(main_branch.messages)
    
    def test_conversation_summary_generation(self):
        """Test conversation summary generation."""
        # Add some conversation content
        for message in self.test_messages:
            classification = None
            if message.role == 'user':
                classification = {
                    'primary_topic': 'geography',
                    'confidence': 0.7,
                    'secondary_topics': [],
                    'keywords_found': ['mountains']
                }
            self.state_machine.process_message(self.test_story_id, message, classification)
        
        # Generate summary
        summary = self.state_machine.get_conversation_summary(self.test_story_id)
        
        assert summary['story_id'] == self.test_story_id
        assert summary['total_messages'] == len(self.test_messages)
        assert summary['current_topic'] == 'geography'
        assert 'active_topics' in summary
        assert 'overall_progress' in summary
        assert summary['overall_progress'] >= 0.0 and summary['overall_progress'] <= 1.0
    
    def test_next_action_suggestions(self):
        """Test next action suggestion generation."""
        # Create conversation with some progress
        for message in self.test_messages:
            classification = None
            if message.role == 'user':
                classification = {
                    'primary_topic': 'geography',
                    'confidence': 0.7,
                    'secondary_topics': [],
                    'keywords_found': ['mountains']
                }
            self.state_machine.process_message(self.test_story_id, message, classification)
        
        # Get suggestions
        suggestions = self.state_machine.suggest_next_actions(self.test_story_id)
        
        assert len(suggestions) > 0
        assert len(suggestions) <= 3
        
        # Check suggestion quality
        for suggestion in suggestions:
            assert len(suggestion) > 10  # Substantial suggestions
            assert isinstance(suggestion, str)
    
    def test_error_handling(self):
        """Test error handling in various scenarios."""
        # Test with invalid story ID
        try:
            state = self.state_machine.get_or_create_conversation_state("")
            # Should not raise exception, should create valid state
            assert state.story_id == ""
        except Exception as e:
            pytest.fail(f"Should handle empty story ID gracefully: {e}")
        
        # Test with malformed message
        try:
            malformed_message = ConversationMessage(
                role="invalid_role",  # Invalid role
                content="",  # Empty content
                timestamp="invalid_timestamp"  # Invalid timestamp
            )
            # Should not crash the system
            self.state_machine.process_message(self.test_story_id, malformed_message)
        except Exception as e:
            # Should handle gracefully or raise specific exception
            assert "role" in str(e).lower() or "timestamp" in str(e).lower()
        
        # Test classification with empty message
        result = self.classifier.classify_message("", 'general')
        assert result.primary_topic == 'general'  # Should default gracefully
        assert result.confidence <= 0.5  # Should have low confidence
    
    def test_persistence_integration(self):
        """Test persistence service integration."""
        # Create conversation state
        for message in self.test_messages:
            classification = None
            if message.role == 'user':
                classification = {
                    'primary_topic': 'geography',
                    'confidence': 0.7,
                    'secondary_topics': [],
                    'keywords_found': ['mountains']
                }
            self.state_machine.process_message(self.test_story_id, message, classification)
        
        # Get current state
        original_state = self.state_machine.get_or_create_conversation_state(self.test_story_id)
        
        # Clear in-memory state
        self.state_machine.conversation_states.clear()
        
        # Load state again (should load from persistence)
        loaded_state = self.state_machine.get_or_create_conversation_state(self.test_story_id)
        
        # Verify state was persisted and loaded correctly
        assert loaded_state.story_id == original_state.story_id
        assert loaded_state.total_messages == original_state.total_messages
        assert loaded_state.current_topic == original_state.current_topic
        assert len(loaded_state.branches) == len(original_state.branches)
    
    def test_complete_conversation_flow(self):
        """Test a complete conversation flow from start to finish."""
        # Simulate a realistic worldbuilding conversation
        conversation_flow = [
            ("user", "I want to create a fantasy world with floating islands.", "geography"),
            ("assistant", "Floating islands are fascinating! What keeps them in the air?", None),
            ("user", "Ancient magic crystals embedded in the rock.", "magic_system"),
            ("assistant", "Interesting! How do people travel between the islands?", None),
            ("user", "They use flying ships powered by smaller crystals.", "technology"),
            ("assistant", "What kind of society has developed on these islands?", None),
            ("user", "Each island is ruled by a crystal keeper who controls the magic.", "politics")
        ]
        
        story_id = "complete_flow_test"
        
        for role, content, expected_topic in conversation_flow:
            message = ConversationMessage(
                role=role,
                content=content,
                timestamp=datetime.now(UTC).isoformat()
            )
            
            classification = None
            if role == "user" and expected_topic:
                # Classify user messages
                classification_result = self.classifier.classify_message(content, 'general')
                classification = {
                    'primary_topic': classification_result.primary_topic,
                    'confidence': classification_result.confidence,
                    'secondary_topics': classification_result.secondary_topics,
                    'keywords_found': classification_result.keywords_found
                }
            
            # Process message
            state, actions = self.state_machine.process_message(story_id, message, classification)
            
            # Verify state progression
            assert state.total_messages > 0
            if expected_topic:
                # Should have transitioned to expected topic or be exploring it
                current_branch = state.branches[state.current_branch_id]
                assert expected_topic in current_branch.topic_contexts or state.current_topic == expected_topic
        
        # Verify final state
        final_state = self.state_machine.get_or_create_conversation_state(story_id)
        current_branch = final_state.branches[final_state.current_branch_id]
        
        # Should have explored multiple topics
        assert len(current_branch.topic_contexts) >= 3
        
        # Should have accumulated substantial content
        total_content_length = sum(
            len(ctx.accumulated_content) for ctx in current_branch.topic_contexts.values()
        )
        assert total_content_length > 100
        
        # Should have reasonable overall progress
        summary = self.state_machine.get_conversation_summary(story_id)
        assert summary['overall_progress'] > 0.1
        
        # Generate final follow-up questions
        wb_context = WorldbuildingChatContext(
            story_id=story_id,
            current_topic=final_state.current_topic,
            conversation_state=final_state.current_state,
            active_topics=list(current_branch.topic_contexts.keys()),
            topic_contexts=current_branch.topic_contexts,
            recent_messages=[],
            story_context={'genre': 'fantasy'}
        )
        
        final_questions = self.followup.generate_followup_questions(wb_context, [], max_questions=5)
        assert len(final_questions) > 0
        
        # Questions should be relevant to developed topics
        question_topics = [q.topic for q in final_questions]
        developed_topics = list(current_branch.topic_contexts.keys())
        
        # At least some questions should relate to developed topics
        relevant_questions = [q for q in question_topics if q in developed_topics or q == 'general']
        assert len(relevant_questions) > 0
    
    # teardown is no longer needed as tmp_path is automatically cleaned up by pytest
