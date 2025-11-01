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
        default=1000,
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

    # Context Processing Priority Settings
    CONTEXT_PRIORITY_PLOT_HIGH: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Priority for high-priority plot elements"
    )
    CONTEXT_PRIORITY_PLOT_MEDIUM: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Priority for medium-priority plot elements"
    )
    CONTEXT_PRIORITY_PLOT_LOW: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Priority for low-priority plot elements"
    )
    CONTEXT_PRIORITY_CHARACTER: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Priority for character context elements"
    )
    CONTEXT_PRIORITY_USER_HIGH: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Priority for high-priority user requests"
    )
    CONTEXT_PRIORITY_USER_MEDIUM: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Priority for medium-priority user requests"
    )
    CONTEXT_PRIORITY_USER_LOW: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Priority for low-priority user requests"
    )
    CONTEXT_PRIORITY_SYSTEM_HIGH: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Priority for high-priority system instructions"
    )
    CONTEXT_PRIORITY_SYSTEM_MEDIUM: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Priority for medium-priority system instructions"
    )
    CONTEXT_PRIORITY_SYSTEM_LOW: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Priority for low-priority system instructions"
    )
    CONTEXT_HIGH_PRIORITY_THRESHOLD: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Threshold for determining high priority elements"
    )

    # Context Adapter Priority Settings
    CONTEXT_ADAPTER_SYSTEM_PREFIX_PRIORITY: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Priority for system prompt prefix in context adapter"
    )
    CONTEXT_ADAPTER_SYSTEM_SUFFIX_PRIORITY: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Priority for system prompt suffix in context adapter"
    )
    CONTEXT_ADAPTER_WRITING_ASSISTANT_PRIORITY: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Priority for writing assistant prompt in context adapter"
    )
    CONTEXT_ADAPTER_WRITING_EDITOR_PRIORITY: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Priority for writing editor prompt in context adapter"
    )
    CONTEXT_ADAPTER_CHARACTER_PROMPT_PRIORITY: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Priority for character prompt in context adapter"
    )
    CONTEXT_ADAPTER_RATER_PROMPT_PRIORITY: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Priority for rater prompt in context adapter"
    )
    CONTEXT_ADAPTER_EDITOR_PROMPT_PRIORITY: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Priority for editor prompt in context adapter"
    )
    CONTEXT_ADAPTER_INSTRUCTION_PRIORITY: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Priority for instructions in context adapter"
    )
    CONTEXT_ADAPTER_OUTPUT_PRIORITY: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Priority for output elements in context adapter"
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

    # Phase Validation Settings
    VALIDATION_PHASE_TRANSITION_THRESHOLD: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Threshold for valid phase transitions"
    )
    VALIDATION_OUTLINE_MIN_WORD_RATIO: float = Field(
        default=50.0,
        ge=1.0,
        le=1000.0,
        description="Minimum word count ratio for outline validation"
    )
    VALIDATION_CONFLICT_PRESENT_SCORE: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Score when conflict is present in validation"
    )
    VALIDATION_CONFLICT_ABSENT_SCORE: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Score when conflict is absent in validation"
    )
    VALIDATION_CHARACTERS_PRESENT_SCORE: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Score when characters are present in validation"
    )
    VALIDATION_CHARACTERS_ABSENT_SCORE: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Score when characters are absent in validation"
    )
    VALIDATION_CHAPTER_MIN_WORD_RATIO: float = Field(
        default=500.0,
        ge=1.0,
        le=5000.0,
        description="Minimum word count ratio for chapter validation"
    )
    VALIDATION_DIALOGUE_PRESENT_SCORE: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Score when dialogue is present in validation"
    )
    VALIDATION_DIALOGUE_ABSENT_SCORE: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Score when dialogue is absent in validation"
    )
    VALIDATION_COMPLETION_SCORE: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Score for completion validation"
    )
    VALIDATION_INCOMPLETE_SCORE: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Score for incomplete validation"
    )
    VALIDATION_SUMMARY_MIN_WORD_RATIO: float = Field(
        default=200.0,
        ge=1.0,
        le=2000.0,
        description="Minimum word count ratio for summary validation"
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
