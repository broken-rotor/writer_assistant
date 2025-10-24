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
        
        # Test layer ratios
        assert settings.CONTEXT_LAYER_A_RATIO == 0.0625
        assert settings.CONTEXT_LAYER_B_RATIO == 0.0
        assert settings.CONTEXT_LAYER_C_RATIO == 0.4375
        assert settings.CONTEXT_LAYER_D_RATIO == 0.15625
        assert settings.CONTEXT_LAYER_E_RATIO == 0.34375
        
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
    
    def test_layer_ratios_sum_validation(self):
        """Test that layer ratios are validated to sum <= 1.0."""
        # Test valid ratios (sum = 1.0)
        with patch.dict(os.environ, {
            'CONTEXT_LAYER_A_RATIO': '0.2',
            'CONTEXT_LAYER_B_RATIO': '0.1',
            'CONTEXT_LAYER_C_RATIO': '0.3',
            'CONTEXT_LAYER_D_RATIO': '0.2',
            'CONTEXT_LAYER_E_RATIO': '0.2'
        }):
            settings = Settings()
            assert settings.CONTEXT_LAYER_A_RATIO == 0.2
        
        # Test invalid ratios (sum > 1.0)
        with patch.dict(os.environ, {
            'CONTEXT_LAYER_A_RATIO': '0.5',
            'CONTEXT_LAYER_B_RATIO': '0.3',
            'CONTEXT_LAYER_C_RATIO': '0.4',
            'CONTEXT_LAYER_D_RATIO': '0.2',
            'CONTEXT_LAYER_E_RATIO': '0.2'
        }):
            with pytest.raises(ValueError, match="Context layer ratios sum to .* which exceeds 1.0"):
                Settings()
    
    def test_context_max_tokens_validation(self):
        """Test CONTEXT_MAX_TOKENS validation."""
        # Test valid values
        with patch.dict(os.environ, {'CONTEXT_MAX_TOKENS': '16000'}):
            settings = Settings()
            assert settings.CONTEXT_MAX_TOKENS == 16000
        
        # Test minimum boundary
        with patch.dict(os.environ, {'CONTEXT_MAX_TOKENS': '1000'}):
            settings = Settings()
            assert settings.CONTEXT_MAX_TOKENS == 1000
        
        # Test maximum boundary
        with patch.dict(os.environ, {'CONTEXT_MAX_TOKENS': '100000'}):
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
        with patch.dict(os.environ, {'CONTEXT_BUFFER_TOKENS': '1500'}):
            settings = Settings()
            assert settings.CONTEXT_BUFFER_TOKENS == 1500
        
        # Test minimum boundary
        with patch.dict(os.environ, {'CONTEXT_BUFFER_TOKENS': '100'}):
            settings = Settings()
            assert settings.CONTEXT_BUFFER_TOKENS == 100
        
        # Test maximum boundary
        with patch.dict(os.environ, {'CONTEXT_BUFFER_TOKENS': '10000'}):
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
    
    def test_layer_ratio_validation(self):
        """Test individual layer ratio validation."""
        # Test valid ratio
        with patch.dict(os.environ, {'CONTEXT_LAYER_A_RATIO': '0.5'}):
            settings = Settings()
            assert settings.CONTEXT_LAYER_A_RATIO == 0.5
        
        # Test minimum boundary (0.0)
        with patch.dict(os.environ, {'CONTEXT_LAYER_A_RATIO': '0.0'}):
            settings = Settings()
            assert settings.CONTEXT_LAYER_A_RATIO == 0.0
        
        # Test maximum boundary (1.0)
        with patch.dict(os.environ, {'CONTEXT_LAYER_A_RATIO': '1.0'}):
            with pytest.raises(ValueError):  # This would make total > 1.0
                Settings()
        
        # Test below minimum
        with patch.dict(os.environ, {'CONTEXT_LAYER_A_RATIO': '-0.1'}):
            with pytest.raises(ValidationError):
                Settings()
        
        # Test above maximum
        with patch.dict(os.environ, {'CONTEXT_LAYER_A_RATIO': '1.5'}):
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
            'CONTEXT_LAYER_A_RATIO': '0.1',
            'CONTEXT_LAYER_B_RATIO': '0.05',
            'CONTEXT_LAYER_C_RATIO': '0.4',
            'CONTEXT_LAYER_D_RATIO': '0.2',
            'CONTEXT_LAYER_E_RATIO': '0.25',
            'CONTEXT_ENABLE_RAG': 'false',
            'CONTEXT_ENABLE_MONITORING': 'false',
            'CONTEXT_OVERFLOW_STRATEGY': 'borrow'
        }
        
        with patch.dict(os.environ, env_vars):
            settings = Settings()
            
            assert settings.CONTEXT_MAX_TOKENS == 16000
            assert settings.CONTEXT_BUFFER_TOKENS == 1000
            assert settings.CONTEXT_LAYER_A_RATIO == 0.1
            assert settings.CONTEXT_LAYER_B_RATIO == 0.05
            assert settings.CONTEXT_LAYER_C_RATIO == 0.4
            assert settings.CONTEXT_LAYER_D_RATIO == 0.2
            assert settings.CONTEXT_LAYER_E_RATIO == 0.25
            assert settings.CONTEXT_ENABLE_RAG is False
            assert settings.CONTEXT_ENABLE_MONITORING is False
            assert settings.CONTEXT_OVERFLOW_STRATEGY == 'borrow'
    
    def test_edge_case_layer_ratios(self):
        """Test edge cases for layer ratio validation."""
        # Test all zeros (valid)
        with patch.dict(os.environ, {
            'CONTEXT_LAYER_A_RATIO': '0.0',
            'CONTEXT_LAYER_B_RATIO': '0.0',
            'CONTEXT_LAYER_C_RATIO': '0.0',
            'CONTEXT_LAYER_D_RATIO': '0.0',
            'CONTEXT_LAYER_E_RATIO': '0.0'
        }):
            settings = Settings()
            total = (settings.CONTEXT_LAYER_A_RATIO + 
                    settings.CONTEXT_LAYER_B_RATIO + 
                    settings.CONTEXT_LAYER_C_RATIO + 
                    settings.CONTEXT_LAYER_D_RATIO + 
                    settings.CONTEXT_LAYER_E_RATIO)
            assert total == 0.0
        
        # Test sum exactly 1.0 (valid)
        with patch.dict(os.environ, {
            'CONTEXT_LAYER_A_RATIO': '0.2',
            'CONTEXT_LAYER_B_RATIO': '0.2',
            'CONTEXT_LAYER_C_RATIO': '0.2',
            'CONTEXT_LAYER_D_RATIO': '0.2',
            'CONTEXT_LAYER_E_RATIO': '0.2'
        }):
            settings = Settings()
            total = (settings.CONTEXT_LAYER_A_RATIO + 
                    settings.CONTEXT_LAYER_B_RATIO + 
                    settings.CONTEXT_LAYER_C_RATIO + 
                    settings.CONTEXT_LAYER_D_RATIO + 
                    settings.CONTEXT_LAYER_E_RATIO)
            assert total == 1.0
        
        # Test sum slightly over 1.0 (invalid)
        with patch.dict(os.environ, {
            'CONTEXT_LAYER_A_RATIO': '0.21',
            'CONTEXT_LAYER_B_RATIO': '0.2',
            'CONTEXT_LAYER_C_RATIO': '0.2',
            'CONTEXT_LAYER_D_RATIO': '0.2',
            'CONTEXT_LAYER_E_RATIO': '0.2'
        }):
            with pytest.raises(ValueError, match="Context layer ratios sum to .* which exceeds 1.0"):
                Settings()
    
    def test_configuration_descriptions(self):
        """Test that configuration fields have proper descriptions."""
        settings = Settings()
        
        # Get field info from the model
        fields = settings.model_fields
        
        # Test that key fields have descriptions
        assert 'description' in fields['CONTEXT_MAX_TOKENS']
        assert 'description' in fields['CONTEXT_LAYER_A_RATIO']
        assert 'description' in fields['CONTEXT_ENABLE_RAG']
        
        # Test specific descriptions
        assert "Maximum context window size" in fields['CONTEXT_MAX_TOKENS']['description']
        assert "System instructions" in fields['CONTEXT_LAYER_A_RATIO']['description']
        assert "RAG-based" in fields['CONTEXT_ENABLE_RAG']['description']
