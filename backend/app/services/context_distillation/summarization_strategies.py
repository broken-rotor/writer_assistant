"""
Summarization strategies for different types of story content.

This module provides specialized summarization strategies that preserve
key information while compressing content for different story elements.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from ..llm_inference import LLMInference

logger = logging.getLogger(__name__)


@dataclass
class SummaryResult:
    """Result of a summarization operation."""
    summary: str
    key_information: List[str] = field(default_factory=list)
    quality_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


class SummarizationStrategy(ABC):
    """
    Abstract base class for content summarization strategies.
    
    Each strategy specializes in summarizing specific types of story content
    while preserving the most important information for that content type.
    """
    
    def __init__(self, llm_service: LLMInference):
        """
        Initialize the summarization strategy.
        
        Args:
            llm_service: LLM service for generating summaries
        """
        self.llm_service = llm_service
    
    @abstractmethod
    def summarize(
        self,
        content: str,
        target_tokens: int,
        context: Dict[str, Any],
        preserve_key_info: bool = True
    ) -> SummaryResult:
        """
        Summarize content according to this strategy.
        
        Args:
            content: Content to summarize
            target_tokens: Target token count for summary
            context: Additional context for summarization
            preserve_key_info: Whether to preserve key information
            
        Returns:
            SummaryResult with the summary and metadata
        """
        pass
    
    def _build_prompt(
        self,
        content: str,
        target_tokens: int,
        specific_instructions: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Build a prompt for LLM summarization.
        
        Args:
            content: Content to summarize
            target_tokens: Target token count
            specific_instructions: Strategy-specific instructions
            context: Additional context
            
        Returns:
            Formatted prompt for the LLM
        """
        base_prompt = f"""You are an expert story editor tasked with creating a concise summary while preserving essential information.

CONTENT TO SUMMARIZE:
{content}

TARGET LENGTH: Approximately {target_tokens} tokens

SPECIFIC INSTRUCTIONS:
{specific_instructions}

CONTEXT:
{self._format_context(context)}

Please provide a well-structured summary that captures the most important elements while staying within the target length."""
        
        return base_prompt
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context information for the prompt."""
        if not context:
            return "No additional context provided."
        
        formatted_parts = []
        for key, value in context.items():
            if key == "is_meta_summary" and value:
                formatted_parts.append("- This is a summary of multiple existing summaries")
            elif key == "source_summary_count":
                formatted_parts.append(f"- Combining {value} previous summaries")
            elif key == "preserve_narrative_flow" and value:
                formatted_parts.append("- Maintain narrative flow and story progression")
            else:
                formatted_parts.append(f"- {key}: {value}")
        
        return "\n".join(formatted_parts) if formatted_parts else "No additional context provided."
    
    def _extract_key_information(self, content: str, summary: str) -> List[str]:
        """
        Extract key information that should be preserved.
        This is a simple implementation - could be enhanced with NLP techniques.
        """
        # Simple heuristic: look for important story elements
        key_info = []
        
        content_lower = content.lower()
        summary_lower = summary.lower()
        
        # Check for character names (capitalized words that appear multiple times)
        import re
        potential_names = re.findall(r'\b[A-Z][a-z]+\b', content)
        name_counts = {}
        for name in potential_names:
            name_counts[name] = name_counts.get(name, 0) + 1
        
        # Names that appear 3+ times are likely important characters
        important_names = [name for name, count in name_counts.items() if count >= 3]
        for name in important_names:
            if name.lower() in summary_lower:
                key_info.append(f"Character: {name}")
        
        # Look for plot keywords
        plot_keywords = ["conflict", "resolution", "climax", "turning point", "revelation", "death", "birth", "marriage"]
        for keyword in plot_keywords:
            if keyword in content_lower and keyword in summary_lower:
                key_info.append(f"Plot element: {keyword}")
        
        return key_info
    
    def _calculate_quality_score(self, content: str, summary: str, target_tokens: int) -> float:
        """
        Calculate a quality score for the summary.
        This is a simple implementation - could be enhanced with more sophisticated metrics.
        """
        if not summary or not content:
            return 0.0
        
        # Basic metrics
        compression_ratio = len(summary) / len(content)
        
        # Penalize if too far from target (simple token approximation)
        summary_tokens = len(summary.split())
        target_deviation = abs(summary_tokens - target_tokens) / target_tokens
        
        # Simple quality score based on compression and target adherence
        quality = 1.0 - min(target_deviation, 0.5)  # Cap penalty at 0.5
        
        # Bonus for reasonable compression (not too aggressive)
        if 0.2 <= compression_ratio <= 0.6:
            quality += 0.1
        
        return min(quality, 1.0)


class PlotSummaryStrategy(SummarizationStrategy):
    """Strategy for summarizing plot and narrative content."""
    
    def summarize(
        self,
        content: str,
        target_tokens: int,
        context: Dict[str, Any],
        preserve_key_info: bool = True
    ) -> SummaryResult:
        """Summarize plot content preserving key story beats."""
        
        specific_instructions = """Focus on:
