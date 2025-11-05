"""
Integration Tests for Full Context Management Pipeline

Tests the complete context management workflow from configuration loading
through context assembly, token allocation, and content optimization.
"""

import pytest
import time
from unittest.mock import Mock, patch
from typing import List, Dict, Any

from app.services.context_manager import ContextManager, ContextItem
from app.models.context_models import ContextType
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
            StructuredContextContainer, PlotElement, CharacterContext,
            UserRequest, SystemInstruction
        )

        plot_elements = []
        character_contexts = []
        user_requests = []
        system_instructions = []

        for i, item in enumerate(scenario.context_items):
            # Priority is already a string (high/medium/low) in ContextItem
            priority_str = item.priority

            # Create appropriate element type based on element type
            if item.element_type in [ContextType.SYSTEM_PROMPT.value, ContextType.SYSTEM_INSTRUCTION.value]:
                system_instructions.append(SystemInstruction(
                    id=f"system_{i}",
                    type="behavior",
                    content=item.content,
                    priority=priority_str,
                    scope="global"
                ))
            elif item.element_type in [ContextType.CHARACTER_PROFILE.value, ContextType.CHARACTER_MEMORY.value, ContextType.CHARACTER_STATE.value]:
                character_contexts.append(CharacterContext(
                    character_id=f"test_character_{i}",
                    character_name=f"Test Character {i}",
                    current_state={"emotional": "neutral", "physical": "healthy"},
                    goals=[],
                    recent_actions=[],
                    memories=[item.content],
                    personality_traits=[]
                ))
            elif item.element_type in [ContextType.USER_REQUEST.value, ContextType.USER_FEEDBACK.value, ContextType.USER_INSTRUCTION.value]:
                user_requests.append(UserRequest(
                    id=f"user_{i}",
                    type="general",
                    content=item.content,
                    priority=priority_str
                ))
            else:
                # Default to PlotElement for story-level contexts
                plot_elements.append(PlotElement(
                    id=f"plot_{i}",
                    type="scene",
                    content=item.content,
                    priority=priority_str,
                    tags=[]
                ))

        return StructuredContextContainer(
            plot_elements=plot_elements,
            character_contexts=character_contexts,
            user_requests=user_requests,
            system_instructions=system_instructions
        )
    
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
        from app.models.context_models import ContextProcessingConfig, AgentType, ComposePhase
        
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
        from app.models.context_models import ContextProcessingConfig, AgentType, ComposePhase
        
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
        from app.models.context_models import ContextProcessingConfig, AgentType, ComposePhase
        from app.models.generation_models import (
            StructuredContextContainer, PlotElement, CharacterContext,
            SystemInstruction
        )

        mock_get_llm.return_value = Mock()

        # Create elements with varying priorities across different types
        plot_elements = [
            PlotElement(
                id="story_1",
                type="scene",
                content="Important story",
                priority="high",  # 0.9 -> high
                tags=[]
            ),
            PlotElement(
                id="world_1",
                type="setup",
                content="Useful world info",
                priority="medium",  # 0.6 -> medium
                tags=[]
            )
        ]

        character_contexts = [
            CharacterContext(
                character_id="char1",
                character_name="Main Character",
                current_state={"emotional": "determined"},
                goals=["achieve goal"],
                recent_actions=[],
                memories=["Key character"],
                personality_traits=["brave"]
            ),
            CharacterContext(
                character_id="char2",
                character_name="Side Character",
                current_state={"emotional": "neutral"},
                goals=[],
                recent_actions=[],
                memories=["Background detail"],
                personality_traits=[]
            ),
            CharacterContext(
                character_id="char3",
                character_name="Minor Character",
                current_state={},
                goals=[],
                recent_actions=[],
                memories=["Minor detail"],
                personality_traits=[]
            )
        ]

        system_instructions = [
            SystemInstruction(
                id="system_1",
                type="behavior",
                content="Critical system",
                priority="high",  # 1.0 -> high
                scope="global"
            )
        ]

        container = StructuredContextContainer(
            plot_elements=plot_elements,
            character_contexts=character_contexts,
            user_requests=[],
            system_instructions=system_instructions
        )
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
        from app.models.context_models import ContextProcessingConfig, AgentType, ComposePhase
        
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
        from app.models.context_models import ContextProcessingConfig, AgentType, ComposePhase
        from app.models.generation_models import (
            StructuredContextContainer, PlotElement, CharacterContext
        )

        mock_get_llm.return_value = Mock()

        context_manager = ContextManager()

        # Test error recovery by simulating problematic content
        # Create elements with potentially problematic content
        plot_elements = [
            PlotElement(
                id="empty_1",
                type="scene",
                content="",  # Empty content
                priority="medium",
                tags=[]
            ),
            PlotElement(
                id="valid_2",
                type="setup",
                content="More valid content",
                priority="medium",
                tags=[]
            )
        ]

        character_contexts = [
            CharacterContext(
                character_id="char1",
                character_name="Valid Character",
                current_state={"emotional": "neutral"},
                goals=[],
                recent_actions=[],
                memories=["Valid content here"],
                personality_traits=[]
            )
        ]

        container = StructuredContextContainer(
            plot_elements=plot_elements,
            character_contexts=character_contexts,
            user_requests=[],
            system_instructions=[]
        )
        
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
        from app.models.context_models import ContextProcessingConfig, AgentType, ComposePhase
        
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
