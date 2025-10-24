"""
Integration tests for transparent context optimization in generation endpoints.

This module tests that context optimization works transparently with existing
generation endpoints while maintaining API compatibility.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json

from backend.app.main import app
from backend.app.models.generation_models import (
    SystemPrompts, CharacterInfo, FeedbackItem
)
from backend.app.services.context_optimization import (
    ContextOptimizationService, OptimizedContext
)


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_system_prompts():
    """Sample system prompts for testing."""
    return {
        "mainPrefix": "You are a creative writing assistant.",
        "mainSuffix": "Always write engaging and vivid content.",
        "assistantPrompt": "Focus on character development and narrative flow.",
        "editorPrompt": "Provide constructive feedback for improvement."
    }


@pytest.fixture
def sample_characters():
    """Sample characters for testing."""
    return [
        {
            "name": "Aria Shadowmere",
            "basicBio": "A skilled elven ranger with a mysterious past",
            "sex": "female",
            "gender": "female",
            "age": 127,
            "physicalAppearance": "Tall and lithe with silver hair and green eyes",
            "personality": "Cautious but fiercely loyal, with a dry sense of humor",
            "motivations": "To protect the ancient forests from destruction",
            "fears": "Losing those she cares about to the darkness",
            "relationships": "Close bond with her wolf companion, Fenris"
        },
        {
            "name": "Marcus Ironforge",
            "basicBio": "A dwarven blacksmith turned reluctant hero",
            "sex": "male", 
            "gender": "male",
            "age": 89,
            "physicalAppearance": "Stocky build with braided red beard and calloused hands",
            "personality": "Gruff exterior hiding a kind heart, values craftsmanship",
            "motivations": "To forge weapons that can defeat the ancient evil",
            "fears": "His creations being used for evil purposes",
            "relationships": "Mentor to young apprentices, friend to Aria"
        }
    ]


@pytest.fixture
def large_worldbuilding():
    """Large worldbuilding text that should trigger optimization."""
    base_text = """The realm of Aethermoor is a vast continent divided into seven kingdoms, each with its own unique culture, magic system, and political structure. The northern kingdom of Frostholm is perpetually covered in snow and ice, ruled by the Ice Queen Morwyn who commands frost magic and maintains an army of ice elementals. The people of Frostholm are hardy and resilient, living in great ice cities carved from glaciers, and they worship the Aurora Spirits that dance across their skies.

To the east lies the desert kingdom of Solaria, where the sun never sets and the sands shift with magical winds. The Solarian people have adapted to the eternal daylight, developing sun magic that allows them to harness solar energy for both practical and combat purposes. Their capital, the Golden Citadel, is a marvel of architecture that floats above the desert sands, powered by concentrated sunlight.

The central kingdom of Verdania is a lush forest realm where nature magic flows strongest. Ancient trees the size of mountains house entire cities in their branches, and the Verdanian druids can communicate with all forms of plant and animal life. The Great Tree, Yggdrasil's Heart, stands at the center of their realm and is said to be the source of all life magic in Aethermoor.

South of Verdania lies the maritime kingdom of Aquatica, built on a series of floating islands connected by bridges of crystallized water. The Aquaticans are master sailors and water mages, able to control tides, summon sea creatures, and even walk on water. Their navy is unmatched, and their underwater cities rival any surface settlement in beauty and complexity.

The western kingdom of Umbros is shrouded in perpetual twilight, where shadow magic reigns supreme. The Umbrosians have learned to manipulate darkness itself, creating constructs of living shadow and traveling through the shadow realm. Their cities exist partially in the shadow plane, making them nearly impossible to attack by conventional means.

In the mountainous regions between kingdoms lies the independent city-state of Nexus, a neutral ground where all magical traditions meet and trade. Nexus is built into a massive mountain that contains veins of pure magical crystal, making it a hub for magical research and artifact creation. The city is governed by the Council of Mages, with representatives from each kingdom.

