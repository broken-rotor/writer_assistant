"""
Tests for chapter outline generation endpoint.
"""
import pytest
import json
from fastapi.testclient import TestClient


class TestGenerateChapterOutlineEndpoint:
    """Test chapter outline generation endpoint"""

    def test_generate_chapter_outlines_success(self, client, sample_chapter_outline_request):
        """Test successful chapter outline generation"""
        response = client.post("/api/v1/generate-chapter-outlines", json=sample_chapter_outline_request)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "outline_items" in data
        assert "summary" in data
        assert "context_metadata" in data
        
        # Check outline items
        assert isinstance(data["outline_items"], list)
        assert len(data["outline_items"]) > 0
        
        # Check first outline item structure
        first_item = data["outline_items"][0]
        assert "id" in first_item
        assert "title" in first_item
        assert "description" in first_item
        assert "involved_characters" in first_item
        assert "order" in first_item
        assert first_item["type"] == "chapter"
        assert first_item["status"] == "draft"

    def test_generate_chapter_outlines_response_structure(self, client, sample_chapter_outline_request):
        """Test chapter outline generation response structure"""
        response = client.post("/api/v1/generate-chapter-outlines", json=sample_chapter_outline_request)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate outline items structure
        for item in data["outline_items"]:
            assert isinstance(item["id"], str)
            assert isinstance(item["title"], str)
            assert isinstance(item["description"], str)
            assert isinstance(item["involved_characters"], list)
            assert isinstance(item["order"], int)
            assert item["type"] == "chapter"
            assert item["status"] == "draft"
            
        # Validate summary
        assert isinstance(data["summary"], str)
        assert len(data["summary"]) > 0
        
        # Validate context metadata
        metadata = data["context_metadata"]
        assert isinstance(metadata, dict)
        assert "generation_timestamp" in metadata
        assert "source_outline_length" in metadata
        assert "generated_chapters" in metadata

    def test_generate_chapter_outlines_with_character_contexts(self, client, sample_chapter_outline_request):
        """Test chapter outline generation with character contexts"""
        response = client.post("/api/v1/generate-chapter-outlines", json=sample_chapter_outline_request)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have outline items with involved characters
        assert len(data["outline_items"]) > 0
        
        # Check that characters from the request appear in involved_characters
        all_involved_characters = []
        for item in data["outline_items"]:
            all_involved_characters.extend(item["involved_characters"])
        
        # Should have some character involvement
        assert len(all_involved_characters) > 0

    def test_generate_chapter_outlines_with_legacy_characters(self, client, sample_chapter_outline_request):
        """Test chapter outline generation with legacy character format"""
        # Remove character_contexts to test legacy fallback
        request = sample_chapter_outline_request.copy()
        request["character_contexts"] = []
        
        response = client.post("/api/v1/generate-chapter-outlines", json=request)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should still generate outline items
        assert len(data["outline_items"]) > 0
        
        # Should have involved characters from legacy format
        all_involved_characters = []
        for item in data["outline_items"]:
            all_involved_characters.extend(item["involved_characters"])
        
        assert len(all_involved_characters) > 0

    def test_generate_chapter_outlines_with_system_prompts(self, client, sample_chapter_outline_request_with_system_prompts):
        """Test chapter outline generation with system prompts"""
        response = client.post("/api/v1/generate-chapter-outlines", json=sample_chapter_outline_request_with_system_prompts)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should generate outline items successfully
        assert len(data["outline_items"]) > 0
        assert isinstance(data["summary"], str)
        assert len(data["summary"]) > 0

    def test_generate_chapter_outlines_without_system_prompts(self, client, sample_chapter_outline_request):
        """Test chapter outline generation without system prompts (backward compatibility)"""
        # Ensure no system_prompts field
        request = sample_chapter_outline_request.copy()
        if "system_prompts" in request:
            del request["system_prompts"]
        
        response = client.post("/api/v1/generate-chapter-outlines", json=request)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should still work without system prompts
        assert len(data["outline_items"]) > 0

    def test_generate_chapter_outlines_with_empty_system_prompts(self, client, sample_chapter_outline_request):
        """Test chapter outline generation with empty system prompts"""
        request = sample_chapter_outline_request.copy()
        request["system_prompts"] = {
            "mainPrefix": "",
            "mainSuffix": "",
            "assistantPrompt": "",
            "editorPrompt": ""
        }
        
        response = client.post("/api/v1/generate-chapter-outlines", json=request)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should work with empty system prompts
        assert len(data["outline_items"]) > 0

    def test_generate_chapter_outlines_with_partial_system_prompts(self, client, sample_chapter_outline_request):
        """Test chapter outline generation with partial system prompts"""
        request = sample_chapter_outline_request.copy()
        request["system_prompts"] = {
            "mainPrefix": "Focus on character development.",
            "mainSuffix": "",  # Empty suffix
            "assistantPrompt": "You are a creative writing assistant.",
            "editorPrompt": ""  # Empty editor prompt
        }
        
        response = client.post("/api/v1/generate-chapter-outlines", json=request)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should work with partial system prompts
        assert len(data["outline_items"]) > 0

    def test_generate_chapter_outlines_empty_story_outline(self, client, sample_chapter_outline_request):
        """Test chapter outline generation with empty story outline"""
        request = sample_chapter_outline_request.copy()
        request["story_outline"] = ""
        
        response = client.post("/api/v1/generate-chapter-outlines", json=request)
        
        assert response.status_code == 400
        assert "Story outline cannot be empty" in response.json()["detail"]

    def test_generate_chapter_outlines_whitespace_only_story_outline(self, client, sample_chapter_outline_request):
        """Test chapter outline generation with whitespace-only story outline"""
        request = sample_chapter_outline_request.copy()
        request["story_outline"] = "   \n\t   "
        
        response = client.post("/api/v1/generate-chapter-outlines", json=request)
        
        assert response.status_code == 400
        assert "Story outline cannot be empty" in response.json()["detail"]

    def test_generate_chapter_outlines_missing_required_fields(self, client):
        """Test chapter outline generation with missing required fields"""
        # Missing story_outline
        response = client.post("/api/v1/generate-chapter-outlines", json={})
        
        assert response.status_code == 422  # Validation error

    def test_generate_chapter_outlines_minimal_request(self, client):
        """Test chapter outline generation with minimal request"""
        minimal_request = {
            "story_outline": "A simple detective story about solving a murder case."
        }
        
        response = client.post("/api/v1/generate-chapter-outlines", json=minimal_request)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should work with minimal request
        assert len(data["outline_items"]) > 0
        assert isinstance(data["summary"], str)

    def test_generate_chapter_outlines_with_story_context_only(self, client):
        """Test chapter outline generation with story context but no character contexts"""
        request = {
            "story_outline": "A detective investigates a murder in 1940s Los Angeles.",
            "story_context": {
                "title": "Noir Mystery",
                "worldbuilding": "1940s Los Angeles",
                "characters": [
                    {
                        "name": "Detective Smith",
                        "basicBio": "A hardboiled detective"
                    }
                ]
            }
        }
        
        response = client.post("/api/v1/generate-chapter-outlines", json=request)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should work with story context only
        assert len(data["outline_items"]) > 0

    def test_generate_chapter_outlines_with_generation_preferences(self, client, sample_chapter_outline_request):
        """Test chapter outline generation with generation preferences"""
        request = sample_chapter_outline_request.copy()
        request["generation_preferences"] = {
            "chapter_count": 10,
            "pacing": "fast",
            "focus": "action"
        }
        
        response = client.post("/api/v1/generate-chapter-outlines", json=request)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should work with generation preferences
        assert len(data["outline_items"]) > 0

    def test_generate_chapter_outlines_order_sequence(self, client, sample_chapter_outline_request):
        """Test that chapter outline items have correct order sequence"""
        response = client.post("/api/v1/generate-chapter-outlines", json=sample_chapter_outline_request)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check that order values are sequential starting from 1
        orders = [item["order"] for item in data["outline_items"]]
        orders.sort()
        
        assert orders == list(range(1, len(orders) + 1))

    def test_generate_chapter_outlines_unique_ids(self, client, sample_chapter_outline_request):
        """Test that chapter outline items have unique IDs"""
        response = client.post("/api/v1/generate-chapter-outlines", json=sample_chapter_outline_request)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check that all IDs are unique
        ids = [item["id"] for item in data["outline_items"]]
        assert len(ids) == len(set(ids))

    def test_generate_chapter_outlines_metadata_content(self, client, sample_chapter_outline_request):
        """Test chapter outline generation metadata content"""
        response = client.post("/api/v1/generate-chapter-outlines", json=sample_chapter_outline_request)
        
        assert response.status_code == 200
        data = response.json()
        
        metadata = data["context_metadata"]
        
        # Check metadata fields
        assert isinstance(metadata["generation_timestamp"], str)
        assert isinstance(metadata["source_outline_length"], int)
        assert isinstance(metadata["generated_chapters"], int)
        assert metadata["source_outline_length"] > 0
        assert metadata["generated_chapters"] > 0
        assert metadata["generated_chapters"] == len(data["outline_items"])

    def test_generate_chapter_outlines_character_involvement_tracking(self, client, sample_chapter_outline_request):
        """Test that character involvement is properly tracked"""
        response = client.post("/api/v1/generate-chapter-outlines", json=sample_chapter_outline_request)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check that involved_characters lists are not empty for most chapters
        non_empty_character_lists = [
            item for item in data["outline_items"] 
            if len(item["involved_characters"]) > 0
        ]
        
        # Most chapters should have character involvement
        assert len(non_empty_character_lists) > 0

    def test_generate_chapter_outlines_title_description_quality(self, client, sample_chapter_outline_request):
        """Test that generated titles and descriptions meet quality standards"""
        response = client.post("/api/v1/generate-chapter-outlines", json=sample_chapter_outline_request)
        
        assert response.status_code == 200
        data = response.json()
        
        for item in data["outline_items"]:
            # Titles should be meaningful (not just "Chapter X")
            assert len(item["title"]) > 5
            assert not item["title"].startswith("Chapter ")
            
            # Descriptions should be substantial
            assert len(item["description"]) > 20
            
            # Should not contain placeholder text
            assert "TODO" not in item["title"]
            assert "TODO" not in item["description"]

