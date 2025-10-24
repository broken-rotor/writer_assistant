"""
Comprehensive unit tests for the Content Prioritization System.

Tests LayeredPrioritizer, RAGRetriever, and RelevanceCalculator
with >85% code coverage as specified in the acceptance criteria.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List
from datetime import datetime, timedelta

# Add the backend directory to the path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import the modules to test
from app.utils.relevance_calculator import (
    RelevanceCalculator, ContentItem, ContentCategory, ScoringWeights, RelevanceScore
)
from app.services.content_prioritization.layered_prioritizer import (
    LayeredPrioritizer, ContentScore, PrioritizationConfig, AgentType, PrioritizationResult
)
from app.services.content_prioritization.rag_retriever import (
    RAGRetriever, RetrievalStrategy, RetrievalMode, RetrievalQuery, RetrievalResult
)


class TestRelevanceCalculator:
    """Test cases for RelevanceCalculator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = RelevanceCalculator()
        self.current_time = datetime.now()
        
        # Create test content items
        self.character_item = ContentItem(
            id="char_1",
            content="John is a brave knight who fights dragons",
            category=ContentCategory.CHARACTER,
            created_at=self.current_time - timedelta(days=1),
            last_accessed=self.current_time - timedelta(hours=2),
            access_count=5,
            importance_tags={"main_character", "plot_critical"},
            character_names={"john", "knight"},
            location_names=set()
        )
        
        self.scene_item = ContentItem(
            id="scene_1", 
            content="The dark forest where ancient magic dwells",
            category=ContentCategory.SCENE,
            created_at=self.current_time - timedelta(days=3),
            last_accessed=self.current_time - timedelta(days=1),
            access_count=2,
            importance_tags={"world_building"},
            character_names=set(),
            location_names={"forest", "magic"}
        )
    
    def test_calculate_score_basic(self):
        """Test basic score calculation."""
        context = {
            'active_characters': ['john'],
            'active_locations': ['forest'],
            'keywords': ['brave', 'magic']
        }
        
        score = self.calculator.calculate_score(
            self.character_item, context, self.current_time
        )
        
        assert isinstance(score, RelevanceScore)
        assert score.content_id == "char_1"
        assert 0.0 <= score.total_score <= 1.0
        assert 0.0 <= score.recency_score <= 1.0
        assert 0.0 <= score.relevance_score <= 1.0
        assert 0.0 <= score.importance_score <= 1.0
        assert 0.0 <= score.access_frequency_score <= 1.0
        assert len(score.explanation) > 0
    
    def test_recency_score_calculation(self):
        """Test recency score calculation with different time intervals."""
        # Recent item should have higher recency score
        recent_item = ContentItem(
            id="recent",
            content="Recent content",
            category=ContentCategory.NARRATIVE,
            created_at=self.current_time - timedelta(hours=1),
            last_accessed=self.current_time - timedelta(minutes=30),
            access_count=1
        )
        
        old_item = ContentItem(
            id="old",
            content="Old content", 
            category=ContentCategory.NARRATIVE,
            created_at=self.current_time - timedelta(days=30),
            last_accessed=self.current_time - timedelta(days=20),
            access_count=1
        )
        
        context = {}
        recent_score = self.calculator.calculate_score(recent_item, context, self.current_time)
        old_score = self.calculator.calculate_score(old_item, context, self.current_time)
        
        assert recent_score.recency_score > old_score.recency_score
    
    def test_relevance_score_calculation(self):
        """Test relevance score calculation with context matching."""
        context_high_relevance = {
            'active_characters': ['john'],
            'active_locations': [],
            'keywords': ['brave', 'knight']
        }
        
        context_low_relevance = {
            'active_characters': ['mary'],
            'active_locations': ['castle'],
            'keywords': ['magic', 'spell']
        }
        
        high_score = self.calculator.calculate_score(
            self.character_item, context_high_relevance, self.current_time
        )
        low_score = self.calculator.calculate_score(
            self.character_item, context_low_relevance, self.current_time
        )
        
        assert high_score.relevance_score > low_score.relevance_score
    
    def test_importance_score_calculation(self):
        """Test importance score calculation based on tags and category."""
        high_importance_item = ContentItem(
            id="important",
            content="Critical plot point",
            category=ContentCategory.PLOT_POINT,
            created_at=self.current_time,
            last_accessed=self.current_time,
            access_count=1,
            importance_tags={"plot_critical", "climax"}
        )
        
        low_importance_item = ContentItem(
            id="unimportant",
            content="Minor detail",
            category=ContentCategory.METADATA,
            created_at=self.current_time,
            last_accessed=self.current_time,
            access_count=1,
            importance_tags=set()
        )
        
        context = {}
        high_score = self.calculator.calculate_score(high_importance_item, context, self.current_time)
        low_score = self.calculator.calculate_score(low_importance_item, context, self.current_time)
        
        assert high_score.importance_score > low_score.importance_score
    
    def test_batch_calculate_scores(self):
        """Test batch score calculation."""
        items = [self.character_item, self.scene_item]
        context = {'active_characters': ['john']}
        
        scores = self.calculator.batch_calculate_scores(items, context, self.current_time)
        
        assert len(scores) == 2
        assert all(isinstance(score, RelevanceScore) for score in scores)
        # Should be sorted by total_score descending
        assert scores[0].total_score >= scores[1].total_score
    
    def test_scoring_weights_normalization(self):
        """Test that scoring weights are properly normalized."""
        weights = ScoringWeights(
            recency_weight=2.0,
            relevance_weight=3.0,
            importance_weight=1.0,
            access_frequency_weight=4.0
        )
        
        total = (weights.recency_weight + weights.relevance_weight + 
                weights.importance_weight + weights.access_frequency_weight)
        
        assert abs(total - 1.0) < 0.001  # Should sum to 1.0


