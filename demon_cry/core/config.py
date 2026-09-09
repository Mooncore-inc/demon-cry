from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DC_")

    db_url: str = "sqlite+aiosqlite:///database.db"
    host: str = "127.0.0.1"
    port: int = 8000


config = Config()
