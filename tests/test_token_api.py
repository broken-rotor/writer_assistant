"""
Unit tests for token counting API endpoints.

This module tests the token counting API endpoints including batch processing,
content type detection, budget validation, and error handling.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.api.v1.endpoints.tokens import router, get_token_counter
from app.services.token_management import TokenCounter, ContentType, CountingStrategy, TokenCount
from app.models.token_models import (
    TokenCountRequest,
    TokenCountRequestItem,
    TokenValidationRequest
)


@pytest.fixture
def app():
    """Create FastAPI app for testing."""
    app = FastAPI()
    app.include_router(router, prefix="/tokens")
    return app


@pytest.fixture
def client(app, mock_token_counter):
    """Create test client with mocked dependencies."""
    app.dependency_overrides[get_token_counter] = lambda: mock_token_counter
    return TestClient(app)


@pytest.fixture
def mock_token_counter():
    """Create mock TokenCounter instance."""
    mock_counter = Mock()
    mock_tokenizer = Mock()
    mock_tokenizer.is_ready.return_value = True
    mock_counter.tokenizer = mock_tokenizer
    return mock_counter


@pytest.fixture
def sample_token_count_result():
    """Create sample TokenCount result."""
    return TokenCount(
        content="Test content",
        token_count=5,
        content_type=ContentType.NARRATIVE,
        strategy=CountingStrategy.EXACT,
        overhead_applied=1.0,
        metadata={
            "base_count": 5,
            "content_length": 12,
            "content_multiplier": 1.0,
            "tokenizer_used": True
        }
    )


class TestTokenCountEndpoint:
    """Test cases for the /tokens/count endpoint."""
    
    def test_count_tokens_success(self, client, mock_token_counter, sample_token_count_result):
        """Test successful token counting."""
        # Setup mock
        mock_token_counter.count_tokens_batch.return_value = [sample_token_count_result]
        
        with patch('app.api.v1.endpoints.tokens.get_token_counter', return_value=mock_token_counter):
            response = client.post("/tokens/count", json={
                "texts": [
                    {
                        "text": "Test content",
                        "content_type": "narrative"
                    }
                ],
                "strategy": "exact",
                "include_metadata": True
            })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert len(data["results"]) == 1
        assert data["results"][0]["text"] == "Test content"
        assert data["results"][0]["token_count"] == 5
        assert data["results"][0]["content_type"] == "narrative"
        assert data["results"][0]["strategy"] == "exact"
        assert data["results"][0]["metadata"] is not None
        
        # Check summary
        assert data["summary"]["total_texts"] == 1
        assert data["summary"]["total_tokens"] == 5
        assert data["summary"]["strategy_used"] == "exact"
    
    def test_count_tokens_batch(self, client, mock_token_counter):
        """Test batch token counting."""
        # Setup mock for multiple results
        results = [
            TokenCount("Text 1", 3, ContentType.NARRATIVE, CountingStrategy.EXACT, 1.0, {}),
            TokenCount("Text 2", 4, ContentType.DIALOGUE, CountingStrategy.EXACT, 1.05, {}),
        ]
        mock_token_counter.count_tokens_batch.return_value = results
        
        with patch('app.api.v1.endpoints.tokens.get_token_counter', return_value=mock_token_counter):
            response = client.post("/tokens/count", json={
                "texts": [
                    {"text": "Text 1", "content_type": "narrative"},
                    {"text": "Text 2", "content_type": "dialogue"}
                ],
                "strategy": "exact",
                "include_metadata": False
            })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert len(data["results"]) == 2
        assert data["summary"]["total_tokens"] == 7
        assert data["results"][0]["metadata"] is None  # metadata disabled
    
    def test_count_tokens_auto_detect_content_type(self, client, mock_token_counter, sample_token_count_result):
        """Test token counting with auto-detected content type."""
        mock_token_counter.count_tokens_batch.return_value = [sample_token_count_result]
        
        with patch('app.api.v1.endpoints.tokens.get_token_counter', return_value=mock_token_counter):
            response = client.post("/tokens/count", json={
                "texts": [
                    {"text": "Test content"}  # No content_type specified
                ],
                "strategy": "exact"
            })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Verify the service was called with None for content type (auto-detect)
        mock_token_counter.count_tokens_batch.assert_called_once()
        args, kwargs = mock_token_counter.count_tokens_batch.call_args
        assert kwargs["content_types"] == [None]
    
    def test_count_tokens_different_strategies(self, client, mock_token_counter, sample_token_count_result):
        """Test different counting strategies."""
        strategies = ["exact", "estimated", "conservative", "optimistic"]
        
        for strategy in strategies:
            mock_token_counter.count_tokens_batch.return_value = [sample_token_count_result]
            
            with patch('app.api.v1.endpoints.tokens.get_token_counter', return_value=mock_token_counter):
                response = client.post("/tokens/count", json={
                    "texts": [{"text": "Test content"}],
                    "strategy": strategy
                })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["summary"]["strategy_used"] == strategy
    
    def test_count_tokens_validation_error_empty_text(self, client):
        """Test validation error for empty text list."""
        response = client.post("/tokens/count", json={
            "texts": [],  # Empty list
            "strategy": "exact"
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_count_tokens_validation_error_too_many_texts(self, client):
        """Test validation error for too many texts."""
        texts = [{"text": f"Text {i}"} for i in range(51)]  # Over limit of 50
        
        response = client.post("/tokens/count", json={
            "texts": texts,
            "strategy": "exact"
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_count_tokens_validation_error_text_too_large(self, client):
        """Test validation error for text that's too large."""
        large_text = "x" * 100001  # Over 100KB limit
        
        response = client.post("/tokens/count", json={
            "texts": [{"text": large_text}],
            "strategy": "exact"
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_count_tokens_service_error(self, client, mock_token_counter):
        """Test handling of service errors."""
        mock_token_counter.count_tokens_batch.side_effect = ValueError("Invalid input")
        
        with patch('app.api.v1.endpoints.tokens.get_token_counter', return_value=mock_token_counter):
            response = client.post("/tokens/count", json={
                "texts": [{"text": "Test content"}],
                "strategy": "exact"
            })
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid input" in str(data["detail"])
    
    def test_count_tokens_unexpected_error(self, client, mock_token_counter):
        """Test handling of unexpected errors."""
        mock_token_counter.count_tokens_batch.side_effect = Exception("Unexpected error")
        
        with patch('app.api.v1.endpoints.tokens.get_token_counter', return_value=mock_token_counter):
            response = client.post("/tokens/count", json={
                "texts": [{"text": "Test content"}],
                "strategy": "exact"
            })
        
        assert response.status_code == 500
        data = response.json()
        assert data["detail"]["success"] is False


class TestTokenValidationEndpoint:
    """Test cases for the /tokens/validate endpoint."""
    
    def test_validate_token_budget_success(self, client, mock_token_counter):
        """Test successful token budget validation."""
        validation_result = {
            "fits_budget": True,
            "total_tokens": 100,
            "budget": 200,
            "utilization": 0.5,
            "remaining_tokens": 100,
            "overflow_tokens": 0
        }
        mock_token_counter.validate_token_budget.return_value = validation_result
        
        with patch('app.api.v1.endpoints.tokens.get_token_counter', return_value=mock_token_counter):
            response = client.post("/tokens/validate", json={
                "texts": ["Text 1", "Text 2"],
                "budget": 200,
                "strategy": "conservative"
            })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["fits_budget"] is True
        assert data["total_tokens"] == 100
        assert data["budget"] == 200
        assert data["utilization"] == 0.5
        assert data["remaining_tokens"] == 100
        assert data["overflow_tokens"] == 0
        assert data["strategy_used"] == "conservative"
    
    def test_validate_token_budget_over_budget(self, client, mock_token_counter):
        """Test token budget validation when over budget."""
        validation_result = {
            "fits_budget": False,
            "total_tokens": 300,
            "budget": 200,
            "utilization": 1.5,
            "remaining_tokens": 0,
            "overflow_tokens": 100
        }
        mock_token_counter.validate_token_budget.return_value = validation_result
        
        with patch('app.api.v1.endpoints.tokens.get_token_counter', return_value=mock_token_counter):
            response = client.post("/tokens/validate", json={
                "texts": ["Very long text content"],
                "budget": 200,
                "strategy": "conservative"
            })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["fits_budget"] is False
        assert data["total_tokens"] == 300
        assert data["overflow_tokens"] == 100
    
    def test_validate_token_budget_validation_error(self, client):
        """Test validation error for invalid budget."""
        response = client.post("/tokens/validate", json={
            "texts": ["Text content"],
            "budget": 0,  # Invalid budget
            "strategy": "conservative"
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_validate_token_budget_service_error(self, client, mock_token_counter):
        """Test handling of service errors in validation."""
        mock_token_counter.validate_token_budget.side_effect = ValueError("Invalid budget")
        
        with patch('app.api.v1.endpoints.tokens.get_token_counter', return_value=mock_token_counter):
            response = client.post("/tokens/validate", json={
                "texts": ["Text content"],
                "budget": 100,
                "strategy": "conservative"
            })
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid budget" in str(data["detail"])


class TestStrategiesEndpoint:
    """Test cases for the /tokens/strategies endpoint."""
    
    def test_get_strategies_success(self, client):
        """Test successful retrieval of strategies and content types."""
        response = client.get("/tokens/strategies")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "strategies" in data
        assert "content_types" in data
        assert "default_strategy" in data
        assert "batch_limits" in data
        
        # Check strategies
        strategies = data["strategies"]
        assert "exact" in strategies
        assert "estimated" in strategies
        assert "conservative" in strategies
        assert "optimistic" in strategies
        
        # Check content types
        content_types = data["content_types"]
        assert "narrative" in content_types
        assert "dialogue" in content_types
        assert "system_prompt" in content_types
        
        # Check batch limits
        batch_limits = data["batch_limits"]
        assert batch_limits["max_texts_per_request"] == 50
        assert batch_limits["max_text_size_bytes"] == 100000


class TestTokenCounterDependency:
    """Test cases for the TokenCounter dependency."""
    
    def test_get_token_counter_creates_instance(self):
        """Test that get_token_counter creates a TokenCounter instance."""
        with patch('app.api.v1.endpoints.tokens.TokenCounter') as mock_class:
            mock_instance = Mock()
            mock_class.return_value = mock_instance
            
            result = get_token_counter()
            
            assert result == mock_instance
            mock_class.assert_called_once()


class TestRequestModels:
    """Test cases for request model validation."""
    
    def test_token_count_request_item_validation(self):
        """Test TokenCountRequestItem validation."""
        # Valid item
        item = TokenCountRequestItem(
            text="Test content",
            content_type=ContentType.NARRATIVE
        )
        assert item.text == "Test content"
        assert item.content_type == ContentType.NARRATIVE
        
        # Test text size validation
        with pytest.raises(ValueError, match="Text content too large"):
            TokenCountRequestItem(text="x" * 100001)
    
    def test_token_count_request_validation(self):
        """Test TokenCountRequest validation."""
        # Valid request
        request = TokenCountRequest(
            texts=[
                TokenCountRequestItem(text="Text 1"),
                TokenCountRequestItem(text="Text 2")
            ],
            strategy=CountingStrategy.EXACT,
            include_metadata=True
        )
        assert len(request.texts) == 2
        assert request.strategy == CountingStrategy.EXACT
        assert request.include_metadata is True
    
    def test_token_validation_request_validation(self):
        """Test TokenValidationRequest validation."""
        # Valid request
        request = TokenValidationRequest(
            texts=["Text 1", "Text 2"],
            budget=1000,
            strategy=CountingStrategy.CONSERVATIVE
        )
        assert len(request.texts) == 2
        assert request.budget == 1000
        assert request.strategy == CountingStrategy.CONSERVATIVE
        
        # Test budget validation
        with pytest.raises(ValueError):
            TokenValidationRequest(
                texts=["Text"],
                budget=0,  # Invalid budget
                strategy=CountingStrategy.CONSERVATIVE
            )
