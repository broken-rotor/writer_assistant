from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import ConfigDict, Field

class Settings(BaseSettings):
    model_config = ConfigDict(
        case_sensitive=True,
        env_file=".env"
    )

    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Writer Assistant"

    # Development settings
    DEBUG: bool = True

    # Database settings (using JSON files for MVP)
    DATA_DIR: str = "data"

    # Agent settings (legacy - may be deprecated)
    MAX_CONTEXT_LENGTH: int = 4000
    DEFAULT_TEMPERATURE: float = 0.7

    # Security settings
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # LLM Configuration
    MODEL_PATH: Optional[str] = Field(
        default=None,
        description="Path to the GGUF model file (required for LLM functionality)"
    )

    # LLM Performance Settings
    LLM_N_CTX: int = Field(
        default=4096,
        description="Context window size"
    )
    LLM_N_GPU_LAYERS: int = Field(
        default=-1,
        description="Number of GPU layers (-1 = all, 0 = CPU only)"
    )
    LLM_N_THREADS: Optional[int] = Field(
        default=None,
        description="Number of CPU threads (None = auto)"
    )

    # LLM Generation Settings
    LLM_TEMPERATURE: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (0.0-2.0)"
    )
    LLM_TOP_P: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling threshold"
    )
    LLM_TOP_K: int = Field(
        default=40,
        ge=1,
        description="Top-k sampling parameter"
    )
    LLM_MAX_TOKENS: int = Field(
        default=2048,
        ge=1,
        description="Maximum tokens to generate"
    )
    LLM_REPEAT_PENALTY: float = Field(
        default=1.1,
        ge=1.0,
        le=2.0,
        description="Penalty for repeating tokens"
    )
    LLM_VERBOSE: bool = Field(
        default=False,
        description="Enable verbose logging for model"
    )

settings = Settings()