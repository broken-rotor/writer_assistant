"""
Llama Tokenizer Utility

Provides tokenization functionality using llama-cpp-python for accurate
token counting and text processing in the Writer Assistant system.
"""

import logging
import threading
from typing import List, Optional, Union, Dict, Any
from pathlib import Path

try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    Llama = None

logger = logging.getLogger(__name__)


class LlamaTokenizer:
    """
    Thread-safe tokenizer using llama-cpp-python for accurate token counting.

    This class provides tokenization services for the Writer Assistant system,
    ensuring consistent token counting across all components.
    """

    _instance = None
    _lock = threading.Lock()

    def __init__(self, model_path: Optional[str] = None, **kwargs):
        """
        Initialize the Llama tokenizer.

        Args:
            model_path: Path to the GGUF model file. If None, will be loaded lazily.
            **kwargs: Additional arguments for Llama initialization
        """
        self.model_path = model_path
        self.model_kwargs = kwargs
        self._model: Optional[Llama] = None
        self._model_lock = threading.Lock()

        if not LLAMA_CPP_AVAILABLE:
            logger.warning("llama-cpp-python not available. Tokenization will use fallback methods.")

    @classmethod
    def get_instance(cls, model_path: Optional[str] = None, **kwargs) -> 'LlamaTokenizer':
        """
        Get singleton instance of LlamaTokenizer.

        Args:
            model_path: Path to the GGUF model file
            **kwargs: Additional arguments for Llama initialization

        Returns:
            LlamaTokenizer instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(model_path, **kwargs)
        return cls._instance

    def _ensure_model_loaded(self) -> bool:
        """
        Ensure the model is loaded and ready for tokenization.

        Returns:
            True if model is loaded successfully, False otherwise
        """
        if not LLAMA_CPP_AVAILABLE:
            return False

        if self._model is not None:
            return True

        with self._model_lock:
            if self._model is not None:
                return True

            if self.model_path is None:
                logger.error("No model path provided for tokenization")
                return False

            try:
                # Initialize with minimal parameters for tokenization only
                self._model = Llama(
                    model_path=self.model_path,
                    n_ctx=512,  # Minimal context for tokenization
                    n_gpu_layers=0,  # CPU only for tokenization
                    verbose=False,
                    **self.model_kwargs
                )
                logger.info(f"Loaded tokenizer model from {self.model_path}")
                return True
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
            return self._fallback_encode(text)

        try:
            # Use the model's tokenizer to encode text
            tokens = self._model.tokenize(text.encode('utf-8'))
            return tokens
        except Exception as e:
            logger.error(f"Error encoding text: {e}")
            return self._fallback_encode(text)

    def decode(self, tokens: List[int]) -> str:
        """
        Decode token IDs to text.

        Args:
            tokens: List of token IDs

        Returns:
            Decoded text
        """
        if not self._ensure_model_loaded():
            return self._fallback_decode(tokens)

        try:
            # Use the model's tokenizer to decode tokens
            text_bytes = self._model.detokenize(tokens)
            return text_bytes.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Error decoding tokens: {e}")
            return self._fallback_decode(tokens)

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

    def estimate_tokens(self, text: str, overhead_factor: float = 1.1) -> int:
        """
        Estimate token count with overhead factor for safety margins.

        Args:
            text: Text to estimate tokens for
            overhead_factor: Multiplier for safety margin (default 1.1 = 10% overhead)

        Returns:
            Estimated token count with overhead
        """
        base_count = self.count_tokens(text)
        return int(base_count * overhead_factor)

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

    def _fallback_encode(self, text: str) -> List[int]:
        """
        Fallback encoding method when llama-cpp-python is not available.
        Uses a simple character-based approximation.

        Args:
            text: Text to encode

        Returns:
            Approximate token IDs
        """
        # Simple approximation: ~4 characters per token for English text
        # This is a rough estimate and should not be used for production
        chars_per_token = 4
        estimated_tokens = max(1, len(text) // chars_per_token)
        return list(range(estimated_tokens))

    def _fallback_decode(self, tokens: List[int]) -> str:
        """
        Fallback decoding method when llama-cpp-python is not available.

        Args:
            tokens: Token IDs to decode

        Returns:
            Placeholder text
        """
        return f"[{len(tokens)} tokens]"

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model.

        Returns:
            Dictionary containing model information
        """
        info = {
            "model_path": self.model_path,
            "model_loaded": self._model is not None,
            "llama_cpp_available": LLAMA_CPP_AVAILABLE
        }

        if self._model is not None:
            try:
                # Get model metadata if available
                info.update({
                    "vocab_size": self._model.n_vocab(),
                    "context_size": self._model.n_ctx(),
                })
            except Exception as e:
                logger.debug(f"Could not get model metadata: {e}")

        return info

    def is_ready(self) -> bool:
        """
        Check if the tokenizer is ready for use.

        Returns:
            True if tokenizer is ready, False otherwise
        """
        return LLAMA_CPP_AVAILABLE and self._ensure_model_loaded()
