"""
Core Context Manager for Writer Assistant

This module provides the central ContextManager service that orchestrates
token management and context distillation for intelligent context handling
across all AI generation endpoints.

Key Features:
- Intelligent context optimization using token allocation and distillation
- Hierarchical memory management with layer priorities
- Content validation and error handling
- Integration with existing token management and context distillation services
- Context statistics and analysis reporting
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from app.services.token_management import (
    TokenCounter, TokenAllocator, LayerHierarchy, LayerType, LayerConfig,
    AllocationRequest, AllocationResult, AllocationMode, OverflowStrategy,
    ContentType, CountingStrategy
)
from app.services.context_distillation import (
    ContextDistiller, DistillationConfig, DistillationResult,
    DistillationTrigger
)

logger = logging.getLogger(__name__)


class ContextType(Enum):
    """Types of context content for management."""
    SYSTEM = "system"
    STORY = "story"
    CHARACTER = "character"
    WORLD = "world"
    FEEDBACK = "feedback"
    MEMORY = "memory"


@dataclass
class ContextItem:
    """Individual context item with metadata."""
    content: str
    context_type: ContextType
    priority: int = 0
    layer_type: LayerType = LayerType.WORKING_MEMORY
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ContextAnalysis:
    """Analysis results for context content."""
    total_tokens: int
    tokens_by_type: Dict[ContextType, int]
    tokens_by_layer: Dict[LayerType, int]
    optimization_needed: bool
    compression_candidates: List[str]
    recommendations: List[str]


@dataclass
class ContextOptimizationResult:
    """Results of context optimization process."""
    optimized_content: Dict[ContextType, str]
    original_tokens: int
    optimized_tokens: int
    compression_ratio: float
    distillation_applied: bool
    layers_compressed: List[LayerType]
    statistics: Dict[str, Any]


class ContextManager:
    """
    Central Context Manager that orchestrates token management and context distillation.
    
    This service provides intelligent context handling for all AI generation endpoints,
    managing token budgets, content prioritization, and context optimization.
    """
    
    def __init__(
        self,
        max_context_tokens: int = 8000,
        distillation_threshold: int = 6000,
        enable_compression: bool = True
    ):
        """
        Initialize the Context Manager.
        
        Args:
            max_context_tokens: Maximum tokens allowed in context
            distillation_threshold: Token count that triggers distillation
            enable_compression: Whether to enable automatic compression
        """
        self.max_context_tokens = max_context_tokens
        self.distillation_threshold = distillation_threshold
        self.enable_compression = enable_compression
        
        # Initialize services
        self.token_counter = TokenCounter()
        self.token_allocator = TokenAllocator()
        self.layer_hierarchy = LayerHierarchy()
        
        # Initialize context distiller with configuration
        distillation_config = DistillationConfig(
            max_tokens_per_layer=2000,
            compression_ratio=0.3,
            preserve_recent_content=True,
            layer_priorities=self.layer_hierarchy.get_default_priorities()
        )
        self.context_distiller = ContextDistiller(distillation_config)
        
        logger.info(f"ContextManager initialized with max_tokens={max_context_tokens}")
    
    def analyze_context(self, context_items: List[ContextItem]) -> ContextAnalysis:
        """
        Analyze context items and provide optimization recommendations.
        
        Args:
            context_items: List of context items to analyze
            
        Returns:
            ContextAnalysis with token counts and recommendations
        """
        try:
            # Count tokens by type and layer
            total_tokens = 0
            tokens_by_type = {ct: 0 for ct in ContextType}
            tokens_by_layer = {lt: 0 for lt in LayerType}
            
            for item in context_items:
                token_count = self.token_counter.count_tokens(
                    item.content, 
                    ContentType.TEXT
                ).total_tokens
                
                total_tokens += token_count
                tokens_by_type[item.context_type] += token_count
                tokens_by_layer[item.layer_type] += token_count
            
            # Determine if optimization is needed
            optimization_needed = total_tokens > self.distillation_threshold
            
            # Identify compression candidates
            compression_candidates = []
            recommendations = []
            
            if optimization_needed:
                # Find layers with high token counts that can be compressed
                for layer_type, token_count in tokens_by_layer.items():
                    if (layer_type != LayerType.WORKING_MEMORY and 
                        token_count > 1000):
                        compression_candidates.append(layer_type.value)
                
                recommendations.append(f"Context exceeds threshold ({total_tokens} > {self.distillation_threshold})")
                recommendations.append("Consider applying context distillation")
                
                if compression_candidates:
                    recommendations.append(f"Compression recommended for: {', '.join(compression_candidates)}")
            else:
                recommendations.append("Context within optimal range")
            
            return ContextAnalysis(
                total_tokens=total_tokens,
                tokens_by_type=tokens_by_type,
                tokens_by_layer=tokens_by_layer,
                optimization_needed=optimization_needed,
                compression_candidates=compression_candidates,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error analyzing context: {str(e)}")
            raise
    
    def optimize_context(
        self, 
        context_items: List[ContextItem],
        target_tokens: Optional[int] = None
    ) -> ContextOptimizationResult:
        """
        Optimize context items to fit within token budget.
        
        Args:
            context_items: List of context items to optimize
            target_tokens: Target token count (defaults to max_context_tokens)
            
        Returns:
            ContextOptimizationResult with optimized content
        """
        if target_tokens is None:
            target_tokens = self.max_context_tokens
        
        try:
            # Analyze current context
            analysis = self.analyze_context(context_items)
            original_tokens = analysis.total_tokens
            
            logger.info(f"Optimizing context: {original_tokens} tokens -> target {target_tokens}")
            
            # If no optimization needed, return original content
            if not analysis.optimization_needed and original_tokens <= target_tokens:
                optimized_content = self._items_to_content_dict(context_items)
                return ContextOptimizationResult(
                    optimized_content=optimized_content,
                    original_tokens=original_tokens,
                    optimized_tokens=original_tokens,
                    compression_ratio=1.0,
                    distillation_applied=False,
                    layers_compressed=[],
                    statistics={"optimization_needed": False}
                )
            
            # Apply context distillation if enabled
            distillation_applied = False
            layers_compressed = []
            
            if self.enable_compression and original_tokens > target_tokens:
                # Organize content by layers for distillation
                layer_content = self._organize_by_layers(context_items)
                
                # Apply distillation to layers that exceed limits
                for layer_type, content in layer_content.items():
                    if layer_type == LayerType.WORKING_MEMORY:
                        continue  # Never compress working memory
                    
                    layer_tokens = self.token_counter.count_tokens(
                        content, ContentType.TEXT
                    ).total_tokens
                    
                    if layer_tokens > 1500:  # Threshold for layer compression
                        try:
                            distillation_result = self.context_distiller.distill_content(
                                content=content,
                                layer_type=layer_type,
                                trigger=DistillationTrigger.TOKEN_OVERFLOW
                            )
                            
                            if distillation_result.success:
                                layer_content[layer_type] = distillation_result.distilled_content
                                layers_compressed.append(layer_type)
                                distillation_applied = True
                                logger.info(f"Compressed layer {layer_type.value}: {layer_tokens} -> {distillation_result.final_token_count} tokens")
                        
                        except Exception as e:
                            logger.warning(f"Failed to compress layer {layer_type.value}: {str(e)}")
                
                # Update context items with compressed content
                context_items = self._update_items_with_compressed_content(
                    context_items, layer_content
                )
            
            # Calculate final metrics
            optimized_content = self._items_to_content_dict(context_items)
            optimized_tokens = sum(
                self.token_counter.count_tokens(content, ContentType.TEXT).total_tokens
                for content in optimized_content.values()
            )
            
            compression_ratio = optimized_tokens / original_tokens if original_tokens > 0 else 1.0
            
            statistics = {
                "optimization_applied": True,
                "distillation_applied": distillation_applied,
                "layers_compressed": len(layers_compressed),
                "compression_ratio": compression_ratio,
                "token_reduction": original_tokens - optimized_tokens
            }
            
            logger.info(f"Context optimization complete: {original_tokens} -> {optimized_tokens} tokens (ratio: {compression_ratio:.2f})")
            
            return ContextOptimizationResult(
                optimized_content=optimized_content,
                original_tokens=original_tokens,
                optimized_tokens=optimized_tokens,
                compression_ratio=compression_ratio,
                distillation_applied=distillation_applied,
                layers_compressed=layers_compressed,
                statistics=statistics
            )
            
        except Exception as e:
            logger.error(f"Error optimizing context: {str(e)}")
            raise
    
    def validate_context(self, context_items: List[ContextItem]) -> Tuple[bool, List[str]]:
        """
        Validate context items for structure and content integrity.
        
        Args:
            context_items: List of context items to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        try:
            # Check for empty or invalid items
            for i, item in enumerate(context_items):
                if not item.content or not item.content.strip():
                    errors.append(f"Item {i}: Empty content")
                
                if not isinstance(item.context_type, ContextType):
                    errors.append(f"Item {i}: Invalid context type")
                
                if not isinstance(item.layer_type, LayerType):
                    errors.append(f"Item {i}: Invalid layer type")
                
                if item.priority < 0:
                    errors.append(f"Item {i}: Invalid priority (must be >= 0)")
            
            # Check total token count
            analysis = self.analyze_context(context_items)
            if analysis.total_tokens > self.max_context_tokens * 2:  # Allow some overflow
                errors.append(f"Total tokens ({analysis.total_tokens}) far exceeds maximum ({self.max_context_tokens})")
            
            # Check for required context types
            present_types = {item.context_type for item in context_items}
            if ContextType.SYSTEM not in present_types:
                errors.append("Missing required SYSTEM context")
            
            is_valid = len(errors) == 0
            
            if is_valid:
                logger.debug("Context validation passed")
            else:
                logger.warning(f"Context validation failed: {len(errors)} errors")
            
            return is_valid, errors
            
        except Exception as e:
            logger.error(f"Error validating context: {str(e)}")
            return False, [f"Validation error: {str(e)}"]
    
    def _items_to_content_dict(self, context_items: List[ContextItem]) -> Dict[ContextType, str]:
        """Convert context items to content dictionary grouped by type."""
        content_dict = {ct: "" for ct in ContextType}
        
        for item in context_items:
            if content_dict[item.context_type]:
                content_dict[item.context_type] += "\n\n" + item.content
            else:
                content_dict[item.context_type] = item.content
        
        return content_dict
    
    def _organize_by_layers(self, context_items: List[ContextItem]) -> Dict[LayerType, str]:
        """Organize context items by layer type."""
        layer_content = {lt: "" for lt in LayerType}
        
        for item in context_items:
            if layer_content[item.layer_type]:
                layer_content[item.layer_type] += "\n\n" + item.content
            else:
                layer_content[item.layer_type] = item.content
        
        return layer_content
    
    def _update_items_with_compressed_content(
        self, 
        context_items: List[ContextItem], 
        layer_content: Dict[LayerType, str]
    ) -> List[ContextItem]:
        """Update context items with compressed layer content."""
        # Group items by layer
        items_by_layer = {}
        for item in context_items:
            if item.layer_type not in items_by_layer:
                items_by_layer[item.layer_type] = []
            items_by_layer[item.layer_type].append(item)
        
        # Update items with compressed content
        updated_items = []
        for layer_type, compressed_content in layer_content.items():
            if layer_type in items_by_layer and compressed_content:
                # For compressed layers, create a single item with the compressed content
                first_item = items_by_layer[layer_type][0]
                updated_item = ContextItem(
                    content=compressed_content,
                    context_type=first_item.context_type,
                    priority=first_item.priority,
                    layer_type=layer_type,
                    metadata={**first_item.metadata, "compressed": True}
                )
                updated_items.append(updated_item)
            elif layer_type in items_by_layer:
                # For non-compressed layers, keep original items
                updated_items.extend(items_by_layer[layer_type])
        
        return updated_items
    
    def get_context_statistics(self, context_items: List[ContextItem]) -> Dict[str, Any]:
        """Get comprehensive statistics about context items."""
        try:
            analysis = self.analyze_context(context_items)
            
            return {
                "total_items": len(context_items),
                "total_tokens": analysis.total_tokens,
                "tokens_by_type": {ct.value: count for ct, count in analysis.tokens_by_type.items()},
                "tokens_by_layer": {lt.value: count for lt, count in analysis.tokens_by_layer.items()},
                "optimization_needed": analysis.optimization_needed,
                "compression_candidates": analysis.compression_candidates,
                "recommendations": analysis.recommendations,
                "utilization_ratio": analysis.total_tokens / self.max_context_tokens,
                "distillation_threshold": self.distillation_threshold,
                "max_context_tokens": self.max_context_tokens
            }
            
        except Exception as e:
            logger.error(f"Error getting context statistics: {str(e)}")
            return {"error": str(e)}
