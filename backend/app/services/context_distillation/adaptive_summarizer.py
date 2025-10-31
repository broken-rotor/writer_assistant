"""
Adaptive Summarization Engine for Writer Assistant.

This module provides intelligent strategy selection for context summarization
based on generation type, endpoint, phase, and agent type. It combines multiple
summarization strategies for complex scenarios and provides configurable
strategy selection logic.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

from .summarization_strategies import (
    SummarizationStrategy, SummaryResult,
    PlotSummaryStrategy, CharacterDevelopmentStrategy, DialogueSummaryStrategy,
    EventSequenceStrategy, EmotionalMomentStrategy, WorldBuildingStrategy,
    FeedbackSummaryStrategy, SystemPromptOptimizationStrategy,
    ConversationHistorySummaryStrategy
)
from ..llm_inference import LLMInference
from ...models.context_models import ContextType, AgentType, ComposePhase

logger = logging.getLogger(__name__)


class GenerationType(Enum):
    """Types of generation that require different summarization approaches."""
    CREATIVE_WRITING = "creative_writing"
    CHAPTER_GENERATION = "chapter_generation"
    CHARACTER_FEEDBACK = "character_feedback"
    RATER_FEEDBACK = "rater_feedback"
    EDITOR_REVIEW = "editor_review"
    FLESH_OUT = "flesh_out"
    MODIFY_CHAPTER = "modify_chapter"
    WORLDBUILDING_CHAT = "worldbuilding_chat"
    GENERAL_CHAT = "general_chat"


@dataclass
class StrategyWeight:
    """Weight configuration for strategy selection."""
    strategy_class: type
    weight: float
    min_content_threshold: int = 100  # Minimum content length to apply this strategy


@dataclass
class AdaptiveSummarizationConfig:
    """Configuration for adaptive summarization behavior."""
    
    # Strategy weights by generation type
    generation_type_strategies: Dict[GenerationType, List[StrategyWeight]] = field(default_factory=lambda: {
        GenerationType.CREATIVE_WRITING: [
            StrategyWeight(PlotSummaryStrategy, 0.4),
            StrategyWeight(CharacterDevelopmentStrategy, 0.3),
            StrategyWeight(WorldBuildingStrategy, 0.2),
            StrategyWeight(EmotionalMomentStrategy, 0.1)
        ],
        GenerationType.CHAPTER_GENERATION: [
            StrategyWeight(PlotSummaryStrategy, 0.35),
            StrategyWeight(CharacterDevelopmentStrategy, 0.25),
            StrategyWeight(WorldBuildingStrategy, 0.15),
            StrategyWeight(EventSequenceStrategy, 0.15),
            StrategyWeight(FeedbackSummaryStrategy, 0.1)
        ],
        GenerationType.CHARACTER_FEEDBACK: [
            StrategyWeight(CharacterDevelopmentStrategy, 0.5),
            StrategyWeight(PlotSummaryStrategy, 0.2),
            StrategyWeight(FeedbackSummaryStrategy, 0.2),
            StrategyWeight(EmotionalMomentStrategy, 0.1)
        ],
        GenerationType.RATER_FEEDBACK: [
            StrategyWeight(PlotSummaryStrategy, 0.3),
            StrategyWeight(CharacterDevelopmentStrategy, 0.25),
            StrategyWeight(FeedbackSummaryStrategy, 0.25),
            StrategyWeight(WorldBuildingStrategy, 0.2)
        ],
        GenerationType.EDITOR_REVIEW: [
            StrategyWeight(PlotSummaryStrategy, 0.3),
            StrategyWeight(CharacterDevelopmentStrategy, 0.2),
            StrategyWeight(DialogueSummaryStrategy, 0.2),
            StrategyWeight(EventSequenceStrategy, 0.15),
            StrategyWeight(FeedbackSummaryStrategy, 0.15)
        ],
        GenerationType.WORLDBUILDING_CHAT: [
            StrategyWeight(WorldBuildingStrategy, 0.6),
            StrategyWeight(ConversationHistorySummaryStrategy, 0.3),
            StrategyWeight(PlotSummaryStrategy, 0.1)
        ],
        GenerationType.GENERAL_CHAT: [
            StrategyWeight(ConversationHistorySummaryStrategy, 0.7),
            StrategyWeight(FeedbackSummaryStrategy, 0.3)
        ]
    })
    
    # Context type to strategy mapping
    context_type_strategies: Dict[ContextType, type] = field(default_factory=lambda: {
        ContextType.PLOT_OUTLINE: PlotSummaryStrategy,
        ContextType.CHARACTER_PROFILE: CharacterDevelopmentStrategy,
        ContextType.CHARACTER_RELATIONSHIP: CharacterDevelopmentStrategy,
        ContextType.CHARACTER_MEMORY: CharacterDevelopmentStrategy,
        ContextType.WORLD_BUILDING: WorldBuildingStrategy,
        ContextType.USER_FEEDBACK: FeedbackSummaryStrategy,
        ContextType.SYSTEM_PROMPT: SystemPromptOptimizationStrategy,
        ContextType.SYSTEM_INSTRUCTION: SystemPromptOptimizationStrategy,
        ContextType.CONVERSATION_HISTORY: ConversationHistorySummaryStrategy,
        ContextType.CONVERSATION_CONTEXT: ConversationHistorySummaryStrategy
    })
    
    # Agent type preferences
    agent_type_preferences: Dict[AgentType, List[type]] = field(default_factory=lambda: {
        AgentType.WRITER: [PlotSummaryStrategy, CharacterDevelopmentStrategy, WorldBuildingStrategy],
        AgentType.CHARACTER: [CharacterDevelopmentStrategy, EmotionalMomentStrategy, DialogueSummaryStrategy],
        AgentType.RATER: [PlotSummaryStrategy, CharacterDevelopmentStrategy, FeedbackSummaryStrategy],
        AgentType.EDITOR: [PlotSummaryStrategy, DialogueSummaryStrategy, EventSequenceStrategy],
        AgentType.WORLDBUILDING: [WorldBuildingStrategy, ConversationHistorySummaryStrategy]
    })
    
    # Phase-specific adjustments
    phase_adjustments: Dict[ComposePhase, Dict[type, float]] = field(default_factory=lambda: {
        ComposePhase.PLOT_OUTLINE: {
            PlotSummaryStrategy: 1.5,  # Boost plot strategy in outline phase
            CharacterDevelopmentStrategy: 1.2,
            WorldBuildingStrategy: 1.1
        },
        ComposePhase.CHAPTER_DETAIL: {
            CharacterDevelopmentStrategy: 1.4,  # Boost character strategy in detail phase
            DialogueSummaryStrategy: 1.3,
            EmotionalMomentStrategy: 1.2
        },
        ComposePhase.FINAL_EDIT: {
            EventSequenceStrategy: 1.3,  # Boost sequence strategy in edit phase
            DialogueSummaryStrategy: 1.2,
            FeedbackSummaryStrategy: 1.4
        }
    })
    
    # Quality thresholds
    min_quality_score: float = 0.6
    max_strategy_combinations: int = 3
    combination_threshold: int = 2000  # Token count above which to consider combinations


@dataclass
class AdaptiveSummaryResult:
    """Result of adaptive summarization with strategy metadata."""
    summary: str
    key_information: List[str]
    quality_score: float
    strategies_used: List[str]
    total_tokens: int
    compression_ratio: float
    metadata: Dict[str, Any]
    warnings: List[str] = field(default_factory=list)


class AdaptiveSummarizationEngine:
    """
    Intelligent summarization engine that selects and combines strategies
    based on generation context and content analysis.
    """
    
    def __init__(self, llm_service: LLMInference, config: Optional[AdaptiveSummarizationConfig] = None):
        """Initialize the adaptive summarization engine."""
        self.llm_service = llm_service
        self.config = config or AdaptiveSummarizationConfig()
        
        # Initialize strategy instances
        self.strategies = {
            PlotSummaryStrategy: PlotSummaryStrategy(llm_service),
            CharacterDevelopmentStrategy: CharacterDevelopmentStrategy(llm_service),
            DialogueSummaryStrategy: DialogueSummaryStrategy(llm_service),
            EventSequenceStrategy: EventSequenceStrategy(llm_service),
            EmotionalMomentStrategy: EmotionalMomentStrategy(llm_service),
            WorldBuildingStrategy: WorldBuildingStrategy(llm_service),
            FeedbackSummaryStrategy: FeedbackSummaryStrategy(llm_service),
            SystemPromptOptimizationStrategy: SystemPromptOptimizationStrategy(llm_service),
            ConversationHistorySummaryStrategy: ConversationHistorySummaryStrategy(llm_service)
        }
        
        logger.info("AdaptiveSummarizationEngine initialized with {} strategies".format(len(self.strategies)))
    
    def summarize_adaptively(
        self,
        content: str,
        target_tokens: int,
        generation_type: GenerationType,
        context_type: Optional[ContextType] = None,
        agent_type: Optional[AgentType] = None,
        compose_phase: Optional[ComposePhase] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> AdaptiveSummaryResult:
        """
        Perform adaptive summarization based on generation context.
        
        Args:
            content: Content to summarize
            target_tokens: Target token count for summary
            generation_type: Type of generation (creative writing, feedback, etc.)
            context_type: Specific context type if known
            agent_type: Target agent type
            compose_phase: Current compose phase
            additional_context: Additional context for summarization
            
        Returns:
            AdaptiveSummaryResult with summary and metadata
        """
        try:
            # Analyze content to determine best strategies
            selected_strategies = self._select_strategies(
                content, generation_type, context_type, agent_type, compose_phase
            )
            
            if not selected_strategies:
                logger.warning("No strategies selected for summarization")
                return AdaptiveSummaryResult(
                    summary=content[:target_tokens * 4],  # Rough token approximation
                    key_information=[],
                    quality_score=0.5,
                    strategies_used=[],
                    total_tokens=len(content.split()),
                    compression_ratio=1.0,
                    metadata={"fallback": True},
                    warnings=["No strategies selected, using fallback"]
                )
            
            # Determine if we need strategy combination
            if len(selected_strategies) > 1 and len(content.split()) > self.config.combination_threshold:
                return self._combine_strategies(
                    content, target_tokens, selected_strategies, additional_context or {}
                )
            else:
                # Use single best strategy
                best_strategy = selected_strategies[0]
                return self._apply_single_strategy(
                    content, target_tokens, best_strategy, additional_context or {}
                )
                
        except Exception as e:
            logger.error(f"Adaptive summarization failed: {e}")
            return AdaptiveSummaryResult(
                summary="",
                key_information=[],
                quality_score=0.0,
                strategies_used=[],
                total_tokens=0,
                compression_ratio=0.0,
                metadata={},
                warnings=[f"Summarization failed: {str(e)}"]
            )
    
    def _select_strategies(
        self,
        content: str,
        generation_type: GenerationType,
        context_type: Optional[ContextType],
        agent_type: Optional[AgentType],
        compose_phase: Optional[ComposePhase]
    ) -> List[Tuple[type, float]]:
        """Select and rank strategies based on context."""
        strategy_scores = {}
        
        # Base scores from generation type
        if generation_type in self.config.generation_type_strategies:
            for strategy_weight in self.config.generation_type_strategies[generation_type]:
                if len(content) >= strategy_weight.min_content_threshold:
                    strategy_scores[strategy_weight.strategy_class] = strategy_weight.weight
        
        # Boost score for context type match
        if context_type and context_type in self.config.context_type_strategies:
            preferred_strategy = self.config.context_type_strategies[context_type]
            strategy_scores[preferred_strategy] = strategy_scores.get(preferred_strategy, 0) + 0.3
        
        # Boost scores for agent type preferences
        if agent_type and agent_type in self.config.agent_type_preferences:
            for preferred_strategy in self.config.agent_type_preferences[agent_type]:
                strategy_scores[preferred_strategy] = strategy_scores.get(preferred_strategy, 0) + 0.1
        
        # Apply phase adjustments
        if compose_phase and compose_phase in self.config.phase_adjustments:
            for strategy_class, multiplier in self.config.phase_adjustments[compose_phase].items():
                if strategy_class in strategy_scores:
                    strategy_scores[strategy_class] *= multiplier
        
        # Sort by score and return top strategies
        sorted_strategies = sorted(strategy_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_strategies[:self.config.max_strategy_combinations]
    
    def _apply_single_strategy(
        self,
        content: str,
        target_tokens: int,
        strategy_info: Tuple[type, float],
        context: Dict[str, Any]
    ) -> AdaptiveSummaryResult:
        """Apply a single summarization strategy."""
        strategy_class, score = strategy_info
        strategy = self.strategies[strategy_class]
        
        result = strategy.summarize(content, target_tokens, context, preserve_key_info=True)
        
        return AdaptiveSummaryResult(
            summary=result.summary,
            key_information=result.key_information,
            quality_score=result.quality_score,
            strategies_used=[result.metadata.get("strategy", strategy_class.__name__)],
            total_tokens=result.metadata.get("actual_tokens", len(result.summary.split())),
            compression_ratio=len(result.summary) / len(content) if content else 1.0,
            metadata=result.metadata,
            warnings=result.warnings
        )
    
    def _combine_strategies(
        self,
        content: str,
        target_tokens: int,
        strategies: List[Tuple[type, float]],
        context: Dict[str, Any]
    ) -> AdaptiveSummaryResult:
        """Combine multiple strategies for complex content."""
        # Allocate tokens proportionally to strategy weights
        total_weight = sum(weight for _, weight in strategies)
        strategy_results = []
        combined_key_info = []
        combined_warnings = []
        
        for strategy_class, weight in strategies:
            strategy_tokens = int((weight / total_weight) * target_tokens)
            strategy = self.strategies[strategy_class]
            
            result = strategy.summarize(content, strategy_tokens, context, preserve_key_info=True)
            strategy_results.append(result)
            combined_key_info.extend(result.key_information)
            combined_warnings.extend(result.warnings)
        
        # Combine summaries intelligently
        combined_summary = self._merge_summaries(strategy_results, target_tokens)
        
        # Calculate combined metrics
        avg_quality = sum(r.quality_score for r in strategy_results) / len(strategy_results)
        strategies_used = [r.metadata.get("strategy", "unknown") for r in strategy_results]
        
        return AdaptiveSummaryResult(
            summary=combined_summary,
            key_information=list(set(combined_key_info)),  # Remove duplicates
            quality_score=avg_quality,
            strategies_used=strategies_used,
            total_tokens=len(combined_summary.split()),
            compression_ratio=len(combined_summary) / len(content) if content else 1.0,
            metadata={
                "combination_used": True,
                "strategy_count": len(strategies),
                "individual_results": [r.metadata for r in strategy_results]
            },
            warnings=list(set(combined_warnings))  # Remove duplicate warnings
        )
    
    def _merge_summaries(self, results: List[SummaryResult], target_tokens: int) -> str:
        """Merge multiple summary results into a coherent summary."""
        # Simple merging strategy - could be enhanced with LLM-based merging
        summaries = [r.summary for r in results if r.summary]
        
        if not summaries:
            return ""
        
        if len(summaries) == 1:
            return summaries[0]
        
        # Combine summaries with clear separation
        combined = "\n\n".join(summaries)
        
        # If combined summary is too long, truncate intelligently
        if len(combined.split()) > target_tokens:
            # Truncate each summary proportionally
            words_per_summary = target_tokens // len(summaries)
            truncated_summaries = []
            
            for summary in summaries:
                words = summary.split()
                if len(words) > words_per_summary:
                    truncated = " ".join(words[:words_per_summary])
                    truncated_summaries.append(truncated)
                else:
                    truncated_summaries.append(summary)
            
            combined = "\n\n".join(truncated_summaries)
        
        return combined
    
    def get_strategy_for_context_type(self, context_type: ContextType) -> Optional[type]:
        """Get the preferred strategy for a specific context type."""
        return self.config.context_type_strategies.get(context_type)
    
    def update_config(self, new_config: AdaptiveSummarizationConfig):
        """Update the configuration for the adaptive engine."""
        self.config = new_config
        logger.info("AdaptiveSummarizationEngine configuration updated")
