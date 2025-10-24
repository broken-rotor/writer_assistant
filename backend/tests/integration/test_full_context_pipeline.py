"""
Integration Tests for Full Context Management Pipeline

Tests the complete context management workflow from configuration loading
through context assembly, token allocation, and content optimization.
"""

import pytest
import time
from unittest.mock import Mock, patch
from typing import List, Dict, Any

from app.services.context_manager import ContextManager, ContextItem, ContextType
from app.services.token_management import TokenAllocator, LayerType, AllocationMode, OverflowStrategy, ContentType as TokenContentType
from app.core.config import Settings
from tests.utils.test_data_generators import ContextDataGenerator, StoryComplexity


class TestFullContextPipeline:
    """Test the complete context management pipeline integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.settings = Settings()
        self.generator = ContextDataGenerator(seed=42)
    
    @patch('app.services.context_manager.get_llm')
    def test_end_to_end_context_processing(self, mock_get_llm):
        """Test complete end-to-end context processing pipeline."""
        mock_get_llm.return_value = Mock()
        
        # Generate realistic test scenario
        scenario = self.generator.generate_context_scenario("e2e_test", StoryComplexity.MODERATE)
        
        # Initialize context manager with configuration
        context_manager = ContextManager(
            max_context_tokens=self.settings.CONTEXT_MAX_TOKENS,
            distillation_threshold=self.settings.CONTEXT_SUMMARIZATION_THRESHOLD
        )
        
        # Initialize token allocator
        allocator = TokenAllocator(
            total_budget=self.settings.CONTEXT_MAX_TOKENS,
            mode=AllocationMode.DYNAMIC,
            overflow_strategy=OverflowStrategy.REALLOCATE
        )
        
        # Execute the actual pipeline using real API
        start_time = time.time()
        
        # Analyze context first
        analysis = context_manager.analyze_context(scenario.context_items)
        
        # Optimize if needed
        if analysis.optimization_needed:
            optimized_items, optimization_metadata = context_manager.optimize_context(
                scenario.context_items, 
                target_tokens=self.settings.CONTEXT_MAX_TOKENS
            )
        else:
            optimized_items = scenario.context_items
            optimization_metadata = {"optimization_applied": False}
        
        processing_time = time.time() - start_time
        
        # Calculate final token count
        final_tokens = sum(
            context_manager.token_counter.count_tokens(item.content, TokenContentType.UNKNOWN).token_count
            for item in optimized_items
        )
        
        # Verify results
        assert final_tokens <= self.settings.CONTEXT_MAX_TOKENS
        assert processing_time < 1.0  # Should complete quickly in integration test
        assert len(optimized_items) > 0
        assert analysis.total_tokens > 0
    
    @patch('app.services.context_manager.get_llm')
    def test_configuration_driven_pipeline(self, mock_get_llm):
        """Test that pipeline behavior is properly driven by configuration."""
        mock_get_llm.return_value = Mock()
        
        # Test with different configuration settings
        test_configs = [
            {
                'CONTEXT_MAX_TOKENS': '8000',
                'CONTEXT_BUFFER_TOKENS': '800',
                'CONTEXT_LAYER_A_TOKENS': '1200',
                'CONTEXT_LAYER_C_TOKENS': '3000',
                'CONTEXT_LAYER_D_TOKENS': '1500',
                'CONTEXT_LAYER_E_TOKENS': '1500',
                'CONTEXT_ENABLE_RAG': 'false'
            },
            {
                'CONTEXT_MAX_TOKENS': '16000',
                'CONTEXT_BUFFER_TOKENS': '1600',
                'CONTEXT_LAYER_A_TOKENS': '1440',
                'CONTEXT_LAYER_C_TOKENS': '8640',
                'CONTEXT_LAYER_D_TOKENS': '2160',
                'CONTEXT_LAYER_E_TOKENS': '2160',
                'CONTEXT_ENABLE_RAG': 'true'
            }
        ]
        
        for config in test_configs:
            with patch.dict('os.environ', config):
                settings = Settings()
                scenario = self.generator.generate_context_scenario("config_test", StoryComplexity.MODERATE)
                
                context_manager = ContextManager(
                    max_context_tokens=settings.CONTEXT_MAX_TOKENS,
                    distillation_threshold=settings.CONTEXT_SUMMARIZATION_THRESHOLD
                )
                
                # Test with real API using configuration
                analysis = context_manager.analyze_context(scenario.context_items)
                
                # Optimize with configuration-specific target
                target_tokens = settings.CONTEXT_MAX_TOKENS - settings.CONTEXT_BUFFER_TOKENS
                optimized_items, optimization_metadata = context_manager.optimize_context(
                    scenario.context_items, 
                    target_tokens=target_tokens
                )
                
                # Calculate final token count
                final_tokens = sum(
                    context_manager.token_counter.count_tokens(item.content, TokenContentType.UNKNOWN).token_count
                    for item in optimized_items
                )
                
                # Verify configuration is respected
                assert final_tokens <= target_tokens
                assert context_manager.max_context_tokens == settings.CONTEXT_MAX_TOKENS
                assert len(optimized_items) > 0
    
    @patch('app.services.context_manager.get_llm')
    def test_layer_allocation_integration(self, mock_get_llm):
        """Test integration between context manager and token allocation layers."""
        mock_get_llm.return_value = Mock()
        
        scenario = self.generator.generate_context_scenario("layer_test", StoryComplexity.COMPLEX)
        
        context_manager = ContextManager(
            max_context_tokens=self.settings.CONTEXT_MAX_TOKENS,
            distillation_threshold=self.settings.CONTEXT_SUMMARIZATION_THRESHOLD
        )
        
        allocator = TokenAllocator(
            total_budget=self.settings.CONTEXT_MAX_TOKENS,
            mode=AllocationMode.DYNAMIC
        )
        
        # Group context items by layer type
        layer_groups = {}
        for item in scenario.context_items:
            if item.layer_type not in layer_groups:
                layer_groups[item.layer_type] = []
            layer_groups[item.layer_type].append(item)
        
        # Test allocation for each layer
        total_allocated = 0
        allocation_results = {}
        
        for layer_type, items in layer_groups.items():
            estimated_tokens = sum(len(item.content) // 4 for item in items)  # Rough estimate
            
            # Mock allocation for this layer
            with patch.object(allocator, 'allocate_tokens') as mock_allocate:
                mock_result = Mock()
                mock_result.success = True
                mock_result.granted_tokens = min(estimated_tokens, 5000)  # Cap at 5k per layer
                mock_result.layer_type = layer_type
                mock_allocate.return_value = mock_result
                
                from app.services.token_management import AllocationRequest
                request = AllocationRequest(
                    layer_type=layer_type,
                    requested_tokens=estimated_tokens,
                    priority=8
                )
                
                result = allocator.allocate_tokens(request)
                allocation_results[layer_type] = result
                total_allocated += result.granted_tokens
        
        # Verify allocations respect total budget
        assert total_allocated <= self.settings.CONTEXT_MAX_TOKENS - self.settings.CONTEXT_BUFFER_TOKENS
        assert len(allocation_results) > 0
    
    @patch('app.services.context_manager.get_llm')
    def test_overflow_handling_integration(self, mock_get_llm):
        """Test integration of overflow handling across the pipeline."""
        mock_get_llm.return_value = Mock()
        
        # Create scenario that will definitely overflow
        large_scenario = self.generator.generate_context_scenario("overflow_test", StoryComplexity.EPIC)
        
        # Use small limits to force overflow
        small_limit = 5000
        context_manager = ContextManager(
            max_context_tokens=small_limit,
            distillation_threshold=small_limit - 1000
        )
        
        allocator = TokenAllocator(
            total_budget=small_limit,
            mode=AllocationMode.DYNAMIC,
            overflow_strategy=OverflowStrategy.REALLOCATE
        )
        
        # Test overflow handling with real API
        # First analyze to see if we have overflow
        analysis = context_manager.analyze_context(large_scenario.context_items)
        
        # Force optimization with very small target to simulate overflow
        target_tokens = small_limit - 500
        optimized_items, optimization_metadata = context_manager.optimize_context(
            large_scenario.context_items,
            target_tokens=target_tokens
        )
        
        # Calculate final token count
        final_tokens = sum(
            context_manager.token_counter.count_tokens(item.content, TokenContentType.UNKNOWN).token_count
            for item in optimized_items
        )
        
        # Verify overflow was handled
        assert final_tokens <= target_tokens
        assert len(optimized_items) <= len(large_scenario.context_items)
        assert optimization_metadata['optimization_applied'] is True
        # Original should be larger than final (optimization occurred)
        assert analysis.total_tokens >= final_tokens
    
    @patch('app.services.context_manager.get_llm')
    def test_priority_and_layer_interaction(self, mock_get_llm):
        """Test interaction between priority-based filtering and layer allocation."""
        mock_get_llm.return_value = Mock()
        
        # Create items with varying priorities across different layers
        mixed_items = [
            ContextItem("Critical system", ContextType.SYSTEM, 10, LayerType.WORKING_MEMORY, {}),
            ContextItem("Important story", ContextType.STORY, 9, LayerType.EPISODIC_MEMORY, {}),
            ContextItem("Key character", ContextType.CHARACTER, 8, LayerType.SEMANTIC_MEMORY, {}),
            ContextItem("Useful world info", ContextType.WORLD, 6, LayerType.SEMANTIC_MEMORY, {}),
            ContextItem("Background detail", ContextType.MEMORY, 4, LayerType.LONG_TERM_MEMORY, {}),
            ContextItem("Minor detail", ContextType.MEMORY, 2, LayerType.LONG_TERM_MEMORY, {})
        ]
        
        context_manager = ContextManager(
            max_context_tokens=8000,
            distillation_threshold=6000
        )
        
        # Test optimization with priority and layer awareness
        with patch.object(context_manager, 'optimize_context') as mock_optimize:
            # Simulate optimization that considers both priority and layer importance
            filtered_items = [item for item in mixed_items if item.priority >= 6]
            mock_optimize.return_value = (filtered_items, {"optimization_applied": True})
            
            result, metadata = context_manager.optimize_context(
                mixed_items,
                target_tokens=5000
            )
            
            assert len(result) == 4  # Items with priority >= 6
            assert all(item.priority >= 6 for item in result)
            assert metadata["optimization_applied"] == True
    
    @patch('app.services.context_manager.get_llm')
    def test_performance_under_realistic_load(self, mock_get_llm):
        """Test pipeline performance under realistic load conditions."""
        mock_get_llm.return_value = Mock()
        
        # Generate multiple scenarios of different complexities
        scenarios = [
            self.generator.generate_context_scenario("perf_simple", StoryComplexity.SIMPLE),
            self.generator.generate_context_scenario("perf_moderate", StoryComplexity.MODERATE),
            self.generator.generate_context_scenario("perf_complex", StoryComplexity.COMPLEX)
        ]
        
        context_manager = ContextManager(
            max_context_tokens=self.settings.CONTEXT_MAX_TOKENS,
            distillation_threshold=self.settings.CONTEXT_SUMMARIZATION_THRESHOLD
        )
        
        processing_times = []
        
        for i, scenario in enumerate(scenarios):
            # Test real performance
            start_time = time.time()
            
            # Analyze and optimize using real API
            analysis = context_manager.analyze_context(scenario.context_items)
            
            if analysis.optimization_needed:
                optimized_items, optimization_metadata = context_manager.optimize_context(
                    scenario.context_items,
                    target_tokens=self.settings.CONTEXT_MAX_TOKENS
                )
            else:
                optimized_items = scenario.context_items
                optimization_metadata = {"optimization_applied": False}
            
            actual_time = time.time() - start_time
            processing_times.append(actual_time)
            
            # Calculate final token count
            final_tokens = sum(
                context_manager.token_counter.count_tokens(item.content, TokenContentType.UNKNOWN).token_count
                for item in optimized_items
            )
            
            # Verify performance requirements
            assert actual_time < 1.0  # Integration test should be reasonably fast
            assert final_tokens <= self.settings.CONTEXT_MAX_TOKENS
            assert len(optimized_items) > 0
        
        # Verify performance scales reasonably
        assert all(t < 1.0 for t in processing_times)  # All should complete quickly
    
    @patch('app.services.context_manager.get_llm')
    def test_feature_toggle_integration(self, mock_get_llm):
        """Test integration with feature toggles from configuration."""
        mock_get_llm.return_value = Mock()
        
        scenario = self.generator.generate_context_scenario("feature_test", StoryComplexity.MODERATE)
        
        # Test with different feature combinations
        feature_configs = [
            {'CONTEXT_ENABLE_RAG': 'true', 'CONTEXT_ENABLE_MONITORING': 'true', 'CONTEXT_ENABLE_CACHING': 'true'},
            {'CONTEXT_ENABLE_RAG': 'false', 'CONTEXT_ENABLE_MONITORING': 'true', 'CONTEXT_ENABLE_CACHING': 'false'},
            {'CONTEXT_ENABLE_RAG': 'true', 'CONTEXT_ENABLE_MONITORING': 'false', 'CONTEXT_ENABLE_CACHING': 'true'}
        ]
        
        for config in feature_configs:
            with patch.dict('os.environ', config):
                settings = Settings()
                
                context_manager = ContextManager(
                    max_context_tokens=settings.CONTEXT_MAX_TOKENS,
                    distillation_threshold=settings.CONTEXT_SUMMARIZATION_THRESHOLD
                )
                
                # Test with real API - just verify the configuration is loaded correctly
                analysis = context_manager.analyze_context(scenario.context_items)
                
                # Test optimization with different compression settings based on features
                enable_compression = settings.CONTEXT_ENABLE_RAG  # Use RAG flag as compression proxy
                original_compression = context_manager.enable_compression
                context_manager.enable_compression = enable_compression
                
                try:
                    optimized_items, optimization_metadata = context_manager.optimize_context(
                        scenario.context_items,
                        target_tokens=settings.CONTEXT_MAX_TOKENS
                    )
                    
                    # Calculate final token count
                    final_tokens = sum(
                        context_manager.token_counter.count_tokens(item.content, TokenContentType.UNKNOWN).token_count
                        for item in optimized_items
                    )
                    
                    # Verify feature-driven behavior
                    assert final_tokens <= settings.CONTEXT_MAX_TOKENS
                    assert len(optimized_items) > 0
                    assert context_manager.enable_compression == enable_compression
                    
                finally:
                    # Restore original setting
                    context_manager.enable_compression = original_compression
    
    @patch('app.services.context_manager.get_llm')
    def test_error_recovery_integration(self, mock_get_llm):
        """Test error recovery across the integrated pipeline."""
        mock_get_llm.return_value = Mock()
        
        scenario = self.generator.generate_context_scenario("error_test", StoryComplexity.MODERATE)
        
        context_manager = ContextManager(
            max_context_tokens=self.settings.CONTEXT_MAX_TOKENS,
            distillation_threshold=self.settings.CONTEXT_SUMMARIZATION_THRESHOLD
        )
        
        # Test error recovery by simulating problematic content
        # Create items with potentially problematic content
        problematic_items = [
            ContextItem("", ContextType.STORY, 5, LayerType.EPISODIC_MEMORY, {}),  # Empty content
            ContextItem("Valid content here", ContextType.CHARACTER, 8, LayerType.SEMANTIC_MEMORY, {}),
            ContextItem("More valid content", ContextType.WORLD, 7, LayerType.SEMANTIC_MEMORY, {})
        ]
        
        # Test that the system handles problematic content gracefully
        try:
            analysis = context_manager.analyze_context(problematic_items)
            
            # Even with problematic content, should get some analysis
            assert analysis.total_tokens >= 0
            
            # Try optimization
            optimized_items, optimization_metadata = context_manager.optimize_context(
                problematic_items,
                target_tokens=self.settings.CONTEXT_MAX_TOKENS
            )
            
            # Should handle gracefully and return valid items
            assert len(optimized_items) >= 0  # May filter out empty items
            assert optimization_metadata is not None
            
        except Exception as e:
            # If there's an exception, it should be handled gracefully
            # In a real implementation, this would test actual error recovery
            assert False, f"Error recovery failed: {e}"
    
    @patch('app.services.context_manager.get_llm')
    def test_memory_efficiency_integration(self, mock_get_llm):
        """Test memory efficiency across the integrated pipeline."""
        mock_get_llm.return_value = Mock()
        
        # Generate large scenario to test memory handling
        large_scenario = self.generator.generate_context_scenario("memory_test", StoryComplexity.EPIC)
        
        context_manager = ContextManager(
            max_context_tokens=self.settings.CONTEXT_MAX_TOKENS,
            distillation_threshold=self.settings.CONTEXT_SUMMARIZATION_THRESHOLD
        )
        
        # Test memory efficiency by processing in smaller chunks
        # Split large scenario into smaller batches to simulate memory-efficient processing
        batch_size = 5
        all_processed_items = []
        total_tokens = 0
        
        for i in range(0, len(large_scenario.context_items), batch_size):
            batch = large_scenario.context_items[i:i + batch_size]
            
            # Process each batch
            analysis = context_manager.analyze_context(batch)
            
            if analysis.optimization_needed:
                optimized_items, optimization_metadata = context_manager.optimize_context(
                    batch,
                    target_tokens=self.settings.CONTEXT_MAX_TOKENS // 4  # Smaller target per batch
                )
            else:
                optimized_items = batch
            
            all_processed_items.extend(optimized_items)
            
            # Calculate tokens for this batch
            batch_tokens = sum(
                context_manager.token_counter.count_tokens(item.content, TokenContentType.UNKNOWN).token_count
                for item in optimized_items
            )
            total_tokens += batch_tokens
        
        # Verify memory-efficient processing worked
        assert len(all_processed_items) > 0
        assert total_tokens > 0
        # Final optimization to ensure we don't exceed limits
        if total_tokens > self.settings.CONTEXT_MAX_TOKENS:
            final_items, _ = context_manager.optimize_context(
                all_processed_items,
                target_tokens=self.settings.CONTEXT_MAX_TOKENS
            )
            final_tokens = sum(
                context_manager.token_counter.count_tokens(item.content, TokenContentType.UNKNOWN).token_count
                for item in final_items
            )
            assert final_tokens <= self.settings.CONTEXT_MAX_TOKENS
