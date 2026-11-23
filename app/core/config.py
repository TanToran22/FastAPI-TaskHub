from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core import constants


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "TaskHub"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/taskhub_db",
        description="Async PostgreSQL Connection URL",
    )
    TEST_DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/taskhub_test_db",
        description="Async PostgreSQL Connection URL for testing",
    )

    SECRET_KEY: str = Field(
        ...,
        min_length=32,
        description="Secret key for JWT signing (generate with: openssl rand -hex 32)",
    )
    JWT_ALGORITHM: str = constants.JWT_ALGORITHM
    ACCESS_TOKEN_EXPIRE_MINUTES: int = constants.ACCESS_TOKEN_EXPIRE_MINUTES
    REFRESH_TOKEN_EXPIRE_DAYS: int = constants.REFRESH_TOKEN_EXPIRE_DAYS

    REDIS_URL: str = "redis://localhost:6379/0"


settings = Settings()
