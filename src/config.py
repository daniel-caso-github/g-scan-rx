from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://gscan:gscan@localhost:5432/gscan_rx"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"
    vision_confidence_readable: float = 0.7
    vision_confidence_uncertain: float = 0.3
    cache_maxsize: int = 256
    rate_limit_extract: str = "10/minute"
    rate_limit_process: str = "10/minute"

    model_config = SettingsConfigDict(env_file="app.env", env_file_encoding="utf-8")


settings = Settings()
