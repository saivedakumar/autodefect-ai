from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    github_token: str = ""
    github_repo: str = ""
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "deepseek-coder:6.7b"
    database_url: str = "sqlite:///./autodefect.db"
    service_token: str = "change-me-local-shared-secret"
    playwright_test_dir: str = "tests/playwright"


@lru_cache
def get_settings() -> Settings:
    return Settings()
