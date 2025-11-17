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
    LLM_CACHE_CAPACITY: int = Field(
        default=2*(1024**3),
        description="LLM prefix cache size (bytes); 0 to disable.")

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
    LLM_VERBOSE_GENERATION: bool = Field(
        default=False,
        description="Enable verbose logging of prompts, messages, and outputs during generation"
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

    # Layer Token Allocation Limits (absolute token numbers)
    CONTEXT_LAYER_A_TOKENS: int = Field(
        default=2000,
        ge=100,
        le=10000,
        description="System instructions layer tokens (1-2k tokens)"
    )
    CONTEXT_LAYER_B_TOKENS: int = Field(
        default=0,
        ge=0,
        le=5000,
        description="Immediate instructions layer tokens (included in Layer A)"
    )
    CONTEXT_LAYER_C_TOKENS: int = Field(
        default=13000,
        ge=1000,
        le=25000,
        description="Recent story segment layer tokens (10-15k tokens)"
    )
    CONTEXT_LAYER_D_TOKENS: int = Field(
        default=5000,
        ge=500,
        le=10000,
        description="Character/scene data layer tokens (2-5k tokens)"
    )
    CONTEXT_LAYER_E_TOKENS: int = Field(
        default=10000,
        ge=1000,
        le=20000,
        description="Plot/world summary layer tokens (5-10k tokens)"
    )

    # Endpoint-Specific Generation Settings
    # Character Feedback Endpoint
    ENDPOINT_CHARACTER_FEEDBACK_TEMPERATURE: float = Field(
        default=0.8,
        ge=0.0,
        le=2.0,
        description="Temperature for character feedback generation"
    )
    ENDPOINT_CHARACTER_FEEDBACK_MAX_TOKENS: int = Field(
        default=800,
        ge=100,
        le=5000,
        description="Maximum tokens for character feedback generation"
    )

    # Editor Review Endpoint
    ENDPOINT_EDITOR_REVIEW_TEMPERATURE: float = Field(
        default=0.6,
        ge=0.0,
        le=2.0,
        description="Temperature for editor review generation"
    )
    ENDPOINT_EDITOR_REVIEW_MAX_TOKENS: int = Field(
        default=800,
        ge=100,
        le=5000,
        description="Maximum tokens for editor review generation"
    )

    # Flesh Out Endpoint
    ENDPOINT_FLESH_OUT_TEMPERATURE: float = Field(
        default=0.8,
        ge=0.0,
        le=2.0,
        description="Temperature for flesh out generation"
    )
    ENDPOINT_FLESH_OUT_MAX_TOKENS: int = Field(
        default=600,
        ge=100,
        le=5000,
        description="Maximum tokens for flesh out generation"
    )

    # Generate Chapter Endpoint
    ENDPOINT_GENERATE_CHAPTER_TEMPERATURE: float = Field(
        default=0.8,
        ge=0.0,
        le=2.0,
        description="Temperature for chapter generation"
    )
    ENDPOINT_GENERATE_CHAPTER_MAX_TOKENS: int = Field(
        default=2000,
        ge=500,
        le=10000,
        description="Maximum tokens for chapter generation"
    )

    # Generate Character Details Endpoint
    ENDPOINT_GENERATE_CHARACTER_DETAILS_TEMPERATURE: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for character details generation"
    )
    ENDPOINT_GENERATE_CHARACTER_DETAILS_MAX_TOKENS: int = Field(
        default=2000,
        ge=100,
        le=5000,
        description="Maximum tokens for character details generation"
    )

    # Modify Chapter Endpoint
    ENDPOINT_MODIFY_CHAPTER_TEMPERATURE: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for chapter modification"
    )
    ENDPOINT_MODIFY_CHAPTER_MAX_TOKENS: int = Field(
        default=2500,
        ge=500,
        le=10000,
        description="Maximum tokens for chapter modification"
    )

    # Rater Feedback Endpoint
    ENDPOINT_RATER_FEEDBACK_TEMPERATURE: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for rater feedback generation"
    )
    ENDPOINT_RATER_FEEDBACK_MAX_TOKENS: int = Field(
        default=600,
        ge=100,
        le=5000,
        description="Maximum tokens for rater feedback generation"
    )

    # Archive Endpoints
    ENDPOINT_ARCHIVE_SEARCH_TEMPERATURE: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Temperature for archive search generation"
    )
    ENDPOINT_ARCHIVE_SUMMARIZE_TEMPERATURE: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="Temperature for archive summarization"
    )

    # Context Distillation Temperature Settings
    DISTILLATION_GENERAL_TEMPERATURE: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="General temperature for context distillation"
    )
    DISTILLATION_PLOT_SUMMARY_TEMPERATURE: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Temperature for plot summary distillation"
    )
    DISTILLATION_CHARACTER_SUMMARY_TEMPERATURE: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Temperature for character summary distillation"
    )
    DISTILLATION_SCENE_SUMMARY_TEMPERATURE: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Temperature for scene summary distillation"
    )
    DISTILLATION_DIALOGUE_SUMMARY_TEMPERATURE: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="Temperature for dialogue summary distillation (higher for emotional nuance)"
    )
    DISTILLATION_FEEDBACK_SUMMARY_TEMPERATURE: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Temperature for feedback summary distillation (very low for consistency)"
    )
    DISTILLATION_SYSTEM_PROMPT_TEMPERATURE: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Temperature for system prompt distillation (very low for consistency)"
    )
    DISTILLATION_CONVERSATION_TEMPERATURE: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Temperature for conversation flow distillation"
    )

    # RAG Service Temperature Settings
    RAG_DEFAULT_TEMPERATURE: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Default temperature for RAG service operations"
    )
    RAG_SUMMARIZATION_TEMPERATURE: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="Temperature for RAG summarization operations"
    )

    def validate_layer_tokens(self) -> 'Settings':
        """Validate that layer token allocations don't exceed max tokens"""
        total_layer_tokens = (
            self.CONTEXT_LAYER_A_TOKENS +
            self.CONTEXT_LAYER_B_TOKENS +
            self.CONTEXT_LAYER_C_TOKENS +
            self.CONTEXT_LAYER_D_TOKENS +
            self.CONTEXT_LAYER_E_TOKENS
        )
        available_tokens = self.CONTEXT_MAX_TOKENS - self.CONTEXT_BUFFER_TOKENS

        if total_layer_tokens > available_tokens:
            raise ValueError(
                f"Context layer tokens sum to {total_layer_tokens}, which exceeds available tokens ({available_tokens}). "
                f"Total layer allocation cannot exceed max tokens minus buffer."
            )
        return self

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.validate_layer_tokens()


settings = Settings()
