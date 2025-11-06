from pydantic_settings import BaseSettings, SettingsConfigDict


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

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
