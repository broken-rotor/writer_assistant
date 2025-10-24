"""
RAG Retriever for Dynamic Character/World Data Retrieval

Implements embedding-based and keyword-based retrieval strategies for identifying
the most relevant character and world data elements for Layer D allocation.
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json

from ...utils.relevance_calculator import (
    ContentItem, ContentCategory, RelevanceCalculator, RelevanceScore
)
from ..token_management.token_counter import TokenCounter, CountingStrategy

logger = logging.getLogger(__name__)


class RetrievalStrategy(Enum):
    """Available retrieval strategies."""
    EMBEDDING_BASED = "embedding_based"
    KEYWORD_BASED = "keyword_based"
    HYBRID = "hybrid"
    SEMANTIC_SEARCH = "semantic_search"


class RetrievalMode(Enum):
    """Retrieval modes for different use cases."""
    CHARACTER_FOCUSED = "character_focused"
    SCENE_FOCUSED = "scene_focused"
    PLOT_FOCUSED = "plot_focused"
    BALANCED = "balanced"


@dataclass
class RetrievalQuery:
    """Query for content retrieval."""
    query_text: str
    strategy: RetrievalStrategy
    mode: RetrievalMode
    max_results: int = 5
    min_relevance_score: float = 0.3
    target_categories: Set[ContentCategory] = field(default_factory=set)
    context: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize default target categories if not specified."""
        if not self.target_categories:
            if self.mode == RetrievalMode.CHARACTER_FOCUSED:
                self.target_categories = {ContentCategory.CHARACTER, ContentCategory.DIALOGUE}
            elif self.mode == RetrievalMode.SCENE_FOCUSED:
                self.target_categories = {ContentCategory.SCENE, ContentCategory.WORLD_BUILDING}
            elif self.mode == RetrievalMode.PLOT_FOCUSED:
                self.target_categories = {ContentCategory.PLOT_POINT, ContentCategory.NARRATIVE}
            else:  # BALANCED
                self.target_categories = set(ContentCategory)


@dataclass
class RetrievalResult:
    """Result of content retrieval operation."""
    query: RetrievalQuery
    retrieved_items: List[ContentItem]
    relevance_scores: List[RelevanceScore]
    total_items_considered: int
    retrieval_time_ms: float
    strategy_used: RetrievalStrategy
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EmbeddingConfig:
    """Configuration for embedding-based retrieval."""
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    similarity_threshold: float = 0.5
    max_embedding_cache_size: int = 1000
    enable_semantic_chunking: bool = True


