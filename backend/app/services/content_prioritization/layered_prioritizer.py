"""
Layered Prioritizer for Content Scoring and Ranking

Implements the main prioritization engine for Layer D (Active Character/Scene Data)
that integrates with the hierarchical memory management system.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from ...utils.relevance_calculator import (
    RelevanceCalculator, ContentItem, ContentCategory, ScoringWeights, RelevanceScore
)
from ..token_management.layers import LayerType, LayerConfig, LayerAllocation
from ..token_management.token_counter import TokenCounter, ContentType, CountingStrategy
from ...core.config import settings

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Types of agents that can request content prioritization."""
    WRITER = "writer"
    CHARACTER = "character"
    RATER = "rater"
    EDITOR = "editor"


@dataclass
class PrioritizationConfig:
    """Configuration for content prioritization."""
    max_items_per_category: int = 10
    min_score_threshold: float = 0.1
    token_budget: int = 2000  # Default Layer D budget
    enable_dynamic_weighting: bool = True
    agent_specific_weights: Dict[AgentType, ScoringWeights] = field(default_factory=dict)
    category_token_limits: Dict[ContentCategory, int] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize default configurations."""
        if not self.agent_specific_weights:
            self._setup_default_agent_weights()
        if not self.category_token_limits:
            self._setup_default_category_limits()

    def _setup_default_agent_weights(self):
        """Setup default scoring weights for different agent types."""
        self.agent_specific_weights = {
            AgentType.WRITER: ScoringWeights(
                recency_weight=0.25,
                relevance_weight=0.45,
                importance_weight=0.25,
                access_frequency_weight=0.05
            ),
            AgentType.CHARACTER: ScoringWeights(
                recency_weight=0.35,
                relevance_weight=0.35,
                importance_weight=0.20,
                access_frequency_weight=0.10
            ),
            AgentType.RATER: ScoringWeights(
                recency_weight=0.20,
                relevance_weight=0.30,
                importance_weight=0.40,
                access_frequency_weight=0.10
            ),
            AgentType.EDITOR: ScoringWeights(
                recency_weight=0.30,
                relevance_weight=0.40,
                importance_weight=0.25,
                access_frequency_weight=0.05
            )
        }

    def _setup_default_category_limits(self):
        """Setup default token limits per content category."""
        self.category_token_limits = {
            ContentCategory.CHARACTER: 800,      # 40% of default budget
            ContentCategory.SCENE: 600,          # 30% of default budget
            ContentCategory.PLOT_POINT: 400,     # 20% of default budget
            ContentCategory.WORLD_BUILDING: 200  # 10% of default budget
        }


@dataclass
class ContentScore:
    """Scored content item with prioritization metadata."""
    content_item: ContentItem
    relevance_score: RelevanceScore
    token_count: int
    priority_rank: int
    selected_for_layer: bool = False
    truncated: bool = False
    agent_context: Optional[AgentType] = None


@dataclass
class PrioritizationResult:
    """Result of content prioritization process."""
    selected_content: List[ContentScore]
    total_tokens_used: int
    total_tokens_available: int
    items_considered: int
    items_selected: int
    agent_type: AgentType
    context_summary: str
    performance_metrics: Dict[str, Any] = field(default_factory=dict)


class LayeredPrioritizer:
    """
    Main prioritization engine for Layer D content scoring and ranking.

    Integrates with the token management system to optimally allocate
    character and scene data within Layer D token budget constraints.
    """

    def __init__(
        self,
        config: Optional[PrioritizationConfig] = None,
        token_counter: Optional[TokenCounter] = None,
        relevance_calculator: Optional[RelevanceCalculator] = None
    ):
        """Initialize the layered prioritizer."""
        self.config = config or PrioritizationConfig()
        self.token_counter = token_counter or TokenCounter(model_path=settings.MODEL_PATH)
        self.relevance_calculator = relevance_calculator or RelevanceCalculator()
        self.logger = logging.getLogger(__name__)

        # Performance tracking
        self._performance_metrics = {
            'total_prioritizations': 0,
            'average_processing_time': 0.0,
            'cache_hit_rate': 0.0
        }

    def prioritize_content(
        self,
        content_items: List[ContentItem],
        context: Dict[str, Any],
        agent_type: AgentType,
        token_budget: Optional[int] = None
    ) -> PrioritizationResult:
        """
        Prioritize content items for Layer D allocation.

        Args:
            content_items: List of content items to prioritize
            context: Current context for relevance calculation
            agent_type: Type of agent requesting prioritization
            token_budget: Override default token budget

        Returns:
            PrioritizationResult with selected and ranked content
        """
        start_time = datetime.now()

        # Use agent-specific or default token budget
        budget = token_budget or self.config.token_budget

        # Get agent-specific scoring weights
        weights = self.config.agent_specific_weights.get(
            agent_type, ScoringWeights()
        )

        # Update relevance calculator with agent-specific weights
        self.relevance_calculator.weights = weights

        # Calculate relevance scores for all items
        relevance_scores = self.relevance_calculator.batch_calculate_scores(
            content_items, context
        )

        # Convert to ContentScore objects with token counts
        scored_content = []
        for i, score in enumerate(relevance_scores):
            content_item = content_items[i]

            # Count tokens for this content
            token_count = self.token_counter.count_tokens(
                content_item.content,
                content_type=self._map_category_to_content_type(content_item.category),
                strategy=CountingStrategy.ESTIMATED
            ).token_count

            content_score = ContentScore(
                content_item=content_item,
                relevance_score=score,
                token_count=token_count,
                priority_rank=i + 1,
                agent_context=agent_type
            )
            scored_content.append(content_score)

        # Apply filtering and selection
        selected_content = self._select_content_within_budget(
            scored_content, budget, agent_type
        )

        # Calculate performance metrics
        processing_time = (datetime.now() - start_time).total_seconds()
        self._update_performance_metrics(processing_time)

        # Create result
        result = PrioritizationResult(
            selected_content=selected_content,
            total_tokens_used=sum(item.token_count for item in selected_content),
            total_tokens_available=budget,
            items_considered=len(content_items),
            items_selected=len(selected_content),
            agent_type=agent_type,
            context_summary=self._generate_context_summary(context),
            performance_metrics={
                'processing_time_ms': processing_time * 1000,
                'items_per_second': len(content_items) / max(processing_time, 0.001),
                'token_utilization': sum(item.token_count for item in selected_content) / budget
            }
        )

        self.logger.info(
            f"Prioritized {len(content_items)} items for {agent_type.value}, "
            f"selected {len(selected_content)} items using {result.total_tokens_used}/{budget} tokens"
        )

        return result

    def _select_content_within_budget(
        self,
        scored_content: List[ContentScore],
        budget: int,
        agent_type: AgentType
    ) -> List[ContentScore]:
        """
        Select content items that fit within the token budget.

        Uses a greedy algorithm with category balancing to ensure
        diverse content selection within budget constraints.
        """
        # Filter by minimum score threshold
        filtered_content = [
            item for item in scored_content
            if item.relevance_score.total_score >= self.config.min_score_threshold
        ]

        # Group by category for balanced selection
        category_groups = {}
        for item in filtered_content:
            category = item.content_item.category
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(item)

        # Sort each category group by score
        for category in category_groups:
            category_groups[category].sort(
                key=lambda x: x.relevance_score.total_score, reverse=True
            )

        # Select items using category-aware greedy algorithm
        selected_items = []
        remaining_budget = budget
        category_budgets = self._calculate_category_budgets(budget, category_groups.keys())

        # First pass: select top items from each category within category budgets
        for category, items in category_groups.items():
            category_budget = category_budgets.get(category, 0)
            category_tokens_used = 0

            for item in items:
                if (category_tokens_used + item.token_count <= category_budget and
                    len([i for i in selected_items if i.content_item.category == category]) <
                        self.config.max_items_per_category):

                    item.selected_for_layer = True
                    selected_items.append(item)
                    category_tokens_used += item.token_count
                    remaining_budget -= item.token_count

        # Second pass: fill remaining budget with highest scoring items
        remaining_items = [
            item for item in filtered_content
            if not item.selected_for_layer
        ]
        remaining_items.sort(
            key=lambda x: x.relevance_score.total_score, reverse=True
        )

        for item in remaining_items:
            if remaining_budget >= item.token_count:
                item.selected_for_layer = True
                selected_items.append(item)
                remaining_budget -= item.token_count

        # Sort final selection by score for consistent ordering
        selected_items.sort(
            key=lambda x: x.relevance_score.total_score, reverse=True
        )

        # Update priority ranks
        for i, item in enumerate(selected_items):
            item.priority_rank = i + 1

        return selected_items

    def _calculate_category_budgets(
        self,
        total_budget: int,
        categories: Set[ContentCategory]
    ) -> Dict[ContentCategory, int]:
        """Calculate token budget allocation per content category."""
        category_budgets = {}

        # Use configured category limits as proportions
        total_configured = sum(
            self.config.category_token_limits.get(cat, 100)
            for cat in categories
        )

        for category in categories:
            configured_limit = self.config.category_token_limits.get(category, 100)
            proportion = configured_limit / total_configured
            category_budgets[category] = int(total_budget * proportion)

        return category_budgets

    def _map_category_to_content_type(self, category: ContentCategory) -> ContentType:
        """Map content category to token counter content type."""
        mapping = {
            ContentCategory.CHARACTER: ContentType.CHARACTER_DESCRIPTION,
            ContentCategory.SCENE: ContentType.SCENE_DESCRIPTION,
            ContentCategory.PLOT_POINT: ContentType.NARRATIVE,
            ContentCategory.WORLD_BUILDING: ContentType.SCENE_DESCRIPTION,
            ContentCategory.DIALOGUE: ContentType.DIALOGUE,
            ContentCategory.NARRATIVE: ContentType.NARRATIVE,
            ContentCategory.METADATA: ContentType.METADATA
        }
        return mapping.get(category, ContentType.UNKNOWN)

    def _generate_context_summary(self, context: Dict[str, Any]) -> str:
        """Generate a human-readable summary of the current context."""
        summary_parts = []

        if 'active_characters' in context:
            chars = context['active_characters']
            if chars:
                summary_parts.append(f"Characters: {', '.join(chars[:3])}")

        if 'active_locations' in context:
            locs = context['active_locations']
            if locs:
                summary_parts.append(f"Locations: {', '.join(locs[:2])}")

        if 'current_scene_type' in context:
            scene_type = context['current_scene_type']
            if scene_type:
                summary_parts.append(f"Scene: {scene_type}")

        if 'keywords' in context:
            keywords = context['keywords']
            if keywords:
                summary_parts.append(f"Keywords: {', '.join(keywords[:3])}")

        return "; ".join(summary_parts) if summary_parts else "No specific context"

    def _update_performance_metrics(self, processing_time: float):
        """Update internal performance tracking metrics."""
        self._performance_metrics['total_prioritizations'] += 1

        # Update rolling average processing time
        total_ops = self._performance_metrics['total_prioritizations']
        current_avg = self._performance_metrics['average_processing_time']
        new_avg = ((current_avg * (total_ops - 1)) + processing_time) / total_ops
        self._performance_metrics['average_processing_time'] = new_avg

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        return self._performance_metrics.copy()

    def update_config(self, new_config: PrioritizationConfig):
        """Update prioritization configuration."""
        self.config = new_config
        self.logger.info("Updated prioritization configuration")

    def clear_performance_metrics(self):
        """Reset performance tracking metrics."""
        self._performance_metrics = {
            'total_prioritizations': 0,
            'average_processing_time': 0.0,
            'cache_hit_rate': 0.0
        }
        self.logger.info("Cleared performance metrics")
