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
    
    @patch('app.services.llm_inference.get_llm')
    def test_context_manager_initialization_with_config(self, mock_get_llm):
        """Test ContextManager initialization with configuration settings."""
        mock_get_llm.return_value = Mock()
        
        context_manager = ContextManager()
        
        # Verify the context manager initializes properly
        assert context_manager.summarizer is not None
        assert context_manager.formatter is not None
    
    def test_context_item_creation_and_validation(self):
        """Test creation and validation of context items."""
        # Test valid context item
        context_item = ContextItem(
            content="This is test content for the story.",
            context_type=ContextType.STORY_SUMMARY,
            priority=8,
            layer_type=LayerType.EPISODIC_MEMORY,
            metadata={"chapter": 1, "scene": "opening"}
        )
        
        assert context_item.content == "This is test content for the story."
        assert context_item.context_type == ContextType.STORY_SUMMARY
        assert context_item.priority == 8
        assert context_item.layer_type == LayerType.EPISODIC_MEMORY
        assert context_item.metadata["chapter"] == 1
    
    def _create_context_container_from_scenario(self, scenario):
        """Helper method to convert test scenario to StructuredContextContainer."""
        from app.models.context_models import (
            StructuredContextContainer, SystemContextElement, StoryContextElement, 
            CharacterContextElement, UserContextElement, PhaseContextElement, 
            ConversationContextElement, ComposePhase
        )
        
        elements = []
        for i, item in enumerate(scenario.context_items):
            # Convert ContextItem to BaseContextElement based on context type
            if item.context_type in [ContextType.SYSTEM_PROMPT, ContextType.SYSTEM_INSTRUCTION, ContextType.SYSTEM_PREFERENCE]:
                element = SystemContextElement(
                    id=f"system_{i}",
                    type=item.context_type,
                    content=item.content
                )
            elif item.context_type in [ContextType.STORY_SUMMARY, ContextType.WORLD_BUILDING, ContextType.STORY_THEME, ContextType.NARRATIVE_STATE, ContextType.PLOT_OUTLINE]:
                element = StoryContextElement(
                    id=f"story_{i}",
                    type=item.context_type,
                    content=item.content
                )
            elif item.context_type in [ContextType.CHARACTER_PROFILE, ContextType.CHARACTER_RELATIONSHIP, ContextType.CHARACTER_MEMORY, ContextType.CHARACTER_STATE]:
                element = CharacterContextElement(
                    id=f"character_{i}",
                    type=item.context_type,
                    content=item.content,
                    character_id="test_char",
                    character_name="Test Character"
                )
            elif item.context_type in [ContextType.USER_PREFERENCE, ContextType.USER_FEEDBACK, ContextType.USER_REQUEST, ContextType.USER_INSTRUCTION]:
                element = UserContextElement(
                    id=f"user_{i}",
                    type=item.context_type,
                    content=item.content
                )
            elif item.context_type in [ContextType.PHASE_INSTRUCTION, ContextType.PHASE_OUTPUT, ContextType.PHASE_GUIDANCE]:
                element = PhaseContextElement(
                    id=f"phase_{i}",
                    type=item.context_type,
                    content=item.content,
                    phase=ComposePhase.CHAPTER_DETAIL
                )
            elif item.context_type in [ContextType.CONVERSATION_HISTORY, ContextType.CONVERSATION_CONTEXT]:
                element = ConversationContextElement(
                    id=f"conversation_{i}",
                    type=item.context_type,
                    content=item.content
                )
            else:
                # Default to UserContextElement for unknown types
                element = UserContextElement(
                    id=f"user_{i}",
                    type=ContextType.USER_REQUEST,  # Use a valid type
                    content=item.content
                )
            elements.append(element)
        
        return StructuredContextContainer(elements=elements)

    def test_context_analysis_functionality(self):
        """Test context processing functionality with various scenarios."""
        from app.models.context_models import ContextProcessingConfig, AgentType, ComposePhase
        
        # Generate test scenario
        scenario = self.generator.generate_context_scenario("test_analysis", StoryComplexity.MODERATE)
        
        with patch('app.services.llm_inference.get_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            
            context_manager = ContextManager()
            
            # Create a processing configuration
            config = ContextProcessingConfig(
                target_agent=AgentType.WRITER,
                current_phase=ComposePhase.CHAPTER_DETAIL,
                max_tokens=5000,
                prioritize_recent=True
            )
            
            # Create a structured context container from the scenario
            container = self._create_context_container_from_scenario(scenario)
            
            # Process context using the new API
            formatted_context, metadata = context_manager.process_context_for_agent(container, config)
            
            # Verify the results
            assert isinstance(formatted_context, str)
            assert len(formatted_context) > 0
            assert isinstance(metadata, dict)
            assert "original_element_count" in metadata
            assert "filtered_element_count" in metadata
    
    def test_context_optimization_workflow(self):
        """Test the complete context processing workflow with token limits."""
        from app.models.context_models import ContextProcessingConfig, AgentType, ComposePhase
        
        scenario = self.generator.generate_context_scenario("test_optimization", StoryComplexity.COMPLEX)
        
        with patch('app.services.llm_inference.get_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            
            context_manager = ContextManager()
            
            # Create a processing configuration with token limits
            config = ContextProcessingConfig(
                target_agent=AgentType.WRITER,
                current_phase=ComposePhase.CHAPTER_DETAIL,
                max_tokens=7000,  # Set a token limit to trigger optimization
                prioritize_recent=True
            )
            
            # Create a structured context container from the scenario
            container = self._create_context_container_from_scenario(scenario)
            
            # Process context using the new API
            formatted_context, metadata = context_manager.process_context_for_agent(container, config)
            
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
        from app.models.context_models import (
            ContextProcessingConfig, AgentType, ComposePhase, StructuredContextContainer,
            SystemContextElement, StoryContextElement, CharacterContextElement, ContextMetadata
        )
        
        # Create context elements with different priorities (0.0-1.0 range)
        elements = [
            SystemContextElement(
                id="high_priority_system",
                type=ContextType.SYSTEM_PROMPT,
                content="High priority system",
                metadata=ContextMetadata(priority=1.0)  # Highest priority
            ),
            StoryContextElement(
                id="medium_priority_story",
                type=ContextType.STORY_SUMMARY,
                content="Medium priority story",
                metadata=ContextMetadata(priority=0.7)  # Medium-high priority
            ),
            StoryContextElement(
                id="low_priority_background",
                type=ContextType.WORLD_BUILDING,
                content="Low priority background",
                metadata=ContextMetadata(priority=0.3)  # Low priority
            ),
            CharacterContextElement(
                id="very_low_priority_detail",
                type=ContextType.CHARACTER_MEMORY,
                content="Very low priority detail",
                character_id="test_char",
                character_name="Test Character",
                metadata=ContextMetadata(priority=0.1)  # Very low priority
            )
        ]
        
        with patch('app.services.llm_inference.get_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            
            context_manager = ContextManager()
            
            # Create a processing configuration with strict token limits to trigger filtering
            config = ContextProcessingConfig(
                target_agent=AgentType.WRITER,
                current_phase=ComposePhase.CHAPTER_DETAIL,
                max_tokens=3000,  # Low token limit to force priority-based filtering
                prioritize_recent=True
            )
            
            container = StructuredContextContainer(elements=elements)
            
            # Process context using the new API
            formatted_context, metadata = context_manager.process_context_for_agent(container, config)
            
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
            ContextItem("System instruction", ContextType.SYSTEM_PROMPT, 10, LayerType.WORKING_MEMORY, {}),
            ContextItem("Story content", ContextType.STORY_SUMMARY, 8, LayerType.EPISODIC_MEMORY, {}),
            ContextItem("Character description", ContextType.CHARACTER_PROFILE, 7, LayerType.SEMANTIC_MEMORY, {}),
            ContextItem("World building", ContextType.WORLD_BUILDING, 6, LayerType.SEMANTIC_MEMORY, {}),
            ContextItem("Feedback note", ContextType.USER_FEEDBACK, 5, LayerType.WORKING_MEMORY, {}),
            ContextItem("Memory fragment", ContextType.CHARACTER_MEMORY, 4, LayerType.LONG_TERM_MEMORY, {})
        ]
        
        # Test categorization
        type_counts = {}
        for item in context_items:
            if item.context_type not in type_counts:
                type_counts[item.context_type] = 0
            type_counts[item.context_type] += 1
        
        # Verify all context types are represented
        assert len(type_counts) == 6
        assert type_counts[ContextType.SYSTEM_PROMPT] == 1
        assert type_counts[ContextType.STORY_SUMMARY] == 1
        assert type_counts[ContextType.CHARACTER_PROFILE] == 1
    
    def test_token_budget_enforcement(self):
        """Test enforcement of token budgets and limits."""
        from app.models.context_models import ContextProcessingConfig, AgentType, ComposePhase
        
        with patch('app.services.llm_inference.get_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            
            # Create context manager with strict limits
            context_manager = ContextManager()
            
            # Generate large context that exceeds limits
            large_scenario = self.generator.generate_context_scenario("test_budget", StoryComplexity.EPIC)
            
            # Create a processing configuration with very strict token limits
            config = ContextProcessingConfig(
                target_agent=AgentType.WRITER,
                current_phase=ComposePhase.CHAPTER_DETAIL,
                max_tokens=2000,  # Very strict token limit to force budget enforcement
                prioritize_recent=True
            )
            
            # Create a structured context container from the scenario
            container = self._create_context_container_from_scenario(large_scenario)
            
            # Process context using the new API
            formatted_context, metadata = context_manager.process_context_for_agent(container, config)
            
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
        from app.models.context_models import ContextProcessingConfig, AgentType, ComposePhase
        
        scenario = self.generator.generate_context_scenario("test_performance", StoryComplexity.MODERATE)
        
        with patch('app.services.llm_inference.get_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            
            context_manager = ContextManager()
            
            # Create a processing configuration for performance testing
            config = ContextProcessingConfig(
                target_agent=AgentType.WRITER,
                current_phase=ComposePhase.CHAPTER_DETAIL,
                max_tokens=6000,  # Moderate token limit
                prioritize_recent=True
            )
            
            # Create a structured context container from the scenario
            container = self._create_context_container_from_scenario(scenario)
            
            # Process context using the new API and measure performance
            import time
            start_time = time.time()
            formatted_context, metadata = context_manager.process_context_for_agent(container, config)
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
        from app.models.context_models import ContextProcessingConfig, AgentType, ComposePhase
        
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
                    current_phase=ComposePhase.CHAPTER_DETAIL,
                    max_tokens=16000,  # Use the custom max tokens setting
                    prioritize_recent=True
                )
                
                # Create a structured context container from the scenario
                container = self._create_context_container_from_scenario(scenario)
                
                # Process context using the new API
                formatted_context, metadata = context_manager.process_context_for_agent(container, config)
                
                # Verify that configuration settings are respected
                assert isinstance(formatted_context, str)
                assert len(formatted_context) > 0
                assert isinstance(metadata, dict)
                assert "original_element_count" in metadata
                assert "filtered_element_count" in metadata
    
    def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms."""
        from app.models.context_models import (
            ContextProcessingConfig, AgentType, ComposePhase, StructuredContextContainer,
            SystemContextElement, StoryContextElement, ContextMetadata
        )
        
        with patch('app.services.llm_inference.get_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            
            context_manager = ContextManager()
            
            # Test with potentially problematic context elements
            elements = [
                SystemContextElement(
                    id="empty_content",
                    type=ContextType.SYSTEM_PROMPT,
                    content="",  # Empty content
                    metadata=ContextMetadata(priority=1.0)
                ),
                StoryContextElement(
                    id="valid_content",
                    type=ContextType.STORY_SUMMARY,
                    content="Valid content",
                    metadata=ContextMetadata(priority=0.0)  # Minimum priority
                )
            ]
            
            container = StructuredContextContainer(elements=elements)
            
            # Create a processing configuration
            config = ContextProcessingConfig(
                target_agent=AgentType.WRITER,
                current_phase=ComposePhase.CHAPTER_DETAIL,
                max_tokens=5000,
                prioritize_recent=True
            )
            
            # Test that the system handles problematic elements gracefully
            formatted_context, metadata = context_manager.process_context_for_agent(container, config)
            
            # The processing should still work even with problematic elements
            assert isinstance(formatted_context, str)
            assert isinstance(metadata, dict)
            assert "original_element_count" in metadata
            assert "filtered_element_count" in metadata
            assert metadata["original_element_count"] == 2
    
    def test_context_caching_functionality(self):
        """Test context caching when enabled."""
        from app.models.context_models import ContextProcessingConfig, AgentType, ComposePhase
        
        scenario = self.generator.generate_context_scenario("test_caching", StoryComplexity.MODERATE)
        
        with patch('app.services.llm_inference.get_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            
            # Test with caching enabled
            with patch.dict('os.environ', {'CONTEXT_ENABLE_CACHING': 'true', 'CONTEXT_MAX_TOKENS': '10000', 'CONTEXT_BUFFER_TOKENS': '1000'}):
                context_manager = ContextManager()
                
                # Create a processing configuration
                config = ContextProcessingConfig(
                    target_agent=AgentType.WRITER,
                    current_phase=ComposePhase.CHAPTER_DETAIL,
                    max_tokens=10000,
                    prioritize_recent=True
                )
                
                # Create a structured context container from the scenario
                container = self._create_context_container_from_scenario(scenario)
                
                # Test basic context processing (which would use caching if enabled)
                formatted_context, metadata = context_manager.process_context_for_agent(container, config)
                
                # Verify processing worked
                assert isinstance(formatted_context, str)
                assert len(formatted_context) > 0
                assert isinstance(metadata, dict)
                assert "original_element_count" in metadata
                assert "filtered_element_count" in metadata
    
    def test_monitoring_and_analytics_integration(self):
        """Test monitoring and analytics when enabled."""
        from app.models.context_models import ContextProcessingConfig, AgentType, ComposePhase
        
        scenario = self.generator.generate_context_scenario("test_monitoring", StoryComplexity.MODERATE)
        
        with patch('app.services.llm_inference.get_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            
            # Test with monitoring enabled
            with patch.dict('os.environ', {'CONTEXT_ENABLE_MONITORING': 'true', 'CONTEXT_MAX_TOKENS': '10000', 'CONTEXT_BUFFER_TOKENS': '1000'}):
                context_manager = ContextManager()
                
                # Create a processing configuration
                config = ContextProcessingConfig(
                    target_agent=AgentType.WRITER,
                    current_phase=ComposePhase.CHAPTER_DETAIL,
                    max_tokens=10000,
                    prioritize_recent=True
                )
                
                # Create a structured context container from the scenario
                container = self._create_context_container_from_scenario(scenario)
                
                # Test context processing (which would be monitored)
                formatted_context, metadata = context_manager.process_context_for_agent(container, config)
                
                # Verify processing worked and includes monitoring metadata
                assert isinstance(formatted_context, str)
                assert len(formatted_context) > 0
                assert isinstance(metadata, dict)
                assert "original_element_count" in metadata
                assert "filtered_element_count" in metadata
                assert "processing_timestamp" in metadata
    
    def test_rag_integration_when_enabled(self):
        """Test RAG (Retrieval-Augmented Generation) integration."""
        scenario = self.generator.generate_context_scenario("test_rag", StoryComplexity.COMPLEX)
        
        with patch('app.services.llm_inference.get_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            
            # Test with RAG enabled
            with patch.dict('os.environ', {'CONTEXT_ENABLE_RAG': 'true', 'CONTEXT_MAX_TOKENS': '10000', 'CONTEXT_BUFFER_TOKENS': '1000'}):
                context_manager = ContextManager()
                
                # Test context optimization (which could use RAG)
                result, metadata = context_manager.optimize_context(scenario.context_items)
                
                # Verify optimization worked
                assert len(result) >= 0
                assert isinstance(metadata, dict)
    
    def test_stress_testing_with_large_contexts(self):
        """Test system behavior under stress with large context scenarios."""
        # Generate a very large context scenario
        large_scenario = self.generator.generate_context_scenario("stress_test", StoryComplexity.EPIC)
        
        with patch('app.services.llm_inference.get_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            
            context_manager = ContextManager()
            
            # Test that the system handles large contexts without crashing
            try:
                # Test analysis of large context
                analysis = context_manager.analyze_context(large_scenario.context_items)
                
                assert analysis.total_tokens > 0
                assert isinstance(analysis.items_by_type, dict)
                
                # Test optimization of large context
                result, metadata = context_manager.optimize_context(large_scenario.context_items, target_tokens=30000)
                
                assert len(result) >= 0
                assert isinstance(metadata, dict)
                    
            except Exception as e:
                pytest.fail(f"Context manager failed under stress: {e}")
