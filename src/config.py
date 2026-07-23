from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # No default: DATABASE_URL must be provided via env (app.env / env_file).
    # Embedding credentials in code is a security risk; fail loudly if missing.
    database_url: str
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"
    vision_confidence_readable: float = 0.7
    vision_confidence_uncertain: float = 0.3
    cache_maxsize: int = 256
    rate_limit_extract: str = "10/minute"
    rate_limit_process: str = "10/minute"
    # Fail-closed switch for production: if True and a critical guardrail
    # (PII / prompt injection) fails to load, startup aborts instead of
    # silently degrading to NullGuardrail. Default False for local dev.
    guardrails_required: bool = False
    # OOD / anomaly detection threshold: scores above this mark the image as
    # out-of-distribution (not a prescription) and trigger abstention.
    anomaly_threshold: float = 0.5

    model_config = SettingsConfigDict(env_file="app.env", env_file_encoding="utf-8")


settings = Settings()
