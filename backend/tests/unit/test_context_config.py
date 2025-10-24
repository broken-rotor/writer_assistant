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
        
        # Test performance settings
        assert settings.CONTEXT_SUMMARIZATION_THRESHOLD == 25000
        assert settings.CONTEXT_ASSEMBLY_TIMEOUT == 100
        
        # Test feature toggles
        assert settings.CONTEXT_ENABLE_RAG is True
        assert settings.CONTEXT_ENABLE_MONITORING is True
        assert settings.CONTEXT_ENABLE_CACHING is True
        
        # Test optimization settings
        assert settings.CONTEXT_MIN_PRIORITY_THRESHOLD == 0.1
        assert settings.CONTEXT_OVERFLOW_STRATEGY == "reallocate"
        assert settings.CONTEXT_ALLOCATION_MODE == "dynamic"
    
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
    
    def test_summarization_threshold_validation(self):
        """Test CONTEXT_SUMMARIZATION_THRESHOLD validation."""
        # Test valid values
        with patch.dict(os.environ, {'CONTEXT_SUMMARIZATION_THRESHOLD': '15000'}):
            settings = Settings()
            assert settings.CONTEXT_SUMMARIZATION_THRESHOLD == 15000
        
        # Test minimum boundary
        with patch.dict(os.environ, {'CONTEXT_SUMMARIZATION_THRESHOLD': '1000'}):
            settings = Settings()
            assert settings.CONTEXT_SUMMARIZATION_THRESHOLD == 1000
        
        # Test maximum boundary
        with patch.dict(os.environ, {'CONTEXT_SUMMARIZATION_THRESHOLD': '100000'}):
            settings = Settings()
            assert settings.CONTEXT_SUMMARIZATION_THRESHOLD == 100000
        
        # Test below minimum
        with patch.dict(os.environ, {'CONTEXT_SUMMARIZATION_THRESHOLD': '500'}):
            with pytest.raises(ValidationError):
                Settings()
        
        # Test above maximum
        with patch.dict(os.environ, {'CONTEXT_SUMMARIZATION_THRESHOLD': '150000'}):
            with pytest.raises(ValidationError):
                Settings()
    
    def test_assembly_timeout_validation(self):
        """Test CONTEXT_ASSEMBLY_TIMEOUT validation."""
        # Test valid values
        with patch.dict(os.environ, {'CONTEXT_ASSEMBLY_TIMEOUT': '200'}):
            settings = Settings()
            assert settings.CONTEXT_ASSEMBLY_TIMEOUT == 200
        
        # Test minimum boundary
        with patch.dict(os.environ, {'CONTEXT_ASSEMBLY_TIMEOUT': '10'}):
            settings = Settings()
            assert settings.CONTEXT_ASSEMBLY_TIMEOUT == 10
        
        # Test maximum boundary
        with patch.dict(os.environ, {'CONTEXT_ASSEMBLY_TIMEOUT': '10000'}):
            settings = Settings()
            assert settings.CONTEXT_ASSEMBLY_TIMEOUT == 10000
        
        # Test below minimum
        with patch.dict(os.environ, {'CONTEXT_ASSEMBLY_TIMEOUT': '5'}):
            with pytest.raises(ValidationError):
                Settings()
        
        # Test above maximum
        with patch.dict(os.environ, {'CONTEXT_ASSEMBLY_TIMEOUT': '15000'}):
            with pytest.raises(ValidationError):
                Settings()
    
    def test_priority_threshold_validation(self):
        """Test CONTEXT_MIN_PRIORITY_THRESHOLD validation."""
        # Test valid values
        with patch.dict(os.environ, {'CONTEXT_MIN_PRIORITY_THRESHOLD': '0.5'}):
            settings = Settings()
            assert settings.CONTEXT_MIN_PRIORITY_THRESHOLD == 0.5
        
        # Test minimum boundary
        with patch.dict(os.environ, {'CONTEXT_MIN_PRIORITY_THRESHOLD': '0.0'}):
            settings = Settings()
            assert settings.CONTEXT_MIN_PRIORITY_THRESHOLD == 0.0
        
        # Test maximum boundary
        with patch.dict(os.environ, {'CONTEXT_MIN_PRIORITY_THRESHOLD': '1.0'}):
            settings = Settings()
            assert settings.CONTEXT_MIN_PRIORITY_THRESHOLD == 1.0
        
        # Test below minimum
        with patch.dict(os.environ, {'CONTEXT_MIN_PRIORITY_THRESHOLD': '-0.1'}):
            with pytest.raises(ValidationError):
                Settings()
        
        # Test above maximum
        with patch.dict(os.environ, {'CONTEXT_MIN_PRIORITY_THRESHOLD': '1.5'}):
            with pytest.raises(ValidationError):
                Settings()
    
    def test_boolean_feature_toggles(self):
        """Test boolean feature toggle configuration."""
        # Test RAG toggle
        with patch.dict(os.environ, {'CONTEXT_ENABLE_RAG': 'false'}):
            settings = Settings()
            assert settings.CONTEXT_ENABLE_RAG is False
        
        with patch.dict(os.environ, {'CONTEXT_ENABLE_RAG': 'true'}):
            settings = Settings()
            assert settings.CONTEXT_ENABLE_RAG is True
        
        # Test monitoring toggle
        with patch.dict(os.environ, {'CONTEXT_ENABLE_MONITORING': 'false'}):
            settings = Settings()
            assert settings.CONTEXT_ENABLE_MONITORING is False
        
        # Test caching toggle
        with patch.dict(os.environ, {'CONTEXT_ENABLE_CACHING': 'false'}):
            settings = Settings()
            assert settings.CONTEXT_ENABLE_CACHING is False
    
    def test_string_configuration_options(self):
        """Test string-based configuration options."""
        # Test overflow strategy
        with patch.dict(os.environ, {'CONTEXT_OVERFLOW_STRATEGY': 'truncate'}):
            settings = Settings()
            assert settings.CONTEXT_OVERFLOW_STRATEGY == 'truncate'
        
        # Test allocation mode
        with patch.dict(os.environ, {'CONTEXT_ALLOCATION_MODE': 'static'}):
            settings = Settings()
            assert settings.CONTEXT_ALLOCATION_MODE == 'static'
    
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
            'CONTEXT_ENABLE_RAG': 'false',
            'CONTEXT_ENABLE_MONITORING': 'false',
            'CONTEXT_OVERFLOW_STRATEGY': 'borrow'
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
            assert settings.CONTEXT_ENABLE_RAG is False
            assert settings.CONTEXT_ENABLE_MONITORING is False
            assert settings.CONTEXT_OVERFLOW_STRATEGY == 'borrow'
    
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
        assert hasattr(fields['CONTEXT_ENABLE_RAG'], 'description')
        
        # Test specific descriptions
        assert "Maximum context window size" in fields['CONTEXT_MAX_TOKENS'].description
        assert "System instructions" in fields['CONTEXT_LAYER_A_TOKENS'].description
        assert "RAG-based" in fields['CONTEXT_ENABLE_RAG'].description
