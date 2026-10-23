from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    mongodb_uri: str
    mongodb_db_name: str = "techgear"

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env")


settings = Settings()
