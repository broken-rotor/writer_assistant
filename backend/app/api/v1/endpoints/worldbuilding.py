"""
Worldbuilding sync API endpoints.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime, UTC
import logging
import json
import asyncio

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


@router.post("/sync")
async def sync_worldbuilding(request: WorldbuildingSyncRequest):
    """
    Sync worldbuilding content from chat messages using Server-Sent Events streaming.
    
    This endpoint processes chat messages to extract and update worldbuilding information,
    providing real-time progress updates during processing.
    """
    async def generate_with_updates():
        try:
            # Validate request
            if not request.story_id:
                yield f"data: {json.dumps({'type': 'error', 'message': 'story_id is required'})}\n\n"
                return
            
            if not request.messages:
                logger.warning(f"No messages provided for story {request.story_id}, returning current content")
                result = WorldbuildingSyncResponse(
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
                yield f"data: {json.dumps({'type': 'result', 'data': result.dict(), 'status': 'complete'})}\n\n"
                return
            
            logger.info(f"Processing worldbuilding sync for story {request.story_id} with {len(request.messages)} messages")
            
            # Phase 1: Message Processing
            yield f"data: {json.dumps({'type': 'status', 'phase': 'message_processing', 'message': f'Processing {len(request.messages)} chat messages...', 'progress': 20})}\n\n"
            await asyncio.sleep(0.1)  # Small delay to ensure streaming works
            
            # Phase 2: Extracting
            yield f"data: {json.dumps({'type': 'status', 'phase': 'extracting', 'message': 'Extracting worldbuilding information...', 'progress': 50})}\n\n"
            await asyncio.sleep(0.1)
            
            # Phase 3: Merging
            yield f"data: {json.dumps({'type': 'status', 'phase': 'merging', 'message': 'Merging with existing worldbuilding content...', 'progress': 75})}\n\n"
            await asyncio.sleep(0.1)
            
            # Process the sync request using the worldbuilding service
            response = await worldbuilding_service.sync_worldbuilding(request)
            
            # Phase 4: Quality Assessment
            yield f"data: {json.dumps({'type': 'status', 'phase': 'quality_assessment', 'message': 'Assessing content quality...', 'progress': 90})}\n\n"
            await asyncio.sleep(0.1)
            
            logger.info(f"Worldbuilding sync completed for story {request.story_id}: "
                       f"success={response.success}, topics={len(response.metadata.topics_identified)}")
            
            yield f"data: {json.dumps({'type': 'result', 'data': response.dict(), 'status': 'complete'})}\n\n"
            
        except HTTPException as e:
            yield f"data: {json.dumps({'type': 'error', 'message': e.detail})}\n\n"
        except Exception as e:
            logger.error(f"Unexpected error in worldbuilding sync: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': f'Internal server error during worldbuilding sync: {str(e)}'})}\n\n"
    
    return StreamingResponse(
        generate_with_updates(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
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
