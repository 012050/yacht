from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./yacht.db"

    # JWT
    SECRET_KEY: str = "change-me-in-production-use-env-var"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Game
    DEFAULT_TIMEOUT_DURATION: int = 60
    JOIN_CODE_LENGTH: int = 6

    # Security
    MAX_LOGIN_ATTEMPTS_PER_MINUTE: int = 10
    MAX_GAME_ACTIONS_PER_MINUTE: int = 30
    MAX_WEBSOCKET_MSGS_PER_SECOND: int = 10

    model_config = {"env_prefix": "YACHT_"}


settings = Settings()
