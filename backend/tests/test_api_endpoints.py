import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test health check and root endpoints"""

    def test_root_endpoint(self, client):
        """Test root endpoint returns correct response"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["message"] == "Writer Assistant API"

    def test_health_check_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"


class TestAPIErrorHandling:
    """Test API error handling"""

    def test_invalid_endpoint(self, client):
        """Test invalid endpoint returns 404"""
        response = client.get("/api/v1/invalid/endpoint")
        assert response.status_code == 404