- Main plot events and story progression
- Key conflicts and their resolutions
- Important character actions and decisions
- Cause-and-effect relationships between events
- Story turning points and climactic moments

Preserve the narrative flow while condensing descriptions and minor details."""
        
        try:
            prompt = self._build_prompt(content, target_tokens, specific_instructions, context)
            
            # Generate summary using LLM
            summary = self.llm_service.generate(
                prompt=prompt,
                max_tokens=target_tokens + 100,  # Allow some buffer
                temperature=0.3  # Lower temperature for consistency
            )
            
            # Extract key information
            key_info = self._extract_key_information(content, summary)
            if preserve_key_info:
                # Add plot-specific key information
                key_info.extend(self._extract_plot_elements(content, summary))
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(content, summary, target_tokens)
            
            return SummaryResult(
                summary=summary,
                key_information=key_info,
                quality_score=quality_score,
                metadata={
                    "strategy": "plot_summary",
                    "target_tokens": target_tokens,
                    "actual_tokens": len(summary.split())
                }
            )
            
        except Exception as e:
            logger.error(f"Plot summarization failed: {e}")
            return SummaryResult(
                summary="",
                warnings=[f"Summarization failed: {str(e)}"]
            )
    
    def _extract_plot_elements(self, content: str, summary: str) -> List[str]:
        """Extract plot-specific elements."""
        elements = []
        
        # Look for story structure elements
        structure_words = ["beginning", "middle", "end", "climax", "resolution", "conflict"]
        for word in structure_words:
            if word in content.lower() and word in summary.lower():
                elements.append(f"Story structure: {word}")
        
        return elements


class CharacterDevelopmentStrategy(SummarizationStrategy):
    """Strategy for summarizing character development and arcs."""
    
    def summarize(
        self,
        content: str,
        target_tokens: int,
        context: Dict[str, Any],
        preserve_key_info: bool = True
    ) -> SummaryResult:
        """Summarize character content preserving development arcs."""
        
        specific_instructions = """Focus on:
- Character growth and development arcs
- Key personality traits and changes
- Important relationships and dynamics
- Character motivations and goals
- Emotional states and psychological changes
- Character-defining moments and decisions

Preserve character authenticity while condensing physical descriptions and minor interactions."""
        
        try:
            prompt = self._build_prompt(content, target_tokens, specific_instructions, context)
            
            summary = self.llm_service.generate(
                prompt=prompt,
                max_tokens=target_tokens + 100,
                temperature=0.3
            )
            
            key_info = self._extract_key_information(content, summary)
            if preserve_key_info:
                key_info.extend(self._extract_character_elements(content, summary))
            
            quality_score = self._calculate_quality_score(content, summary, target_tokens)
            
            return SummaryResult(
                summary=summary,
                key_information=key_info,
                quality_score=quality_score,
                metadata={
                    "strategy": "character_development",
                    "target_tokens": target_tokens,
                    "actual_tokens": len(summary.split())
                }
            )
            
        except Exception as e:
            logger.error(f"Character development summarization failed: {e}")
            return SummaryResult(
                summary="",
                warnings=[f"Summarization failed: {str(e)}"]
            )
    
    def _extract_character_elements(self, content: str, summary: str) -> List[str]:
        """Extract character-specific elements."""
        elements = []
        
        # Look for character development keywords
        development_words = ["growth", "change", "learns", "realizes", "becomes", "transforms"]
        for word in development_words:
            if word in content.lower() and word in summary.lower():
                elements.append(f"Character development: {word}")
        
        return elements


class DialogueSummaryStrategy(SummarizationStrategy):
    """Strategy for summarizing dialogue and conversations."""
    
    def summarize(
        self,
        content: str,
        target_tokens: int,
        context: Dict[str, Any],
        preserve_key_info: bool = True
    ) -> SummaryResult:
        """Summarize dialogue preserving key exchanges."""
        
        specific_instructions = """Focus on:
