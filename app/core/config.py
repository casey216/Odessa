from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    DATABASE_URL_SYNC: str
    # Security
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    SESSION_SECRET_KEY: str

    # App
    APP_NAME: str
    APP_VERSION: str
    DEBUG: bool

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, env_file_encoding="utf-8"
    )


settings = Settings()  # type: ignore
