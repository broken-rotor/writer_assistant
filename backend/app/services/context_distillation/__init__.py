"""
Context Distillation and Summarization Engine

This module provides intelligent content compression and rolling summarization
for the Writer Assistant's hierarchical memory management system.

Key Features:
- Rolling summarization at 25k token threshold
- Hierarchical summarization preserving key plot points and character development
- Summary-of-summary operations for extremely long stories
- Different summarization strategies per content type
- Overflow handling with graceful degradation
- Integration with LLM service for summarization
"""

from .context_distiller import (
    ContextDistiller, DistillationConfig, DistillationResult,
    ContentType, DistillationTrigger
)
from .summarization_strategies import (
    SummarizationStrategy,
    PlotSummaryStrategy,
    CharacterDevelopmentStrategy,
    DialogueSummaryStrategy,
    EventSequenceStrategy,
    EmotionalMomentStrategy,
    WorldBuildingStrategy,
    FeedbackSummaryStrategy,
    SystemPromptOptimizationStrategy,
    ConversationHistorySummaryStrategy
)
__all__ = [
    "ContextDistiller",
    "DistillationConfig",
    "DistillationResult",
    "ContentType",
    "DistillationTrigger",
    "SummarizationStrategy",
    "PlotSummaryStrategy",
    "CharacterDevelopmentStrategy",
    "DialogueSummaryStrategy",
    "EventSequenceStrategy",
    "EmotionalMomentStrategy",
    "WorldBuildingStrategy",
    "FeedbackSummaryStrategy",
    "SystemPromptOptimizationStrategy",
    "ConversationHistorySummaryStrategy"
]