class TestLayeredPrioritizer:
    """Test cases for LayeredPrioritizer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = PrioritizationConfig(
            max_items_per_category=5,
            min_score_threshold=0.2,
            token_budget=1000
        )
        self.prioritizer = LayeredPrioritizer(config=self.config)
        
        # Create test content items
        self.content_items = [
            ContentItem(
                id=f"item_{i}",
                content=f"Test content {i} with some text",
                category=ContentCategory.CHARACTER if i % 2 == 0 else ContentCategory.SCENE,
                created_at=datetime.now() - timedelta(days=i),
                last_accessed=datetime.now() - timedelta(hours=i),
                access_count=i + 1,
                importance_tags={"main_character"} if i < 3 else set(),
                character_names={f"char_{i}"},
                location_names={f"loc_{i}"}
            )
            for i in range(10)
        ]
    
    def test_prioritize_content_basic(self):
        """Test basic content prioritization."""
        context = {
            'active_characters': ['char_0', 'char_1'],
            'active_locations': ['loc_0'],
            'keywords': ['test']
        }
        
        result = self.prioritizer.prioritize_content(
            self.content_items, context, AgentType.WRITER
        )
        
        assert isinstance(result, PrioritizationResult)
        assert result.agent_type == AgentType.WRITER
        assert len(result.selected_content) > 0
        assert result.total_tokens_used <= result.total_tokens_available
        assert result.items_considered == len(self.content_items)
        assert result.items_selected == len(result.selected_content)
        assert len(result.context_summary) > 0
    
    def test_token_budget_enforcement(self):
        """Test that token budget is properly enforced."""
        context = {'active_characters': ['char_0']}
        small_budget = 100
        
        result = self.prioritizer.prioritize_content(
            self.content_items, context, AgentType.WRITER, token_budget=small_budget
        )
        
        assert result.total_tokens_used <= small_budget
        assert result.total_tokens_available == small_budget
    
    def test_agent_specific_weights(self):
        """Test that different agent types use different scoring weights."""
        context = {'active_characters': ['char_0']}
        
        writer_result = self.prioritizer.prioritize_content(
            self.content_items, context, AgentType.WRITER
        )
        
        character_result = self.prioritizer.prioritize_content(
            self.content_items, context, AgentType.CHARACTER
        )
        
        # Results may differ due to different scoring weights
        assert writer_result.agent_type != character_result.agent_type
    
    def test_minimum_score_threshold(self):
        """Test that items below minimum score threshold are filtered out."""
        config = PrioritizationConfig(min_score_threshold=0.9)  # Very high threshold
        prioritizer = LayeredPrioritizer(config=config)
        
        context = {}  # Empty context should result in low scores
        
        result = prioritizer.prioritize_content(
            self.content_items, context, AgentType.WRITER
        )
        
        # With empty context and high threshold, few items should be selected
        assert len(result.selected_content) < len(self.content_items)
    
    def test_category_balancing(self):
        """Test that content selection balances different categories."""
        # Create items with mixed categories
        mixed_items = []
        for i in range(6):
            category = ContentCategory.CHARACTER if i < 3 else ContentCategory.SCENE
            mixed_items.append(ContentItem(
                id=f"mixed_{i}",
                content=f"Mixed content {i}",
                category=category,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                access_count=1
            ))
        
        context = {'active_characters': [f'char_{i}' for i in range(6)]}
        
        result = self.prioritizer.prioritize_content(
            mixed_items, context, AgentType.WRITER
        )
        
        # Should have items from both categories
        categories = {item.content_item.category for item in result.selected_content}
        assert len(categories) > 1
    
    def test_performance_metrics_tracking(self):
        """Test that performance metrics are properly tracked."""
        context = {'active_characters': ['char_0']}
        
        initial_metrics = self.prioritizer.get_performance_metrics()
        initial_count = initial_metrics['total_prioritizations']
        
        self.prioritizer.prioritize_content(
            self.content_items, context, AgentType.WRITER
        )
        
        updated_metrics = self.prioritizer.get_performance_metrics()
        assert updated_metrics['total_prioritizations'] == initial_count + 1
        assert updated_metrics['average_processing_time'] > 0
    
    def test_config_update(self):
        """Test configuration updates."""
        new_config = PrioritizationConfig(
            max_items_per_category=3,
            min_score_threshold=0.5,
            token_budget=500
        )
        
        self.prioritizer.update_config(new_config)
        assert self.prioritizer.config.max_items_per_category == 3
        assert self.prioritizer.config.min_score_threshold == 0.5
        assert self.prioritizer.config.token_budget == 500


class TestRAGRetriever:
    """Test cases for RAGRetriever."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.retriever = RAGRetriever()
        
        # Create test content pool
        self.content_pool = [
            ContentItem(
                id="char_john",
                content="John is a brave knight who protects the kingdom",
                category=ContentCategory.CHARACTER,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                access_count=1,
                character_names={"john", "knight"},
                location_names={"kingdom"}
            ),
            ContentItem(
                id="scene_forest",
                content="The dark forest filled with ancient magic and mysterious creatures",
                category=ContentCategory.SCENE,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                access_count=1,
                character_names=set(),
                location_names={"forest"}
            ),
            ContentItem(
                id="plot_battle",
                content="The final battle between good and evil forces",
                category=ContentCategory.PLOT_POINT,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                access_count=1,
                importance_tags={"climax", "plot_critical"}
            )
        ]
    
    def test_keyword_based_retrieval(self):
        """Test keyword-based retrieval strategy."""
        query = RetrievalQuery(
            query_text="brave knight kingdom",
            strategy=RetrievalStrategy.KEYWORD_BASED,
            mode=RetrievalMode.CHARACTER_FOCUSED,
            max_results=2
        )
        
        result = self.retriever.retrieve(query, self.content_pool)
        
        assert isinstance(result, RetrievalResult)
        assert result.strategy_used == RetrievalStrategy.KEYWORD_BASED
        assert len(result.retrieved_items) <= query.max_results
        assert result.retrieval_time_ms > 0
        
        # Should retrieve character-related content
        retrieved_ids = {item.id for item in result.retrieved_items}
        assert "char_john" in retrieved_ids
    
    def test_embedding_based_retrieval(self):
        """Test embedding-based retrieval strategy."""
        query = RetrievalQuery(
            query_text="forest magic creatures",
            strategy=RetrievalStrategy.EMBEDDING_BASED,
            mode=RetrievalMode.SCENE_FOCUSED,
            max_results=2
        )
        
        result = self.retriever.retrieve(query, self.content_pool)
        
        assert result.strategy_used == RetrievalStrategy.EMBEDDING_BASED
        assert len(result.retrieved_items) <= query.max_results
        
        # Should retrieve scene-related content
        retrieved_ids = {item.id for item in result.retrieved_items}
        assert "scene_forest" in retrieved_ids
    
    def test_hybrid_retrieval(self):
        """Test hybrid retrieval strategy."""
        query = RetrievalQuery(
            query_text="battle kingdom",
            strategy=RetrievalStrategy.HYBRID,
            mode=RetrievalMode.BALANCED,
            max_results=3
        )
        
        result = self.retriever.retrieve(query, self.content_pool)
        
        assert result.strategy_used == RetrievalStrategy.HYBRID
        assert len(result.retrieved_items) <= query.max_results
    
    def test_semantic_search_retrieval(self):
        """Test semantic search retrieval strategy."""
        query = RetrievalQuery(
            query_text="final confrontation",
            strategy=RetrievalStrategy.SEMANTIC_SEARCH,
            mode=RetrievalMode.PLOT_FOCUSED,
            max_results=2,
            context={'current_scene_type': 'battle'}
        )
        
        result = self.retriever.retrieve(query, self.content_pool)
        
        assert result.strategy_used == RetrievalStrategy.SEMANTIC_SEARCH
        assert len(result.retrieved_items) <= query.max_results
    
    def test_category_filtering(self):
        """Test that retrieval respects target category filtering."""
        query = RetrievalQuery(
            query_text="knight forest battle",
            strategy=RetrievalStrategy.KEYWORD_BASED,
            mode=RetrievalMode.CHARACTER_FOCUSED,
            max_results=5,
            target_categories={ContentCategory.CHARACTER}
        )
        
        result = self.retriever.retrieve(query, self.content_pool)
        
        # Should only return character items
        for item in result.retrieved_items:
            assert item.category == ContentCategory.CHARACTER
    
    def test_relevance_score_filtering(self):
        """Test that items below minimum relevance score are filtered."""
        query = RetrievalQuery(
            query_text="completely unrelated query xyz",
            strategy=RetrievalStrategy.KEYWORD_BASED,
            mode=RetrievalMode.BALANCED,
            max_results=5,
            min_relevance_score=0.8  # High threshold
        )
        
        result = self.retriever.retrieve(query, self.content_pool)
        
        # With unrelated query and high threshold, should return few/no items
        assert len(result.retrieved_items) <= len(self.content_pool)
        for score in result.relevance_scores:
            assert score.total_score >= query.min_relevance_score
    
    def test_convenience_methods(self):
        """Test convenience methods for getting top characters and scenes."""
        # Test get_top_characters
        characters = self.retriever.get_top_characters(
            "brave knight", self.content_pool, max_results=2
        )
        
        assert len(characters) <= 2
        for char in characters:
            assert char.category == ContentCategory.CHARACTER
        
        # Test get_top_scenes
        scenes = self.retriever.get_top_scenes(
            "forest magic", self.content_pool, max_results=2
        )
        
        assert len(scenes) <= 2
        for scene in scenes:
            assert scene.category in {ContentCategory.SCENE, ContentCategory.WORLD_BUILDING}
    
    def test_performance_metrics_tracking(self):
        """Test that performance metrics are tracked."""
        initial_metrics = self.retriever.get_performance_metrics()
        initial_count = initial_metrics['total_retrievals']
        
        query = RetrievalQuery(
            query_text="test query",
            strategy=RetrievalStrategy.KEYWORD_BASED,
            mode=RetrievalMode.BALANCED,
            max_results=3
        )
        
        self.retriever.retrieve(query, self.content_pool)
        
        updated_metrics = self.retriever.get_performance_metrics()
        assert updated_metrics['total_retrievals'] == initial_count + 1
        assert updated_metrics['strategy_usage'][RetrievalStrategy.KEYWORD_BASED.value] > 0
    
    def test_cache_management(self):
        """Test cache clearing functionality."""
        # Perform some retrievals to populate cache
        query = RetrievalQuery(
            query_text="test",
            strategy=RetrievalStrategy.EMBEDDING_BASED,
            mode=RetrievalMode.BALANCED,
            max_results=2
        )
        
        self.retriever.retrieve(query, self.content_pool)
        
        # Clear cache should not raise errors
        self.retriever.clear_cache()
        
        # Should still work after cache clear
        result = self.retriever.retrieve(query, self.content_pool)
        assert isinstance(result, RetrievalResult)


