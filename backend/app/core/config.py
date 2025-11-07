from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Dict, List


class Settings(BaseSettings):
    APP_NAME: str = "ChainReport API"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./sql_app.db"
    ONCHAIN_METRICS_URL: str | None = None
    TOKENOMICS_URL: str | None = None
    TWITTER_API_KEY: str = ""
    REDDIT_API_KEY: str = ""
    NEWS_API_KEY: str = ""
    USER_AGENT: str = "ChainReport-API/1.0 (https://lumintelanalytics.com)"
    REQUEST_DELAY_SECONDS: float = 1.0
    AGENT_TIMEOUT: float = 30.0
    TEAM_PROFILE_URLS: Dict[str, List[str]] = {}
    WHITEPAPER_TEXT_SOURCES: Dict[str, str] = {}
    CODE_AUDIT_REPO_URL: str | None = None

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
