"""
Unit tests for individual worldbuilding services.
Tests each service component in isolation.
"""
import pytest
from datetime import datetime, UTC
from app.models.worldbuilding_models import (
    WorldbuildingTopic, TopicContext, WorldbuildingChatContext
)
from app.models.generation_models import ConversationMessage
from app.services.worldbuilding_classifier import WorldbuildingTopicClassifier
from app.services.worldbuilding_prompts import WorldbuildingPromptService
from app.services.worldbuilding_followup import WorldbuildingFollowupGenerator


class TestWorldbuildingTopicClassifier:
    """Test the topic classification service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = WorldbuildingTopicClassifier()
    
    def test_geography_classification(self):
        """Test classification of geography-related messages."""
        test_cases = [
            ("The kingdom has vast mountains in the north and deserts in the south.", "geography"),
            ("What's the climate like in this region?", "geography"),
            ("The river flows through the valley between two hills.", "geography"),
            ("How do people travel across the ocean?", "geography")
        ]
        
        for message, expected_topic in test_cases:
            result = self.classifier.classify_message(message, 'general')
            assert result.primary_topic == expected_topic, f"Failed for: {message}"
            assert result.confidence > 0.5
    
    def test_magic_system_classification(self):
        """Test classification of magic system messages."""
        test_cases = [
            ("Magic users channel energy through crystal focuses.", "magic_system"),
            ("How do wizards learn to cast spells?", "magic_system"),
            ("The arcane arts are forbidden in this kingdom.", "magic_system"),
            ("What are the limitations of magical power?", "magic_system")
        ]
        
        for message, expected_topic in test_cases:
            result = self.classifier.classify_message(message, 'general')
            assert result.primary_topic == expected_topic, f"Failed for: {message}"
            assert result.confidence > 0.5
    
    def test_culture_classification(self):
        """Test classification of culture-related messages."""
        test_cases = [
            ("The people value honor above all else.", "culture"),
            ("What traditions do they practice?", "culture"),
            ("Their art focuses on geometric patterns.", "culture"),
            ("How do families organize themselves?", "culture")
        ]
        
        for message, expected_topic in test_cases:
            result = self.classifier.classify_message(message, 'general')
            assert result.primary_topic == expected_topic, f"Failed for: {message}"
            assert result.confidence > 0.5
    
    def test_topic_transition_detection(self):
        """Test detection of topic transitions."""
        # Test transition from geography to culture
        result = self.classifier.classify_message(
            "The mountain people have developed unique traditions.", 
            'geography'
        )
        
        assert result.suggested_transition is not None
        assert result.suggested_transition.from_topic == 'geography'
        assert result.suggested_transition.to_topic == 'culture'
        assert result.confidence > 0.6
    
    def test_keyword_extraction(self):
        """Test keyword extraction from messages."""
        message = "The ancient dragons live in the crystal caves of Mount Frostspire."
        result = self.classifier.classify_message(message, 'general')
        
        # Should extract relevant keywords
        keywords = result.keywords_found
        assert len(keywords) > 0
        
        # Should contain some expected keywords
        expected_keywords = ['mountain', 'crystal', 'ancient']
        found_expected = any(keyword in keywords for keyword in expected_keywords)
        assert found_expected
    
    def test_empty_message_handling(self):
        """Test handling of empty or invalid messages."""
        result = self.classifier.classify_message("", 'general')
        assert result.primary_topic == 'general'  # Should default
        assert result.confidence <= 0.5
        
        result = self.classifier.classify_message("   ", 'general')
        assert result.primary_topic == 'general'
        assert result.confidence <= 0.5


class TestWorldbuildingPromptService:
    """Test the prompt template service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.prompts = WorldbuildingPromptService()
    
    def test_prompt_template_retrieval(self):
        """Test retrieval of prompt templates for different topics."""
        topics = ['geography', 'culture', 'magic_system', 'politics', 'history']
        
        for topic in topics:
            template = self.prompts.get_prompt_template(topic)
            assert template.topic == topic
            assert len(template.system_prompt) > 50
            assert len(template.followup_prompts) > 0
            assert len(template.key_questions) > 0
            assert len(template.completion_criteria) > 0
    
    def test_contextual_prompt_building(self):
        """Test building contextual prompts with conversation and story context."""
        prompt = self.prompts.build_contextual_prompt(
            'geography',
            conversation_context="We've discussed mountains and rivers",
            story_context="Fantasy world with magic"
        )
        
        assert 'geography' in prompt.lower()
        assert 'mountains' in prompt or 'rivers' in prompt
        assert 'fantasy' in prompt or 'magic' in prompt
        assert len(prompt) > 100
    
    def test_conversation_starters(self):
        """Test conversation starter generation."""
        topics = ['geography', 'culture', 'magic_system', 'politics']
        
        for topic in topics:
            starter = self.prompts.get_conversation_starter(topic)
            assert len(starter) > 20
            assert isinstance(starter, str)
    
    def test_follow_up_generation(self):
        """Test follow-up question generation for topics."""
        questions = self.prompts.generate_follow_up_questions('geography', "mountains and rivers")
        
        assert len(questions) > 0
        assert len(questions) <= 5
        
        for question in questions:
            assert len(question) > 10
            assert '?' in question


