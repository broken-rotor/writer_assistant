"""
Integration tests for context management API endpoints.

This module provides comprehensive tests for the context management functionality
including realistic data scenarios, context optimization, error handling,
and integration with existing endpoints.
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from backend.app.main import app
from backend.app.models.context_models import (
    ContextManageRequest, ContextItemRequest, ContextTypeEnum, LayerTypeEnum
)
from backend.app.services.context_manager import ContextManager


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_context_items():
    """Sample context items for testing."""
    return [
        {
            "content": "You are a helpful AI assistant for creative writing. Focus on character development and narrative flow.",
            "context_type": "system",
            "priority": 10,
            "layer_type": "working_memory",
            "metadata": {"source": "system_config"}
        },
        {
            "content": "In the mystical realm of Aethermoor, magic flows through crystalline ley lines that crisscross the landscape. The capital city of Lumenhaven sits at the convergence of three major ley lines, making it a hub of magical activity.",
            "context_type": "world",
            "priority": 8,
            "layer_type": "long_term_memory",
            "metadata": {"world_element": "setting"}
        },
        {
            "content": "Lyra Nightwhisper is a 25-year-old elven mage with silver hair and violet eyes. She specializes in shadow magic and has a mysterious past involving the destruction of her home village. She's cautious but fiercely loyal to those she trusts.",
            "context_type": "character",
            "priority": 9,
            "layer_type": "short_term_memory",
            "metadata": {"character_name": "Lyra"}
        },
        {
            "content": "The story follows Lyra as she investigates a series of magical disturbances in Lumenhaven. She discovers that someone is deliberately disrupting the ley lines, threatening the city's magical defenses.",
            "context_type": "story",
            "priority": 7,
            "layer_type": "episodic_memory",
            "metadata": {"plot_element": "main_conflict"}
        },
        {
            "content": "Previous feedback: Add more sensory details to the magical descriptions. The shadow magic scenes need more emotional depth. Consider expanding on Lyra's internal conflict about using her powers.",
            "context_type": "feedback",
            "priority": 6,
            "layer_type": "agent_specific_memory",
            "metadata": {"feedback_source": "editor"}
        }
    ]


@pytest.fixture
def large_context_items():
    """Large context items that should trigger optimization."""
    base_content = "This is a very long piece of content that will be repeated many times to create a large context that exceeds the normal token limits and should trigger context optimization and distillation processes. "
    
    return [
        {
            "content": "You are an AI writing assistant. " + base_content * 50,
            "context_type": "system",
            "priority": 10,
            "layer_type": "working_memory"
        },
        {
            "content": "World description: " + base_content * 100,
            "context_type": "world", 
            "priority": 8,
            "layer_type": "long_term_memory"
        },
        {
            "content": "Character details: " + base_content * 75,
            "context_type": "character",
            "priority": 9,
            "layer_type": "short_term_memory"
        },
        {
            "content": "Story summary: " + base_content * 60,
            "context_type": "story",
            "priority": 7,
            "layer_type": "episodic_memory"
        }
    ]


class TestContextManagementEndpoints:
    """Test suite for context management API endpoints."""
    
    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get("/api/v1/context/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "services" in data
        assert "configuration" in data
        assert "timestamp" in data
    
    def test_get_configuration(self, client):
        """Test the configuration endpoint."""
        response = client.get("/api/v1/context/config")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "configuration" in data
        
        config = data["configuration"]
        assert "max_context_tokens" in config
        assert "distillation_threshold" in config
        assert "supported_context_types" in config
        assert "supported_layer_types" in config
    
    def test_context_analysis(self, client, sample_context_items):
        """Test context analysis without optimization."""
        request_data = {
            "context_items": sample_context_items,
            "enable_compression": False
        }
        
        response = client.post("/api/v1/context/analyze", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "analysis" in data
        assert "statistics" in data
        assert "processing_time_ms" in data
        
        analysis = data["analysis"]
        assert "total_tokens" in analysis
        assert "total_items" in analysis
        assert analysis["total_items"] == len(sample_context_items)
        assert "tokens_by_type" in analysis
        assert "tokens_by_layer" in analysis
        assert "optimization_needed" in analysis
        assert "recommendations" in analysis
    
    def test_context_validation(self, client, sample_context_items):
        """Test context validation endpoint."""
        request_data = {
            "context_items": sample_context_items
        }
        
        response = client.post("/api/v1/context/validate", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "validation" in data
        
        validation = data["validation"]
        assert "is_valid" in validation
        assert "errors" in validation
        assert "warnings" in validation
        assert validation["is_valid"] is True
        assert len(validation["errors"]) == 0
    
    def test_context_management_basic(self, client, sample_context_items):
        """Test basic context management without optimization."""
        request_data = {
            "context_items": sample_context_items,
            "enable_compression": False
        }
        
        response = client.post("/api/v1/context/manage", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "analysis" in data
        assert "validation" in data
        assert "statistics" in data
        assert data["optimization"] is None  # No optimization requested
        
        # Check validation passed
        assert data["validation"]["is_valid"] is True
        
        # Check analysis results
        analysis = data["analysis"]
        assert analysis["total_tokens"] > 0
        assert analysis["total_items"] == len(sample_context_items)
    
    def test_context_management_with_optimization(self, client, large_context_items):
        """Test context management with optimization enabled."""
        request_data = {
            "context_items": large_context_items,
            "enable_compression": True,
            "target_tokens": 4000,
            "optimization_mode": "balanced"
        }
        
        response = client.post("/api/v1/context/manage", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "optimization" in data
        assert data["optimization"] is not None
        
        optimization = data["optimization"]
        assert "original_tokens" in optimization
        assert "optimized_tokens" in optimization
        assert "compression_ratio" in optimization
        assert "distillation_applied" in optimization
        
        # Should have reduced token count
        assert optimization["optimized_tokens"] < optimization["original_tokens"]
        assert optimization["compression_ratio"] < 1.0
    
    def test_context_management_validation_errors(self, client):
        """Test context management with validation errors."""
        # Missing required system context
        invalid_items = [
            {
                "content": "Some character info",
                "context_type": "character",
                "priority": 5,
                "layer_type": "working_memory"
            }
        ]
        
        request_data = {
            "context_items": invalid_items
        }
        
        response = client.post("/api/v1/context/manage", json=request_data)
        assert response.status_code == 400
        
        data = response.json()
        assert data["success"] is False
        assert "error" in data
        assert "details" in data
    
    def test_context_management_empty_request(self, client):
        """Test context management with empty context items."""
        request_data = {
            "context_items": []
        }
        
        response = client.post("/api/v1/context/manage", json=request_data)
        assert response.status_code == 422  # Pydantic validation error
    
    def test_context_management_invalid_types(self, client):
        """Test context management with invalid context types."""
        invalid_items = [
            {
                "content": "System prompt",
                "context_type": "invalid_type",
                "priority": 10,
                "layer_type": "working_memory"
            }
        ]
        
        request_data = {
            "context_items": invalid_items
        }
        
        response = client.post("/api/v1/context/manage", json=request_data)
        assert response.status_code == 422  # Pydantic validation error
    
    def test_context_management_preserve_types(self, client, sample_context_items):
        """Test context management with preserve types setting."""
        request_data = {
            "context_items": sample_context_items,
            "enable_compression": True,
            "target_tokens": 2000,
            "preserve_types": ["system", "character"]
        }
        
        response = client.post("/api/v1/context/manage", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        
        # System should always be preserved (added automatically)
        # Character should be preserved as requested
        if data["optimization"]:
            optimized_content = data["optimization"]["optimized_content"]
            assert "system" in optimized_content
            assert optimized_content["system"]  # Should not be empty
    
    def test_context_analysis_token_breakdown(self, client, sample_context_items):
        """Test detailed token breakdown in analysis."""
        request_data = {
            "context_items": sample_context_items
        }
        
        response = client.post("/api/v1/context/analyze", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        analysis = data["analysis"]
        
        # Check token breakdown by type
        tokens_by_type = analysis["tokens_by_type"]
        assert "system" in tokens_by_type
        assert "world" in tokens_by_type
        assert "character" in tokens_by_type
        assert "story" in tokens_by_type
        assert "feedback" in tokens_by_type
        
        # Check token breakdown by layer
        tokens_by_layer = analysis["tokens_by_layer"]
        assert "working_memory" in tokens_by_layer
        assert "short_term_memory" in tokens_by_layer
        assert "long_term_memory" in tokens_by_layer
        assert "episodic_memory" in tokens_by_layer
        assert "agent_specific_memory" in tokens_by_layer
        
        # Total should match sum of parts
        total_by_type = sum(tokens_by_type.values())
        total_by_layer = sum(tokens_by_layer.values())
        assert total_by_type == analysis["total_tokens"]
        assert total_by_layer == analysis["total_tokens"]
    
    def test_context_management_realistic_scenario(self, client):
        """Test context management with realistic story generation scenario."""
        # Simulate a realistic story generation context
        realistic_items = [
            {
                "content": """You are an expert creative writing assistant specializing in fantasy fiction. 
                Your role is to help generate compelling chapters that maintain character consistency, 
                advance the plot meaningfully, and create immersive scenes with rich sensory details.
                Focus on showing rather than telling, and ensure dialogue feels natural and character-appropriate.""",
                "context_type": "system",
                "priority": 10,
                "layer_type": "working_memory",
                "metadata": {"role": "writing_assistant"}
            },
            {
                "content": """The Kingdom of Valdris is a mountainous realm where ancient magic still flows through 
                crystalline formations called Heartstone Veins. The capital, Ironhold, is built into the side 
                of Mount Drakmoor, with levels carved directly into the living rock. The city is powered by 
                a massive Heartstone at its core, which also serves as the source of the kingdom's magical defenses.
                
                The current political situation is tense - King Aldric III is aging and has no clear heir, 
                leading to various noble houses positioning themselves for succession. The Mage's Guild holds 
                significant influence, as they control access to the Heartstone's power.""",
                "context_type": "world",
                "priority": 8,
                "layer_type": "long_term_memory",
                "metadata": {"world_element": "setting_politics"}
            },
            {
                "content": """Kira Stormwind - Age 28, Human Battlemage
                Physical: Tall and athletic, auburn hair usually braided for combat, green eyes, 
                distinctive scar across left cheek from training accident.
                
                Personality: Fiercely independent, quick-tempered but loyal, struggles with self-doubt 
                despite her abilities. Has a dry sense of humor and tends to use sarcasm as a defense mechanism.
                
                Background: Born to minor nobility but chose the path of a battlemage against her family's wishes. 
                Trained at the Royal Academy and now serves as a Captain in the King's Guard. 
                Secretly investigating corruption within the noble houses.
                
                Abilities: Expert in combat magic, particularly lightning and force spells. 
                Skilled swordswoman. Has an unusual ability to sense magical disturbances.""",
                "context_type": "character",
                "priority": 9,
                "layer_type": "short_term_memory",
                "metadata": {"character_name": "Kira", "role": "protagonist"}
            },
            {
                "content": """Current Story Arc: "The Heartstone Conspiracy"
                
                Kira has discovered that someone is systematically weakening the Heartstone's power by 
                introducing corrupted magical elements into the city's ley line network. This threatens 
                not only Ironhold's defenses but could destabilize the entire kingdom's magical infrastructure.
                
                Recent developments:
                - Kira found evidence linking Lord Blackthorne to the sabotage
                - The King's health is declining faster than expected
                - Strange magical creatures have been spotted in the lower city levels
                - Kira's investigation has put her at odds with her superior, Commander Thorne
                
                Current chapter goal: Kira must infiltrate Lord Blackthorne's estate during a formal dinner 
                to gather evidence, while maintaining her cover and avoiding detection by the house guards 
                and magical wards.""",
                "context_type": "story",
                "priority": 9,
                "layer_type": "episodic_memory",
                "metadata": {"arc": "heartstone_conspiracy", "chapter_goal": "infiltration"}
            },
            {
                "content": """Previous Chapter Feedback:
                - Excellent character voice for Kira - her internal monologue feels authentic
                - The magical system descriptions are clear and consistent
                - Need more sensory details in the castle scenes (sounds, smells, textures)
                - Dialogue between Kira and Commander Thorne could be more tense
                - The pacing in the investigation scenes is good, but the action sequence felt rushed
                - Consider adding more details about Kira's emotional state during confrontations""",
                "context_type": "feedback",
                "priority": 7,
                "layer_type": "agent_specific_memory",
                "metadata": {"feedback_type": "editor_review", "chapter": "previous"}
            }
        ]
        
        request_data = {
            "context_items": realistic_items,
            "enable_compression": True,
            "target_tokens": 6000,
            "optimization_mode": "balanced",
            "preserve_types": ["system", "character"]
        }
        
        response = client.post("/api/v1/context/manage", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        
        # Verify the response structure
        assert "analysis" in data
        assert "statistics" in data
        assert "validation" in data
        
        # Check that validation passed
        assert data["validation"]["is_valid"] is True
        
        # Check analysis results
        analysis = data["analysis"]
        assert analysis["total_tokens"] > 0
        assert analysis["utilization_ratio"] > 0
        
        # If optimization was applied, verify results
        if data["optimization"]:
            optimization = data["optimization"]
            assert optimization["optimized_tokens"] <= request_data["target_tokens"] * 1.1  # Allow 10% overage
            
            # Verify preserved types are present
            optimized_content = optimization["optimized_content"]
            assert optimized_content["system"]  # System should be preserved
            assert optimized_content["character"]  # Character should be preserved
    
    def test_context_management_error_handling(self, client):
        """Test error handling in context management."""
        # Test with malformed request
        response = client.post("/api/v1/context/manage", json={"invalid": "data"})
        assert response.status_code == 422
        
        # Test with empty content
        invalid_items = [
            {
                "content": "",
                "context_type": "system",
                "priority": 10,
                "layer_type": "working_memory"
            }
        ]
        
        request_data = {
            "context_items": invalid_items
        }
        
        response = client.post("/api/v1/context/manage", json=request_data)
        assert response.status_code == 422  # Pydantic validation should catch this
    
    def test_context_management_performance(self, client, sample_context_items):
        """Test context management performance metrics."""
        request_data = {
            "context_items": sample_context_items,
            "enable_compression": True,
            "target_tokens": 3000
        }
        
        response = client.post("/api/v1/context/manage", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "metadata" in data
        assert "processing_time_ms" in data["metadata"]
        
        # Processing should complete in reasonable time (less than 5 seconds)
        processing_time = data["metadata"]["processing_time_ms"]
        assert processing_time < 5000
    
    @pytest.mark.parametrize("optimization_mode", ["aggressive", "balanced", "conservative"])
    def test_optimization_modes(self, client, large_context_items, optimization_mode):
        """Test different optimization modes."""
        request_data = {
            "context_items": large_context_items,
            "enable_compression": True,
            "target_tokens": 4000,
            "optimization_mode": optimization_mode
        }
        
        response = client.post("/api/v1/context/manage", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        
        # All modes should produce some optimization
        if data["optimization"]:
            optimization = data["optimization"]
            assert optimization["optimized_tokens"] < optimization["original_tokens"]


class TestContextManagerIntegration:
    """Test integration between context management and existing endpoints."""
    
    def test_context_manager_initialization(self):
        """Test that ContextManager initializes correctly."""
        cm = ContextManager()
        assert cm.max_context_tokens > 0
        assert cm.distillation_threshold > 0
        assert cm.token_counter is not None
        assert cm.context_distiller is not None
    
    def test_context_item_conversion(self, sample_context_items):
        """Test conversion between API models and service models."""
        from app.services.context_manager import ContextItem, ContextType
        from app.services.token_management import LayerType
        
        # Convert API model to service model
        api_item = sample_context_items[0]
        service_item = ContextItem(
            content=api_item["content"],
            context_type=ContextType(api_item["context_type"]),
            priority=api_item["priority"],
            layer_type=LayerType(api_item["layer_type"]),
            metadata=api_item.get("metadata", {})
        )
        
        assert service_item.content == api_item["content"]
        assert service_item.context_type.value == api_item["context_type"]
        assert service_item.priority == api_item["priority"]
        assert service_item.layer_type.value == api_item["layer_type"]
    
    def test_token_counting_accuracy(self):
        """Test that token counting is reasonably accurate."""
        cm = ContextManager()
        
        # Test with known content
        test_content = "This is a test sentence with exactly ten words in it."
        from app.services.context_manager import ContextItem, ContextType
        from app.services.token_management import LayerType
        
        item = ContextItem(
            content=test_content,
            context_type=ContextType.SYSTEM,
            layer_type=LayerType.WORKING_MEMORY
        )
        
        analysis = cm.analyze_context([item])
        
        # Should have some reasonable token count (not zero, not excessive)
        assert analysis.total_tokens > 0
        assert analysis.total_tokens < 100  # Should be reasonable for short text
