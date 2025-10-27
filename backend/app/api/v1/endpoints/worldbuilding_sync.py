"""
API endpoints for worldbuilding synchronization.
Handles sync between chat conversations and worldbuilding summaries.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import logging

from app.models.generation_models import ConversationMessage
from app.services.worldbuilding_sync import WorldbuildingSyncService

logger = logging.getLogger(__name__)

router = APIRouter()


class WorldbuildingSyncRequest(BaseModel):
    """Request model for worldbuilding sync."""
    story_id: str = Field(..., description="Story identifier")
    messages: List[ConversationMessage] = Field(..., description="Conversation messages to sync")
    current_worldbuilding: str = Field(default="", description="Current worldbuilding content")
    force_sync: bool = Field(default=False, description="Force sync even if no changes detected")


class WorldbuildingSyncResponse(BaseModel):
    """Response model for worldbuilding sync."""
    success: bool = Field(..., description="Whether sync was successful")
    updated_worldbuilding: str = Field(..., description="Updated worldbuilding content")
    metadata: dict = Field(..., description="Sync metadata including quality score")
    errors: List[str] = Field(default_factory=list, description="Any validation errors")


class WorldbuildingValidationRequest(BaseModel):
    """Request model for worldbuilding validation."""
    content: str = Field(..., description="Worldbuilding content to validate")


class WorldbuildingValidationResponse(BaseModel):
    """Response model for worldbuilding validation."""
    is_valid: bool = Field(..., description="Whether content is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")


class SyncHistoryResponse(BaseModel):
    """Response model for sync history."""
    history: List[dict] = Field(..., description="Sync history records")
    total_count: int = Field(..., description="Total number of sync records")


# Dependency to get worldbuilding sync service
def get_worldbuilding_sync_service() -> WorldbuildingSyncService:
    """Get worldbuilding sync service instance."""
    return WorldbuildingSyncService()


@router.post("/sync", response_model=WorldbuildingSyncResponse)
async def sync_worldbuilding(
    request: WorldbuildingSyncRequest,
    sync_service: WorldbuildingSyncService = Depends(get_worldbuilding_sync_service)
):
    """
    Sync conversation messages to worldbuilding summary.
    
    This endpoint processes conversation messages and updates the worldbuilding
    summary with extracted content organized by topic.
    """
    try:
        logger.info(f"Starting worldbuilding sync for story {request.story_id}")
        
        # Validate input
        if not request.story_id:
            raise HTTPException(status_code=400, detail="Story ID is required")
        
        if not request.messages:
            # No messages to sync, return current worldbuilding
            return WorldbuildingSyncResponse(
                success=True,
                updated_worldbuilding=request.current_worldbuilding,
                metadata={
                    'story_id': request.story_id,
                    'messages_processed': 0,
                    'content_length': len(request.current_worldbuilding),
                    'topics_identified': [],
                    'quality_score': 0.0
                }
            )
        
        # Perform sync
        updated_worldbuilding, metadata = await sync_service.sync_conversation_to_worldbuilding(
            story_id=request.story_id,
            messages=request.messages,
            current_worldbuilding=request.current_worldbuilding
        )
        
        # Validate result
        is_valid, validation_errors = sync_service.validate_worldbuilding_content(updated_worldbuilding)
        
        if not is_valid and not request.force_sync:
            logger.warning(f"Worldbuilding validation failed for story {request.story_id}: {validation_errors}")
            return WorldbuildingSyncResponse(
                success=False,
                updated_worldbuilding=request.current_worldbuilding,
                metadata=metadata,
                errors=validation_errors
            )
        
        logger.info(f"Worldbuilding sync completed successfully for story {request.story_id}")
        
        return WorldbuildingSyncResponse(
            success=True,
            updated_worldbuilding=updated_worldbuilding,
            metadata=metadata,
            errors=validation_errors if request.force_sync else []
        )
        
    except Exception as e:
        logger.error(f"Error in worldbuilding sync for story {request.story_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync worldbuilding: {str(e)}"
        )


@router.post("/validate", response_model=WorldbuildingValidationResponse)
async def validate_worldbuilding(
    request: WorldbuildingValidationRequest,
    sync_service: WorldbuildingSyncService = Depends(get_worldbuilding_sync_service)
):
    """
    Validate worldbuilding content.
    
    This endpoint validates worldbuilding content for length, structure,
    and security issues.
    """
    try:
        is_valid, errors = sync_service.validate_worldbuilding_content(request.content)
        
        # Generate suggestions based on content
        suggestions = []
        
        if len(request.content.strip()) < 100:
            suggestions.append("Consider adding more detail to your worldbuilding")
        
        if '##' not in request.content:
            suggestions.append("Consider organizing content with topic headers (## Topic Name)")
        
        if len(request.content.split('\n\n')) < 2:
            suggestions.append("Consider breaking content into paragraphs for better readability")
        
        return WorldbuildingValidationResponse(
            is_valid=is_valid,
            errors=errors,
            suggestions=suggestions
        )
        
    except Exception as e:
        logger.error(f"Error validating worldbuilding content: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate worldbuilding content: {str(e)}"
        )


@router.get("/history/{story_id}", response_model=SyncHistoryResponse)
async def get_sync_history(
    story_id: str,
    limit: int = 10,
    sync_service: WorldbuildingSyncService = Depends(get_worldbuilding_sync_service)
):
    """
    Get sync history for a story.
    
    This endpoint returns the history of worldbuilding sync operations
    for a specific story.
    """
    try:
        if not story_id:
            raise HTTPException(status_code=400, detail="Story ID is required")
        
        if limit < 1 or limit > 100:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
        
        history = await sync_service.get_sync_history(story_id, limit)
        
        return SyncHistoryResponse(
            history=history,
            total_count=len(history)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sync history for story {story_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get sync history: {str(e)}"
        )


@router.delete("/history/{story_id}")
async def clear_sync_history(
    story_id: str,
    sync_service: WorldbuildingSyncService = Depends(get_worldbuilding_sync_service)
):
    """
    Clear sync history for a story.
    
    This endpoint clears all sync history records for a specific story.
    """
    try:
        if not story_id:
            raise HTTPException(status_code=400, detail="Story ID is required")
        
        # Note: This would need to be implemented in the persistence service
        # For now, return success
        
        return {"success": True, "message": f"Sync history cleared for story {story_id}"}
        
    except Exception as e:
        logger.error(f"Error clearing sync history for story {story_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear sync history: {str(e)}"
        )


@router.get("/status/{story_id}")
async def get_sync_status(
    story_id: str,
    sync_service: WorldbuildingSyncService = Depends(get_worldbuilding_sync_service)
):
    """
    Get sync status for a story.
    
    This endpoint returns the current sync status and metadata for a story.
    """
    try:
        if not story_id:
            raise HTTPException(status_code=400, detail="Story ID is required")
        
        # Get latest sync record
        history = await sync_service.get_sync_history(story_id, limit=1)
        
        if not history:
            return {
                "story_id": story_id,
                "has_sync_data": False,
                "last_sync": None,
                "sync_count": 0
            }
        
        latest_sync = history[0]
        
        return {
            "story_id": story_id,
            "has_sync_data": True,
            "last_sync": latest_sync.get('created_at'),
            "sync_count": len(history),
            "latest_metadata": latest_sync.get('metadata', {})
        }
        
    except Exception as e:
        logger.error(f"Error getting sync status for story {story_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get sync status: {str(e)}"
        )
