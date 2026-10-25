"""
NEXUS Backend Configuration (Pydantic Settings)
Loads environment variables safely with strict validation and sane defaults.
"""
import json
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    ENV: str = "dev"
    DEBUG: bool = True

    # Security & Auth
    JWT_SECRET: str = Field(
        default="nexus_dev_insecure_jwt_secret_key_change_in_production_32bytes",
        description="HMAC secret key for JWT access and refresh tokens"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = 30
    REFRESH_TOKEN_DAYS: int = 7

    # Databases
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://nexus:nexus_password@localhost:5432/nexus",
        description="Async SQLAlchemy database connection string (asyncpg)"
    )
    CHECKPOINT_DSN: str = Field(
        default="postgresql://nexus:nexus_password@localhost:5432/nexus",
        description="Psycopg connection string for LangGraph checkpointer"
    )
    CHROMA_PATH: str = "./data/chroma"

    # Ollama & Local Model
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    QWEN3_4B_URL: str = "http://127.0.0.1:8080"
    QWEN3_8B_URL: str = "http://127.0.0.1:8081"
    LOCAL_QWEN_DIR: str = r"D:\own ai\Local_Qwen3_System"
    DEFAULT_PROFILE: str = "fast"
    OLLAMA_TIMEOUT_SECONDS: float = 60.0
    OLLAMA_KEEP_ALIVE: str = "10m"

    # Document Uploads & Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_MB: int = 25
    MAX_USER_QUOTA_MB: int = 500

    # RAG Settings
    RAG_MIN_SCORE: float = 0.35
    RAG_MAX_CHUNKS: int = 6

    # Sandbox
    SANDBOX_URL: str = "http://localhost:8001"
    SANDBOX_KEY: str = "nexus_dev_sandbox_shared_secret"

    # CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                return [s.strip() for s in v.split(",") if s.strip()]
        return v


settings = Settings()
