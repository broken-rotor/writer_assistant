import pytest
from pydantic import ValidationError
from app.models.story import (
    StoryPhase,
    StoryStatus,
    CharacterConfig,
    GenerationConfig,
    OutlineStructure,
    ChapterContent,
    AgentFeedback
)


class TestStoryEnums:
    """Test story enumeration types"""

    def test_story_phase_values(self):
        """Test StoryPhase enum values"""
        assert StoryPhase.OUTLINE_DEVELOPMENT == "outline_development"
        assert StoryPhase.CHAPTER_DEVELOPMENT == "chapter_development"
        assert StoryPhase.COMPLETED == "completed"

    def test_story_status_values(self):
        """Test StoryStatus enum values"""
        assert StoryStatus.DRAFT == "draft"
        assert StoryStatus.IN_PROGRESS == "in_progress"
        assert StoryStatus.REVIEW == "review"
        assert StoryStatus.APPROVED == "approved"


class TestCharacterConfig:
    """Test CharacterConfig model"""

    def test_character_config_minimal(self):
        """Test CharacterConfig with minimal required fields"""
        character = CharacterConfig(
            name="Detective Morrison",
            role="protagonist"
        )
        assert character.name == "Detective Morrison"
        assert character.role == "protagonist"
        assert character.personality_traits == []
        assert character.background == {}

    def test_character_config_complete(self):
        """Test CharacterConfig with all fields"""
        character = CharacterConfig(
            name="Detective Morrison",
            role="protagonist",
            personality_traits=["analytical", "reserved", "determined"],
            background={
                "age": 42,
                "occupation": "detective",
                "backstory": "Former FBI profiler"
            }
        )
        assert character.name == "Detective Morrison"
        assert len(character.personality_traits) == 3
        assert character.background["age"] == 42

    def test_character_config_missing_name(self):
        """Test CharacterConfig fails without name"""
        with pytest.raises(ValidationError):
            CharacterConfig(role="protagonist")

    def test_character_config_missing_role(self):
        """Test CharacterConfig fails without role"""
        with pytest.raises(ValidationError):
            CharacterConfig(name="Detective Morrison")


class TestGenerationConfig:
    """Test GenerationConfig model"""

    def test_generation_config_defaults(self):
        """Test GenerationConfig with default values"""
        config = GenerationConfig()
        assert config.style_profile == "standard"
        assert config.character_templates == []
        assert config.rater_preferences == []
        assert config.target_length == "novel"
        assert config.complexity_level == "moderate"

    def test_generation_config_custom(self):
        """Test GenerationConfig with custom values"""
        config = GenerationConfig(
            style_profile="noir_detective",
            character_templates=["complex_protagonist", "mysterious_antagonist"],
            rater_preferences=["character_consistency", "narrative_flow"],
            target_length="novella",
            complexity_level="high"
        )
        assert config.style_profile == "noir_detective"
        assert len(config.character_templates) == 2
        assert len(config.rater_preferences) == 2
        assert config.target_length == "novella"
        assert config.complexity_level == "high"


class TestOutlineStructure:
    """Test OutlineStructure model"""

    def test_outline_structure_empty(self):
        """Test OutlineStructure with default empty values"""
        outline = OutlineStructure()
        assert outline.acts == []
        assert outline.chapters == []
        assert outline.characters == []
        assert outline.themes == []

    def test_outline_structure_complete(self):
        """Test OutlineStructure with complete data"""
        outline = OutlineStructure(
            acts=[
                {"act": 1, "title": "Setup", "chapters": [1, 2, 3]},
                {"act": 2, "title": "Confrontation", "chapters": [4, 5, 6]}
            ],
            chapters=[
                {"number": 1, "title": "The Beginning", "summary": "Introduction"},
                {"number": 2, "title": "The Mystery", "summary": "Discovery"}
            ],
            characters=[
                CharacterConfig(name="Hero", role="protagonist"),
                CharacterConfig(name="Villain", role="antagonist")
            ],
            themes=["redemption", "courage", "truth"]
        )
        assert len(outline.acts) == 2
        assert len(outline.chapters) == 2
        assert len(outline.characters) == 2
        assert len(outline.themes) == 3
        assert outline.acts[0]["title"] == "Setup"


class TestChapterContent:
    """Test ChapterContent model"""

    def test_chapter_content_minimal(self):
        """Test ChapterContent with minimal required fields"""
        chapter = ChapterContent(
            text="This is the chapter text.",
            word_count=5
        )
        assert chapter.text == "This is the chapter text."
        assert chapter.word_count == 5
        assert chapter.character_perspectives == {}

    def test_chapter_content_with_perspectives(self):
        """Test ChapterContent with character perspectives"""
        chapter = ChapterContent(
            text="Detective Morrison walked into the room.",
            word_count=7,
            character_perspectives={
                "detective_morrison": {
                    "internal_monologue": ["Something feels off"],
                    "observations": ["Room was too clean"],
                    "emotional_state": "suspicious"
                }
            }
        )
        assert chapter.word_count == 7
        assert "detective_morrison" in chapter.character_perspectives
        assert len(chapter.character_perspectives["detective_morrison"]["observations"]) == 1

    def test_chapter_content_missing_text(self):
        """Test ChapterContent fails without text"""
        with pytest.raises(ValidationError):
            ChapterContent(word_count=100)

    def test_chapter_content_missing_word_count(self):
        """Test ChapterContent fails without word_count"""
        with pytest.raises(ValidationError):
            ChapterContent(text="Some text here")


class TestAgentFeedback:
    """Test AgentFeedback model"""

    def test_agent_feedback_minimal(self):
        """Test AgentFeedback with minimal required fields"""
        feedback = AgentFeedback(
            score=8.5,
            feedback="Great character development"
        )
        assert feedback.score == 8.5
        assert feedback.feedback == "Great character development"
        assert feedback.suggestions == []
        assert feedback.priority == "medium"

    def test_agent_feedback_complete(self):
        """Test AgentFeedback with all fields"""
        feedback = AgentFeedback(
            score=7.2,
            feedback="Good narrative flow but pacing needs improvement",
            suggestions=[
                "Increase tension in Act 2",
                "Develop supporting characters more",
                "Add more descriptive details"
            ],
            priority="high"
        )
        assert feedback.score == 7.2
        assert len(feedback.suggestions) == 3
        assert feedback.priority == "high"

    def test_agent_feedback_score_validation(self):
        """Test AgentFeedback score is a valid float"""
        feedback = AgentFeedback(score=9.99, feedback="Excellent")
        assert isinstance(feedback.score, float)

        feedback2 = AgentFeedback(score=0.0, feedback="Needs work")
        assert feedback2.score == 0.0

    def test_agent_feedback_missing_score(self):
        """Test AgentFeedback fails without score"""
        with pytest.raises(ValidationError):
            AgentFeedback(feedback="Some feedback")

    def test_agent_feedback_missing_feedback(self):
        """Test AgentFeedback fails without feedback text"""
        with pytest.raises(ValidationError):
            AgentFeedback(score=8.0)
