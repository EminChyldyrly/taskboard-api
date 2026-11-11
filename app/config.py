"""Настройки приложения: читаются из переменных окружения."""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./taskboard.db")
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-change-me-please-use-a-long-random-string")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


settings = Settings()
