"""
Tests for LLM Inference module.
Note: These tests don't require an actual model file - they test configuration and error handling.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from app.services.llm_inference import (
    LLMInferenceConfig,
    LLMInference,
    initialize_llm,
    get_llm,
    LLAMA_CPP_AVAILABLE
)
from app.core.config import Settings


class TestLLMInferenceConfig:
    """Test LLM configuration"""

    def test_config_defaults(self):
        """Test default configuration values"""
        config = LLMInferenceConfig(model_path="/path/to/model.gguf")

        assert config.model_path == "/path/to/model.gguf"
        assert config.n_ctx == 4096
        assert config.n_gpu_layers == -1
        assert config.n_threads is None
        assert config.temperature == 0.7
        assert config.top_p == 0.95
        assert config.top_k == 40
        assert config.max_tokens == 2048
        assert config.repeat_penalty == 1.1
        assert config.verbose is False
        assert config.verbose_generation is False

    def test_config_custom_values(self):
        """Test custom configuration values"""
        config = LLMInferenceConfig(
            model_path="/custom/path.gguf",
            n_ctx=8192,
            n_gpu_layers=32,
            n_threads=8,
            temperature=0.9,
            top_p=0.9,
            top_k=50,
            max_tokens=1024,
            repeat_penalty=1.2,
            verbose=True,
            verbose_generation=True
        )

        assert config.model_path == "/custom/path.gguf"
        assert config.n_ctx == 8192
        assert config.n_gpu_layers == 32
        assert config.n_threads == 8
        assert config.temperature == 0.9
        assert config.top_p == 0.9
        assert config.top_k == 50
        assert config.max_tokens == 1024
        assert config.repeat_penalty == 1.2
        assert config.verbose is True
        assert config.verbose_generation is True

    def test_config_from_settings(self):
        """Test creating config from Settings object"""
        mock_settings = Mock(spec=Settings)
        mock_settings.MODEL_PATH = '/test/model.gguf'
        mock_settings.LLM_N_CTX = 2048
        mock_settings.LLM_N_GPU_LAYERS = 0
        mock_settings.LLM_N_THREADS = None
        mock_settings.LLM_TEMPERATURE = 0.8
        mock_settings.LLM_TOP_P = 0.95
        mock_settings.LLM_TOP_K = 40
        mock_settings.LLM_MAX_TOKENS = 2048
        mock_settings.LLM_REPEAT_PENALTY = 1.1
        mock_settings.LLM_VERBOSE = False
        mock_settings.LLM_VERBOSE_GENERATION = False

        config = LLMInferenceConfig.from_settings(mock_settings)

        assert config is not None
        assert config.model_path == "/test/model.gguf"
        assert config.n_ctx == 2048
        assert config.n_gpu_layers == 0
        assert config.temperature == 0.8
        assert config.top_p == 0.95
        assert config.max_tokens == 2048

    def test_config_from_settings_minimal(self):
        """Test config from settings with only MODEL_PATH"""
        mock_settings = Mock(spec=Settings)
        mock_settings.MODEL_PATH = '/test/model.gguf'
        mock_settings.LLM_N_CTX = 4096
        mock_settings.LLM_N_GPU_LAYERS = -1
        mock_settings.LLM_N_THREADS = None
        mock_settings.LLM_TEMPERATURE = 0.7
        mock_settings.LLM_TOP_P = 0.95
        mock_settings.LLM_TOP_K = 40
        mock_settings.LLM_MAX_TOKENS = 2048
        mock_settings.LLM_REPEAT_PENALTY = 1.1
        mock_settings.LLM_VERBOSE = False
        mock_settings.LLM_VERBOSE_GENERATION = False

        config = LLMInferenceConfig.from_settings(mock_settings)

        assert config is not None
        assert config.model_path == "/test/model.gguf"
        # All other values should be defaults from settings
        assert config.n_ctx == 4096
        assert config.temperature == 0.7

    def test_config_from_settings_no_model_path(self):
        """Test config from settings returns None when MODEL_PATH not set"""
        mock_settings = Mock(spec=Settings)
        mock_settings.MODEL_PATH = None

        config = LLMInferenceConfig.from_settings(mock_settings)

        assert config is None

    def test_config_from_settings_with_verbose(self):
        """Test LLM_VERBOSE from settings"""
        mock_settings = Mock(spec=Settings)
        mock_settings.MODEL_PATH = '/test/model.gguf'
        mock_settings.LLM_N_CTX = 4096
        mock_settings.LLM_N_GPU_LAYERS = -1
        mock_settings.LLM_N_THREADS = None
        mock_settings.LLM_TEMPERATURE = 0.7
        mock_settings.LLM_TOP_P = 0.95
        mock_settings.LLM_TOP_K = 40
        mock_settings.LLM_MAX_TOKENS = 2048
        mock_settings.LLM_REPEAT_PENALTY = 1.1
        mock_settings.LLM_VERBOSE = True
        mock_settings.LLM_VERBOSE_GENERATION = False

        config = LLMInferenceConfig.from_settings(mock_settings)

        assert config.verbose is True

    def test_config_from_settings_with_verbose_generation(self):
        """Test LLM_VERBOSE_GENERATION from settings"""
        mock_settings = Mock(spec=Settings)
        mock_settings.MODEL_PATH = '/test/model.gguf'
        mock_settings.LLM_N_CTX = 4096
        mock_settings.LLM_N_GPU_LAYERS = -1
        mock_settings.LLM_N_THREADS = None
        mock_settings.LLM_TEMPERATURE = 0.7
        mock_settings.LLM_TOP_P = 0.95
        mock_settings.LLM_TOP_K = 40
        mock_settings.LLM_MAX_TOKENS = 2048
        mock_settings.LLM_REPEAT_PENALTY = 1.1
        mock_settings.LLM_VERBOSE = False
        mock_settings.LLM_VERBOSE_GENERATION = True

        config = LLMInferenceConfig.from_settings(mock_settings)

        assert config.verbose_generation is True


class TestLLMInferenceInitialization:
    """Test LLM inference initialization and error handling"""

    def test_file_not_found_error(self):
        """Test that FileNotFoundError is raised for non-existent model"""
        if not LLAMA_CPP_AVAILABLE:
            pytest.skip("Requires llama-cpp-python to be installed")

        config = LLMInferenceConfig(model_path="/nonexistent/model.gguf")

        with pytest.raises(FileNotFoundError, match="Model file not found"):
            LLMInference(config)

    @patch('app.services.llm_inference.Llama')
    @patch('pathlib.Path.exists')
    def test_successful_initialization(self, mock_exists, mock_llama):
        """Test successful model initialization with mocked llama.cpp"""
        if not LLAMA_CPP_AVAILABLE:
            pytest.skip("Requires llama-cpp-python to be installed")

        mock_exists.return_value = True
        mock_model = MagicMock()
        mock_llama.return_value = mock_model

        config = LLMInferenceConfig(
            model_path="/test/model.gguf",
            n_ctx=2048,
            n_gpu_layers=0
        )

        llm = LLMInference(config)

        # Verify Llama was called with correct parameters
        mock_llama.assert_called_once()
        call_kwargs = mock_llama.call_args[1]
        assert 'model_path' in call_kwargs
        assert call_kwargs['n_ctx'] == 2048
        assert call_kwargs['n_gpu_layers'] == 0

        assert llm.model is not None


class TestLLMInferenceGeneration:
    """Test text generation functionality"""

    @patch('app.services.llm_inference.Llama')
    @patch('pathlib.Path.exists')
    def test_generate_basic(self, mock_exists, mock_llama):
        """Test basic text generation"""
        if not LLAMA_CPP_AVAILABLE:
            pytest.skip("Requires llama-cpp-python to be installed")

        mock_exists.return_value = True
        mock_model = MagicMock()
        mock_model.return_value = {
            'choices': [{'text': 'Generated response'}]
        }
        mock_llama.return_value = mock_model

        config = LLMInferenceConfig(model_path="/test/model.gguf")
        llm = LLMInference(config)

        response = llm.generate("Test prompt")

        assert response == "Generated response"
        mock_model.assert_called_once()

    @patch('app.services.llm_inference.Llama')
    @patch('pathlib.Path.exists')
    def test_generate_with_custom_parameters(self, mock_exists, mock_llama):
        """Test generation with custom parameters"""
        if not LLAMA_CPP_AVAILABLE:
            pytest.skip("Requires llama-cpp-python to be installed")

        mock_exists.return_value = True
        mock_model = MagicMock()
        mock_model.return_value = {
            'choices': [{'text': 'Custom response'}]
        }
        mock_llama.return_value = mock_model

        config = LLMInferenceConfig(model_path="/test/model.gguf")
        llm = LLMInference(config)

        response = llm.generate(
            "Test prompt",
            max_tokens=100,
            temperature=0.9,
            top_p=0.8
        )

        assert response == "Custom response"

        # Verify custom parameters were passed
        call_kwargs = mock_model.call_args[1]
        assert call_kwargs['max_tokens'] == 100
        assert call_kwargs['temperature'] == 0.9
        assert call_kwargs['top_p'] == 0.8

    @patch('app.services.llm_inference.Llama')
    @patch('pathlib.Path.exists')
    def test_chat_completion(self, mock_exists, mock_llama):
        """Test chat completion"""
        if not LLAMA_CPP_AVAILABLE:
            pytest.skip("Requires llama-cpp-python to be installed")

        mock_exists.return_value = True
        mock_model = MagicMock()
        mock_model.create_chat_completion.return_value = {
            'choices': [{'message': {'content': 'Chat response'}}]
        }
        mock_llama.return_value = mock_model

        config = LLMInferenceConfig(model_path="/test/model.gguf")
        llm = LLMInference(config)

        messages = [
            {"role": "user", "content": "Hello"}
        ]
        response = llm.chat_completion(messages)

        assert response == "Chat response"
        mock_model.create_chat_completion.assert_called_once()


class TestSingletonPattern:
    """Test global singleton instance management"""

    def test_initialize_llm(self):
        """Test initializing global LLM instance"""
        with patch('app.services.llm_inference.LLMInference') as mock_llm_class:
            mock_instance = MagicMock()
            mock_llm_class.return_value = mock_instance

            config = LLMInferenceConfig(model_path="/test/model.gguf")
            instance = initialize_llm(config)

            assert instance == mock_instance

    def test_get_llm_when_not_initialized(self):
        """Test getting LLM when not initialized returns None"""
        # Clear any existing instance
        import app.services.llm_inference as llm_module
        llm_module._llm_instance = None

        instance = get_llm()
        assert instance is None

    def test_get_llm_after_initialization(self):
        """Test getting LLM after initialization"""
        with patch('app.services.llm_inference.LLMInference') as mock_llm_class:
            mock_instance = MagicMock()
            mock_llm_class.return_value = mock_instance

            config = LLMInferenceConfig(model_path="/test/model.gguf")
            initialize_llm(config)

            instance = get_llm()
            assert instance == mock_instance


class TestErrorHandling:
    """Test error handling in various scenarios"""

    @patch('app.services.llm_inference.Llama')
    @patch('pathlib.Path.exists')
    def test_generation_error_handling(self, mock_exists, mock_llama):
        """Test error handling during generation"""
        if not LLAMA_CPP_AVAILABLE:
            pytest.skip("Requires llama-cpp-python to be installed")

        mock_exists.return_value = True
        mock_model = MagicMock()
        mock_model.side_effect = Exception("Generation error")
        mock_llama.return_value = mock_model

        config = LLMInferenceConfig(model_path="/test/model.gguf")
        llm = LLMInference(config)

        with pytest.raises(RuntimeError, match="Generation failed"):
            llm.generate("Test prompt")

    @patch('app.services.llm_inference.Llama')
    @patch('pathlib.Path.exists')
    def test_chat_completion_error_handling(self, mock_exists, mock_llama):
        """Test error handling during chat completion"""
        if not LLAMA_CPP_AVAILABLE:
            pytest.skip("Requires llama-cpp-python to be installed")

        mock_exists.return_value = True
        mock_model = MagicMock()
        mock_model.create_chat_completion.side_effect = Exception("Chat error")
        mock_llama.return_value = mock_model

        config = LLMInferenceConfig(model_path="/test/model.gguf")
        llm = LLMInference(config)

        messages = [{"role": "user", "content": "Hello"}]

        with pytest.raises(RuntimeError, match="Chat completion failed"):
            llm.chat_completion(messages)
