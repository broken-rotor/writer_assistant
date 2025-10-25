"""
Integration tests for token counting API endpoints.

This module tests the complete end-to-end functionality of the token counting API,
including real HTTP requests, response validation, and integration with the
TokenCounter service.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

from app.main import app
from app.services.token_management import TokenCounter, ContentType, CountingStrategy


@pytest.fixture
def client():
    """Create test client for the full application."""
    return TestClient(app)


@pytest.fixture
def mock_tokenizer():
    """Create a mock tokenizer for testing."""
    mock_tokenizer = Mock()
    mock_tokenizer.is_ready.return_value = True
    mock_tokenizer.count_tokens.side_effect = lambda text: max(1, len(text.split()))
    return mock_tokenizer


class TestTokenCountEndpointIntegration:
    """Integration tests for the /api/v1/tokens/count endpoint."""
    
    def test_count_tokens_endpoint_exists(self, client):
        """Test that the token count endpoint is accessible."""
        response = client.post("/api/v1/tokens/count", json={
            "texts": [{"text": "Hello world"}],
            "strategy": "exact"
        })
        
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
    
    def test_count_tokens_full_integration(self, client, mock_tokenizer):
        """Test full integration with real TokenCounter service."""
        with patch('app.services.token_management.token_counter.LlamaTokenizer.get_instance', 
                   return_value=mock_tokenizer):
            response = client.post("/api/v1/tokens/count", json={
                "texts": [
                    {
                        "text": "You are a helpful writing assistant.",
                        "content_type": "system_prompt"
                    },
                    {
                        "text": "Once upon a time, in a distant kingdom, there lived a brave knight.",
                        "content_type": "narrative"
                    }
                ],
                "strategy": "exact",
                "include_metadata": True
            })
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data["success"] is True
        assert "results" in data
        assert "summary" in data
        assert len(data["results"]) == 2
        
        # Verify first result (system prompt)
        result1 = data["results"][0]
        assert result1["text"] == "You are a helpful writing assistant."
        assert result1["content_type"] == "system_prompt"
        assert result1["strategy"] == "exact"
        assert result1["token_count"] > 0
        assert result1["metadata"] is not None
        
        # Verify second result (narrative)
        result2 = data["results"][1]
        assert result2["text"] == "Once upon a time, in a distant kingdom, there lived a brave knight."
        assert result2["content_type"] == "narrative"
        assert result2["strategy"] == "exact"
        assert result2["token_count"] > 0
        
        # Verify summary
        summary = data["summary"]
        assert summary["total_texts"] == 2
        assert summary["total_tokens"] > 0
        assert summary["strategy_used"] == "exact"
        assert "content_type_distribution" in summary
    
    def test_count_tokens_auto_content_detection(self, client, mock_tokenizer):
        """Test content type auto-detection integration."""
        with patch('app.services.token_management.token_counter.LlamaTokenizer.get_instance', 
                   return_value=mock_tokenizer):
            response = client.post("/api/v1/tokens/count", json={
                "texts": [
                    {"text": "You are a helpful assistant."},  # Should detect as system_prompt
                    {"text": "\"Hello there,\" she said with a smile."},  # Should detect as dialogue
                    {"text": "The old castle stood majestically on the hill."}  # Should detect as narrative
                ],
                "strategy": "exact",
                "include_metadata": True
            })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert len(data["results"]) == 3
        
        # Content types should be auto-detected (exact types depend on detection logic)
        for result in data["results"]:
            assert result["content_type"] in [
                "system_prompt", "dialogue", "narrative", "unknown"
            ]
    
    def test_count_tokens_different_strategies_integration(self, client, mock_tokenizer):
        """Test different counting strategies integration."""
        strategies = ["exact", "estimated", "conservative", "optimistic"]
        
        for strategy in strategies:
            with patch('app.services.token_management.token_counter.LlamaTokenizer.get_instance', 
                       return_value=mock_tokenizer):
                response = client.post("/api/v1/tokens/count", json={
                    "texts": [{"text": "This is a test message for token counting."}],
                    "strategy": strategy,
                    "include_metadata": True
                })
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["summary"]["strategy_used"] == strategy
            assert data["results"][0]["strategy"] == strategy
            
            # Different strategies should potentially give different token counts
            # due to different overhead multipliers
            assert data["results"][0]["token_count"] > 0
    
    def test_count_tokens_batch_processing_integration(self, client, mock_tokenizer):
        """Test batch processing with multiple texts."""
        # Create a batch of 10 texts
        texts = [
            {"text": f"This is test message number {i} for batch processing.", 
             "content_type": "narrative"}
            for i in range(1, 11)
        ]
        
        with patch('app.services.token_management.token_counter.LlamaTokenizer.get_instance', 
                   return_value=mock_tokenizer):
            response = client.post("/api/v1/tokens/count", json={
                "texts": texts,
                "strategy": "exact",
                "include_metadata": True
            })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert len(data["results"]) == 10
        assert data["summary"]["total_texts"] == 10
        
        # All results should have the same content type
        for result in data["results"]:
            assert result["content_type"] == "narrative"
            assert result["token_count"] > 0
    
    def test_count_tokens_error_handling_integration(self, client):
        """Test error handling in integration environment."""
        # Test with invalid request (empty texts)
        response = client.post("/api/v1/tokens/count", json={
            "texts": [],
            "strategy": "exact"
        })
        
        assert response.status_code == 422  # Validation error
        
        # Test with text too large
        response = client.post("/api/v1/tokens/count", json={
            "texts": [{"text": "x" * 100001}],  # Over 100KB limit
            "strategy": "exact"
        })
        
        assert response.status_code == 422  # Validation error
        
        # Test with too many texts
        texts = [{"text": f"Text {i}"} for i in range(51)]  # Over limit of 50
        response = client.post("/api/v1/tokens/count", json={
            "texts": texts,
            "strategy": "exact"
        })
        
        assert response.status_code == 422  # Validation error


class TestTokenValidationEndpointIntegration:
    """Integration tests for the /api/v1/tokens/validate endpoint."""
    
    def test_validate_endpoint_exists(self, client):
        """Test that the token validation endpoint is accessible."""
        response = client.post("/api/v1/tokens/validate", json={
            "texts": ["Hello world"],
            "budget": 100,
            "strategy": "conservative"
        })
        
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
    
    def test_validate_token_budget_integration(self, client, mock_tokenizer):
        """Test token budget validation integration."""
        with patch('app.services.token_management.token_counter.LlamaTokenizer.get_instance', 
                   return_value=mock_tokenizer):
            response = client.post("/api/v1/tokens/validate", json={
                "texts": [
                    "System prompt for the AI assistant.",
                    "User input message here.",
                    "Expected AI response content."
                ],
                "budget": 1000,
                "strategy": "conservative"
            })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "fits_budget" in data
        assert "total_tokens" in data
        assert "budget" in data
        assert "utilization" in data
        assert "remaining_tokens" in data
        assert "overflow_tokens" in data
        assert data["strategy_used"] == "conservative"
        assert data["budget"] == 1000
    
    def test_validate_over_budget_integration(self, client, mock_tokenizer):
        """Test validation when content exceeds budget."""
        # Mock tokenizer to return high token counts
        mock_tokenizer.count_tokens.side_effect = lambda text: len(text) * 2  # High token count
        
        with patch('app.services.token_management.token_counter.LlamaTokenizer.get_instance', 
                   return_value=mock_tokenizer):
            response = client.post("/api/v1/tokens/validate", json={
                "texts": [
                    "This is a very long text that should exceed the small budget limit.",
                    "Another long text to push us over the budget."
                ],
                "budget": 10,  # Very small budget
                "strategy": "conservative"
            })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["fits_budget"] is False
        assert data["total_tokens"] > data["budget"]
        assert data["overflow_tokens"] > 0
        assert data["remaining_tokens"] == 0
    
    def test_validate_error_handling_integration(self, client):
        """Test validation error handling."""
        # Test with invalid budget
        response = client.post("/api/v1/tokens/validate", json={
            "texts": ["Test content"],
            "budget": 0,  # Invalid budget
            "strategy": "conservative"
        })
        
        assert response.status_code == 422  # Validation error


class TestStrategiesEndpointIntegration:
    """Integration tests for the /api/v1/tokens/strategies endpoint."""
    
    def test_strategies_endpoint_exists(self, client):
        """Test that the strategies endpoint is accessible."""
        response = client.get("/api/v1/tokens/strategies")
        
        assert response.status_code == 200
    
    def test_get_strategies_integration(self, client):
        """Test getting strategies and content types."""
        response = client.get("/api/v1/tokens/strategies")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "strategies" in data
        assert "content_types" in data
        assert "default_strategy" in data
        assert "batch_limits" in data
        
        # Verify strategies
        strategies = data["strategies"]
        expected_strategies = ["exact", "estimated", "conservative", "optimistic"]
        for strategy in expected_strategies:
            assert strategy in strategies
            assert "description" in strategies[strategy]
            assert "overhead" in strategies[strategy]
            assert "use_case" in strategies[strategy]
        
        # Verify content types
        content_types = data["content_types"]
        expected_types = [
            "narrative", "dialogue", "system_prompt", "character_description",
            "scene_description", "internal_monologue", "metadata", "unknown"
        ]
        for content_type in expected_types:
            assert content_type in content_types
            assert "description" in content_types[content_type]
            assert "multiplier" in content_types[content_type]
        
        # Verify batch limits
        batch_limits = data["batch_limits"]
        assert batch_limits["max_texts_per_request"] == 50
        assert batch_limits["max_text_size_bytes"] == 100000


class TestAPIDocumentationIntegration:
    """Integration tests for API documentation generation."""
    
    def test_openapi_schema_generation(self, client):
        """Test that OpenAPI schema is generated correctly."""
        response = client.get("/api/v1/openapi.json")
        
        # Should be able to access OpenAPI schema
        assert response.status_code == 200
        schema = response.json()
        
        # Verify token endpoints are documented
        paths = schema.get("paths", {})
        assert "/api/v1/tokens/count" in paths
        assert "/api/v1/tokens/validate" in paths
        assert "/api/v1/tokens/strategies" in paths
        
        # Verify POST method for count endpoint
        count_endpoint = paths["/api/v1/tokens/count"]
        assert "post" in count_endpoint
        
        # Verify response schemas are defined
        components = schema.get("components", {})
        schemas = components.get("schemas", {})
        assert "TokenCountResponse" in schemas
        assert "TokenValidationResponse" in schemas
        assert "ErrorResponse" in schemas
    
    def test_docs_page_accessible(self, client):
        """Test that the API documentation page is accessible."""
        response = client.get("/docs")
        
        # Should be able to access Swagger UI
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")


class TestEndToEndWorkflow:
    """End-to-end workflow tests."""
    
    def test_complete_token_counting_workflow(self, client, mock_tokenizer):
        """Test a complete workflow from strategies to counting to validation."""
        with patch('app.services.token_management.token_counter.LlamaTokenizer.get_instance', 
                   return_value=mock_tokenizer):
            
            # Step 1: Get available strategies
            strategies_response = client.get("/api/v1/tokens/strategies")
            assert strategies_response.status_code == 200
            strategies_data = strategies_response.json()
            
            # Step 2: Count tokens for some content
            count_response = client.post("/api/v1/tokens/count", json={
                "texts": [
                    {"text": "System: You are a helpful assistant.", "content_type": "system_prompt"},
                    {"text": "User: Write a short story about a dragon.", "content_type": "narrative"},
                    {"text": "Assistant: Once upon a time...", "content_type": "narrative"}
                ],
                "strategy": "conservative",
                "include_metadata": True
            })
            assert count_response.status_code == 200
            count_data = count_response.json()
            
            total_tokens = count_data["summary"]["total_tokens"]
            
            # Step 3: Validate against a budget
            validate_response = client.post("/api/v1/tokens/validate", json={
                "texts": [
                    "System: You are a helpful assistant.",
                    "User: Write a short story about a dragon.",
                    "Assistant: Once upon a time..."
                ],
                "budget": total_tokens + 100,  # Should fit
                "strategy": "conservative"
            })
            assert validate_response.status_code == 200
            validate_data = validate_response.json()
            
            assert validate_data["fits_budget"] is True
            assert validate_data["total_tokens"] <= validate_data["budget"]
            
            # Step 4: Validate against a smaller budget
            small_budget_response = client.post("/api/v1/tokens/validate", json={
                "texts": [
                    "System: You are a helpful assistant.",
                    "User: Write a short story about a dragon.",
                    "Assistant: Once upon a time..."
                ],
                "budget": max(1, total_tokens - 10),  # Should not fit
                "strategy": "conservative"
            })
            assert small_budget_response.status_code == 200
            small_budget_data = small_budget_response.json()
            
            # Should not fit in smaller budget
            assert small_budget_data["fits_budget"] is False
            assert small_budget_data["overflow_tokens"] > 0
