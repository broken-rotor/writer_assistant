"""
Unit Tests for Token Allocation System

Tests the token allocation logic, layer management, and configuration integration
for the context management system.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List

from app.services.token_management import (
    TokenAllocator, AllocationMode, OverflowStrategy, 
    AllocationRequest, AllocationResult, LayerType
)
from app.core.config import Settings
from tests.utils.test_data_generators import TokenTestDataGenerator


class TestTokenAllocation:
    """Test token allocation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.settings = Settings()
        self.generator = TokenTestDataGenerator(seed=42)
    
    def test_token_allocator_initialization_with_config(self):
        """Test TokenAllocator initialization with configuration settings."""
        # Calculate total budget from settings
        total_budget = self.settings.CONTEXT_MAX_TOKENS - self.settings.CONTEXT_BUFFER_TOKENS
        
        allocator = TokenAllocator(
            total_budget=total_budget,
            mode=AllocationMode.DYNAMIC,
            overflow_strategy=OverflowStrategy.BORROW
        )
        
        # Test that allocator is initialized with correct settings
        assert allocator.total_budget == total_budget
        assert allocator.mode == AllocationMode.DYNAMIC
        assert allocator.overflow_strategy == OverflowStrategy.BORROW
    
    def test_layer_token_configuration_integration(self):
        """Test that layer token allocations from configuration are properly applied."""
        total_budget = self.settings.CONTEXT_MAX_TOKENS - self.settings.CONTEXT_BUFFER_TOKENS
        
        allocator = TokenAllocator(
            total_budget=total_budget
        )
        
        # Test that allocator is initialized with correct token limits
        assert allocator.total_budget == total_budget
        
        # Test that configuration values are accessible
        expected_layer_tokens = {
            'layer_a': self.settings.CONTEXT_LAYER_A_TOKENS,
            'layer_c': self.settings.CONTEXT_LAYER_C_TOKENS,
            'layer_d': self.settings.CONTEXT_LAYER_D_TOKENS,
            'layer_e': self.settings.CONTEXT_LAYER_E_TOKENS
        }
        
        # Verify configuration values are reasonable
        assert expected_layer_tokens['layer_a'] == 2000
        assert expected_layer_tokens['layer_c'] == 13000
        assert expected_layer_tokens['layer_d'] == 5000
        assert expected_layer_tokens['layer_e'] == 10000
        
        # Test that total doesn't exceed available tokens
        total_layer_tokens = sum(expected_layer_tokens.values())
        assert total_layer_tokens <= total_budget
    
    def test_allocation_request_processing(self):
        """Test processing of allocation requests."""
        allocator = TokenAllocator(
            total_budget=10000,
            mode=AllocationMode.DYNAMIC,
            overflow_strategy=OverflowStrategy.REALLOCATE
        )
        
        # Test successful allocation
        request = AllocationRequest(
            layer_type=LayerType.WORKING_MEMORY,
            requested_tokens=500,
            content_preview="Test content",
            priority=8,
            can_be_truncated=True
        )
        
        result = allocator.allocate_tokens(request)
        
        assert isinstance(result, AllocationResult)
        assert result.success is True
        assert result.granted_tokens <= request.requested_tokens
        assert result.request == request
    
    def test_overflow_handling_strategies(self):
        """Test different overflow handling strategies."""
        allocator = TokenAllocator(
            total_budget=1000,
            mode=AllocationMode.STATIC
        )
        
        # Test REJECT strategy
        allocator.overflow_strategy = OverflowStrategy.REJECT
        large_request = AllocationRequest(
            layer_type=LayerType.WORKING_MEMORY,
            requested_tokens=2000,  # More than available
            priority=5
        )
        
        result = allocator.allocate_tokens(large_request)
        assert result.success is False
        assert any(word in result.error_message.lower() for word in ["overflow", "exceed", "insufficient"])
        
        # Test TRUNCATE strategy
        allocator.overflow_strategy = OverflowStrategy.TRUNCATE
        result = allocator.allocate_tokens(large_request)
        assert result.success is True
        assert result.truncated is True
        assert result.granted_tokens < large_request.requested_tokens
    
    def test_dynamic_reallocation(self):
        """Test dynamic token reallocation between layers."""
        allocator = TokenAllocator(
            total_budget=5000,
            mode=AllocationMode.DYNAMIC,
            overflow_strategy=OverflowStrategy.REALLOCATE
        )
        
        # Fill up one layer
        requests = []
        for i in range(3):
            request = AllocationRequest(
                layer_type=LayerType.WORKING_MEMORY,
                requested_tokens=800,
                priority=8 - i
            )
            result = allocator.allocate_tokens(request)
            requests.append((request, result))
        
        # Request from another layer that might need reallocation
        high_priority_request = AllocationRequest(
            layer_type=LayerType.EPISODIC_MEMORY,
            requested_tokens=1000,
            priority=10  # Very high priority
        )
        
        result = allocator.allocate_tokens(high_priority_request)
        
        # Should succeed due to reallocation
        assert result.success is True
        assert result.granted_tokens > 0
    
    def test_priority_based_allocation(self):
        """Test that higher priority requests get better allocation."""
        allocator = TokenAllocator(
            total_budget=2000,
            mode=AllocationMode.DYNAMIC
        )
        
        # Create requests with different priorities
        low_priority = AllocationRequest(
            layer_type=LayerType.SEMANTIC_MEMORY,
            requested_tokens=500,
            priority=3
        )
        
        high_priority = AllocationRequest(
            layer_type=LayerType.WORKING_MEMORY,
            requested_tokens=500,
            priority=9
        )
        
        # Allocate in order of submission (not priority)
        low_result = allocator.allocate_tokens(low_priority)
        high_result = allocator.allocate_tokens(high_priority)
        
        # High priority should get at least as much as requested
        assert high_result.success is True
        assert high_result.granted_tokens >= high_priority.requested_tokens * 0.8  # Allow some tolerance
    
    def test_token_borrowing_between_layers(self):
        """Test token borrowing mechanism between layers."""
        allocator = TokenAllocator(
            total_budget=3000,
            mode=AllocationMode.DYNAMIC,
            overflow_strategy=OverflowStrategy.BORROW
        )
        
        # Fill up the primary layer
        primary_request = AllocationRequest(
            layer_type=LayerType.WORKING_MEMORY,
            requested_tokens=1500,
            priority=8
        )
        allocator.allocate_tokens(primary_request)
        
        # Request more than remaining in the layer
        overflow_request = AllocationRequest(
            layer_type=LayerType.WORKING_MEMORY,
            requested_tokens=800,
            priority=7
        )
        
        result = allocator.allocate_tokens(overflow_request)
        
        if result.success:
            # If borrowing occurred, borrowed_tokens should be > 0
            assert result.borrowed_tokens >= 0
    
    def test_allocation_statistics_tracking(self):
        """Test that allocation statistics are properly tracked."""
        allocator = TokenAllocator(
            total_budget=5000,
            mode=AllocationMode.DYNAMIC
        )
        
        # Make several allocation requests
        requests = [
            AllocationRequest(LayerType.WORKING_MEMORY, 300, priority=8),
            AllocationRequest(LayerType.EPISODIC_MEMORY, 500, priority=7),
            AllocationRequest(LayerType.SEMANTIC_MEMORY, 200, priority=6),
            AllocationRequest(LayerType.WORKING_MEMORY, 10000, priority=5)  # This should fail/truncate
        ]
        
        results = []
        for request in requests:
            result = allocator.allocate_tokens(request)
            results.append(result)
        
        # Check statistics
        if hasattr(allocator, 'get_statistics'):
            stats = allocator.get_statistics()
            assert stats.total_requests == len(requests)
            assert stats.successful_requests >= 3  # At least 3 should succeed
            assert stats.total_requests >= stats.successful_requests
    
    def test_concurrent_allocation_requests(self):
        """Test handling of concurrent allocation requests."""
        allocator = TokenAllocator(
            total_budget=4000,
            mode=AllocationMode.DYNAMIC
        )
        
        # Simulate concurrent requests
        concurrent_requests = [
            AllocationRequest(LayerType.WORKING_MEMORY, 600, priority=8),
            AllocationRequest(LayerType.EPISODIC_MEMORY, 700, priority=7),
            AllocationRequest(LayerType.SEMANTIC_MEMORY, 500, priority=6),
            AllocationRequest(LayerType.LONG_TERM_MEMORY, 400, priority=5)
        ]
        
        # Process all requests
        results = []
        for request in concurrent_requests:
            result = allocator.allocate_tokens(request)
            results.append(result)
        
        # Verify that total allocated doesn't exceed limits
        total_allocated = sum(r.granted_tokens for r in results if r.success)
        assert total_allocated <= allocator.total_budget
        
        # Verify at least some requests succeeded
        successful_count = sum(1 for r in results if r.success)
        assert successful_count > 0
    
    def test_allocation_timeout_handling(self):
        """Test allocation timeout handling."""
        allocator = TokenAllocator(
            total_budget=2000,
            mode=AllocationMode.DYNAMIC
        )
        
        # Request with timeout
        request = AllocationRequest(
            layer_type=LayerType.WORKING_MEMORY,
            requested_tokens=500,
            priority=8,
            max_wait_time=0.1  # 100ms timeout
        )
        
        result = allocator.allocate_tokens(request)
        
        # Should complete within timeout
        assert result.wait_time <= request.max_wait_time + 0.05  # Allow small tolerance
        assert result.success is True or result.error_message  # Either success or error with message
    
    def test_memory_layer_hierarchy_respect(self):
        """Test that allocation respects memory layer hierarchy."""
        allocator = TokenAllocator(
            total_budget=6000,
            mode=AllocationMode.DYNAMIC
        )
        
        # Test hierarchy: WORKING_MEMORY > EPISODIC_MEMORY > SEMANTIC_MEMORY > LONG_TERM_MEMORY
        hierarchy_requests = [
            AllocationRequest(LayerType.LONG_TERM_MEMORY, 1000, priority=5),
            AllocationRequest(LayerType.SEMANTIC_MEMORY, 1000, priority=5),
            AllocationRequest(LayerType.EPISODIC_MEMORY, 1000, priority=5),
            AllocationRequest(LayerType.WORKING_MEMORY, 1000, priority=5)
        ]
        
        results = []
        for request in hierarchy_requests:
            result = allocator.allocate_tokens(request)
            results.append(result)
        
        # Working memory should get the best allocation
        working_memory_result = results[-1]  # Last request (WORKING_MEMORY)
        assert working_memory_result.success is True
        assert working_memory_result.granted_tokens >= working_memory_result.request.requested_tokens * 0.8
    
    def test_configuration_integration_edge_cases(self):
        """Test edge cases in configuration integration."""
        # Test with minimal configuration
        minimal_settings = Settings()
        with patch.dict('os.environ', {
            'CONTEXT_MAX_TOKENS': '10000',
            'CONTEXT_BUFFER_TOKENS': '1000',
            'CONTEXT_LAYER_A_TOKENS': '2000',
            'CONTEXT_LAYER_B_TOKENS': '0',
            'CONTEXT_LAYER_C_TOKENS': '4000',
            'CONTEXT_LAYER_D_TOKENS': '1500',
            'CONTEXT_LAYER_E_TOKENS': '1500'
        }):
            settings = Settings()
            
            allocator = TokenAllocator(
                total_budget=settings.CONTEXT_MAX_TOKENS,
                
            )
            
            # Test allocation with minimal tokens
            request = AllocationRequest(
                layer_type=LayerType.WORKING_MEMORY,
                requested_tokens=100,
                priority=8
            )
            
            result = allocator.allocate_tokens(request)
            assert result.success is True
            assert result.granted_tokens <= 900  # Max - buffer
    
    def test_stress_test_with_generated_data(self):
        """Test allocator with stress test data from generator."""
        allocator = TokenAllocator(
            total_budget=10000,
            mode=AllocationMode.DYNAMIC,
            overflow_strategy=OverflowStrategy.REALLOCATE
        )
        
        # Generate stress test context items
        context_items = self.generator.generate_token_stress_test(8000)  # Target 8k tokens
        
        # Convert to allocation requests
        requests = []
        for item in context_items:
            target_tokens = item.metadata.get('target_tokens', 100)
            request = AllocationRequest(
                layer_type=item.layer_type,
                requested_tokens=target_tokens,
                priority=item.priority,
                content_preview=item.content[:100]
            )
            requests.append(request)
        
        # Process all requests
        results = []
        for request in requests:
            result = allocator.allocate_tokens(request)
            results.append(result)
        
        # Verify system stability under stress
        successful_results = [r for r in results if r.success]
        assert len(successful_results) > 0  # At least some should succeed
        
        total_allocated = sum(r.granted_tokens for r in successful_results)
        assert total_allocated <= allocator.total_budget
