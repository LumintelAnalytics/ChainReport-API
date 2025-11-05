from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "ChainReport API"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./sql_app.db"
    ONCHAIN_METRICS_URL: str | None = None
    TOKENOMICS_URL: str | None = None

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
