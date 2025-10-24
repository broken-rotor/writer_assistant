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

    # Development settings
    DEBUG: bool = True

    # Archive settings (ChromaDB) - Optional feature
    ARCHIVE_DB_PATH: Optional[str] = Field(
        default=None,
        description="Path to ChromaDB vector database for story archive (None = disabled)"
    )
    ARCHIVE_COLLECTION_NAME: str = Field(
        default="story_archive",
        description="ChromaDB collection name for story archive"
    )

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

    # Context Management Configuration
    CONTEXT_MAX_TOKENS: int = Field(
        default=32000,
        ge=1000,
        le=100000,
        description="Maximum context window size for context management"
    )
    CONTEXT_BUFFER_TOKENS: int = Field(
        default=2000,
        ge=100,
        le=10000,
        description="Reserved tokens for generation buffer"
    )
    
    # Layer Token Allocation Ratios (must sum to <= 1.0)
    CONTEXT_LAYER_A_RATIO: float = Field(
        default=0.0625,
        ge=0.0,
        le=1.0,
        description="System instructions layer ratio (1-2k tokens)"
    )
    CONTEXT_LAYER_B_RATIO: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Immediate instructions layer ratio (included in Layer A)"
    )
    CONTEXT_LAYER_C_RATIO: float = Field(
        default=0.4375,
        ge=0.0,
        le=1.0,
        description="Recent story segment layer ratio (10-15k tokens)"
    )
    CONTEXT_LAYER_D_RATIO: float = Field(
        default=0.15625,
        ge=0.0,
        le=1.0,
        description="Character/scene data layer ratio (2-5k tokens)"
    )
    CONTEXT_LAYER_E_RATIO: float = Field(
        default=0.34375,
        ge=0.0,
        le=1.0,
        description="Plot/world summary layer ratio (5-10k tokens)"
    )
    
    # Context Management Performance Settings
    CONTEXT_SUMMARIZATION_THRESHOLD: int = Field(
        default=25000,
        ge=1000,
        le=100000,
        description="Token threshold for triggering summarization"
    )
    CONTEXT_ASSEMBLY_TIMEOUT: int = Field(
        default=100,
        ge=10,
        le=10000,
        description="Maximum context assembly time in milliseconds"
    )
    
    # Context Management Feature Toggles
    CONTEXT_ENABLE_RAG: bool = Field(
        default=True,
        description="Enable RAG-based content retrieval"
    )
    CONTEXT_ENABLE_MONITORING: bool = Field(
        default=True,
        description="Enable context management analytics and monitoring"
    )
    CONTEXT_ENABLE_CACHING: bool = Field(
        default=True,
        description="Enable context assembly result caching"
    )
    
    # Context Optimization Settings
    CONTEXT_MIN_PRIORITY_THRESHOLD: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Minimum priority threshold for content inclusion"
    )
    CONTEXT_OVERFLOW_STRATEGY: str = Field(
        default="reallocate",
        description="Strategy for handling token overflow (reject, truncate, borrow, reallocate)"
    )
    CONTEXT_ALLOCATION_MODE: str = Field(
        default="dynamic",
        description="Token allocation mode (static, dynamic, adaptive)"
    )

    def validate_layer_ratios(self) -> 'Settings':
        """Validate that layer ratios sum to <= 1.0"""
        total_ratio = (
            self.CONTEXT_LAYER_A_RATIO +
            self.CONTEXT_LAYER_B_RATIO +
            self.CONTEXT_LAYER_C_RATIO +
            self.CONTEXT_LAYER_D_RATIO +
            self.CONTEXT_LAYER_E_RATIO
        )
        if total_ratio > 1.0:
            raise ValueError(
                f"Context layer ratios sum to {total_ratio:.4f}, which exceeds 1.0. "
                f"Total allocation cannot exceed 100% of available tokens."
            )
        return self

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.validate_layer_ratios()

settings = Settings()
