"""
Integration tests for worldbuilding chat to data model integration.
Tests the complete pipeline from chat messages to worldbuilding summaries.
"""
import pytest
import asyncio
from datetime import datetime, UTC
from typing import List

from app.models.generation_models import ConversationMessage
from app.services.worldbuilding_sync import WorldbuildingSyncService
from app.services.worldbuilding_validator import WorldbuildingValidator
from app.services.worldbuilding_persistence import WorldbuildingPersistenceService


class TestWorldbuildingIntegration:
    """Integration tests for worldbuilding sync pipeline."""
    
    @pytest.fixture
    def sync_service(self, persistence_service):
        """Create a worldbuilding sync service for testing."""
        return WorldbuildingSyncService(persistence=persistence_service)
    
    @pytest.fixture
    def validator(self):
        """Create a worldbuilding validator for testing."""
        return WorldbuildingValidator()
    
    @pytest.fixture
    def persistence_service(self, tmp_path):
        """Create a persistence service for testing."""
        storage_path = tmp_path / "worldbuilding_conversations"
        return WorldbuildingPersistenceService(storage_path=str(storage_path))
    
    @pytest.fixture
    def sample_messages(self) -> List[ConversationMessage]:
        """Create sample conversation messages for testing."""
        return [
            ConversationMessage(
                role="user",
                content="My world is called Aethermoor. It's a floating island kingdom suspended in the clouds by ancient magic crystals.",
                timestamp=datetime.now(UTC).isoformat()
            ),
            ConversationMessage(
                role="assistant",
                content="Aethermoor sounds fascinating! The floating islands create unique geographical challenges. How do people travel between the islands? Are there sky ships or magical bridges?",
                timestamp=datetime.now(UTC).isoformat()
            ),
            ConversationMessage(
                role="user",
                content="They use sky ships powered by wind crystals. The main city, Nimbusgarde, is built around the largest crystal formation. The society is divided into three castes: the Crystal Keepers who maintain the magic, the Sky Sailors who handle transportation, and the Cloud Farmers who grow crops in floating gardens.",
                timestamp=datetime.now(UTC).isoformat()
            ),
            ConversationMessage(
                role="assistant",
                content="This creates an interesting social structure! The Crystal Keepers would likely hold significant political power since they maintain what keeps the islands afloat. How does this caste system affect daily life and governance in Aethermoor?",
                timestamp=datetime.now(UTC).isoformat()
            ),
            ConversationMessage(
                role="user",
                content="The Crystal Keepers rule through a council called the Luminous Assembly. They make all major decisions about crystal usage and island positioning. There's growing tension because the Sky Sailors want more representation, especially since they control trade routes.",
                timestamp=datetime.now(UTC).isoformat()
            )
        ]
    
    @pytest.mark.asyncio
    async def test_complete_sync_pipeline(self, sync_service, sample_messages):
        """Test the complete sync pipeline from messages to worldbuilding."""
        
        story_id = "test_story_001"
        current_worldbuilding = ""
        
        # Perform sync
        updated_worldbuilding, metadata = await sync_service.sync_conversation_to_worldbuilding(
            story_id=story_id,
            messages=sample_messages,
            current_worldbuilding=current_worldbuilding
        )
        
        # Verify results
        assert updated_worldbuilding is not None
        assert len(updated_worldbuilding) > 0
        assert metadata is not None
        assert metadata['story_id'] == story_id
        assert metadata['messages_processed'] == len(sample_messages)
        assert metadata['quality_score'] > 0
        
        # Check that worldbuilding contains expected content
        assert 'Aethermoor' in updated_worldbuilding
        assert 'Nimbusgarde' in updated_worldbuilding
        assert 'Crystal Keepers' in updated_worldbuilding
        
        # Verify structure
        assert '##' in updated_worldbuilding  # Should have topic headers
    
    @pytest.mark.asyncio
    async def test_incremental_sync(self, sync_service, sample_messages):
        """Test incremental sync with existing worldbuilding content."""
        
        story_id = "test_story_002"
        
        # Initial sync with first 3 messages
        initial_messages = sample_messages[:3]
        initial_worldbuilding, _ = await sync_service.sync_conversation_to_worldbuilding(
            story_id=story_id,
            messages=initial_messages,
            current_worldbuilding=""
        )
        
        # Incremental sync with remaining messages
        remaining_messages = sample_messages[3:]
        updated_worldbuilding, metadata = await sync_service.sync_conversation_to_worldbuilding(
            story_id=story_id,
            messages=remaining_messages,
            current_worldbuilding=initial_worldbuilding
        )
        
        # Verify incremental update
        assert len(updated_worldbuilding) > len(initial_worldbuilding)
        assert 'Luminous Assembly' in updated_worldbuilding
        assert 'Sky Sailors' in updated_worldbuilding
        
        # Should contain content from both syncs
        assert 'Aethermoor' in updated_worldbuilding
        assert 'Crystal Keepers' in updated_worldbuilding
    
    @pytest.mark.asyncio
    async def test_validation_integration(self, sync_service, validator, sample_messages):
        """Test integration with validation service."""
        
        story_id = "test_story_003"
        
        # Perform sync
        updated_worldbuilding, _ = await sync_service.sync_conversation_to_worldbuilding(
            story_id=story_id,
            messages=sample_messages,
            current_worldbuilding=""
        )
        
        # Validate the result
        is_valid, errors = sync_service.validate_worldbuilding_content(updated_worldbuilding)
        
        assert is_valid is True
        assert len(errors) == 0
        
        # Test validator directly
        validation_result = validator.validate_content(updated_worldbuilding)
        assert validation_result.is_valid is True
        
        # Get content statistics
        stats = validator.get_content_statistics(updated_worldbuilding)
        assert stats['word_count'] > 0
        assert stats['character_count'] > 0
        assert len(stats['topics_identified']) > 0
    
    @pytest.mark.asyncio
    async def test_persistence_integration(self, sync_service, persistence_service, sample_messages):
        """Test integration with persistence service."""
        
        story_id = "test_story_004"
        
        # Perform sync (this should store the result)
        updated_worldbuilding, metadata = await sync_service.sync_conversation_to_worldbuilding(
            story_id=story_id,
            messages=sample_messages,
            current_worldbuilding=""
        )
        
        # Verify sync history was stored
        history = await sync_service.get_sync_history(story_id, limit=5)
        
        assert len(history) > 0
        latest_sync = history[-1]
        assert latest_sync['story_id'] == story_id
        assert 'worldbuilding_content' in latest_sync
        assert 'metadata' in latest_sync
    
    @pytest.mark.asyncio
    async def test_error_handling(self, sync_service):
        """Test error handling in sync pipeline."""
        
        story_id = "test_story_005"
        
        # Test with empty messages
        empty_messages = []
        result, metadata = await sync_service.sync_conversation_to_worldbuilding(
            story_id=story_id,
            messages=empty_messages,
            current_worldbuilding="Existing content"
        )
        
        # Should return existing content when no messages
        assert result == "Existing content"
        assert metadata['messages_processed'] == 0
        
        # Test with invalid content
        invalid_messages = [
            ConversationMessage(
                role="user",
                content="<script>alert('xss')</script>",
                timestamp=datetime.now(UTC).isoformat()
            )
        ]
        
        result, _ = await sync_service.sync_conversation_to_worldbuilding(
            story_id=story_id,
            messages=invalid_messages,
            current_worldbuilding=""
        )
        
        # Should handle dangerous content
        assert '<script>' not in result
    
    @pytest.mark.asyncio
    async def test_content_quality_scoring(self, sync_service, sample_messages):
        """Test quality scoring of extracted content."""
        
        story_id = "test_story_006"
        
        # Test with high-quality messages
        updated_worldbuilding, metadata = await sync_service.sync_conversation_to_worldbuilding(
            story_id=story_id,
            messages=sample_messages,
            current_worldbuilding=""
        )
        
        quality_score = metadata['quality_score']
        assert 0.0 <= quality_score <= 1.0
        assert quality_score > 0.3  # Should be reasonably high for good content
        
        # Test with low-quality messages
        low_quality_messages = [
            ConversationMessage(
                role="user",
                content="yes",
                timestamp=datetime.now(UTC).isoformat()
            ),
            ConversationMessage(
                role="assistant",
                content="ok",
                timestamp=datetime.now(UTC).isoformat()
            )
        ]
        
        _, low_quality_metadata = await sync_service.sync_conversation_to_worldbuilding(
            story_id=story_id,
            messages=low_quality_messages,
            current_worldbuilding=""
        )
        
        low_quality_score = low_quality_metadata['quality_score']
        assert low_quality_score < quality_score  # Should be lower than high-quality content
    
    @pytest.mark.asyncio
    async def test_topic_classification(self, sync_service, sample_messages):
        """Test topic classification in sync process."""
        
        story_id = "test_story_007"
        
        updated_worldbuilding, metadata = await sync_service.sync_conversation_to_worldbuilding(
            story_id=story_id,
            messages=sample_messages,
            current_worldbuilding=""
        )
        
        topics_identified = metadata['topics_identified']
        
        # Should identify relevant topics
        assert len(topics_identified) > 0
        
        # Check for expected topic categories
        worldbuilding_content_lower = updated_worldbuilding.lower()
        
        # Should contain geography-related content
        assert any(geo_term in worldbuilding_content_lower 
                  for geo_term in ['island', 'floating', 'cloud', 'sky'])
        
        # Should contain culture/society-related content
        assert any(culture_term in worldbuilding_content_lower 
                  for culture_term in ['caste', 'society', 'keeper', 'sailor'])
        
        # Should contain politics-related content
        assert any(politics_term in worldbuilding_content_lower 
                  for politics_term in ['council', 'assembly', 'rule', 'governance'])
    
    @pytest.mark.asyncio
    async def test_concurrent_sync_operations(self, sync_service, sample_messages):
        """Test handling of concurrent sync operations."""
        
        story_id = "test_story_008"
        
        # Start multiple sync operations concurrently
        tasks = []
        for i in range(3):
            task = sync_service.sync_conversation_to_worldbuilding(
                story_id=f"{story_id}_{i}",
                messages=sample_messages,
                current_worldbuilding=""
            )
            tasks.append(task)
        
        # Wait for all to complete
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert len(results) == 3
        for result, metadata in results:
            assert result is not None
            assert len(result) > 0
            assert metadata is not None
    
    def test_sanitization_integration(self, validator):
        """Test content sanitization integration."""
        
        dangerous_content = """
        <script>alert('xss')</script>
        My world has javascript:void(0) links.
        <div onclick="malicious()">Click me</div>
        Normal worldbuilding content here.
        """
        
        sanitized = validator.sanitize_content(dangerous_content)
        
        # Should remove dangerous content
        assert '<script>' not in sanitized
        assert 'javascript:' not in sanitized
        assert 'onclick=' not in sanitized
        
        # Should preserve normal content
        assert 'Normal worldbuilding content' in sanitized
    
    def test_suggestion_generation(self, validator):
        """Test improvement suggestion generation."""
        
        # Test with minimal content
        minimal_content = "A world."
        suggestions = validator.suggest_improvements(minimal_content)
        
        assert len(suggestions) > 0
        assert any('more detail' in suggestion.lower() for suggestion in suggestions)
        
        # Test with well-structured content
        good_content = """
        ## Geography
        The world of Aethermoor consists of floating islands suspended in the clouds.
        
        ## Culture
        The society is organized into three main castes with distinct roles.
        
        ## Politics
        Governance is handled by the Luminous Assembly of Crystal Keepers.
        """
        
        good_suggestions = validator.suggest_improvements(good_content)
        
        # Should have fewer suggestions for well-structured content
        assert len(good_suggestions) <= len(suggestions)
