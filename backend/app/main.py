import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.config import settings
from app.services.llm_inference import initialize_llm, LLMInferenceConfig, get_llm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Track LLM loading state
llm_loading = False
llm_load_error: str | None = None


async def load_llm_async():
    """Load LLM asynchronously in the background."""
    global llm_loading, llm_load_error

    config = LLMInferenceConfig.from_settings(settings)
    if not config:
        logger.info("No MODEL_PATH configured in settings. LLM functionality will not be available.")
        return

    llm_loading = True
    logger.info(f"Starting LLM initialization with model: {config.model_path}")

    try:
        # Run LLM initialization in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, initialize_llm, config)
        logger.info("LLM initialized successfully")
        llm_loading = False
    except Exception as e:
        logger.exception(f"Failed to initialize LLM: {e}")
        llm_load_error = str(e)
        llm_loading = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup: Start LLM loading in background
    asyncio.create_task(load_llm_async())
    logger.info("Server started. LLM loading in background...")

    yield

    # Shutdown: Cleanup if needed
    logger.info("Server shutting down")


app = FastAPI(
    title="Writer Assistant API",
    description="Multi-agent AI system for collaborative storytelling",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Angular dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    llm = get_llm()
    if llm_loading:
        llm_status = "loading"
    elif llm_load_error:
        llm_status = f"error: {llm_load_error}"
    elif llm:
        llm_status = "available"
    else:
        llm_status = "not configured"

    return {
        "message": "Writer Assistant API",
        "version": "1.0.0",
        "llm_status": llm_status
    }


@app.get("/health")
async def health_check():
    llm = get_llm()
    return {
        "status": "healthy",
        "llm_available": llm is not None,
        "llm_loading": llm_loading,
        "llm_error": llm_load_error
    }
