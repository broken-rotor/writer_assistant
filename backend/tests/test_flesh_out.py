"""
Tests for flesh out text expansion endpoint.
"""
import pytest
from fastapi.testclient import TestClient


class TestFleshOutEndpoint:
    """Test flesh out text expansion endpoint"""

    def test_flesh_out_success(self, client, sample_flesh_out_request):
        """Test successful text expansion"""
        response = client.post("/api/v1/flesh-out", json=sample_flesh_out_request)
        assert response.status_code == 200
        data = response.json()
        assert "fleshedOutText" in data
        assert "originalText" in data

    def test_flesh_out_response_structure(self, client, sample_flesh_out_request):
        """Test flesh out response structure"""
        response = client.post("/api/v1/flesh-out", json=sample_flesh_out_request)
        data = response.json()

        assert isinstance(data["fleshedOutText"], str)
        assert isinstance(data["originalText"], str)
        assert len(data["fleshedOutText"]) > len(data["originalText"])

    def test_flesh_out_includes_original_text(self, client, sample_flesh_out_request):
        """Test fleshed out text includes original"""
        original = sample_flesh_out_request["textToFleshOut"]
        response = client.post("/api/v1/flesh-out", json=sample_flesh_out_request)
        fleshed_out = response.json()["fleshedOutText"]

        assert original in fleshed_out

    def test_flesh_out_returns_original_text(self, client, sample_flesh_out_request):
        """Test that original text is returned unchanged"""
        original = sample_flesh_out_request["textToFleshOut"]
        response = client.post("/api/v1/flesh-out", json=sample_flesh_out_request)
        returned_original = response.json()["originalText"]

        assert original == returned_original

    def test_flesh_out_with_short_text(self, client, sample_flesh_out_request):
        """Test flesh out with very short text"""
        sample_flesh_out_request["textToFleshOut"] = "The detective arrives."
        response = client.post("/api/v1/flesh-out", json=sample_flesh_out_request)
        assert response.status_code == 200

    def test_flesh_out_with_long_text(self, client, sample_flesh_out_request):
        """Test flesh out with longer text"""
        long_text = "The investigation begins. " * 20
        sample_flesh_out_request["textToFleshOut"] = long_text
        response = client.post("/api/v1/flesh-out", json=sample_flesh_out_request)
        assert response.status_code == 200

    def test_flesh_out_with_different_contexts(self, client, sample_flesh_out_request):
        """Test flesh out with different context types"""
        contexts = ["worldbuilding", "plot point", "character development", "scene description"]

        for context in contexts:
            sample_flesh_out_request["context"] = context
            response = client.post("/api/v1/flesh-out", json=sample_flesh_out_request)
            assert response.status_code == 200

    def test_flesh_out_missing_text_to_flesh_out(self, client):
        """Test flesh out fails without text to expand"""
        invalid_request = {
            "systemPrompts": {"mainPrefix": "", "mainSuffix": ""},
            "worldbuilding": "Test",
            "storySummary": "Test",
            "context": "Test"
        }
        response = client.post("/api/v1/flesh-out", json=invalid_request)
        assert response.status_code == 422
