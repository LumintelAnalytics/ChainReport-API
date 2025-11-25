from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Dict, List


class Settings(BaseSettings):
    APP_NAME: str = "ChainReport API"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_URL: str = "sqlite+aiosqlite:///./sql_app.db"
    ONCHAIN_METRICS_URL: str | None = None
    TOKENOMICS_URL: str | None = None
    TWITTER_API_KEY: str = ""
    REDDIT_API_KEY: str = ""
    NEWS_API_KEY: str = ""
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None
    USER_AGENT: str = "ChainReport-API/1.0 (https://lumintelanalytics.com)"
    REQUEST_DELAY_SECONDS: float = 1.0
    MAX_RETRIES: int = 5
    RETRY_MULTIPLIER: float = 1.0
    MIN_RETRY_DELAY: float = 1.0
    MAX_RETRY_DELAY: float = 60.0
    AGENT_TIMEOUT: float = 30.0
    TEAM_PROFILE_URLS: Dict[str, List[str]] = {}
    WHITEPAPER_TEXT_SOURCES: Dict[str, str] = {}
    CODE_AUDIT_REPO_URL: str | None = None

    # Database connection settings for PostgreSQL (if used)
    DB_USER: str | None = None
    DB_PASSWORD: str | None = None
    DB_HOST: str | None = None
    DB_PORT: str | None = None
    DB_NAME: str | None = None

    # Test database connection settings
    TEST_DB_USER: str | None = None
    TEST_DB_PASSWORD: str | None = None
    TEST_DB_HOST: str | None = None
    TEST_DB_PORT: str | None = None
    TEST_DB_NAME: str | None = None

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