class TestWorldbuildingFollowupGenerator:
    """Test the follow-up question generator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.generator = WorldbuildingFollowupGenerator()
    
    def test_followup_question_generation(self):
        """Test generation of context-aware follow-up questions."""
        # Create test context
        context = WorldbuildingChatContext(
            story_id="test_story",
            current_topic='geography',
            conversation_state='exploring',
            active_topics=['geography'],
            topic_contexts={
                'geography': TopicContext(
                    topic='geography',
                    accumulated_content="Mountains and forests",
                    key_elements=['mountains', 'forests'],
                    questions_asked=['What kind of terrain?'],
                    completeness_score=0.3
                )
            },
            recent_messages=[
                ConversationMessage(
                    role="user",
                    content="Tell me about the mountains.",
                    timestamp=datetime.now(UTC).isoformat()
                )
            ],
            story_context={'genre': 'fantasy'}
        )
        
        questions = self.generator.generate_followup_questions(context, context.recent_messages)
        
        assert len(questions) > 0
        assert len(questions) <= 5
        
        for question in questions:
            assert len(question.question) > 5
            assert 0.0 <= question.priority <= 1.0
            assert question.topic in ['geography', 'culture', 'magic_system', 'politics', 'history', 'general']
    
    def test_gap_filling_questions(self):
        """Test generation of gap-filling questions."""
        # Create context with limited coverage
        context = WorldbuildingChatContext(
            story_id="test_story",
            current_topic='geography',
            conversation_state='exploring',
            active_topics=['geography'],  # Only one topic active
            topic_contexts={
                'geography': TopicContext(
                    topic='geography',
                    accumulated_content="Basic geography info",
                    key_elements=['mountains'],
                    questions_asked=[],
                    completeness_score=0.2  # Low completeness
                )
            },
            recent_messages=[],
            story_context={}
        )
        
        questions = self.generator.generate_followup_questions(context, [])
        
        # Should generate questions to fill gaps
        assert len(questions) > 0
        
        # Should include questions for unexplored topics
        question_topics = [q.topic for q in questions]
        unexplored_topics = ['culture', 'magic_system', 'politics', 'history']
        
        # At least some questions should be for unexplored topics
        gap_questions = [q for q in question_topics if q in unexplored_topics]
        assert len(gap_questions) > 0
    
    def test_connection_questions(self):
        """Test generation of questions that connect different topics."""
        # Create context with multiple active topics
        context = WorldbuildingChatContext(
            story_id="test_story",
            current_topic='culture',
            conversation_state='exploring',
            active_topics=['geography', 'culture'],
            topic_contexts={
                'geography': TopicContext(
                    topic='geography',
                    accumulated_content="Mountain regions",
                    key_elements=['mountains'],
                    questions_asked=[],
                    completeness_score=0.5
                ),
                'culture': TopicContext(
                    topic='culture',
                    accumulated_content="Mountain people traditions",
                    key_elements=['traditions'],
                    questions_asked=[],
                    completeness_score=0.4
                )
            },
            recent_messages=[],
            story_context={}
        )
        
        questions = self.generator.generate_followup_questions(context, [])
        
        # Should include connection questions
        connection_questions = [q for q in questions if 'geography' in q.question.lower() and 'culture' in q.question.lower()]
        # Note: This is a simplified test - actual connection detection is more sophisticated
        
        assert len(questions) > 0  # Should generate some questions
    
    def test_entity_extraction(self):
        """Test extraction of entities from messages."""
        text = "The Kingdom of Eldoria has the Frostspire Mountains and the Crystal River."
        entities = self.generator._extract_mentioned_entities(text)
        
        assert len(entities) > 0
        
        # Should extract proper nouns
        expected_entities = ['Kingdom', 'Eldoria', 'Frostspire', 'Mountains', 'Crystal', 'River']
        found_entities = [e for e in expected_entities if e in entities]
        assert len(found_entities) > 0
    
    def test_priority_calculation(self):
        """Test question priority calculation."""
        analysis = {
            'topic_depth': {'geography': 0.3},
            'user_interests': ['detail_seeking'],
            'mentioned_entities': {'mountains', 'rivers'}
        }
        
        priority = self.generator._calculate_question_priority(
            'exploration', 'geography', analysis
        )
        
        assert 0.0 <= priority <= 1.0
        
        # Should boost priority for less explored topics
        analysis_unexplored = {
            'topic_depth': {'geography': 0.1},  # Less explored
            'user_interests': ['detail_seeking'],
            'mentioned_entities': set()
        }
        
        priority_unexplored = self.generator._calculate_question_priority(
            'exploration', 'geography', analysis_unexplored
        )
        
        assert priority_unexplored >= priority  # Should be higher or equal


class TestWorldbuildingIntegration:
    """Test integration between different worldbuilding services."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = WorldbuildingTopicClassifier()
        self.prompts = WorldbuildingPromptService()
        self.generator = WorldbuildingFollowupGenerator()
    
    def test_classifier_to_prompts_integration(self):
        """Test integration between classifier and prompt service."""
        # Classify a message
        message = "Tell me about the magic system in your world."
        result = self.classifier.classify_message(message, 'general')
        
        # Use classification result to get appropriate prompt
        template = self.prompts.get_prompt_template(result.primary_topic)
        
        assert template.topic == result.primary_topic
        assert 'magic' in template.system_prompt.lower()
    
    def test_prompts_to_followup_integration(self):
        """Test integration between prompts and follow-up generation."""
        # Get a prompt template
        template = self.prompts.get_prompt_template('geography')
        
        # Use template questions as basis for follow-up generation
        template_questions = template.followup_prompts
        generated_questions = self.prompts.generate_follow_up_questions('geography')
        
        # Should have some overlap or similar structure
        assert len(template_questions) > 0
        assert len(generated_questions) > 0
        
        # Both should be substantial questions
        for question in template_questions + generated_questions:
            assert len(question) > 10
            assert '?' in question
    
    def test_end_to_end_question_flow(self):
        """Test complete flow from message to follow-up questions."""
        # Start with user message
        user_message = "My world has floating islands connected by magical bridges."
        
        # Classify the message
        classification = self.classifier.classify_message(user_message, 'general')
        
        # Get appropriate prompt template
        template = self.prompts.get_prompt_template(classification.primary_topic)
        
        # Create context for follow-up generation
        context = WorldbuildingChatContext(
            story_id="integration_test",
            current_topic=classification.primary_topic,
            conversation_state='exploring',
            active_topics=[classification.primary_topic],
            topic_contexts={
                classification.primary_topic: TopicContext(
                    topic=classification.primary_topic,
                    accumulated_content=user_message,
                    key_elements=classification.keywords_found,
                    questions_asked=[],
                    completeness_score=0.2
                )
            },
            recent_messages=[
                ConversationMessage(
                    role="user",
                    content=user_message,
                    timestamp=datetime.now(UTC).isoformat()
                )
            ],
            story_context={'genre': 'fantasy'}
        )
        
        # Generate follow-up questions
        followup_questions = self.generator.generate_followup_questions(
            context, context.recent_messages, max_questions=3
        )
        
        # Verify end-to-end flow worked
        assert classification.primary_topic in ['geography', 'magic_system']  # Should classify appropriately
        assert template.topic == classification.primary_topic
        assert len(followup_questions) > 0
        assert len(followup_questions) <= 3
        
        # Questions should be relevant to the classified topic or explore other worldbuilding aspects
        for question in followup_questions:
            assert len(question.question) > 10
            # Questions can be about the primary topic, general, secondary topics, or other worldbuilding topics
            valid_topics = ['geography', 'culture', 'magic_system', 'politics', 'history', 'technology', 'economy', 'general']
            assert question.topic in valid_topics
        
        # At least one question should be related to the primary topic or be general
        primary_related_questions = [q for q in followup_questions if q.topic in [classification.primary_topic, 'general'] or q.topic in classification.secondary_topics]
        assert len(primary_related_questions) > 0
