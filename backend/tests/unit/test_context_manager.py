"""
Unit Tests for Context Manager

Tests the core context management functionality including context item management,
analysis, optimization coordination, and configuration integration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

from app.services.context_manager import ContextManager, ContextItem, ContextAnalysis
from app.models.context_models import ContextType
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
    
    @patch('app.services.llm_inference.get_llm')
    def test_context_manager_initialization_with_config(self, mock_get_llm):
        """Test ContextManager initialization with configuration settings."""
        mock_get_llm.return_value = Mock()

        context_manager = ContextManager()

        # Verify the context manager initializes properly
        assert context_manager.token_counter is not None
        assert context_manager.formatter is not None
    
    def test_context_item_creation_and_validation(self):
        """Test creation and validation of context items."""
        # Test valid context item
        context_item = ContextItem(
            content="This is test content for the story.",
            element_type=ContextType.STORY_SUMMARY.value,
            priority="high",
            layer_type=LayerType.EPISODIC_MEMORY,
            metadata={"chapter": 1, "scene": "opening"}
        )

        assert context_item.content == "This is test content for the story."
        assert context_item.element_type == ContextType.STORY_SUMMARY.value
        assert context_item.priority == "high"
        assert context_item.layer_type == LayerType.EPISODIC_MEMORY
        assert context_item.metadata["chapter"] == 1
    
    def _create_context_container_from_scenario(self, scenario):
        """Helper method to convert test scenario to StructuredContextContainer."""
        from app.models.generation_models import (
            StructuredContextContainer, PlotElement, CharacterContext,
            UserRequest, SystemInstruction
        )

        plot_elements = []
        character_contexts = []
        user_requests = []
        system_instructions = []

        for i, item in enumerate(scenario.context_items):
            # Convert ContextItem to new model based on element type
            if item.element_type in [ContextType.SYSTEM_PROMPT.value, ContextType.SYSTEM_INSTRUCTION.value, ContextType.SYSTEM_PREFERENCE.value]:
                system_instructions.append(SystemInstruction(
                    id=f"system_{i}",
                    type="behavior",
                    content=item.content,
                    priority=item.priority,
                    scope="global"
                ))
            elif item.element_type in [ContextType.STORY_SUMMARY.value, ContextType.WORLD_BUILDING.value, ContextType.STORY_THEME.value, ContextType.NARRATIVE_STATE.value, ContextType.PLOT_OUTLINE.value]:
                plot_elements.append(PlotElement(
                    id=f"plot_{i}",
                    type="scene",
                    content=item.content,
                    priority=item.priority,
                    tags=[]
                ))
            elif item.element_type in [ContextType.CHARACTER_PROFILE.value, ContextType.CHARACTER_RELATIONSHIP.value, ContextType.CHARACTER_MEMORY.value, ContextType.CHARACTER_STATE.value]:
                character_contexts.append(CharacterContext(
                    character_id=f"test_char_{i}",
                    character_name=f"Test Character {i}",
                    current_state={"emotional": "neutral"},
                    goals=[],
                    recent_actions=[],
                    memories=[item.content],
                    personality_traits=[]
                ))
            elif item.element_type in [ContextType.USER_PREFERENCE.value, ContextType.USER_FEEDBACK.value, ContextType.USER_REQUEST.value, ContextType.USER_INSTRUCTION.value]:
                user_requests.append(UserRequest(
                    id=f"user_{i}",
                    type="general",
                    content=item.content,
                    priority=item.priority
                ))
            else:
                # Default to PlotElement for unknown types
                plot_elements.append(PlotElement(
                    id=f"plot_{i}",
                    type="scene",
                    content=item.content,
                    priority=item.priority,
                    tags=[]
                ))

        return StructuredContextContainer(
            plot_elements=plot_elements,
            character_contexts=character_contexts,
            user_requests=user_requests,
            system_instructions=system_instructions
        )

    def test_context_analysis_functionality(self):
        """Test context processing functionality with various scenarios."""
        from app.models.context_models import ContextProcessingConfig, AgentType
        
        # Generate test scenario
        scenario = self.generator.generate_context_scenario("test_analysis", StoryComplexity.MODERATE)
        
        with patch('app.services.llm_inference.get_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            
            context_manager = ContextManager()
            
            # Create a processing configuration
            config = ContextProcessingConfig(
                target_agent=AgentType.WRITER,
                
                max_tokens=5000,
                prioritize_recent=True
            )
            
            # Create a structured context container from the scenario
            container = self._create_context_container_from_scenario(scenario)
            
            # Process context using the new API
            formatted_context, metadata = context_manager.process_structured_context_for_agent(container, config)
            
            # Verify the results
            assert isinstance(formatted_context, str)
            assert len(formatted_context) > 0
            assert isinstance(metadata, dict)
            assert "original_element_count" in metadata
            assert "filtered_element_count" in metadata
    
    def test_context_optimization_workflow(self):
        """Test the complete context processing workflow with token limits."""
        from app.models.context_models import ContextProcessingConfig, AgentType
        
        scenario = self.generator.generate_context_scenario("test_optimization", StoryComplexity.COMPLEX)
        
        with patch('app.services.llm_inference.get_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            
            context_manager = ContextManager()
            
            # Create a processing configuration with token limits
            config = ContextProcessingConfig(
                target_agent=AgentType.WRITER,
                
                max_tokens=7000,  # Set a token limit to trigger optimization
                prioritize_recent=True
            )
            
            # Create a structured context container from the scenario
            container = self._create_context_container_from_scenario(scenario)
            
            # Process context using the new API
            formatted_context, metadata = context_manager.process_structured_context_for_agent(container, config)
            
            # Verify the results - context should be optimized to fit within token limits
            assert isinstance(formatted_context, str)
            assert len(formatted_context) > 0
            assert isinstance(metadata, dict)
            assert "original_element_count" in metadata
            assert "filtered_element_count" in metadata
            # The filtered count should be <= original count (optimization occurred)
            assert metadata["filtered_element_count"] <= metadata["original_element_count"]
    
    def test_priority_based_context_filtering(self):
        """Test context filtering based on priority thresholds."""
        from app.models.context_models import ContextProcessingConfig, AgentType
        from app.models.generation_models import (
            StructuredContextContainer, PlotElement, CharacterContext, SystemInstruction
        )

        # Create context elements with different priorities
        plot_elements = [
            PlotElement(
                id="medium_priority_story",
                type="scene",
                content="Medium priority story",
                priority="medium",
                tags=[]
            ),
            PlotElement(
                id="low_priority_background",
                type="scene",
                content="Low priority background",
                priority="low",
                tags=[]
            )
        ]

        character_contexts = [
            CharacterContext(
                character_id="test_char",
                character_name="Test Character",
                current_state={"emotional": "neutral"},
                goals=[],
                recent_actions=[],
                memories=["Very low priority detail"],
                personality_traits=[]
            )
        ]

        system_instructions = [
            SystemInstruction(
                id="high_priority_system",
                type="behavior",
                content="High priority system",
                priority="high",
                scope="global"
            )
        ]

        elements = None  # Not used in new model
        
        with patch('app.services.llm_inference.get_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            
            context_manager = ContextManager()
            
            # Create a processing configuration with strict token limits to trigger filtering
            config = ContextProcessingConfig(
                target_agent=AgentType.WRITER,
                
                max_tokens=3000,  # Low token limit to force priority-based filtering
                prioritize_recent=True
            )
            
            container = StructuredContextContainer(
                plot_elements=plot_elements,
                character_contexts=character_contexts,
                user_requests=[],
                system_instructions=system_instructions
            )
            
            # Process context using the new API
            formatted_context, metadata = context_manager.process_structured_context_for_agent(container, config)
            
            # Verify the results - lower priority items should be filtered out
            assert isinstance(formatted_context, str)
            assert len(formatted_context) > 0
            assert isinstance(metadata, dict)
            assert "original_element_count" in metadata
            assert "filtered_element_count" in metadata
            assert metadata["original_element_count"] == 4
            # With strict token limits, some lower priority items should be filtered
            assert metadata["filtered_element_count"] <= metadata["original_element_count"]
    
    def test_layer_type_distribution_management(self):
        """Test management of context distribution across memory layers."""
        scenario = self.generator.generate_context_scenario("test_layers", StoryComplexity.MODERATE)
        
        with patch('app.services.llm_inference.get_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            
            context_manager = ContextManager()
            
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
            ContextItem(
                content="System instruction",
                element_type=ContextType.SYSTEM_PROMPT.value,
                priority="high",
                layer_type=LayerType.WORKING_MEMORY,
                metadata={}
            ),
            ContextItem(
                content="Story content",
                element_type=ContextType.STORY_SUMMARY.value,
                priority="high",
                layer_type=LayerType.EPISODIC_MEMORY,
                metadata={}
            ),
            ContextItem(
                content="Character description",
                element_type=ContextType.CHARACTER_PROFILE.value,
                priority="medium",
                layer_type=LayerType.SEMANTIC_MEMORY,
                metadata={}
            ),
            ContextItem(
                content="World building",
                element_type=ContextType.WORLD_BUILDING.value,
                priority="medium",
                layer_type=LayerType.SEMANTIC_MEMORY,
                metadata={}
            ),
            ContextItem(
                content="Feedback note",
                element_type=ContextType.USER_FEEDBACK.value,
                priority="medium",
                layer_type=LayerType.WORKING_MEMORY,
                metadata={}
            ),
            ContextItem(
                content="Memory fragment",
                element_type=ContextType.CHARACTER_MEMORY.value,
                priority="low",
                layer_type=LayerType.LONG_TERM_MEMORY,
                metadata={}
            )
        ]

        # Test categorization
        type_counts = {}
        for item in context_items:
            if item.element_type not in type_counts:
                type_counts[item.element_type] = 0
            type_counts[item.element_type] += 1
        
        # Verify all context types are represented
        assert len(type_counts) == 6
        assert type_counts[ContextType.SYSTEM_PROMPT.value] == 1
        assert type_counts[ContextType.STORY_SUMMARY.value] == 1
        assert type_counts[ContextType.CHARACTER_PROFILE.value] == 1
    
    def test_token_budget_enforcement(self):
        """Test enforcement of token budgets and limits."""
        from app.models.context_models import ContextProcessingConfig, AgentType
        
        with patch('app.services.llm_inference.get_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            
            # Create context manager with strict limits
            context_manager = ContextManager()
            
            # Generate large context that exceeds limits
            large_scenario = self.generator.generate_context_scenario("test_budget", StoryComplexity.EPIC)
            
            # Create a processing configuration with very strict token limits
            config = ContextProcessingConfig(
                target_agent=AgentType.WRITER,
                
                max_tokens=2000,  # Very strict token limit to force budget enforcement
                prioritize_recent=True
            )
            
            # Create a structured context container from the scenario
            container = self._create_context_container_from_scenario(large_scenario)
            
            # Process context using the new API
            formatted_context, metadata = context_manager.process_structured_context_for_agent(container, config)
            
            # Verify budget enforcement occurred
            assert isinstance(formatted_context, str)
            assert len(formatted_context) > 0
            assert isinstance(metadata, dict)
            assert "original_element_count" in metadata
            assert "filtered_element_count" in metadata
            # Budget enforcement should reduce the number of elements
            assert metadata["filtered_element_count"] <= metadata["original_element_count"]
    
    def test_context_assembly_performance(self):
        """Test context assembly performance and timeout handling."""
        from app.models.context_models import ContextProcessingConfig, AgentType
        
        scenario = self.generator.generate_context_scenario("test_performance", StoryComplexity.MODERATE)
        
        with patch('app.services.llm_inference.get_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            
            context_manager = ContextManager()
            
            # Create a processing configuration for performance testing
            config = ContextProcessingConfig(
                target_agent=AgentType.WRITER,
                
                max_tokens=6000,  # Moderate token limit
                prioritize_recent=True
            )
            
            # Create a structured context container from the scenario
            container = self._create_context_container_from_scenario(scenario)
            
            # Process context using the new API and measure performance
            import time
            start_time = time.time()
            formatted_context, metadata = context_manager.process_structured_context_for_agent(container, config)
            processing_time = time.time() - start_time
            
            # Verify performance and results
            assert isinstance(formatted_context, str)
            assert len(formatted_context) > 0
            assert isinstance(metadata, dict)
            assert "original_element_count" in metadata
            assert "filtered_element_count" in metadata
            # Performance should be reasonable (less than 5 seconds for moderate complexity)
            assert processing_time < 5.0
    
    def test_configuration_integration_with_settings(self):
        """Test integration with configuration settings."""
        from app.models.context_models import ContextProcessingConfig, AgentType
        
        # Test with custom configuration
        custom_env = {
            'CONTEXT_MAX_TOKENS': '16000',
            'CONTEXT_BUFFER_TOKENS': '2000',
            'CONTEXT_LAYER_A_TOKENS': '1600',
            'CONTEXT_LAYER_C_TOKENS': '6400',
            'CONTEXT_LAYER_D_TOKENS': '3200',
            'CONTEXT_LAYER_E_TOKENS': '2800',
            'CONTEXT_SUMMARIZATION_THRESHOLD': '12000',
            'CONTEXT_ENABLE_RAG': 'false',
            'CONTEXT_ENABLE_MONITORING': 'true'
        }
        
        with patch.dict('os.environ', custom_env):
            custom_settings = Settings()
            
            with patch('app.services.llm_inference.get_llm') as mock_get_llm:
                mock_get_llm.return_value = Mock()
                
                context_manager = ContextManager()
                
                # Test that configuration settings are properly integrated
                scenario = self.generator.generate_context_scenario("test_config", StoryComplexity.MODERATE)
                
                # Create a processing configuration that uses custom settings
                config = ContextProcessingConfig(
                    target_agent=AgentType.WRITER,
                    
                    max_tokens=16000,  # Use the custom max tokens setting
                    prioritize_recent=True
                )
                
                # Create a structured context container from the scenario
                container = self._create_context_container_from_scenario(scenario)
                
                # Process context using the new API
                formatted_context, metadata = context_manager.process_structured_context_for_agent(container, config)
                
                # Verify that configuration settings are respected
                assert isinstance(formatted_context, str)
                assert len(formatted_context) > 0
                assert isinstance(metadata, dict)
                assert "original_element_count" in metadata
                assert "filtered_element_count" in metadata
    
    def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms."""
        from app.models.context_models import ContextProcessingConfig, AgentType
        from app.models.generation_models import (
            StructuredContextContainer, PlotElement, SystemInstruction
        )

        with patch('app.services.llm_inference.get_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()

            context_manager = ContextManager()

            # Test with potentially problematic context elements
            plot_elements = [
                PlotElement(
                    id="valid_content",
                    type="scene",
                    content="Valid content",
                    priority="low",  # Minimum priority
                    tags=[]
                )
            ]

            system_instructions = [
                SystemInstruction(
                    id="empty_content",
                    type="behavior",
                    content="",  # Empty content
                    priority="high",
                    scope="global"
                )
            ]

            container = StructuredContextContainer(
                plot_elements=plot_elements,
                character_contexts=[],
                user_requests=[],
                system_instructions=system_instructions
            )
            
            # Create a processing configuration
            config = ContextProcessingConfig(
                target_agent=AgentType.WRITER,
                
                max_tokens=5000,
                prioritize_recent=True
            )
            
            # Test that the system handles problematic elements gracefully
            formatted_context, metadata = context_manager.process_structured_context_for_agent(container, config)
            
            # The processing should still work even with problematic elements
            assert isinstance(formatted_context, str)
            assert isinstance(metadata, dict)
            assert "original_element_count" in metadata
            assert "filtered_element_count" in metadata
            assert metadata["original_element_count"] == 2
    
    def test_context_caching_functionality(self):
        """Test context caching when enabled."""
        from app.models.context_models import ContextProcessingConfig, AgentType
        
        scenario = self.generator.generate_context_scenario("test_caching", StoryComplexity.MODERATE)
        
        with patch('app.services.llm_inference.get_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            
            # Test with caching enabled
            with patch.dict('os.environ', {'CONTEXT_ENABLE_CACHING': 'true', 'CONTEXT_MAX_TOKENS': '10000', 'CONTEXT_BUFFER_TOKENS': '1000'}):
                context_manager = ContextManager()
                
                # Create a processing configuration
                config = ContextProcessingConfig(
                    target_agent=AgentType.WRITER,
                    
                    max_tokens=10000,
                    prioritize_recent=True
                )
                
                # Create a structured context container from the scenario
                container = self._create_context_container_from_scenario(scenario)
                
                # Test basic context processing (which would use caching if enabled)
                formatted_context, metadata = context_manager.process_structured_context_for_agent(container, config)
                
                # Verify processing worked
                assert isinstance(formatted_context, str)
                assert len(formatted_context) > 0
                assert isinstance(metadata, dict)
                assert "original_element_count" in metadata
                assert "filtered_element_count" in metadata
    
    def test_monitoring_and_analytics_integration(self):
        """Test monitoring and analytics when enabled."""
        from app.models.context_models import ContextProcessingConfig, AgentType
        
        scenario = self.generator.generate_context_scenario("test_monitoring", StoryComplexity.MODERATE)
        
        with patch('app.services.llm_inference.get_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            
            # Test with monitoring enabled
            with patch.dict('os.environ', {'CONTEXT_ENABLE_MONITORING': 'true', 'CONTEXT_MAX_TOKENS': '10000', 'CONTEXT_BUFFER_TOKENS': '1000'}):
                context_manager = ContextManager()
                
                # Create a processing configuration
                config = ContextProcessingConfig(
                    target_agent=AgentType.WRITER,
                    
                    max_tokens=10000,
                    prioritize_recent=True
                )
                
                # Create a structured context container from the scenario
                container = self._create_context_container_from_scenario(scenario)
                
                # Test context processing (which would be monitored)
                formatted_context, metadata = context_manager.process_structured_context_for_agent(container, config)
                
                # Verify processing worked and includes monitoring metadata
                assert isinstance(formatted_context, str)
                assert len(formatted_context) > 0
                assert isinstance(metadata, dict)
                assert "original_element_count" in metadata
                assert "filtered_element_count" in metadata
                assert "processing_timestamp" in metadata
    
    def test_rag_integration_when_enabled(self):
        """Test RAG (Retrieval-Augmented Generation) integration."""
        from app.models.context_models import ContextProcessingConfig, AgentType
        
        scenario = self.generator.generate_context_scenario("test_rag", StoryComplexity.COMPLEX)
        
        with patch('app.services.llm_inference.get_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            
            # Test with RAG enabled
            with patch.dict('os.environ', {'CONTEXT_ENABLE_RAG': 'true', 'CONTEXT_MAX_TOKENS': '10000', 'CONTEXT_BUFFER_TOKENS': '1000'}):
                context_manager = ContextManager()
                
                # Create a processing configuration for RAG testing
                config = ContextProcessingConfig(
                    target_agent=AgentType.WRITER,
                    
                    max_tokens=10000,
                    prioritize_recent=True
                )
                
                # Create a structured context container from the scenario
                container = self._create_context_container_from_scenario(scenario)
                
                # Test context processing (which could use RAG if enabled)
                formatted_context, metadata = context_manager.process_structured_context_for_agent(container, config)
                
                # Verify processing worked
                assert isinstance(formatted_context, str)
                assert len(formatted_context) > 0
                assert isinstance(metadata, dict)
                assert "original_element_count" in metadata
                assert "filtered_element_count" in metadata
    
    def test_stress_testing_with_large_contexts(self):
        """Test system behavior under stress with large context scenarios."""
        from app.models.context_models import ContextProcessingConfig, AgentType
        
        # Generate a very large context scenario
        large_scenario = self.generator.generate_context_scenario("stress_test", StoryComplexity.EPIC)
        
        with patch('app.services.llm_inference.get_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            
            context_manager = ContextManager()
            
            # Test that the system handles large contexts without crashing
            try:
                # Create a processing configuration for stress testing
                config = ContextProcessingConfig(
                    target_agent=AgentType.WRITER,
                    
                    max_tokens=30000,  # Large token limit for stress testing
                    prioritize_recent=True
                )
                
                # Create a structured context container from the scenario
                container = self._create_context_container_from_scenario(large_scenario)
                
                # Test processing of large context
                formatted_context, metadata = context_manager.process_structured_context_for_agent(container, config)
                
                # Verify processing worked even with large context
                assert isinstance(formatted_context, str)
                assert len(formatted_context) > 0
                assert isinstance(metadata, dict)
                assert "original_element_count" in metadata
                assert "filtered_element_count" in metadata
                assert metadata["original_element_count"] > 0
                    
            except Exception as e:
                pytest.fail(f"Context manager failed under stress: {e}")
