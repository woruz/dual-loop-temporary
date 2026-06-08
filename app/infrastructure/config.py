import logging
from urllib.parse import urlparse
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

class Settings(BaseSettings):

    database_url: str
    redis_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith("postgresql"):
            logger.warning("database_url does not start with postgresql")
        return v

    @field_validator("redis_url")
    @classmethod
    def validate_redis_url(cls, v: str) -> str:
        if not v.startswith("redis"):
            logger.warning("redis_url does not start with redis")
        return v

try:
    import os

    print("cwd =", os.getcwd())
    print("REDIS_URL from env =", os.getenv("REDIS_URL"))
    settings = Settings()
    logger.info("Settings loaded successfully")
except ValidationError as e:
    logger.exception(f"Failed to load settings: {e}")
    raise e
