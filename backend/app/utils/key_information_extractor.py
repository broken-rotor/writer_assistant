"""
Key Information Extractor for Context Distillation

This utility module provides functions to extract and identify key information
from story content that should be preserved during summarization and compression.
"""

import logging
import re
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import Counter
from enum import Enum

logger = logging.getLogger(__name__)


class InformationType(Enum):
    """Types of key information that can be extracted."""
    CHARACTER_NAME = "character_name"
    PLOT_POINT = "plot_point"
    LOCATION = "location"
    RELATIONSHIP = "relationship"
    CONFLICT = "conflict"
    EMOTION = "emotion"
    DIALOGUE = "dialogue"
    WORLD_BUILDING = "world_building"
    TEMPORAL_MARKER = "temporal_marker"
    CAUSAL_RELATIONSHIP = "causal_relationship"


@dataclass
class KeyInformation:
    """Represents a piece of key information extracted from content."""
    info_type: InformationType
    content: str
    importance_score: float
    context: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractionResult:
    """Result of key information extraction."""
    key_information: List[KeyInformation] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


class KeyInformationExtractor:
    """
    Extracts key information from story content that should be preserved
    during summarization and compression operations.
    """

    def __init__(self):
        """Initialize the key information extractor."""
        self._character_patterns = self._build_character_patterns()
        self._plot_patterns = self._build_plot_patterns()
        self._location_patterns = self._build_location_patterns()
        self._emotion_patterns = self._build_emotion_patterns()
        self._temporal_patterns = self._build_temporal_patterns()
        self._causal_patterns = self._build_causal_patterns()

        logger.info("KeyInformationExtractor initialized")

    def extract_key_information(
        self,
        content: str,
        content_type: Optional[str] = None,
        preserve_threshold: float = 0.5
    ) -> ExtractionResult:
        """
        Extract key information from content.

        Args:
            content: Text content to analyze
            content_type: Type of content (plot, character, dialogue, etc.)
            preserve_threshold: Minimum importance score to preserve information

        Returns:
            ExtractionResult with extracted key information
        """
        if not content or not content.strip():
            return ExtractionResult(warnings=["Empty content provided"])

        logger.info(f"Extracting key information from {len(content)} characters of content")

        key_info = []

        # Extract different types of information
        key_info.extend(self._extract_characters(content))
        key_info.extend(self._extract_plot_points(content))
        key_info.extend(self._extract_locations(content))
        key_info.extend(self._extract_relationships(content))
        key_info.extend(self._extract_conflicts(content))
        key_info.extend(self._extract_emotions(content))
        key_info.extend(self._extract_dialogue_elements(content))
        key_info.extend(self._extract_world_building(content))
        key_info.extend(self._extract_temporal_markers(content))
        key_info.extend(self._extract_causal_relationships(content))

        # Filter by importance threshold
        filtered_info = [info for info in key_info if info.importance_score >= preserve_threshold]

        # Sort by importance
        filtered_info.sort(key=lambda x: x.importance_score, reverse=True)

        # Generate statistics
        stats = self._generate_statistics(key_info, filtered_info)

        logger.info(f"Extracted {len(filtered_info)} key information items (threshold: {preserve_threshold})")

        return ExtractionResult(
            key_information=filtered_info,
            statistics=stats
        )

    def _extract_characters(self, content: str) -> List[KeyInformation]:
        """Extract character names and references."""
        characters = []

        # Find potential character names (capitalized words that appear multiple times)
        potential_names = re.findall(r'\b[A-Z][a-z]+\b', content)
        name_counts = Counter(potential_names)

        # Filter out common words that aren't names
        common_words = {
            'The', 'This', 'That', 'They', 'Then', 'There', 'When', 'Where', 'What', 'Who',
            'How', 'Why', 'But', 'And', 'Or', 'So', 'If', 'As', 'At', 'In', 'On', 'To',
            'For', 'With', 'By', 'From', 'Up', 'About', 'Into', 'Through', 'During',
            'Before', 'After', 'Above', 'Below', 'Between', 'Among', 'Chapter', 'Part'
        }

        for name, count in name_counts.items():
            if name not in common_words and count >= 2:  # Appears at least twice
                # Calculate importance based on frequency and context
                importance = min(0.5 + (count * 0.1), 1.0)

                # Look for character-indicating context
                name_pattern = rf'\b{re.escape(name)}\b'
                contexts = []
                for match in re.finditer(name_pattern, content):
                    start = max(0, match.start() - 50)
                    end = min(len(content), match.end() + 50)
                    contexts.append(content[start:end])

                # Boost importance if found with character indicators
                character_indicators = ['said', 'thought', 'felt', 'walked', 'ran', 'smiled', 'frowned']
                for context in contexts:
                    if any(indicator in context.lower() for indicator in character_indicators):
                        importance = min(importance + 0.2, 1.0)
                        break

                characters.append(KeyInformation(
                    info_type=InformationType.CHARACTER_NAME,
                    content=name,
                    importance_score=importance,
                    context=contexts[0] if contexts else "",
                    metadata={"frequency": count, "contexts": len(contexts)}
                ))

        return characters

    def _extract_plot_points(self, content: str) -> List[KeyInformation]:
        """Extract key plot points and story events."""
        plot_points = []

        for pattern_info in self._plot_patterns:
            pattern, keywords, base_importance = pattern_info

            for match in pattern.finditer(content):
                matched_text = match.group()

                # Get surrounding context
                start = max(0, match.start() - 100)
                end = min(len(content), match.end() + 100)
                context = content[start:end]

                # Calculate importance based on keywords present
                importance = base_importance
                for keyword in keywords:
                    if keyword.lower() in context.lower():
                        importance = min(importance + 0.1, 1.0)

                plot_points.append(KeyInformation(
                    info_type=InformationType.PLOT_POINT,
                    content=matched_text,
                    importance_score=importance,
                    context=context,
                    metadata={"pattern": pattern.pattern, "keywords_found": keywords}
                ))

        return plot_points

    def _extract_locations(self, content: str) -> List[KeyInformation]:
        """Extract location names and setting information."""
        locations = []

        for pattern_info in self._location_patterns:
            pattern, base_importance = pattern_info

            for match in pattern.finditer(content):
                matched_text = match.group()

                # Get context
                start = max(0, match.start() - 50)
                end = min(len(content), match.end() + 50)
                context = content[start:end]

                locations.append(KeyInformation(
                    info_type=InformationType.LOCATION,
                    content=matched_text,
                    importance_score=base_importance,
                    context=context,
                    metadata={"pattern": pattern.pattern}
                ))

        return locations

    def _extract_relationships(self, content: str) -> List[KeyInformation]:
        """Extract character relationships and dynamics."""
        relationships = []

        # Look for relationship indicators
        relationship_patterns = [
            (re.compile(r'\b(\w+)\s+(?:loves?|hates?|fears?|trusts?|betrays?)\s+(\w+)\b', re.IGNORECASE), 0.7),
            (re.compile(r'\b(\w+)\s+(?:and|with)\s+(\w+)\s+(?:were|are)\s+(?:friends?|enemies?|lovers?)\b', re.IGNORECASE), 0.8),
            (re.compile(r'\b(\w+)(?:\'s)?\s+(?:mother|father|sister|brother|son|daughter|wife|husband)\s+(\w+)\b', re.IGNORECASE), 0.9),
        ]

        for pattern, importance in relationship_patterns:
            for match in pattern.finditer(content):
                matched_text = match.group()

                # Get context
                start = max(0, match.start() - 75)
                end = min(len(content), match.end() + 75)
                context = content[start:end]

                relationships.append(KeyInformation(
                    info_type=InformationType.RELATIONSHIP,
                    content=matched_text,
                    importance_score=importance,
                    context=context,
                    metadata={"pattern": pattern.pattern}
                ))

        return relationships

    def _extract_conflicts(self, content: str) -> List[KeyInformation]:
        """Extract conflicts and tensions."""
        conflicts = []

        conflict_patterns = [
            (re.compile(r'\b(?:conflict|fight|battle|war|struggle|confrontation)\b.*?[.!?]', re.IGNORECASE | re.DOTALL), 0.8),
            (re.compile(r'\b(?:against|versus|opposed|enemy|rival)\b.*?[.!?]', re.IGNORECASE | re.DOTALL), 0.7),
            (re.compile(r'\b(?:tension|disagreement|argument|dispute)\b.*?[.!?]', re.IGNORECASE | re.DOTALL), 0.6),
        ]

        for pattern, importance in conflict_patterns:
            for match in pattern.finditer(content):
                matched_text = match.group().strip()

                # Limit length
                if len(matched_text) > 200:
                    matched_text = matched_text[:200] + "..."

                conflicts.append(KeyInformation(
                    info_type=InformationType.CONFLICT,
                    content=matched_text,
                    importance_score=importance,
                    context=matched_text,
                    metadata={"pattern": pattern.pattern}
                ))

        return conflicts

    def _extract_emotions(self, content: str) -> List[KeyInformation]:
        """Extract emotional moments and feelings."""
        emotions = []

        for pattern_info in self._emotion_patterns:
            emotion, pattern, importance = pattern_info

            for match in pattern.finditer(content):
                matched_text = match.group()

                # Get context
                start = max(0, match.start() - 50)
                end = min(len(content), match.end() + 50)
                context = content[start:end]

                emotions.append(KeyInformation(
                    info_type=InformationType.EMOTION,
                    content=matched_text,
                    importance_score=importance,
                    context=context,
                    metadata={"emotion": emotion, "pattern": pattern.pattern}
                ))

        return emotions

    def _extract_dialogue_elements(self, content: str) -> List[KeyInformation]:
        """Extract important dialogue and conversations."""
        dialogue_elements = []

        # Find quoted dialogue
        dialogue_pattern = r'"([^"]{20,200})"'

        for match in re.finditer(dialogue_pattern, content):
            dialogue_text = match.group(1)

            # Calculate importance based on content
            importance = 0.5

            # Boost importance for plot-relevant dialogue
            plot_keywords = ['secret', 'truth', 'lie', 'plan', 'kill', 'love', 'hate', 'betrayal']
            for keyword in plot_keywords:
                if keyword.lower() in dialogue_text.lower():
                    importance = min(importance + 0.2, 1.0)

            # Get speaker context
            start = max(0, match.start() - 100)
            context = content[start:match.end()]

            dialogue_elements.append(KeyInformation(
                info_type=InformationType.DIALOGUE,
                content=f'"{dialogue_text}"',
                importance_score=importance,
                context=context,
                metadata={"length": len(dialogue_text)}
            ))

        return dialogue_elements

    def _extract_world_building(self, content: str) -> List[KeyInformation]:
        """Extract world-building and setting details."""
        world_building = []

        world_patterns = [
            (re.compile(r'\b(?:kingdom|realm|empire|land|world|dimension)\s+of\s+\w+\b', re.IGNORECASE | re.DOTALL), 0.8),
            (re.compile(r'\b(?:magic|spell|enchantment|curse|prophecy)\b.*?[.!?]', re.IGNORECASE | re.DOTALL), 0.7),
            (re.compile(r'\b(?:ancient|legendary|mythical|sacred)\s+\w+\b', re.IGNORECASE | re.DOTALL), 0.6),
        ]

        for pattern, importance in world_patterns:
            for match in pattern.finditer(content):
                matched_text = match.group().strip()

                # Limit length
                if len(matched_text) > 150:
                    matched_text = matched_text[:150] + "..."

                world_building.append(KeyInformation(
                    info_type=InformationType.WORLD_BUILDING,
                    content=matched_text,
                    importance_score=importance,
                    context=matched_text,
                    metadata={"pattern": pattern.pattern}
                ))

        return world_building

    def _extract_temporal_markers(self, content: str) -> List[KeyInformation]:
        """Extract temporal markers and time references."""
        temporal_markers = []

        for pattern_info in self._temporal_patterns:
            pattern, importance = pattern_info

            for match in pattern.finditer(content):
                matched_text = match.group()

                # Get context
                start = max(0, match.start() - 30)
                end = min(len(content), match.end() + 30)
                context = content[start:end]

                temporal_markers.append(KeyInformation(
                    info_type=InformationType.TEMPORAL_MARKER,
                    content=matched_text,
                    importance_score=importance,
                    context=context,
                    metadata={"pattern": pattern.pattern}
                ))

        return temporal_markers

    def _extract_causal_relationships(self, content: str) -> List[KeyInformation]:
        """Extract cause-and-effect relationships."""
        causal_relationships = []

        for pattern_info in self._causal_patterns:
            pattern, importance = pattern_info

            for match in pattern.finditer(content):
                matched_text = match.group().strip()

                # Limit length
                if len(matched_text) > 200:
                    matched_text = matched_text[:200] + "..."

                causal_relationships.append(KeyInformation(
                    info_type=InformationType.CAUSAL_RELATIONSHIP,
                    content=matched_text,
                    importance_score=importance,
                    context=matched_text,
                    metadata={"pattern": pattern.pattern}
                ))

        return causal_relationships

    def _build_character_patterns(self) -> List[Tuple[re.Pattern, List[str], float]]:
        """Build patterns for character detection."""
        return [(re.compile(r'\b[A-Z][a-z]+\s+(?:said|thought|felt|walked|ran|smiled)\b', re.IGNORECASE), ['dialogue', 'action'],
                 0.8), (re.compile(r'\b(?:he|she|they)\s+(?:was|were|is|are)\s+\w+\b', re.IGNORECASE), ['description'], 0.6), ]

    def _build_plot_patterns(self) -> List[Tuple[re.Pattern, List[str], float]]:
        """Build patterns for plot point detection."""
        return [
            (re.compile(r'\b(?:suddenly|unexpectedly|meanwhile|however)\b.*?[.!?]', re.IGNORECASE), ['transition', 'surprise'], 0.7),
            (re.compile(r'\b(?:revealed|discovered|realized|understood)\b.*?[.!?]', re.IGNORECASE), ['revelation'], 0.8),
            (re.compile(r'\b(?:died|killed|murdered|destroyed)\b.*?[.!?]', re.IGNORECASE), ['death', 'violence'], 0.9),
            (re.compile(r'\b(?:married|wedding|born|birth)\b.*?[.!?]', re.IGNORECASE), ['life_event'], 0.8),
        ]

    def _build_location_patterns(self) -> List[Tuple[re.Pattern, float]]:
        """Build patterns for location detection."""
        return [
            (re.compile(r'\b(?:castle|palace|tower|fortress|stronghold)\s+\w+\b', re.IGNORECASE), 0.8),
            (re.compile(r'\b(?:city|town|village|hamlet)\s+of\s+\w+\b', re.IGNORECASE), 0.7),
            (re.compile(r'\b(?:forest|mountain|river|lake|sea|ocean)\s+\w+\b', re.IGNORECASE), 0.6),
            (re.compile(r'\b(?:in|at|near|by)\s+(?:the\s+)?\w+(?:\s+\w+)?\b', re.IGNORECASE), 0.5),
        ]

    def _build_emotion_patterns(self) -> List[Tuple[str, re.Pattern, float]]:
        """Build patterns for emotion detection."""
        return [
            ('love', re.compile(r'\b(?:love|adore|cherish|treasure)\b', re.IGNORECASE), 0.8),
            ('fear', re.compile(r'\b(?:fear|afraid|terrified|scared|frightened)\b', re.IGNORECASE), 0.7),
            ('anger', re.compile(r'\b(?:angry|furious|rage|mad|enraged)\b', re.IGNORECASE), 0.7),
            ('sadness', re.compile(r'\b(?:sad|depressed|melancholy|grief|sorrow)\b', re.IGNORECASE), 0.7),
            ('joy', re.compile(r'\b(?:happy|joyful|elated|delighted|ecstatic)\b', re.IGNORECASE), 0.6),
            ('surprise', re.compile(r'\b(?:surprised|shocked|amazed|astonished)\b', re.IGNORECASE), 0.6),
        ]

    def _build_temporal_patterns(self) -> List[Tuple[re.Pattern, float]]:
        """Build patterns for temporal marker detection."""
        return [
            (re.compile(r'\b(?:then|next|after|before|during|while|when|meanwhile)\b', re.IGNORECASE), 0.6),
            (re.compile(r'\b(?:years?|months?|weeks?|days?|hours?|minutes?)\s+(?:ago|later|before|after)\b', re.IGNORECASE), 0.7),
            (re.compile(r'\b(?:yesterday|today|tomorrow|now|soon|eventually)\b', re.IGNORECASE), 0.5),
        ]

    def _build_causal_patterns(self) -> List[Tuple[re.Pattern, float]]:
        """Build patterns for causal relationship detection."""
        return [
            (re.compile(r'\b(?:because|since|as|due to|owing to)\b.*?[.!?]', re.IGNORECASE), 0.8),
            (re.compile(r'\b(?:therefore|thus|consequently|as a result)\b.*?[.!?]', re.IGNORECASE), 0.8),
            (re.compile(r'\b(?:if|when|unless|provided that)\b.*?[.!?]', re.IGNORECASE), 0.7),
        ]

    def _generate_statistics(
        self,
        all_info: List[KeyInformation],
        filtered_info: List[KeyInformation]
    ) -> Dict[str, Any]:
        """Generate statistics about extracted information."""

        # Count by type
        type_counts = Counter(info.info_type for info in all_info)
        filtered_type_counts = Counter(info.info_type for info in filtered_info)

        # Calculate average importance scores
        avg_importance = sum(info.importance_score for info in all_info) / len(all_info) if all_info else 0

        return {
            "total_extracted": len(all_info),
            "total_preserved": len(filtered_info),
            "preservation_ratio": len(filtered_info) / len(all_info) if all_info else 0,
            "average_importance": avg_importance,
            "type_counts": {info_type.value: count for info_type, count in type_counts.items()},
            "filtered_type_counts": {info_type.value: count for info_type, count in filtered_type_counts.items()},
            "top_importance_scores": sorted([info.importance_score for info in filtered_info], reverse=True)[:10]
        }

    def get_preservation_recommendations(
        self,
        extraction_result: ExtractionResult,
        target_compression_ratio: float = 0.3
    ) -> Dict[str, Any]:
        """
        Get recommendations for what information to preserve during compression.

        Args:
            extraction_result: Result from extract_key_information
            target_compression_ratio: Target compression ratio (0.3 = compress to 30%)

        Returns:
            Dictionary with preservation recommendations
        """
        key_info = extraction_result.key_information

        if not key_info:
            return {"recommendations": [], "warnings": ["No key information found"]}

        # Calculate how many items to preserve based on compression ratio
        target_items = max(1, int(len(key_info) * target_compression_ratio))

        # Sort by importance and take top items
        top_items = sorted(key_info, key=lambda x: x.importance_score, reverse=True)[:target_items]

        # Group recommendations by type
        recommendations_by_type = {}
        for item in top_items:
            info_type = item.info_type.value
            if info_type not in recommendations_by_type:
                recommendations_by_type[info_type] = []
            recommendations_by_type[info_type].append({
                "content": item.content,
                "importance": item.importance_score,
                "context": item.context[:100] + "..." if len(item.context) > 100 else item.context
            })

        return {
            "target_items": target_items,
            "recommendations_by_type": recommendations_by_type,
            "preservation_strategy": self._suggest_preservation_strategy(top_items),
            "quality_indicators": self._assess_preservation_quality(top_items, extraction_result.statistics)
        }

    def _suggest_preservation_strategy(self, preserved_items: List[KeyInformation]) -> Dict[str, str]:
        """Suggest preservation strategy based on preserved items."""
        type_counts = Counter(item.info_type for item in preserved_items)

        strategy = {}

        if type_counts[InformationType.CHARACTER_NAME] > 0:
            strategy["characters"] = "Preserve main character names and key relationships"

        if type_counts[InformationType.PLOT_POINT] > 0:
            strategy["plot"] = "Maintain story progression and key events"

        if type_counts[InformationType.CONFLICT] > 0:
            strategy["conflict"] = "Keep central conflicts and resolutions"

        if type_counts[InformationType.EMOTION] > 0:
            strategy["emotion"] = "Preserve emotional beats and character development"

        return strategy

    def _assess_preservation_quality(
        self,
        preserved_items: List[KeyInformation],
        statistics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess the quality of preservation recommendations."""

        if not preserved_items:
            return {"quality_score": 0.0, "issues": ["No items preserved"]}

        # Calculate quality metrics
        avg_importance = sum(item.importance_score for item in preserved_items) / len(preserved_items)
        type_diversity = len(set(item.info_type for item in preserved_items))

        quality_score = (avg_importance * 0.7) + (min(type_diversity / 5, 1.0) * 0.3)

        issues = []
        if avg_importance < 0.6:
            issues.append("Low average importance score")
        if type_diversity < 3:
            issues.append("Limited diversity in information types")

        return {
            "quality_score": quality_score,
            "average_importance": avg_importance,
            "type_diversity": type_diversity,
            "issues": issues
        }
