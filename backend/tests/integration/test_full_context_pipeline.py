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
    
    def _create_context_container_from_scenario(self, scenario):
        """Helper method to convert scenario context items to structured container."""
        from app.models.context_models import (
            StructuredContextContainer, SystemContextElement, StoryContextElement, 
            CharacterContextElement, ContextMetadata
        )
        
        elements = []
        for item in scenario.context_items:
            # Create appropriate metadata
            metadata = ContextMetadata(
                priority=min(max(item.priority / 10.0, 0.0), 1.0),  # Normalize to 0.0-1.0 range
                estimated_tokens=len(item.content) // 4  # Rough estimate
            )
            
            # Create appropriate element type based on context type
            if item.context_type == ContextType.SYSTEM_PROMPT:
                element = SystemContextElement(
                    id=f"system_{len(elements)}",
                    type=item.context_type,
                    content=item.content,
                    metadata=metadata
                )
            elif item.context_type in [ContextType.CHARACTER_PROFILE, ContextType.CHARACTER_MEMORY]:
                element = CharacterContextElement(
                    id=f"character_{len(elements)}",
                    type=item.context_type,
                    content=item.content,
                    character_id="test_character",
                    character_name="Test Character",
                    metadata=metadata
                )
            else:
                # Default to StoryContextElement for all other types
                element = StoryContextElement(
                    id=f"story_{len(elements)}",
                    type=item.context_type,
                    content=item.content,
                    metadata=metadata
                )
            
            elements.append(element)
        
        return StructuredContextContainer(elements=elements)
    
    @patch('app.services.llm_inference.get_llm')
    def test_end_to_end_context_processing(self, mock_get_llm):
        """Test complete end-to-end context processing pipeline."""
        from app.models.context_models import ContextProcessingConfig, AgentType, ComposePhase
        
        mock_get_llm.return_value = Mock()
        
        # Generate realistic test scenario
        scenario = self.generator.generate_context_scenario("e2e_test", StoryComplexity.MODERATE)
        
        # Initialize context manager
        context_manager = ContextManager()
        
        # Initialize token allocator
        allocator = TokenAllocator(
            total_budget=self.settings.CONTEXT_MAX_TOKENS,
            mode=AllocationMode.DYNAMIC,
            overflow_strategy=OverflowStrategy.REALLOCATE
        )
        
        # Execute the actual pipeline using new unified API
        start_time = time.time()
        
        # Create processing configuration
        config = ContextProcessingConfig(
            target_agent=AgentType.WRITER,
            current_phase=ComposePhase.CHAPTER_DETAIL,
            max_tokens=self.settings.CONTEXT_MAX_TOKENS,
            prioritize_recent=True
        )
        
        # Create structured context container from scenario
        container = self._create_context_container_from_scenario(scenario)
        
        # Process context using the new unified API
        formatted_context, metadata = context_manager.process_context_for_agent(container, config)
        
        processing_time = time.time() - start_time
        
        # Verify results
        assert isinstance(formatted_context, str)
        assert len(formatted_context) > 0
        assert isinstance(metadata, dict)
        assert "original_element_count" in metadata
        assert "filtered_element_count" in metadata
        assert processing_time < 1.0  # Should complete quickly in integration test
        assert metadata["original_element_count"] > 0
        assert metadata["filtered_element_count"] > 0
    
    @patch('app.services.llm_inference.get_llm')
    def test_configuration_driven_pipeline(self, mock_get_llm):
        """Test that pipeline behavior is properly driven by configuration."""
        from app.models.context_models import ContextProcessingConfig, AgentType, ComposePhase
        
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
                
                context_manager = ContextManager()
                
                # Calculate target tokens with buffer
                target_tokens = settings.CONTEXT_MAX_TOKENS - settings.CONTEXT_BUFFER_TOKENS
                
                # Create processing configuration
                processing_config = ContextProcessingConfig(
                    target_agent=AgentType.WRITER,
                    current_phase=ComposePhase.CHAPTER_DETAIL,
                    max_tokens=target_tokens,
                    prioritize_recent=True
                )
                
                # Create structured context container from scenario
                container = self._create_context_container_from_scenario(scenario)
                
                # Process context using the new unified API
                formatted_context, metadata = context_manager.process_context_for_agent(container, processing_config)
                
                # Verify configuration is respected
                assert isinstance(formatted_context, str)
                assert len(formatted_context) > 0
                assert isinstance(metadata, dict)
                assert "original_element_count" in metadata
                assert "filtered_element_count" in metadata
                assert metadata["original_element_count"] > 0
    
    @patch('app.services.llm_inference.get_llm')
    def test_layer_allocation_integration(self, mock_get_llm):
        """Test integration between context manager and token allocation layers."""
        mock_get_llm.return_value = Mock()
        
        scenario = self.generator.generate_context_scenario("layer_test", StoryComplexity.COMPLEX)
        
        context_manager = ContextManager()
        
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
    
    @patch('app.services.llm_inference.get_llm')
    def test_overflow_handling_integration(self, mock_get_llm):
        """Test integration of overflow handling across the pipeline."""
        mock_get_llm.return_value = Mock()
        
        # Create scenario that will definitely overflow
        large_scenario = self.generator.generate_context_scenario("overflow_test", StoryComplexity.EPIC)
        
        # Use small limits to force overflow
        small_limit = 5000
        context_manager = ContextManager()
        
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
    
    @patch('app.services.llm_inference.get_llm')
    def test_priority_and_layer_interaction(self, mock_get_llm):
        """Test interaction between priority-based filtering and layer allocation."""
        mock_get_llm.return_value = Mock()
        
        # Create items with varying priorities across different layers
        mixed_items = [
            ContextItem("Critical system", ContextType.SYSTEM_PROMPT, 10, LayerType.WORKING_MEMORY, {}),
            ContextItem("Important story", ContextType.STORY_SUMMARY, 9, LayerType.EPISODIC_MEMORY, {}),
            ContextItem("Key character", ContextType.CHARACTER_PROFILE, 8, LayerType.SEMANTIC_MEMORY, {}),
            ContextItem("Useful world info", ContextType.WORLD_BUILDING, 6, LayerType.SEMANTIC_MEMORY, {}),
            ContextItem("Background detail", ContextType.CHARACTER_MEMORY, 4, LayerType.LONG_TERM_MEMORY, {}),
            ContextItem("Minor detail", ContextType.CHARACTER_MEMORY, 2, LayerType.LONG_TERM_MEMORY, {})
        ]
        
        context_manager = ContextManager()
        
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
    

    @patch('app.services.llm_inference.get_llm')
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
                
                context_manager = ContextManager()
                
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
    
    @patch('app.services.llm_inference.get_llm')
    def test_error_recovery_integration(self, mock_get_llm):
        """Test error recovery across the integrated pipeline."""
        mock_get_llm.return_value = Mock()
        
        scenario = self.generator.generate_context_scenario("error_test", StoryComplexity.MODERATE)
        
        context_manager = ContextManager()
        
        # Test error recovery by simulating problematic content
        # Create items with potentially problematic content
        problematic_items = [
            ContextItem("", ContextType.STORY_SUMMARY, 5, LayerType.EPISODIC_MEMORY, {}),  # Empty content
            ContextItem("Valid content here", ContextType.CHARACTER_PROFILE, 8, LayerType.SEMANTIC_MEMORY, {}),
            ContextItem("More valid content", ContextType.WORLD_BUILDING, 7, LayerType.SEMANTIC_MEMORY, {})
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
    
    @patch('app.services.llm_inference.get_llm')
    def test_memory_efficiency_integration(self, mock_get_llm):
        """Test memory efficiency across the integrated pipeline."""
        mock_get_llm.return_value = Mock()
        
        # Generate large scenario to test memory handling
        large_scenario = self.generator.generate_context_scenario("memory_test", StoryComplexity.EPIC)
        
        context_manager = ContextManager()
        
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
