from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Writer Assistant"

    # Development settings
    DEBUG: bool = True

    # Database settings (using JSON files for MVP)
    DATA_DIR: str = "data"

    # Agent settings
    MAX_CONTEXT_LENGTH: int = 4000
    DEFAULT_TEMPERATURE: float = 0.7

    # Security settings
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()