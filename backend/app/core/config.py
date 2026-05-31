from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]
ROOT_ENV_FILE = REPO_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_ENV_FILE),
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
    jwt_mfa_challenge_expire_seconds: int = 300  # 5 minutos

    FRONTEND_URL: str = Field(default="http://localhost:5173")
    RESEND_API_KEY: str = Field(default="")
    EMAILS_FROM: str = Field(default="noreply@fleetops.local")
    EMAILS_FROM_NAME: str = Field(default="FleetOps")


settings = Settings()
