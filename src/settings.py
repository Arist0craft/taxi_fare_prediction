from functools import lru_cache
from pathlib import Path

from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_DIR: Path = Path(__file__).resolve().parent.parent
    APP_DIR: Path = PROJECT_DIR / "src"

    SECRET_KEY: str = Field()
    TG_BOT_TOKEN: str = Field()
    TG_WEBHOOK_URL: AnyUrl = Field()

    model_config = SettingsConfigDict(env_file=PROJECT_DIR / ".env")


@lru_cache
def get_settings() -> Settings:
    return Settings()
