from fastapi import APIRouter
from app.api.v1.endpoints import ai_generation
from app.api.v1.endpoints import archive
from app.api.v1.endpoints import tokens
from app.api.v1.endpoints import agentic_modify_chapter

api_router = APIRouter()
api_router.include_router(ai_generation.router, tags=["ai-generation"])
api_router.include_router(agentic_modify_chapter.router, tags=["agentic"])
api_router.include_router(archive.router, prefix="/archive", tags=["archive"])
api_router.include_router(tokens.router, prefix="/tokens", tags=["tokens"])
