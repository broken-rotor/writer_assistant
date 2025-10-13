import pytest
from app.core.config import Settings


class TestSettings:
    """Test application settings and configuration"""

    def test_settings_defaults(self):
        """Test Settings class with default values"""
        settings = Settings()
        assert settings.API_V1_STR == "/api/v1"
        assert settings.DEBUG is True

    def test_settings_api_version(self):
        """Test API version string format"""
        settings = Settings()
        assert settings.API_V1_STR.startswith("/api/")
        assert "v1" in settings.API_V1_STR