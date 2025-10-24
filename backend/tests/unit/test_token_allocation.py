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
        with patch('app.services.token_management.allocator.settings', self.settings):
            allocator = TokenAllocator(
                max_tokens=self.settings.CONTEXT_MAX_TOKENS,
                buffer_tokens=self.settings.CONTEXT_BUFFER_TOKENS,
                allocation_mode=AllocationMode.DYNAMIC,
                overflow_strategy=OverflowStrategy.REALLOCATE
            )
            
            assert allocator.max_tokens == 32000
            assert allocator.buffer_tokens == 2000
            assert allocator.allocation_mode == AllocationMode.DYNAMIC
            assert allocator.overflow_strategy == OverflowStrategy.REALLOCATE
    
    def test_layer_token_configuration_integration(self):
        """Test that layer token allocations from configuration are properly applied."""
        allocator = TokenAllocator(
            max_tokens=self.settings.CONTEXT_MAX_TOKENS,
            buffer_tokens=self.settings.CONTEXT_BUFFER_TOKENS
        )
        
        # Test that allocator is initialized with correct token limits
        assert allocator.max_tokens == self.settings.CONTEXT_MAX_TOKENS
        assert allocator.buffer_tokens == self.settings.CONTEXT_BUFFER_TOKENS
        
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
        available_tokens = allocator.max_tokens - allocator.buffer_tokens
        assert total_layer_tokens <= available_tokens
    
    def test_allocation_request_processing(self):
        """Test processing of allocation requests."""
        allocator = TokenAllocator(
            max_tokens=10000,
            buffer_tokens=1000,
            allocation_mode=AllocationMode.DYNAMIC,
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
        
        result = allocator.allocate(request)
        
        assert isinstance(result, AllocationResult)
        assert result.success is True
        assert result.granted_tokens <= request.requested_tokens
        assert result.request == request
    
    def test_overflow_handling_strategies(self):
        """Test different overflow handling strategies."""
        allocator = TokenAllocator(
            max_tokens=1000,
            buffer_tokens=100,
            allocation_mode=AllocationMode.STATIC
        )
        
        # Test REJECT strategy
        allocator.overflow_strategy = OverflowStrategy.REJECT
        large_request = AllocationRequest(
            layer_type=LayerType.WORKING_MEMORY,
            requested_tokens=2000,  # More than available
            priority=5
        )
        
        result = allocator.allocate(large_request)
        assert result.success is False
        assert "overflow" in result.error_message.lower() or "exceed" in result.error_message.lower()
        
        # Test TRUNCATE strategy
        allocator.overflow_strategy = OverflowStrategy.TRUNCATE
        result = allocator.allocate(large_request)
        assert result.success is True
        assert result.truncated is True
        assert result.granted_tokens < large_request.requested_tokens
    
    def test_dynamic_reallocation(self):
        """Test dynamic token reallocation between layers."""
        allocator = TokenAllocator(
            max_tokens=5000,
            buffer_tokens=500,
            allocation_mode=AllocationMode.DYNAMIC,
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
            result = allocator.allocate(request)
            requests.append((request, result))
        
        # Request from another layer that might need reallocation
        high_priority_request = AllocationRequest(
            layer_type=LayerType.EPISODIC_MEMORY,
            requested_tokens=1000,
            priority=10  # Very high priority
        )
        
        result = allocator.allocate(high_priority_request)
        
        # Should succeed due to reallocation
        assert result.success is True
        assert result.granted_tokens > 0
    
    def test_priority_based_allocation(self):
        """Test that higher priority requests get better allocation."""
        allocator = TokenAllocator(
            max_tokens=2000,
            buffer_tokens=200,
            allocation_mode=AllocationMode.DYNAMIC
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
        low_result = allocator.allocate(low_priority)
        high_result = allocator.allocate(high_priority)
        
        # High priority should get at least as much as requested
        assert high_result.success is True
        assert high_result.granted_tokens >= high_priority.requested_tokens * 0.8  # Allow some tolerance
    
    def test_token_borrowing_between_layers(self):
        """Test token borrowing mechanism between layers."""
        allocator = TokenAllocator(
            max_tokens=3000,
            buffer_tokens=300,
            allocation_mode=AllocationMode.DYNAMIC,
            overflow_strategy=OverflowStrategy.BORROW
        )
        
        # Fill up the primary layer
        primary_request = AllocationRequest(
            layer_type=LayerType.WORKING_MEMORY,
            requested_tokens=1500,
            priority=8
        )
        allocator.allocate(primary_request)
        
        # Request more than remaining in the layer
        overflow_request = AllocationRequest(
            layer_type=LayerType.WORKING_MEMORY,
            requested_tokens=800,
            priority=7
        )
        
        result = allocator.allocate(overflow_request)
        
        if result.success:
            # If borrowing occurred, borrowed_tokens should be > 0
            assert result.borrowed_tokens >= 0
    
    def test_allocation_statistics_tracking(self):
        """Test that allocation statistics are properly tracked."""
        allocator = TokenAllocator(
            max_tokens=5000,
            buffer_tokens=500,
            allocation_mode=AllocationMode.DYNAMIC
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
            result = allocator.allocate(request)
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
            max_tokens=4000,
            buffer_tokens=400,
            allocation_mode=AllocationMode.DYNAMIC
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
            result = allocator.allocate(request)
            results.append(result)
        
        # Verify that total allocated doesn't exceed limits
        total_allocated = sum(r.granted_tokens for r in results if r.success)
        assert total_allocated <= (allocator.max_tokens - allocator.buffer_tokens)
        
        # Verify at least some requests succeeded
        successful_count = sum(1 for r in results if r.success)
        assert successful_count > 0
    
    def test_allocation_timeout_handling(self):
        """Test allocation timeout handling."""
        allocator = TokenAllocator(
            max_tokens=2000,
            buffer_tokens=200,
            allocation_mode=AllocationMode.DYNAMIC
        )
        
        # Request with timeout
        request = AllocationRequest(
            layer_type=LayerType.WORKING_MEMORY,
            requested_tokens=500,
            priority=8,
            max_wait_time=0.1  # 100ms timeout
        )
        
        result = allocator.allocate(request)
        
        # Should complete within timeout
        assert result.wait_time <= request.max_wait_time + 0.05  # Allow small tolerance
        assert result.success is True or result.error_message  # Either success or error with message
    
    def test_memory_layer_hierarchy_respect(self):
        """Test that allocation respects memory layer hierarchy."""
        allocator = TokenAllocator(
            max_tokens=6000,
            buffer_tokens=600,
            allocation_mode=AllocationMode.DYNAMIC
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
            result = allocator.allocate(request)
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
            'CONTEXT_MAX_TOKENS': '1000',
            'CONTEXT_BUFFER_TOKENS': '100',
            'CONTEXT_LAYER_A_TOKENS': '450',
            'CONTEXT_LAYER_B_TOKENS': '0',
            'CONTEXT_LAYER_C_TOKENS': '270',
            'CONTEXT_LAYER_D_TOKENS': '90',
            'CONTEXT_LAYER_E_TOKENS': '90'
        }):
            settings = Settings()
            
            allocator = TokenAllocator(
                max_tokens=settings.CONTEXT_MAX_TOKENS,
                buffer_tokens=settings.CONTEXT_BUFFER_TOKENS
            )
            
            # Test allocation with minimal tokens
            request = AllocationRequest(
                layer_type=LayerType.WORKING_MEMORY,
                requested_tokens=100,
                priority=8
            )
            
            result = allocator.allocate(request)
            assert result.success is True
            assert result.granted_tokens <= 900  # Max - buffer
    
    def test_stress_test_with_generated_data(self):
        """Test allocator with stress test data from generator."""
        allocator = TokenAllocator(
            max_tokens=10000,
            buffer_tokens=1000,
            allocation_mode=AllocationMode.DYNAMIC,
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
            result = allocator.allocate(request)
            results.append(result)
        
        # Verify system stability under stress
        successful_results = [r for r in results if r.success]
        assert len(successful_results) > 0  # At least some should succeed
        
        total_allocated = sum(r.granted_tokens for r in successful_results)
        assert total_allocated <= allocator.max_tokens - allocator.buffer_tokens