- Key information revealed through dialogue
- Important character interactions and conflicts
- Emotional subtext and relationship dynamics
- Plot-advancing conversations
- Character voice and personality through speech

Convert lengthy dialogue into concise narrative summary while preserving essential exchanges."""
        
        try:
            prompt = self._build_prompt(content, target_tokens, specific_instructions, context)
            
            summary = self.llm_service.generate(
                prompt=prompt,
                max_tokens=target_tokens + 100,
                temperature=0.3
            )
            
            key_info = self._extract_key_information(content, summary)
            if preserve_key_info:
                key_info.extend(self._extract_dialogue_elements(content, summary))
            
            quality_score = self._calculate_quality_score(content, summary, target_tokens)
            
            return SummaryResult(
                summary=summary,
                key_information=key_info,
                quality_score=quality_score,
                metadata={
                    "strategy": "dialogue_summary",
                    "target_tokens": target_tokens,
                    "actual_tokens": len(summary.split())
                }
            )
            
        except Exception as e:
            logger.error(f"Dialogue summarization failed: {e}")
            return SummaryResult(
                summary="",
                warnings=[f"Summarization failed: {str(e)}"]
            )
    
    def _extract_dialogue_elements(self, content: str, summary: str) -> List[str]:
        """Extract dialogue-specific elements."""
        elements = []
        
        # Count dialogue markers
        quote_count = content.count('"') + content.count("'")
        if quote_count > 10:
            elements.append(f"Dialogue-heavy content: {quote_count} quote marks")
        
        return elements


class EventSequenceStrategy(SummarizationStrategy):
    """Strategy for summarizing sequences of events."""
    
    def summarize(
        self,
        content: str,
        target_tokens: int,
        context: Dict[str, Any],
        preserve_key_info: bool = True
    ) -> SummaryResult:
        """Summarize event sequences preserving chronology and causation."""
        
        specific_instructions = """Focus on:
- Chronological sequence of events
- Cause-and-effect relationships
- Key actions and their consequences
- Timeline and pacing
- Important transitions between events

Maintain the logical flow while condensing detailed descriptions."""
        
        try:
            prompt = self._build_prompt(content, target_tokens, specific_instructions, context)
            
            summary = self.llm_service.generate(
                prompt=prompt,
                max_tokens=target_tokens + 100,
                temperature=0.3
            )
            
            key_info = self._extract_key_information(content, summary)
            if preserve_key_info:
                key_info.extend(self._extract_event_elements(content, summary))
            
            quality_score = self._calculate_quality_score(content, summary, target_tokens)
            
            return SummaryResult(
                summary=summary,
                key_information=key_info,
                quality_score=quality_score,
                metadata={
                    "strategy": "event_sequence",
                    "target_tokens": target_tokens,
                    "actual_tokens": len(summary.split())
                }
            )
            
        except Exception as e:
            logger.error(f"Event sequence summarization failed: {e}")
            return SummaryResult(
                summary="",
                warnings=[f"Summarization failed: {str(e)}"]
            )
    
    def _extract_event_elements(self, content: str, summary: str) -> List[str]:
        """Extract event-specific elements."""
        elements = []
        
        # Look for temporal markers
        time_words = ["then", "next", "after", "before", "during", "while", "when"]
        for word in time_words:
            if word in content.lower() and word in summary.lower():
                elements.append(f"Temporal sequence: {word}")
        
        return elements


class EmotionalMomentStrategy(SummarizationStrategy):
    """Strategy for summarizing emotional moments and character feelings."""
    
    def summarize(
        self,
        content: str,
        target_tokens: int,
        context: Dict[str, Any],
        preserve_key_info: bool = True
    ) -> SummaryResult:
        """Summarize emotional content preserving feeling and impact."""
        
        specific_instructions = """Focus on:
