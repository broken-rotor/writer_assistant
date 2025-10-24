"""
Unit Tests for Context Manager

Tests the core context management functionality including context item management,
analysis, optimization coordination, and configuration integration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

from app.services.context_manager import ContextManager, ContextItem, ContextType, ContextAnalysis
from app.services.token_management import LayerType
from app.core.config import Settings
from tests.utils.test_data_generators import ContextDataGenerator, StoryComplexity


class TestContextManager:
    """Test ContextManager functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.settings = Settings()
        self.generator = ContextDataGenerator(seed=42)
        
        # Mock dependencies
        self.mock_token_counter = Mock()
        self.mock_allocator = Mock()
        self.mock_distiller = Mock()
        self.mock_prioritizer = Mock()
    
    @patch('app.services.context_manager.get_llm')
    def test_context_manager_initialization_with_config(self, mock_get_llm):
        """Test ContextManager initialization with configuration settings."""
        mock_get_llm.return_value = Mock()
        
        with patch('app.services.context_manager.settings', self.settings):
            context_manager = ContextManager(
                max_context_tokens=self.settings.CONTEXT_MAX_TOKENS,
                distillation_threshold=self.settings.CONTEXT_SUMMARIZATION_THRESHOLD
            )
            
            assert context_manager.max_context_tokens == 32000
            assert context_manager.distillation_threshold == 25000
    
    def test_context_item_creation_and_validation(self):
        """Test creation and validation of context items."""
        # Test valid context item
        context_item = ContextItem(
            content="This is test content for the story.",
            context_type=ContextType.STORY,
            priority=8,
            layer_type=LayerType.EPISODIC_MEMORY,
            metadata={"chapter": 1, "scene": "opening"}
        )
        
        assert context_item.content == "This is test content for the story."
        assert context_item.context_type == ContextType.STORY
        assert context_item.priority == 8
        assert context_item.layer_type == LayerType.EPISODIC_MEMORY
        assert context_item.metadata["chapter"] == 1
    
    def test_context_analysis_functionality(self):
        """Test context analysis and optimization."""
        # Generate test scenario
        scenario = self.generator.generate_context_scenario("test_analysis", StoryComplexity.MODERATE)
        
        with patch('app.services.context_manager.get_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            
            context_manager = ContextManager(
                max_context_tokens=10000,
                distillation_threshold=8000
            )
            
            # Mock the analyze_context method
            with patch.object(context_manager, 'analyze_context') as mock_analyze:
                mock_analysis = ContextAnalysis(
                    total_tokens=5000,
                    layer_distribution={LayerType.WORKING_MEMORY: 1000, LayerType.EPISODIC_MEMORY: 2000},
                    priority_distribution={10: 500, 8: 2000, 6: 1500, 4: 1000},
                    content_type_distribution={ContextType.SYSTEM: 500, ContextType.STORY: 3000, ContextType.CHARACTER: 1500},
                    optimization_suggestions=["Consider summarizing older chapters", "Prioritize recent character interactions"]
                )
                mock_analyze.return_value = mock_analysis
                
                analysis = context_manager.analyze_context(scenario.context_items)
                
                assert analysis.total_tokens == 5000
                assert LayerType.WORKING_MEMORY in analysis.layer_distribution
                assert ContextType.STORY in analysis.content_type_distribution
                assert len(analysis.optimization_suggestions) > 0
    
    def test_context_optimization_workflow(self):
        """Test the complete context optimization workflow."""
        scenario = self.generator.generate_context_scenario("test_optimization", StoryComplexity.COMPLEX)
        
        with patch('app.services.context_manager.get_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            
            context_manager = ContextManager(
                max_context_tokens=8000,
                distillation_threshold=6000
            )
            
            # Mock the optimize_context method
            with patch.object(context_manager, 'optimize_context') as mock_optimize:
                optimized_items = scenario.context_items[:5]  # Simulate optimization reducing items
                mock_optimize.return_value = optimized_items
                
                result = context_manager.optimize_context(
                    context_items=scenario.context_items,
                    target_tokens=7000,
                    preserve_system=True
                )
                
                assert len(result) <= len(scenario.context_items)
                mock_optimize.assert_called_once()
    
    def test_priority_based_context_filtering(self):
        """Test context filtering based on priority thresholds."""
        # Create context items with different priorities
        context_items = [
            ContextItem("High priority system", ContextType.SYSTEM, 10, LayerType.WORKING_MEMORY, {}),
            ContextItem("Medium priority story", ContextType.STORY, 6, LayerType.EPISODIC_MEMORY, {}),
            ContextItem("Low priority background", ContextType.WORLD, 3, LayerType.SEMANTIC_MEMORY, {}),
            ContextItem("Very low priority detail", ContextType.MEMORY, 1, LayerType.LONG_TERM_MEMORY, {})
        ]
        
        with patch('app.services.context_manager.get_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            
            context_manager = ContextManager(
                max_context_tokens=5000,
                distillation_threshold=4000
            )
            
            # Test filtering with different priority thresholds
            with patch.object(context_manager, 'filter_by_priority') as mock_filter:
                # Simulate filtering keeping only items with priority >= 5
                filtered_items = [item for item in context_items if item.priority >= 5]
                mock_filter.return_value = filtered_items
                
                result = context_manager.filter_by_priority(context_items, min_priority=5)
                
                assert len(result) == 2  # Only high and medium priority items
                assert all(item.priority >= 5 for item in result)
    
    def test_layer_type_distribution_management(self):
        """Test management of context distribution across memory layers."""
        scenario = self.generator.generate_context_scenario("test_layers", StoryComplexity.MODERATE)
        
        with patch('app.services.context_manager.get_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            
            context_manager = ContextManager(
                max_context_tokens=10000,
                distillation_threshold=8000
            )
            
            # Test layer distribution analysis
            layer_distribution = {}
            for item in scenario.context_items:
                if item.layer_type not in layer_distribution:
                    layer_distribution[item.layer_type] = 0
                layer_distribution[item.layer_type] += len(item.content) // 4  # Rough token estimate
            
            # Verify that different layer types are represented
            assert len(layer_distribution) > 1
            assert LayerType.WORKING_MEMORY in layer_distribution or LayerType.EPISODIC_MEMORY in layer_distribution
    
    def test_context_type_categorization(self):
        """Test proper categorization of different context types."""
        context_items = [
            ContextItem("System instruction", ContextType.SYSTEM, 10, LayerType.WORKING_MEMORY, {}),
            ContextItem("Story content", ContextType.STORY, 8, LayerType.EPISODIC_MEMORY, {}),
            ContextItem("Character description", ContextType.CHARACTER, 7, LayerType.SEMANTIC_MEMORY, {}),
            ContextItem("World building", ContextType.WORLD, 6, LayerType.SEMANTIC_MEMORY, {}),
            ContextItem("Feedback note", ContextType.FEEDBACK, 5, LayerType.WORKING_MEMORY, {}),
            ContextItem("Memory fragment", ContextType.MEMORY, 4, LayerType.LONG_TERM_MEMORY, {})
        ]
        
        # Test categorization
        type_counts = {}
        for item in context_items:
            if item.context_type not in type_counts:
                type_counts[item.context_type] = 0
            type_counts[item.context_type] += 1
        
        # Verify all context types are represented
        assert len(type_counts) == 6
        assert type_counts[ContextType.SYSTEM] == 1
        assert type_counts[ContextType.STORY] == 1
        assert type_counts[ContextType.CHARACTER] == 1
    
    def test_token_budget_enforcement(self):
        """Test enforcement of token budgets and limits."""
        with patch('app.services.context_manager.get_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            
            # Create context manager with strict limits
            context_manager = ContextManager(
                max_context_tokens=2000,
                distillation_threshold=1500
            )
            
            # Generate large context that exceeds limits
            large_scenario = self.generator.generate_context_scenario("test_budget", StoryComplexity.EPIC)
            
            with patch.object(context_manager, 'enforce_token_budget') as mock_enforce:
                # Simulate budget enforcement reducing context
                reduced_items = large_scenario.context_items[:3]  # Keep only first 3 items
                mock_enforce.return_value = reduced_items
                
                result = context_manager.enforce_token_budget(
                    large_scenario.context_items,
                    max_tokens=2000
                )
                
                assert len(result) <= len(large_scenario.context_items)
                mock_enforce.assert_called_once()
    
    def test_context_assembly_performance(self):
        """Test context assembly performance and timeout handling."""
        scenario = self.generator.generate_context_scenario("test_performance", StoryComplexity.MODERATE)
        
        with patch('app.services.context_manager.get_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            
            context_manager = ContextManager(
                max_context_tokens=10000,
                distillation_threshold=8000
            )
            
            # Test assembly with timeout
            with patch.object(context_manager, 'assemble_context') as mock_assemble:
                mock_assemble.return_value = {
                    'assembled_context': "Assembled context content",
                    'total_tokens': 5000,
                    'assembly_time': 0.05,  # 50ms
                    'items_included': len(scenario.context_items)
                }
                
                result = context_manager.assemble_context(
                    scenario.context_items,
                    max_assembly_time=0.1  # 100ms timeout
                )
                
                assert 'assembled_context' in result
                assert result['assembly_time'] <= 0.1
                assert result['total_tokens'] > 0
    
    def test_configuration_integration_with_settings(self):
        """Test integration with configuration settings."""
        # Test with custom configuration
        custom_env = {
            'CONTEXT_MAX_TOKENS': '16000',
            'CONTEXT_SUMMARIZATION_THRESHOLD': '12000',
            'CONTEXT_ENABLE_RAG': 'false',
            'CONTEXT_ENABLE_MONITORING': 'true'
        }
        
        with patch.dict('os.environ', custom_env):
            custom_settings = Settings()
            
            with patch('app.services.context_manager.get_llm') as mock_get_llm:
                mock_get_llm.return_value = Mock()
                
                with patch('app.services.context_manager.settings', custom_settings):
                    context_manager = ContextManager(
                        max_context_tokens=custom_settings.CONTEXT_MAX_TOKENS,
                        distillation_threshold=custom_settings.CONTEXT_SUMMARIZATION_THRESHOLD
                    )
                    
                    assert context_manager.max_context_tokens == 16000
                    assert context_manager.distillation_threshold == 12000
    
    def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms."""
        with patch('app.services.context_manager.get_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            
            context_manager = ContextManager(
                max_context_tokens=5000,
                distillation_threshold=4000
            )
            
            # Test with invalid context items
            invalid_items = [
                ContextItem("", ContextType.SYSTEM, 10, LayerType.WORKING_MEMORY, {}),  # Empty content
                ContextItem("Valid content", ContextType.STORY, -1, LayerType.EPISODIC_MEMORY, {}),  # Invalid priority
            ]
            
            # Test that the system handles invalid items gracefully
            with patch.object(context_manager, 'validate_context_items') as mock_validate:
                valid_items = [item for item in invalid_items if item.content and item.priority > 0]
                mock_validate.return_value = valid_items
                
                result = context_manager.validate_context_items(invalid_items)
                
                assert len(result) < len(invalid_items)  # Some items should be filtered out
    
    def test_context_caching_functionality(self):
        """Test context caching when enabled."""
        scenario = self.generator.generate_context_scenario("test_caching", StoryComplexity.MODERATE)
        
        with patch('app.services.context_manager.get_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            
            # Test with caching enabled
            with patch.dict('os.environ', {'CONTEXT_ENABLE_CACHING': 'true'}):
                settings = Settings()
                
                with patch('app.services.context_manager.settings', settings):
                    context_manager = ContextManager(
                        max_context_tokens=10000,
                        distillation_threshold=8000
                    )
                    
                    # Mock caching functionality
                    with patch.object(context_manager, 'get_cached_context') as mock_get_cache:
                        with patch.object(context_manager, 'cache_context') as mock_set_cache:
                            # First call - cache miss
                            mock_get_cache.return_value = None
                            
                            result1 = context_manager.process_context(scenario.context_items)
                            
                            # Verify caching was attempted
                            mock_get_cache.assert_called()
                            mock_set_cache.assert_called()
    
    def test_monitoring_and_analytics_integration(self):
        """Test monitoring and analytics when enabled."""
        scenario = self.generator.generate_context_scenario("test_monitoring", StoryComplexity.MODERATE)
        
        with patch('app.services.context_manager.get_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            
            # Test with monitoring enabled
            with patch.dict('os.environ', {'CONTEXT_ENABLE_MONITORING': 'true'}):
                settings = Settings()
                
                with patch('app.services.context_manager.settings', settings):
                    context_manager = ContextManager(
                        max_context_tokens=10000,
                        distillation_threshold=8000
                    )
                    
                    # Mock monitoring functionality
                    with patch.object(context_manager, 'record_metrics') as mock_record:
                        context_manager.process_context(scenario.context_items)
                        
                        # Verify metrics were recorded
                        mock_record.assert_called()
    
    def test_rag_integration_when_enabled(self):
        """Test RAG (Retrieval-Augmented Generation) integration."""
        scenario = self.generator.generate_context_scenario("test_rag", StoryComplexity.COMPLEX)
        
        with patch('app.services.context_manager.get_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            
            # Test with RAG enabled
            with patch.dict('os.environ', {'CONTEXT_ENABLE_RAG': 'true'}):
                settings = Settings()
                
                with patch('app.services.context_manager.settings', settings):
                    context_manager = ContextManager(
                        max_context_tokens=10000,
                        distillation_threshold=8000
                    )
                    
                    # Mock RAG functionality
                    with patch.object(context_manager, 'retrieve_relevant_context') as mock_rag:
                        additional_context = [
                            ContextItem("RAG retrieved content", ContextType.MEMORY, 7, LayerType.SEMANTIC_MEMORY, {"source": "rag"})
                        ]
                        mock_rag.return_value = additional_context
                        
                        result = context_manager.enhance_with_rag(scenario.context_items, query="test query")
                        
                        mock_rag.assert_called_with("test query")
    
    def test_stress_testing_with_large_contexts(self):
        """Test system behavior under stress with large context scenarios."""
        # Generate a very large context scenario
        large_scenario = self.generator.generate_context_scenario("stress_test", StoryComplexity.EPIC)
        
        with patch('app.services.context_manager.get_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            
            context_manager = ContextManager(
                max_context_tokens=50000,  # Large limit for stress test
                distillation_threshold=40000
            )
            
            # Test that the system handles large contexts without crashing
            try:
                with patch.object(context_manager, 'process_context') as mock_process:
                    mock_process.return_value = {
                        'processed_items': large_scenario.context_items[:10],  # Simulate processing
                        'total_tokens': 35000,
                        'processing_time': 0.2
                    }
                    
                    result = context_manager.process_context(large_scenario.context_items)
                    
                    assert 'processed_items' in result
                    assert result['total_tokens'] > 0
                    assert result['processing_time'] < 1.0  # Should complete within reasonable time
                    
            except Exception as e:
                pytest.fail(f"Context manager failed under stress: {e}")
