from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str = ""
    supabase_secret_key: str = ""
    supabase_jwks_url: str = ""

    litellm_base_url: str = "http://localhost:4000"
    litellm_api_key: str = ""

    # pydantic-settings tries to JSON-parse env vars for list[str] fields
    # before any validator runs, so a plain comma-separated string (e.g.
    # "http://a.com,http://b.com") would blow up at import time. Keep the
    # raw string and split it ourselves instead.
    cors_origins_raw: str = Field(default="http://localhost:3000", validation_alias="CORS_ORIGINS")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


settings = Settings()
