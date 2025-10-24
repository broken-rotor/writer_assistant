"""
Comprehensive tests for the Context Distillation and Summarization Engine.

This test suite covers all aspects of the context distillation system including:
- Context distiller functionality
- Summarization strategies
- Key information extraction
- Integration with token management system
- Error handling and edge cases
"""

import pytest
import logging
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, List, Any

# Import the modules we're testing
from backend.app.services.context_distillation import (
    ContextDistiller, DistillationConfig, DistillationResult,
    ContentType, DistillationTrigger
)
from backend.app.services.context_distillation.summarization_strategies import (
    SummarizationStrategy, PlotSummaryStrategy, CharacterDevelopmentStrategy,
    DialogueSummaryStrategy, EventSequenceStrategy, EmotionalMomentStrategy,
    WorldBuildingStrategy, SummaryResult
)
from backend.app.utils.key_information_extractor import (
    KeyInformationExtractor, KeyInformation, InformationType, ExtractionResult
)
from backend.app.services.token_management import (
    TokenCounter, TokenAllocator, LayerType, LayerHierarchy
)
from backend.app.services.llm_inference import LLMInference


# Test fixtures and sample data
@pytest.fixture
def mock_token_counter():
    """Mock token counter for testing."""
    counter = Mock(spec=TokenCounter)
    counter.count_tokens.side_effect = lambda text: len(text.split()) * 1.3  # Rough approximation
    return counter


@pytest.fixture
def mock_token_allocator():
    """Mock token allocator for testing."""
    allocator = Mock(spec=TokenAllocator)
    return allocator


@pytest.fixture
def mock_llm_service():
    """Mock LLM service for testing."""
    service = Mock(spec=LLMInference)
    service.generate.return_value = "This is a mock summary of the provided content."
    return service


@pytest.fixture
def sample_story_content():
    """Sample story content for testing."""
    return """
    Chapter 1: The Beginning
    
    Sarah walked through the ancient forest, her heart pounding with fear. The mysterious castle loomed ahead,
    its towers reaching toward the stormy sky. She had been searching for her missing brother Tom for weeks,
    following clues that led her to this dark realm.
    
    "I must find him," she whispered to herself, clutching the magical amulet her grandmother had given her.
    The amulet glowed softly, indicating that Tom was somewhere nearby.
    
    Suddenly, a figure emerged from the shadows. It was Marcus, the dark sorcerer who had kidnapped Tom.
    "You're too late," Marcus sneered. "Your brother is already under my spell."
    
    Sarah felt a surge of anger and determination. This was the moment she had been preparing for.
    The final confrontation between good and evil was about to begin.
    """


@pytest.fixture
def distillation_config():
    """Standard distillation configuration for testing."""
    return DistillationConfig(
        rolling_summary_threshold=1000,  # Lower threshold for testing
        emergency_compression_threshold=1500,
        compression_ratios={
            ContentType.PLOT_SUMMARY: 0.4,
            ContentType.CHARACTER_DEVELOPMENT: 0.5,
            ContentType.DIALOGUE: 0.3,
        }
    )


