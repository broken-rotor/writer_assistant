from fastapi import APIRouter
from app.api.v1.endpoints import ai_generation
from app.api.v1.endpoints import archive
from app.api.v1.endpoints import tokens
from app.api.v1.endpoints import llm_chat
from app.api.v1.endpoints import phase_validation
from app.api.v1.endpoints import worldbuilding_sync

api_router = APIRouter()
api_router.include_router(ai_generation.router, tags=["ai-generation"])
api_router.include_router(archive.router, prefix="/archive", tags=["archive"])
api_router.include_router(tokens.router, prefix="/tokens", tags=["tokens"])
api_router.include_router(llm_chat.router, tags=["llm-chat"])
api_router.include_router(phase_validation.router, tags=["phase-validation"])
api_router.include_router(worldbuilding_sync.router, prefix="/worldbuilding", tags=["worldbuilding-sync"])
