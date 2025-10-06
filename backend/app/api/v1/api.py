from fastapi import APIRouter
from app.api.v1.endpoints import generation

api_router = APIRouter()
api_router.include_router(generation.router, prefix="/generate", tags=["generation"])