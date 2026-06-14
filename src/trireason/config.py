"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_base_url: str | None = None

    # Database
    database_url: str = "postgresql+asyncpg://trireason:trireason@localhost:5432/trireason"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Server
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "info"

    # TriReason defaults
    default_max_iterations: int = 5
    default_score_threshold: int = 85

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
