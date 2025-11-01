"""
Context Distiller for intelligent content compression and summarization.

This module implements the core context distillation system that handles
overflow and rolling summarization of story content across hierarchical layers.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import json

from app.core.config import settings

from ..token_management import (
    TokenCounter, TokenAllocator, LayerType, LayerHierarchy,
    AllocationRequest, AllocationResult, OverflowStrategy
)
from ..llm_inference import LLMInference
from .summarization_strategies import SummarizationStrategy, PlotSummaryStrategy

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Types of content that can be distilled."""
    PLOT_SUMMARY = "plot_summary"
    CHARACTER_DEVELOPMENT = "character_development"
    DIALOGUE = "dialogue"
    EVENT_SEQUENCE = "event_sequence"
    EMOTIONAL_MOMENT = "emotional_moment"
    WORLD_BUILDING = "world_building"
    MIXED_CONTENT = "mixed_content"


class DistillationTrigger(Enum):
    """Triggers for context distillation."""
    TOKEN_THRESHOLD = "token_threshold"
    LAYER_OVERFLOW = "layer_overflow"
    MANUAL_REQUEST = "manual_request"
    SCHEDULED_COMPRESSION = "scheduled_compression"


@dataclass
class DistillationConfig:
    """Configuration for context distillation operations."""

    # Token thresholds
    rolling_summary_threshold: int = 25000  # 25k token threshold as per requirements
    emergency_compression_threshold: int = 30000

    # Compression ratios by content type
    compression_ratios: Dict[ContentType, float] = field(default_factory=lambda: {
        ContentType.PLOT_SUMMARY: 0.3,  # Compress to 30% of original
        ContentType.CHARACTER_DEVELOPMENT: 0.4,  # Preserve more character details
        ContentType.DIALOGUE: 0.2,  # Dialogue can be heavily compressed
        ContentType.EVENT_SEQUENCE: 0.35,
        ContentType.EMOTIONAL_MOMENT: 0.5,  # Preserve emotional content
        ContentType.WORLD_BUILDING: 0.4,
        ContentType.MIXED_CONTENT: 0.35
    })

    # Layer priorities for overflow handling
    layer_priorities: Dict[LayerType, int] = field(default_factory=lambda: {
        LayerType.WORKING_MEMORY: 5,  # Highest priority - never compress
        LayerType.EPISODIC_MEMORY: 4,
        LayerType.SEMANTIC_MEMORY: 3,
        LayerType.LONG_TERM_MEMORY: 2,
        LayerType.AGENT_SPECIFIC_MEMORY: 1  # Lowest priority - compress first
    })

    # Quality preservation settings
    preserve_key_plot_points: bool = True
    preserve_character_arcs: bool = True
    preserve_emotional_beats: bool = True
    min_summary_quality_score: float = 0.7

    # LLM settings for summarization
    llm_temperature: float = field(default_factory=lambda: settings.DISTILLATION_GENERAL_TEMPERATURE)  # Lower temperature for consistent summaries
    llm_max_tokens: int = 2048

    # Summary-of-summary settings
    max_summary_depth: int = 3  # Maximum levels of summary-of-summary
    summary_merge_threshold: int = 5  # Merge summaries when more than 5 exist


@dataclass
class DistillationResult:
    """Result of a context distillation operation."""

    success: bool
    original_token_count: int
    compressed_token_count: int
    compression_ratio: float
    content_type: ContentType
    trigger: DistillationTrigger
    layer_affected: LayerType

    # Quality metrics
    key_information_preserved: List[str] = field(default_factory=list)
    information_lost: List[str] = field(default_factory=list)
    quality_score: float = 0.0

    # Output content
    original_content: str = ""
    compressed_content: str = ""
    summary_metadata: Dict[str, Any] = field(default_factory=dict)

    # Error information
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


