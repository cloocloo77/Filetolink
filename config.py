from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    bot_token: str = Field(alias='BOT_TOKEN')
    api_id: int = Field(alias='API_ID')
    api_hash: str = Field(alias='API_HASH')
    base_url: str = Field(alias='BASE_URL')
    port: int = Field(default=8000, alias='PORT')
    database_url: str = Field(default='sqlite+aiosqlite:///./filetolink.db', alias='DATABASE_URL')
    file_expiry_hours: int = Field(default=24, alias='FILE_EXPIRY_HOURS')
    max_file_size: int = Field(default=2147483648, alias='MAX_FILE_SIZE')
    owner_id: int | None = Field(default=None, alias='OWNER_ID')
    force_download: bool = Field(default=False, alias='FORCE_DOWNLOAD')
    run_bot: bool = Field(default=True, alias='RUN_BOT')


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
