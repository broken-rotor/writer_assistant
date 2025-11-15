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
        
        # Test layer token allocations
        assert settings.CONTEXT_LAYER_A_TOKENS == 2000
        assert settings.CONTEXT_LAYER_B_TOKENS == 0
        assert settings.CONTEXT_LAYER_C_TOKENS == 13000
        assert settings.CONTEXT_LAYER_D_TOKENS == 5000
        assert settings.CONTEXT_LAYER_E_TOKENS == 10000
        
    def test_layer_tokens_sum_validation(self):
        """Test that layer token allocations don't exceed available tokens."""
        # Test valid token allocations (within limits)
        with patch.dict(os.environ, {
            'CONTEXT_MAX_TOKENS': '32000',
            'CONTEXT_BUFFER_TOKENS': '2000',
            'CONTEXT_LAYER_A_TOKENS': '2000',
            'CONTEXT_LAYER_B_TOKENS': '1000',
            'CONTEXT_LAYER_C_TOKENS': '10000',
            'CONTEXT_LAYER_D_TOKENS': '8000',
            'CONTEXT_LAYER_E_TOKENS': '9000'
        }):
            settings = Settings()
            assert settings.CONTEXT_LAYER_A_TOKENS == 2000
        
        # Test invalid token allocations (exceed available tokens)
        with patch.dict(os.environ, {
            'CONTEXT_MAX_TOKENS': '10000',
            'CONTEXT_BUFFER_TOKENS': '1000',
            'CONTEXT_LAYER_A_TOKENS': '3000',
            'CONTEXT_LAYER_B_TOKENS': '2000',
            'CONTEXT_LAYER_C_TOKENS': '3000',
            'CONTEXT_LAYER_D_TOKENS': '2000',
            'CONTEXT_LAYER_E_TOKENS': '2000'
        }):
            with pytest.raises(ValueError, match="Context layer tokens sum to .* which exceeds available tokens"):
                Settings()
    
    def test_context_max_tokens_validation(self):
        """Test CONTEXT_MAX_TOKENS validation."""
        # Test valid values with compatible layer tokens
        with patch.dict(os.environ, {
            'CONTEXT_MAX_TOKENS': '50000',
            'CONTEXT_BUFFER_TOKENS': '2000'
        }):
            settings = Settings()
            assert settings.CONTEXT_MAX_TOKENS == 50000
        
        # Test minimum boundary with minimal layer tokens
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
        # Test valid values with compatible max tokens
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
    
    def test_layer_token_validation(self):
        """Test individual layer token validation."""
        # Test valid token allocation with adjusted other layers
        with patch.dict(os.environ, {
            'CONTEXT_LAYER_A_TOKENS': '3000',
            'CONTEXT_LAYER_C_TOKENS': '12000',
            'CONTEXT_LAYER_D_TOKENS': '5000',
            'CONTEXT_LAYER_E_TOKENS': '10000'
        }):
            settings = Settings()
            assert settings.CONTEXT_LAYER_A_TOKENS == 3000
        
        # Test minimum boundary
        with patch.dict(os.environ, {
            'CONTEXT_LAYER_A_TOKENS': '100',
            'CONTEXT_LAYER_C_TOKENS': '12900',
            'CONTEXT_LAYER_D_TOKENS': '5000',
            'CONTEXT_LAYER_E_TOKENS': '10000'
        }):
            settings = Settings()
            assert settings.CONTEXT_LAYER_A_TOKENS == 100
        
        # Test maximum boundary
        with patch.dict(os.environ, {
            'CONTEXT_LAYER_A_TOKENS': '10000',
            'CONTEXT_LAYER_C_TOKENS': '5000',
            'CONTEXT_LAYER_D_TOKENS': '5000',
            'CONTEXT_LAYER_E_TOKENS': '10000'
        }):
            settings = Settings()
            assert settings.CONTEXT_LAYER_A_TOKENS == 10000
        
        # Test below minimum
        with patch.dict(os.environ, {'CONTEXT_LAYER_A_TOKENS': '50'}):
            with pytest.raises(ValidationError):
                Settings()
        
        # Test above maximum
        with patch.dict(os.environ, {'CONTEXT_LAYER_A_TOKENS': '15000'}):
            with pytest.raises(ValidationError):
                Settings()
    
    def test_configuration_from_env_file(self):
        """Test loading configuration from environment variables."""
        env_vars = {
            'CONTEXT_MAX_TOKENS': '16000',
            'CONTEXT_BUFFER_TOKENS': '1000',
            'CONTEXT_LAYER_A_TOKENS': '1500',
            'CONTEXT_LAYER_B_TOKENS': '750',
            'CONTEXT_LAYER_C_TOKENS': '6000',
            'CONTEXT_LAYER_D_TOKENS': '3000',
            'CONTEXT_LAYER_E_TOKENS': '3750',
        }
        
        with patch.dict(os.environ, env_vars):
            settings = Settings()
            
            assert settings.CONTEXT_MAX_TOKENS == 16000
            assert settings.CONTEXT_BUFFER_TOKENS == 1000
            assert settings.CONTEXT_LAYER_A_TOKENS == 1500
            assert settings.CONTEXT_LAYER_B_TOKENS == 750
            assert settings.CONTEXT_LAYER_C_TOKENS == 6000
            assert settings.CONTEXT_LAYER_D_TOKENS == 3000
            assert settings.CONTEXT_LAYER_E_TOKENS == 3750
    
    def test_edge_case_layer_tokens(self):
        """Test edge cases for layer token validation."""
        # Test all minimum values (valid)
        with patch.dict(os.environ, {
            'CONTEXT_MAX_TOKENS': '10000',
            'CONTEXT_BUFFER_TOKENS': '1000',
            'CONTEXT_LAYER_A_TOKENS': '100',
            'CONTEXT_LAYER_B_TOKENS': '0',
            'CONTEXT_LAYER_C_TOKENS': '1000',
            'CONTEXT_LAYER_D_TOKENS': '500',
            'CONTEXT_LAYER_E_TOKENS': '1000'
        }):
            settings = Settings()
            total = (settings.CONTEXT_LAYER_A_TOKENS + 
                    settings.CONTEXT_LAYER_B_TOKENS + 
                    settings.CONTEXT_LAYER_C_TOKENS + 
                    settings.CONTEXT_LAYER_D_TOKENS + 
                    settings.CONTEXT_LAYER_E_TOKENS)
            assert total == 2600
            assert total <= settings.CONTEXT_MAX_TOKENS - settings.CONTEXT_BUFFER_TOKENS
        
        # Test sum exactly at limit (valid)
        with patch.dict(os.environ, {
            'CONTEXT_MAX_TOKENS': '10000',
            'CONTEXT_BUFFER_TOKENS': '1000',
            'CONTEXT_LAYER_A_TOKENS': '2000',
            'CONTEXT_LAYER_B_TOKENS': '1000',
            'CONTEXT_LAYER_C_TOKENS': '3000',
            'CONTEXT_LAYER_D_TOKENS': '1500',
            'CONTEXT_LAYER_E_TOKENS': '1500'
        }):
            settings = Settings()
            total = (settings.CONTEXT_LAYER_A_TOKENS + 
                    settings.CONTEXT_LAYER_B_TOKENS + 
                    settings.CONTEXT_LAYER_C_TOKENS + 
                    settings.CONTEXT_LAYER_D_TOKENS + 
                    settings.CONTEXT_LAYER_E_TOKENS)
            assert total == 9000
            assert total == settings.CONTEXT_MAX_TOKENS - settings.CONTEXT_BUFFER_TOKENS
        
        # Test sum slightly over limit (invalid)
        with patch.dict(os.environ, {
            'CONTEXT_MAX_TOKENS': '10000',
            'CONTEXT_BUFFER_TOKENS': '1000',
            'CONTEXT_LAYER_A_TOKENS': '2100',
            'CONTEXT_LAYER_B_TOKENS': '2000',
            'CONTEXT_LAYER_C_TOKENS': '2000',
            'CONTEXT_LAYER_D_TOKENS': '2000',
            'CONTEXT_LAYER_E_TOKENS': '2000'
        }):
            with pytest.raises(ValueError, match="Context layer tokens sum to .* which exceeds available tokens"):
                Settings()
    
    def test_configuration_descriptions(self):
        """Test that configuration fields have proper descriptions."""
        # Get field info from the model class (not instance)
        fields = Settings.model_fields
        
        # Test that key fields have descriptions
        assert hasattr(fields['CONTEXT_MAX_TOKENS'], 'description')
        assert hasattr(fields['CONTEXT_LAYER_A_TOKENS'], 'description')
        
        # Test specific descriptions
        assert "Maximum context window size" in fields['CONTEXT_MAX_TOKENS'].description
        assert "System instructions" in fields['CONTEXT_LAYER_A_TOKENS'].description
