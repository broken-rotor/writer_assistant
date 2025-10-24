"""
Token Allocator for Hierarchical Context Manager

Manages token budget allocation and enforcement across the hierarchical memory layers (WRI-14)
with support for dynamic reallocation, overflow detection, and real-time tracking.
"""

import logging
import time
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum

from .layers import LayerType, LayerConfig, LayerAllocation, LayerHierarchy
from .token_counter import TokenCounter, CountingStrategy

logger = logging.getLogger(__name__)


class AllocationMode(Enum):
    """Token allocation modes."""
    STATIC = "static"      # Fixed allocations per layer
    DYNAMIC = "dynamic"    # Dynamic reallocation based on usage
    ADAPTIVE = "adaptive"  # Machine learning-based allocation


class OverflowStrategy(Enum):
    """Strategies for handling token overflow."""
    REJECT = "reject"          # Reject requests that exceed budget
    TRUNCATE = "truncate"      # Truncate content to fit budget
    BORROW = "borrow"          # Borrow tokens from other layers
    REALLOCATE = "reallocate"  # Reallocate tokens dynamically


@dataclass
class AllocationRequest:
    """Request for token allocation."""
    layer_type: LayerType
    requested_tokens: int
    content_preview: str = ""
    priority: int = 0
    can_be_truncated: bool = True
    max_wait_time: float = 0.0  # Maximum time to wait for allocation
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AllocationResult:
    """Result of token allocation request."""
    request: AllocationRequest
    granted_tokens: int
    success: bool
    truncated: bool = False
    borrowed_tokens: int = 0
    wait_time: float = 0.0
    error_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AllocationStats:
    """Statistics for token allocation tracking."""
    total_requests: int = 0
    successful_requests: int = 0
    rejected_requests: int = 0
    truncated_requests: int = 0
    borrowed_tokens: int = 0
    average_wait_time: float = 0.0
    peak_utilization: float = 0.0
    overflow_events: int = 0


