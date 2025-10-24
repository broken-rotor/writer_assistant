"""
Services module for the Writer Assistant backend.

This package contains all service classes and business logic for the application.
"""

# Import token management system
from .token_management import (
    TokenCounter, ContentType, CountingStrategy, TokenCount,
    TokenAllocator, AllocationMode, OverflowStrategy, AllocationRequest, AllocationResult,
    LayerType, LayerConfig, LayerAllocation, LayerHierarchy
)

# Import context distillation system
from .context_distillation import (
    ContextDistiller, DistillationConfig, DistillationResult,
    SummarizationStrategy, PlotSummaryStrategy, CharacterDevelopmentStrategy,
    DialogueSummaryStrategy, EventSequenceStrategy, EmotionalMomentStrategy,
    WorldBuildingStrategy
)

# Import content prioritization system
from .content_prioritization import (
    LayeredPrioritizer, ContentScore, PrioritizationConfig,
    RAGRetriever, RetrievalStrategy, RetrievalResult
)
