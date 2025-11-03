"""
Local LLM Inference using llama.cpp
Provides a simple interface for generating text with local models.
"""
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    Llama = None

logger = logging.getLogger(__name__)


class LLMInferenceConfig:
    """Configuration for LLM inference"""

    def __init__(
        self,
        model_path: str,
        n_ctx: int = 4096,
        n_gpu_layers: int = -1,
        n_threads: Optional[int] = None,
        temperature: float = 0.7,
        top_p: float = 0.95,
        top_k: int = 40,
        max_tokens: int = 2048,
        repeat_penalty: float = 1.1,
        verbose: bool = False,
        verbose_generation: bool = False
    ):
        """
        Initialize LLM inference configuration.

        Args:
            model_path: Path to the GGUF model file
            n_ctx: Context window size (default: 4096)
            n_gpu_layers: Number of layers to offload to GPU (-1 for all, 0 for CPU only)
            n_threads: Number of CPU threads to use (None for auto)
            temperature: Sampling temperature (0.0-2.0, lower = more deterministic)
            top_p: Nucleus sampling threshold
            top_k: Top-k sampling parameter
            max_tokens: Maximum tokens to generate
            repeat_penalty: Penalty for repeating tokens
            verbose: Enable verbose logging
            verbose_generation: Enable verbose logging of prompts, messages, and outputs
        """
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self.n_threads = n_threads
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.max_tokens = max_tokens
        self.repeat_penalty = repeat_penalty
        self.verbose = verbose
        self.verbose_generation = verbose_generation

    @classmethod
    def from_settings(cls, settings) -> Optional["LLMInferenceConfig"]:
        """
        Create config from Settings object.

        Args:
            settings: Settings object from app.core.config

        Returns:
            LLMInferenceConfig if MODEL_PATH is set, None otherwise
        """
        if not settings.MODEL_PATH:
            return None

        return cls(
            model_path=settings.MODEL_PATH,
            n_ctx=settings.LLM_N_CTX,
            n_gpu_layers=settings.LLM_N_GPU_LAYERS,
            n_threads=settings.LLM_N_THREADS,
            temperature=settings.LLM_TEMPERATURE,
            top_p=settings.LLM_TOP_P,
            top_k=settings.LLM_TOP_K,
            max_tokens=settings.LLM_MAX_TOKENS,
            repeat_penalty=settings.LLM_REPEAT_PENALTY,
            verbose=settings.LLM_VERBOSE,
            verbose_generation=settings.LLM_VERBOSE_GENERATION
        )


