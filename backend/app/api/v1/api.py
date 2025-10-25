from fastapi import APIRouter
from app.api.v1.endpoints import ai_generation
from app.api.v1.endpoints import archive
from app.api.v1.endpoints import tokens

api_router = APIRouter()
api_router.include_router(ai_generation.router, tags=["ai-generation"])
api_router.include_router(archive.router, prefix="/archive", tags=["archive"])
api_router.include_router(tokens.router, prefix="/tokens", tags=["tokens"])
