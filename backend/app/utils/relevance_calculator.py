"""
Relevance Calculator for Content Prioritization

Provides algorithms for scoring content based on recency, relevance, and importance
for the Writer Assistant's hierarchical memory management system.
"""

import logging
import math
import re
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ContentCategory(Enum):
    """Categories of content for different scoring strategies."""
    CHARACTER = "character"
    SCENE = "scene"
    PLOT_POINT = "plot_point"
    WORLD_BUILDING = "world_building"
    DIALOGUE = "dialogue"
    NARRATIVE = "narrative"
    METADATA = "metadata"


@dataclass
class ContentItem:
    """Represents a piece of content to be scored."""
    id: str
    content: str
    category: ContentCategory
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    importance_tags: Set[str] = None
    character_names: Set[str] = None
    location_names: Set[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.importance_tags is None:
            self.importance_tags = set()
        if self.character_names is None:
            self.character_names = set()
        if self.location_names is None:
            self.location_names = set()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ScoringWeights:
    """Configurable weights for different scoring components."""
    recency_weight: float = 0.3
    relevance_weight: float = 0.4
    importance_weight: float = 0.3
    access_frequency_weight: float = 0.1
    
    def __post_init__(self):
        """Normalize weights to sum to 1.0."""
        total = (self.recency_weight + self.relevance_weight + 
                self.importance_weight + self.access_frequency_weight)
        if total > 0:
            self.recency_weight /= total
            self.relevance_weight /= total
            self.importance_weight /= total
            self.access_frequency_weight /= total


@dataclass
class RelevanceScore:
    """Result of relevance calculation."""
    content_id: str
    total_score: float
    recency_score: float
    relevance_score: float
    importance_score: float
    access_frequency_score: float
    explanation: str = ""


class RelevanceCalculator:
    """
    Calculates relevance scores for content items based on multiple factors.
    
    Scoring components:
    1. Recency: How recently the content was created or accessed
    2. Relevance: Semantic similarity to current context
    3. Importance: Intrinsic importance based on content type and tags
    4. Access Frequency: How often the content has been accessed
    """
    
    def __init__(self, weights: Optional[ScoringWeights] = None):
        """Initialize the relevance calculator with scoring weights."""
        self.weights = weights or ScoringWeights()
        self.logger = logging.getLogger(__name__)
    
    def calculate_score(
        self,
        content_item: ContentItem,
        context: Dict[str, Any],
        current_time: Optional[datetime] = None
    ) -> RelevanceScore:
        """
        Calculate comprehensive relevance score for a content item.
        
        Args:
            content_item: The content to score
            context: Current context including active characters, scenes, etc.
            current_time: Current timestamp (defaults to now)
            
        Returns:
            RelevanceScore with component scores and explanation
        """
        if current_time is None:
            current_time = datetime.now()
        
        # Calculate component scores
        recency_score = self._calculate_recency_score(content_item, current_time)
        relevance_score = self._calculate_relevance_score(content_item, context)
        importance_score = self._calculate_importance_score(content_item, context)
        access_frequency_score = self._calculate_access_frequency_score(content_item)
        
        # Calculate weighted total score
        total_score = (
            recency_score * self.weights.recency_weight +
            relevance_score * self.weights.relevance_weight +
            importance_score * self.weights.importance_weight +
            access_frequency_score * self.weights.access_frequency_weight
        )
        
        # Generate explanation
        explanation = self._generate_explanation(
            content_item, recency_score, relevance_score, 
            importance_score, access_frequency_score
        )
        
        return RelevanceScore(
            content_id=content_item.id,
            total_score=total_score,
            recency_score=recency_score,
            relevance_score=relevance_score,
            importance_score=importance_score,
            access_frequency_score=access_frequency_score,
            explanation=explanation
        )
    
    def _calculate_recency_score(
        self, 
        content_item: ContentItem, 
        current_time: datetime
    ) -> float:
        """
        Calculate recency score using exponential decay.
        
        More recent content gets higher scores with exponential decay.
        """
        # Use the more recent of created_at or last_accessed
        most_recent = max(content_item.created_at, content_item.last_accessed)
        time_diff = current_time - most_recent
        
        # Exponential decay with half-life of 7 days
        half_life_days = 7.0
        decay_constant = math.log(2) / half_life_days
        days_old = time_diff.total_seconds() / (24 * 3600)
        
        # Score ranges from 0 to 1, with 1 being most recent
        score = math.exp(-decay_constant * days_old)
        return min(1.0, max(0.0, score))
    
    def _calculate_relevance_score(
        self, 
        content_item: ContentItem, 
        context: Dict[str, Any]
    ) -> float:
        """
        Calculate relevance score based on context matching.
        
        Uses keyword matching and entity overlap as a proxy for semantic similarity.
        """
        score = 0.0
        
        # Get context elements
        active_characters = set(context.get('active_characters', []))
        active_locations = set(context.get('active_locations', []))
        current_scene_type = context.get('current_scene_type', '')
        active_keywords = set(context.get('keywords', []))
        
        # Character relevance (high weight)
        character_overlap = len(content_item.character_names & active_characters)
        if active_characters:
            character_score = character_overlap / len(active_characters)
            score += character_score * 0.4
        
        # Location relevance (medium weight)
        location_overlap = len(content_item.location_names & active_locations)
        if active_locations:
            location_score = location_overlap / len(active_locations)
            score += location_score * 0.3
        
        # Keyword relevance (medium weight)
        if active_keywords:
            content_words = set(re.findall(r'\b\w+\b', content_item.content.lower()))
            keyword_overlap = len(content_words & active_keywords)
            keyword_score = keyword_overlap / len(active_keywords)
            score += keyword_score * 0.2
        
        # Category relevance (low weight)
        if current_scene_type:
            category_match = self._category_matches_scene_type(
                content_item.category, current_scene_type
            )
            score += category_match * 0.1
        
        return min(1.0, max(0.0, score))
    
    def _calculate_importance_score(
        self, 
        content_item: ContentItem, 
        context: Dict[str, Any]
    ) -> float:
        """
        Calculate importance score based on content type and tags.
        """
        base_importance = self._get_base_importance(content_item.category)
        
        # Boost for importance tags
        importance_boost = 0.0
        high_importance_tags = {'main_character', 'plot_critical', 'climax', 'resolution'}
        medium_importance_tags = {'character_development', 'world_building', 'conflict'}
        
        for tag in content_item.importance_tags:
            if tag in high_importance_tags:
                importance_boost += 0.3
            elif tag in medium_importance_tags:
                importance_boost += 0.2
            else:
                importance_boost += 0.1
        
        # Context-specific importance
        context_boost = 0.0
        current_agent = context.get('current_agent', '')
        if current_agent == 'character' and content_item.category == ContentCategory.CHARACTER:
            context_boost += 0.2
        elif current_agent == 'writer' and content_item.category in [
            ContentCategory.PLOT_POINT, ContentCategory.NARRATIVE
        ]:
            context_boost += 0.2
        
        total_score = base_importance + importance_boost + context_boost
        return min(1.0, max(0.0, total_score))
    
    def _calculate_access_frequency_score(self, content_item: ContentItem) -> float:
        """
        Calculate score based on how frequently content has been accessed.
        """
        if content_item.access_count == 0:
            return 0.0
        
        # Logarithmic scaling to prevent over-weighting frequently accessed items
        score = math.log(content_item.access_count + 1) / math.log(10)  # log base 10
        return min(1.0, max(0.0, score))
    
    def _get_base_importance(self, category: ContentCategory) -> float:
        """Get base importance score for content category."""
        importance_map = {
            ContentCategory.CHARACTER: 0.8,
            ContentCategory.PLOT_POINT: 0.9,
            ContentCategory.SCENE: 0.7,
            ContentCategory.WORLD_BUILDING: 0.6,
            ContentCategory.DIALOGUE: 0.5,
            ContentCategory.NARRATIVE: 0.6,
            ContentCategory.METADATA: 0.3
        }
        return importance_map.get(category, 0.5)
    
    def _category_matches_scene_type(
        self, 
        category: ContentCategory, 
        scene_type: str
    ) -> float:
        """Check if content category matches current scene type."""
        scene_type_lower = scene_type.lower()
        
        if category == ContentCategory.CHARACTER and 'character' in scene_type_lower:
            return 1.0
        elif category == ContentCategory.DIALOGUE and 'dialogue' in scene_type_lower:
            return 1.0
        elif category == ContentCategory.SCENE and 'scene' in scene_type_lower:
            return 1.0
        elif category == ContentCategory.WORLD_BUILDING and 'world' in scene_type_lower:
            return 1.0
        
        return 0.0
    
    def _generate_explanation(
        self,
        content_item: ContentItem,
        recency_score: float,
        relevance_score: float,
        importance_score: float,
        access_frequency_score: float
    ) -> str:
        """Generate human-readable explanation of the scoring."""
        explanations = []
        
        if recency_score > 0.8:
            explanations.append("very recent")
        elif recency_score > 0.5:
            explanations.append("moderately recent")
        elif recency_score > 0.2:
            explanations.append("somewhat old")
        else:
            explanations.append("old")
        
        if relevance_score > 0.7:
            explanations.append("highly relevant to current context")
        elif relevance_score > 0.4:
            explanations.append("moderately relevant")
        elif relevance_score > 0.1:
            explanations.append("somewhat relevant")
        else:
            explanations.append("low relevance")
        
        if importance_score > 0.8:
            explanations.append("high importance")
        elif importance_score > 0.5:
            explanations.append("moderate importance")
        else:
            explanations.append("low importance")
        
        if access_frequency_score > 0.5:
            explanations.append("frequently accessed")
        elif access_frequency_score > 0.2:
            explanations.append("occasionally accessed")
        else:
            explanations.append("rarely accessed")
        
        return f"{content_item.category.value}: {', '.join(explanations)}"
    
    def batch_calculate_scores(
        self,
        content_items: List[ContentItem],
        context: Dict[str, Any],
        current_time: Optional[datetime] = None
    ) -> List[RelevanceScore]:
        """
        Calculate relevance scores for multiple content items efficiently.
        
        Args:
            content_items: List of content items to score
            context: Current context for relevance calculation
            current_time: Current timestamp (defaults to now)
            
        Returns:
            List of RelevanceScore objects sorted by total_score descending
        """
        scores = []
        for item in content_items:
            try:
                score = self.calculate_score(item, context, current_time)
                scores.append(score)
            except Exception as e:
                self.logger.error(f"Error calculating score for {item.id}: {e}")
                # Add a zero score to maintain list consistency
                scores.append(RelevanceScore(
                    content_id=item.id,
                    total_score=0.0,
                    recency_score=0.0,
                    relevance_score=0.0,
                    importance_score=0.0,
                    access_frequency_score=0.0,
                    explanation=f"Error calculating score: {e}"
                ))
        
        # Sort by total score descending
        scores.sort(key=lambda x: x.total_score, reverse=True)
        return scores