Finally, there are the Shattered Isles to the far south, a chaotic region where wild magic storms rage constantly. These islands are home to the most dangerous magical creatures and the most powerful artifacts, but also the greatest treasures. Only the bravest adventurers dare to explore the Shattered Isles, and few return unchanged."""
    
    # Repeat the text multiple times to create a large context
    return base_text * 5


@pytest.fixture
def large_story_summary():
    """Large story summary that should trigger optimization."""
    base_text = """The story follows our heroes as they embark on an epic quest to prevent the awakening of the Ancient Darkness, a primordial evil that was sealed away millennia ago by the combined efforts of all seven kingdoms. The seal is weakening, and dark creatures are beginning to emerge from the void between worlds.

Our protagonists must gather the Seven Sacred Artifacts, each hidden in one of the kingdoms and guarded by powerful magical trials. The Frost Crown of Frostholm grants dominion over ice and winter, the Solar Scepter of Solaria commands the power of eternal flame, the Living Staff of Verdania channels the essence of nature itself, the Tidal Orb of Aquatica controls all waters, the Shadow Cloak of Umbros allows mastery over darkness, the Crystal Core of Nexus amplifies all magical abilities, and the Chaos Stone of the Shattered Isles can reshape reality itself.

However, they are not the only ones seeking these artifacts. The Cult of the Void, led by the mysterious Shadow Prophet, seeks to claim the artifacts to break the seal completely and usher in an age of darkness. The cult has infiltrated all levels of society across the kingdoms, and our heroes must be careful who they trust.

As the story progresses, our heroes discover that the Ancient Darkness is not just a mindless evil, but a sentient entity that was once part of the world itself - the shadow cast by creation. It seeks to reclaim what it believes is rightfully its domain, and it has been manipulating events for centuries to engineer its own release.

