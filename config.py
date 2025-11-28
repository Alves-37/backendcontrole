from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # Para rodar localmente, use a URL pública da Railway
    DATABASE_URL: str = "postgresql://postgres:lqlwBvNzwXPhgRjQgbMOYHgopHWqnCvr@tramway.proxy.rlwy.net:55237/railway"
    DATABASE_PUBLIC_URL: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