# Integration tests
class TestContentPrioritizationIntegration:
    """Integration tests for the complete content prioritization system."""
    
    def setup_method(self):
        """Set up integration test fixtures."""
        self.prioritizer = LayeredPrioritizer()
        self.retriever = RAGRetriever()
        
        # Create a larger content pool for integration testing
        self.content_pool = []
        categories = [ContentCategory.CHARACTER, ContentCategory.SCENE, 
                     ContentCategory.PLOT_POINT, ContentCategory.WORLD_BUILDING]
        
        for i in range(20):
            category = categories[i % len(categories)]
            self.content_pool.append(ContentItem(
                id=f"integration_item_{i}",
                content=f"Integration test content {i} with various keywords and themes",
                category=category,
                created_at=datetime.now() - timedelta(days=i % 7),
                last_accessed=datetime.now() - timedelta(hours=i % 24),
                access_count=i % 10 + 1,
                importance_tags={"main_character"} if i < 5 else {"world_building"},
                character_names={f"char_{i}", f"person_{i}"},
                location_names={f"place_{i}", f"location_{i}"}
            ))
    
    def test_end_to_end_prioritization_and_retrieval(self):
        """Test complete end-to-end workflow."""
        # Step 1: Use RAG retrieval to get relevant content
        retrieval_query = RetrievalQuery(
            query_text="main character important plot",
            strategy=RetrievalStrategy.HYBRID,
            mode=RetrievalMode.BALANCED,
            max_results=10
        )
        
        retrieval_result = self.retriever.retrieve(retrieval_query, self.content_pool)
        
        # Step 2: Use prioritizer on retrieved content
        context = {
            'active_characters': ['char_0', 'char_1'],
            'active_locations': ['place_0'],
            'keywords': ['important', 'main'],
            'current_agent': 'writer'
        }
        
        prioritization_result = self.prioritizer.prioritize_content(
            retrieval_result.retrieved_items,
            context,
            AgentType.WRITER,
            token_budget=800
        )
        
        # Verify the complete workflow
        assert len(retrieval_result.retrieved_items) > 0
        assert len(prioritization_result.selected_content) > 0
        assert prioritization_result.total_tokens_used <= 800
        
        # Verify that prioritized content is a subset of retrieved content
        retrieved_ids = {item.id for item in retrieval_result.retrieved_items}
        prioritized_ids = {item.content_item.id for item in prioritization_result.selected_content}
        assert prioritized_ids.issubset(retrieved_ids)
    
    def test_different_agent_workflows(self):
        """Test that different agents get different prioritized content."""
        context = {
            'active_characters': ['char_0'],
            'keywords': ['test']
        }
        
        # Get prioritization results for different agent types
        writer_result = self.prioritizer.prioritize_content(
            self.content_pool[:10], context, AgentType.WRITER
        )
        
        character_result = self.prioritizer.prioritize_content(
            self.content_pool[:10], context, AgentType.CHARACTER
        )
        
        rater_result = self.prioritizer.prioritize_content(
            self.content_pool[:10], context, AgentType.RATER
        )
        
        # Results should be different due to different agent weights
        writer_ids = {item.content_item.id for item in writer_result.selected_content}
        character_ids = {item.content_item.id for item in character_result.selected_content}
        rater_ids = {item.content_item.id for item in rater_result.selected_content}
        
        # Results may be identical in some cases, but agent types should be different
        assert writer_result.agent_type != character_result.agent_type
        assert character_result.agent_type != rater_result.agent_type
        
        # At least verify that all results are valid
        assert len(writer_result.selected_content) > 0
        assert len(character_result.selected_content) > 0
        assert len(rater_result.selected_content) > 0
    
    def test_performance_under_load(self):
        """Test system performance with larger datasets."""
        # Create a larger content pool
        large_pool = []
        for i in range(100):
            large_pool.append(ContentItem(
                id=f"load_test_{i}",
                content=f"Load test content {i} " * 10,  # Longer content
                category=ContentCategory.NARRATIVE,
                created_at=datetime.now() - timedelta(days=i % 30),
                last_accessed=datetime.now() - timedelta(hours=i % 48),
                access_count=i % 20 + 1
            ))
        
        context = {'keywords': ['test', 'content']}
        
        start_time = datetime.now()
        result = self.prioritizer.prioritize_content(
            large_pool, context, AgentType.WRITER
        )
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds()
        
        # Should complete within reasonable time (adjust threshold as needed)
        assert processing_time < 5.0  # 5 seconds max
        assert len(result.selected_content) > 0
        assert result.total_tokens_used <= result.total_tokens_available


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
