from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


API_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    mongodb_uri: str
    db_name: str = "techgear"
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    admin_registration_code: str = ""

    model_config = SettingsConfigDict(env_file=API_ROOT / ".env", extra="ignore")


settings = Settings()