"""
Unit Tests for Context Management Configuration

Tests the Pydantic Settings configuration for context management,
including validation, defaults, and error handling.
"""

import pytest
import os
from unittest.mock import patch
from pydantic import ValidationError

from app.core.config import Settings


class TestContextManagementConfig:
    """Test context management configuration settings."""

    def test_default_context_config_values(self):
        """Test that default context configuration values are correct."""
        settings = Settings()

        # Test token limits
        assert settings.CONTEXT_MAX_TOKENS == 32000
        assert settings.CONTEXT_BUFFER_TOKENS == 2000
        
    
    def test_context_max_tokens_validation(self):
        """Test CONTEXT_MAX_TOKENS validation."""
        # Test valid values
        with patch.dict(os.environ, {
            'CONTEXT_MAX_TOKENS': '50000',
            'CONTEXT_BUFFER_TOKENS': '2000'
        }):
            settings = Settings()
            assert settings.CONTEXT_MAX_TOKENS == 50000

        # Test minimum boundary
        with patch.dict(os.environ, {
            'CONTEXT_MAX_TOKENS': '35000',
            'CONTEXT_BUFFER_TOKENS': '2000'
        }):
            settings = Settings()
            assert settings.CONTEXT_MAX_TOKENS == 35000

        # Test maximum boundary
        with patch.dict(os.environ, {
            'CONTEXT_MAX_TOKENS': '100000',
            'CONTEXT_BUFFER_TOKENS': '2000'
        }):
            settings = Settings()
            assert settings.CONTEXT_MAX_TOKENS == 100000

        # Test below minimum
        with patch.dict(os.environ, {'CONTEXT_MAX_TOKENS': '500'}):
            with pytest.raises(ValidationError):
                Settings()

        # Test above maximum
        with patch.dict(os.environ, {'CONTEXT_MAX_TOKENS': '200000'}):
            with pytest.raises(ValidationError):
                Settings()
    
    def test_context_buffer_tokens_validation(self):
        """Test CONTEXT_BUFFER_TOKENS validation."""
        # Test valid values
        with patch.dict(os.environ, {
            'CONTEXT_MAX_TOKENS': '35000',
            'CONTEXT_BUFFER_TOKENS': '3000'
        }):
            settings = Settings()
            assert settings.CONTEXT_BUFFER_TOKENS == 3000

        # Test minimum boundary
        with patch.dict(os.environ, {
            'CONTEXT_MAX_TOKENS': '35000',
            'CONTEXT_BUFFER_TOKENS': '100'
        }):
            settings = Settings()
            assert settings.CONTEXT_BUFFER_TOKENS == 100

        # Test maximum boundary
        with patch.dict(os.environ, {
            'CONTEXT_MAX_TOKENS': '50000',
            'CONTEXT_BUFFER_TOKENS': '10000'
        }):
            settings = Settings()
            assert settings.CONTEXT_BUFFER_TOKENS == 10000

        # Test below minimum
        with patch.dict(os.environ, {'CONTEXT_BUFFER_TOKENS': '50'}):
            with pytest.raises(ValidationError):
                Settings()

        # Test above maximum
        with patch.dict(os.environ, {'CONTEXT_BUFFER_TOKENS': '15000'}):
            with pytest.raises(ValidationError):
                Settings()
    
    def test_configuration_from_env_file(self):
        """Test loading configuration from environment variables."""
        env_vars = {
            'CONTEXT_MAX_TOKENS': '16000',
            'CONTEXT_BUFFER_TOKENS': '1000'
        }

        with patch.dict(os.environ, env_vars):
            settings = Settings()

            assert settings.CONTEXT_MAX_TOKENS == 16000
            assert settings.CONTEXT_BUFFER_TOKENS == 1000
    
    def test_configuration_descriptions(self):
        """Test that configuration fields have proper descriptions."""
        # Get field info from the model class (not instance)
        fields = Settings.model_fields

        # Test that key fields have descriptions
        assert hasattr(fields['CONTEXT_MAX_TOKENS'], 'description')
        assert hasattr(fields['CONTEXT_BUFFER_TOKENS'], 'description')

        # Test specific descriptions
        assert "Maximum context window size" in fields['CONTEXT_MAX_TOKENS'].description
        assert "Reserved tokens for generation buffer" in fields['CONTEXT_BUFFER_TOKENS'].description
