from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    llm_provider: str = "openrouter"
    llm_model: str = "nvidia/nemotron-3-super-120b-a12b:free"
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    database_url: str = "sqlite:///./parcelpilot.db"
    embedding_model: str = "all-MiniLM-L6-v2"
    vector_store: str = "chromadb"
    environment: str = "development"
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
