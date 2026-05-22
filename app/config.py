from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://aegis:aegis@localhost:5432/aegis_db"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_database_url(cls, v: str) -> str:
        if v and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Security
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # LLM Settings
    LLM_PROVIDER: str = "ollama"  # "ollama", "openai", or "google"
    LLM_MODEL: str = "mistral"    # Default model for the chosen provider

    # Ollama LLM
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "mistral"

    # Qdrant Vector DB
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333

    # Application
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            import json

            try:
                return json.loads(v)
            except Exception:
                return [origin.strip() for origin in v.split(",")]
        return v

    # External AI APIs
    OPENAI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""

    # Cloudinary Storage
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    model_config = {"env_file": ".env", "case_sensitive": True, "extra": "ignore"}


settings = Settings()


# Propagate external-API keys into os.environ so child libraries (openai SDK,
# google SDK, t2v pipeline agents) that read them directly from the
# environment pick them up. Pydantic-settings only populates the Settings
# object — it does not mutate the process environment.
import os as _os  # noqa: E402

if settings.OPENAI_API_KEY and not _os.environ.get("OPENAI_API_KEY"):
    _os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
if settings.GOOGLE_API_KEY and not _os.environ.get("GOOGLE_API_KEY"):
    _os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY
if settings.CLOUDINARY_CLOUD_NAME and not _os.environ.get("CLOUDINARY_CLOUD_NAME"):
    _os.environ["CLOUDINARY_CLOUD_NAME"] = settings.CLOUDINARY_CLOUD_NAME
if settings.CLOUDINARY_API_KEY and not _os.environ.get("CLOUDINARY_API_KEY"):
    _os.environ["CLOUDINARY_API_KEY"] = settings.CLOUDINARY_API_KEY
if settings.CLOUDINARY_API_SECRET and not _os.environ.get("CLOUDINARY_API_SECRET"):
    _os.environ["CLOUDINARY_API_SECRET"] = settings.CLOUDINARY_API_SECRET
