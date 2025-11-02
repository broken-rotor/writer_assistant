"""
Worldbuilding sync API endpoints.
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime, UTC
import logging

from app.models.worldbuilding_models import (
    WorldbuildingSyncRequest,
    WorldbuildingSyncResponse,
    WorldbuildingStatusResponse
)
from app.services.worldbuilding_sync import WorldbuildingSyncService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize the worldbuilding sync service
worldbuilding_service = WorldbuildingSyncService()


@router.post("/sync", response_model=WorldbuildingSyncResponse)
async def sync_worldbuilding(request: WorldbuildingSyncRequest):
    """
    Sync worldbuilding content from chat messages.
    
    This endpoint processes chat messages to extract and update worldbuilding information,
    providing intelligent merging with existing content.
    """
    try:
        logger.info(f"Processing worldbuilding sync for story {request.story_id} with {len(request.messages)} messages")
        
        # Validate request
        if not request.story_id:
            raise HTTPException(status_code=400, detail="story_id is required")
        
        if not request.messages:
            logger.warning(f"No messages provided for story {request.story_id}, returning current content")
            # Return current content with minimal metadata
            return WorldbuildingSyncResponse(
                success=True,
                updated_worldbuilding=request.current_worldbuilding,
                metadata={
                    "story_id": request.story_id,
                    "messages_processed": 0,
                    "content_length": len(request.current_worldbuilding),
                    "topics_identified": [],
                    "sync_timestamp": datetime.now(UTC).isoformat(),
                    "quality_score": 0.5 if request.current_worldbuilding else 0.0
                },
                errors=[]
            )
        
        # Process the sync request
        response = await worldbuilding_service.sync_worldbuilding(request)
        
        logger.info(f"Worldbuilding sync completed for story {request.story_id}: "
                   f"success={response.success}, topics={len(response.metadata.topics_identified)}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in worldbuilding sync: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error during worldbuilding sync: {str(e)}"
        )


@router.get("/status/test", response_model=WorldbuildingStatusResponse)
async def test_worldbuilding_status():
    """
    Health check endpoint for worldbuilding sync functionality.
    
    Used by the frontend to test backend connectivity for worldbuilding features.
    """
    try:
        return WorldbuildingStatusResponse(
            status="ok",
            timestamp=datetime.now(UTC).isoformat(),
            version="1.0.0"
        )
    except Exception as e:
        logger.error(f"Error in worldbuilding status check: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Status check failed: {str(e)}"
        )