class RAGRetriever:
    """
    RAG-based retrieval system for dynamic character/world data retrieval.
    
    Supports multiple retrieval strategies:
    1. Embedding-based: Uses semantic similarity with embeddings
    2. Keyword-based: Uses keyword matching and TF-IDF scoring
    3. Hybrid: Combines embedding and keyword approaches
    4. Semantic search: Advanced semantic understanding
    """
    
    def __init__(
        self,
        relevance_calculator: Optional[RelevanceCalculator] = None,
        token_counter: Optional[TokenCounter] = None,
        embedding_config: Optional[EmbeddingConfig] = None
    ):
        """Initialize the RAG retriever."""
        self.relevance_calculator = relevance_calculator or RelevanceCalculator()
        self.token_counter = token_counter or TokenCounter()
        self.embedding_config = embedding_config or EmbeddingConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize retrieval components
        self._embedding_cache = {}
        self._keyword_index = {}
        self._performance_metrics = {
            'total_retrievals': 0,
            'average_retrieval_time': 0.0,
            'cache_hit_rate': 0.0,
            'strategy_usage': {strategy.value: 0 for strategy in RetrievalStrategy}
        }
    
    def retrieve(
        self,
        query: RetrievalQuery,
        content_pool: List[ContentItem]
    ) -> RetrievalResult:
        """
        Retrieve the most relevant content items based on the query.
        
        Args:
            query: Retrieval query with strategy and parameters
            content_pool: Pool of content items to search through
            
        Returns:
            RetrievalResult with retrieved items and metadata
        """
        start_time = datetime.now()
        
        # Filter content pool by target categories
        filtered_pool = [
            item for item in content_pool
            if item.category in query.target_categories
        ]
        
        # Apply retrieval strategy
        if query.strategy == RetrievalStrategy.EMBEDDING_BASED:
            retrieved_items = self._embedding_based_retrieval(query, filtered_pool)
        elif query.strategy == RetrievalStrategy.KEYWORD_BASED:
            retrieved_items = self._keyword_based_retrieval(query, filtered_pool)
        elif query.strategy == RetrievalStrategy.HYBRID:
            retrieved_items = self._hybrid_retrieval(query, filtered_pool)
        elif query.strategy == RetrievalStrategy.SEMANTIC_SEARCH:
            retrieved_items = self._semantic_search_retrieval(query, filtered_pool)
        else:
            # Default to keyword-based
            retrieved_items = self._keyword_based_retrieval(query, filtered_pool)
        
        # Calculate relevance scores for retrieved items
        relevance_scores = self.relevance_calculator.batch_calculate_scores(
            retrieved_items, query.context
        )
        
        # Filter by minimum relevance score
        filtered_results = [
            (item, score) for item, score in zip(retrieved_items, relevance_scores)
            if score.total_score >= query.min_relevance_score
        ]
        
        # Sort by relevance score and limit results
        filtered_results.sort(key=lambda x: x[1].total_score, reverse=True)
        filtered_results = filtered_results[:query.max_results]
        
        final_items = [item for item, _ in filtered_results]
        final_scores = [score for _, score in filtered_results]
        
        # Calculate performance metrics
        retrieval_time = (datetime.now() - start_time).total_seconds() * 1000
        self._update_performance_metrics(query.strategy, retrieval_time)
        
        result = RetrievalResult(
            query=query,
            retrieved_items=final_items,
            relevance_scores=final_scores,
            total_items_considered=len(filtered_pool),
            retrieval_time_ms=retrieval_time,
            strategy_used=query.strategy,
            metadata={
                'filtered_pool_size': len(filtered_pool),
                'pre_filter_results': len(retrieved_items),
                'post_filter_results': len(final_items),
                'average_relevance_score': sum(s.total_score for s in final_scores) / max(len(final_scores), 1)
            }
        )
        
        self.logger.info(
            f"Retrieved {len(final_items)} items using {query.strategy.value} "
            f"strategy in {retrieval_time:.2f}ms"
        )
        
        return result
    
    def _embedding_based_retrieval(
        self,
        query: RetrievalQuery,
        content_pool: List[ContentItem]
    ) -> List[ContentItem]:
        """
        Retrieve content using embedding-based semantic similarity.
        
        Note: This is a simplified implementation. In a production system,
        you would use actual embedding models like sentence-transformers.
        """
        # For now, implement a simplified version using keyword overlap
        # as a proxy for semantic similarity
        query_words = set(self._extract_keywords(query.query_text))
        
        scored_items = []
        for item in content_pool:
            content_words = set(self._extract_keywords(item.content))
            
            # Calculate Jaccard similarity as proxy for embedding similarity
            intersection = len(query_words & content_words)
            union = len(query_words | content_words)
            similarity = intersection / union if union > 0 else 0.0
            
            # Boost similarity for character/location name matches
            if query_words & item.character_names:
                similarity += 0.3
            if query_words & item.location_names:
                similarity += 0.2
            
            scored_items.append((item, similarity))
        
        # Sort by similarity and return top items
        scored_items.sort(key=lambda x: x[1], reverse=True)
        return [item for item, _ in scored_items[:query.max_results * 2]]
    
    def _keyword_based_retrieval(
        self,
        query: RetrievalQuery,
        content_pool: List[ContentItem]
    ) -> List[ContentItem]:
        """Retrieve content using keyword matching and TF-IDF-like scoring."""
        query_keywords = self._extract_keywords(query.query_text)
        
        scored_items = []
        for item in content_pool:
            score = self._calculate_keyword_score(query_keywords, item)
            scored_items.append((item, score))
        
        # Sort by score and return top items
        scored_items.sort(key=lambda x: x[1], reverse=True)
        return [item for item, score in scored_items if score > 0][:query.max_results * 2]
    
    def _hybrid_retrieval(
        self,
        query: RetrievalQuery,
        content_pool: List[ContentItem]
    ) -> List[ContentItem]:
        """Combine embedding-based and keyword-based retrieval."""
        # Get results from both strategies
        embedding_query = RetrievalQuery(
            query_text=query.query_text,
            strategy=RetrievalStrategy.EMBEDDING_BASED,
            mode=query.mode,
            max_results=query.max_results,
            target_categories=query.target_categories,
            context=query.context
        )
        
        keyword_query = RetrievalQuery(
            query_text=query.query_text,
            strategy=RetrievalStrategy.KEYWORD_BASED,
            mode=query.mode,
            max_results=query.max_results,
            target_categories=query.target_categories,
            context=query.context
        )
        
        embedding_items = self._embedding_based_retrieval(embedding_query, content_pool)
        keyword_items = self._keyword_based_retrieval(keyword_query, content_pool)
        
        # Combine and deduplicate results
        combined_items = []
        seen_ids = set()
        
        # Interleave results to balance both approaches
        max_len = max(len(embedding_items), len(keyword_items))
        for i in range(max_len):
            if i < len(embedding_items) and embedding_items[i].id not in seen_ids:
                combined_items.append(embedding_items[i])
                seen_ids.add(embedding_items[i].id)
            
            if i < len(keyword_items) and keyword_items[i].id not in seen_ids:
                combined_items.append(keyword_items[i])
                seen_ids.add(keyword_items[i].id)
        
        return combined_items[:query.max_results * 2]
    
    def _semantic_search_retrieval(
        self,
        query: RetrievalQuery,
        content_pool: List[ContentItem]
    ) -> List[ContentItem]:
        """
        Advanced semantic search with context understanding.
        
        This implementation uses enhanced keyword matching with context awareness.
        In a production system, this would use advanced NLP models.
        """
        # Extract entities and concepts from query
        query_entities = self._extract_entities(query.query_text)
        query_concepts = self._extract_concepts(query.query_text, query.context)
        
        scored_items = []
        for item in content_pool:
            # Calculate semantic relevance score
            entity_score = self._calculate_entity_overlap(query_entities, item)
            concept_score = self._calculate_concept_relevance(query_concepts, item)
            context_score = self._calculate_context_relevance(query.context, item)
            
            # Weighted combination
            total_score = (entity_score * 0.4 + concept_score * 0.4 + context_score * 0.2)
            scored_items.append((item, total_score))
        
        # Sort by score and return top items
        scored_items.sort(key=lambda x: x[1], reverse=True)
        return [item for item, score in scored_items if score > 0.1][:query.max_results * 2]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        # Simple keyword extraction - remove stopwords and punctuation
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
        }
        
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [word for word in words if word not in stopwords and len(word) > 2]
        return keywords
    
    def _calculate_keyword_score(self, query_keywords: List[str], item: ContentItem) -> float:
        """Calculate keyword-based relevance score."""
        content_keywords = self._extract_keywords(item.content)
        
        if not query_keywords or not content_keywords:
            return 0.0
        
        # Calculate term frequency
        keyword_matches = 0
        for keyword in query_keywords:
            if keyword in content_keywords:
                keyword_matches += 1
        
        # Base score from keyword overlap
        base_score = keyword_matches / len(query_keywords)
        
        # Boost for exact phrase matches
        phrase_boost = 0.0
        query_text = ' '.join(query_keywords)
        if query_text in item.content.lower():
            phrase_boost = 0.3
        
        # Boost for character/location name matches
        name_boost = 0.0
        query_set = set(query_keywords)
        if query_set & item.character_names:
            name_boost += 0.2
        if query_set & item.location_names:
            name_boost += 0.1
        
        return base_score + phrase_boost + name_boost
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities from text (simplified implementation)."""
        # Simple pattern-based entity extraction
        entities = {
            'characters': [],
            'locations': [],
            'objects': []
        }
        
        # Look for capitalized words (potential proper nouns)
        words = re.findall(r'\b[A-Z][a-z]+\b', text)
        
        # Simple heuristics for entity classification
        for word in words:
            if word.lower() in ['room', 'house', 'city', 'forest', 'mountain']:
                entities['locations'].append(word.lower())
            elif len(word) > 2:  # Assume other capitalized words are character names
                entities['characters'].append(word.lower())
        
        return entities
    
    def _extract_concepts(self, text: str, context: Dict[str, Any]) -> List[str]:
        """Extract conceptual themes from text."""
        concepts = []
        
        # Emotion concepts
        emotion_words = ['happy', 'sad', 'angry', 'fear', 'love', 'hate', 'joy', 'sorrow']
        for emotion in emotion_words:
            if emotion in text.lower():
                concepts.append(f"emotion_{emotion}")
        
        # Action concepts
        action_words = ['fight', 'run', 'walk', 'talk', 'think', 'remember', 'forget']
        for action in action_words:
            if action in text.lower():
                concepts.append(f"action_{action}")
        
        # Context-based concepts
        if 'current_scene_type' in context:
            concepts.append(f"scene_{context['current_scene_type']}")
        
        return concepts
    
    def _calculate_entity_overlap(
        self, 
        query_entities: Dict[str, List[str]], 
        item: ContentItem
    ) -> float:
        """Calculate entity overlap score."""
        total_overlap = 0
        total_entities = sum(len(entities) for entities in query_entities.values())
        
        if total_entities == 0:
            return 0.0
        
        # Character entity overlap
        query_chars = set(query_entities.get('characters', []))
        item_chars = {name.lower() for name in item.character_names}
        char_overlap = len(query_chars & item_chars)
        
        # Location entity overlap
        query_locs = set(query_entities.get('locations', []))
        item_locs = {name.lower() for name in item.location_names}
        loc_overlap = len(query_locs & item_locs)
        
        total_overlap = char_overlap + loc_overlap
        return total_overlap / total_entities
    
    def _calculate_concept_relevance(self, query_concepts: List[str], item: ContentItem) -> float:
        """Calculate conceptual relevance score."""
        if not query_concepts:
            return 0.0
        
        content_lower = item.content.lower()
        concept_matches = 0
        
        for concept in query_concepts:
            if concept.startswith('emotion_'):
                emotion = concept.split('_')[1]
                if emotion in content_lower:
                    concept_matches += 1
            elif concept.startswith('action_'):
                action = concept.split('_')[1]
                if action in content_lower:
                    concept_matches += 1
            elif concept.startswith('scene_'):
                scene_type = concept.split('_')[1]
                if scene_type.lower() in content_lower:
                    concept_matches += 1
        
        return concept_matches / len(query_concepts)
    
    def _calculate_context_relevance(self, context: Dict[str, Any], item: ContentItem) -> float:
        """Calculate relevance based on current context."""
        relevance_score = 0.0
        
        # Active characters context
        active_chars = set(context.get('active_characters', []))
        if active_chars & item.character_names:
            relevance_score += 0.5
        
        # Active locations context
        active_locs = set(context.get('active_locations', []))
        if active_locs & item.location_names:
            relevance_score += 0.3
        
        # Keywords context
        active_keywords = set(context.get('keywords', []))
        content_words = set(self._extract_keywords(item.content))
        if active_keywords & content_words:
            relevance_score += 0.2
        
        return min(1.0, relevance_score)
    
    def _update_performance_metrics(self, strategy: RetrievalStrategy, retrieval_time: float):
        """Update performance tracking metrics."""
        self._performance_metrics['total_retrievals'] += 1
        self._performance_metrics['strategy_usage'][strategy.value] += 1
        
        # Update rolling average retrieval time
        total_retrievals = self._performance_metrics['total_retrievals']
        current_avg = self._performance_metrics['average_retrieval_time']
        new_avg = ((current_avg * (total_retrievals - 1)) + retrieval_time) / total_retrievals
        self._performance_metrics['average_retrieval_time'] = new_avg
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        return self._performance_metrics.copy()
    
    def clear_cache(self):
        """Clear embedding and keyword caches."""
        self._embedding_cache.clear()
        self._keyword_index.clear()
        self.logger.info("Cleared retrieval caches")
    
    def get_top_characters(
        self,
        query_text: str,
        content_pool: List[ContentItem],
        max_results: int = 3
    ) -> List[ContentItem]:
        """Convenience method to get top relevant characters."""
        query = RetrievalQuery(
            query_text=query_text,
            strategy=RetrievalStrategy.HYBRID,
            mode=RetrievalMode.CHARACTER_FOCUSED,
            max_results=max_results,
            target_categories={ContentCategory.CHARACTER}
        )
        
        result = self.retrieve(query, content_pool)
        return result.retrieved_items
    
    def get_top_scenes(
        self,
        query_text: str,
        content_pool: List[ContentItem],
        max_results: int = 3
    ) -> List[ContentItem]:
        """Convenience method to get top relevant scenes."""
        query = RetrievalQuery(
            query_text=query_text,
            strategy=RetrievalStrategy.HYBRID,
            mode=RetrievalMode.SCENE_FOCUSED,
            max_results=max_results,
            target_categories={ContentCategory.SCENE, ContentCategory.WORLD_BUILDING}
        )
        
        result = self.retrieve(query, content_pool)
        return result.retrieved_items

