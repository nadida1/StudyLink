from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Единая точка конфигурации (паттерн Singleton через lru_cache)."""
    database_url: str = "sqlite+aiosqlite:///./tutor.db"
    secret_key: str = "dev-secret-key-change-in-production"
    access_token_expire_minutes: int = 60 * 24
    tutor_email: str = "tutor@example.com"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    app_name: str = "Tutor Platform"
    debug: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