class LLMInference:
    """
    Local LLM inference engine using llama.cpp.
    Provides text generation capabilities with local models.
    """

    def __init__(self, config: LLMInferenceConfig):
        """
        Initialize the LLM inference engine.

        Args:
            config: LLMInferenceConfig with model settings

        Raises:
            ImportError: If llama-cpp-python is not installed
            FileNotFoundError: If model file doesn't exist
            RuntimeError: If model fails to load
        """
        if not LLAMA_CPP_AVAILABLE:
            raise ImportError(
                "llama-cpp-python is not installed. "
                "Install it with: pip install llama-cpp-python"
            )

        self.config = config
        self.model: Optional[Llama] = None
        self._load_model()

    def _load_model(self):
        """Load the model from disk"""
        model_path = Path(self.config.model_path)

        if not model_path.exists():
            raise FileNotFoundError(
                f"Model file not found: {self.config.model_path}\n"
                f"Please provide a valid path to a GGUF model file."
            )

        logger.info(f"Loading model from {self.config.model_path}")
        logger.info(f"Context size: {self.config.n_ctx}, GPU layers: {self.config.n_gpu_layers}")

        try:
            self.model = Llama(
                model_path=str(model_path),
                n_ctx=self.config.n_ctx,
                n_gpu_layers=self.config.n_gpu_layers,
                n_threads=self.config.n_threads,
                verbose=self.config.verbose
            )
            logger.info("Model loaded successfully")
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {str(e)}")

    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        repeat_penalty: Optional[float] = None,
        stop: Optional[List[str]] = None,
        stream: bool = False
    ) -> str:
        """
        Generate text from a prompt.

        Args:
            prompt: Input text prompt
            max_tokens: Maximum tokens to generate (overrides config)
            temperature: Sampling temperature (overrides config)
            top_p: Nucleus sampling (overrides config)
            top_k: Top-k sampling (overrides config)
            repeat_penalty: Repetition penalty (overrides config)
            stop: List of stop sequences
            stream: Whether to stream the response (not implemented for sync)

        Returns:
            Generated text string

        Raises:
            RuntimeError: If model is not loaded
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call _load_model() first.")

        # Use provided values or fall back to config
        generation_params = {
            "max_tokens": max_tokens or self.config.max_tokens,
            "temperature": temperature if temperature is not None else self.config.temperature,
            "top_p": top_p if top_p is not None else self.config.top_p,
            "top_k": top_k if top_k is not None else self.config.top_k,
            "repeat_penalty": repeat_penalty if repeat_penalty is not None else self.config.repeat_penalty,
            "stop": stop or [],
        }

        logger.debug(f"Generating with params: {generation_params}")

        # Log prompt if verbose generation is enabled
        if self.config.verbose_generation:
            logger.info(f"[LLM Prompt]\n{prompt}")

        try:
            response = self.model(
                prompt,
                **generation_params
            )

            # Extract text from response
            if isinstance(response, dict) and 'choices' in response:
                generated_text = response['choices'][0]['text']
            else:
                generated_text = str(response)

            generated_text = generated_text.strip()

            # Log output if verbose generation is enabled
            if self.config.verbose_generation:
                logger.info(f"[LLM Output]\n{generated_text}")

            return generated_text

        except Exception as e:
            logger.error(f"Error during generation: {str(e)}")
            raise RuntimeError(f"Generation failed: {str(e)}")

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        repeat_penalty: Optional[float] = None,
        stop: Optional[List[str]] = None
    ) -> str:
        """
        Generate a chat completion from a list of messages.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
                     Example: [{"role": "user", "content": "Hello"}]
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling
            top_k: Top-k sampling
            repeat_penalty: Repetition penalty
            stop: List of stop sequences

        Returns:
            Generated response text
        """
        if self.model is None:
            raise RuntimeError("Model not loaded.")

        generation_params = {
            "max_tokens": max_tokens or self.config.max_tokens,
            "temperature": temperature if temperature is not None else self.config.temperature,
            "top_p": top_p if top_p is not None else self.config.top_p,
            "top_k": top_k if top_k is not None else self.config.top_k,
            "repeat_penalty": repeat_penalty if repeat_penalty is not None else self.config.repeat_penalty,
            "stop": stop or [],
        }

        # Log messages if verbose generation is enabled
        if self.config.verbose_generation:
            debug_messages = ''
            for msg in messages:
                for k, v in msg.items():
                    debug_messages += f"\n**{k}**: {v}"
            logger.info(f"[LLM Messages]{debug_messages}")

        try:
            response = self.model.create_chat_completion(
                messages=messages,
                **generation_params
            )

            # Extract message content
            if isinstance(response, dict) and 'choices' in response:
                generated_text = response['choices'][0]['message']['content']
            else:
                generated_text = str(response)

            generated_text = generated_text.strip()

            # Log output if verbose generation is enabled
            if self.config.verbose_generation:
                logger.info(f"[LLM Output]\n{generated_text}")

            return generated_text

        except Exception as e:
            logger.error(f"Error during chat completion: {str(e)}")
            raise RuntimeError(f"Chat completion failed: {str(e)}")

    def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        repeat_penalty: Optional[float] = None,
        stop: Optional[List[str]] = None
    ):
        """
        Generate a streaming chat completion from a list of messages.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling
            top_k: Top-k sampling
            repeat_penalty: Repetition penalty
            stop: List of stop sequences

        Yields:
            Token strings as they are generated
        """
        if self.model is None:
            raise RuntimeError("Model not loaded.")

        generation_params = {
            "max_tokens": max_tokens or self.config.max_tokens,
            "temperature": temperature if temperature is not None else self.config.temperature,
            "top_p": top_p if top_p is not None else self.config.top_p,
            "top_k": top_k if top_k is not None else self.config.top_k,
            "repeat_penalty": repeat_penalty if repeat_penalty is not None else self.config.repeat_penalty,
            "stop": stop or [],
            "stream": True
        }

        # Log messages if verbose generation is enabled
        if self.config.verbose_generation:
            debug_messages = ''
            for msg in messages:
                for k, v in msg.items():
                    debug_messages += f"\n{k}: {v}"
            logger.info(f"[LLM Messages (streaming)]{debug_messages}")

        try:
            stream = self.model.create_chat_completion(
                messages=messages,
                **generation_params
            )

            # Accumulate output for logging if verbose generation is enabled
            accumulated_output = [] if self.config.verbose_generation else None

            for chunk in stream:
                if 'choices' in chunk and len(chunk['choices']) > 0:
                    delta = chunk['choices'][0].get('delta', {})
                    if 'content' in delta:
                        content = delta['content']
                        if accumulated_output is not None:
                            accumulated_output.append(content)
                        yield content

            # Log complete output if verbose generation is enabled
            if self.config.verbose_generation and accumulated_output:
                complete_output = ''.join(accumulated_output)
                logger.info(f"[LLM Output (streaming)]\n{complete_output}")

        except Exception as e:
            logger.error(f"Error during streaming chat completion: {str(e)}")
            raise RuntimeError(f"Streaming chat completion failed: {str(e)}")

    def get_embedding(self, text: str) -> List[float]:
        """
        Get embeddings for text (if model supports it).

        Args:
            text: Input text

        Returns:
            List of embedding values
        """
        if self.model is None:
            raise RuntimeError("Model not loaded.")

        try:
            embedding = self.model.embed(text)
            return embedding
        except Exception as e:
            logger.error(f"Error getting embedding: {str(e)}")
            raise RuntimeError(f"Embedding generation failed: {str(e)}")

    def __del__(self):
        """Cleanup when object is destroyed"""
        if hasattr(self, 'model') and self.model is not None:
            logger.info("Unloading model")
            del self.model


# Global instance for singleton pattern
_llm_instance: Optional[LLMInference] = None


def initialize_llm(config: LLMInferenceConfig) -> LLMInference:
    """
    Initialize the global LLM instance.

    Args:
        config: LLMInferenceConfig with model settings

    Returns:
        Initialized LLMInference instance
    """
    global _llm_instance

    if _llm_instance is not None:
        logger.warning("LLM already initialized. Replacing existing instance.")
        del _llm_instance

    _llm_instance = LLMInference(config)
    return _llm_instance


def get_llm() -> Optional[LLMInference]:
    """
    Get the global LLM instance.

    Returns:
        LLMInference instance if initialized, None otherwise
    """
    return _llm_instance