class TestDistillationConfig:
    """Test the DistillationConfig class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = DistillationConfig()
        
        assert config.rolling_summary_threshold == 25000
        assert config.emergency_compression_threshold == 30000
        assert config.preserve_key_plot_points is True
        assert config.preserve_character_arcs is True
        assert config.llm_temperature == 0.3
        assert config.max_summary_depth == 3
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = DistillationConfig(
            rolling_summary_threshold=10000,
            preserve_key_plot_points=False,
            llm_temperature=0.5
        )
        
        assert config.rolling_summary_threshold == 10000
        assert config.preserve_key_plot_points is False
        assert config.llm_temperature == 0.5
        # Default values should still be present
        assert config.emergency_compression_threshold == 30000


class TestContextDistiller:
    """Test the main ContextDistiller class."""
    
    def test_initialization(self, mock_token_counter, mock_token_allocator, mock_llm_service):
        """Test proper initialization of ContextDistiller."""
        distiller = ContextDistiller(
            token_counter=mock_token_counter,
            token_allocator=mock_token_allocator,
            llm_service=mock_llm_service
        )
        
        assert distiller.token_counter == mock_token_counter
        assert distiller.token_allocator == mock_token_allocator
        assert distiller.llm_service == mock_llm_service
        assert isinstance(distiller.config, DistillationConfig)
        assert isinstance(distiller.layer_hierarchy, LayerHierarchy)
        assert len(distiller._strategies) == 7  # All content types should have strategies
    
    def test_check_distillation_needed_threshold(
        self, mock_token_counter, mock_token_allocator, mock_llm_service, distillation_config
    ):
        """Test distillation threshold detection."""
        distiller = ContextDistiller(
            token_counter=mock_token_counter,
            token_allocator=mock_token_allocator,
            llm_service=mock_llm_service,
            config=distillation_config
        )
        
        # Mock token counting to exceed threshold
        mock_token_counter.count_tokens.return_value = 600  # Will total 1200 > 1000 threshold
        
        layer_contents = {
            LayerType.WORKING_MEMORY: "content1",
            LayerType.EPISODIC_MEMORY: "content2"
        }
        current_allocation = {
            LayerType.WORKING_MEMORY: 1000,
            LayerType.EPISODIC_MEMORY: 1000
        }
        
        needs_distillation, trigger, layer = distiller.check_distillation_needed(
            layer_contents, current_allocation
        )
        
        assert needs_distillation is True
        assert trigger == DistillationTrigger.TOKEN_THRESHOLD
        assert layer is None  # No specific layer for threshold trigger
    
    def test_check_distillation_needed_overflow(
        self, mock_token_counter, mock_token_allocator, mock_llm_service, distillation_config
    ):
        """Test layer overflow detection."""
        distiller = ContextDistiller(
            token_counter=mock_token_counter,
            token_allocator=mock_token_allocator,
            llm_service=mock_llm_service,
            config=distillation_config
        )
        
        # Mock token counting for overflow scenario
        def mock_count_tokens(text):
            if text == "overflow_content":
                return 1200  # Exceeds allocation of 1000
            return 100
        
        mock_token_counter.count_tokens.side_effect = mock_count_tokens
        
        layer_contents = {
            LayerType.WORKING_MEMORY: "normal_content",
            LayerType.EPISODIC_MEMORY: "overflow_content"
        }
        current_allocation = {
            LayerType.WORKING_MEMORY: 1000,
            LayerType.EPISODIC_MEMORY: 1000
        }
        
        needs_distillation, trigger, layer = distiller.check_distillation_needed(
            layer_contents, current_allocation
        )
        
        assert needs_distillation is True
        assert trigger == DistillationTrigger.LAYER_OVERFLOW
        assert layer == LayerType.EPISODIC_MEMORY
    
    def test_distill_content_success(
        self, mock_token_counter, mock_token_allocator, mock_llm_service, sample_story_content
    ):
        """Test successful content distillation."""
        distiller = ContextDistiller(
            token_counter=mock_token_counter,
            token_allocator=mock_token_allocator,
            llm_service=mock_llm_service
        )
        
        # Mock token counting
        mock_token_counter.count_tokens.side_effect = [100, 40]  # Original, then compressed
        
        # Mock strategy summarization
        mock_summary_result = SummaryResult(
            summary="Compressed story content",
            key_information=["Character: Sarah", "Plot element: conflict"],
            quality_score=0.8,
            metadata={"strategy": "plot_summary"}
        )
        
        with patch.object(distiller._strategies[ContentType.PLOT_SUMMARY], 'summarize', return_value=mock_summary_result):
            result = distiller.distill_content(
                content=sample_story_content,
                content_type=ContentType.PLOT_SUMMARY,
                target_layer=LayerType.EPISODIC_MEMORY,
                trigger=DistillationTrigger.TOKEN_THRESHOLD
            )
        
        assert result.success is True
        assert result.original_token_count == 100
        assert result.compressed_token_count == 40
        assert result.compression_ratio == 0.4
        assert result.content_type == ContentType.PLOT_SUMMARY
        assert result.trigger == DistillationTrigger.TOKEN_THRESHOLD
        assert result.layer_affected == LayerType.EPISODIC_MEMORY
        assert len(result.key_information_preserved) == 2
        assert result.quality_score == 0.8
    
    def test_distill_content_failure(
        self, mock_token_counter, mock_token_allocator, mock_llm_service
    ):
        """Test content distillation failure handling."""
        distiller = ContextDistiller(
            token_counter=mock_token_counter,
            token_allocator=mock_token_allocator,
            llm_service=mock_llm_service
        )
        
        # Mock token counting
        mock_token_counter.count_tokens.return_value = 100
        
        # Mock strategy to raise exception
        with patch.object(distiller._strategies[ContentType.PLOT_SUMMARY], 'summarize', side_effect=Exception("Test error")):
            result = distiller.distill_content(
                content="test content",
                content_type=ContentType.PLOT_SUMMARY,
                target_layer=LayerType.EPISODIC_MEMORY,
                trigger=DistillationTrigger.TOKEN_THRESHOLD
            )
        
        assert result.success is False
        assert result.error_message == "Test error"
        assert result.compressed_token_count == 0
        assert result.compression_ratio == 0.0
    
    def test_handle_overflow(
        self, mock_token_counter, mock_token_allocator, mock_llm_service, distillation_config
    ):
        """Test overflow handling across multiple layers."""
        distiller = ContextDistiller(
            token_counter=mock_token_counter,
            token_allocator=mock_token_allocator,
            llm_service=mock_llm_service,
            config=distillation_config
        )
        
        # Mock token counting
        mock_token_counter.count_tokens.side_effect = [200, 100, 150, 75]  # Original, compressed for each layer
        
        # Mock strategy summarization
        mock_summary_result = SummaryResult(
            summary="Compressed content",
            key_information=["Test info"],
            quality_score=0.7
        )
        
        layer_contents = {
            LayerType.WORKING_MEMORY: "working content",  # Should be skipped (highest priority)
            LayerType.EPISODIC_MEMORY: "episodic content",
            LayerType.SEMANTIC_MEMORY: "semantic content"
        }
        
        with patch.object(distiller._strategies[ContentType.MIXED_CONTENT], 'summarize', return_value=mock_summary_result):
            results = distiller.handle_overflow(
                layer_contents=layer_contents,
                overflow_layer=LayerType.EPISODIC_MEMORY,
                target_reduction=150
            )
        
        assert len(results) >= 1  # At least one layer should be compressed
        assert all(result.success for result in results)
        assert all(result.trigger == DistillationTrigger.LAYER_OVERFLOW for result in results)
    
    def test_create_summary_of_summaries(
        self, mock_token_counter, mock_token_allocator, mock_llm_service
    ):
        """Test meta-summarization of multiple summaries."""
        distiller = ContextDistiller(
            token_counter=mock_token_counter,
            token_allocator=mock_token_allocator,
            llm_service=mock_llm_service
        )
        
        summaries = [
            "Summary 1: Sarah begins her quest to find Tom.",
            "Summary 2: Sarah encounters Marcus the sorcerer.",
            "Summary 3: The final confrontation approaches."
        ]
        
        # Mock token counting
        mock_token_counter.count_tokens.side_effect = [300, 150]  # Combined, then compressed
        
        # Mock strategy summarization
        mock_summary_result = SummaryResult(
            summary="Meta-summary of all story events",
            key_information=["Character: Sarah", "Character: Tom", "Character: Marcus"],
            quality_score=0.8
        )
        
        with patch.object(distiller._strategies[ContentType.PLOT_SUMMARY], 'summarize', return_value=mock_summary_result):
            result = distiller.create_summary_of_summaries(
                summaries=summaries,
                content_type=ContentType.PLOT_SUMMARY,
                target_tokens=150
            )
        
        assert result.success is True
        assert result.original_token_count == 300
        assert result.compressed_token_count == 150
        assert result.trigger == DistillationTrigger.SCHEDULED_COMPRESSION
        assert result.layer_affected == LayerType.LONG_TERM_MEMORY
    
    def test_create_summary_of_summaries_empty(
        self, mock_token_counter, mock_token_allocator, mock_llm_service
    ):
        """Test meta-summarization with empty summaries list."""
        distiller = ContextDistiller(
            token_counter=mock_token_counter,
            token_allocator=mock_token_allocator,
            llm_service=mock_llm_service
        )
        
        result = distiller.create_summary_of_summaries(
            summaries=[],
            content_type=ContentType.PLOT_SUMMARY
        )
        
        assert result.success is False
        assert result.error_message == "No summaries provided"
    
    def test_classify_content(
        self, mock_token_counter, mock_token_allocator, mock_llm_service
    ):
        """Test content classification heuristics."""
        distiller = ContextDistiller(
            token_counter=mock_token_counter,
            token_allocator=mock_token_allocator,
            llm_service=mock_llm_service
        )
        
        # Test different content types
        plot_content = "The story begins with a conflict between the hero and villain."
        character_content = "Sarah's personality changed as she developed courage and strength."
        dialogue_content = '"Hello," she said. "How are you?" he replied. "Fine," she answered.'
        world_content = "The ancient kingdom of Eldoria was built in the mystical forest."
        emotion_content = "She felt overwhelming love and joy in her heart."
        event_content = "The event happened suddenly when the explosion occurred."
        
        assert distiller._classify_content(plot_content) == ContentType.PLOT_SUMMARY
        assert distiller._classify_content(character_content) == ContentType.CHARACTER_DEVELOPMENT
        assert distiller._classify_content(dialogue_content) == ContentType.DIALOGUE
        assert distiller._classify_content(world_content) == ContentType.WORLD_BUILDING
        assert distiller._classify_content(emotion_content) == ContentType.EMOTIONAL_MOMENT
        assert distiller._classify_content(event_content) == ContentType.EVENT_SEQUENCE
        assert distiller._classify_content("random text") == ContentType.MIXED_CONTENT
    
    def test_get_compression_stats(
        self, mock_token_counter, mock_token_allocator, mock_llm_service
    ):
        """Test compression statistics generation."""
        distiller = ContextDistiller(
            token_counter=mock_token_counter,
            token_allocator=mock_token_allocator,
            llm_service=mock_llm_service
        )
        
        # Add some mock distillation history
        distiller._distillation_history = [
            DistillationResult(
                success=True,
                original_token_count=100,
                compressed_token_count=40,
                compression_ratio=0.4,
                content_type=ContentType.PLOT_SUMMARY,
                trigger=DistillationTrigger.TOKEN_THRESHOLD,
                layer_affected=LayerType.EPISODIC_MEMORY,
                quality_score=0.8
            ),
            DistillationResult(
                success=True,
                original_token_count=200,
                compressed_token_count=100,
                compression_ratio=0.5,
                content_type=ContentType.CHARACTER_DEVELOPMENT,
                trigger=DistillationTrigger.LAYER_OVERFLOW,
                layer_affected=LayerType.SEMANTIC_MEMORY,
                quality_score=0.7
            )
        ]
        
        stats = distiller.get_compression_stats()
        
        assert stats["total_operations"] == 2
        assert stats["successful_operations"] == 2
        assert stats["total_tokens_processed"] == 300
        assert stats["total_tokens_saved"] == 160
        assert stats["average_compression_ratio"] == 140 / 300  # (40 + 100) / (100 + 200)
        assert "content_type_breakdown" in stats
        assert "layer_breakdown" in stats


class TestSummarizationStrategies:
    """Test the various summarization strategies."""
    
    def test_plot_summary_strategy(self, mock_llm_service, sample_story_content):
        """Test plot summarization strategy."""
        strategy = PlotSummaryStrategy(mock_llm_service)
        
        result = strategy.summarize(
            content=sample_story_content,
            target_tokens=50,
            context={},
            preserve_key_info=True
        )
        
        assert isinstance(result, SummaryResult)
        assert result.summary == "This is a mock summary of the provided content."
        assert result.metadata["strategy"] == "plot_summary"
        assert result.metadata["target_tokens"] == 50
    
    def test_character_development_strategy(self, mock_llm_service):
        """Test character development summarization strategy."""
        strategy = CharacterDevelopmentStrategy(mock_llm_service)
        
        character_content = """
        Sarah started as a timid girl but grew into a brave warrior. Her personality transformed
        through her journey. She learned to trust herself and became confident in her abilities.
        """
        
        result = strategy.summarize(
            content=character_content,
            target_tokens=30,
            context={},
            preserve_key_info=True
        )
        
        assert isinstance(result, SummaryResult)
        assert result.metadata["strategy"] == "character_development"
    
    def test_dialogue_summary_strategy(self, mock_llm_service):
        """Test dialogue summarization strategy."""
        strategy = DialogueSummaryStrategy(mock_llm_service)
        
        dialogue_content = '''
        "I must find him," Sarah said desperately.
        "You're too late," Marcus replied with a sneer.
        "I'll never give up," she declared with determination.
        '''
        
        result = strategy.summarize(
            content=dialogue_content,
            target_tokens=20,
            context={},
            preserve_key_info=True
        )
        
        assert isinstance(result, SummaryResult)
        assert result.metadata["strategy"] == "dialogue_summary"
    
    def test_strategy_error_handling(self, mock_llm_service):
        """Test strategy error handling."""
        strategy = PlotSummaryStrategy(mock_llm_service)
        mock_llm_service.generate.side_effect = Exception("LLM error")
        
        result = strategy.summarize(
            content="test content",
            target_tokens=50,
            context={},
            preserve_key_info=True
        )
        
        assert result.summary == ""
        assert len(result.warnings) > 0
        assert "Summarization failed" in result.warnings[0]


class TestKeyInformationExtractor:
    """Test the key information extraction utility."""
    
    def test_initialization(self):
        """Test proper initialization of KeyInformationExtractor."""
        extractor = KeyInformationExtractor()
        
        assert extractor._character_patterns is not None
        assert extractor._plot_patterns is not None
        assert extractor._location_patterns is not None
        assert extractor._emotion_patterns is not None
        assert extractor._temporal_patterns is not None
        assert extractor._causal_patterns is not None
    
    def test_extract_key_information(self, sample_story_content):
        """Test key information extraction from story content."""
        extractor = KeyInformationExtractor()
        
        result = extractor.extract_key_information(
            content=sample_story_content,
            preserve_threshold=0.5
        )
        
        assert isinstance(result, ExtractionResult)
        assert len(result.key_information) > 0
        assert result.statistics["total_extracted"] >= result.statistics["total_preserved"]
        assert result.statistics["preservation_ratio"] <= 1.0
    
    def test_extract_characters(self, sample_story_content):
        """Test character name extraction."""
        extractor = KeyInformationExtractor()
        
        characters = extractor._extract_characters(sample_story_content)
        
        # Should find Sarah, Tom, and Marcus
        character_names = [char.content for char in characters]
        assert "Sarah" in character_names
        assert "Tom" in character_names
        assert "Marcus" in character_names
        
        # Check importance scores
        for char in characters:
            assert char.importance_score > 0
            assert char.info_type == InformationType.CHARACTER_NAME
    
    def test_extract_empty_content(self):
        """Test extraction with empty content."""
        extractor = KeyInformationExtractor()
        
        result = extractor.extract_key_information(content="")
        
        assert len(result.key_information) == 0
        assert len(result.warnings) > 0
        assert "Empty content provided" in result.warnings[0]
    
    def test_get_preservation_recommendations(self, sample_story_content):
        """Test preservation recommendations."""
        extractor = KeyInformationExtractor()
        
        extraction_result = extractor.extract_key_information(
            content=sample_story_content,
            preserve_threshold=0.3
        )
        
        recommendations = extractor.get_preservation_recommendations(
            extraction_result=extraction_result,
            target_compression_ratio=0.4
        )
        
        assert "target_items" in recommendations
        assert "recommendations_by_type" in recommendations
        assert "preservation_strategy" in recommendations
        assert "quality_indicators" in recommendations
        assert recommendations["target_items"] > 0


class TestIntegration:
    """Integration tests for the complete context distillation system."""
    
    def test_end_to_end_distillation(
        self, mock_token_counter, mock_token_allocator, mock_llm_service, sample_story_content
    ):
        """Test complete end-to-end distillation process."""
        # Setup
        distiller = ContextDistiller(
            token_counter=mock_token_counter,
            token_allocator=mock_token_allocator,
            llm_service=mock_llm_service
        )
        
        # Mock token counting
        mock_token_counter.count_tokens.side_effect = [1000, 400]  # Original, then compressed
        
        # Mock LLM response
        mock_llm_service.generate.return_value = "Comprehensive summary of the story content preserving key elements."
        
        # Test the complete flow
        layer_contents = {
            LayerType.WORKING_MEMORY: sample_story_content,
            LayerType.EPISODIC_MEMORY: "Additional story content"
        }
        current_allocation = {
            LayerType.WORKING_MEMORY: 2000,
            LayerType.EPISODIC_MEMORY: 1500
        }
        
        # Check if distillation is needed
        needs_distillation, trigger, layer = distiller.check_distillation_needed(
            layer_contents, current_allocation
        )
        
        # Perform distillation if needed
        if needs_distillation:
            result = distiller.distill_content(
                content=sample_story_content,
                content_type=ContentType.PLOT_SUMMARY,
                target_layer=LayerType.EPISODIC_MEMORY,
                trigger=trigger
            )
            
            assert result.success is True
            assert result.compressed_token_count < result.original_token_count
            assert result.compression_ratio < 1.0
    
    def test_multiple_distillation_operations(
        self, mock_token_counter, mock_token_allocator, mock_llm_service
    ):
        """Test multiple distillation operations and history tracking."""
        distiller = ContextDistiller(
            token_counter=mock_token_counter,
            token_allocator=mock_token_allocator,
            llm_service=mock_llm_service
        )
        
        # Mock responses
        mock_token_counter.count_tokens.side_effect = [100, 40, 200, 80, 150, 60]
        mock_llm_service.generate.return_value = "Mock summary"
        
        # Perform multiple distillations
        contents = [
            ("Plot content", ContentType.PLOT_SUMMARY),
            ("Character content", ContentType.CHARACTER_DEVELOPMENT),
            ("Dialogue content", ContentType.DIALOGUE)
        ]
        
        for content, content_type in contents:
            result = distiller.distill_content(
                content=content,
                content_type=content_type,
                target_layer=LayerType.EPISODIC_MEMORY,
                trigger=DistillationTrigger.TOKEN_THRESHOLD
            )
            assert result.success is True
        
        # Check history and statistics
        history = distiller.get_distillation_history()
        assert len(history) == 3
        
        stats = distiller.get_compression_stats()
        assert stats["total_operations"] == 3
        assert stats["successful_operations"] == 3
        assert stats["total_tokens_processed"] == 450  # 100 + 200 + 150
        assert stats["total_tokens_saved"] == 270  # (100-40) + (200-80) + (150-60)
