"""
Token Counter for Writer Assistant

Provides accurate token counting for different content types using Llama tokenization.
Supports various counting strategies and content type detection for the multi-agent
storytelling system.
"""

import logging
import re
from typing import Dict, List, Optional, Union, Tuple, Any
from enum import Enum
from dataclasses import dataclass

from ...utils.llama_tokenizer import LlamaTokenizer

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Content types for different token counting strategies."""
    NARRATIVE = "narrative"
    DIALOGUE = "dialogue"
    SYSTEM_PROMPT = "system_prompt"
    CHARACTER_DESCRIPTION = "character_description"
    SCENE_DESCRIPTION = "scene_description"
    INTERNAL_MONOLOGUE = "internal_monologue"
    METADATA = "metadata"
    UNKNOWN = "unknown"


class CountingStrategy(Enum):
    """Token counting strategies for different use cases."""
    EXACT = "exact"  # Precise token count using tokenizer
    ESTIMATED = "estimated"  # Fast estimation with overhead
    CONSERVATIVE = "conservative"  # Higher overhead for safety
    OPTIMISTIC = "optimistic"  # Lower overhead for efficiency


@dataclass
class TokenCount:
    """Result of token counting operation."""
    content: str
    token_count: int
    content_type: ContentType
    strategy: CountingStrategy
    overhead_applied: float
    metadata: Dict[str, Any]


class TokenCounter:
    """
    Advanced token counter with content type detection and multiple counting strategies.
    
    This class provides accurate token counting for the Writer Assistant's multi-agent
    storytelling system, with support for different content types and counting strategies.
    """
    
    def __init__(self, tokenizer: Optional[LlamaTokenizer] = None, model_path: Optional[str] = None):
        """
        Initialize the TokenCounter.
        
        Args:
            tokenizer: LlamaTokenizer instance. If None, will create or get singleton.
            model_path: Path to model file for tokenizer initialization.
        """
        if tokenizer is not None:
            self.tokenizer = tokenizer
        else:
            self.tokenizer = LlamaTokenizer.get_instance(model_path)
        
        # Content type detection patterns
        self._content_patterns = {
            ContentType.DIALOGUE: [
                r'"[^"]*"',  # Quoted dialogue
                r"'[^']*'",  # Single-quoted dialogue
                r'said|asked|replied|whispered|shouted|exclaimed',  # Dialogue tags
            ],
            ContentType.SYSTEM_PROMPT: [
                r'You are|Your role|Act as|Respond as',  # System instructions
                r'<\|system\|>|<\|user\|>|<\|assistant\|>',  # Chat templates
            ],
            ContentType.CHARACTER_DESCRIPTION: [
                r'character|personality|trait|appearance|background',
                r'age:|height:|occupation:|personality:',
            ],
            ContentType.SCENE_DESCRIPTION: [
                r'The room|The street|The forest|The building',
                r'setting|location|environment|atmosphere',
            ],
            ContentType.INTERNAL_MONOLOGUE: [
                r'thought|wondered|realized|remembered|felt',
                r'\(thinking\)|\(internal\)|mental note',
            ],
            ContentType.METADATA: [
                r'timestamp:|id:|type:|version:',
                r'\{[^}]*\}',  # JSON-like structures
            ]
        }
        
        # Strategy configurations
        self._strategy_configs = {
            CountingStrategy.EXACT: {"overhead": 1.0, "use_tokenizer": True},
            CountingStrategy.ESTIMATED: {"overhead": 1.1, "use_tokenizer": True},
            CountingStrategy.CONSERVATIVE: {"overhead": 1.25, "use_tokenizer": True},
            CountingStrategy.OPTIMISTIC: {"overhead": 0.95, "use_tokenizer": True},
        }
        
        # Content type multipliers for different overhead needs
        self._content_type_multipliers = {
            ContentType.NARRATIVE: 1.0,
            ContentType.DIALOGUE: 1.05,  # Slightly higher due to formatting
            ContentType.SYSTEM_PROMPT: 1.15,  # Higher due to special tokens
            ContentType.CHARACTER_DESCRIPTION: 1.0,
            ContentType.SCENE_DESCRIPTION: 1.0,
            ContentType.INTERNAL_MONOLOGUE: 1.0,
            ContentType.METADATA: 1.2,  # Higher due to structured format
            ContentType.UNKNOWN: 1.1,  # Conservative default
        }
    
    def detect_content_type(self, content: str) -> ContentType:
        """
        Detect the content type based on text patterns.
        
        Args:
            content: Text content to analyze
            
        Returns:
            Detected content type
        """
        if not content:
            return ContentType.UNKNOWN
        
        content_lower = content.lower()
        
        # Score each content type based on pattern matches
        scores = {content_type: 0 for content_type in ContentType}
        
        for content_type, patterns in self._content_patterns.items():
            for pattern in patterns:
                matches = len(re.findall(pattern, content_lower, re.IGNORECASE))
                scores[content_type] += matches
        
        # Return the content type with the highest score
        best_type = max(scores.items(), key=lambda x: x[1])
        return best_type[0] if best_type[1] > 0 else ContentType.NARRATIVE
    
    def count_tokens(
        self,
        content: str,
        content_type: Optional[ContentType] = None,
        strategy: CountingStrategy = CountingStrategy.EXACT
    ) -> TokenCount:
        """
        Count tokens in the given content.
        
        Args:
            content: Text content to count tokens for
            content_type: Content type (auto-detected if None)
            strategy: Counting strategy to use
            
        Returns:
            TokenCount result with detailed information
        """
        if not content:
            return TokenCount(
                content="",
                token_count=0,
                content_type=ContentType.UNKNOWN,
                strategy=strategy,
                overhead_applied=1.0,
                metadata={}
            )
        
        # Auto-detect content type if not provided
        if content_type is None:
            content_type = self.detect_content_type(content)
        
        # Get strategy configuration
        config = self._strategy_configs[strategy]
        base_overhead = config["overhead"]
        use_tokenizer = config["use_tokenizer"]
        
        # Apply content type multiplier
        content_multiplier = self._content_type_multipliers[content_type]
        total_overhead = base_overhead * content_multiplier
        
        # Count tokens
        if use_tokenizer and self.tokenizer.is_ready():
            base_count = self.tokenizer.count_tokens(content)
        else:
            # Fallback to character-based estimation
            base_count = max(1, len(content) // 4)
            logger.warning("Using fallback token counting method")
        
        # Apply overhead
        final_count = int(base_count * total_overhead)
        
        # Collect metadata
        metadata = {
            "base_count": base_count,
            "content_length": len(content),
            "content_multiplier": content_multiplier,
            "tokenizer_used": use_tokenizer and self.tokenizer.is_ready(),
            "auto_detected_type": content_type if content_type != ContentType.UNKNOWN else None
        }
        
        return TokenCount(
            content=content,
            token_count=final_count,
            content_type=content_type,
            strategy=strategy,
            overhead_applied=total_overhead,
            metadata=metadata
        )
    
    def count_tokens_batch(
        self,
        contents: List[str],
        content_types: Optional[List[ContentType]] = None,
        strategy: CountingStrategy = CountingStrategy.EXACT
    ) -> List[TokenCount]:
        """
        Count tokens for multiple contents efficiently.
        
        Args:
            contents: List of text contents to count tokens for
            content_types: List of content types (auto-detected if None)
            strategy: Counting strategy to use
            
        Returns:
            List of TokenCount results
        """
        if content_types is None:
            content_types = [None] * len(contents)
        elif len(content_types) != len(contents):
            raise ValueError("content_types length must match contents length")
        
        results = []
        for content, content_type in zip(contents, content_types):
            result = self.count_tokens(content, content_type, strategy)
            results.append(result)
        
        return results
    
    def estimate_tokens_for_generation(
        self,
        prompt: str,
        expected_response_length: int,
        content_type: Optional[ContentType] = None,
        strategy: CountingStrategy = CountingStrategy.CONSERVATIVE
    ) -> Tuple[int, int, int]:
        """
        Estimate total tokens needed for a generation request.
        
        Args:
            prompt: Input prompt text
            expected_response_length: Expected length of response in characters
            content_type: Content type for the response
            strategy: Counting strategy to use
            
        Returns:
            Tuple of (prompt_tokens, estimated_response_tokens, total_tokens)
        """
        # Count prompt tokens
        prompt_result = self.count_tokens(prompt, ContentType.SYSTEM_PROMPT, strategy)
        prompt_tokens = prompt_result.token_count
        
        # Estimate response tokens
        if content_type is None:
            content_type = ContentType.NARRATIVE
        
        # Create a sample text for estimation
        sample_text = "x" * expected_response_length
        response_result = self.count_tokens(sample_text, content_type, strategy)
        response_tokens = response_result.token_count
        
        total_tokens = prompt_tokens + response_tokens
        
        return prompt_tokens, response_tokens, total_tokens
    
    def analyze_content_distribution(self, content: str) -> Dict[ContentType, float]:
        """
        Analyze the distribution of different content types in text.
        
        Args:
            content: Text content to analyze
            
        Returns:
            Dictionary mapping content types to their proportion (0.0-1.0)
        """
        if not content:
            return {ContentType.UNKNOWN: 1.0}
        
        # Split content into sentences for analysis
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return {ContentType.UNKNOWN: 1.0}
        
        # Classify each sentence
        type_counts = {content_type: 0 for content_type in ContentType}
        
        for sentence in sentences:
            detected_type = self.detect_content_type(sentence)
            type_counts[detected_type] += 1
        
        # Convert to proportions
        total_sentences = len(sentences)
        proportions = {
            content_type: count / total_sentences
            for content_type, count in type_counts.items()
            if count > 0
        }
        
        return proportions
    
    def get_token_efficiency_stats(self, contents: List[str]) -> Dict[str, Any]:
        """
        Get efficiency statistics for a batch of contents.
        
        Args:
            contents: List of text contents to analyze
            
        Returns:
            Dictionary with efficiency statistics
        """
        if not contents:
            return {}
        
        results = self.count_tokens_batch(contents)
        
        token_counts = [r.token_count for r in results]
        char_counts = [len(r.content) for r in results]
        
        # Calculate statistics
        total_tokens = sum(token_counts)
        total_chars = sum(char_counts)
        avg_tokens_per_char = total_tokens / total_chars if total_chars > 0 else 0
        
        # Content type distribution
        type_counts = {}
        for result in results:
            content_type = result.content_type
            type_counts[content_type] = type_counts.get(content_type, 0) + 1
        
        type_distribution = {
            content_type.value: count / len(results)
            for content_type, count in type_counts.items()
        }
        
        return {
            "total_contents": len(contents),
            "total_tokens": total_tokens,
            "total_characters": total_chars,
            "avg_tokens_per_content": total_tokens / len(contents),
            "avg_chars_per_content": total_chars / len(contents),
            "avg_tokens_per_char": avg_tokens_per_char,
            "content_type_distribution": type_distribution,
            "tokenizer_ready": self.tokenizer.is_ready()
        }
    
    def validate_token_budget(
        self,
        contents: List[str],
        budget: int,
        strategy: CountingStrategy = CountingStrategy.CONSERVATIVE
    ) -> Dict[str, Any]:
        """
        Validate if contents fit within a token budget.
        
        Args:
            contents: List of text contents to validate
            budget: Maximum token budget
            strategy: Counting strategy to use
            
        Returns:
            Dictionary with validation results
        """
        results = self.count_tokens_batch(contents, strategy=strategy)
        total_tokens = sum(r.token_count for r in results)
        
        fits_budget = total_tokens <= budget
        utilization = total_tokens / budget if budget > 0 else float('inf')
        
        return {
            "fits_budget": fits_budget,
            "total_tokens": total_tokens,
            "budget": budget,
            "utilization": utilization,
            "remaining_tokens": max(0, budget - total_tokens),
            "overflow_tokens": max(0, total_tokens - budget),
            "content_count": len(contents),
            "strategy_used": strategy.value
        }
