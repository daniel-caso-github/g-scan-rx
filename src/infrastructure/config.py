from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://gscan:gscan@localhost:5432/gscan_rx"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"
    confidence_threshold: float = 0.7
    normalizer_url: str = "http://localhost:8080/v1"
    normalizer_model: str = "gscan-norm-v1"
    vision_model: str = "claude-opus-4-8"
    vision_confidence_readable: float = 0.7
    vision_confidence_uncertain: float = 0.3
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    model_config = SettingsConfigDict(env_file="app.env", env_file_encoding="utf-8")


settings = Settings()
