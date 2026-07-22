from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://gscan:gscan@localhost:5432/gscan_rx"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"
    confidence_threshold: float = 0.7

    model_config = SettingsConfigDict(env_file="app.env", env_file_encoding="utf-8")


settings = Settings()
