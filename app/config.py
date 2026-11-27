"""Настройки приложения: читаются из переменных окружения."""
import os
from dataclasses import dataclass, field
from secrets import token_urlsafe


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./taskboard.db")
    secret_key: str = field(default_factory=lambda: os.getenv("SECRET_KEY") or token_urlsafe(48))
    environment: str = field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


    def __post_init__(self) -> None:
        if self.environment not in {"development", "production"}:
            raise ValueError("APP_ENV must be development or production")
        if self.environment == "production" and not os.getenv("SECRET_KEY"):
            raise ValueError("SECRET_KEY must be set in production")
        if len(self.secret_key.encode()) < 32 or self.secret_key in {
            "dev-secret-change-me-please-use-a-long-random-string",
            "change-me-to-a-long-random-string-before-production",
        }:
            raise ValueError("SECRET_KEY must contain at least 32 bytes and cannot use a sample value")
        if self.access_token_expire_minutes < 1:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be positive")


settings = Settings()
