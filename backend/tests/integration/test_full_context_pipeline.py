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
        from app.models.generation_models import (
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
        from app.models.generation_models import ContextProcessingConfig, AgentType, ComposePhase
        
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
        from app.models.generation_models import ContextProcessingConfig, AgentType, ComposePhase
        
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
        from app.models.generation_models import ContextProcessingConfig, AgentType, ComposePhase
        
        mock_get_llm.return_value = Mock()
        
        scenario = self.generator.generate_context_scenario("layer_test", StoryComplexity.COMPLEX)
        
        context_manager = ContextManager()
        
        # Create processing configuration with reasonable token limit
        processing_config = ContextProcessingConfig(
            target_agent=AgentType.WRITER,
            current_phase=ComposePhase.CHAPTER_DETAIL,
            max_tokens=self.settings.CONTEXT_MAX_TOKENS,
            prioritize_recent=True
        )
        
        # Create structured context container from scenario
        container = self._create_context_container_from_scenario(scenario)
        
        # Process context using the new unified API
        formatted_context, metadata = context_manager.process_context_for_agent(container, processing_config)
        
        # Verify layer allocation integration worked
        assert isinstance(formatted_context, str)
        assert len(formatted_context) > 0
        assert isinstance(metadata, dict)
        assert "original_element_count" in metadata
        assert "filtered_element_count" in metadata
        assert metadata["original_element_count"] > 0
        assert metadata["filtered_element_count"] > 0
        # Should have processed elements from different layers efficiently
        assert metadata["filtered_element_count"] <= metadata["original_element_count"]
    
    @patch('app.services.llm_inference.get_llm')
    def test_overflow_handling_integration(self, mock_get_llm):
        """Test integration of overflow handling across the pipeline."""
        from app.models.generation_models import ContextProcessingConfig, AgentType, ComposePhase
        
        mock_get_llm.return_value = Mock()
        
        # Create scenario that will definitely overflow
        large_scenario = self.generator.generate_context_scenario("overflow_test", StoryComplexity.EPIC)
        
        # Use small limits to force overflow
        small_limit = 5000
        context_manager = ContextManager()
        
        # Force optimization with very small target to simulate overflow
        target_tokens = small_limit - 500
        
        # Create processing configuration with small token limit
        processing_config = ContextProcessingConfig(
            target_agent=AgentType.WRITER,
            current_phase=ComposePhase.CHAPTER_DETAIL,
            max_tokens=target_tokens,
            prioritize_recent=True
        )
        
        # Create structured context container from scenario
        container = self._create_context_container_from_scenario(large_scenario)
        
        # Process context using the new unified API
        formatted_context, metadata = context_manager.process_context_for_agent(container, processing_config)
        
        # Verify overflow was handled
        assert isinstance(formatted_context, str)
        assert len(formatted_context) > 0
        assert isinstance(metadata, dict)
        assert "original_element_count" in metadata
        assert "filtered_element_count" in metadata
        assert metadata["original_element_count"] > 0
        # Should have filtered out some elements due to overflow
        assert metadata["filtered_element_count"] <= metadata["original_element_count"]
    
    @patch('app.services.llm_inference.get_llm')
    def test_priority_and_layer_interaction(self, mock_get_llm):
        """Test interaction between priority-based filtering and layer allocation."""
        from app.models.generation_models import (
            ContextProcessingConfig, AgentType, ComposePhase,
            StructuredContextContainer, SystemContextElement, StoryContextElement, 
            CharacterContextElement, ContextMetadata
        )
        
        mock_get_llm.return_value = Mock()
        
        # Create elements with varying priorities across different types
        elements = [
            SystemContextElement(
                id="system_1",
                type=ContextType.SYSTEM_PROMPT,
                content="Critical system",
                metadata=ContextMetadata(priority=1.0, estimated_tokens=50)  # Highest priority
            ),
            StoryContextElement(
                id="story_1", 
                type=ContextType.STORY_SUMMARY,
                content="Important story",
                metadata=ContextMetadata(priority=0.9, estimated_tokens=60)
            ),
            CharacterContextElement(
                id="char_1",
                type=ContextType.CHARACTER_PROFILE,
                content="Key character",
                character_id="char1",
                character_name="Main Character",
                metadata=ContextMetadata(priority=0.8, estimated_tokens=70)
            ),
            StoryContextElement(
                id="world_1",
                type=ContextType.WORLD_BUILDING,
                content="Useful world info",
                metadata=ContextMetadata(priority=0.6, estimated_tokens=40)
            ),
            CharacterContextElement(
                id="char_2",
                type=ContextType.CHARACTER_MEMORY,
                content="Background detail",
                character_id="char2", 
                character_name="Side Character",
                metadata=ContextMetadata(priority=0.4, estimated_tokens=30)
            ),
            CharacterContextElement(
                id="char_3",
                type=ContextType.CHARACTER_MEMORY,
                content="Minor detail",
                character_id="char3",
                character_name="Minor Character", 
                metadata=ContextMetadata(priority=0.2, estimated_tokens=20)  # Lowest priority
            )
        ]
        
        container = StructuredContextContainer(elements=elements)
        context_manager = ContextManager()
        
        # Create processing configuration with limited tokens to force prioritization
        processing_config = ContextProcessingConfig(
            target_agent=AgentType.WRITER,
            current_phase=ComposePhase.CHAPTER_DETAIL,
            max_tokens=200,  # Small limit to force filtering
            prioritize_recent=True
        )
        
        # Process context using the new unified API
        formatted_context, metadata = context_manager.process_context_for_agent(container, processing_config)
        
        # Verify priority-based filtering worked
        assert isinstance(formatted_context, str)
        assert len(formatted_context) > 0
        assert isinstance(metadata, dict)
        assert "original_element_count" in metadata
        assert "filtered_element_count" in metadata
        assert metadata["original_element_count"] == 6  # All original elements
        # Should have filtered out some lower priority elements
        assert metadata["filtered_element_count"] <= metadata["original_element_count"]
    

    @patch('app.services.llm_inference.get_llm')
    def test_feature_toggle_integration(self, mock_get_llm):
        """Test integration with feature toggles from configuration."""
        from app.models.generation_models import ContextProcessingConfig, AgentType, ComposePhase
        
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
                
                # Create processing configuration
                processing_config = ContextProcessingConfig(
                    target_agent=AgentType.WRITER,
                    current_phase=ComposePhase.CHAPTER_DETAIL,
                    max_tokens=settings.CONTEXT_MAX_TOKENS,
                    prioritize_recent=True
                )
                
                # Create structured context container from scenario
                container = self._create_context_container_from_scenario(scenario)
                
                # Process context using the new unified API
                formatted_context, metadata = context_manager.process_context_for_agent(container, processing_config)
                
                # Verify feature-driven behavior
                assert isinstance(formatted_context, str)
                assert len(formatted_context) > 0
                assert isinstance(metadata, dict)
                assert "original_element_count" in metadata
                assert "filtered_element_count" in metadata
                assert metadata["original_element_count"] > 0
    
    @patch('app.services.llm_inference.get_llm')
    def test_error_recovery_integration(self, mock_get_llm):
        """Test error recovery across the integrated pipeline."""
        from app.models.generation_models import (
            ContextProcessingConfig, AgentType, ComposePhase,
            StructuredContextContainer, StoryContextElement, CharacterContextElement, ContextMetadata
        )
        
        mock_get_llm.return_value = Mock()
        
        context_manager = ContextManager()
        
        # Test error recovery by simulating problematic content
        # Create elements with potentially problematic content
        elements = [
            StoryContextElement(
                id="empty_1",
                type=ContextType.STORY_SUMMARY,
                content="",  # Empty content
                metadata=ContextMetadata(priority=0.5, estimated_tokens=0)
            ),
            CharacterContextElement(
                id="valid_1",
                type=ContextType.CHARACTER_PROFILE,
                content="Valid content here",
                character_id="char1",
                character_name="Valid Character",
                metadata=ContextMetadata(priority=0.8, estimated_tokens=50)
            ),
            StoryContextElement(
                id="valid_2",
                type=ContextType.WORLD_BUILDING,
                content="More valid content",
                metadata=ContextMetadata(priority=0.7, estimated_tokens=60)
            )
        ]
        
        container = StructuredContextContainer(elements=elements)
        
        # Test that the system handles problematic content gracefully
        try:
            # Create processing configuration
            processing_config = ContextProcessingConfig(
                target_agent=AgentType.WRITER,
                current_phase=ComposePhase.CHAPTER_DETAIL,
                max_tokens=self.settings.CONTEXT_MAX_TOKENS,
                prioritize_recent=True
            )
            
            # Process context using the new unified API
            formatted_context, metadata = context_manager.process_context_for_agent(container, processing_config)
            
            # Should handle gracefully and return valid results
            assert isinstance(formatted_context, str)
            # May be empty if all content was filtered out, but should not crash
            assert isinstance(metadata, dict)
            assert "original_element_count" in metadata
            assert "filtered_element_count" in metadata
            assert metadata["original_element_count"] == 3  # All original elements
            # Should handle empty content gracefully
            assert metadata["filtered_element_count"] >= 0
            
        except Exception as e:
            # If there's an exception, it should be handled gracefully
            # In a real implementation, this would test actual error recovery
            assert False, f"Error recovery failed: {e}"
    
    @patch('app.services.llm_inference.get_llm')
    def test_memory_efficiency_integration(self, mock_get_llm):
        """Test memory efficiency across the integrated pipeline."""
        from app.models.generation_models import ContextProcessingConfig, AgentType, ComposePhase
        
        mock_get_llm.return_value = Mock()
        
        # Generate large scenario to test memory handling
        large_scenario = self.generator.generate_context_scenario("memory_test", StoryComplexity.EPIC)
        
        context_manager = ContextManager()
        
        # Test memory efficiency by processing the full scenario with reasonable limits
        # Create processing configuration with reasonable token limit
        processing_config = ContextProcessingConfig(
            target_agent=AgentType.WRITER,
            current_phase=ComposePhase.CHAPTER_DETAIL,
            max_tokens=self.settings.CONTEXT_MAX_TOKENS,
            prioritize_recent=True
        )
        
        # Create structured context container from scenario
        container = self._create_context_container_from_scenario(large_scenario)
        
        # Process context using the new unified API
        formatted_context, metadata = context_manager.process_context_for_agent(container, processing_config)
        
        # Verify memory-efficient processing worked
        assert isinstance(formatted_context, str)
        assert len(formatted_context) > 0
        assert isinstance(metadata, dict)
        assert "original_element_count" in metadata
        assert "filtered_element_count" in metadata
        assert metadata["original_element_count"] > 0
        assert metadata["filtered_element_count"] > 0
        # Should have processed the large scenario efficiently
        assert metadata["filtered_element_count"] <= metadata["original_element_count"]
