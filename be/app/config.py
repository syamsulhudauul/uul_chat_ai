from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""

    litellm_base_url: str = "http://litellm:4000"
    litellm_api_key: str = ""

    cors_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
