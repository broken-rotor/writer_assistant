"""
Context Manager for Writer Assistant

This module provides the core context management functionality for the Writer Assistant,
including context item management, context analysis, and optimization coordination.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from app.services.token_management import LayerType, TokenCounter, ContentType as TokenContentType, TokenAllocator
from app.core.config import settings
from app.services.context_distillation import ContextDistiller, DistillationConfig
from app.services.content_prioritization import LayeredPrioritizer, PrioritizationConfig
from app.services.llm_inference import get_llm

logger = logging.getLogger(__name__)


class ContextType(Enum):
    """Types of context content for categorization and prioritization."""
    SYSTEM = "system"
    STORY = "story"
    CHARACTER = "character"
    WORLD = "world"
    FEEDBACK = "feedback"
    MEMORY = "memory"


@dataclass
class ContextItem:
    """
    Represents a single item of context with metadata for optimization.
    
    Attributes:
        content: The actual text content
        context_type: Type of context for categorization
        priority: Priority level (1-10, higher is more important)
        layer_type: Memory layer type for token management
        metadata: Additional metadata for processing
    """
    content: str
    context_type: ContextType
    priority: int
    layer_type: LayerType
    metadata: Dict[str, Any]


@dataclass
class ContextAnalysis:
    """
    Analysis results for a set of context items.
    
    Attributes:
        total_tokens: Total token count across all items
        items_by_type: Context items grouped by type
        priority_distribution: Token distribution by priority level
        optimization_needed: Whether optimization is recommended
        compression_ratio: Potential compression ratio if optimized
        recommendations: List of optimization recommendations
    """
    total_tokens: int
    items_by_type: Dict[ContextType, List[ContextItem]]
    priority_distribution: Dict[int, int]
    optimization_needed: bool
    compression_ratio: float
    recommendations: List[str]


class ContextManager:
    """
    Core context management system that coordinates context optimization,
    distillation, and prioritization.
    """
    
    def __init__(
        self,
        max_context_tokens: int = 32000,
        distillation_threshold: int = 6000,
        enable_compression: bool = True
    ):
        """
        Initialize the context manager.
        
        Args:
            max_context_tokens: Maximum tokens allowed in context
            distillation_threshold: Token threshold to trigger distillation
            enable_compression: Whether to enable content compression
        """
        self.max_context_tokens = max_context_tokens
        self.distillation_threshold = distillation_threshold
        self.enable_compression = enable_compression
        
        # Initialize components
        self.token_counter = TokenCounter(model_path=settings.MODEL_PATH)
        self.token_allocator = TokenAllocator(total_budget=max_context_tokens)
        self.llm_service = get_llm()
        self.distiller = ContextDistiller(
            token_counter=self.token_counter,
            token_allocator=self.token_allocator,
            llm_service=self.llm_service,
            config=DistillationConfig(
                max_summary_depth=3,
                preserve_key_plot_points=True,
                preserve_character_arcs=True,
                preserve_emotional_beats=True
            )
        )
        self.prioritizer = LayeredPrioritizer(
            config=PrioritizationConfig(
                token_budget=max_context_tokens,
                max_items_per_category=20,
                min_score_threshold=0.1
            )
        )
        
        logger.info(f"ContextManager initialized with max_tokens={max_context_tokens}, threshold={distillation_threshold}")
    
    def analyze_context(self, context_items: List[ContextItem]) -> ContextAnalysis:
        """
        Analyze a set of context items to determine optimization needs.
        
        Args:
            context_items: List of context items to analyze
            
        Returns:
            ContextAnalysis with analysis results
        """
        # Count total tokens
        total_tokens = 0
        items_by_type = {}
        priority_distribution = {}
        
        for item in context_items:
            # Count tokens in content
            token_count = self.token_counter.count_tokens(
                item.content, 
                TokenContentType.UNKNOWN
            ).token_count
            total_tokens += token_count
            
            # Group by type
            if item.context_type not in items_by_type:
                items_by_type[item.context_type] = []
            items_by_type[item.context_type].append(item)
            
            # Track priority distribution
            if item.priority not in priority_distribution:
                priority_distribution[item.priority] = 0
            priority_distribution[item.priority] += token_count
        
        # Determine if optimization is needed
        optimization_needed = (
            self.enable_compression and 
            total_tokens > self.distillation_threshold
        )
        
        # Estimate compression ratio
        compression_ratio = 0.3 if optimization_needed else 1.0
        
        # Generate recommendations based on analysis
        recommendations = self._generate_recommendations(
            total_tokens, items_by_type, priority_distribution, optimization_needed
        )
        
        return ContextAnalysis(
            total_tokens=total_tokens,
            items_by_type=items_by_type,
            priority_distribution=priority_distribution,
            optimization_needed=optimization_needed,
            compression_ratio=compression_ratio,
            recommendations=recommendations
        )
    
    def _generate_recommendations(
        self,
        total_tokens: int,
        items_by_type: Dict[ContextType, List[ContextItem]],
        priority_distribution: Dict[int, int],
        optimization_needed: bool
    ) -> List[str]:
        """
        Generate optimization recommendations based on context analysis.
        
        Args:
            total_tokens: Total token count
            items_by_type: Context items grouped by type
            priority_distribution: Token distribution by priority
            optimization_needed: Whether optimization is needed
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        if not optimization_needed:
            recommendations.append("Context is within optimal size limits")
            return recommendations
        
        # Token-based recommendations
        if total_tokens > self.max_context_tokens:
            recommendations.append(f"Context exceeds maximum limit ({total_tokens} > {self.max_context_tokens} tokens)")
        elif total_tokens > self.distillation_threshold:
            recommendations.append(f"Context approaching limit, consider optimization ({total_tokens} > {self.distillation_threshold} tokens)")
        
        # Type-based recommendations
        for context_type, items in items_by_type.items():
            item_count = len(items)
            if item_count > 10:  # Arbitrary threshold for too many items
                recommendations.append(f"Consider reducing {context_type.value} items (currently {item_count})")
        
        # Priority-based recommendations
        low_priority_tokens = sum(tokens for priority, tokens in priority_distribution.items() if priority <= 3)
        if low_priority_tokens > total_tokens * 0.3:  # More than 30% low priority
            recommendations.append("Consider removing low-priority content to optimize context")
        
        # Compression recommendations
        if optimization_needed:
            recommendations.append("Apply context compression to reduce token usage")
            recommendations.append("Prioritize high-importance content during optimization")
        
        return recommendations
    
    def optimize_context(
        self, 
        context_items: List[ContextItem],
        target_tokens: Optional[int] = None
    ) -> Tuple[List[ContextItem], Dict[str, Any]]:
        """
        Optimize a set of context items to fit within token limits.
        
        Args:
            context_items: List of context items to optimize
            target_tokens: Target token count (defaults to max_context_tokens)
            
        Returns:
            Tuple of (optimized_items, optimization_metadata)
        """
        if target_tokens is None:
            target_tokens = self.max_context_tokens
        
        # Analyze current context
        analysis = self.analyze_context(context_items)
        
        if not analysis.optimization_needed:
            logger.info("No optimization needed, returning original context")
            return context_items, {"optimization_applied": False, "original_tokens": analysis.total_tokens}
        
        logger.info(f"Optimizing context: {analysis.total_tokens} tokens -> target {target_tokens}")
        
        # Sort items by priority (highest first)
        sorted_items = sorted(context_items, key=lambda x: x.priority, reverse=True)
        
        optimized_items = []
        current_tokens = 0
        
        for item in sorted_items:
            item_tokens = self.token_counter.count_tokens(
                item.content, 
                TokenContentType.UNKNOWN
            ).token_count
            
            # Always include highest priority items (priority >= 9)
            if item.priority >= 9:
                optimized_items.append(item)
                current_tokens += item_tokens
                continue
            
            # For lower priority items, check if we have space
            if current_tokens + item_tokens <= target_tokens:
                optimized_items.append(item)
                current_tokens += item_tokens
            else:
                # Try to compress the item if possible
                if self.enable_compression and len(item.content) > 500:
                    try:
                        compressed_content = self._compress_content(item.content, item.context_type)
                        compressed_tokens = self.token_counter.count_tokens(
                            compressed_content, 
                            TokenContentType.UNKNOWN
                        ).token_count
                        
                        if current_tokens + compressed_tokens <= target_tokens:
                            compressed_item = ContextItem(
                                content=compressed_content,
                                context_type=item.context_type,
                                priority=item.priority,
                                layer_type=item.layer_type,
                                metadata={**item.metadata, "compressed": True}
                            )
                            optimized_items.append(compressed_item)
                            current_tokens += compressed_tokens
                    except Exception as e:
                        logger.warning(f"Failed to compress content: {e}")
        
        optimization_metadata = {
            "optimization_applied": True,
            "original_tokens": analysis.total_tokens,
            "optimized_tokens": current_tokens,
            "compression_ratio": current_tokens / analysis.total_tokens if analysis.total_tokens > 0 else 1.0,
            "items_removed": len(context_items) - len(optimized_items)
        }
        
        logger.info(f"Context optimization complete: {analysis.total_tokens} -> {current_tokens} tokens")
        
        return optimized_items, optimization_metadata
    
    def _compress_content(self, content: str, context_type: ContextType) -> str:
        """
        Compress content using the distillation service.
        
        Args:
            content: Content to compress
            context_type: Type of content for appropriate compression strategy
            
        Returns:
            Compressed content
        """
        try:
            # Map context types to distillation content types
            content_type_mapping = {
                ContextType.STORY: "story_summary",
                ContextType.CHARACTER: "character_profile",
                ContextType.WORLD: "world_building",
                ContextType.FEEDBACK: "feedback_summary",
                ContextType.MEMORY: "memory_summary",
                ContextType.SYSTEM: "system_prompt"  # Usually not compressed
            }
            
            distillation_type = content_type_mapping.get(context_type, "general")
            
            # Use distillation service to compress
            result = self.distiller.distill_content(
                content=content,
                content_type=distillation_type,
                target_length=len(content) // 3  # Aim for 1/3 original length
            )
            
            return result.distilled_content
            
        except Exception as e:
            logger.warning(f"Content compression failed: {e}")
            # Return truncated content as fallback
            return content[:len(content) // 2] + "..."
