from fastapi import APIRouter
from app.api.v1.endpoints import ai_generation

api_router = APIRouter()
api_router.include_router(ai_generation.router, tags=["ai-generation"])