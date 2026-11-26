from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações lidas de variáveis de ambiente (ou do arquivo .env)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: str = "anthropic"  # anthropic | openai | mock

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-5-5"

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    llm_timeout_seconds: float = 30.0
    llm_max_retries: int = 1


@lru_cache
def get_settings() -> Settings:
    return Settings()
