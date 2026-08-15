from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str = "sqlite:////app/data/yacht.db"
    SECRET_KEY: str = "change-me-to-a-random-secret-key"
    JWT_ACCESS_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_EXPIRE_DAYS: int = 7
    TURN_TIME_LIMIT: int = 60
    # Comma-separated list of allowed CORS origins (empty = dev defaults).
    CORS_ORIGINS: str = ""


settings = Settings()
