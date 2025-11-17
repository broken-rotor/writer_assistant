"""
Llama Tokenizer Utility

Provides tokenization functionality using llama-cpp-python for accurate
token counting and text processing in the Writer Assistant system.
"""

import logging
from typing import List, Optional, Union, Dict, Any
from app.services.llm_inference import get_llm
from pathlib import Path

logger = logging.getLogger(__name__)


class LlamaTokenizer:
    _instance = None

    def __init__(self):
        self._model: Optional[Llama] = None

    @classmethod
    def get_instance(cls) -> 'LlamaTokenizer':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _ensure_model_loaded(self) -> bool:
        """
        Ensure the model is loaded and ready for tokenization.

        Returns:
            True if model is loaded successfully, False otherwise
        """
        if self._model is not None:
            return True

        try:
            # Initialize with minimal parameters for tokenization only
            self._model = get_llm().model
            return self._model is not None
        except Exception as e:
            logger.error(f"Failed to load tokenizer model: {e}")
            return False

    def encode(self, text: str) -> List[int]:
        """
        Encode text to token IDs.

        Args:
            text: Text to encode

        Returns:
            List of token IDs
        """
        if not self._ensure_model_loaded():
            raise ValueError('Model not loaded')

        try:
            # Use the model's tokenizer to encode text
            tokens = self._model.tokenize(text.encode('utf-8'))
            return tokens
        except Exception as e:
            logger.error(f"Error encoding text", e)
            raise ValueError('Model not loaded')

    def decode(self, tokens: List[int]) -> str:
        """
        Decode token IDs to text.

        Args:
            tokens: List of token IDs

        Returns:
            Decoded text
        """
        if not self._ensure_model_loaded():
            raise ValueError('Model not loaded')

        try:
            # Use the model's tokenizer to decode tokens
            text_bytes = self._model.detokenize(tokens)
            return text_bytes.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Error decoding tokens: {e}")
            raise ValueError('Model not loaded')

    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in the given text.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        if not text:
            return 0

        tokens = self.encode(text)
        return len(tokens)

    def count_tokens_batch(self, texts: List[str]) -> List[int]:
        """
        Count tokens for multiple texts efficiently.

        Args:
            texts: List of texts to count tokens for

        Returns:
            List of token counts corresponding to input texts
        """
        return [self.count_tokens(text) for text in texts]

    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to fit within a maximum token count.

        Args:
            text: Text to truncate
            max_tokens: Maximum number of tokens allowed

        Returns:
            Truncated text that fits within token limit
        """
        if not text:
            return text

        tokens = self.encode(text)
        if len(tokens) <= max_tokens:
            return text

        # Truncate tokens and decode back to text
        truncated_tokens = tokens[:max_tokens]
        return self.decode(truncated_tokens)

    def is_ready(self) -> bool:
        """
        Check if the tokenizer is ready for use.

        Returns:
            True if tokenizer is ready, False otherwise
        """
        return self._ensure_model_loaded()
