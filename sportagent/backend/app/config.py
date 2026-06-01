import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    news_api_key: str = ""
    app_bearer_token: str = ""
    database_url: str = "postgresql+asyncpg://sportagent:devpass@localhost:5432/sportagent"
    log_level: str = "INFO"
    tz: str = "Europe/Istanbul"
    n8n_url: str = "http://localhost:5678"
    outputs_dir: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")


settings = Settings()
