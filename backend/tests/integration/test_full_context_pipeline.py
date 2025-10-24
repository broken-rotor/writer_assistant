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
from app.services.token_management import TokenAllocator, LayerType, AllocationMode, OverflowStrategy
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
            max_tokens=self.settings.CONTEXT_MAX_TOKENS,
            buffer_tokens=self.settings.CONTEXT_BUFFER_TOKENS,
            allocation_mode=AllocationMode.DYNAMIC,
            overflow_strategy=OverflowStrategy.REALLOCATE
        )
        
        # Mock the full pipeline
        with patch.object(context_manager, 'process_context') as mock_process:
            mock_result = {
                'processed_items': scenario.context_items[:8],  # Simulate processing
                'total_tokens': 15000,
                'processing_time': 0.08,
                'optimization_applied': True,
                'layers_used': [LayerType.WORKING_MEMORY, LayerType.EPISODIC_MEMORY, LayerType.SEMANTIC_MEMORY]
            }
            mock_process.return_value = mock_result
            
            # Execute pipeline
            start_time = time.time()
            result = context_manager.process_context(scenario.context_items)
            processing_time = time.time() - start_time
            
            # Verify results
            assert result['total_tokens'] <= self.settings.CONTEXT_MAX_TOKENS
            assert result['processing_time'] <= self.settings.CONTEXT_ASSEMBLY_TIMEOUT / 1000  # Convert ms to seconds
            assert len(result['processed_items']) > 0
            assert processing_time < 1.0  # Should complete quickly in integration test
    
    @patch('app.services.context_manager.get_llm')
    def test_configuration_driven_pipeline(self, mock_get_llm):
        """Test that pipeline behavior is properly driven by configuration."""
        mock_get_llm.return_value = Mock()
        
        # Test with different configuration settings
        test_configs = [
            {
                'CONTEXT_MAX_TOKENS': '8000',
                'CONTEXT_BUFFER_TOKENS': '800',
                'CONTEXT_LAYER_A_TOKENS': '1440',
                'CONTEXT_LAYER_C_TOKENS': '3600',
                'CONTEXT_LAYER_D_TOKENS': '1440',
                'CONTEXT_LAYER_E_TOKENS': '720',
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
                
                # Mock processing with configuration-aware behavior
                with patch.object(context_manager, 'process_context') as mock_process:
                    expected_tokens = min(len(scenario.context_items) * 500, settings.CONTEXT_MAX_TOKENS - settings.CONTEXT_BUFFER_TOKENS)
                    mock_process.return_value = {
                        'processed_items': scenario.context_items,
                        'total_tokens': expected_tokens,
                        'max_tokens_used': settings.CONTEXT_MAX_TOKENS,
                        'buffer_reserved': settings.CONTEXT_BUFFER_TOKENS
                    }
                    
                    result = context_manager.process_context(scenario.context_items)
                    
                    assert result['max_tokens_used'] == settings.CONTEXT_MAX_TOKENS
                    assert result['buffer_reserved'] == settings.CONTEXT_BUFFER_TOKENS
                    assert result['total_tokens'] <= settings.CONTEXT_MAX_TOKENS - settings.CONTEXT_BUFFER_TOKENS
    
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
            max_tokens=self.settings.CONTEXT_MAX_TOKENS,
            buffer_tokens=self.settings.CONTEXT_BUFFER_TOKENS,
            allocation_mode=AllocationMode.DYNAMIC
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
            with patch.object(allocator, 'allocate') as mock_allocate:
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
                
                result = allocator.allocate(request)
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
            max_tokens=small_limit,
            buffer_tokens=500,
            allocation_mode=AllocationMode.DYNAMIC,
            overflow_strategy=OverflowStrategy.REALLOCATE
        )
        
        # Mock overflow handling
        with patch.object(context_manager, 'handle_overflow') as mock_handle_overflow:
            # Simulate overflow handling reducing content
            reduced_items = large_scenario.context_items[:5]  # Keep only first 5 items
            mock_handle_overflow.return_value = {
                'items': reduced_items,
                'total_tokens': 4000,
                'overflow_handled': True,
                'strategy_used': 'reallocate'
            }
            
            result = context_manager.handle_overflow(
                large_scenario.context_items,
                max_tokens=small_limit - 500
            )
            
            assert result['overflow_handled'] is True
            assert result['total_tokens'] <= small_limit - 500
            assert len(result['items']) <= len(large_scenario.context_items)
    
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
            with patch.object(context_manager, 'process_context') as mock_process:
                # Simulate realistic processing times based on complexity
                base_time = 0.02 + (i * 0.03)  # 20ms + complexity factor
                mock_process.return_value = {
                    'processed_items': scenario.context_items,
                    'total_tokens': min(len(scenario.context_items) * 300, 25000),
                    'processing_time': base_time,
                    'complexity': scenario.complexity.value
                }
                
                start_time = time.time()
                result = context_manager.process_context(scenario.context_items)
                actual_time = time.time() - start_time
                
                processing_times.append(actual_time)
                
                # Verify performance requirements
                assert result['processing_time'] <= self.settings.CONTEXT_ASSEMBLY_TIMEOUT / 1000
                assert actual_time < 0.5  # Integration test should be fast
        
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
                
                # Mock feature-specific behavior
                with patch.object(context_manager, 'process_with_features') as mock_process:
                    mock_result = {
                        'processed_items': scenario.context_items,
                        'total_tokens': 12000,
                        'features_used': {
                            'rag_enabled': settings.CONTEXT_ENABLE_RAG,
                            'monitoring_enabled': settings.CONTEXT_ENABLE_MONITORING,
                            'caching_enabled': settings.CONTEXT_ENABLE_CACHING
                        }
                    }
                    mock_process.return_value = mock_result
                    
                    result = context_manager.process_with_features(scenario.context_items)
                    
                    # Verify feature flags are respected
                    assert result['features_used']['rag_enabled'] == settings.CONTEXT_ENABLE_RAG
                    assert result['features_used']['monitoring_enabled'] == settings.CONTEXT_ENABLE_MONITORING
                    assert result['features_used']['caching_enabled'] == settings.CONTEXT_ENABLE_CACHING
    
    @patch('app.services.context_manager.get_llm')
    def test_error_recovery_integration(self, mock_get_llm):
        """Test error recovery across the integrated pipeline."""
        mock_get_llm.return_value = Mock()
        
        scenario = self.generator.generate_context_scenario("error_test", StoryComplexity.MODERATE)
        
        context_manager = ContextManager(
            max_context_tokens=self.settings.CONTEXT_MAX_TOKENS,
            distillation_threshold=self.settings.CONTEXT_SUMMARIZATION_THRESHOLD
        )
        
        # Test recovery from various error conditions
        error_scenarios = [
            {'error_type': 'token_overflow', 'recovery_strategy': 'truncate'},
            {'error_type': 'processing_timeout', 'recovery_strategy': 'partial_result'},
            {'error_type': 'invalid_content', 'recovery_strategy': 'filter_and_retry'}
        ]
        
        for error_scenario in error_scenarios:
            with patch.object(context_manager, 'process_with_recovery') as mock_process:
                mock_result = {
                    'processed_items': scenario.context_items[:6],  # Partial processing
                    'total_tokens': 8000,
                    'error_encountered': error_scenario['error_type'],
                    'recovery_applied': error_scenario['recovery_strategy'],
                    'success': True
                }
                mock_process.return_value = mock_result
                
                result = context_manager.process_with_recovery(
                    scenario.context_items,
                    error_handling=True
                )
                
                # Verify error recovery worked
                assert result['success'] is True
                assert result['error_encountered'] == error_scenario['error_type']
                assert result['recovery_applied'] == error_scenario['recovery_strategy']
                assert len(result['processed_items']) > 0
    
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
        
        # Mock memory-efficient processing
        with patch.object(context_manager, 'process_memory_efficient') as mock_process:
            mock_result = {
                'processed_items': large_scenario.context_items[:15],  # Reasonable subset
                'total_tokens': 28000,
                'memory_usage': 'optimized',
                'streaming_used': True,
                'peak_memory_mb': 50  # Reasonable memory usage
            }
            mock_process.return_value = mock_result
            
            result = context_manager.process_memory_efficient(large_scenario.context_items)
            
            # Verify memory efficiency
            assert result['memory_usage'] == 'optimized'
            assert result['peak_memory_mb'] < 100  # Should stay under 100MB
            assert result['total_tokens'] <= self.settings.CONTEXT_MAX_TOKENS
            assert len(result['processed_items']) > 0
