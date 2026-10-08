from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "NeroSentinel"
    app_env: str = "development"
    database_url: str = "sqlite:///./aquasentinel.db"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "development-only-change-this-secret-now"
    access_token_minutes: int = 30
    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"])
    demo_mode: bool = True
    log_level: str = "INFO"

    @model_validator(mode="after")
    def secure_non_demo(self) -> "Settings":
        if not self.demo_mode and self.jwt_secret == "development-only-change-this-secret-now":
            raise ValueError("JWT_SECRET must be configured outside demo mode")
        if not self.demo_mode and len(self.jwt_secret) < 32:
            raise ValueError("JWT_SECRET must contain at least 32 characters")
        return self

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
