import pytest
from app.core.config import Settings


class TestSettings:
    """Test application settings and configuration"""

    def test_settings_defaults(self):
        """Test Settings class with default values"""
        settings = Settings()
        assert settings.API_V1_STR == "/api/v1"
        assert settings.PROJECT_NAME == "Writer Assistant"
        assert settings.DEBUG is True
        assert settings.DATA_DIR == "data"
        assert settings.MAX_CONTEXT_LENGTH == 4000
        assert settings.DEFAULT_TEMPERATURE == 0.7
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30

    def test_settings_api_version(self):
        """Test API version string format"""
        settings = Settings()
        assert settings.API_V1_STR.startswith("/api/")
        assert "v1" in settings.API_V1_STR

    def test_settings_agent_config(self):
        """Test agent-related configuration"""
        settings = Settings()
        assert isinstance(settings.MAX_CONTEXT_LENGTH, int)
        assert settings.MAX_CONTEXT_LENGTH > 0
        assert isinstance(settings.DEFAULT_TEMPERATURE, float)
        assert 0.0 <= settings.DEFAULT_TEMPERATURE <= 1.0

    def test_settings_data_directory(self):
        """Test data directory configuration"""
        settings = Settings()
        assert isinstance(settings.DATA_DIR, str)
        assert len(settings.DATA_DIR) > 0

    def test_settings_security_config(self):
        """Test security-related settings"""
        settings = Settings()
        assert isinstance(settings.SECRET_KEY, str)
        assert len(settings.SECRET_KEY) > 0
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0