class ContextDistiller:
    """
    Main context distillation engine for intelligent content compression.

    This class handles rolling summarization, hierarchical compression,
    and overflow management across the Writer Assistant's memory layers.
    """

    def __init__(
        self,
        token_counter: TokenCounter,
        token_allocator: TokenAllocator,
        llm_service: LLMInference,
        config: Optional[DistillationConfig] = None
    ):
        """
        Initialize the Context Distiller.

        Args:
            token_counter: Token counting service
            token_allocator: Token allocation service
            llm_service: LLM service for summarization
            config: Distillation configuration
        """
        self.token_counter = token_counter
        self.token_allocator = token_allocator
        self.llm_service = llm_service
        self.config = config or DistillationConfig()
        self.layer_hierarchy = LayerHierarchy()

        # Initialize summarization strategies
        self._strategies: Dict[ContentType, SummarizationStrategy] = {}
        self._initialize_strategies()

        # Track distillation history
        self._distillation_history: List[DistillationResult] = []

        logger.info("ContextDistiller initialized with config: %s", self.config)

    def _initialize_strategies(self) -> None:
        """Initialize summarization strategies for different content types."""
        from .summarization_strategies import (
            PlotSummaryStrategy, CharacterDevelopmentStrategy,
            DialogueSummaryStrategy, EventSequenceStrategy,
            EmotionalMomentStrategy, WorldBuildingStrategy
        )

        self._strategies = {
            ContentType.PLOT_SUMMARY: PlotSummaryStrategy(self.llm_service),
            ContentType.CHARACTER_DEVELOPMENT: CharacterDevelopmentStrategy(self.llm_service),
            ContentType.DIALOGUE: DialogueSummaryStrategy(self.llm_service),
            ContentType.EVENT_SEQUENCE: EventSequenceStrategy(self.llm_service),
            ContentType.EMOTIONAL_MOMENT: EmotionalMomentStrategy(self.llm_service),
            ContentType.WORLD_BUILDING: WorldBuildingStrategy(self.llm_service),
            ContentType.MIXED_CONTENT: PlotSummaryStrategy(self.llm_service)  # Default strategy
        }

    def check_distillation_needed(
        self,
        layer_contents: Dict[LayerType, str],
        current_allocation: Dict[LayerType, int]
    ) -> Tuple[bool, DistillationTrigger, Optional[LayerType]]:
        """
        Check if context distillation is needed.

        Args:
            layer_contents: Current content in each layer
            current_allocation: Current token allocation per layer

        Returns:
            Tuple of (needs_distillation, trigger_type, affected_layer)
        """
        # Calculate total token usage
        total_tokens = 0
        layer_usage = {}

        for layer_type, content in layer_contents.items():
            token_count = self.token_counter.count_tokens(content)
            layer_usage[layer_type] = token_count
            total_tokens += token_count

        # Check rolling summary threshold
        if total_tokens >= self.config.rolling_summary_threshold:
            logger.info(f"Rolling summary threshold reached: {total_tokens} >= {self.config.rolling_summary_threshold}")
            return True, DistillationTrigger.TOKEN_THRESHOLD, None

        # Check emergency compression threshold
        if total_tokens >= self.config.emergency_compression_threshold:
            logger.warning(
                f"Emergency compression threshold reached: {total_tokens} >= {
                    self.config.emergency_compression_threshold}")
            return True, DistillationTrigger.TOKEN_THRESHOLD, None

        # Check for layer overflow
        for layer_type, usage in layer_usage.items():
            allocated = current_allocation.get(layer_type, 0)
            if usage > allocated * 1.1:  # 10% overflow tolerance
                logger.info(f"Layer overflow detected in {layer_type}: {usage} > {allocated}")
                return True, DistillationTrigger.LAYER_OVERFLOW, layer_type

        return False, DistillationTrigger.MANUAL_REQUEST, None

    def distill_content(
        self,
        content: str,
        content_type: ContentType,
        target_layer: LayerType,
        trigger: DistillationTrigger,
        context: Optional[Dict[str, Any]] = None
    ) -> DistillationResult:
        """
        Distill content using appropriate summarization strategy.

        Args:
            content: Content to distill
            content_type: Type of content being distilled
            target_layer: Layer where distilled content will be stored
            trigger: What triggered this distillation
            context: Additional context for summarization

        Returns:
            DistillationResult with compression details
        """
        try:
            logger.info(f"Starting distillation: {content_type} for {target_layer} (trigger: {trigger})")

            # Count original tokens
            original_tokens = self.token_counter.count_tokens(content)

            # Get target compression ratio
            compression_ratio = self.config.compression_ratios.get(content_type, 0.35)
            target_tokens = int(original_tokens * compression_ratio)

            # Get appropriate strategy
            strategy = self._strategies.get(content_type, self._strategies[ContentType.MIXED_CONTENT])

            # Perform summarization
            summary_result = strategy.summarize(
                content=content,
                target_tokens=target_tokens,
                context=context or {},
                preserve_key_info=self.config.preserve_key_plot_points
            )

            # Count compressed tokens
            compressed_tokens = self.token_counter.count_tokens(summary_result.summary)
            actual_compression_ratio = compressed_tokens / original_tokens if original_tokens > 0 else 0

            # Create result
            result = DistillationResult(
                success=True,
                original_token_count=original_tokens,
                compressed_token_count=compressed_tokens,
                compression_ratio=actual_compression_ratio,
                content_type=content_type,
                trigger=trigger,
                layer_affected=target_layer,
                key_information_preserved=summary_result.key_information,
                quality_score=summary_result.quality_score,
                original_content=content,
                compressed_content=summary_result.summary,
                summary_metadata=summary_result.metadata
            )

            # Add to history
            self._distillation_history.append(result)

            logger.info(
                f"Distillation completed: {original_tokens} -> {compressed_tokens} tokens ({actual_compression_ratio:.2%})")
            return result

        except Exception as e:
            logger.error(f"Distillation failed: {e}")
            return DistillationResult(
                success=False,
                original_token_count=self.token_counter.count_tokens(content),
                compressed_token_count=0,
                compression_ratio=0.0,
                content_type=content_type,
                trigger=trigger,
                layer_affected=target_layer,
                error_message=str(e)
            )

    def handle_overflow(
        self,
        layer_contents: Dict[LayerType, str],
        overflow_layer: LayerType,
        target_reduction: int
    ) -> List[DistillationResult]:
        """
        Handle layer overflow by compressing content in priority order.

        Args:
            layer_contents: Current content in each layer
            overflow_layer: Layer that is overflowing
            target_reduction: Target token reduction needed

        Returns:
            List of distillation results
        """
        results = []
        remaining_reduction = target_reduction

        # Sort layers by priority (lowest first for compression)
        sorted_layers = sorted(
            layer_contents.keys(),
            key=lambda x: self.config.layer_priorities.get(x, 0)
        )

        logger.info(f"Handling overflow in {overflow_layer}, need to reduce by {target_reduction} tokens")

        for layer_type in sorted_layers:
            if remaining_reduction <= 0:
                break

            # Skip working memory (highest priority)
            if layer_type == LayerType.WORKING_MEMORY:
                continue

            content = layer_contents[layer_type]
            if not content:
                continue

            # Determine content type (simplified heuristic)
            content_type = self._classify_content(content)

            # Calculate how much to compress from this layer
            current_tokens = self.token_counter.count_tokens(content)
            max_reduction = int(current_tokens * 0.7)  # Don't compress more than 70%
            layer_reduction = min(remaining_reduction, max_reduction)

            if layer_reduction > 0:
                # Perform distillation
                result = self.distill_content(
                    content=content,
                    content_type=content_type,
                    target_layer=layer_type,
                    trigger=DistillationTrigger.LAYER_OVERFLOW
                )

                if result.success:
                    actual_reduction = result.original_token_count - result.compressed_token_count
                    remaining_reduction -= actual_reduction
                    results.append(result)

                    logger.info(f"Compressed {layer_type}: reduced by {actual_reduction} tokens")

        if remaining_reduction > 0:
            logger.warning(f"Could not achieve full reduction target. {remaining_reduction} tokens still needed.")

        return results

    def create_summary_of_summaries(
        self,
        summaries: List[str],
        content_type: ContentType,
        target_tokens: Optional[int] = None
    ) -> DistillationResult:
        """
        Create a summary of multiple summaries for extremely long stories.

        Args:
            summaries: List of existing summaries to combine
            content_type: Type of content being summarized
            target_tokens: Target token count for final summary

        Returns:
            DistillationResult with the meta-summary
        """
        if not summaries:
            return DistillationResult(
                success=False,
                original_token_count=0,
                compressed_token_count=0,
                compression_ratio=0.0,
                content_type=content_type,
                trigger=DistillationTrigger.MANUAL_REQUEST,
                layer_affected=LayerType.LONG_TERM_MEMORY,
                error_message="No summaries provided"
            )

        # Combine all summaries
        combined_content = "\n\n".join(summaries)
        original_tokens = self.token_counter.count_tokens(combined_content)

        # Set target tokens if not provided
        if target_tokens is None:
            target_tokens = int(original_tokens * 0.5)  # 50% compression for meta-summaries

        logger.info(f"Creating summary of {len(summaries)} summaries: {original_tokens} -> {target_tokens} tokens")

        # Use appropriate strategy for meta-summarization
        strategy = self._strategies.get(content_type, self._strategies[ContentType.MIXED_CONTENT])

        # Add meta-summary context
        context = {
            "is_meta_summary": True,
            "source_summary_count": len(summaries),
            "preserve_narrative_flow": True
        }

        return self.distill_content(
            content=combined_content,
            content_type=content_type,
            target_layer=LayerType.LONG_TERM_MEMORY,
            trigger=DistillationTrigger.SCHEDULED_COMPRESSION,
            context=context
        )

    def _classify_content(self, content: str) -> ContentType:
        """
        Classify content type using simple heuristics.

        Args:
            content: Content to classify

        Returns:
            Classified content type
        """
        content_lower = content.lower()

        # Simple keyword-based classification
        if any(word in content_lower for word in ["plot", "story", "narrative", "chapter"]):
            return ContentType.PLOT_SUMMARY
        elif any(word in content_lower for word in ["character", "personality", "trait", "development"]):
            return ContentType.CHARACTER_DEVELOPMENT
        elif content.count('"') > 10 or content.count("'") > 10:  # Lots of quotes = dialogue
            return ContentType.DIALOGUE
        elif any(word in content_lower for word in ["world", "setting", "location", "environment"]):
            return ContentType.WORLD_BUILDING
        elif any(word in content_lower for word in ["emotion", "feeling", "heart", "love", "fear", "anger"]):
            return ContentType.EMOTIONAL_MOMENT
        elif any(word in content_lower for word in ["event", "happened", "occurred", "sequence"]):
            return ContentType.EVENT_SEQUENCE
        else:
            return ContentType.MIXED_CONTENT

    def get_distillation_history(self) -> List[DistillationResult]:
        """Get the history of distillation operations."""
        return self._distillation_history.copy()

    def get_compression_stats(self) -> Dict[str, Any]:
        """Get statistics about compression operations."""
        if not self._distillation_history:
            return {"total_operations": 0}

        successful_ops = [r for r in self._distillation_history if r.success]

        total_original = sum(r.original_token_count for r in successful_ops)
        total_compressed = sum(r.compressed_token_count for r in successful_ops)

        return {
            "total_operations": len(self._distillation_history),
            "successful_operations": len(successful_ops),
            "total_tokens_processed": total_original,
            "total_tokens_saved": total_original - total_compressed,
            "average_compression_ratio": total_compressed / total_original if total_original > 0 else 0,
            "content_type_breakdown": self._get_content_type_stats(),
            "layer_breakdown": self._get_layer_stats()
        }

    def _get_content_type_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics broken down by content type."""
        stats = {}

        for content_type in ContentType:
            type_results = [r for r in self._distillation_history if r.content_type == content_type and r.success]

            if type_results:
                total_original = sum(r.original_token_count for r in type_results)
                total_compressed = sum(r.compressed_token_count for r in type_results)

                stats[content_type.value] = {
                    "operations": len(type_results),
                    "tokens_processed": total_original,
                    "tokens_saved": total_original - total_compressed,
                    "average_compression": total_compressed / total_original if total_original > 0 else 0,
                    "average_quality": sum(r.quality_score for r in type_results) / len(type_results)
                }

        return stats

    def _get_layer_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics broken down by layer."""
        stats = {}

        for layer_type in LayerType:
            layer_results = [r for r in self._distillation_history if r.layer_affected == layer_type and r.success]

            if layer_results:
                total_original = sum(r.original_token_count for r in layer_results)
                total_compressed = sum(r.compressed_token_count for r in layer_results)

                stats[layer_type.value] = {
                    "operations": len(layer_results),
                    "tokens_processed": total_original,
                    "tokens_saved": total_original - total_compressed,
                    "average_compression": total_compressed / total_original if total_original > 0 else 0
                }

        return stats
