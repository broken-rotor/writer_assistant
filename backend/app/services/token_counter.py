"""
Token Counter for Writer Assistant

Provides accurate token counting for different content types using Llama tokenization.
Supports various counting strategies and content type detection for the multi-agent
storytelling system.
"""

import logging
from typing import Dict, List, Optional, Any

from ..utils.llama_tokenizer import LlamaTokenizer

logger = logging.getLogger(__name__)


class TokenCounter:
    """
    Advanced token counter with content type detection and multiple counting strategies.

    This class provides accurate token counting for the Writer Assistant's multi-agent
    storytelling system, with support for different content types and counting strategies.
    """

    def __init__(self, tokenizer: Optional[LlamaTokenizer] = None):
        """
        Initialize the TokenCounter.

        Args:
            tokenizer: LlamaTokenizer instance. If None, will create or get singleton.
        """
        if tokenizer is not None:
            self.tokenizer = tokenizer
        else:
            self.tokenizer = LlamaTokenizer.get_instance()

    def count_tokens(self, content: str) -> int:
        if not content:
            return 0

        if not self.tokenizer.is_ready():
            raise ValueError("Tokenizer not available")

        return self.tokenizer.count_tokens(content)

    def count_tokens_batch(self, contents: List[str]) -> List[int]:
        return [self.count_tokens(content) for content in contents]

    def validate_token_budget(self, contents: List[str], budget: int) -> Dict[str, Any]:
        """
        Validate if contents fit within a token budget.

        Args:
            contents: List of text contents to validate
            budget: Maximum token budget
            strategy: Counting strategy to use (for compatibility, currently ignored)

        Returns:
            Dictionary with validation results
        """
        results = self.count_tokens_batch(contents)
        total_tokens = sum(results)

        fits_budget = total_tokens <= budget
        utilization = total_tokens / budget if budget > 0 else float('inf')

        return {
            "fits_budget": fits_budget,
            "total_tokens": total_tokens,
            "budget": budget,
            "utilization": utilization,
            "remaining_tokens": max(0, budget - total_tokens),
            "overflow_tokens": max(0, total_tokens - budget),
            "content_count": len(contents)
        }