The heroes must not only gather the artifacts but also learn to work together despite their different backgrounds and magical traditions. They face internal conflicts, betrayals, and the constant threat of corruption by the very darkness they seek to defeat. Each character must confront their own inner darkness and make difficult choices about what they are willing to sacrifice to save their world."""
    
    # Repeat to create large context
    return base_text * 3


class TestContextOptimizationIntegration:
    """Test suite for context optimization integration with generation endpoints."""
    
    @patch('backend.app.services.llm_inference.get_llm')
    def test_generate_chapter_with_small_context(self, mock_get_llm, client, sample_system_prompts, sample_characters):
        """Test chapter generation with small context that doesn't need optimization."""
        # Mock LLM
        mock_llm = Mock()
        mock_llm.chat_completion.return_value = "This is a generated chapter with vivid descriptions and engaging dialogue."
        mock_get_llm.return_value = mock_llm
        
        request_data = {
            "systemPrompts": sample_system_prompts,
            "worldbuilding": "A small fantasy village with a magical forest nearby.",
            "storySummary": "Heroes must save the village from dark creatures.",
            "previousChapters": [],
            "characters": sample_characters[:1],  # Only one character
            "plotPoint": "The hero discovers a mysterious artifact in the forest.",
            "incorporatedFeedback": []
        }
        
        response = client.post("/api/v1/generate-chapter", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "chapterText" in data
        assert "wordCount" in data
        assert "metadata" in data
        
        # Verify LLM was called
        mock_llm.chat_completion.assert_called_once()
        call_args = mock_llm.chat_completion.call_args
        messages = call_args[0][0]
        
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
    
    @patch('backend.app.services.llm_inference.get_llm')
    def test_generate_chapter_with_large_context(self, mock_get_llm, client, sample_system_prompts, sample_characters, large_worldbuilding, large_story_summary):
        """Test chapter generation with large context that should trigger optimization."""
        # Mock LLM
        mock_llm = Mock()
        mock_llm.chat_completion.return_value = "This is a generated chapter with optimized context."
        mock_get_llm.return_value = mock_llm
        
        # Create large feedback list
        large_feedback = [
            {"source": "editor", "type": "style", "content": f"Feedback item {i}: Add more descriptive language and sensory details to enhance the reader's immersion in the story world.", "incorporated": True}
            for i in range(10)
        ]
        
        request_data = {
            "systemPrompts": sample_system_prompts,
            "worldbuilding": large_worldbuilding,
            "storySummary": large_story_summary,
            "previousChapters": [],
            "characters": sample_characters * 3,  # Multiple characters
            "plotPoint": "The heroes must infiltrate the enemy stronghold while avoiding detection by the shadow guards and magical wards.",
            "incorporatedFeedback": large_feedback
        }
        
        response = client.post("/api/v1/generate-chapter", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "chapterText" in data
        assert "wordCount" in data
        assert "metadata" in data
        
        # Verify LLM was called with optimized context
        mock_llm.chat_completion.assert_called_once()
        call_args = mock_llm.chat_completion.call_args
        messages = call_args[0][0]
        
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        
        # The context should be present but potentially optimized
        system_content = messages[0]["content"]
        user_content = messages[1]["content"]
        
        assert len(system_content) > 0
        assert len(user_content) > 0
        assert "Plot point for this chapter" in user_content or "infiltrate the enemy stronghold" in user_content
    
    @patch('backend.app.services.llm_inference.get_llm')
    def test_character_feedback_with_optimization(self, mock_get_llm, client, sample_system_prompts, sample_characters, large_worldbuilding, large_story_summary):
        """Test character feedback with context optimization."""
        # Mock LLM
        mock_llm = Mock()
        mock_llm.chat_completion.return_value = json.dumps({
            "actions": ["Draw her bow", "Scan the forest", "Signal to Marcus"],
            "dialog": ["Something's not right here", "We should proceed carefully", "Do you sense that?"],
            "physicalSensations": ["Heart racing", "Muscles tense", "Cold sweat"],
            "emotions": ["Anxious", "Alert", "Protective"],
            "internalMonologue": ["This feels like a trap", "I need to protect Marcus", "Trust your instincts"]
        })
        mock_get_llm.return_value = mock_llm
        
        request_data = {
            "systemPrompts": sample_system_prompts,
            "worldbuilding": large_worldbuilding,
            "storySummary": large_story_summary,
            "previousChapters": [],
            "character": sample_characters[0],
            "plotPoint": "The party encounters a group of suspicious travelers on the forest path who claim to be merchants but carry weapons.",
            "incorporatedFeedback": []
        }
        
        response = client.post("/api/v1/character-feedback", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "characterName" in data
        assert "feedback" in data
        assert data["characterName"] == "Aria Shadowmere"
        
        feedback = data["feedback"]
        assert "actions" in feedback
        assert "dialog" in feedback
        assert "physicalSensations" in feedback
        assert "emotions" in feedback
        assert "internalMonologue" in feedback
        
        # Verify LLM was called
        mock_llm.chat_completion.assert_called_once()
    
    @patch('backend.app.services.llm_inference.get_llm')
    def test_rater_feedback_with_optimization(self, mock_get_llm, client, sample_system_prompts, large_worldbuilding, large_story_summary):
        """Test rater feedback with context optimization."""
        # Mock LLM
        mock_llm = Mock()
        mock_llm.chat_completion.return_value = json.dumps({
            "opinion": "This plot point has good tension and mystery. The suspicious travelers create intrigue.",
            "suggestions": [
                "Add more specific details about what makes the travelers suspicious",
                "Consider the party's previous experiences with deception",
                "Develop the setting more - what does the forest path look like?",
                "Think about the travelers' motivations and backstory"
            ]
        })
        mock_get_llm.return_value = mock_llm
        
        request_data = {
            "systemPrompts": sample_system_prompts,
            "raterPrompt": "You are an experienced story editor. Evaluate plot points for narrative strength, character development, and reader engagement.",
            "worldbuilding": large_worldbuilding,
            "storySummary": large_story_summary,
            "previousChapters": [],
            "plotPoint": "The party encounters suspicious travelers who claim to be merchants.",
            "incorporatedFeedback": []
        }
        
        response = client.post("/api/v1/rater-feedback", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "raterName" in data
        assert "feedback" in data
        
        feedback = data["feedback"]
        assert "opinion" in feedback
        assert "suggestions" in feedback
        assert isinstance(feedback["suggestions"], list)
        
        # Verify LLM was called
        mock_llm.chat_completion.assert_called_once()
    
    @patch('backend.app.services.llm_inference.get_llm')
    def test_editor_review_with_optimization(self, mock_get_llm, client, sample_system_prompts, large_worldbuilding, large_story_summary):
        """Test editor review with context optimization."""
        # Mock LLM
        mock_llm = Mock()
        mock_llm.chat_completion.return_value = json.dumps({
            "suggestions": [
                {"issue": "Pacing", "suggestion": "The chapter moves too quickly through important events", "priority": "high"},
                {"issue": "Character development", "suggestion": "Show more of Aria's internal conflict", "priority": "medium"},
                {"issue": "Setting description", "suggestion": "Add more sensory details about the forest", "priority": "medium"},
                {"issue": "Dialogue", "suggestion": "Make the conversation more natural", "priority": "low"}
            ]
        })
        mock_get_llm.return_value = mock_llm
        
        large_chapter = """Chapter 1: The Forest Path

Aria Shadowmere moved silently through the ancient forest, her elven senses alert to every sound and shadow. The path ahead wound between towering oaks whose branches formed a canopy so thick that only scattered beams of sunlight reached the forest floor. Behind her, Marcus Ironforge's heavy boots crunched on fallen leaves despite his attempts at stealth.

"We should reach the village by nightfall," Aria whispered, her green eyes scanning the undergrowth for any sign of danger.

Marcus adjusted his pack, the weight of his smithing tools a familiar burden. "Assuming we don't run into any of those shadow creatures you mentioned."

As if summoned by his words, a group of travelers appeared on the path ahead. They wore the rough clothing of merchants, but Aria's keen eyes noticed the way they moved - too coordinated, too alert. And those weren't merchant tools hanging from their belts.

"Greetings, fellow travelers," called their leader, a man with a scar across his left cheek. "The road ahead is dangerous. Perhaps we should travel together for safety."

Aria's hand moved instinctively to her bow. Something about these men set her nerves on edge, and in her long years as a ranger, she had learned to trust her instincts. The forest itself seemed to whisper warnings in the rustling of leaves overhead.""" * 3  # Make it longer
        
        request_data = {
            "systemPrompts": sample_system_prompts,
            "worldbuilding": large_worldbuilding,
            "storySummary": large_story_summary,
            "previousChapters": [],
            "characters": sample_characters,
            "chapterToReview": large_chapter
        }
        
        response = client.post("/api/v1/editor-review", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)
        assert len(data["suggestions"]) > 0
        
        # Check suggestion structure
        for suggestion in data["suggestions"]:
            assert "issue" in suggestion
            assert "suggestion" in suggestion
            assert "priority" in suggestion
        
        # Verify LLM was called
        mock_llm.chat_completion.assert_called_once()
    
    def test_context_optimization_service_initialization(self):
        """Test that the context optimization service initializes correctly."""
        from backend.app.services.context_optimization import get_context_optimization_service
        
        service = get_context_optimization_service()
        assert service is not None
        assert service.max_context_tokens > 0
        assert service.optimization_threshold > 0
        assert service.context_manager is not None
    
    def test_context_optimization_with_small_content(self):
        """Test context optimization with small content that doesn't need optimization."""
        from backend.app.services.context_optimization import ContextOptimizationService
        from backend.app.models.generation_models import SystemPrompts, CharacterInfo
        
        service = ContextOptimizationService()
        
        system_prompts = SystemPrompts(
            mainPrefix="You are a helpful assistant.",
            mainSuffix="Always be creative.",
            assistantPrompt="Focus on storytelling."
        )
        
        character = CharacterInfo(
            name="Test Character",
            basicBio="A simple test character",
            personality="Friendly",
            motivations="To help others",
            fears="Being alone"
        )
        
        result = service.optimize_character_feedback_context(
            system_prompts=system_prompts,
            worldbuilding="A small village",
            story_summary="A simple story",
            character=character,
            plot_point="Character meets a friend"
        )
        
        assert result is not None
        assert result.system_prompt
        assert result.user_message
        assert result.total_tokens > 0
        # With small content, optimization likely won't be applied
        assert result.compression_ratio <= 1.0
    
    @patch('backend.app.services.llm_inference.get_llm')
    def test_api_compatibility_maintained(self, mock_get_llm, client, sample_system_prompts, sample_characters):
        """Test that API contracts remain exactly the same after context optimization integration."""
        # Mock LLM
        mock_llm = Mock()
        mock_llm.chat_completion.return_value = "Generated chapter content"
        mock_get_llm.return_value = mock_llm
        
        # Test the same request format as before
        request_data = {
            "systemPrompts": sample_system_prompts,
            "worldbuilding": "Fantasy world",
            "storySummary": "Epic quest",
            "previousChapters": [],
            "characters": sample_characters,
            "plotPoint": "Heroes face a challenge",
            "incorporatedFeedback": []
        }
        
        response = client.post("/api/v1/generate-chapter", json=request_data)
        
        # Response format should be exactly the same
        assert response.status_code == 200
        data = response.json()
        
        # Check all expected fields are present
        assert "chapterText" in data
        assert "wordCount" in data
        assert "metadata" in data
        
        # Check field types
        assert isinstance(data["chapterText"], str)
        assert isinstance(data["wordCount"], int)
        assert isinstance(data["metadata"], dict)
        
        # Metadata should contain expected fields
        metadata = data["metadata"]
        assert "generatedAt" in metadata
        assert "plotPoint" in metadata
        assert "feedbackItemsIncorporated" in metadata
    
    @patch('backend.app.services.llm_inference.get_llm')
    def test_error_handling_when_optimization_fails(self, mock_get_llm, client, sample_system_prompts, sample_characters):
        """Test that endpoints gracefully handle context optimization failures."""
        # Mock LLM
        mock_llm = Mock()
        mock_llm.chat_completion.return_value = "Generated content despite optimization failure"
        mock_get_llm.return_value = mock_llm
        
        # Mock context optimization service to raise an exception
        with patch('backend.app.services.context_optimization.get_context_optimization_service') as mock_service:
            mock_service.side_effect = Exception("Context optimization service unavailable")
            
            request_data = {
                "systemPrompts": sample_system_prompts,
                "worldbuilding": "Fantasy world",
                "storySummary": "Epic quest",
                "previousChapters": [],
                "characters": sample_characters,
                "plotPoint": "Heroes face a challenge",
                "incorporatedFeedback": []
            }
            
            response = client.post("/api/v1/generate-chapter", json=request_data)
            
            # Should still work with fallback
            assert response.status_code == 200
            data = response.json()
            assert "chapterText" in data
            assert data["chapterText"] == "Generated content despite optimization failure"
    
    def test_performance_impact_acceptable(self, client, sample_system_prompts, sample_characters):
        """Test that context optimization doesn't introduce unacceptable latency."""
        import time
        
        with patch('backend.app.services.llm_inference.get_llm') as mock_get_llm:
            mock_llm = Mock()
            mock_llm.chat_completion.return_value = "Fast generated content"
            mock_get_llm.return_value = mock_llm
            
            request_data = {
                "systemPrompts": sample_system_prompts,
                "worldbuilding": "Small fantasy world",
                "storySummary": "Simple quest",
                "previousChapters": [],
                "characters": sample_characters[:1],
                "plotPoint": "Hero finds artifact",
                "incorporatedFeedback": []
            }
            
            start_time = time.time()
            response = client.post("/api/v1/generate-chapter", json=request_data)
            end_time = time.time()
            
            assert response.status_code == 200
            
            # Context optimization overhead should be minimal (< 100ms for small content)
            processing_time = end_time - start_time
            assert processing_time < 1.0  # Should be much faster, but allowing 1s for test environment
