"""Application settings, read from environment variables and an optional .env file."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Every field can be set with an environment variable name MURMUR_<FIELD>."""

    model_config = SettingsConfigDict(env_prefix="MURMUR_", env_file=".env", extra="ignore")

    app_name: str = "Murmur API"
    max_message_length: int = Field(default=4000, gt=0)
    database_url: str = "postgresql+psycopg://murmur:murmur@localhost:5433/murmur"


@lru_cache
def get_settings() -> Settings:
    return Settings()


SettingsDep = Annotated[Settings, Depends(get_settings)]
