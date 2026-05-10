from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str = Field(default="", alias="BOT_TOKEN")
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/game.db",
        alias="DATABASE_URL",
    )
    stories_path: Path = Field(default=Path("./stories"), alias="STORIES_PATH")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def sqlite_path(self) -> Path:
        prefix = "sqlite+aiosqlite:///"
        if not self.database_url.startswith(prefix):
            msg = "Only sqlite+aiosqlite DATABASE_URL is supported by the MVP."
            raise ValueError(msg)
        raw_path = self.database_url.removeprefix(prefix)
        return Path(raw_path)


@lru_cache
def get_settings() -> Settings:
    return Settings()
