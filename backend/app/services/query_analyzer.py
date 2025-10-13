"""
Query Analyzer for RAG Service.

Analyzes user queries to determine retrieval strategy:
- Whether full documents should be retrieved
- Source file specifications
- Follow-up detection
"""

import re
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class QueryAnalysis:
    """Result of query analysis."""
    needs_full_document: bool
    specified_sources: List[str]  # List of file names/paths specified by user
    detail_indicators: List[str]  # Keywords that triggered full document retrieval
    is_followup: bool  # Whether this appears to be a follow-up question


class QueryAnalyzer:
    """
    Analyzes queries to determine optimal retrieval strategy.

    Detects:
    - Keywords indicating need for detailed context
    - source:<filename> tags for specific document requests
    - Follow-up questions that need expanded context
    """

    # Keywords that indicate need for full document context
    DETAIL_KEYWORDS = [
        # Direct indicators
        'detail', 'detailed', 'details', 'elaborate', 'explain', 'explanation',
        'full', 'complete', 'entire', 'comprehensive', 'thorough',
        'tell me about', 'walk me through', 'describe', 'summarize', 'summary',

        # Temporal/progression indicators
        'throughout', 'over time', 'progression', 'evolution', 'develop', 'development',
        'how does', 'why does', 'what happens', 'trace', 'follow',

        # Scope indicators
        'all', 'every', 'whole', 'across', 'through',

        # Analytical indicators
        'relationship', 'interaction', 'connection', 'arc', 'journey',
        'theme', 'thematic', 'analysis', 'analyze'
    ]

    # Follow-up indicators
    FOLLOWUP_KEYWORDS = [
        'more', 'also', 'additionally', 'furthermore', 'what else',
        'tell me more', 'continue', 'expand', 'and then', 'next',
        'besides', 'other', 'another', 'further'
    ]

    # Pattern for source specification: source:<filename>
    SOURCE_TAG_PATTERN = re.compile(r'source:(\S+)', re.IGNORECASE)

    def __init__(self):
        """Initialize the query analyzer."""
        self._last_query_topic: Optional[str] = None
        self._conversation_depth = 0

    def analyze(
        self,
        query: str,
        previous_messages: Optional[List[Dict[str, str]]] = None
    ) -> QueryAnalysis:
        """
        Analyze a query to determine retrieval strategy.

        Args:
            query: The user's query text
            previous_messages: Optional list of previous chat messages for context

        Returns:
            QueryAnalysis with retrieval strategy recommendations
        """
        query_lower = query.lower()

        # 1. Check for source:<filename> tags
        specified_sources = self._extract_source_tags(query)

        # 2. Check for detail keywords
        detail_indicators = self._detect_detail_keywords(query_lower)

        # 3. Check if this is a follow-up question
        is_followup = self._detect_followup(query_lower, previous_messages)

        # 4. Determine if full document retrieval is needed
        needs_full_document = (
            len(specified_sources) > 0 or  # User explicitly specified sources
            len(detail_indicators) > 0 or   # Query contains detail keywords
            (is_followup and self._conversation_depth >= 1)  # Follow-up with context
        )

        # Update conversation tracking
        if is_followup:
            self._conversation_depth += 1
        else:
            self._conversation_depth = 0
            self._last_query_topic = self._extract_topic(query_lower)

        logger.info(
            f"Query analysis: full_doc={needs_full_document}, "
            f"sources={specified_sources}, "
            f"indicators={detail_indicators}, "
            f"followup={is_followup}"
        )

        return QueryAnalysis(
            needs_full_document=needs_full_document,
            specified_sources=specified_sources,
            detail_indicators=detail_indicators,
            is_followup=is_followup
        )

    def _extract_source_tags(self, query: str) -> List[str]:
        """
        Extract source:<filename> tags from query.

        Args:
            query: The query text

        Returns:
            List of specified file names
        """
        matches = self.SOURCE_TAG_PATTERN.findall(query)
        return [match.strip() for match in matches]

    def _detect_detail_keywords(self, query_lower: str) -> List[str]:
        """
        Detect keywords indicating need for detailed context.

        Args:
            query_lower: Lowercased query text

        Returns:
            List of detected detail keywords
        """
        detected = []
        for keyword in self.DETAIL_KEYWORDS:
            if keyword in query_lower:
                detected.append(keyword)

        return detected

    def _detect_followup(
        self,
        query_lower: str,
        previous_messages: Optional[List[Dict[str, str]]]
    ) -> bool:
        """
        Detect if query is a follow-up question.

        Args:
            query_lower: Lowercased query text
            previous_messages: Previous chat messages

        Returns:
            True if this appears to be a follow-up question
        """
        # Check for follow-up keywords
        for keyword in self.FOLLOWUP_KEYWORDS:
            if keyword in query_lower:
                return True

        # Check conversation history
        if previous_messages and len(previous_messages) > 0:
            # If there are recent messages and the query is short, likely a follow-up
            if len(query_lower.split()) < 10:
                return True

            # Check if same topic as last query
            if self._last_query_topic:
                current_topic = self._extract_topic(query_lower)
                if current_topic and self._has_topic_overlap(current_topic, self._last_query_topic):
                    return True

        return False

    def _extract_topic(self, query_lower: str) -> Optional[str]:
        """
        Extract main topic/subject from query.

        Simple extraction based on common nouns and character names.

        Args:
            query_lower: Lowercased query text

        Returns:
            Main topic or None
        """
        # Remove common question words
        words = query_lower.split()
        filtered_words = [
            w for w in words
            if w not in ['what', 'when', 'where', 'who', 'why', 'how', 'is', 'are', 'the', 'a', 'an']
        ]

        # Return first significant word as topic indicator
        if filtered_words:
            return filtered_words[0]

        return None

    def _has_topic_overlap(self, topic1: str, topic2: str) -> bool:
        """
        Check if two topics are related.

        Args:
            topic1: First topic
            topic2: Second topic

        Returns:
            True if topics appear related
        """
        # Simple substring check
        return (
            topic1 in topic2 or
            topic2 in topic1 or
            topic1[:4] == topic2[:4]  # Prefix match
        )

    def reset_conversation(self):
        """Reset conversation tracking state."""
        self._last_query_topic = None
        self._conversation_depth = 0
