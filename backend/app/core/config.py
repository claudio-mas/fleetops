from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Literal["dev", "test", "staging", "production"] = "dev"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    database_url: str = Field(..., min_length=1)
    redis_url: str = Field(..., min_length=1)
    secret_key: str = Field(..., min_length=32)

    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_seconds: int = 900  # 15 minutos
    jwt_refresh_token_expire_seconds: int = 604800  # 7 dias

    RESEND_API_KEY: str = Field(default="")
    EMAILS_FROM: str = Field(default="noreply@fleetops.local")
    EMAILS_FROM_NAME: str = Field(default="FleetOps")


settings = Settings()
