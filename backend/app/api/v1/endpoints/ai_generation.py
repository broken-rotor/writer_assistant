"""
AI Generation endpoints aggregator for Writer Assistant.
This file imports and combines all individual endpoint routers.
"""
from fastapi import APIRouter

# Import individual endpoint routers
from app.api.v1.endpoints.character_feedback import router as character_feedback_router
from app.api.v1.endpoints.rater_feedback import router as rater_feedback_router
from app.api.v1.endpoints.generate_chapter import router as generate_chapter_router
from app.api.v1.endpoints.modify_chapter import router as modify_chapter_router
from app.api.v1.endpoints.editor_review import router as editor_review_router
from app.api.v1.endpoints.flesh_out import router as flesh_out_router
from app.api.v1.endpoints.generate_character_details import router as generate_character_details_router
from app.api.v1.endpoints import regenerate_bio
from app.api.v1.endpoints import generate_chapter_outlines
from app.api.v1.endpoints import llm_chat

# Create main router
router = APIRouter()

# Include all endpoint routers
router.include_router(character_feedback_router, tags=["ai-generation"])
router.include_router(rater_feedback_router, tags=["ai-generation"])
router.include_router(generate_chapter_router, tags=["ai-generation"])
router.include_router(modify_chapter_router, tags=["ai-generation"])
router.include_router(editor_review_router, tags=["ai-generation"])
router.include_router(flesh_out_router, tags=["ai-generation"])
router.include_router(generate_character_details_router, tags=["ai-generation"])
router.include_router(generate_chapter_outlines.router, tags=["ai-generation"])
router.include_router(regenerate_bio.router, tags=["ai-generation"])
router.include_router(llm_chat.router, tags=["ai-generation"])