class TokenAllocator:
    """
    Advanced token allocator with hierarchical budget management.
    
    This class manages token allocation across the hierarchical memory layers (WRI-14),
    providing budget enforcement, overflow detection, and dynamic reallocation
    capabilities for the Writer Assistant's multi-agent storytelling system.
    """
    
    def __init__(
        self,
        total_budget: int,
        hierarchy: Optional[LayerHierarchy] = None,
        token_counter: Optional[TokenCounter] = None,
        mode: AllocationMode = AllocationMode.DYNAMIC,
        overflow_strategy: OverflowStrategy = OverflowStrategy.BORROW
    ):
        """
        Initialize the TokenAllocator.
        
        Args:
            total_budget: Total token budget to manage
            hierarchy: Layer hierarchy (creates default if None)
            token_counter: Token counter instance (creates default if None)
            mode: Allocation mode to use
            overflow_strategy: Strategy for handling overflows
        """
        self.total_budget = total_budget
        self.hierarchy = hierarchy or LayerHierarchy()
        self.token_counter = token_counter or TokenCounter()
        self.mode = mode
        self.overflow_strategy = overflow_strategy
        
        # Initialize layer allocations
        self._layer_allocations = self._initialize_allocations()
        
        # Tracking and statistics
        self._allocation_history: List[AllocationResult] = []
        self._stats = AllocationStats()
        self._start_time = time.time()
        
        # Configuration
        self._borrowing_enabled = True
        self._max_borrow_ratio = 0.3  # Maximum 30% of layer budget can be borrowed
        self._reallocation_threshold = 0.8  # Trigger reallocation at 80% utilization
        
        logger.info(f"TokenAllocator initialized with budget {total_budget}, mode {mode.value}")
    
    def _initialize_allocations(self) -> Dict[LayerType, LayerAllocation]:
        """Initialize layer allocations based on hierarchy and budget."""
        suggested_allocations = self.hierarchy.suggest_balanced_allocation(self.total_budget)
        
        allocations = {}
        for layer_type, allocated_tokens in suggested_allocations.items():
            allocations[layer_type] = LayerAllocation(
                layer_type=layer_type,
                allocated_tokens=allocated_tokens,
                used_tokens=0,
                reserved_tokens=0,
                borrowed_tokens=0,
                lent_tokens=0
            )
        
        return allocations
    
    def allocate_tokens(self, request: AllocationRequest) -> AllocationResult:
        """
        Allocate tokens for a request.
        
        Args:
            request: Token allocation request
            
        Returns:
            Allocation result with granted tokens and metadata
        """
        start_time = time.time()
        self._stats.total_requests += 1
        
        try:
            # Check if we can fulfill the request directly
            layer_allocation = self._layer_allocations[request.layer_type]
            available_tokens = layer_allocation.available_tokens
            
            if available_tokens >= request.requested_tokens:
                # Direct allocation possible
                result = self._grant_direct_allocation(request, start_time)
            else:
                # Need to handle overflow
                result = self._handle_overflow(request, available_tokens, start_time)
            
            # Update statistics
            self._update_stats(result)
            self._allocation_history.append(result)
            
            # Trigger reallocation if needed
            if self.mode == AllocationMode.DYNAMIC:
                self._check_reallocation_trigger()
            
            return result
            
        except Exception as e:
            logger.error(f"Error in token allocation: {e}")
            return AllocationResult(
                request=request,
                granted_tokens=0,
                success=False,
                wait_time=time.time() - start_time,
                error_message=str(e)
            )
    
    def _grant_direct_allocation(self, request: AllocationRequest, start_time: float) -> AllocationResult:
        """Grant tokens directly from the layer's available budget."""
        layer_allocation = self._layer_allocations[request.layer_type]
        layer_allocation.used_tokens += request.requested_tokens
        
        return AllocationResult(
            request=request,
            granted_tokens=request.requested_tokens,
            success=True,
            wait_time=time.time() - start_time,
            metadata={"allocation_type": "direct"}
        )
    
    def _handle_overflow(
        self,
        request: AllocationRequest,
        available_tokens: int,
        start_time: float
    ) -> AllocationResult:
        """Handle token allocation overflow based on strategy."""
        self._stats.overflow_events += 1
        
        if self.overflow_strategy == OverflowStrategy.REJECT:
            return self._reject_request(request, start_time, "Insufficient tokens")
        
        elif self.overflow_strategy == OverflowStrategy.TRUNCATE:
            return self._truncate_request(request, available_tokens, start_time)
        
        elif self.overflow_strategy == OverflowStrategy.BORROW:
            return self._borrow_tokens(request, available_tokens, start_time)
        
        elif self.overflow_strategy == OverflowStrategy.REALLOCATE:
            return self._reallocate_and_retry(request, start_time)
        
        else:
            return self._reject_request(request, start_time, "Unknown overflow strategy")
    
    def _reject_request(self, request: AllocationRequest, start_time: float, reason: str) -> AllocationResult:
        """Reject a token allocation request."""
        return AllocationResult(
            request=request,
            granted_tokens=0,
            success=False,
            wait_time=time.time() - start_time,
            error_message=reason,
            metadata={"allocation_type": "rejected"}
        )
    
    def _truncate_request(
        self,
        request: AllocationRequest,
        available_tokens: int,
        start_time: float
    ) -> AllocationResult:
        """Truncate request to fit available tokens."""
        if not request.can_be_truncated or available_tokens <= 0:
            return self._reject_request(request, start_time, "Cannot truncate request")
        
        # Grant available tokens
        layer_allocation = self._layer_allocations[request.layer_type]
        layer_allocation.used_tokens += available_tokens
        
        return AllocationResult(
            request=request,
            granted_tokens=available_tokens,
            success=True,
            truncated=True,
            wait_time=time.time() - start_time,
            metadata={"allocation_type": "truncated", "original_request": request.requested_tokens}
        )
    
    def _borrow_tokens(
        self,
        request: AllocationRequest,
        available_tokens: int,
        start_time: float
    ) -> AllocationResult:
        """Attempt to borrow tokens from other layers."""
        if not self._borrowing_enabled:
            return self._reject_request(request, start_time, "Borrowing disabled")
        
        needed_tokens = request.requested_tokens - available_tokens
        borrowed_tokens = self._find_borrowable_tokens(request.layer_type, needed_tokens)
        
        if borrowed_tokens < needed_tokens:
            # Partial borrowing - check if we can fulfill with available + borrowed
            total_available = available_tokens + borrowed_tokens
            if total_available >= request.requested_tokens:
                granted_tokens = request.requested_tokens
            elif request.can_be_truncated:
                granted_tokens = total_available
            else:
                return self._reject_request(request, start_time, "Insufficient tokens even with borrowing")
        else:
            granted_tokens = request.requested_tokens
        
        # Execute the borrowing
        self._execute_borrowing(request.layer_type, borrowed_tokens)
        
        # Update allocations
        layer_allocation = self._layer_allocations[request.layer_type]
        layer_allocation.used_tokens += granted_tokens
        layer_allocation.borrowed_tokens += borrowed_tokens
        
        return AllocationResult(
            request=request,
            granted_tokens=granted_tokens,
            success=True,
            truncated=granted_tokens < request.requested_tokens,
            borrowed_tokens=borrowed_tokens,
            wait_time=time.time() - start_time,
            metadata={"allocation_type": "borrowed"}
        )
    
    def _find_borrowable_tokens(self, requesting_layer: LayerType, needed_tokens: int) -> int:
        """Find tokens that can be borrowed from other layers."""
        borrowable_tokens = 0
        layer_config = self.hierarchy.get_layer_config(requesting_layer)
        
        # Check layers in order of preference (siblings, then ancestors, then descendants)
        candidate_layers = self._get_borrowing_candidates(requesting_layer)
        
        for candidate_layer in candidate_layers:
            candidate_allocation = self._layer_allocations[candidate_layer]
            candidate_config = self.hierarchy.get_layer_config(candidate_layer)
            
            if not candidate_config.can_lend:
                continue
            
            # Calculate how much this layer can lend
            max_lendable = int(candidate_allocation.allocated_tokens * self._max_borrow_ratio)
            current_lent = candidate_allocation.lent_tokens
            available_to_lend = max_lendable - current_lent
            
            # Don't lend if it would make the layer go below its minimum
            available_tokens = candidate_allocation.available_tokens
            min_tokens = candidate_config.min_tokens
            safe_to_lend = max(0, available_tokens - min_tokens)
            
            lendable = min(available_to_lend, safe_to_lend, needed_tokens - borrowable_tokens)
            
            if lendable > 0:
                borrowable_tokens += lendable
                
                if borrowable_tokens >= needed_tokens:
                    break
        
        return borrowable_tokens
    
    def _get_borrowing_candidates(self, requesting_layer: LayerType) -> List[LayerType]:
        """Get candidate layers for borrowing in order of preference."""
        candidates = []
        
        # Add sibling layers (same parent)
        parent = self.hierarchy.get_parent_layer(requesting_layer)
        if parent:
            siblings = self.hierarchy.get_child_layers(parent)
            candidates.extend([layer for layer in siblings if layer != requesting_layer])
        
        # Add ancestor layers
        ancestors = self.hierarchy.get_ancestor_layers(requesting_layer)
        candidates.extend(ancestors)
        
        # Add descendant layers
        descendants = self.hierarchy.get_descendant_layers(requesting_layer)
        candidates.extend(descendants)
        
        # Sort by priority (higher priority layers are less preferred for lending)
        candidates.sort(key=lambda l: self.hierarchy.get_layer_config(l).priority)
        
        return candidates
    
    def _execute_borrowing(self, borrowing_layer: LayerType, total_borrowed: int):
        """Execute the actual borrowing from candidate layers."""
        remaining_to_borrow = total_borrowed
        candidates = self._get_borrowing_candidates(borrowing_layer)
        
        for candidate_layer in candidates:
            if remaining_to_borrow <= 0:
                break
            
            candidate_allocation = self._layer_allocations[candidate_layer]
            candidate_config = self.hierarchy.get_layer_config(candidate_layer)
            
            # Calculate how much to borrow from this layer
            max_lendable = int(candidate_allocation.allocated_tokens * self._max_borrow_ratio)
            current_lent = candidate_allocation.lent_tokens
            available_to_lend = max_lendable - current_lent
            
            available_tokens = candidate_allocation.available_tokens
            min_tokens = candidate_config.min_tokens
            safe_to_lend = max(0, available_tokens - min_tokens)
            
            to_borrow = min(available_to_lend, safe_to_lend, remaining_to_borrow)
            
            if to_borrow > 0:
                candidate_allocation.lent_tokens += to_borrow
                remaining_to_borrow -= to_borrow
    
    def _reallocate_and_retry(self, request: AllocationRequest, start_time: float) -> AllocationResult:
        """Reallocate tokens dynamically and retry the request."""
        # Trigger dynamic reallocation
        self._perform_dynamic_reallocation()
        
        # Retry the request
        layer_allocation = self._layer_allocations[request.layer_type]
        available_tokens = layer_allocation.available_tokens
        
        if available_tokens >= request.requested_tokens:
            return self._grant_direct_allocation(request, start_time)
        else:
            # Still not enough, fall back to borrowing
            return self._borrow_tokens(request, available_tokens, start_time)
    
    def _perform_dynamic_reallocation(self):
        """Perform dynamic reallocation based on usage patterns."""
        logger.info("Performing dynamic token reallocation")
        
        # Analyze usage patterns
        usage_stats = self.get_layer_usage_stats()
        
        # Identify over-utilized and under-utilized layers
        over_utilized = []
        under_utilized = []
        
        for layer_type, allocation in self._layer_allocations.items():
            utilization = allocation.utilization
            if utilization > self._reallocation_threshold:
                over_utilized.append((layer_type, utilization))
            elif utilization < 0.5:  # Under 50% utilization
                under_utilized.append((layer_type, utilization))
        
        # Reallocate from under-utilized to over-utilized layers
        for over_layer, _ in over_utilized:
            over_config = self.hierarchy.get_layer_config(over_layer)
            over_allocation = self._layer_allocations[over_layer]
            
            for under_layer, _ in under_utilized:
                under_config = self.hierarchy.get_layer_config(under_layer)
                under_allocation = self._layer_allocations[under_layer]
                
                # Calculate how much we can reallocate
                under_excess = under_allocation.allocated_tokens - under_config.min_tokens
                over_need = over_config.max_tokens - over_allocation.allocated_tokens
                
                reallocation_amount = min(under_excess, over_need, under_allocation.available_tokens)
                
                if reallocation_amount > 0:
                    under_allocation.allocated_tokens -= reallocation_amount
                    over_allocation.allocated_tokens += reallocation_amount
                    
                    logger.info(f"Reallocated {reallocation_amount} tokens from {under_layer.value} to {over_layer.value}")
    
    def _check_reallocation_trigger(self):
        """Check if dynamic reallocation should be triggered."""
        # Check overall utilization
        total_used = sum(alloc.used_tokens for alloc in self._layer_allocations.values())
        overall_utilization = total_used / self.total_budget
        
        if overall_utilization > self._reallocation_threshold:
            # Check if any layer is significantly over-utilized
            for allocation in self._layer_allocations.values():
                if allocation.utilization > self._reallocation_threshold:
                    self._perform_dynamic_reallocation()
                    break
    
    def _update_stats(self, result: AllocationResult):
        """Update allocation statistics."""
        if result.success:
            self._stats.successful_requests += 1
            if result.truncated:
                self._stats.truncated_requests += 1
            if result.borrowed_tokens > 0:
                self._stats.borrowed_tokens += result.borrowed_tokens
        else:
            self._stats.rejected_requests += 1
        
        # Update average wait time
        total_wait_time = self._stats.average_wait_time * (self._stats.total_requests - 1) + result.wait_time
        self._stats.average_wait_time = total_wait_time / self._stats.total_requests
        
        # Update peak utilization
        current_utilization = self.get_overall_utilization()
        self._stats.peak_utilization = max(self._stats.peak_utilization, current_utilization)
    
    def release_tokens(self, layer_type: LayerType, tokens: int) -> bool:
        """
        Release tokens back to a layer's budget.
        
        Args:
            layer_type: Layer to release tokens to
            tokens: Number of tokens to release
            
        Returns:
            True if successful, False otherwise
        """
        try:
            allocation = self._layer_allocations[layer_type]
            
            if allocation.used_tokens >= tokens:
                allocation.used_tokens -= tokens
                logger.debug(f"Released {tokens} tokens to {layer_type.value}")
                return True
            else:
                logger.warning(f"Cannot release {tokens} tokens from {layer_type.value}, only {allocation.used_tokens} in use")
                return False
                
        except Exception as e:
            logger.error(f"Error releasing tokens: {e}")
            return False
    
    def reserve_tokens(self, layer_type: LayerType, tokens: int) -> bool:
        """
        Reserve tokens for future use.
        
        Args:
            layer_type: Layer to reserve tokens in
            tokens: Number of tokens to reserve
            
        Returns:
            True if successful, False otherwise
        """
        try:
            allocation = self._layer_allocations[layer_type]
            
            if allocation.available_tokens >= tokens:
                allocation.reserved_tokens += tokens
                logger.debug(f"Reserved {tokens} tokens in {layer_type.value}")
                return True
            else:
                logger.warning(f"Cannot reserve {tokens} tokens in {layer_type.value}, only {allocation.available_tokens} available")
                return False
                
        except Exception as e:
            logger.error(f"Error reserving tokens: {e}")
            return False
    
    def get_layer_allocation(self, layer_type: LayerType) -> LayerAllocation:
        """Get current allocation for a specific layer."""
        return self._layer_allocations[layer_type]
    
    def get_all_allocations(self) -> Dict[LayerType, LayerAllocation]:
        """Get all current layer allocations."""
        return self._layer_allocations.copy()
    
    def get_overall_utilization(self) -> float:
        """Get overall token utilization across all layers."""
        total_used = sum(alloc.used_tokens + alloc.reserved_tokens for alloc in self._layer_allocations.values())
        return total_used / self.total_budget if self.total_budget > 0 else 0.0
    
    def get_layer_usage_stats(self) -> Dict[str, Any]:
        """Get detailed usage statistics for all layers."""
        stats = {}
        
        for layer_type, allocation in self._layer_allocations.items():
            stats[layer_type.value] = {
                "allocated_tokens": allocation.allocated_tokens,
                "used_tokens": allocation.used_tokens,
                "reserved_tokens": allocation.reserved_tokens,
                "borrowed_tokens": allocation.borrowed_tokens,
                "lent_tokens": allocation.lent_tokens,
                "available_tokens": allocation.available_tokens,
                "utilization": allocation.utilization
            }
        
        return stats
    
    def get_allocation_stats(self) -> AllocationStats:
        """Get overall allocation statistics."""
        return self._stats
    
    def reset_allocations(self, new_budget: Optional[int] = None):
        """
        Reset all allocations to initial state.
        
        Args:
            new_budget: New total budget (keeps current if None)
        """
        if new_budget is not None:
            self.total_budget = new_budget
        
        self._layer_allocations = self._initialize_allocations()
        self._allocation_history.clear()
        self._stats = AllocationStats()
        self._start_time = time.time()
        
        logger.info(f"Token allocations reset with budget {self.total_budget}")
    
    def validate_allocations(self) -> Dict[str, Any]:
        """Validate current allocations against constraints."""
        current_allocations = {
            layer_type: allocation.allocated_tokens
            for layer_type, allocation in self._layer_allocations.items()
        }
        
        validation_result = self.hierarchy.validate_layer_allocation(current_allocations)
        
        # Add runtime validation
        total_allocated = sum(alloc.allocated_tokens for alloc in self._layer_allocations.values())
        total_used = sum(alloc.used_tokens for alloc in self._layer_allocations.values())
        total_borrowed = sum(alloc.borrowed_tokens for alloc in self._layer_allocations.values())
        total_lent = sum(alloc.lent_tokens for alloc in self._layer_allocations.values())
        
        validation_result.update({
            "runtime_validation": {
                "total_budget": self.total_budget,
                "total_allocated": total_allocated,
                "total_used": total_used,
                "total_borrowed": total_borrowed,
                "total_lent": total_lent,
                "budget_exceeded": total_allocated > self.total_budget,
                "borrowing_balanced": total_borrowed == total_lent
            }
        })
        
        return validation_result
