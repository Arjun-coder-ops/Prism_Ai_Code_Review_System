from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="PRISM_", extra="ignore")
    env: str = "development"
    database_url: str = "postgresql+asyncpg://prism:prism@localhost:5432/prism"
    alembic_database_url: str = "postgresql+psycopg://prism:prism@localhost:5432/prism"
    redis_url: str = "redis://localhost:6379/0"
    github_token: str | None = None
    github_app_id: str | None = None
    github_webhook_secret: str | None = None
    github_private_key_path: str | None = None
    api_key: str | None = None
    rate_limit_per_minute: int = 30
    allow_private_ai: bool = False
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