- Emotional states and feelings
- Character reactions and responses
- Psychological impact of events
- Relationship dynamics and tensions
- Moments of vulnerability or strength
- Emotional turning points

Preserve the emotional resonance while condensing excessive detail."""
        
        try:
            prompt = self._build_prompt(content, target_tokens, specific_instructions, context)
            
            summary = self.llm_service.generate(
                prompt=prompt,
                max_tokens=target_tokens + 100,
                temperature=0.4  # Slightly higher temperature for emotional nuance
            )
            
            key_info = self._extract_key_information(content, summary)
            if preserve_key_info:
                key_info.extend(self._extract_emotional_elements(content, summary))
            
            quality_score = self._calculate_quality_score(content, summary, target_tokens)
            
            return SummaryResult(
                summary=summary,
                key_information=key_info,
                quality_score=quality_score,
                metadata={
                    "strategy": "emotional_moment",
                    "target_tokens": target_tokens,
                    "actual_tokens": len(summary.split())
                }
            )
            
        except Exception as e:
            logger.error(f"Emotional moment summarization failed: {e}")
            return SummaryResult(
                summary="",
                warnings=[f"Summarization failed: {str(e)}"]
            )
    
    def _extract_emotional_elements(self, content: str, summary: str) -> List[str]:
        """Extract emotion-specific elements."""
        elements = []
        
        # Look for emotional keywords
        emotion_words = ["love", "fear", "anger", "joy", "sadness", "hope", "despair", "anxiety"]
        for word in emotion_words:
            if word in content.lower() and word in summary.lower():
                elements.append(f"Emotion: {word}")
        
        return elements


class WorldBuildingStrategy(SummarizationStrategy):
    """Strategy for summarizing world-building and setting information."""
    
    def summarize(
        self,
        content: str,
        target_tokens: int,
        context: Dict[str, Any],
        preserve_key_info: bool = True
    ) -> SummaryResult:
        """Summarize world-building content preserving key setting details."""
        
        specific_instructions = """Focus on:
- Key locations and their significance
- World rules and systems
- Cultural and social elements
- Historical background relevant to the story
- Environmental details that affect the plot
- Unique aspects of the fictional world

Preserve essential world-building while condensing excessive descriptive detail."""
        
        try:
            prompt = self._build_prompt(content, target_tokens, specific_instructions, context)
            
            summary = self.llm_service.generate(
                prompt=prompt,
                max_tokens=target_tokens + 100,
                temperature=0.3
            )
            
            key_info = self._extract_key_information(content, summary)
            if preserve_key_info:
                key_info.extend(self._extract_worldbuilding_elements(content, summary))
            
            quality_score = self._calculate_quality_score(content, summary, target_tokens)
            
            return SummaryResult(
                summary=summary,
                key_information=key_info,
                quality_score=quality_score,
                metadata={
                    "strategy": "world_building",
                    "target_tokens": target_tokens,
                    "actual_tokens": len(summary.split())
                }
            )
            
        except Exception as e:
            logger.error(f"World building summarization failed: {e}")
            return SummaryResult(
                summary="",
                warnings=[f"Summarization failed: {str(e)}"]
            )
    
    def _extract_worldbuilding_elements(self, content: str, summary: str) -> List[str]:
        """Extract world-building specific elements."""
        elements = []
        
        # Look for setting keywords
        setting_words = ["kingdom", "city", "forest", "mountain", "castle", "village", "realm"]
        for word in setting_words:
            if word in content.lower() and word in summary.lower():
                elements.append(f"Setting: {word}")
        
        return elements
